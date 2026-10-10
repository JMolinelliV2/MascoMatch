"""Private contact messages with durable email delivery."""
from alembic import op
import sqlalchemy as sa

revision = "0017_contact_messages"
down_revision = "0016_account_management"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("contact_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("topic", sa.String(24), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("email_status", sa.String(24), nullable=False),
        sa.Column("email_attempts", sa.Integer(), nullable=False),
        sa.Column("email_available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email_sent_at", sa.DateTime(timezone=True)))
    op.create_index("ix_contact_messages_delivery", "contact_messages", ["email_status", "email_available_at"])


def downgrade():
    op.drop_table("contact_messages")
