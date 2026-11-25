from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.models import CaseReview, User
from app.analysis.service import utcnow
from app.review_identity import abbreviated_name
from test_public_lost_dogs import publish
from test_product_analytics import promote


def retired_notice(client, headers):
    _, case = publish(client, headers)
    assert client.patch(f"/api/v1/lost-cases/{case['id']}", headers=headers, json={"status": "FOUND"}).status_code == 200
    return case


def review_payload(**changes):
    return {"rating": 4, "comment": "Una experiencia de prueba con MascoMatch.", "anonymous": False, "consent": True, **changes}


def set_name(client, headers, db_factory, name="Julian Molinelli"):
    identity = UUID(client.get("/api/v1/auth/me", headers=headers).json()["id"])
    with db_factory() as db:
        user = db.get(User, identity); user.name = name; db.commit()
    return identity


@pytest.mark.parametrize("name,expected", [("Julian Molinelli", "Julian M."), ("  María   Pérez  ", "María P."),
                                           ("Julian Molinelli Verzi", "Julian M."), ("Julian", "Julian")])
def test_review_names_use_the_account_and_never_expose_the_rest(name, expected):
    assert abbreviated_name(name) == expected


def test_next_recovery_reuses_and_edits_the_same_account_review(client, auth_headers, db_factory):
    author = set_name(client, auth_headers, db_factory)
    first = retired_notice(client, auth_headers)
    path = f"/api/v1/reviews/lost-cases/{first['id']}"
    response = client.post(path, headers=auth_headers, json=review_payload())
    assert response.status_code == 201, response.text
    original = response.json()
    assert original["display_name"] == "Julian M." and original["anonymous"] is False
    second = retired_notice(client, auth_headers)
    next_path = f"/api/v1/reviews/lost-cases/{second['id']}"
    state = client.get(next_path, headers=auth_headers).json()
    assert state["review"]["id"] == original["id"]
    assert state["account_display_name"] == "Julian M."
    assert client.post(next_path, headers=auth_headers, json=review_payload()).status_code == 409
    # Keeping it as-is is read-only, including its original creation date.
    assert client.get(next_path, headers=auth_headers).json()["review"] == state["review"]
    edited = client.patch(next_path, headers=auth_headers, json=review_payload(rating=5, comment="Actualizo mi experiencia después de otro reencuentro."))
    assert edited.status_code == 200, edited.text
    assert edited.json()["id"] == original["id"] and edited.json()["created_at"] == original["created_at"]
    assert client.get(path, headers=auth_headers).json()["review"]["rating"] == 5
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(CaseReview).where(CaseReview.author_id == author, CaseReview.is_current.is_(True))) == 1
    public = client.get("/api/v1/public/reviews").json()["items"]
    assert len(public) == 1 and public[0]["comment"] == edited.json()["comment"]


def test_own_account_review_can_be_managed_after_origin_is_reopened_or_removed(client, auth_headers):
    case = retired_notice(client, auth_headers)
    assert client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).status_code == 201
    assert client.patch(f"/api/v1/lost-cases/{case['id']}", headers=auth_headers, json={"status": "ACTIVE"}).status_code == 200
    assert len(client.get("/api/v1/public/reviews").json()["items"]) == 1
    assert client.delete(f"/api/v1/lost-cases/{case['id']}", headers=auth_headers).status_code == 204
    assert client.patch("/api/v1/reviews/me", headers=auth_headers, json=review_payload(anonymous=True)).status_code == 200
    assert client.get("/api/v1/reviews/me", headers=auth_headers).json()["review"]["display_name"] == "Anónimo"


@pytest.mark.parametrize("anonymous", [True, False])
def test_identity_and_avatar_follow_anonymity_without_leaking_account_details(client, auth_headers, db_factory, monkeypatch, anonymous):
    from app.routers import reviews
    author = set_name(client, auth_headers, db_factory)
    case = retired_notice(client, auth_headers)
    avatar_version = uuid4()
    with db_factory() as db:
        user = db.get(User, author); user.avatar_storage_key = "private-avatar.jpg"; user.avatar_version = avatar_version; db.commit()
    response = client.post(f"/api/v1/reviews/lost-cases/{case['id']}", headers=auth_headers, json=review_payload(anonymous=anonymous))
    assert response.status_code == 201
    item = client.get("/api/v1/public/reviews").json()["items"][0]
    assert item["display_name"] == ("Anónimo" if anonymous else "Julian M.")
    assert item["avatar_version"] == (None if anonymous else str(avatar_version))
    assert all(value not in str(item) for value in (str(author), "private-avatar.jpg", "owner@example.com", "Molinelli"))
    monkeypatch.setattr(reviews, "load_display_image", lambda *args: (b"clean-avatar", "image/jpeg"))
    image = client.get(f"/api/v1/public/reviews/{item['id']}/avatar")
    assert image.status_code == (404 if anonymous else 200)


def test_account_name_change_updates_the_public_abbreviation(client, auth_headers, db_factory):
    retired_notice(client, auth_headers)
    assert client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).status_code == 201
    set_name(client, auth_headers, db_factory, "Ana Pérez")
    assert client.get("/api/v1/public/reviews").json()["items"][0]["display_name"] == "Ana P."


@pytest.mark.parametrize("change", [{"display_name": "Un apodo"}, {"anonymous": "false"}, {"rating": True},
                                     {"rating": 6}, {"comment": "corto"}, {"consent": False}, {"consent": 1}])
def test_review_rejects_aliases_and_invalid_or_unconsented_edits(client, auth_headers, change):
    retired_notice(client, auth_headers)
    assert client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload(**change)).status_code == 422
    assert client.get("/api/v1/public/reviews").json()["items"] == []


def test_review_creation_requires_a_retired_own_notice_and_verified_account(client, auth_headers, db_factory):
    assert client.post("/api/v1/reviews/me", json=review_payload()).status_code == 401
    assert client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).status_code == 409
    _, case = publish(client, auth_headers)
    path = f"/api/v1/reviews/lost-cases/{case['id']}"
    assert client.post(path, headers=auth_headers, json=review_payload()).status_code == 409
    assert client.patch(f"/api/v1/lost-cases/{case['id']}", headers=auth_headers, json={"status": "FOUND"}).status_code == 200
    author = UUID(client.get("/api/v1/auth/me", headers=auth_headers).json()["id"])
    with db_factory() as db:
        db.get(User, author).email_verified_at = None; db.commit()
    assert client.post(path, headers=auth_headers, json=review_payload()).status_code == 403


def test_review_access_is_scoped_to_its_account_and_foreign_notices(client, auth_headers):
    case = retired_notice(client, auth_headers)
    path = f"/api/v1/reviews/lost-cases/{case['id']}"
    client.post(path, headers=auth_headers, json=review_payload())
    outsider = client.post("/api/v1/auth/register", json={"email": "review-outsider@example.test", "password": "a-strong-passphrase", "name": "Other"}).json()
    headers = {"Authorization": f"Bearer {outsider['access_token']}"}
    assert client.get("/api/v1/reviews/me", headers=headers).json()["review"] is None
    assert client.get(path, headers=headers).status_code == 404
    assert client.delete(path, headers=headers).status_code == 404
    assert client.patch(path, headers=headers, json=review_payload()).status_code == 403


def test_hidden_and_withdrawn_reviews_cannot_bypass_moderation_by_editing(client, auth_headers, db_factory):
    retired_notice(client, auth_headers)
    created = client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).json()
    promote(client, auth_headers, db_factory)
    moderation = f"/api/v1/admin/reviews/{created['id']}"
    assert client.patch(moderation, headers=auth_headers, json={"visibility": "HIDDEN"}).status_code == 200
    assert client.patch("/api/v1/reviews/me", headers=auth_headers, json=review_payload(comment="Mi comentario editado sigue pendiente de moderación.")).json()["visibility"] == "HIDDEN"
    assert client.delete("/api/v1/reviews/me", headers=auth_headers).status_code == 204
    assert client.patch(moderation, headers=auth_headers, json={"visibility": "VISIBLE"}).status_code == 409
    assert client.patch("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).json()["visibility"] == "HIDDEN"
    assert client.get("/api/v1/public/reviews").json()["items"] == []
    assert client.patch(moderation, headers=auth_headers, json={"visibility": "VISIBLE"}).status_code == 200
    assert len(client.get("/api/v1/public/reviews").json()["items"]) == 1


def test_withdrawal_can_be_reversed_only_by_the_author_with_explicit_consent(client, auth_headers):
    retired_notice(client, auth_headers)
    original = client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).json()
    assert client.delete("/api/v1/reviews/me", headers=auth_headers).status_code == 204
    assert client.get("/api/v1/public/reviews").json()["items"] == []
    assert client.get("/api/v1/reviews/me", headers=auth_headers).json()["review"]["comment"] == original["comment"]
    restored = client.patch("/api/v1/reviews/me", headers=auth_headers, json=review_payload(anonymous=True))
    assert restored.status_code == 200 and restored.json()["id"] == original["id"]
    assert restored.json()["visibility"] == "VISIBLE"


def test_historical_reviews_are_preserved_but_never_counted_or_republished(client, auth_headers, db_factory):
    author = set_name(client, auth_headers, db_factory)
    retired_notice(client, auth_headers)
    current = client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).json()
    other = retired_notice(client, auth_headers)
    with db_factory() as db:
        historical = CaseReview(author_id=author, lost_case_id=UUID(other["id"]), is_current=False,
            is_anonymous=True, display_name="Alias anterior privado", rating=2, comment="Comentario histórico que se conserva sin publicarlo.", consent_at=utcnow())
        db.add(historical); db.commit(); old_id = str(historical.id)
    assert [item["id"] for item in client.get("/api/v1/public/reviews").json()["items"]] == [current["id"]]
    assert client.get(f"/api/v1/public/reviews/{old_id}/avatar").status_code == 404
    promote(client, auth_headers, db_factory)
    records = client.get("/api/v1/admin/records/reviews", headers=auth_headers).json()["items"]
    assert len(records) == 2
    assert next(item for item in records if item["id"] == old_id)["is_current"] is False
    assert "Alias anterior privado" not in str(records)
    assert client.get("/api/v1/admin/overview", headers=auth_headers).json()["counts"]["case_reviews"] == 1
    assert client.patch(f"/api/v1/admin/reviews/{old_id}", headers=auth_headers, json={"visibility": "VISIBLE"}).status_code == 409


def test_account_review_disappears_for_a_blocked_or_unverified_author(client, auth_headers, db_factory):
    author = set_name(client, auth_headers, db_factory)
    retired_notice(client, auth_headers)
    assert client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).status_code == 201
    with db_factory() as db:
        db.get(User, author).status = "BLOCKED"; db.commit()
    assert client.get("/api/v1/public/reviews").json()["items"] == []
    with db_factory() as db:
        user = db.get(User, author); user.status = "ACTIVE"; user.email_verified_at = None; db.commit()
    assert client.get("/api/v1/public/reviews").json()["items"] == []


def test_deleting_the_account_removes_its_review_and_history(client, auth_headers, db_factory):
    author = set_name(client, auth_headers, db_factory)
    retired_notice(client, auth_headers)
    assert client.post("/api/v1/reviews/me", headers=auth_headers, json=review_payload()).status_code == 201
    previous = retired_notice(client, auth_headers)
    with db_factory() as db:
        db.add(CaseReview(author_id=author, lost_case_id=UUID(previous["id"]), is_current=False,
            display_name="Anónimo", rating=3, comment="Una reseña anterior conservada en el historial.", consent_at=utcnow()))
        db.commit()
    response = client.request("DELETE", "/api/v1/auth/me", headers=auth_headers,
        json={"password": "a-strong-passphrase", "confirmation": "ELIMINAR"})
    assert response.status_code == 204, response.text
    assert client.get("/api/v1/public/reviews").json()["items"] == []
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(CaseReview)) == 0
