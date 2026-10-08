"""Opt-in linked sighting -> real local vision -> private alert -> real local SMTP.

Uses a separate SQLite database and Redis queue. Emails go only to Mailpit.
"""
from datetime import timedelta
import os
from pathlib import Path
from uuid import uuid4

import httpx2 as httpx
import pytest
from rq import Queue, SpawnWorker
from rq.serializers import JSONSerializer
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.analysis import queue, tasks
from app.analysis.queue import get_queue
from app.analysis.service import utcnow
from app.core.config import settings
from app.core.image_storage import delete_private_image
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Notification, Observation, Photo
from app.notifications import email


@pytest.mark.skipif(os.getenv("RUN_LINKED_INTEGRATION") != "1", reason="Requires local Ollama, Redis, MinIO and Mailpit")
def test_linked_photo_notification_and_mailpit(client, tmp_path, monkeypatch):
    image_path = os.getenv("AI_SMOKE_IMAGE_PATH")
    assert image_path, "Set AI_SMOKE_IMAGE_PATH to the local demonstration dog image"
    image = Path(image_path).read_bytes()
    url = f"sqlite:///{tmp_path / 'linked.sqlite'}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def local_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = local_db
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setattr(queue, "SessionLocal", factory)
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    real_queue = get_queue()
    isolated = Queue(f"petmatch-linked-check-{uuid4().hex}", connection=real_queue.connection, serializer=JSONSerializer)
    monkeypatch.setattr(queue, "get_queue", lambda: isolated)
    recipient = f"linked-check-{uuid4().hex}@example.test"
    stored_keys = []
    try:
        owner = client.post("/api/v1/auth/register", json={"email": recipient, "password": "test-only-passphrase", "name": "Dueño de prueba"}).json()
        headers = {"Authorization": f"Bearer {owner['access_token']}"}
        pet = client.post("/api/v1/pets", headers=headers, json={"name": "Animal de prueba", "species": "dog"}).json()
        case = client.post("/api/v1/lost-cases", headers=headers, json={"pet_id": pet["id"], "description": "Aviso de prueba de integración", "lost_at": (utcnow() - timedelta(hours=2)).isoformat(), "latitude": -34.9, "longitude": -56.15}).json()
        no_photo = client.post(f"/api/v1/public/lost-animals/{case['id']}/sightings", data={"request_id": str(uuid4()), "observed_at": (utcnow() - timedelta(minutes=15)).isoformat(), "latitude": "-34.901", "longitude": "-56.151"})
        assert no_photo.status_code == 201
        assert no_photo.json()["status"] == "UNVERIFIED"
        monkeypatch.setattr(settings, "ai_enabled", True)
        target_photo = client.post("/api/v1/photos/upload", headers=headers, data={"owner_type": "lost_case", "owner_id": case["id"]}, files={"file": ("dog.jpg", image, "image/jpeg")})
        assert target_photo.status_code == 201
        stored_keys.append(target_photo.json()["photo"]["storage_key"])
        sighting = client.post(f"/api/v1/public/lost-animals/{case['id']}/sightings", data={"request_id": str(uuid4()), "observed_at": (utcnow() - timedelta(minutes=5)).isoformat(), "latitude": "-34.901", "longitude": "-56.151"}, files=[("photos", ("dog.jpg", image, "image/jpeg"))])
        assert sighting.status_code == 201, sighting.text
        assert sighting.json()["status"] == "PENDING"
        with factory() as db:
            stored_keys.extend(db.scalars(select(Photo.storage_key).where(Photo.owner_type == "observation")))
        assert queue.dispatch_pending() == 2
        engine.dispose()
        SpawnWorker([isolated], connection=isolated.connection, serializer=JSONSerializer).work(burst=True)
        with factory() as db:
            from uuid import UUID
            observation = db.get(Observation, UUID(sighting.json()["id"]))
            assert observation.matching_status == "POSSIBLE_MATCH", observation.matching_reasons
            assert db.scalar(select(Notification).where(Notification.observation_id == observation.id)) is not None
        inbox = client.get("/api/v1/notifications", headers=headers)
        assert inbox.status_code == 200
        assert inbox.json()["total"] == 2
        photo_notice = next(notice for notice in inbox.json()["items"] if notice["kind"] == "POSSIBLE_MATCH")
        image_url = f"/api/v1/notifications/{photo_notice['id']}/photos/{photo_notice['photo_ids'][0]}"
        assert client.get(image_url).status_code == 401
        image_response = client.get(image_url, headers=headers)
        assert image_response.status_code == 200
        assert image_response.headers["content-type"] == "image/jpeg"
        monkeypatch.setattr(settings, "mail_delivery_mode", "preview")
        monkeypatch.setattr(settings, "smtp_host", "mailpit")
        monkeypatch.setattr(settings, "smtp_port", 1025)
        monkeypatch.setattr(settings, "smtp_username", "")
        assert email.deliver_pending(factory) == 2
        assert email.deliver_pending(factory) == 0
        with factory() as db:
            assert all(item.email_status == "PREVIEWED" for item in db.scalars(select(Notification)))
        with httpx.Client(trust_env=False, timeout=10) as smtp_api:
            messages = smtp_api.get("http://mailpit:8025/api/v1/messages").json()["messages"]
            captured = [item for item in messages if any(address.get("Address") == recipient for address in item.get("To", []))]
            assert len(captured) == 2
            assert all("Posible avistamiento" in item["Subject"] for item in captured)
    finally:
        for key in stored_keys:
            delete_private_image(key)
        isolated.delete(delete_jobs=True)
        engine.dispose()
