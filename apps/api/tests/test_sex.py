from datetime import datetime, timezone

import pytest


@pytest.mark.parametrize("sex", ["male", "female", "unknown"])
@pytest.mark.parametrize("source_type", ["USER_SIGHTING", "FOUND_ANIMAL"])
def test_observation_persists_sex_and_can_be_edited(client, auth_headers, sex, source_type):
    response = client.post("/api/v1/observations", headers=auth_headers, json={
        "species": "dog", "sex": sex, "source_type": source_type,
        "description": "Perro visto", "observed_at": datetime.now(timezone.utc).isoformat(),
    })
    assert response.status_code == 201
    assert response.json()["sex"] == sex
    path = f"/api/v1/observations/{response.json()['id']}"
    assert client.get(path).json()["sex"] == sex
    updated = client.patch(path, headers=auth_headers, json={"sex": "female"})
    assert updated.status_code == 200
    assert updated.json()["sex"] == "female"
    assert client.get("/api/v1/observations").json()[0]["sex"] == "female"


def test_sex_defaults_to_unknown_when_omitted(client, auth_headers):
    pet = client.post("/api/v1/pets", headers=auth_headers, json={"name": "Luna", "species": "dog"})
    assert pet.json()["sex"] == "unknown"
    observation = client.post("/api/v1/observations", headers=auth_headers, json={
        "species": "dog", "description": "Animal visto", "observed_at": datetime.now(timezone.utc).isoformat(),
    })
    assert observation.json()["sex"] == "unknown"


@pytest.mark.parametrize("invalid", ["other", "masculino", None])
def test_invalid_sex_is_rejected_on_create_and_update(client, auth_headers, invalid):
    pet_data = {"name": "Luna", "species": "dog"}
    obs_data = {"species": "dog", "description": "Animal visto", "observed_at": datetime.now(timezone.utc).isoformat()}
    for route, data in (("pets", pet_data), ("observations", obs_data)):
        path = f"/api/v1/{route}"
        assert client.post(path, headers=auth_headers, json={**data, "sex": invalid}).status_code == 422
        item = client.post(path, headers=auth_headers, json=data).json()
        assert client.patch(f"{path}/{item['id']}", headers=auth_headers, json={"sex": invalid}).status_code == 422
