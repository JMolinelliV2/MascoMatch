"""Opt-in check against real local Redis/RQ and Ollama, with an isolated database."""
import os
from pathlib import Path
from uuid import uuid4

import pytest
from rq import SpawnWorker
from rq.serializers import JSONSerializer
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.analysis import queue, tasks
from app.analysis.queue import get_queue
from app.analysis.service import schedule_photo, schedule_text, utcnow
from app.core.config import settings
from app.core.image_storage import delete_private_image, store_private_image
from app.db.base import Base
from app.models import AnalysisJob, FeatureSet, Observation, Photo


@pytest.mark.skipif(os.getenv("RUN_LOCAL_AI_TESTS") != "1", reason="Requires an explicitly enabled local Ollama and Redis")
def test_real_queue_worker_and_local_model(tmp_path, monkeypatch):
    # A separate SQLite file avoids touching the user's application database.
    database_url = f"sqlite:///{tmp_path / 'analysis.sqlite'}"
    factory = sessionmaker(bind=create_engine(database_url))
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("AI_ENABLED", "true")
    Base.metadata.create_all(factory.kw["bind"])
    monkeypatch.setattr(settings, "ai_enabled", True)
    monkeypatch.setattr(queue, "SessionLocal", factory)
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    real_queue = get_queue()
    from rq import Queue
    isolated_queue = Queue(f"petmatch-check-{uuid4().hex}", connection=real_queue.connection, serializer=JSONSerializer)
    monkeypatch.setattr(queue, "get_queue", lambda: isolated_queue)
    storage_key = None
    try:
        with factory() as db:
            observation = Observation(species="dog", description="Era un perro de color chocolate, tamaño mediano; tenía una mancha blanca en el pecho y llevaba un collar rojo.", observed_at=utcnow())
            db.add(observation)
            db.flush()
            job = schedule_text(db, "observation", observation.id)
            job_id = job.id
            negative = Observation(species="cat", description="Vi un gato negro. No tenía collar ni manchas blancas en el pecho.", observed_at=utcnow())
            db.add(negative)
            db.flush()
            negative_job_id = schedule_text(db, "observation", negative.id).id
            image_path = os.getenv("AI_SMOKE_IMAGE_PATH")
            photo_id = None
            if image_path:
                storage_key, width, height = store_private_image("observation", observation.id, "image/jpeg", Path(image_path).read_bytes())
                photo = Photo(owner_type="observation", owner_id=observation.id,
                              storage_key=storage_key, mime_type="image/jpeg", width=width, height=height)
                db.add(photo)
                db.flush()
                photo_id = schedule_photo(db, photo).id
            db.commit()
        assert queue.dispatch_pending() == (3 if photo_id else 2)
        factory.kw["bind"].dispose()
        SpawnWorker([isolated_queue], connection=isolated_queue.connection, serializer=JSONSerializer).work(burst=True)
        with factory() as db:
            job = db.get(AnalysisJob, job_id)
            assert job.status == "SUCCEEDED", job.error_code
            features = db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id == job_id)).features
            assert features["species"]["value"] == "dog"
            assert features["primary_color"]["value"] == "brown"
            assert features["size"]["value"] == "medium"
            assert features["breed_type"]["value"] == "unknown"
            assert features["distinctive_features"]["value"] not in ("unknown", "not_visible", "uncertain")
            assert db.get(AnalysisJob, negative_job_id).status == "SUCCEEDED"
            negative_features = db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id == negative_job_id)).features
            assert negative_features["species"]["value"] == "cat"
            assert negative_features["primary_color"]["value"] == "black"
            assert negative_features["accessories"]["value"] in ([], "unknown", "not_visible", "uncertain")
            assert negative_features["distinctive_features"]["value"] in ([], "unknown", "not_visible", "uncertain")
            if photo_id:
                photo_job = db.get(AnalysisJob, photo_id)
                assert photo_job.status == "SUCCEEDED", photo_job.error_code
                image_features = db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id == photo_id)).features
                assert image_features["species"]["source"] == "image"
                assert image_features["species"]["value"] == "dog"
    finally:
        if storage_key:
            delete_private_image(storage_key)
        # This queue contains only jobs created by this test.
        isolated_queue.delete(delete_jobs=True)
        factory.kw["bind"].dispose()
