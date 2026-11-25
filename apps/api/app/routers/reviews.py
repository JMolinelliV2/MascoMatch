from typing import Literal
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.analysis.service import utcnow
from app.db.session import get_db
from app.dependencies import current_user, verified_user
from app.models import AdminAudit, CaseReview, LostCase, Pet, User
from app.species import SUPPORTED_SPECIES, is_supported_species
from app.admin_access import administrator
from app.core.image_storage import load_display_image
from app.account_management import lock_active_user
from app.review_identity import abbreviated_name

router = APIRouter(tags=["reviews"])
RETIRED_STATUSES = {"FOUND", "CLOSED", "CANCELLED"}


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    anonymous: StrictBool = True
    rating: StrictInt = Field(ge=1, le=5)
    comment: str = Field(min_length=20, max_length=800)
    consent: Literal[True]

    @field_validator("comment", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("consent", mode="before")
    @classmethod
    def explicit_consent(cls, value):
        if value is not True:
            raise ValueError("Autorizá expresamente la publicación de tu reseña.")
        return value


class VisibilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visibility: Literal["VISIBLE", "HIDDEN"]


def owned_review_case(db, case_id, user, *, lock=False):
    query = select(LostCase).join(Pet).where(LostCase.id == case_id, Pet.owner_id == user.id)
    if lock:
        query = query.with_for_update(of=LostCase)
    case = db.scalar(query)
    if case is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado.")
    return case


def anonymous_review(item):
    return item.is_anonymous


def review_avatar_version(item, user):
    if user and item.is_current and item.visibility == "VISIBLE" and not anonymous_review(item) and user.avatar_storage_key:
        return user.avatar_version
    return None


def public_review(item, user=None):
    # The review ID scopes photo access without exposing account IDs or storage keys.
    name = "Anónimo" if anonymous_review(item) or user is None else abbreviated_name(user.name)
    return {"id": item.id, "display_name": name, "anonymous": item.is_anonymous, "rating": item.rating,
            "comment": item.comment, "created_at": item.created_at, "updated_at": item.updated_at,
            "avatar_version": review_avatar_version(item, user)}


def visible_reviews():
    return select(CaseReview, User).select_from(CaseReview).join(User, CaseReview.author_id == User.id).where(
        CaseReview.is_current.is_(True), CaseReview.visibility == "VISIBLE", User.status == "ACTIVE", User.email_verified_at.is_not(None),
    )


@router.get("/public/reviews")
def public_reviews(response: Response, limit: int = Query(default=6, ge=1, le=12), db=Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    query = visible_reviews().order_by(CaseReview.created_at.desc(), CaseReview.id.desc()).limit(limit)
    return {"items": [public_review(item, user) for item, user in db.execute(query)]}


@router.get("/public/reviews/{review_id}/avatar")
def public_review_avatar(review_id: UUID, db=Depends(get_db)):
    row = db.execute(visible_reviews().where(CaseReview.id == review_id)).first()
    if row is None or review_avatar_version(*row) is None:
        raise HTTPException(404, "Esta reseña no tiene una foto pública disponible.")
    _, author = row
    try:
        payload, mime = load_display_image(author.avatar_storage_key, "image/jpeg")
    except Exception as exc:
        logging.getLogger(__name__).warning("review_avatar_unavailable")
        raise HTTPException(503, "No pudimos cargar la foto de esta reseña.") from exc
    return Response(content=payload, media_type=mime, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


def account_review(db, user, *, lock=False):
    query = select(CaseReview).where(CaseReview.author_id == user.id, CaseReview.is_current.is_(True))
    return db.scalar(query.with_for_update() if lock else query)


def eligible_origin(db, user):
    return db.scalar(select(LostCase).join(Pet).where(Pet.owner_id == user.id, Pet.species.in_(SUPPORTED_SPECIES),
        LostCase.status.in_(RETIRED_STATUSES), LostCase.moderation_status == "VISIBLE").order_by(LostCase.created_at.desc(), LostCase.id.desc()).limit(1))


def eligible(case):
    return case is not None and is_supported_species(case.pet.species) and case.status in RETIRED_STATUSES and case.moderation_status == "VISIBLE"


def account_review_state(response, db, user, case=None):
    item = account_review(db, user)
    response.headers["Cache-Control"] = "no-store"
    return {"eligible": item is not None or eligible(case if case is not None else eligible_origin(db, user)),
            "account_display_name": abbreviated_name(user.name),
            "email_verified": user.email_verified, "review": {**public_review(item, user), "visibility": item.visibility} if item else None}


@router.get("/reviews/me")
def my_review(response: Response, db=Depends(get_db), user=Depends(current_user)):
    return account_review_state(response, db, user)


@router.get("/reviews/lost-cases/{case_id}")
def review_state(case_id: UUID, response: Response, db=Depends(get_db), user=Depends(current_user)):
    case = owned_review_case(db, case_id, user)
    return account_review_state(response, db, user, case)


def save_account_review(payload, response, db, user, *, case_id=None, editing=False):
    # All writes lock the account before a notice/review, including first creation
    # from two different recoveries. The partial unique index is a second guard.
    user = lock_active_user(db, user)
    case = owned_review_case(db, case_id, user, lock=True) if case_id else None
    item = account_review(db, user, lock=True)
    if editing and item is None:
        raise HTTPException(404, "Todavía no dejaste una reseña de MascoMatch.")
    if not editing and item is not None:
        raise HTTPException(409, "Ya tenés una reseña de MascoMatch. Podés conservarla o editarla.")
    if item is None:
        case = case or eligible_origin(db, user)
        if not eligible(case):
            raise HTTPException(409, "Podés dejar una reseña después de cerrar un aviso o recuperar a tu mascota.")
        item = CaseReview(lost_case_id=case.id, author_id=user.id)
        db.add(item)
    item.is_anonymous = payload.anonymous
    item.display_name = "Anónimo" if payload.anonymous else abbreviated_name(user.name)
    item.rating, item.comment, item.consent_at = payload.rating, payload.comment, utcnow()
    if item.visibility == "WITHDRAWN":
        item.visibility = "HIDDEN" if item.moderation_hidden else "VISIBLE"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya tenés una reseña de MascoMatch. Actualizá la página para editarla.")
    db.refresh(item)
    response.headers["Cache-Control"] = "no-store"
    return {**public_review(item, user), "visibility": item.visibility}


@router.post("/reviews/me", status_code=201)
def create_my_review(payload: ReviewInput, response: Response, db=Depends(get_db), user=Depends(verified_user)):
    return save_account_review(payload, response, db, user)


@router.patch("/reviews/me")
def edit_my_review(payload: ReviewInput, response: Response, db=Depends(get_db), user=Depends(verified_user)):
    return save_account_review(payload, response, db, user, editing=True)


@router.post("/reviews/lost-cases/{case_id}", status_code=201)
def create_review(case_id: UUID, payload: ReviewInput, response: Response, db=Depends(get_db), user=Depends(verified_user)):
    return save_account_review(payload, response, db, user, case_id=case_id)


@router.patch("/reviews/lost-cases/{case_id}")
def edit_review(case_id: UUID, payload: ReviewInput, response: Response, db=Depends(get_db), user=Depends(verified_user)):
    return save_account_review(payload, response, db, user, case_id=case_id, editing=True)


def withdraw_account_review(db, user, case_id=None):
    user = lock_active_user(db, user)
    if case_id:
        owned_review_case(db, case_id, user, lock=True)
    item = account_review(db, user, lock=True)
    if item is None:
        raise HTTPException(404, "Reseña no encontrada.")
    item.visibility = "WITHDRAWN"
    db.commit()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.delete("/reviews/me", status_code=204)
def withdraw_my_review(db=Depends(get_db), user=Depends(current_user)):
    return withdraw_account_review(db, user)


@router.delete("/reviews/lost-cases/{case_id}", status_code=204)
def withdraw_review(case_id: UUID, db=Depends(get_db), user=Depends(current_user)):
    return withdraw_account_review(db, user, case_id)


@router.patch("/admin/reviews/{review_id}")
def review_visibility(review_id: UUID, payload: VisibilityInput, response: Response, db=Depends(get_db), user=Depends(administrator)):
    item = db.scalar(select(CaseReview).where(CaseReview.id == review_id).with_for_update())
    if item is None:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    if not item.is_current:
        raise HTTPException(409, "Esta reseña es histórica. Solo puede publicarse la reseña actual de la cuenta.")
    if item.visibility == "WITHDRAWN":
        raise HTTPException(status_code=409, detail="El autor retiró esta reseña y no puede volver a publicarse.")
    item.visibility = payload.visibility
    item.moderation_hidden = payload.visibility == "HIDDEN"
    db.add(AdminAudit(actor_id=user.id, action="RESTORE_REVIEW" if payload.visibility == "VISIBLE" else "HIDE_REVIEW",
                      target_type="case_review", target_id=item.id))
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"id": item.id, "visibility": item.visibility}
