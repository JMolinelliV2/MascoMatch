"""Minimal public health and token-protected operational metrics."""
from datetime import datetime, timezone
import hmac
import urllib.request
from app.core.image_storage import _client
from fastapi import APIRouter, Header, HTTPException, Response
from redis import Redis
from sqlalchemy import select, func, text
from app.analysis.service import utcnow
from app.core.config import settings
from app.db.session import SessionLocal
from app.matching.linked import aware
from app.models import AccountToken, AnalysisJob, Notification

router = APIRouter(tags=["operations"])


def readiness():
    checks = {"database":False, "queue":False, "photos":False}
    try:
        with SessionLocal() as db:
            checks["database"] = db.scalar(text("SELECT 1")) == 1
    except Exception:
        pass
    try:
        with Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2) as redis:
            checks["queue"] = bool(redis.ping())
    except Exception:
        pass
    try:
        _client(settings.s3_endpoint).head_bucket(Bucket=settings.s3_bucket)
        checks["photos"] = True
    except Exception:
        pass
    return checks


@router.get("/health/ready")
def ready():
    checks = readiness()
    ok = all(checks.values())
    return Response('{"status":"' + ("ok" if ok else "unavailable") + '"}',
                    status_code=200 if ok else 503, media_type="application/json", headers={"Cache-Control":"no-store"})


@router.get("/internal/metrics", include_in_schema=False)
def metrics(authorization: str | None = Header(default=None)):
    secret = settings.metrics_token.get_secret_value()
    if not secret or not authorization or not hmac.compare_digest(authorization.encode(), ("Bearer " + secret).encode()):
        raise HTTPException(status_code=404, detail="Not found")
    values = {"mascomatch_ready":float(all(readiness().values())),
              "mascomatch_email_enabled":float(settings.mail_delivery_mode == "smtp")}
    try:
        with SessionLocal() as db:
            values["mascomatch_analysis_failed"] = db.scalar(select(func.count()).select_from(AnalysisJob).where(AnalysisJob.status == "FAILED"))
            values["mascomatch_analysis_pending"] = db.scalar(select(func.count()).select_from(AnalysisJob).where(AnalysisJob.status.in_(["PENDING","DISPATCHING","QUEUED","RUNNING"])))
            oldest = db.scalar(select(func.min(AnalysisJob.created_at)).where(AnalysisJob.status.in_(["PENDING","DISPATCHING","QUEUED","RUNNING"])))
            values["mascomatch_analysis_oldest_seconds"] = max(0, (utcnow()-aware(oldest)).total_seconds()) if oldest else 0
            values["mascomatch_email_failed"] = db.scalar(select(func.count()).select_from(Notification).where(Notification.email_status == "FAILED", Notification.is_active.is_(True)))
            values["mascomatch_email_pending"] = db.scalar(select(func.count()).select_from(Notification).where(Notification.email_status == "PENDING", Notification.is_active.is_(True)))
            values["mascomatch_account_email_failed"] = db.scalar(select(func.count()).select_from(AccountToken).where(AccountToken.email_status == "FAILED"))
    except Exception:
        values["mascomatch_ready"] = 0
    try:
        with Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2) as redis:
            for status, count in redis.hgetall("mascomatch:metrics:http").items():
                if status in {b"1xx",b"2xx",b"3xx",b"4xx",b"5xx"}:
                    values[f'mascomatch_http_requests_total{{status_class="{status.decode()}"}}'] = int(count)
            values["mascomatch_backup_last_success_unixtime"] = float(redis.get("mascomatch:backup:last_success") or 0)
    except Exception:
        values["mascomatch_ready"] = 0
    return Response("\n".join(f"{name} {value}" for name,value in sorted(values.items()))+"\n",
                    media_type="text/plain; version=0.0.4", headers={"Cache-Control":"no-store"})
