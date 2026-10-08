"""Basic reports, administrator permissions and action audit."""
from alembic import op
import sqlalchemy as sa
from app.models import ModerationReport,AdminAudit
revision="0008_moderation"
down_revision="0007_observation_traits"
branch_labels=None
depends_on=None


def upgrade():
    bind=op.get_bind()
    # The initial migration reads the current users ORM table when installing afresh.
    if "role" not in {item["name"] for item in sa.inspect(bind).get_columns("users")}:
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("role",sa.String(24),nullable=False,server_default="USER"))
    for name in ("lost_cases","observations"):
        with op.batch_alter_table(name) as batch:
            batch.add_column(sa.Column("moderation_status",sa.String(24),nullable=False,server_default="VISIBLE"))
    ModerationReport.__table__.create(bind=bind)
    op.create_table("admin_audit",sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("actor_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("action",sa.String(40),nullable=False),sa.Column("target_type",sa.String(24),nullable=False),
        sa.Column("target_id",sa.Uuid(),nullable=False),sa.Column("report_id",sa.Uuid(),sa.ForeignKey("moderation_reports.id",ondelete="SET NULL")),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))


def downgrade():
    bind=op.get_bind()
    AdminAudit.__table__.drop(bind=bind)
    ModerationReport.__table__.drop(bind=bind)
    for name in ("lost_cases","observations"):
        with op.batch_alter_table(name) as batch:
            batch.drop_column("moderation_status")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("role")
