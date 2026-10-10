import asyncio
from datetime import timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime
import logging
import smtplib
import ssl
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select

from app.analysis.logging import log_event
from app.analysis.service import utcnow
from app.core.config import settings
from app.db.session import SessionLocal
from app.matching.linked import aware
from app.models import LostCase, Notification, Observation, User


def build_message(notification, owner, observation=None, related=None):
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = owner.email
    message["Subject"] = " ".join(notification.title.splitlines())
    message["Date"] = format_datetime(utcnow())
    message["Message-ID"] = f"<mascomatch-{notification.id}@mascomatch.local>"
    context = ""
    if observation:
        try:
            zone, label = ZoneInfo("America/Montevideo"), "hora de Uruguay"
        except ZoneInfoNotFoundError:
            zone, label = timezone.utc, "UTC"
        when = aware(observation.observed_at).astimezone(zone).strftime("%d/%m/%Y %H:%M")
        context = f"\n\nFecha del avistamiento: {when} ({label})."
        if observation.public_location:
            context += f"\nZona: {observation.public_location}"
    message.set_content(f"{notification.title}\n\n{notification.body}{context}\n\nRevisá el lugar y las fotos en MascoMatch:\n{settings.public_site_url.rstrip('/')}/notificaciones?aviso={notification.id}\n\nSe trata de una posible coincidencia, que necesita revisión.\nPodés cambiar tus preferencias de correo en Notificaciones.")
    if related and len(related)>1:
        message.replace_header("Subject", f"{len(related)} reportes nuevos: {notification.title}")
        links="\n".join(f"{settings.public_site_url.rstrip('/')}/notificaciones?aviso={item.id}" for item in related)
        message.set_content(f"Recibimos {len(related)} avistamientos potencialmente relacionados con el mismo aviso.\n\nRevisá los lugares, fotos y motivos de cada reporte:\n{links}\n\nLa identidad de los animales necesita confirmación.\nPodés cambiar tus preferencias de correo en Notificaciones.")
    return message


def send_message(message):
    tls = "none" if settings.mail_delivery_mode == "preview" else settings.smtp_tls_mode
    context = ssl.create_default_context()
    connection = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15, context=context) if tls == "ssl" else smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
    with connection as smtp:
        if tls == "starttls":
            smtp.starttls(context=context)
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        refused = smtp.send_message(message)
        if refused:
            raise smtplib.SMTPException("Recipient refused")


def deliver_pending(session_factory=None):
    if settings.mail_delivery_mode == "disabled":
        return 0
    factory = session_factory or SessionLocal
    with factory() as db:
        identities = list(db.scalars(select(Notification.id).where(Notification.is_active.is_(True), Notification.email_status == "PENDING", Notification.email_available_at <= utcnow()).order_by(Notification.created_at).limit(10)))
    sent = 0
    for identity in identities:
        with factory() as db:
            notification = db.get(Notification, identity)
            if notification is None or not notification.is_active or notification.email_status != "PENDING" or aware(notification.email_available_at) > utcnow():
                continue
            # Match evaluators and delivery both lock the case before related records.
            case = db.scalar(select(LostCase).where(LostCase.id==notification.lost_case_id).with_for_update(skip_locked=True))
            if case is None:
                continue
            group=list(db.scalars(select(Notification).where(Notification.lost_case_id==case.id,Notification.owner_id==notification.owner_id,
                Notification.is_active.is_(True),Notification.email_status=="PENDING",Notification.email_available_at<=utcnow()).order_by(Notification.created_at,Notification.id).limit(100).with_for_update()))
            if not group:
                continue
            notification=group[0]
            owner = db.get(User, notification.owner_id)
            if not owner or owner.status != "ACTIVE" or not case or case.status != "ACTIVE":
                for item in group:item.email_status = "CANCELLED"
            elif owner.notification_preferences.get("email", True) is False:
                for item in group:item.email_status = "SKIPPED"
            elif not owner.email_verified:
                for item in group:item.email_available_at=utcnow()+timedelta(minutes=5)
            else:
                for item in group:item.email_attempts += 1
                try:
                    send_message(build_message(notification, owner, db.get(Observation, notification.observation_id), group))
                    for item in group:
                        item.email_status = "PREVIEWED" if settings.mail_delivery_mode == "preview" else "SENT"
                        item.email_sent_at = utcnow()
                    sent += 1
                except (OSError, smtplib.SMTPException, ValueError):
                    for item in group:
                        item.email_status = "FAILED" if item.email_attempts >= 5 else "PENDING"
                        item.email_available_at = utcnow() + timedelta(seconds=min(3600, 30 * 2 ** item.email_attempts))
                    log_event("notification_email_failed", level=logging.WARNING, notification_id=str(identity), attempts=notification.email_attempts)
            db.commit()
    return sent


async def delivery_loop():
    while True:
        try:
            await asyncio.to_thread(deliver_pending)
        except Exception:
            log_event("email_delivery_unavailable", level=logging.WARNING)
        await asyncio.sleep(10)
