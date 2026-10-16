from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.analysis.service import input_hash, photo_snapshot, utcnow
from app.core.config import settings
from app.embeddings.specs import photo_species, spec_for_photo
from app.models import AnalysisJob, Photo


def embedding_snapshot(db, photo):
    spec = spec_for_photo(db, photo)
    if spec is None:
        return None
    return {**photo_snapshot(photo), "species": photo_species(db, photo), "spec": spec.to_dict()}


def is_current_embedding(db, job):
    photo = db.get(Photo, job.photo_id) if job.photo_id else None
    if photo is None or photo.owner_type != job.owner_type or photo.owner_id != job.owner_id:
        return False
    snapshot = embedding_snapshot(db, photo)
    return snapshot is not None and input_hash(snapshot) == job.input_hash


def schedule_embedding(db, photo, *, priority=None):
    if not settings.embeddings_enabled:
        return None
    snapshot = embedding_snapshot(db, photo)
    if snapshot is None:
        return None
    spec = spec_for_photo(db, photo)
    digest = input_hash(snapshot)
    key = input_hash({"source":"embedding", "photo":str(photo.id), "input":digest, "spec":spec.to_dict()})
    existing = db.scalar(select(AnalysisJob).where(AnalysisJob.deduplication_key == key))
    if existing is not None:
        if priority is not None and existing.status == "PENDING":
            existing.priority = max(existing.priority, priority)
        return existing
    from app.analysis.service import owner_priority
    try:
        with db.begin_nested():
            job = AnalysisJob(deduplication_key=key, owner_type=photo.owner_type, owner_id=photo.owner_id, photo_id=photo.id,
                source_type="embedding", provider=spec.provider, model=spec.model, prompt_version="visual-v2",
                preprocessing_version=spec.preprocessing_version, input_hash=digest, input_snapshot=snapshot,
                priority=priority if priority is not None else owner_priority(db,photo.owner_type,photo.owner_id),
                max_attempts=settings.ai_max_attempts, available_at=utcnow())
            db.add(job)
            db.flush()
        return job
    except IntegrityError:
        return db.scalar(select(AnalysisJob).where(AnalysisJob.deduplication_key == key))