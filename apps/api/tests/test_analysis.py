import asyncio
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
from unittest.mock import AsyncMock
from uuid import UUID

import httpx2 as httpx
from PIL import Image
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.analysis import queue, tasks
from app.analysis.providers import ExtractionProvider, OllamaProvider, ProviderError
from app.analysis.schemas import AnimalFeatures, parse_extraction_output, parse_features
from app.analysis.service import schedule_text, utcnow
from app.core.config import Settings, settings
from app.models import AnalysisJob, FeatureSet, Observation


def evidence(source="text"):
    return parse_features(json.dumps({
        "species": {"value": "dog", "confidence": .96},
        "primary_color": {"value": "brown", "confidence": .9},
        "distinctive_features": {"value": ["pecho blanco"], "confidence": .85},
    }), source)


class FakeProvider(ExtractionProvider):
    def __init__(self, failure=None):
        self.calls = 0
        self.failure = failure

    async def extract_observation(self, text):
        self.calls += 1
        if self.failure:
            raise self.failure
        return evidence("text")

    async def analyze_image(self, image, mime_type):
        self.calls += 1
        assert mime_type == "image/jpeg"
        assert image
        return evidence("image")


def create_observation(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "ai_enabled", True)
    return client.post("/api/v1/observations", headers=auth_headers, json={
        "species": "dog", "description": "Perro marrón con pecho blanco",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }).json()["id"]


def owner_jobs(client, auth_headers, owner_id):
    response = client.get(f"/api/v1/analysis/observation/{owner_id}", headers=auth_headers)
    assert response.status_code == 200
    return response.json()["jobs"]


def bind_worker(monkeypatch, db_factory, provider):
    monkeypatch.setattr(tasks, "SessionLocal", db_factory)
    monkeypatch.setattr(tasks, "get_provider", lambda name, model: provider)


def test_schema_preserves_provenance_and_unknowns():
    features = evidence("image")
    assert features.primary_color.value == "brown"
    assert features.primary_color.source == "image"
    assert features.size.value == "unknown"
    assert features.size.confidence == 0
    assert all(attribute.source == "image" for attribute in features.__dict__.values())
    result = parse_features('{"species":{"value":"uncertain","confidence":0.9}}', "text")
    assert result.species.confidence == 0


@pytest.mark.parametrize("value,expected", [(["unknown"], "unknown"), (["not_visible"], "not_visible"), (["uncertain", "unknown"], "uncertain")])
def test_unknown_list_entries_are_not_physical_traits(value, expected):
    result = parse_features(json.dumps({"accessories": {"value": value, "confidence": .95}}), "text")
    assert result.accessories.value == expected
    assert result.accessories.confidence == 0


@pytest.mark.parametrize("content", [
    '{"species":{"value":"dragon","confidence":0.9}}',
    '{"size":{"value":"small","confidence":1.5}}',
    '{"size":{"value":"small","confidence":-0.1}}',
    '{"size":{"value":"small"}}',
    '{"extra":"invented"}', '[]', '```json\n{}\n```',
])
def test_invalid_features_are_rejected(content):
    with pytest.raises((ValueError, ValidationError)):
        parse_features(content, "text")


@pytest.mark.parametrize("kwargs", [
    {"ai_provider": "openai"}, {"ai_text_model": "gemma4:cloud"},
    {"ai_vision_model": "gemma4:31b-cloud"}, {"ollama_base_url": "https://ollama.com"},
    {"ollama_base_url": "http://127.0.0.1:11434@external.example"},
    {"ollama_base_url": "http://user:password@localhost:11434"},
])
def test_paid_or_external_providers_are_not_configurable(kwargs):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **kwargs)


@pytest.mark.parametrize("url", ["http://localhost:11434", "http://ollama:11434", "http://192.168.1.2:11434", "http://host.docker.internal:11434"])
def test_private_local_provider_configuration(url):
    assert Settings(_env_file=None, ollama_base_url=url).ollama_base_url == url


def test_analysis_is_disabled_without_configuration(client, auth_headers):
    record = client.post("/api/v1/observations", headers=auth_headers, json={
        "species": "dog", "description": "Perro marrón", "observed_at": utcnow().isoformat(),
    }).json()["id"]
    response = client.get(f"/api/v1/analysis/observation/{record}", headers=auth_headers).json()
    assert response == {"enabled": False, "jobs": []}
    assert client.post(f"/api/v1/analysis/observation/{record}", headers=auth_headers).status_code == 409


def test_automatic_text_analysis_is_private_and_deduplicated(client, auth_headers, monkeypatch):
    record = create_observation(client, auth_headers, monkeypatch)
    first = owner_jobs(client, auth_headers, record)
    second = client.post(f"/api/v1/analysis/observation/{record}", headers=auth_headers).json()["jobs"]
    assert len(first) == len(second) == 1
    assert first[0]["id"] == second[0]["id"]
    assert first[0]["status"] == "PENDING"
    assert "input_snapshot" not in first[0]
    assert client.get(f"/api/v1/analysis/observation/{record}").status_code == 401
    other = client.post("/api/v1/auth/register", json={"email": "other@example.com", "password": "another-passphrase", "name": "Other"}).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get(f"/api/v1/analysis/observation/{record}", headers=other_headers).status_code == 404
    assert client.get(f"/api/v1/analysis/jobs/{first[0]['id']}", headers=other_headers).status_code == 404
    assert client.post(f"/api/v1/analysis/jobs/{first[0]['id']}/retry", headers=other_headers).status_code == 404


def test_worker_is_idempotent_and_preserves_original_text(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    job_id = owner_jobs(client, auth_headers, record)[0]["id"]
    provider = FakeProvider()
    bind_worker(monkeypatch, db_factory, provider)
    assert tasks.process_analysis(job_id, 0) == "SUCCEEDED"
    assert tasks.process_analysis(job_id, 0) == "SUCCEEDED"
    assert provider.calls == 1
    job = owner_jobs(client, auth_headers, record)[0]
    assert job["feature_set"]["features"]["primary_color"]["value"] == "brown"
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(FeatureSet)) == 1
        assert db.get(Observation, UUID(record)).description == "Perro marrón con pecho blanco"


def test_changed_description_invalidates_old_results(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    first = owner_jobs(client, auth_headers, record)[0]["id"]
    provider = FakeProvider()
    bind_worker(monkeypatch, db_factory, provider)
    assert tasks.process_analysis(first, 0) == "SUCCEEDED"
    client.patch(f"/api/v1/observations/{record}", headers=auth_headers, json={"description": "Perro blanco pequeño"})
    jobs = owner_jobs(client, auth_headers, record)
    assert len(jobs) == 1 and jobs[0]["id"] != first
    assert jobs[0]["feature_set"] is None
    assert client.get(f"/api/v1/analysis/jobs/{first}", headers=auth_headers).json()["feature_set"] is None


def test_stale_pending_job_does_not_call_model(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    old_id = owner_jobs(client, auth_headers, record)[0]["id"]
    client.patch(f"/api/v1/observations/{record}", headers=auth_headers, json={"description": "Ahora se ve un gato"})
    provider = FakeProvider()
    bind_worker(monkeypatch, db_factory, provider)
    assert tasks.process_analysis(old_id, 0) == "STALE"
    assert provider.calls == 0


def test_provider_failure_has_bounded_backoff(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    job_id = owner_jobs(client, auth_headers, record)[0]["id"]
    provider = FakeProvider(ProviderError("PROVIDER_TIMEOUT"))
    bind_worker(monkeypatch, db_factory, provider)
    assert tasks.process_analysis(job_id, 0) == "PENDING"
    assert tasks.process_analysis(job_id, 0) == "PENDING"  # Duplicate delivery cannot bypass backoff.
    assert provider.calls == 1
    with db_factory() as db:
        job = db.get(AnalysisJob, UUID(job_id))
        assert job.attempts == 1
        assert job.available_at.replace(tzinfo=timezone.utc) > utcnow()
    for attempt in range(2, settings.ai_max_attempts + 1):
        with db_factory() as db:
            db.get(AnalysisJob, UUID(job_id)).available_at = utcnow() - timedelta(seconds=1)
            db.commit()
        status = tasks.process_analysis(job_id, 0)
    assert status == "FAILED"
    assert provider.calls == settings.ai_max_attempts
    assert client.post(f"/api/v1/analysis/jobs/{job_id}/retry", headers=auth_headers).status_code == 429
    with db_factory() as db:
        db.get(AnalysisJob, UUID(job_id)).finished_at = utcnow() - timedelta(seconds=61)
        db.commit()
    assert client.post(f"/api/v1/analysis/jobs/{job_id}/retry", headers=auth_headers).json()["status"] == "PENDING"


def test_missing_model_is_not_retried_automatically(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    job_id = owner_jobs(client, auth_headers, record)[0]["id"]
    provider = FakeProvider(ProviderError("MODEL_UNAVAILABLE", retryable=False))
    bind_worker(monkeypatch, db_factory, provider)
    assert tasks.process_analysis(job_id, 0) == "FAILED"
    assert tasks.process_analysis(job_id, 0) == "FAILED"
    assert provider.calls == 1


def test_photo_upload_schedules_image_analysis(client, auth_headers, monkeypatch, db_factory):
    from app.routers import photos
    record = create_observation(client, auth_headers, monkeypatch)
    monkeypatch.setattr(photos, "store_private_image", lambda *args: (f"observation/{record}/image.jpg", 2, 2))
    monkeypatch.setattr(photos, "create_download_url", lambda key: "http://localhost/signed")
    monkeypatch.setattr(photos, "delete_private_image", lambda key: None)
    image = BytesIO()
    Image.new("RGB", (2, 2), "brown").save(image, format="JPEG")
    response = client.post("/api/v1/photos/upload", headers=auth_headers,
                           data={"owner_type": "observation", "owner_id": record},
                           files={"file": ("dog.jpg", image.getvalue(), "image/jpeg")})
    assert response.status_code == 201
    jobs = owner_jobs(client, auth_headers, record)
    image_job = next(job for job in jobs if job["source_type"] == "image")
    provider = FakeProvider()
    bind_worker(monkeypatch, db_factory, provider)
    monkeypatch.setattr(tasks, "load_analysis_image", lambda *args: (image.getvalue(), "image/jpeg"))
    assert tasks.process_analysis(image_job["id"], 0) == "SUCCEEDED"
    result = client.get(f"/api/v1/analysis/jobs/{image_job['id']}", headers=auth_headers).json()
    assert result["feature_set"]["features"]["species"]["source"] == "image"
    assert client.delete(f"/api/v1/photos/{response.json()['photo']['id']}", headers=auth_headers).status_code == 204
    assert tasks.process_analysis(image_job["id"], 0) == "OBSOLETE"


def test_deleting_report_removes_analysis(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    job_id = owner_jobs(client, auth_headers, record)[0]["id"]
    bind_worker(monkeypatch, db_factory, FakeProvider())
    tasks.process_analysis(job_id, 0)
    assert client.delete(f"/api/v1/observations/{record}", headers=auth_headers).status_code == 204
    with db_factory() as db:
        assert db.get(AnalysisJob, UUID(job_id)) is None
        assert db.scalar(select(func.count()).select_from(FeatureSet)) == 0


def test_outbox_keeps_job_when_redis_is_unavailable(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    monkeypatch.setattr(queue, "SessionLocal", db_factory)

    class OfflineQueue:
        def enqueue(self, *args, **kwargs):
            raise ConnectionError("Redis unavailable")
    monkeypatch.setattr(queue, "get_queue", OfflineQueue)
    assert queue.dispatch_pending() == 0
    job = owner_jobs(client, auth_headers, record)[0]
    assert job["status"] == "PENDING" and job["error_code"] == "QUEUE_UNAVAILABLE"


def test_dispatch_is_unique_and_old_generation_cannot_run(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    job_id = owner_jobs(client, auth_headers, record)[0]["id"]
    monkeypatch.setattr(queue, "SessionLocal", db_factory)
    calls = []
    class RecordingQueue:
        def enqueue(self, *args, **kwargs):
            calls.append((args, kwargs))
    monkeypatch.setattr(queue, "get_queue", RecordingQueue)
    assert queue.dispatch_pending() == 1
    assert queue.dispatch_pending() == 0
    assert calls[0][1]["unique"] is True
    assert owner_jobs(client, auth_headers, record)[0]["status"] == "QUEUED"
    provider = FakeProvider()
    bind_worker(monkeypatch, db_factory, provider)
    assert tasks.process_analysis(job_id, 0) == "OBSOLETE"
    assert tasks.process_analysis(job_id, 1) == "SUCCEEDED"
    assert provider.calls == 1


def test_expired_worker_lease_is_recovered(client, auth_headers, monkeypatch, db_factory):
    record = create_observation(client, auth_headers, monkeypatch)
    job_id = owner_jobs(client, auth_headers, record)[0]["id"]
    with db_factory() as db:
        job = db.get(AnalysisJob, UUID(job_id))
        job.status, job.attempts, job.run_token = "RUNNING", 1, "old-run"
        job.lease_expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    monkeypatch.setattr(queue, "SessionLocal", db_factory)
    class RecordingQueue:
        def enqueue(self, *args, **kwargs):
            return None
    monkeypatch.setattr(queue, "get_queue", RecordingQueue)
    assert queue.dispatch_pending() == 1
    assert owner_jobs(client, auth_headers, record)[0]["status"] == "QUEUED"


@pytest.mark.parametrize("status,code,retryable", [(404, "MODEL_UNAVAILABLE", False), (401, "PROVIDER_AUTH_FAILED", False), (500, "PROVIDER_UNAVAILABLE", True)])
def test_ollama_http_errors_are_classified(monkeypatch, status, code, retryable):
    response = httpx.Response(status, request=httpx.Request("POST", "http://localhost:11434/api/chat"))
    monkeypatch.setattr(httpx.AsyncClient, "post", AsyncMock(return_value=response))
    with pytest.raises(ProviderError) as error:
        asyncio.run(OllamaProvider("local-model").extract_observation("perro marrón"))
    assert error.value.code == code and error.value.retryable == retryable


def test_ollama_uses_json_schema_without_auth_and_sends_base64_image(monkeypatch):
    features = evidence("image").model_dump(mode="json")
    raw = {name: item["value"] for name, item in features.items()}
    raw["confidence"] = {name: item["confidence"] for name, item in features.items()}
    response = httpx.Response(200, json={"done": True, "message": {"content": json.dumps(raw)}},
                              request=httpx.Request("POST", "http://localhost:11434/api/chat"))
    post = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    result = asyncio.run(OllamaProvider("local-model").analyze_image(b"image-bytes", "image/jpeg"))
    body = post.call_args.kwargs["json"]
    assert body["format"]["type"] == "object" and body["stream"] is False
    assert body["messages"][1]["images"] == ["aW1hZ2UtYnl0ZXM="]
    assert "headers" not in post.call_args.kwargs
    assert result.species.source == "image"


def test_compact_schema_keeps_per_attribute_confidence_and_source():
    features = evidence("text").model_dump(mode="json")
    raw = {name: item["value"] for name, item in features.items()}
    raw["confidence"] = {name: item["confidence"] for name, item in features.items()}
    parsed = parse_extraction_output(json.dumps(raw), "image")
    assert parsed.primary_color.value == "brown"
    assert parsed.primary_color.confidence == .9
    assert all(item.source == "image" for item in parsed.__dict__.values())
    del raw["confidence"]["species"]
    with pytest.raises(ValidationError):
        parse_extraction_output(json.dumps(raw), "image")


def test_supported_thinking_is_disabled_for_extraction(monkeypatch):
    features = evidence("text").model_dump(mode="json")
    raw = {name: item["value"] for name, item in features.items()}
    raw["confidence"] = {name: item["confidence"] for name, item in features.items()}
    request = httpx.Request("POST", "http://localhost:11434/api/chat")
    post = AsyncMock(side_effect=[httpx.Response(200, json={"capabilities": ["completion", "thinking"]}, request=request),
                                  httpx.Response(200, json={"done": True, "message": {"content": json.dumps(raw)}}, request=request)])
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    asyncio.run(OllamaProvider("local-model").extract_observation("perro marrón"))
    assert post.call_args.kwargs["json"]["think"] is False


def test_image_analysis_uses_a_small_clean_thumbnail(monkeypatch):
    from app.core import image_storage
    exif = Image.Exif()
    exif[0x010E] = "private note"
    original = BytesIO()
    Image.new("RGB", (2000, 1200), "brown").save(original, format="JPEG", exif=exif)
    stream = BytesIO(original.getvalue())
    class Storage:
        def get_object(self, **kwargs):
            return {"Body": stream}
    monkeypatch.setattr(image_storage, "_client", lambda endpoint: Storage())
    payload, mime = image_storage.load_analysis_image("photo.jpg", "image/jpeg")
    with Image.open(BytesIO(payload)) as image:
        assert max(image.size) == 1024
        assert image.getexif().get(0x010E) is None
        assert image.format == "JPEG"
    assert stream.closed and mime == "image/jpeg"


def test_lost_case_includes_pet_traits_without_duplicate_pet_analysis(client, auth_headers, monkeypatch, db_factory):
    monkeypatch.setattr(settings, "ai_enabled", True)
    pet = client.post("/api/v1/pets", headers=auth_headers, json={"name": "Luna", "species": "dog", "primary_color": "brown"}).json()
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(AnalysisJob)) == 0
    case = client.post("/api/v1/lost-cases", headers=auth_headers, json={"pet_id": pet["id"], "lost_at": utcnow().isoformat(), "description": "Pecho blanco"}).json()
    jobs = client.get(f"/api/v1/analysis/lost_case/{case['id']}", headers=auth_headers).json()["jobs"]
    assert len(jobs) == 1
    with db_factory() as db:
        snapshot = db.get(AnalysisJob, UUID(jobs[0]["id"])).input_snapshot
        assert snapshot["declared_features"]["primary_color"] == "brown"
        assert "name" not in snapshot["declared_features"]
        assert "microchip_reference" not in snapshot["declared_features"]
    client.patch(f"/api/v1/pets/{pet['id']}", headers=auth_headers, json={"primary_color": "black"})
    new_jobs = client.get(f"/api/v1/analysis/lost_case/{case['id']}", headers=auth_headers).json()["jobs"]
    assert len(new_jobs) == 1 and new_jobs[0]["id"] != jobs[0]["id"]
