"""Persistent delayed reminders for new lost notices without a photo."""
from alembic import op
import sqlalchemy as sa

revision = "0015_photo_reminders"
down_revision = "0014_case_reviews"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "photo_reminders",
        sa.Column("lost_case_id", sa.Uuid(), sa.ForeignKey("lost_cases.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_photo_reminders_due", "photo_reminders", ["status", "available_at"])


def downgrade():
    op.drop_table("photo_reminders")
