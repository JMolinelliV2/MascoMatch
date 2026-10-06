from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    notification_preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", nullable=False)
    pets: Mapped[list["Pet"]] = relationship(back_populates="owner")


class Pet(TimestampMixin, Base):
    __tablename__ = "pets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    species: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    breed: Mapped[str] = mapped_column(String(120), default="unknown", nullable=False)
    sex: Mapped[str] = mapped_column(String(24), default="unknown", nullable=False)
    size: Mapped[str] = mapped_column(String(24), default="unknown", nullable=False)
    age_estimate: Mapped[str | None] = mapped_column(String(80))
    primary_color: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    secondary_colors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    coat_type: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    distinctive_features: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    collar_description: Mapped[str | None] = mapped_column(String(255))
    microchip_reference: Mapped[str | None] = mapped_column(String(80))
    owner: Mapped[User] = relationship(back_populates="pets")
    lost_cases: Mapped[list["LostCase"]] = relationship(back_populates="pet")


class LostCase(TimestampMixin, Base):
    __tablename__ = "lost_cases"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    pet_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("pets.id", ondelete="RESTRICT"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", index=True, nullable=False)
    lost_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_accuracy_meters: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(4000), default="", nullable=False)
    search_radius_meters: Mapped[int] = mapped_column(Integer, default=15000, nullable=False)
    pet: Mapped[Pet] = relationship(back_populates="lost_cases")


class Observation(TimestampMixin, Base):
    __tablename__ = "observations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    author_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    species: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_accuracy_meters: Mapped[int | None] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(String(24), default="USER_SIGHTING", index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=0.5, nullable=False)


class Photo(TimestampMixin, Base):
    __tablename__ = "photos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_type: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)

