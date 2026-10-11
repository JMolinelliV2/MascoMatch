"""Private telemetry with bounded retention. Authentication never depends on telemetry."""
import asyncio
import logging
from datetime import timedelta
from sqlalchemy import delete, or_, text, update
from app.analysis.service import utcnow
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import EmailDeliveryLog, User, UserActivity


def record_activity(identity):
    minute = utcnow().replace(second=0, microsecond=0)
    try:
        with SessionLocal() as db:
            if db.bind.dialect.name == "postgresql":
                db.execute(text("SET LOCAL lock_timeout = '250ms'"))
            # Atomic guard also deduplicates requests across multiple API processes.
            changed = db.execute(update(User).where(User.id == identity, User.status == "ACTIVE",
                or_(User.last_active_at.is_(None), User.last_active_at < minute))
                .values(last_active_at=minute, updated_at=User.updated_at))
            if changed.rowcount:
                db.add(UserActivity(user_id=identity, occurred_at=minute))
            db.commit()
    except Exception:
        logging.getLogger(__name__).warning("activity_tracking_unavailable")


def record_mail(db, kind, source_type, source_ids, recipient_user_id, status):
    db.add(EmailDeliveryLog(kind=kind, source_type=source_type,
        source_ids=[str(identity) for identity in source_ids], recipient_user_id=recipient_user_id,
        status=status, item_count=len(source_ids), created_at=utcnow()))


def cleanup_tracking():
    with SessionLocal() as db:
        cutoff = utcnow() - timedelta(days=90)
        db.execute(delete(UserActivity).where(UserActivity.occurred_at < cutoff))
        db.execute(delete(EmailDeliveryLog).where(EmailDeliveryLog.created_at < cutoff))
        db.commit()


async def cleanup_loop():
    while True:
        try:
            if settings.app_env != "test":
                await asyncio.to_thread(cleanup_tracking)
        except Exception:
            logging.getLogger(__name__).warning("tracking_cleanup_unavailable")
        await asyncio.sleep(3600)
