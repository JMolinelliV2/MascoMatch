"""Persistent notification archiving, independent of matching eligibility."""
from alembic import op
import sqlalchemy as sa

revision = "0018_notification_archive"
down_revision = "0017_contact_messages"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notifications", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("notifications", "archived_at")
