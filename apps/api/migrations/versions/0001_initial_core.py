"""Initial accounts and evidence records.

Revision ID: 0001_initial_core
Revises:
"""
from alembic import op
import sqlalchemy as sa

from app.db.base import Base
from app import models  # noqa: F401

revision = "0001_initial_core"
down_revision = None
branch_labels = None
depends_on = None
CORE_TABLE_NAMES = ("users", "pets", "lost_cases", "observations", "photos")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("users",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("email",sa.String(320),nullable=False),
        sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("phone",sa.String(32)),
        sa.Column("name",sa.String(120),nullable=False),sa.Column("notification_preferences",sa.JSON(),nullable=False),
        sa.Column("status",sa.String(24),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
    op.create_index("ix_users_email","users",["email"],unique=True)
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in ("pets","photos")])
    # Keep initial evidence tables fixed as later migrations add columns to the current ORM model.
    op.create_table(
        "lost_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("pet_id", sa.Uuid(), sa.ForeignKey("pets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("lost_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("location_accuracy_meters", sa.Integer()),
        sa.Column("description", sa.String(4000), nullable=False),
        sa.Column("search_radius_meters", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lost_cases_pet_id", "lost_cases", ["pet_id"])
    op.create_index("ix_lost_cases_status", "lost_cases", ["status"])
    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("species", sa.String(40), nullable=False),
        sa.Column("description", sa.String(4000), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("location_accuracy_meters", sa.Integer()),
        sa.Column("source_type", sa.String(24), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("author_id", "species", "source_type"):
        op.create_index(f"ix_observations_{column}", "observations", [column])


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in CORE_TABLE_NAMES])

