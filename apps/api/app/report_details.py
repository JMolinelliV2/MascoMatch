"""Optional traits supplied by a person, independent of model suggestions."""
import unicodedata
from typing import Literal
from pydantic import BaseModel, Field, model_validator

AccessoryStatus = Literal["unknown", "yes", "no"]
COLOR_LABELS = {"brown": "Marrón", "black": "Negro", "white": "Blanco", "gray": "Gris",
                "cream": "Crema", "orange": "Naranja", "tan": "Beige / canela", "red": "Rojizo", "multicolor": "Varios colores"}


def color_value(value):
    if value is None:
        return value
    if not isinstance(value, str):
        raise ValueError("Ingresá un color como texto.")
    value = value.strip()
    key = "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))
    aliases = {"marron": "brown", "negro": "black", "blanco": "white", "gris": "gray", "crema": "cream",
               "naranja": "orange", "beige": "tan", "canela": "tan", "beige / canela": "tan", "rojizo": "red", "varios colores": "multicolor"}
    return aliases.get(key, key if key in COLOR_LABELS else value) or "unknown"


class ReportDetails(BaseModel):
    breed: str = Field(default="unknown", max_length=120)
    secondary_colors: list[str] = Field(default_factory=list)
    collar_status: AccessoryStatus = "unknown"
    collar_color: str | None = Field(default=None, max_length=40)
    collar_description: str | None = Field(default=None, max_length=255)
    clothing_status: AccessoryStatus = "unknown"
    clothing_description: str | None = Field(default=None, max_length=120)
    clothing_color: str | None = Field(default=None, max_length=40)


class NormalizeDetails(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def normalize_details(cls, data):
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for key in ("breed", "primary_color", "secondary_colors", "collar_status", "clothing_status"):
            if key in data and data[key] is None:
                raise ValueError(f"{key}: indicá un valor o 'unknown'.")
        if "breed" in data:
            if not isinstance(data["breed"], str):
                raise ValueError("Ingresá la raza como texto.")
            data["breed"] = data["breed"].strip() or "unknown"
        for key in ("primary_color", "collar_color", "clothing_color"):
            if key in data:
                data[key] = color_value(data[key])
                if key != "primary_color" and data[key] == "unknown":
                    data[key] = None
        if "secondary_colors" in data and isinstance(data["secondary_colors"], list):
            if any(not isinstance(v, str) for v in data["secondary_colors"]):
                raise ValueError("Ingresá los colores como texto.")
            values = [color_value(v) for v in data["secondary_colors"] if isinstance(v, str) and v.strip()]
            if any(len(v) > 40 for v in values):
                raise ValueError("Cada color puede tener hasta 40 caracteres.")
            data["secondary_colors"] = list(dict.fromkeys(v for v in values if v != "unknown"))
        for key in ("collar_description", "clothing_description"):
            if key in data and isinstance(data[key], str):
                data[key] = data[key].strip() or None
        for prefix in ("collar", "clothing"):
            if data.get(f"{prefix}_status") == "no":
                data[f"{prefix}_color"] = None
                data[f"{prefix}_description"] = None
        return data


class ReportDetailsUpdate(NormalizeDetails):
    breed: str | None = Field(default=None, max_length=120)
    secondary_colors: list[str] | None = Field(default=None, max_length=5)
    collar_status: AccessoryStatus | None = None
    collar_color: str | None = Field(default=None, max_length=40)
    collar_description: str | None = Field(default=None, max_length=255)
    clothing_status: AccessoryStatus | None = None
    clothing_description: str | None = Field(default=None, max_length=120)
    clothing_color: str | None = Field(default=None, max_length=40)


class ReportDetailsCreate(ReportDetails, NormalizeDetails):
    secondary_colors: list[str] = Field(default_factory=list, max_length=5)
    primary_color: str = Field(default="unknown", max_length=40)
