from sqlalchemy import select
from app.analysis.service import input_hash, photo_snapshot, utcnow
from app.core.config import settings
from app.embeddings.provider import model_id, VERSION
from app.models import AnalysisJob


def schedule_embedding(db, photo):
    if not settings.embeddings_enabled:
        return None
    snapshot = photo_snapshot(photo)
    digest = input_hash(snapshot)
    key = input_hash({"source": "embedding", "photo": str(photo.id), "input": digest, "model": model_id(), "version": VERSION})
    existing = db.scalar(select(AnalysisJob).where(AnalysisJob.deduplication_key == key))
    if existing:
        return existing
    from sqlalchemy.exc import IntegrityError
    try:
        with db.begin_nested():
            job = AnalysisJob(deduplication_key=key, owner_type=photo.owner_type, owner_id=photo.owner_id, photo_id=photo.id,
                source_type="embedding", provider="open_clip", model=model_id(), prompt_version=VERSION,
                input_hash=digest, input_snapshot=snapshot, max_attempts=settings.ai_max_attempts, available_at=utcnow())
            db.add(job)
            db.flush()
        return job
    except IntegrityError:
        return db.scalar(select(AnalysisJob).where(AnalysisJob.deduplication_key == key))
