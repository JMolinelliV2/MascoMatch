"""Private, retryable delivery of public contact submissions to one fixed inbox."""
import asyncio
from datetime import timedelta
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import format_datetime, make_msgid
from html import escape
import logging
import smtplib

from sqlalchemy import delete, select, update

from app.analysis.logging import log_event
from app.analysis.service import utcnow
from app.core.config import settings
from app.db.session import SessionLocal
from app.matching.linked import aware
from app.mail_templates import LOGO_PATH
from app.models import ContactMessage
from app.notifications.email import send_message

CONTACT_RECIPIENT = "info@mascomatch.com"
TOPICS = {"improvement": "Sugerencia de mejora", "problem": "Problema con la página", "other": "Consulta"}


def build_message(contact):
    topic = TOPICS[contact.topic]
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = CONTACT_RECIPIENT
    message["Reply-To"] = Address(display_name=contact.name, addr_spec=contact.email)
    message["Subject"] = f"MascoMatch · {topic}"
    message["Date"] = format_datetime(aware(contact.created_at))
    message["Message-ID"] = f"<mascomatch-contact-{contact.id}@mascomatch.com>"
    message.set_content(f"Nuevo mensaje desde Contacto de MascoMatch\n\nTipo: {topic}\nNombre: {contact.name}\nCorreo: {contact.email}\n\n{contact.message}\n\nPodés responder directamente a este correo. La dirección fue indicada por la persona y no se verificó.\nReferencia: {contact.id}")
    logo_cid = make_msgid(domain="mascomatch.com")
    content = escape(contact.message).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    message.add_alternative(f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:24px 12px;background:#f6f7fb;color:#0b2a4a;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" align="center" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#fff;border:1px solid #e5eaf0;border-top:5px solid #d93646;border-radius:16px;">
<tr><td style="padding:28px;border-bottom:1px solid #e5eaf0;"><table role="presentation" cellspacing="0" cellpadding="0"><tr><td><img src="cid:{logo_cid[1:-1]}" width="44" height="44" alt="" style="display:block;"></td><td style="padding-left:10px;font-size:26px;font-weight:800;">Masco<span style="color:#d93646;">Match</span></td></tr></table></td></tr>
<tr><td style="padding:28px;"><p style="color:#0863b4;font-size:12px;font-weight:700;letter-spacing:1px;">CONTACTO</p><h1 style="font-size:24px;line-height:1.3;">{escape(topic)}</h1><p style="font-size:14px;line-height:1.7;"><strong>Nombre:</strong> {escape(contact.name)}<br><strong>Correo:</strong> {escape(contact.email)}</p><div style="padding:20px;background:#eff8ff;border-radius:12px;line-height:1.7;word-break:break-word;overflow-wrap:anywhere;">{content}</div></td></tr>
<tr><td style="padding:20px 28px;border-top:1px solid #e5eaf0;color:#52677e;font-size:12px;line-height:1.7;">Podés responder directamente a este correo. La dirección fue indicada por la persona y no se verificó.<br>Referencia: {contact.id}</td></tr></table></body></html>""", subtype="html")
    message.get_payload()[-1].add_related(LOGO_PATH.read_bytes(), maintype="image", subtype="png", cid=logo_cid, filename="mascomatch-logo.png", disposition="inline")
    return message


def deliver_pending(factory=None):
    if settings.mail_delivery_mode == "disabled":
        return 0
    factory = factory or SessionLocal
    with factory() as db:
        identities = list(db.scalars(select(ContactMessage.id).where(ContactMessage.email_status == "PENDING", ContactMessage.email_available_at <= utcnow()).order_by(ContactMessage.created_at).limit(10)))
        db.execute(delete(ContactMessage).where(ContactMessage.email_status.in_(["SENT", "PREVIEWED"]), ContactMessage.email_sent_at < utcnow() - timedelta(days=30)))
        db.commit()
    sent = 0
    for identity in identities:
        with factory() as db:
            contact = db.scalar(select(ContactMessage).where(ContactMessage.id == identity).with_for_update(skip_locked=True))
            if not contact or contact.email_status != "PENDING" or aware(contact.email_available_at) > utcnow():
                continue
            contact.email_attempts += 1
            try:
                send_message(build_message(contact))
                contact.email_status = "PREVIEWED" if settings.mail_delivery_mode == "preview" else "SENT"
                contact.email_sent_at = utcnow()
                sent += 1
            except (OSError, smtplib.SMTPException, ValueError):
                contact.email_status = "FAILED" if contact.email_attempts >= 5 else "PENDING"
                contact.email_available_at = utcnow() + timedelta(seconds=min(3600, 30 * 2 ** contact.email_attempts))
                log_event("contact_email_failed", level=logging.WARNING, message_id=str(identity), attempts=contact.email_attempts)
            db.commit()
    return sent


async def delivery_loop():
    while True:
        try:
            await asyncio.to_thread(deliver_pending)
        except Exception:
            log_event("contact_delivery_unavailable", level=logging.WARNING)
        await asyncio.sleep(10)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reintentar correos de contacto después de corregir SMTP.")
    parser.add_argument("--retry-failed", action="store_true", required=True)
    parser.parse_args()
    with SessionLocal() as db:
        result = db.execute(update(ContactMessage).where(ContactMessage.email_status == "FAILED").values(email_status="PENDING", email_attempts=0, email_available_at=utcnow()))
        db.commit()
        print(f"Mensajes de contacto pendientes de reintento: {result.rowcount}")
