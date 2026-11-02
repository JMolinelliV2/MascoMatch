from datetime import datetime, timezone
import json
from uuid import UUID

import pytest

from app.analysis.service import text_snapshot
from app.models import Observation
from test_linked_sightings import data, lost_notice, submit
from test_public_lost_dogs import publish, add_photo

DETAILS = {"breed": "  Cruza de terrier uruguayo  ", "primary_color": "Gris azulado",
           "secondary_colors": ["Blanco", "gris azulado"], "collar_status": "yes", "collar_color": "Turquesa",
           "collar_description": "Con chapita", "clothing_status": "yes", "clothing_description": "Pañuelo",
           "clothing_color": "Violeta"}


def test_lost_report_custom_details_survive_edit_public_read_and_analysis(client, auth_headers, db_factory):
    pet, case = publish(client, auth_headers)
    updated = client.patch(f"/api/v1/me/cases/{case['id']}", headers=auth_headers,
                           json={"pet": DETAILS, "case": {"description": "Texto original sin procesar"}})
    assert updated.status_code == 200
    owner_pet = client.get(f"/api/v1/pets/{pet['id']}", headers=auth_headers).json()
    public = client.get(f"/api/v1/public/lost-animals/{case['id']}").json()
    assert owner_pet["breed"] == public["breed"] == DETAILS["breed"].strip()
    assert public["primary_color"] == "Gris azulado"
    assert public["secondary_colors"] == ["white", "gris azulado"]
    for key in ("collar_status", "collar_color", "collar_description", "clothing_status", "clothing_description", "clothing_color"):
        assert public[key] == owner_pet[key] == DETAILS[key]
    assert public["description"] == "Texto original sin procesar"
    with db_factory() as db:
        traits = text_snapshot(db, "lost_case", UUID(case["id"]))["declared_features"]
        assert traits["breed"] == DETAILS["breed"].strip()
        assert traits["clothing_color"] == "Violeta"
    assert client.patch(f"/api/v1/pets/{pet['id']}", headers=auth_headers, json={"collar_status": "no"}).status_code == 200
    final = client.get(f"/api/v1/pets/{pet['id']}", headers=auth_headers).json()
    assert final["collar_color"] is None and final["collar_description"] is None
    assert final["breed"] == owner_pet["breed"]  # Partial edits preserve other traits.


@pytest.mark.parametrize("source", ["USER_SIGHTING", "FOUND_ANIMAL"])
def test_all_observation_types_keep_custom_traits_and_expose_them_for_editing(client, auth_headers, source):
    body = {**DETAILS, "species": "cat", "source_type": source, "description": "Descripción escrita",
            "observed_at": datetime.now(timezone.utc).isoformat()}
    response = client.post("/api/v1/observations", headers=auth_headers, json=body)
    assert response.status_code == 201
    identity = response.json()["id"]
    edit = client.get(f"/api/v1/observations/{identity}/edit", headers=auth_headers).json()
    public = client.get(f"/api/v1/public/observations/{identity}").json()
    assert public["breed"] == edit["breed"] == DETAILS["breed"].strip()
    assert public["collar_color"] == edit["collar_color"] == "Turquesa"
    assert "author_id" not in public and "latitude" not in public
    changed = client.patch(f"/api/v1/observations/{identity}", headers=auth_headers,
                           json={"breed": "Siamés mestizo", "primary_color": "MARRÓN", "clothing_status": "no"})
    assert changed.status_code == 200
    assert changed.json()["breed"] == "Siamés mestizo"
    assert changed.json()["primary_color"] == "brown"
    assert changed.json()["clothing_color"] is None
    assert changed.json()["description"] == "Descripción escrita"


def test_brief_linked_sighting_accepts_optional_independent_details_idempotently(client, auth_headers, db_factory):
    _, case = lost_notice(client, auth_headers)
    payload = data(details=json.dumps(DETAILS))
    result = submit(client, case, payload)
    assert result.status_code == 201 and result.json()["owner_notified"]
    assert submit(client, case, payload).json() == result.json()
    with db_factory() as db:
        observation = db.get(Observation, UUID(result.json()["id"]))
        assert observation.breed == DETAILS["breed"].strip()
        assert observation.primary_color == "Gris azulado"
        assert observation.collar_color == "Turquesa"
        assert observation.author_id is None
    payload["details"] = json.dumps({**DETAILS, "breed": "Otra raza"})
    assert submit(client, case, payload).status_code == 409


def test_filters_combine_before_pagination_and_accept_custom_values(client, auth_headers):
    pet, case = publish(client, auth_headers, name="Uno")
    client.patch(f"/api/v1/me/cases/{case['id']}", headers=auth_headers, json={"pet": {**DETAILS, "sex": "male"}, "case": {}})
    publish(client, auth_headers, name="Dos", species="cat")
    path = "/api/v1/public/lost-animals"
    criteria = {"species": "dog", "sex": "male", "breed": "TERRIER", "color": "gris AZULADO", "size": "medium", "collar": "yes", "limit": 1}
    response = client.get(path, params=criteria).json()
    assert response["total"] == 1 and response["items"][0]["id"] == case["id"]
    assert client.get(path, params={**criteria, "offset": 1}).json()["items"] == []
    assert client.get(path, params={**criteria, "color": "Blanco"}).json()["total"] == 1  # Secondary color.
    assert client.get(path, params={**criteria, "species": "cat"}).json()["total"] == 0
    assert client.get(path, params={"breed": "%"}).json()["total"] == 0
    assert client.get(path, params={"breed": "_"}).json()["total"] == 0
    assert client.get(path, params={"with_photos": True}).json()["total"] == 0
    add_photo(client, auth_headers, "pet", pet["id"])
    assert client.get(path, params={**criteria, "with_photos": True}).json()["total"] == 1
    assert client.get(path, params={**criteria, "with_photos": False}).json()["total"] == 0


def test_lost_date_filters_include_whole_uruguayan_day(client, auth_headers):
    cases = [publish(client, auth_headers, name=name)[1] for name in ("Antes", "Inicio", "Fin", "Después")]
    for case, when in zip(cases, ("2026-10-20T02:59:59Z", "2026-10-20T03:00:00Z", "2026-10-21T02:59:59Z", "2026-10-21T03:00:00Z")):
        assert client.patch(f"/api/v1/lost-cases/{case['id']}", headers=auth_headers, json={"lost_at": when}).status_code == 200
    path = "/api/v1/public/lost-animals"
    listing = client.get(path, params={"lost_from": "2026-10-20", "lost_to": "2026-10-20"}).json()
    assert listing["total"] == 2
    assert {item["name"] for item in listing["items"]} == {"Inicio", "Fin"}
    assert client.get(path, params={"lost_from": "2026-10-21", "lost_to": "2026-10-20"}).status_code == 422
    assert client.get(path, params={"lost_to": "9999-12-31"}).status_code == 422


def test_card_gallery_metadata_matches_album_and_selected_inherited_cover(client, auth_headers):
    pet, case = publish(client, auth_headers)
    inherited = add_photo(client, auth_headers, "pet", pet["id"])
    own = add_photo(client, auth_headers, "lost_case", case["id"])
    response = client.put("/api/v1/photos/cover", headers=auth_headers,
                          json={"owner_type": "lost_case", "owner_id": case["id"], "photo_id": inherited["id"]})
    assert response.status_code == 200
    base = f"/api/v1/public/lost-animals/{case['id']}"
    gallery = client.get(f"{base}/photos").json()["items"]
    ids = client.get("/api/v1/public/lost-animals").json()["items"][0]["photo_ids"]
    assert ids == [item["id"] for item in gallery] == [inherited["id"], own["id"]]
    assert client.get(base).json()["photo_ids"] == ids


@pytest.mark.parametrize("changes", [{"primary_color": 12}, {"breed": None}, {"collar_status": None}, {"collar_status": "maybe"}, {"secondary_colors": ["a", "b", "c", "d", "e", "f"]}, {"secondary_colors": ["x" * 41]}, {"secondary_colors": [12]}])
def test_invalid_optional_traits_return_validation_errors(client, auth_headers, changes):
    response = client.post("/api/v1/pets", headers=auth_headers, json={"species": "dog", "name": "Prueba", **changes})
    assert response.status_code == 422


def test_custom_color_is_not_a_hard_contradiction_against_a_model_category():
    from app.matching.linked import compare_traits
    assert compare_traits({"primary_color": "gris azulado"}, {"primary_color": "gray"})[3] is False
    assert compare_traits({"primary_color": "black"}, {"primary_color": "white"})[3] is True


def test_secondary_color_search_handles_accents_and_literal_wildcards(client, auth_headers):
    pet, case = publish(client, auth_headers)
    assert client.patch(f"/api/v1/pets/{pet['id']}", headers=auth_headers, json={"secondary_colors": ["Marrón oscuro", "Gris metálico", "azul_10%"]}).status_code == 200
    path = "/api/v1/public/lost-animals"
    for color in ("brown", "Gris metálico", "azul_10%"):
        assert client.get(path, params={"color": color}).json()["total"] == 1
    assert client.get(path, params={"color": "verde%"}).json()["total"] == 0
