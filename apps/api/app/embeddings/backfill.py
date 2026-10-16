"""Idempotent, resumable current-space backfill; never deletes historical vectors."""
import argparse
import json
from sqlalchemy import select,func
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Photo,AnalysisJob
from app.embeddings.service import schedule_embedding
from app.analysis.service import utcnow


def backfill(factory=SessionLocal, *, batch_size=100, retry_failed=False):
    if not settings.embeddings_enabled:
        raise ValueError("Enable EMBEDDINGS_ENABLED before scheduling backfill")
    last=None
    counts={"photos":0,"created":0,"existing":0,"retried":0}
    while True:
        with factory() as db:
            query=select(Photo).order_by(Photo.id).limit(batch_size)
            if last:
                query=query.where(Photo.id>last)
            photos=list(db.scalars(query))
            if not photos:
                break
            for photo in photos:
                before=db.scalar(select(func.count()).select_from(AnalysisJob).where(AnalysisJob.photo_id==photo.id,AnalysisJob.source_type=="embedding"))
                job=schedule_embedding(db,photo,priority=10)
                counts["photos"]+=1
                after=db.scalar(select(func.count()).select_from(AnalysisJob).where(AnalysisJob.photo_id==photo.id,AnalysisJob.source_type=="embedding"))
                counts["created" if after>before else "existing"]+=1
                if job and job.status in {"FAILED","STALE"} and retry_failed:
                    job.status,job.attempts,job.error_code="PENDING",0,None
                    job.available_at,job.finished_at=utcnow(),None
                    counts["retried"]+=1
            last=photos[-1].id
            db.commit()
    with factory() as db:
        counts["pending"]=db.scalar(select(func.count()).select_from(AnalysisJob).where(AnalysisJob.source_type=="embedding",AnalysisJob.status.in_(["PENDING","QUEUED","DISPATCHING","RUNNING"])))
    return counts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retry-failed",action="store_true")
    args=parser.parse_args()
    print(json.dumps(backfill(retry_failed=args.retry_failed)))


if __name__=="__main__":
    main()
