"""Private activity buckets and SMTP attempt ledger, starting with observed events only."""
from alembic import op
import sqlalchemy as sa

revision = "0021_admin_operations"
down_revision = "0020_admin_matching"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(timezone=True)))
    op.create_index("ix_users_last_active_at", "users", ["last_active_at"])
    tracking = op.create_table("operational_tracking",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_single_operational_tracking"))
    op.get_bind().execute(tracking.insert().values(id=1))
    op.create_table("user_activity",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), primary_key=True))
    op.create_index("ix_user_activity_occurred_at", "user_activity", ["occurred_at"])
    op.create_table("email_delivery_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("source_type", sa.String(24), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    for name in ("recipient_user_id", "status", "created_at"):
        op.create_index(f"ix_email_delivery_log_{name}", "email_delivery_log", [name])
    op.create_index("ix_analysis_jobs_finished_at", "analysis_jobs", ["finished_at"])
    op.create_index("ix_analysis_jobs_created_at", "analysis_jobs", ["created_at"])


def downgrade():
    op.drop_index("ix_analysis_jobs_created_at", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_finished_at", table_name="analysis_jobs")
    op.drop_table("email_delivery_log")
    op.drop_table("user_activity")
    op.drop_table("operational_tracking")
    op.drop_index("ix_users_last_active_at", table_name="users")
    op.drop_column("users", "last_active_at")
