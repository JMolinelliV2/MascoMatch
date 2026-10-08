import asyncio
from datetime import timedelta, timezone
import json
from time import monotonic
from uuid import UUID, uuid4

from sqlalchemy import select

from app.analysis.providers import ProviderError, get_provider
from app.analysis.logging import log_event
from app.analysis.schemas import AnimalFeatures
from app.analysis.service import is_current, utcnow
from app.core.config import settings
from app.core.image_storage import load_analysis_image
from app.db.session import SessionLocal
from app.models import AnalysisJob, FeatureSet

BACKOFF_SECONDS = (15, 60, 180, 300)


def process_analysis(job_id: str, generation: int) -> str:
    identity = UUID(job_id)
    now = utcnow()
    with SessionLocal() as db:
        job = db.scalar(select(AnalysisJob).where(AnalysisJob.id == identity).with_for_update())
        if job is None or job.dispatch_generation != generation:
            return "OBSOLETE"
        if job.status in ("SUCCEEDED", "FAILED", "STALE", "RUNNING"):
            return job.status
        available = job.available_at.replace(tzinfo=timezone.utc) if job.available_at.tzinfo is None else job.available_at
        if job.status == "PENDING" and available > now:
            return "PENDING"
        if not settings.ai_enabled:
            job.status, job.lease_expires_at = "PENDING", None
            db.commit()
            return "DISABLED"
        if not is_current(db, job):
            job.status, job.finished_at, job.lease_expires_at = "STALE", now, None
            db.commit()
            return "STALE"
        if job.attempts >= job.max_attempts:
            job.status, job.error_code, job.finished_at = "FAILED", "ATTEMPTS_EXHAUSTED", now
            db.commit()
            return "FAILED"
        job.status, job.started_at = "RUNNING", now
        job.attempts += 1
        job.run_token = run_token = str(uuid4())
        job.lease_expires_at = now + timedelta(seconds=settings.ai_job_timeout_seconds + 30)
        source, snapshot, provider_name, model = job.source_type, job.input_snapshot, job.provider, job.model
        owner_type, owner_id = job.owner_type, job.owner_id
        db.commit()

    started = monotonic()
    failure: ProviderError | None = None
    features: AnimalFeatures | None = None
    try:
        provider = get_provider(provider_name, model)
        if source == "image":
            try:
                image, mime_type = load_analysis_image(snapshot["storage_key"], snapshot["mime_type"])
            except Exception as exc:
                raise ProviderError("IMAGE_UNAVAILABLE") from exc
            features = asyncio.run(provider.analyze_image(image, mime_type))
        else:
            features = asyncio.run(provider.extract_observation(json.dumps(snapshot, ensure_ascii=False)))
        # Enforce the common contract for every provider implementation.
        features = AnimalFeatures.model_validate(features.model_dump())
        if any(attribute.source != source for attribute in features.__dict__.values()):
            raise ProviderError("INVALID_FEATURE_SOURCE", retryable=False)
    except ProviderError as exc:
        failure = exc
    except Exception:
        failure = ProviderError("ANALYSIS_FAILED")

    with SessionLocal() as db:
        job = db.scalar(select(AnalysisJob).where(AnalysisJob.id == identity).with_for_update())
        if job is None or job.run_token != run_token or job.status != "RUNNING":
            return "OBSOLETE"
        job.run_token, job.lease_expires_at = None, None
        if not is_current(db, job):
            job.status, job.finished_at = "STALE", utcnow()
        elif failure is not None:
            job.error_code = failure.code
            if failure.retryable and job.attempts < job.max_attempts:
                job.status = "PENDING"
                job.available_at = utcnow() + timedelta(seconds=BACKOFF_SECONDS[min(job.attempts - 1, len(BACKOFF_SECONDS) - 1)])
            else:
                job.status, job.finished_at = "FAILED", utcnow()
        else:
            result = db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id == identity))
            if result is None:
                db.add(FeatureSet(analysis_job_id=identity, features=features.model_dump(mode="json")))
            job.status, job.error_code, job.finished_at = "SUCCEEDED", None, utcnow()
        db.commit()
        status = job.status
    log_event("analysis_finished", job_id=job_id, provider=provider_name, model=model,
              status=status, error_code=failure.code if failure else None, latency_ms=round((monotonic() - started) * 1000))
    try:
        from app.matching.linked import reconcile_related
        reconcile_related(owner_type, owner_id, session_factory=SessionLocal)
    except Exception:
        # The API's durable pending reconciler recovers an interruption after analysis commits.
        log_event("linked_matching_deferred", job_id=job_id)
    return status
