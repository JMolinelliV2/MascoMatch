from uuid import UUID, uuid4
import json

import pytest
from sqlalchemy import select

from app.matching import linked
from app.models import FoundReportContact, LostCase, Match, Notification, Observation, User
from app.notifications import email
from test_linked_sightings import lost_notice, mock_storage, submit


def payload(**changes):
    return {"request_id": str(uuid4()), "source_type": "FOUND_ANIMAL", "finder_name": "Persona Privada Prueba",
            "finder_phone": "+598 98 765 432", "description": "Tiene una mancha blanca en el pecho y un collar violeta.",
            "details": json.dumps({"breed": "Mestizo", "primary_color": "brown", "collar_status": "yes", "collar_color": "Violeta"}), **changes}


def photos():
    return [("photos", ("found.jpg", b"photo", "image/jpeg"))]


def found_report(client, auth_headers, monkeypatch):
    _, case = lost_notice(client, auth_headers)
    mock_storage(monkeypatch)
    data = payload()
    response = submit(client, case, data, files=photos())
    assert response.status_code == 201, response.text
    candidate = client.get(f"/api/v1/matches/lost-cases/{case['id']}", headers=auth_headers).json()["items"][0]
    return case, data, response.json(), candidate["match"]["id"]


def test_anonymous_custody_report_needs_no_location_or_discovery_time(client, auth_headers, db_factory, monkeypatch):
    case, data, result, match_id = found_report(client, auth_headers, monkeypatch)
    assert result["owner_notified"] is True
    assert result["status"] == "UNVERIFIED"
    with db_factory() as db:
        observation = db.get(Observation, UUID(result["id"]))
        assert observation.author_id is None
        assert observation.latitude is observation.longitude is observation.public_location is None
        assert observation.description == data["description"]
        contact = db.get(FoundReportContact, observation.id)
        assert contact.name == data["finder_name"] and contact.phone == data["finder_phone"]
    assert submit(client, case, data, files=photos()).json() == result
    assert submit(client, case, {**data, "finder_phone": "+598 99 555 555"}, files=photos()).status_code == 409
    notice = client.get("/api/v1/notifications", headers=auth_headers).json()["items"][0]
    assert notice["description"] == data["description"]
    assert notice["pet_details"]["breed"] == "Mestizo"
    assert notice["pet_details"]["collar_color"] == "Violeta"
    assert len(notice["photo_ids"]) == 1
    assert notice["reporter_contact"] is None
    assert client.get(f"/api/v1/matches/{match_id}/reporter-contact", headers=auth_headers).status_code == 403


@pytest.mark.parametrize("change,with_photo", [
    ({"finder_name": " "}, True), ({"finder_name": "123"}, True), ({"finder_phone": "abc"}, True),
    ({"finder_phone": "+598 123"}, True), ({"description": " "}, True), ({}, False),
])
def test_custody_requires_real_contact_pet_description_and_photo(client, auth_headers, monkeypatch, change, with_photo):
    _, case = lost_notice(client, auth_headers)
    mock_storage(monkeypatch)
    response = submit(client, case, payload(**change), files=photos() if with_photo else None)
    assert response.status_code == 422
    assert client.get("/api/v1/notifications", headers=auth_headers).json()["total"] == 0


def test_discovery_location_and_date_never_reject_a_custody_report(client, auth_headers, db_factory, monkeypatch):
    _, case = lost_notice(client, auth_headers)
    mock_storage(monkeypatch)
    response = submit(client, case, payload(latitude="45", longitude="12", public_location="Far away", observed_at="2000-01-01T00:00:00Z"), files=photos())
    assert response.status_code == 201
    assert response.json()["owner_notified"] and response.json()["status"] == "UNVERIFIED"
    with db_factory() as db:
        observation = db.get(Observation, UUID(response.json()["id"]))
        assert observation.latitude is observation.longitude is observation.public_location is None
        assert not any("radio" in reason or "Falta una ubicación" in reason for reason in observation.matching_reasons)


def test_only_the_notice_owner_after_identity_confirmation_can_read_contact(client, auth_headers, db_factory, monkeypatch):
    case, data, result, match_id = found_report(client, auth_headers, monkeypatch)
    path = f"/api/v1/matches/{match_id}/reporter-contact"
    feedback = f"/api/v1/matches/{match_id}/feedback"
    assert client.get(path).status_code == 401
    stranger = client.post("/api/v1/auth/register", json={"email": "outsider@example.test", "password": "a-strong-passphrase", "name": "Other"}).json()
    stranger_headers = {"Authorization": f"Bearer {stranger['access_token']}"}
    assert client.get(path, headers=stranger_headers).status_code == 404
    assert client.patch(feedback, headers=stranger_headers, json={"status": "RESOLVED"}).status_code == 404
    assert client.patch(feedback, headers=auth_headers, json={"status": "CONFIRMED_RELEVANT"}).status_code == 200
    assert client.get(path, headers=auth_headers).status_code == 403
    assert client.patch(feedback, headers=auth_headers, json={"status": "RESOLVED"}).status_code == 200
    contact = client.get(path, headers=auth_headers)
    assert contact.status_code == 200
    assert contact.headers["cache-control"] == "private, no-store"
    assert contact.json() == {"contact": {"name": data["finder_name"], "phone": data["finder_phone"]}}
    assert client.get(path, headers=stranger_headers).status_code == 404
    with db_factory() as db:
        assert db.get(LostCase, UUID(case["id"])).status == "ACTIVE"
        assert linked.evaluate_sighting(db, UUID(result["id"])) == "UNVERIFIED"
        db.commit()
        assert db.scalar(select(Notification).where(Notification.observation_id == UUID(result["id"]))).is_active
    assert client.get(path, headers=auth_headers).json() == contact.json()
    assert client.patch(feedback, headers=auth_headers, json={"status": "FALSE_MATCH"}).status_code == 200
    assert client.get(path, headers=auth_headers).status_code == 403


def test_contact_is_not_in_public_status_notification_candidates_or_email_payloads(client, auth_headers, db_factory, monkeypatch):
    case, data, result, match_id = found_report(client, auth_headers, monkeypatch)
    paths = [f"/api/v1/public/observations/{result['id']}", f"/api/v1/observations/{result['id']}",
             f"/api/v1/public/lost-animals/{case['id']}/sightings/{result['id']}/status",
             f"/api/v1/matches/lost-cases/{case['id']}", "/api/v1/notifications"]
    for path in paths:
        response = client.get(path, headers=auth_headers)
        assert response.status_code == 200, (path, response.text)
        assert data["finder_name"] not in response.text and data["finder_phone"] not in response.text
    with db_factory() as db:
        notice = db.scalar(select(Notification).where(Notification.observation_id == UUID(result["id"])))
        message = email.build_message(notice, db.get(User, notice.owner_id), db.get(Observation, UUID(result["id"])))
        assert data["description"] in message.get_body(preferencelist=("plain",)).get_content()
        for part in message.iter_parts():
            if part.get_content_maintype() == "text":
                assert data["finder_name"] not in part.get_content() and data["finder_phone"] not in part.get_content()


def test_hidden_report_cannot_reveal_contact_even_after_confirmation(client, auth_headers, db_factory, monkeypatch):
    _, _, result, match_id = found_report(client, auth_headers, monkeypatch)
    assert client.patch(f"/api/v1/matches/{match_id}/feedback", headers=auth_headers, json={"status": "RESOLVED"}).status_code == 200
    with db_factory() as db:
        db.get(Observation, UUID(result["id"])).moderation_status = "HIDDEN"
        db.commit()
    assert client.get(f"/api/v1/matches/{match_id}/reporter-contact", headers=auth_headers).status_code == 404


def test_account_email_never_bypasses_confirmation_and_deletion_removes_finder_contact(client, auth_headers, confirm_account, db_factory, monkeypatch):
    _, case = lost_notice(client, auth_headers)
    mock_storage(monkeypatch)
    account = client.post("/api/v1/auth/register", json={"email": "finder-private@example.test", "password": "a-strong-passphrase", "name": "Finder Private"}).json()
    confirm_account("finder-private@example.test")
    finder_headers = {"Authorization": f"Bearer {account['access_token']}"}
    response = submit(client, case, payload(), files=photos(), headers=finder_headers)
    assert response.status_code == 201
    identity = UUID(response.json()["id"])
    # A retained legacy opt-in cannot expose the account email in this new flow.
    with db_factory() as db:
        db.get(Observation, identity).share_contact = True
        db.commit()
    notice = client.get("/api/v1/notifications", headers=auth_headers).json()["items"][0]
    assert notice["reporter_contact"] is None
    assert client.get(f"/api/v1/public/observations/{identity}").json()["publisher_name"] is None
    assert client.request("DELETE", "/api/v1/auth/me", headers=finder_headers, json={"password": "a-strong-passphrase", "confirmation": "ELIMINAR"}).status_code == 204
    with db_factory() as db:
        assert db.get(FoundReportContact, identity) is None
        assert db.get(Observation, identity).author_id is None
