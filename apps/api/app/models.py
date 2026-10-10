from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Uuid, UniqueConstraint, func
from pgvector.sqlalchemy import Vector
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
    role: Mapped[str] = mapped_column(String(24), default="USER", server_default="USER", nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pets: Mapped[list["Pet"]] = relationship(back_populates="owner")

    @property
    def email_verified(self):
        return self.email_verified_at is not None


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountToken(Base):
    __tablename__ = "account_tokens"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    encrypted_token: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_status: Mapped[str] = mapped_column(String(24), default="PENDING", nullable=False)
    email_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    email_available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


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
    moderation_status: Mapped[str] = mapped_column(String(24), default="VISIBLE", server_default="VISIBLE", nullable=False)
    lost_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_accuracy_meters: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(4000), default="", nullable=False)
    public_location: Mapped[str | None] = mapped_column(String(350))
    search_radius_meters: Mapped[int] = mapped_column(Integer, default=15000, nullable=False)
    pet: Mapped[Pet] = relationship(back_populates="lost_cases")


class Observation(TimestampMixin, Base):
    __tablename__ = "observations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    author_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    species: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    sex: Mapped[str] = mapped_column(String(24), default="unknown", server_default="unknown", nullable=False)
    primary_color: Mapped[str] = mapped_column(String(40), default="unknown", server_default="unknown", nullable=False)
    size: Mapped[str] = mapped_column(String(24), default="unknown", server_default="unknown", nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_accuracy_meters: Mapped[int | None] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(String(24), default="USER_SIGHTING", index=True, nullable=False)
    moderation_status: Mapped[str] = mapped_column(String(24), default="VISIBLE", server_default="VISIBLE", nullable=False)
    share_contact: Mapped[bool] = mapped_column(Boolean,default=False,server_default="false",nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=0.5, nullable=False)
    linked_case_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("lost_cases.id", ondelete="SET NULL"), index=True)
    submission_hash: Mapped[str | None] = mapped_column(String(64))
    public_location: Mapped[str | None] = mapped_column(String(350))
    matching_status: Mapped[str] = mapped_column(String(32), default="NOT_REQUESTED", server_default="NOT_REQUESTED", index=True, nullable=False)
    matching_score: Mapped[float | None] = mapped_column(Float)
    matching_reasons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    matching_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("lost_case_id", "observation_id", name="uq_notification_case_observation"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    lost_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("lost_cases.id", ondelete="CASCADE"), index=True, nullable=False)
    observation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("observations.id", ondelete="CASCADE"), nullable=False)
    match_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_status: Mapped[str] = mapped_column(String(24), default="PENDING", server_default="PENDING", nullable=False)
    email_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    email_available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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


class AnalysisJob(TimestampMixin, Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    deduplication_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    owner_type: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    photo_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", index=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    dispatch_generation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_token: Mapped[str | None] = mapped_column(String(36))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(80))


class FeatureSet(TimestampMixin, Base):
    __tablename__ = "feature_sets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    analysis_job_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)


class Embedding(TimestampMixin, Base):
    __tablename__ = "embeddings"
    analysis_job_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), primary_key=True)
    photo_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    vector: Mapped[list[float]] = mapped_column(Vector(512).with_variant(JSON(), "sqlite"), nullable=False)


class Match(TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("lost_case_id", "observation_id", name="uq_match_case_observation"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    lost_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("lost_cases.id", ondelete="CASCADE"), index=True, nullable=False)
    observation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("observations.id", ondelete="CASCADE"), index=True, nullable=False)
    feature_score: Mapped[float] = mapped_column(Float, nullable=False)
    visual_score: Mapped[float | None] = mapped_column(Float)
    visual_similarity: Mapped[float | None] = mapped_column(Float)
    geo_score: Mapped[float] = mapped_column(Float, nullable=False)
    temporal_score: Mapped[float] = mapped_column(Float, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="NEW", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    feedback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CaseReview(TimestampMixin, Base):
    __tablename__ = "case_reviews"
    __table_args__ = (
        UniqueConstraint("lost_case_id", name="uq_case_review_case"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_case_review_rating"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    lost_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("lost_cases.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(String(800), nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), default="VISIBLE", server_default="VISIBLE", nullable=False)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModerationReport(TimestampMixin, Base):
    __tablename__="moderation_reports"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),primary_key=True,default=uuid4)
    reporter_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True),ForeignKey("users.id",ondelete="SET NULL"))
    target_type: Mapped[str] = mapped_column(String(24),nullable=False)
    target_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),index=True,nullable=False)
    reason: Mapped[str] = mapped_column(String(40),nullable=False)
    detail: Mapped[str] = mapped_column(String(1000),default="",nullable=False)
    status: Mapped[str] = mapped_column(String(24),default="OPEN",index=True,nullable=False)


class AdminAudit(TimestampMixin, Base):
    __tablename__="admin_audit"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),primary_key=True,default=uuid4)
    actor_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),ForeignKey("users.id",ondelete="RESTRICT"),nullable=False)
    action: Mapped[str] = mapped_column(String(40),nullable=False)
    target_type: Mapped[str] = mapped_column(String(24),nullable=False)
    target_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),nullable=False)
    report_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True),ForeignKey("moderation_reports.id",ondelete="SET NULL"))
    details: Mapped[dict] = mapped_column(JSON,default=dict,nullable=False)

