"""Offline numbering-plan validation for new contact details; no SMS or API calls."""
import re
from typing import Annotated

import phonenumbers
from pydantic import AfterValidator, Field

PHONE_ERROR = "Ingresá un teléfono válido. Para Uruguay, por ejemplo 099 123 456; para otros países, incluí + y el código de país."


def validate_phone(value: str) -> str:
    value = " ".join(value.split())
    if not value or len(value) > 32 or not re.fullmatch(r"\+?[0-9 ()\-.]+", value):
        raise ValueError(PHONE_ERROR)
    try:
        number = phonenumbers.parse(value, "UY")
    except phonenumbers.NumberParseException:
        raise ValueError(PHONE_ERROR) from None
    if not phonenumbers.is_valid_number(number) or number.extension:
        raise ValueError(PHONE_ERROR)
    return value


def optional_phone(value: str | None) -> str | None:
    return validate_phone(value) if value and value.strip() else None


OptionalPhone = Annotated[str | None, Field(max_length=32), AfterValidator(optional_phone)]
