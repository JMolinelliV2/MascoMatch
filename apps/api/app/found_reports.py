"""Private contact and owner-facing pet details for linked custody reports."""
import re
from pydantic import BaseModel, Field, field_validator
from app.report_details import ReportDetailsCreate


class FinderContact(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=32)

    @field_validator("name", "phone", mode="before")
    @classmethod
    def trim(cls, value):
        return " ".join(value.split()) if isinstance(value, str) else value

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        if not any(c.isalpha() for c in value):
            raise ValueError("Ingresá tu nombre.")
        return value

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value):
        if not re.fullmatch(r"\+?[0-9 ()\-.]+", value) or not 7 <= sum(c.isdigit() for c in value) <= 15:
            raise ValueError("Ingresá un número de teléfono válido, con código de país.")
        return value


def pet_details(observation):
    return {**{name: getattr(observation, name) for name in ReportDetailsCreate.model_fields},
            "species": observation.species, "sex": observation.sex, "size": observation.size}
