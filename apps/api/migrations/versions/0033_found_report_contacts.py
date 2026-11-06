"""Finder contact for linked found-pet reports, disclosed only after confirmation."""
from alembic import op
import sqlalchemy as sa

revision = "0033_found_report_contacts"
down_revision = "0032_report_details"
branch_labels = depends_on = None


def upgrade():
    op.create_table("found_report_contacts",
        sa.Column("observation_id", sa.Uuid(), sa.ForeignKey("observations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("found_report_contacts")
