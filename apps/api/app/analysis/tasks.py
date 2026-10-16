import asyncio
from datetime import timedelta, timezone
import json
from time import monotonic, process_time
from uuid import UUID, uuid4
from sqlalchemy import select
from app.analysis.providers import ProviderError, get_provider
from app.analysis.logging import log_event
from app.analysis.schemas import AnimalFeatures
from app.analysis.service import is_current, utcnow
from app.core.config import settings
from app.core.image_storage import load_analysis_image
from app.db.session import SessionLocal
from app.models import AnalysisJob, Embedding, FeatureSet

BACKOFF_SECONDS = (15,60,180,300)


def process_analysis(job_id: str,generation: int) -> str:
    identity=UUID(job_id)
    now=utcnow()
    with SessionLocal() as db:
        job=db.scalar(select(AnalysisJob).where(AnalysisJob.id==identity).with_for_update())
        if job is None or job.dispatch_generation!=generation:
            return "OBSOLETE"
        if job.status in ("SUCCEEDED","FAILED","STALE","RUNNING"):
            return job.status
        available=job.available_at.replace(tzinfo=timezone.utc) if job.available_at.tzinfo is None else job.available_at
        if job.status=="PENDING" and available>now:
            return "PENDING"
        if not (settings.embeddings_enabled if job.source_type=="embedding" else settings.ai_enabled):
            job.status,job.lease_expires_at="PENDING",None
            db.commit()
            return "DISABLED"
        if not is_current(db,job):
            job.status,job.finished_at,job.lease_expires_at="STALE",now,None
            db.commit()
            return "STALE"
        if job.attempts>=job.max_attempts:
            job.status,job.error_code,job.finished_at="FAILED","ATTEMPTS_EXHAUSTED",now
            db.commit()
            return "FAILED"
        job.status,job.started_at="RUNNING",now
        job.attempts+=1
        job.run_token=run_token=str(uuid4())
        job.lease_expires_at=now+timedelta(seconds=settings.timeout_for_source(job.source_type)+30)
        source,snapshot,provider_name,model=job.source_type,job.input_snapshot,job.provider,job.model
        owner_type,owner_id,photo_id=job.owner_type,job.owner_id,job.photo_id
        db.commit()

    started,cpu_started=monotonic(),process_time()
    failure=features=visual_result=provider=None
    metrics={}
    try:
        provider=get_provider(provider_name,model) if source!="embedding" else None
        if source in {"image","embedding"}:
            phase=monotonic()
            try:
                image,mime_type=load_analysis_image(snapshot["storage_key"],snapshot["mime_type"])
            except ValueError as exc:
                raise ProviderError("INVALID_IMAGE",retryable=False) from exc
            except Exception as exc:
                raise ProviderError("IMAGE_UNAVAILABLE") from exc
            metrics["load_image_ms"]=(monotonic()-phase)*1000
            phase=monotonic()
            if source=="embedding":
                from app.embeddings.provider import get_embedding_provider
                from app.embeddings.specs import EmbeddingSpec
                spec=EmbeddingSpec.from_dict(snapshot["spec"])
                visual_result=get_embedding_provider(spec).encode_result(image,snapshot["species"])
                if visual_result.spec!=spec:
                    raise ProviderError("EMBEDDING_SPEC_CHANGED",retryable=False)
                metrics.update(visual_result.metadata)
                metrics["visual_inference_ms"]=(monotonic()-phase)*1000
            else:
                from app.analysis.image_preprocessing import prepare_vlm_image
                from app.embeddings.cropper import PetCropper
                crop=None
                if settings.pet_crop_enabled and snapshot.get("species") in {"dog","cat"}:
                    # Reuse only current provenance for this same stored photo.
                    with SessionLocal() as db:
                        for embedding, visual_job in db.execute(select(Embedding,AnalysisJob).join(AnalysisJob,
                                Embedding.analysis_job_id==AnalysisJob.id).where(Embedding.photo_id==photo_id,
                                Embedding.provider=="pet_reid",AnalysisJob.status=="SUCCEEDED")):
                            if is_current(db,visual_job):
                                crop=embedding.quality
                                metrics["crop_reused"]=True
                                break
                    if crop is None:
                        _,crop=PetCropper().prepare(image,snapshot["species"])
                prepared=prepare_vlm_image(image,mime_type,crop_bbox=tuple(crop["bbox"]) if crop and crop.get("crop_used") else None,
                    crop_confidence=crop.get("detection_confidence") if crop else None,crop_margin=0)
                metrics.update(prepared.metadata)
                metrics["preprocess_image_ms"]=(monotonic()-phase)*1000
                features=asyncio.run(provider.analyze_image(prepared.data,prepared.mime_type))
        else:
            features=asyncio.run(provider.extract_observation(json.dumps(snapshot,ensure_ascii=False)))
        if source!="embedding":
            features=AnimalFeatures.model_validate(features.model_dump())
        if features and any(attribute.source!=source for attribute in features.__dict__.values()):
            raise ProviderError("INVALID_FEATURE_SOURCE",retryable=False)
    except ProviderError as exc:
        failure=exc
    except Exception as exc:
        from rq.timeouts import JobTimeoutException
        failure=ProviderError("PROVIDER_TIMEOUT" if isinstance(exc,JobTimeoutException) else "ANALYSIS_FAILED",
                              retryable=isinstance(exc,JobTimeoutException))
    if provider:
        metrics.update(getattr(provider,"last_metrics",{}))
    metrics.update(total_ms=(monotonic()-started)*1000,cpu_ms=(process_time()-cpu_started)*1000)
    phase=monotonic()
    with SessionLocal() as db:
        job=db.scalar(select(AnalysisJob).where(AnalysisJob.id==identity).with_for_update())
        if job is None or job.run_token!=run_token or job.status!="RUNNING":
            return "OBSOLETE"
        job.run_token,job.lease_expires_at=None,None
        if not is_current(db,job):
            job.status,job.finished_at="STALE",utcnow()
        elif failure:
            job.error_code=failure.code
            if failure.retryable and job.attempts<job.max_attempts:
                job.status="PENDING"
                job.available_at=utcnow()+timedelta(seconds=BACKOFF_SECONDS[min(job.attempts-1,len(BACKOFF_SECONDS)-1)])
            else:
                job.status,job.finished_at="FAILED",utcnow()
        else:
            if source=="embedding":
                if db.get(Embedding,identity) is None:
                    spec=visual_result.spec
                    db.add(Embedding(analysis_job_id=identity,photo_id=job.photo_id,model=spec.model,dimension=spec.dimension,
                        provider=spec.provider,revision=spec.revision,preprocessing_version=spec.preprocessing_version,
                        space_id=spec.space_id,input_hash=job.input_hash,vector=visual_result.vector,quality=visual_result.metadata))
            elif db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id==identity)) is None:
                db.add(FeatureSet(analysis_job_id=identity,features=features.model_dump(mode="json")))
            job.status,job.error_code,job.finished_at="SUCCEEDED",None,utcnow()
        metrics["persist_result_ms"]=(monotonic()-phase)*1000
        # Attempts are retained in bounded aggregate counters, no source text/images/tokens.
        prior=job.metrics or {}
        for key in ("retries","timeouts","invalid_responses","incomplete_responses"):
            metrics[key]=prior.get(key,0)
        if failure:
            metrics["retries"]+=int(job.status=="PENDING")
            metrics["timeouts"]+=int(failure.code in {"PROVIDER_TIMEOUT","EMBEDDING_TIMEOUT"})
            metrics["invalid_responses"]+=int(failure.code=="INVALID_FEATURE_RESPONSE")
            metrics["incomplete_responses"]+=int(failure.code=="INCOMPLETE_MODEL_RESPONSE")
        job.metrics=metrics
        db.commit()
        status=job.status
    log_event("analysis_finished",job_id=job_id,provider=provider_name,model=model,status=status,
              error_code=failure.code if failure else None,latency_ms=round(metrics["total_ms"]))
    phase=monotonic()
    try:
        from app.matching.engine import request_matching
        from app.matching.linked import mark_related_pending,reconcile_related
        with SessionLocal() as db:
            mark_related_pending(db,owner_type,owner_id)
            db.commit()
        reconcile_related(owner_type,owner_id,session_factory=SessionLocal)
    except Exception:
        log_event("linked_matching_deferred",job_id=job_id)
    with SessionLocal() as db:
        job=db.get(AnalysisJob,identity)
        if job:
            job.metrics={**job.metrics,"trigger_matching_ms":(monotonic()-phase)*1000}
            db.commit()
    return status
