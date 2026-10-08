"""Optional contact sharing only with the owner of a compatible case."""
from alembic import op
import sqlalchemy as sa
revision="0011_private_report_contact"
down_revision="0010_observation_map_index"
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table("observations") as batch:
        batch.add_column(sa.Column("share_contact",sa.Boolean(),nullable=False,server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("observations") as batch:batch.drop_column("share_contact")
