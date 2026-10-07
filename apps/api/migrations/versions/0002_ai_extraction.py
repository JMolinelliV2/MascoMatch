"""Durable extraction jobs and structured, source-specific features."""
from alembic import op
import sqlalchemy as sa

revision = "0002_ai_extraction"
down_revision = "0001_initial_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("deduplication_key", sa.String(64), nullable=False, unique=True),
        sa.Column("owner_type", sa.String(24), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("photo_id", sa.Uuid(), sa.ForeignKey("photos.id", ondelete="CASCADE")),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("dispatch_generation", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("run_token", sa.String(36)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name in ("owner_type", "owner_id", "photo_id", "status"):
        op.create_index(f"ix_analysis_jobs_{name}", "analysis_jobs", [name])
    op.create_table(
        "feature_sets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("analysis_job_id", sa.Uuid(), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("feature_sets")
    op.drop_table("analysis_jobs")
