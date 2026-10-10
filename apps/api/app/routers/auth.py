from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
import re

from app.core.security import create_access_token, decode_token_claims, hash_password, verify_password, password_needs_upgrade
from app.core.config import settings
from app.core.login_limit import check_login_budget
from app.analysis.service import utcnow
from app.db.session import get_db
from app.dependencies import current_user, oauth2_scheme
from app.models import User, AuthSession, Notification
from app.schemas import LoginRequest, NotificationPreferences, RegisterRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def issue_session(db, user):
    session = AuthSession(user_id=user.id, expires_at=utcnow() + timedelta(minutes=settings.access_token_minutes))
    db.add(session)
    db.flush()
    token = create_access_token(user.id, session.id)
    db.commit()
    return TokenResponse(access_token=token, user=user, expires_in=settings.access_token_minutes * 60)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email) or not payload.name.strip():
        raise HTTPException(status_code=422, detail="A valid email address is required")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    require_account_mail()
    user = User(email=email, password_hash=hash_password(payload.password), name=payload.name.strip(), phone=payload.phone)
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409,detail="An account with this email already exists") from exc
    from app.account_mail import issue_token
    issue_token(db,user,"VERIFY_EMAIL")
    return issue_session(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    check_login_budget(email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect", headers={"WWW-Authenticate": "Bearer"})
    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="This account is unavailable")
    if password_needs_upgrade(user.password_hash):
        user.password_hash = hash_password(payload.password)
    return issue_session(db, user)


@router.post("/logout", status_code=204)
def logout(token=Depends(oauth2_scheme), user=Depends(current_user), db=Depends(get_db)):
    session = db.get(AuthSession, UUID(decode_token_claims(token)["jti"]))
    session.revoked_at = utcnow()
    db.commit()
    return Response(status_code=204)


class AccountEmail(BaseModel):
    email:str=Field(min_length=5,max_length=320)


class VerificationCode(BaseModel):
    code:str=Field(min_length=20,max_length=100)


class ResetPassword(VerificationCode):
    password:str=Field(min_length=12,max_length=128)


def require_account_mail():
    if settings.mail_delivery_mode == "disabled":
        raise HTTPException(status_code=503, detail="El envío de correos está desactivado. La recuperación y la confirmación de cuentas no están disponibles por el momento.")


@router.post("/request-verification")
def request_verification(db=Depends(get_db),user=Depends(current_user)):
    from app.account_mail import issue_token
    if not user.email_verified:
        require_account_mail()
        wait=issue_token(db,user,"VERIFY_EMAIL")
        if wait:
            raise HTTPException(status_code=429, detail="Ya pediste un enlace recientemente. Esperá antes de reenviarlo.", headers={"Retry-After":str(wait)})
        db.commit()
    return {"ok":True, "already_verified":user.email_verified, **({"delivery_mode":"preview"} if settings.mail_delivery_mode=="preview" else {})}


@router.post("/verify-email")
def verify_email(payload:VerificationCode,db=Depends(get_db)):
    from app.account_mail import consume_token
    user=consume_token(db,payload.code,"VERIFY_EMAIL")
    if user is None:
        raise HTTPException(status_code=400,detail="El enlace venció o ya fue usado. Pedí uno nuevo.")
    user.email_verified_at=utcnow()
    db.execute(update(Notification).where(Notification.owner_id==user.id,Notification.email_status=="PENDING").values(email_available_at=utcnow()))
    db.commit()
    return {"ok":True}


@router.post("/password-reset")
def password_reset(payload:AccountEmail,db=Depends(get_db)):
    from app.account_mail import issue_token
    require_account_mail()
    email=payload.email.strip().lower()
    user=db.scalar(select(User).where(User.email==email,User.status=="ACTIVE"))
    if user:
        issue_token(db,user,"RESET_PASSWORD")
        db.commit()
    # Do not disclose whether the address belongs to a registered account.
    return {"ok":True, **({"delivery_mode":"preview"} if settings.mail_delivery_mode == "preview" else {})}


@router.post("/reset-password")
def reset_password(payload:ResetPassword,db=Depends(get_db)):
    from app.account_mail import consume_token
    user=consume_token(db,payload.code,"RESET_PASSWORD")
    if user is None:
        raise HTTPException(status_code=400,detail="El enlace venció o ya fue usado. Pedí uno nuevo.")
    user.password_hash=hash_password(payload.password)
    user.email_verified_at=utcnow()
    db.execute(update(AuthSession).where(AuthSession.user_id==user.id,AuthSession.revoked_at.is_(None)).values(revoked_at=utcnow()))
    db.execute(update(Notification).where(Notification.owner_id==user.id,Notification.email_status=="PENDING").values(email_available_at=utcnow()))
    db.commit()
    return {"ok":True}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/notification-preferences", response_model=UserRead)
def notification_preferences(payload: NotificationPreferences, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.notification_preferences = {**user.notification_preferences, "email": payload.email}
    db.commit()
    db.refresh(user)
    return user

