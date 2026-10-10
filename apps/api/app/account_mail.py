"""Single-use account tokens and transactional delivery; no raw token logs."""
import asyncio
import base64
from datetime import timedelta
from email.message import EmailMessage
from hashlib import sha256
from math import ceil
import logging
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select, update, func
from app.analysis.service import utcnow
from app.core.config import settings
from app.db.session import SessionLocal
from app.matching.linked import aware
from app.mail_templates import add_password_reset_content, add_email_verification_content, add_email_change_content
from app.models import AccountToken, AuthSession, Notification, User
from app.notifications.email import send_message

AAD = b"mascomatch-account-token-v1"


def encrypt_token(token):
    nonce=secrets.token_bytes(12)
    key=sha256(AAD+settings.jwt_secret.encode()).digest()
    return base64.urlsafe_b64encode(nonce+AESGCM(key).encrypt(nonce,token.encode(),AAD)).decode()


def decrypt_token(value):
    data=base64.urlsafe_b64decode(value)
    key=sha256(AAD+settings.jwt_secret.encode()).digest()
    return AESGCM(key).decrypt(data[:12],data[12:],AAD).decode()


def issue_token(db, user, kind):
    db.scalar(select(User).where(User.id==user.id).with_for_update())
    now=utcnow()
    last=db.scalar(select(AccountToken).where(AccountToken.user_id==user.id,AccountToken.kind==kind).order_by(AccountToken.created_at.desc()).limit(1))
    recent=db.scalar(select(func.count()).select_from(AccountToken).where(AccountToken.user_id==user.id,AccountToken.created_at>now-timedelta(hours=1)))
    if recent>=3:
        oldest=db.scalar(select(func.min(AccountToken.created_at)).where(AccountToken.user_id==user.id,AccountToken.created_at>now-timedelta(hours=1)))
        return max(1,ceil((aware(oldest)+timedelta(hours=1)-now).total_seconds()))
    if last and aware(last.created_at)>now-timedelta(minutes=1):
        return max(1,ceil((aware(last.created_at)+timedelta(minutes=1)-now).total_seconds()))
    # A replacement invalidates older links of the same purpose.
    db.execute(update(AccountToken).where(AccountToken.user_id==user.id,AccountToken.kind==kind,AccountToken.consumed_at.is_(None)).values(consumed_at=utcnow(),email_status="CANCELLED"))
    token=secrets.token_urlsafe(32)
    db.add(AccountToken(user_id=user.id,kind=kind,destination_email=user.pending_email if kind=="CHANGE_EMAIL" else user.email,
                        token_hash=sha256(token.encode()).hexdigest(),encrypted_token=encrypt_token(token),
                        expires_at=now+timedelta(minutes=30) if kind=="RESET_PASSWORD" else now+timedelta(hours=24),email_available_at=now))
    return 0


def consume_token(db, token, kind):
    owner_id=db.scalar(select(AccountToken.user_id).where(AccountToken.token_hash==sha256(token.encode()).hexdigest(),AccountToken.kind==kind))
    if owner_id is None:
        return None
    user=db.scalar(select(User).where(User.id==owner_id).with_for_update().execution_options(populate_existing=True))
    ticket=db.scalar(select(AccountToken).where(AccountToken.token_hash==sha256(token.encode()).hexdigest(),AccountToken.kind==kind).with_for_update())
    if not ticket or ticket.consumed_at is not None or aware(ticket.expires_at)<=utcnow():
        return None
    if not user or user.status!="ACTIVE":
        return None
    expected=user.pending_email if kind=="CHANGE_EMAIL" else user.email
    if not expected or (ticket.destination_email is not None and ticket.destination_email!=expected):
        return None
    if kind=="CHANGE_EMAIL" and ticket.destination_email!=expected:
        return None
    ticket.consumed_at=utcnow()
    ticket.email_status="CONSUMED"
    return user


def deliver_pending(factory=None):
    if settings.mail_delivery_mode=="disabled":
        return 0
    factory=factory or SessionLocal
    sent=0
    with factory() as db:
        identities=list(db.scalars(select(AccountToken.id).where(AccountToken.email_status=="PENDING",AccountToken.email_available_at<=utcnow()).limit(10)))
    for identity in identities:
        with factory() as db:
            owner_id=db.scalar(select(AccountToken.user_id).where(AccountToken.id==identity))
            if owner_id is None:
                continue
            user=db.scalar(select(User).where(User.id==owner_id).with_for_update(skip_locked=True).execution_options(populate_existing=True))
            if not user:
                continue
            ticket=db.scalar(select(AccountToken).where(AccountToken.id==identity).with_for_update(skip_locked=True))
            if not ticket or ticket.email_status!="PENDING":
                continue
            expected=user.pending_email if ticket.kind=="CHANGE_EMAIL" else user.email
            destination=ticket.destination_email or (expected if ticket.kind!="CHANGE_EMAIL" else None)
            if ticket.consumed_at is not None or aware(ticket.expires_at)<=utcnow() or user.status!="ACTIVE" or not expected or destination!=expected:
                ticket.email_status="CANCELLED"
            else:
                ticket.email_attempts+=1
                try:
                    token=decrypt_token(ticket.encrypted_token)
                    path="recuperar" if ticket.kind=="RESET_PASSWORD" else "confirmar-correo"
                    message=EmailMessage()
                    message["From"],message["To"]=settings.smtp_from,destination
                    message["Subject"]="Recuperá tu cuenta de MascoMatch" if ticket.kind=="RESET_PASSWORD" else "Confirmá tu nuevo correo en MascoMatch" if ticket.kind=="CHANGE_EMAIL" else "Confirmá tu correo en MascoMatch"
                    message["Message-ID"]=f"<mascomatch-account-{ticket.id}@mascomatch.local>"
                    url=f"{settings.public_site_url.rstrip('/')}/{path}?codigo={token}"
                    if ticket.kind=="RESET_PASSWORD":
                        add_password_reset_content(message,url)
                    elif ticket.kind=="CHANGE_EMAIL":
                        add_email_change_content(message,url)
                    else:
                        add_email_verification_content(message,url)
                    send_message(message)
                    ticket.email_status="PREVIEWED" if settings.mail_delivery_mode=="preview" else "SENT"
                    sent+=1
                except Exception:
                    ticket.email_status="FAILED" if ticket.email_attempts>=5 else "PENDING"
                    ticket.email_available_at=utcnow()+timedelta(seconds=min(3600,30*2**ticket.email_attempts))
                    logging.getLogger("mascomatch.accounts").warning("account_mail_failed")
            db.commit()
    return sent


async def delivery_loop():
    while True:
        try:
            await asyncio.to_thread(deliver_pending)
        except Exception:
            logging.getLogger("mascomatch.accounts").warning("account_mail_unavailable")
        await asyncio.sleep(10)
