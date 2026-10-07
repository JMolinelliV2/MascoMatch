from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Species = Literal["dog", "cat", "rabbit", "bird", "other", "unknown"]
Sex = Literal["male", "female", "unknown"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=10, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserRead(ORMModel):
    id: UUID
    email: str
    name: str
    phone: str | None
    notification_preferences: dict
    status: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class PetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    species: Species
    breed: str = Field(default="unknown", max_length=120)
    sex: Sex = "unknown"
    size: str = Field(default="unknown", max_length=24)
    age_estimate: str | None = Field(default=None, max_length=80)
    primary_color: str = Field(default="unknown", max_length=40)
    secondary_colors: list[str] = Field(default_factory=list)
    coat_type: str = Field(default="unknown", max_length=40)
    distinctive_features: list[str] = Field(default_factory=list)
    collar_description: str | None = Field(default=None, max_length=255)
    microchip_reference: str | None = Field(default=None, max_length=80)


class PetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    species: Species | None = None
    breed: str | None = Field(default=None, max_length=120)
    sex: Sex | None = None
    size: str | None = Field(default=None, max_length=24)
    age_estimate: str | None = Field(default=None, max_length=80)
    primary_color: str | None = Field(default=None, max_length=40)
    secondary_colors: list[str] | None = None
    coat_type: str | None = Field(default=None, max_length=40)
    distinctive_features: list[str] | None = None
    collar_description: str | None = Field(default=None, max_length=255)
    microchip_reference: str | None = Field(default=None, max_length=80)

    @field_validator("sex")
    @classmethod
    def sex_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("Use 'unknown' when sex is not known")
        return value


class PetRead(ORMModel):
    id: UUID
    owner_id: UUID
    name: str
    species: str
    breed: str
    sex: str
    size: str
    age_estimate: str | None
    primary_color: str
    secondary_colors: list
    coat_type: str
    distinctive_features: list
    collar_description: str | None
    microchip_reference: str | None
    created_at: datetime
    updated_at: datetime


class LostCaseCreate(BaseModel):
    pet_id: UUID
    lost_at: datetime
    last_seen_at: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy_meters: int | None = Field(default=None, ge=0)
    description: str = Field(default="", max_length=4000)
    public_location: str | None = Field(default=None, max_length=350)
    search_radius_meters: int = Field(default=15000, ge=100, le=200000)

    @model_validator(mode="after")
    def paired_coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class LostCaseUpdate(BaseModel):
    status: Literal["ACTIVE", "FOUND", "CLOSED", "CANCELLED"] | None = None
    last_seen_at: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy_meters: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=4000)
    public_location: str | None = Field(default=None, max_length=350)
    search_radius_meters: int | None = Field(default=None, ge=100, le=200000)


class LostCaseRead(ORMModel):
    id: UUID
    pet_id: UUID
    status: str
    lost_at: datetime
    last_seen_at: datetime | None
    latitude: float | None
    longitude: float | None
    location_accuracy_meters: int | None
    description: str
    public_location: str | None
    search_radius_meters: int
    created_at: datetime
    updated_at: datetime


class PublicLostDogRead(BaseModel):
    id: UUID
    name: str
    species: Species
    sex: str
    breed: str
    size: str
    primary_color: str
    description: str
    public_location: str | None
    lost_at: datetime
    photo_url: str | None


class PublicLostDogList(BaseModel):
    items: list[PublicLostDogRead]
    total: int
    limit: int
    offset: int


class ObservationCreate(BaseModel):
    species: Species
    sex: Sex = "unknown"
    description: str = Field(min_length=1, max_length=4000)
    observed_at: datetime
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy_meters: int | None = Field(default=None, ge=0)
    source_type: Literal["USER_SIGHTING", "FOUND_ANIMAL"] = "USER_SIGHTING"
    confidence: float = Field(default=0.5, ge=0, le=1)

    @model_validator(mode="after")
    def paired_coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class ObservationUpdate(BaseModel):
    species: Species | None = None
    sex: Sex | None = None
    description: str | None = Field(default=None, min_length=1, max_length=4000)
    observed_at: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy_meters: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator("sex")
    @classmethod
    def sex_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("Use 'unknown' when sex is not known")
        return value


class ObservationRead(ORMModel):
    id: UUID
    species: str
    sex: str
    description: str
    observed_at: datetime
    latitude: float | None
    longitude: float | None
    location_accuracy_meters: int | None
    source_type: str
    confidence: float
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def hide_exact_public_location(self):
        # Precise coordinates remain in storage for future internal matching.
        if self.latitude is not None and self.longitude is not None:
            self.latitude = round(self.latitude, 2)
            self.longitude = round(self.longitude, 2)
        return self


class PhotoCreate(BaseModel):
    owner_type: Literal["pet", "lost_case", "observation"]
    owner_id: UUID
    storage_key: str = Field(min_length=1, max_length=512)
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    width: int | None = Field(default=None, ge=1, le=30000)
    height: int | None = Field(default=None, ge=1, le=30000)


class PhotoRead(ORMModel):
    id: UUID
    owner_type: str
    owner_id: UUID
    storage_key: str
    url: str | None
    mime_type: str
    width: int | None
    height: int | None
    created_at: datetime


class PhotoUpdate(BaseModel):
    width: int | None = Field(default=None, ge=1, le=30000)
    height: int | None = Field(default=None, ge=1, le=30000)


class PhotoUploadRead(BaseModel):
    photo: PhotoRead
    signed_url: str

