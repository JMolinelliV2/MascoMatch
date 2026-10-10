"""Single-use account tokens and transactional delivery; no raw token logs."""
import asyncio
import base64
from datetime import timedelta
from email.message import EmailMessage
from hashlib import sha256
import logging
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select, update, func
from app.analysis.service import utcnow
from app.core.config import settings
from app.db.session import SessionLocal
from app.matching.linked import aware
from app.mail_templates import add_password_reset_content
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
    last=db.scalar(select(AccountToken).where(AccountToken.user_id==user.id,AccountToken.kind==kind).order_by(AccountToken.created_at.desc()).limit(1))
    recent=db.scalar(select(func.count()).select_from(AccountToken).where(AccountToken.user_id==user.id,AccountToken.created_at>utcnow()-timedelta(hours=1)))
    if recent>=3:
        return
    if last and aware(last.created_at)>utcnow()-timedelta(minutes=1):
        return
    # A replacement invalidates older links of the same purpose.
    db.execute(update(AccountToken).where(AccountToken.user_id==user.id,AccountToken.kind==kind,AccountToken.consumed_at.is_(None)).values(consumed_at=utcnow(),email_status="CANCELLED"))
    token=secrets.token_urlsafe(32)
    db.add(AccountToken(user_id=user.id,kind=kind,token_hash=sha256(token.encode()).hexdigest(),encrypted_token=encrypt_token(token),
                        expires_at=utcnow()+timedelta(hours=24) if kind=="VERIFY_EMAIL" else utcnow()+timedelta(minutes=30),email_available_at=utcnow()))


def consume_token(db, token, kind):
    owner_id=db.scalar(select(AccountToken.user_id).where(AccountToken.token_hash==sha256(token.encode()).hexdigest(),AccountToken.kind==kind))
    if owner_id is None:
        return None
    db.scalar(select(User).where(User.id==owner_id).with_for_update())
    ticket=db.scalar(select(AccountToken).where(AccountToken.token_hash==sha256(token.encode()).hexdigest(),AccountToken.kind==kind).with_for_update())
    if not ticket or ticket.consumed_at is not None or aware(ticket.expires_at)<=utcnow():
        return None
    user=db.get(User,ticket.user_id)
    if not user or user.status!="ACTIVE":
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
            ticket=db.scalar(select(AccountToken).where(AccountToken.id==identity).with_for_update(skip_locked=True))
            if not ticket or ticket.email_status!="PENDING":
                continue
            user=db.get(User,ticket.user_id)
            if ticket.consumed_at is not None or aware(ticket.expires_at)<=utcnow() or not user or user.status!="ACTIVE":
                ticket.email_status="CANCELLED"
            else:
                ticket.email_attempts+=1
                try:
                    token=decrypt_token(ticket.encrypted_token)
                    path="confirmar-correo" if ticket.kind=="VERIFY_EMAIL" else "recuperar"
                    message=EmailMessage()
                    message["From"],message["To"]=settings.smtp_from,user.email
                    message["Subject"]="Confirmá tu correo en MascoMatch" if ticket.kind=="VERIFY_EMAIL" else "Recuperá tu cuenta de MascoMatch"
                    message["Message-ID"]=f"<mascomatch-account-{ticket.id}@mascomatch.local>"
                    url=f"{settings.public_site_url.rstrip('/')}/{path}?codigo={token}"
                    if ticket.kind=="RESET_PASSWORD":
                        add_password_reset_content(message,url)
                    else:
                        message.set_content(f"Abrí este enlace para confirmar tu correo y recibir alertas:\n\n{url}\n\nEl enlace es de un solo uso y tiene vencimiento. Si no pediste esto, podés ignorar este mensaje.")
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
