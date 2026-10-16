"""Reclaim interrupted jobs during a controlled rollout, after stopping ALL workers/API."""
import argparse
import json
from sqlalchemy import select
from app.analysis.queue import get_queue,QUEUE_NAME
from app.analysis.service import utcnow
from app.db.session import SessionLocal
from app.models import AnalysisJob


def reclaim(factory=SessionLocal):
    count=0
    with factory() as db:
        for job in db.scalars(select(AnalysisJob).where(AnalysisJob.status.in_(["DISPATCHING","QUEUED","RUNNING"])).with_for_update()):
            job.status="PENDING"
            job.run_token=job.lease_expires_at=None
            job.dispatch_generation+=1
            job.available_at=utcnow()
            count+=1
        db.commit()
    return count


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers-stopped",action="store_true",required=True)
    parser.parse_args()
    count=reclaim()
    from rq import Queue
    from rq.serializers import JSONSerializer
    connection=get_queue().connection
    names=[QUEUE_NAME]+[f"{QUEUE_NAME}-{lane}-{tier}" for lane in ("visual","semantic") for tier in ("urgent","normal","backfill")]
    for name in names:
        Queue(name,connection=connection,serializer=JSONSerializer).empty()
    print(json.dumps({"reclaimed":count,"queues_reset":len(names)}))


if __name__=="__main__":
    main()
