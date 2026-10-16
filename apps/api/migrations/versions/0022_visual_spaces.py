"""Preserve historical vectors, add immutable spaces, priorities and safe telemetry."""
from alembic import op
import sqlalchemy as sa

revision = "0022_visual_spaces"
down_revision = "0021_admin_operations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("analysis_jobs", sa.Column("priority", sa.Integer(), nullable=False, server_default="50"))
    op.add_column("analysis_jobs", sa.Column("preprocessing_version", sa.String(240), nullable=False, server_default="legacy"))
    op.add_column("analysis_jobs", sa.Column("metrics", sa.JSON(), nullable=False, server_default="{}"))
    op.create_index("ix_analysis_jobs_dispatch", "analysis_jobs", ["status", "priority", "available_at"])
    for name, length in (("provider",40), ("revision",80), ("preprocessing_version",240), ("space_id",64)):
        op.add_column("embeddings", sa.Column(name, sa.String(length), nullable=False, server_default="legacy"))
    op.add_column("embeddings", sa.Column("quality", sa.JSON(), nullable=False, server_default="{}"))
    op.create_index("ix_embeddings_space_id", "embeddings", ["space_id"])


def downgrade():
    # Roll back with feature flags. Removing these columns would erase provenance.
    raise RuntimeError("Use PET_REID_ENABLED=false; this data-preserving migration cannot be downgraded.")
