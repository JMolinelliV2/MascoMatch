from datetime import datetime, timezone
from io import BytesIO

from PIL import Image


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_login_and_duplicate_email(client):
    registration = client.post("/api/v1/auth/register", json={"email": "Person@Example.com", "password": "a-strong-passphrase", "name": "Person"})
    assert registration.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "a-strong-passphrase"})
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "person@example.com"
    duplicate = client.post("/api/v1/auth/register", json={"email": "person@example.com", "password": "a-strong-passphrase", "name": "Person"})
    assert duplicate.status_code == 409


def test_pet_and_lost_case_crud(client, auth_headers):
    assert client.get("/api/v1/pets").status_code == 401
    pet = client.post("/api/v1/pets", headers=auth_headers, json={"name": "Luna", "species": "dog", "primary_color": "brown", "distinctive_features": ["white chest"]})
    assert pet.status_code == 201
    pet_id = pet.json()["id"]
    assert pet.json()["breed"] == "unknown"
    assert client.get("/api/v1/pets", headers=auth_headers).json()[0]["name"] == "Luna"

    case = client.post("/api/v1/lost-cases", headers=auth_headers, json={
        "pet_id": pet_id,
        "lost_at": datetime.now(timezone.utc).isoformat(),
        "latitude": -34.7912,
        "longitude": -55.9545,
        "description": "Perdida cerca de la plaza",
    })
    assert case.status_code == 201
    case_id = case.json()["id"]
    updated = client.patch(f"/api/v1/lost-cases/{case_id}", headers=auth_headers, json={"status": "FOUND"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "FOUND"

    removed_case = client.delete(f"/api/v1/lost-cases/{case_id}", headers=auth_headers)
    assert removed_case.status_code == 204
    removed_pet = client.delete(f"/api/v1/pets/{pet_id}", headers=auth_headers)
    assert removed_pet.status_code == 204


def test_observation_without_photo_and_public_listing(client, auth_headers):
    response = client.post("/api/v1/observations", headers=auth_headers, json={
        "species": "dog",
        "description": "Perro marrón mediano con el pecho blanco",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "latitude": -34.79,
        "longitude": -55.95,
    })
    assert response.status_code == 201
    observation_id = response.json()["id"]
    public = client.get("/api/v1/observations")
    assert public.status_code == 200
    assert public.json()[0]["id"] == observation_id
    assert public.json()[0]["latitude"] == -34.79
    assert public.json()[0]["longitude"] == -55.95
    changed = client.patch(f"/api/v1/observations/{observation_id}", headers=auth_headers, json={"description": "Actualización"})
    assert changed.json()["description"] == "Actualización"


def test_coordinate_validation(client, auth_headers):
    response = client.post("/api/v1/observations", headers=auth_headers, json={
        "species": "cat",
        "description": "Gato visto",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "latitude": -34.79,
    })
    assert response.status_code == 422


def test_photo_metadata_crud_is_scoped_to_owner(client, auth_headers, monkeypatch):
    from app.routers import photos

    monkeypatch.setattr(photos, "delete_private_image", lambda key: None)
    pet = client.post("/api/v1/pets", headers=auth_headers, json={"name": "Luna", "species": "dog"}).json()
    created = client.post("/api/v1/photos", headers=auth_headers, json={
        "owner_type": "pet",
        "owner_id": pet["id"],
        "storage_key": f"pet/{pet['id']}/photo-1.jpg",
        "mime_type": "image/jpeg",
    })
    assert created.status_code == 201
    photo_id = created.json()["id"]
    listing = client.get(f"/api/v1/photos?owner_type=pet&owner_id={pet['id']}", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    updated = client.patch(f"/api/v1/photos/{photo_id}", headers=auth_headers, json={"width": 640, "height": 480})
    assert updated.json()["width"] == 640
    assert client.delete(f"/api/v1/photos/{photo_id}", headers=auth_headers).status_code == 204


def test_photo_upload_uses_private_storage_and_returns_signed_url(client, auth_headers, monkeypatch):
    from app.routers import photos

    pet = client.post("/api/v1/pets", headers=auth_headers, json={"name": "Luna", "species": "dog"}).json()
    monkeypatch.setattr(photos, "store_private_image", lambda owner_type, owner_id, mime_type, payload: ("pet/test/luna.jpg", 2, 2))
    monkeypatch.setattr(photos, "create_download_url", lambda key: "http://localhost:9000/pet-photos/signed")
    monkeypatch.setattr(photos, "delete_private_image", lambda key: None)
    image = BytesIO()
    Image.new("RGB", (2, 2), "brown").save(image, format="JPEG")

    uploaded = client.post(
        "/api/v1/photos/upload",
        headers=auth_headers,
        data={"owner_type": "pet", "owner_id": pet["id"]},
        files={"file": ("luna.jpg", image.getvalue(), "image/jpeg")},
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["photo"]["width"] == 2
    assert uploaded.json()["signed_url"].endswith("/signed")
    photo_id = uploaded.json()["photo"]["id"]
    assert client.get(f"/api/v1/photos/{photo_id}/url", headers=auth_headers).json()["expires_in_seconds"] == 900
    assert client.delete(f"/api/v1/photos/{photo_id}", headers=auth_headers).status_code == 204


def test_image_cleaning_strips_exif_metadata():
    from app.core.image_storage import _clean_image

    exif = Image.Exif()
    exif[0x010E] = "private camera note"
    original = BytesIO()
    Image.new("RGB", (10, 20), "brown").save(original, format="JPEG", exif=exif)
    clean_bytes, width, height, suffix = _clean_image(original.getvalue(), "image/jpeg")
    clean = Image.open(BytesIO(clean_bytes))

    assert (width, height, suffix) == (10, 20, "jpg")
    assert clean.getexif().get(0x010E) is None

