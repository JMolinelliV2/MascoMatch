"""Public report details and metadata-cleaned photos, without private contact or GPS."""
from datetime import datetime, timedelta
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.analysis.service import utcnow
from app.core.image_storage import load_analysis_image
from app.db.session import get_db
from app.models import LostCase, Observation, Photo
from app.routers.public_lost_dogs import active_dogs

router = APIRouter(prefix="/public/observations", tags=["public-observations"])


class RelatedNotice(BaseModel):
    id: UUID
    name: str


class PublicObservationRead(BaseModel):
    id: UUID
    species: str
    sex: str
    primary_color: str
    size: str
    description: str
    source_type: str
    public_location: str | None
    observed_at: datetime
    photo_url: str | None
    related_notice: RelatedNotice | None


def visible_observations():
    return select(Observation).where(
        Observation.moderation_status == "VISIBLE",
        Observation.source_type.in_(["USER_SIGHTING", "FOUND_ANIMAL"]),
        Observation.observed_at <= utcnow() + timedelta(minutes=1),
    )


def observation_photo_exists():
    return exists().where(Photo.owner_type == "observation", Photo.owner_id == Observation.id).correlate(Observation)


def public_photo_url(identity, has_photo):
    return f"/api/v1/public/observations/{identity}/photo" if has_photo else None


@router.get("/{observation_id}", response_model=PublicObservationRead)
def get_public_observation(observation_id: UUID, response: Response, db: Session = Depends(get_db)):
    row = db.execute(visible_observations().where(Observation.id == observation_id).add_columns(observation_photo_exists())).first()
    if row is None:
        raise HTTPException(status_code=404, detail="El reporte ya no está disponible.")
    observation, has_photo = row
    related_notice = None
    if observation.linked_case_id:
        related = db.execute(active_dogs().where(LostCase.id == observation.linked_case_id)).first()
        if related:
            case, pet = related
            related_notice = RelatedNotice(id=case.id, name=pet.name)
    response.headers["Cache-Control"] = "no-store"
    # Explicit allowlist: no author, contact preferences, matching scores, storage keys or precise location.
    return PublicObservationRead(
        id=observation.id, species=observation.species, sex=observation.sex,
        primary_color=observation.primary_color, size=observation.size,
        description=observation.description, source_type=observation.source_type,
        public_location=observation.public_location, observed_at=observation.observed_at,
        photo_url=public_photo_url(observation.id, has_photo), related_notice=related_notice,
    )


@router.get("/{observation_id}/photo")
def get_public_observation_photo(observation_id: UUID, db: Session = Depends(get_db)):
    observation = db.scalar(visible_observations().where(Observation.id == observation_id))
    if observation is None:
        raise HTTPException(status_code=404, detail="El reporte ya no está disponible.")
    photo = db.scalar(select(Photo).where(Photo.owner_type == "observation", Photo.owner_id == observation.id).order_by(Photo.created_at.desc(), Photo.id.desc()).limit(1))
    if photo is None:
        raise HTTPException(status_code=404, detail="El reporte no tiene foto.")
    try:
        payload, mime_type = load_analysis_image(photo.storage_key, photo.mime_type)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(status_code=404, detail="La foto no está disponible.") from exc
        raise HTTPException(status_code=503, detail="No pudimos cargar la foto por ahora.") from exc
    except (BotoCoreError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="No pudimos cargar la foto por ahora.") from exc
    return Response(content=payload, media_type=mime_type, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
