"""Retain the previous evidence when an administrator corrects a description."""
from alembic import op
import sqlalchemy as sa
revision="0009_admin_corrections"
down_revision="0008_moderation"
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table("admin_audit") as batch:
        batch.add_column(sa.Column("details",sa.JSON(),nullable=False,server_default=sa.text("'{}'")))


def downgrade():
    with op.batch_alter_table("admin_audit") as batch:batch.drop_column("details")
