"""Accept suggestions privately; recipients and mail headers stay server-controlled."""
from email.headerregistry import Address
import re
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.analysis.service import utcnow
from app.core.config import settings
from app.db.session import get_db
from app.models import ContactMessage

router = APIRouter(prefix="/contact", tags=["contact"])


class ContactSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    name: str = Field(min_length=1, max_length=120, strict=True)
    email: str = Field(min_length=5, max_length=320, strict=True)
    topic: Literal["improvement", "problem", "other"]
    message: str = Field(min_length=10, max_length=4000, strict=True)
    website: Literal[""] = ""

    @field_validator("name")
    @classmethod
    def name_without_controls(cls, value):
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("Invalid name")
        return value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        if not value.isascii() or not re.fullmatch(r'[^@\s<>(),;:"\\]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}', value):
            raise ValueError("Invalid email")
        Address(addr_spec=value)
        return value.lower()

    @field_validator("message")
    @classmethod
    def message_without_controls(cls, value):
        if any((ord(character) < 32 and character not in "\n\r\t") or ord(character) == 127 for character in value):
            raise ValueError("Invalid message")
        return value


async def contact_payload(request: Request):
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(status_code=415, detail="Enviá el mensaje desde el formulario de contacto.")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 24576:
            raise HTTPException(status_code=413, detail="El mensaje es demasiado largo.")
    try:
        return ContactSubmission.model_validate_json(bytes(body))
    except ValueError as exc:
        # Never reflect an email address or message in a validation response.
        raise HTTPException(status_code=422, detail="Revisá tu nombre, correo y mensaje (entre 10 y 4000 caracteres).") from exc


@router.post("", status_code=202)
def create_contact(response: Response, payload: ContactSubmission = Depends(contact_payload), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    if settings.mail_delivery_mode == "disabled":
        raise HTTPException(status_code=503, detail="El formulario no está disponible por ahora. Escribinos a info@mascomatch.com.")
    values = {"name": payload.name, "email": payload.email, "topic": payload.topic, "message": payload.message}
    existing = db.get(ContactMessage, payload.request_id)
    if existing:
        if any(getattr(existing, key) != value for key, value in values.items()):
            raise HTTPException(status_code=409, detail="El mensaje cambió. Volvé a enviarlo.")
        return {"ok": True}
    db.add(ContactMessage(id=payload.request_id, email_available_at=utcnow(), **values))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.get(ContactMessage, payload.request_id)
        if not existing or any(getattr(existing, key) != value for key, value in values.items()):
            raise HTTPException(status_code=409, detail="El mensaje cambió. Volvé a enviarlo.") from exc
    return {"ok": True}
