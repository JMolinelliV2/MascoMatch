"""Optional, author supplied breed, colors and accessories for every report."""
from alembic import op
import sqlalchemy as sa

revision = "0032_report_details"
down_revision = "0031_donations"
branch_labels = depends_on = None


def upgrade():
    for table in ("pets", "observations"):
        op.add_column(table, sa.Column("collar_status", sa.String(12), nullable=False, server_default="unknown"))
        op.add_column(table, sa.Column("collar_color", sa.String(40)))
        op.add_column(table, sa.Column("clothing_status", sa.String(12), nullable=False, server_default="unknown"))
        op.add_column(table, sa.Column("clothing_description", sa.String(120)))
        op.add_column(table, sa.Column("clothing_color", sa.String(40)))
    op.add_column("observations", sa.Column("breed", sa.String(120), nullable=False, server_default="unknown"))
    op.add_column("observations", sa.Column("secondary_colors", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("observations", sa.Column("collar_description", sa.String(255)))


def downgrade():
    for name in ("collar_description", "secondary_colors", "breed"):
        op.drop_column("observations", name)
    for table in ("pets", "observations"):
        for name in ("clothing_color", "clothing_description", "clothing_status", "collar_color", "collar_status"):
            op.drop_column(table, name)
