from datetime import datetime, timedelta
from uuid import UUID

import pytest

from app.analysis.service import utcnow
from app.models import LostCase, Observation, Pet


def seed_points(client, auth_headers, db_factory, events):
    owner = UUID(client.get("/api/v1/auth/me", headers=auth_headers).json()["id"])
    result = []
    with db_factory() as db:
        for when, latitude, longitude in events:
            pet = Pet(owner_id=owner, name="Mascota de prueba", species="dog")
            db.add(pet)
            db.flush()
            case = LostCase(pet_id=pet.id, lost_at=when, latitude=latitude, longitude=longitude)
            observation = Observation(species="dog", description="Avistamiento de prueba", source_type="USER_SIGHTING",
                                      observed_at=when, latitude=latitude, longitude=longitude)
            db.add_all([case, observation])
            db.flush()
            result.append({str(case.id), str(observation.id)})
        db.commit()
    return result


def ids(response):
    assert response.status_code == 200, response.text
    return {point["id"] for point in response.json()["points"]}


def test_map_date_range_includes_whole_local_days_for_both_layers(client, auth_headers, db_factory):
    # Uruguay: 4 January starts at 03:00 UTC and ends just before 03:00 on 5 January.
    times = ["2024-01-04T02:59:59+00:00", "2024-01-04T03:00:00+00:00", "2024-01-05T02:59:59+00:00", "2024-01-05T03:00:00+00:00"]
    groups = seed_points(client, auth_headers, db_factory, [(datetime.fromisoformat(value), -34.9, -56.16) for value in times])
    response = client.get("/api/v1/public/map", params={"date_from": "2024-01-04", "date_to": "2024-01-04"})
    assert ids(response) == groups[1] | groups[2]
    assert response.headers["Cache-Control"] == "no-store"


def test_map_open_date_ranges_override_the_legacy_30_day_default(client, auth_headers, db_factory):
    times = ["2024-01-03T12:00:00+00:00", "2024-01-05T12:00:00+00:00"]
    groups = seed_points(client, auth_headers, db_factory, [(datetime.fromisoformat(value), -34.9, -56.16) for value in times])
    assert ids(client.get("/api/v1/public/map", params={"date_from": "2024-01-04"})) == groups[1]
    assert ids(client.get("/api/v1/public/map", params={"date_to": "2024-01-04"})) == groups[0]
    assert ids(client.get("/api/v1/public/map", params={"days": 0})) == groups[0] | groups[1]
    assert ids(client.get("/api/v1/public/map")) == set()


@pytest.mark.parametrize("params", [
    {"date_from": "2024-01-05", "date_to": "2024-01-04"},
    {"date_to": "9999-12-31"}, {"date_from": "2024-02-31"}, {"date_to": "invalid"},
    {"radius_km": -1}, {"radius_km": 501}, {"latitude": -34.9},
])
def test_map_rejects_invalid_filters(client, params):
    assert client.get("/api/v1/public/map", params=params).status_code == 422


def test_map_distance_zero_and_large_radius_filter_both_layers(client, auth_headers, db_factory):
    when = utcnow() - timedelta(hours=1)
    groups = seed_points(client, auth_headers, db_factory, [(when, -34.9, -56.16), (when, -34.91, -56.17), (when, -31.4, -57.9)])
    origin = {"latitude": -34.9, "longitude": -56.16, "days": 0}
    assert ids(client.get("/api/v1/public/map", params={**origin, "radius_km": 0})) == groups[0]
    assert ids(client.get("/api/v1/public/map", params={**origin, "radius_km": 2})) == groups[0] | groups[1]
    assert ids(client.get("/api/v1/public/map", params={**origin, "radius_km": 500})) == set().union(*groups)
    assert ids(client.get("/api/v1/public/map", params={"days": 0})) == set().union(*groups)
    for point in client.get("/api/v1/public/map", params={**origin, "radius_km": 2}).json()["points"]:
        assert point["latitude"] == round(point["latitude"], 2)
        assert point["longitude"] == round(point["longitude"], 2)
