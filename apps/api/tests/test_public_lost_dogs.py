from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from app.models import FoundReportContact, LostCase, Notification, Observation, Photo, RecoveryOutcome


def publish(client, headers, *, name="Luna", species="dog", sex="unknown", description="Perro marrón con pecho blanco", area="El Pinar, Canelones, Uruguay"):
    pet = client.post("/api/v1/pets", headers=headers, json={
        "name": name, "species": species, "sex": sex, "primary_color": "brown", "size": "medium",
        "microchip_reference": "private-chip",
    }).json()
    case_response = client.post("/api/v1/lost-cases", headers=headers, json={
        "pet_id": pet["id"], "lost_at": datetime.now(timezone.utc).isoformat(),
        "latitude": -34.791234, "longitude": -55.954567, "description": description,
        "public_location": area,
    })
    assert case_response.status_code == 201
    return pet, case_response.json()


def add_photo(client, headers, owner_type, owner_id):
    response = client.post("/api/v1/photos", headers=headers, json={
        "owner_type": owner_type, "owner_id": owner_id,
        "storage_key": f"{owner_type}/{owner_id}/{uuid4()}.jpg", "mime_type": "image/jpeg",
    })
    assert response.status_code == 201
    return response.json()


def test_public_dogs_need_no_login_and_expose_only_notice_fields(client, auth_headers):
    _, case = publish(client, auth_headers)
    listing = client.get("/api/v1/public/lost-animals")
    assert listing.status_code == 200
    assert listing.headers["cache-control"] == "no-store"
    assert listing.json()["total"] == 1
    dog = listing.json()["items"][0]
    assert set(dog) == {"id", "public_id", "name", "species", "sex", "breed", "size", "primary_color", "description", "public_location", "lost_at", "photo_url", "publisher_name", "photo_ids", "secondary_colors", "collar_status", "collar_color", "collar_description", "clothing_status", "clothing_description", "clothing_color"}
    assert dog["name"] == "Luna"
    assert dog["sex"] == "unknown"
    assert dog["public_location"] == "El Pinar, Canelones, Uruguay"
    assert dog["photo_url"] is None
    assert "private-chip" not in listing.text
    assert "owner@example.com" not in listing.text
    detail = client.get(f"/api/v1/public/lost-animals/{case['id']}")
    assert detail.json() == dog
    assert client.get(f"/api/v1/lost-cases/{case['id']}").status_code == 401


@pytest.mark.parametrize("sex", ["male", "female"])
def test_declared_pet_sex_is_public_and_updates_with_pet(client, auth_headers, sex):
    pet, case = publish(client, auth_headers, sex=sex)
    path = f"/api/v1/public/lost-animals/{case['id']}"
    assert client.get(path).json()["sex"] == sex
    assert client.get("/api/v1/public/lost-animals").json()["items"][0]["sex"] == sex
    assert client.patch(f"/api/v1/pets/{pet['id']}", headers=auth_headers, json={"sex": "unknown"}).status_code == 200
    assert client.get(path).json()["sex"] == "unknown"


@pytest.mark.parametrize("status", ["FOUND", "CLOSED", "CANCELLED"])
def test_finished_notices_are_hidden_in_list_detail_and_photo(client, auth_headers, status):
    _, case = publish(client, auth_headers)
    add_photo(client, auth_headers, "lost_case", case["id"])
    assert client.patch(f"/api/v1/lost-cases/{case['id']}", headers=auth_headers, json={"status": status}).status_code == 200
    assert client.get("/api/v1/public/lost-animals").json()["total"] == 0
    assert client.get(f"/api/v1/public/lost-animals/{case['id']}").status_code == 404
    assert client.get(f"/api/v1/public/lost-animals/{case['id']}/photo").status_code == 404


@pytest.mark.parametrize("species", ["dog", "cat"])
def test_owner_can_confirm_recovery_without_photos_or_another_report(client, auth_headers, db_factory, species):
    _, case = publish(client, auth_headers, species=species)
    path = f"/api/v1/lost-cases/{case['id']}"
    # This is the action used by the owner on the notice and its linked found page.
    # Nothing is required beyond the existing notice and the intended new state.
    for _ in range(2):
        response = client.patch(path, headers=auth_headers, json={"status": "FOUND"})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "FOUND"
        assert response.json()["public_id"] == case["public_id"]
    with db_factory() as db:
        assert db.get(LostCase, UUID(case["id"])).status == "FOUND"
        outcome = db.get(RecoveryOutcome, UUID(case["id"]))
        assert outcome and outcome.reason == "PREFER_NOT_TO_SAY"
        assert outcome.match_id is outcome.observation_id is None
        assert db.scalar(select(func.count()).select_from(RecoveryOutcome)) == 1
        for model in (Photo, Observation, FoundReportContact, Notification):
            assert db.scalar(select(func.count()).select_from(model)) == 0
    assert client.get("/api/v1/public/lost-animals").json()["total"] == 0
    assert client.get(f"/api/v1/public/lost-animals/{case['id']}").status_code == 404
    assert client.get(f"/api/v1/reviews/lost-cases/{case['id']}", headers=auth_headers).json()["eligible"] is True


def test_direct_recovery_is_exclusively_for_the_notice_owner(client, auth_headers, db_factory):
    _, case = publish(client, auth_headers)
    path = f"/api/v1/lost-cases/{case['id']}"
    stranger = client.post("/api/v1/auth/register", json={
        "email": "recovery-stranger@example.test", "password": "a-strong-passphrase", "name": "Stranger",
    }).json()
    stranger_headers = {"Authorization": f"Bearer {stranger['access_token']}"}
    assert client.get(path, headers=auth_headers).status_code == 200
    assert client.get(path, headers=stranger_headers).status_code == 404
    assert client.patch(path, json={"status": "FOUND"}).status_code == 401
    assert client.patch(path, headers=stranger_headers, json={"status": "FOUND"}).status_code == 404
    with db_factory() as db:
        assert db.get(LostCase, UUID(case["id"])).status == "ACTIVE"
        assert db.scalar(select(func.count()).select_from(RecoveryOutcome)) == 0
    assert client.get(f"/api/v1/public/lost-animals/{case['id']}").status_code == 200


@pytest.mark.parametrize("species", ["dog", "cat"])
def test_supported_lost_species_are_listed_and_unknown_ids_are_hidden(client, auth_headers, species):
    _, case = publish(client, auth_headers, species=species)
    listing = client.get("/api/v1/public/lost-animals").json()
    assert listing["total"] == 1
    assert listing["items"][0]["species"] == species
    assert listing["items"][0]["id"] == case["id"]
    assert client.get(f"/api/v1/public/lost-animals/{case['id']}").json()["species"] == species
    assert client.get(f"/api/v1/public/lost-animals/{uuid4()}").status_code == 404


def test_previous_public_route_still_works(client, auth_headers):
    _, case = publish(client, auth_headers)
    assert client.get("/api/v1/public/lost-dogs").json() == client.get("/api/v1/public/lost-animals").json()
    assert client.get(f"/api/v1/public/lost-dogs/{case['id']}").json() == client.get(f"/api/v1/public/lost-animals/{case['id']}").json()


def test_search_pagination_and_literal_wildcards(client, auth_headers):
    publish(client, auth_headers, name="Luna")
    publish(client, auth_headers, name="Toby", description="Perro negro", area="Montevideo, Uruguay")
    assert client.get("/api/v1/public/lost-animals?q=LUNA").json()["total"] == 1
    assert client.get("/api/v1/public/lost-animals?q=montevideo").json()["items"][0]["name"] == "Toby"
    assert client.get("/api/v1/public/lost-animals?q=pecho%20blanco").json()["items"][0]["name"] == "Luna"
    assert client.get("/api/v1/public/lost-animals?q=%25").json()["total"] == 0
    assert client.get("/api/v1/public/lost-animals?q=_").json()["total"] == 0
    first = client.get("/api/v1/public/lost-animals?limit=1").json()
    second = client.get("/api/v1/public/lost-animals?limit=1&offset=1").json()
    assert first["total"] == second["total"] == 2
    assert first["items"][0]["id"] != second["items"][0]["id"]
    assert client.get("/api/v1/public/lost-animals?limit=1&offset=2").json()["items"] == []
    assert client.get("/api/v1/public/lost-animals?limit=100").status_code == 422
    assert client.get("/api/v1/public/lost-animals?offset=-1").status_code == 422


def test_old_notice_locality_and_edited_notice(client, auth_headers):
    _, case = publish(client, auth_headers, description="Marrón\n\nZona: El Pinar, Canelones, Uruguay", area=None)
    path = f"/api/v1/public/lost-animals/{case['id']}"
    assert client.get(path).json()["public_location"] == "El Pinar, Canelones, Uruguay"
    client.patch(f"/api/v1/lost-cases/{case['id']}", headers=auth_headers, json={"public_location": "Solymar, Canelones", "description": "Actualización"})
    notice = client.get(path).json()
    assert notice["description"] == "Actualización"
    assert notice["public_location"] == "Solymar, Canelones"
    assert client.delete(f"/api/v1/lost-cases/{case['id']}", headers=auth_headers).status_code == 204
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("species", ["dog", "cat"])
def test_public_photo_selects_case_before_pet_and_keeps_storage_private(client, auth_headers, monkeypatch, species):
    from app.routers import public_lost_dogs

    pet, case = publish(client, auth_headers, species=species)
    pet_photo = add_photo(client, auth_headers, "pet", pet["id"])
    used_keys = []
    monkeypatch.setattr(public_lost_dogs, "load_analysis_image", lambda key, mime: (used_keys.append(key) or b"clean-jpeg", "image/jpeg"))
    path = f"/api/v1/public/lost-animals/{case['id']}"
    assert client.get(path).json()["photo_url"] == path + "/photo"
    assert client.get(path + "/photo").content == b"clean-jpeg"
    assert used_keys[-1] == pet_photo["storage_key"]
    case_photo = add_photo(client, auth_headers, "lost_case", case["id"])
    client.put("/api/v1/photos/cover", headers=auth_headers, json={"owner_type":"lost_case","owner_id":case["id"],"photo_id":case_photo["id"]})
    image = client.get(path + "/photo")
    assert used_keys[-1] == case_photo["storage_key"]
    assert image.headers["content-type"] == "image/jpeg"
    assert image.headers["cache-control"] == "no-store"
    assert image.headers["x-content-type-options"] == "nosniff"
    assert "storage_key" not in client.get(path).text
    assert client.get(f"/api/v1/photos/{case_photo['id']}/url").status_code == 401


def test_public_photo_does_not_fall_back_to_another_dog(client, auth_headers, monkeypatch):
    from app.routers import public_lost_dogs

    _, first = publish(client, auth_headers)
    _, second = publish(client, auth_headers, name="Toby")
    add_photo(client, auth_headers, "lost_case", second["id"])
    monkeypatch.setattr(public_lost_dogs, "load_analysis_image", lambda *_: pytest.fail("Wrong dog's image read"))
    assert client.get(f"/api/v1/public/lost-animals/{first['id']}/photo").status_code == 404


def test_public_photo_handles_unavailable_storage_without_leaking_errors(client, auth_headers, monkeypatch):
    from app.routers import public_lost_dogs

    _, case = publish(client, auth_headers)
    add_photo(client, auth_headers, "lost_case", case["id"])
    def unavailable(*_):
        raise ValueError("private storage details")
    monkeypatch.setattr(public_lost_dogs, "load_analysis_image", unavailable)
    response = client.get(f"/api/v1/public/lost-animals/{case['id']}/photo")
    assert response.status_code == 503
    assert "private storage details" not in response.text
