from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis.service import utcnow
from app.matching.linked import aware
from app.core.image_storage import load_analysis_image
from app.db.session import get_db
from app.dependencies import current_user
from app.models import LostCase, Match, Notification, Observation, Pet, Photo, User
from app.schemas import NotificationList, NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


def private_notifications(user):
    return select(Notification, LostCase, Pet, Observation).join(LostCase, Notification.lost_case_id == LostCase.id).join(Pet, LostCase.pet_id == Pet.id).join(Observation, Notification.observation_id == Observation.id).where(
        Notification.owner_id == user.id, Pet.owner_id == user.id, Notification.is_active.is_(True), LostCase.status == "ACTIVE",
        LostCase.moderation_status=="VISIBLE",Observation.moderation_status=="VISIBLE",
    )


def owned_row(db, identity, user):
    row = db.execute(private_notifications(user).where(Notification.id == identity)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    return row


def serialize(db, row):
    notification, case, pet, observation = row
    match = db.get(Match, notification.match_id) if notification.match_id else None
    author=db.get(User,observation.author_id) if observation.share_contact and observation.author_id else None
    photos = list(db.scalars(select(Photo.id).where(Photo.owner_type == "observation", Photo.owner_id == observation.id).order_by(Photo.created_at, Photo.id)))
    return NotificationRead(
        id=notification.id, kind=notification.kind, title=notification.title, body=notification.body,
        read_at=notification.read_at, created_at=aware(notification.created_at), lost_case_id=case.id,
        pet_name=pet.name, observed_at=aware(observation.observed_at), public_location=observation.public_location,
        latitude=observation.latitude, longitude=observation.longitude,
        reasons=match.explanation if match else observation.matching_reasons, photo_ids=photos,
        email_status=notification.email_status,
        match_id=notification.match_id, match_status=match.status if match else None,
        reporter_contact=author.email if author and author.status=="ACTIVE" and author.email_verified else None,
        matching_status=observation.matching_status,linked_to_notice=observation.linked_case_id==case.id,
    )


@router.get("", response_model=NotificationList)
def list_notifications(response: Response, limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0, le=10000), db: Session = Depends(get_db), user: User = Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    query = private_notifications(user)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    unread = db.scalar(select(func.count()).select_from(query.where(Notification.read_at.is_(None)).subquery())) or 0
    rows = list(db.execute(query.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(offset).limit(limit)))
    return NotificationList(items=[serialize(db, row) for row in rows], unread_count=unread, total=total)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: UUID, response: Response, db: Session = Depends(get_db), user: User = Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    row = owned_row(db, notification_id, user)
    notification = row[0]
    if notification.read_at is None:
        notification.read_at = utcnow()
        db.commit()
    return serialize(db, row)


@router.get("/{notification_id}", response_model=NotificationRead)
def get_notification(notification_id: UUID, response: Response, db: Session = Depends(get_db), user: User = Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    return serialize(db, owned_row(db, notification_id, user))


@router.get("/{notification_id}/photos/{photo_id}")
def notification_photo(notification_id: UUID, photo_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    observation = owned_row(db, notification_id, user)[3]
    photo = db.scalar(select(Photo).where(Photo.id == photo_id, Photo.owner_type == "observation", Photo.owner_id == observation.id))
    if photo is None:
        raise HTTPException(status_code=404, detail="Foto no encontrada.")
    try:
        payload, mime_type = load_analysis_image(photo.storage_key, photo.mime_type)
    except (BotoCoreError, ClientError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Foto no disponible en este momento.") from exc
    return Response(payload, media_type=mime_type, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
