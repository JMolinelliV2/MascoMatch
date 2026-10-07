"""Readable public area for lost dog notices, without exact coordinates."""
from alembic import op
import sqlalchemy as sa

revision = "0003_public_lost_dogs"
down_revision = "0002_ai_extraction"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lost_cases", sa.Column("public_location", sa.String(350), nullable=True))


def downgrade() -> None:
    op.drop_column("lost_cases", "public_location")
