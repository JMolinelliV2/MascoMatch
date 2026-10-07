"""User-declared sex for sightings and found animals."""
from alembic import op
import sqlalchemy as sa

revision = "0004_observation_sex"
down_revision = "0003_public_lost_dogs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("observations", sa.Column("sex", sa.String(24), nullable=False, server_default="unknown"))


def downgrade() -> None:
    op.drop_column("observations", "sex")
