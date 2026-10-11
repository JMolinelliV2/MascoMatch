"""One operator, reserved from a private command and claimed by verified email."""
from fastapi import Depends, HTTPException
from sqlalchemy import select
from app.dependencies import current_user
from app.models import AdminAccess


def administrator(user=Depends(current_user)):
    if not user.admin_access:
        raise HTTPException(status_code=403, detail="Acceso reservado a la cuenta administradora de MascoMatch.")
    return user


def claim_reserved_access(db, user):
    if not user.email_verified or user.status != "ACTIVE":
        return
    reservation = db.scalar(select(AdminAccess).where(AdminAccess.id == 1).with_for_update())
    if reservation and reservation.user_id is None and reservation.pending_email == user.email:
        reservation.owner = user
        reservation.pending_email = None
        user.role = "ADMIN"
