"""Initial accounts and evidence records.

Revision ID: 0001_initial_core
Revises:
"""
from alembic import op

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
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in CORE_TABLE_NAMES])


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in CORE_TABLE_NAMES])

