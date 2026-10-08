"""Preserve the physical traits explicitly selected by a reporter."""
from alembic import op
import sqlalchemy as sa
revision="0007_observation_traits"
down_revision="0006_embeddings_matching"
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table("observations") as batch:
        batch.add_column(sa.Column("primary_color",sa.String(40),nullable=False,server_default="unknown"))
        batch.add_column(sa.Column("size",sa.String(24),nullable=False,server_default="unknown"))


def downgrade():
    with op.batch_alter_table("observations") as batch:
        batch.drop_column("size")
        batch.drop_column("primary_color")
