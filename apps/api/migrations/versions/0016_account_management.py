"""Contact changes and account deletion with durable private image cleanup."""
from alembic import op
import sqlalchemy as sa

revision = "0016_account_management"
down_revision = "0015_photo_reminders"
branch_labels = None
depends_on = None


def audit_foreign_key():
    return next(key["name"] for key in sa.inspect(op.get_bind()).get_foreign_keys("admin_audit")
                if key["constrained_columns"] == ["actor_id"])


def upgrade():
    op.add_column("users", sa.Column("pending_email", sa.String(320)))
    op.add_column("account_tokens", sa.Column("destination_email", sa.String(320)))
    op.create_table("photo_deletions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("storage_key", sa.String(512), unique=True, nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False))
    op.create_index("ix_photo_deletions_available_at", "photo_deletions", ["available_at"])
    key = audit_foreign_key()
    with op.batch_alter_table("admin_audit", naming_convention={"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}) as batch:
        batch.drop_constraint(key or "fk_admin_audit_actor_id_users", type_="foreignkey")
        batch.alter_column("actor_id", existing_type=sa.Uuid(), nullable=True)
        batch.create_foreign_key("fk_admin_audit_actor_id_users", "users", ["actor_id"], ["id"], ondelete="SET NULL")


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM admin_audit WHERE actor_id IS NULL")):
        raise RuntimeError("Deleted audit actors cannot be restored; restore a backup before downgrading.")
    with op.batch_alter_table("admin_audit") as batch:
        batch.drop_constraint(audit_foreign_key(), type_="foreignkey")
        batch.alter_column("actor_id", existing_type=sa.Uuid(), nullable=False)
        batch.create_foreign_key("fk_admin_audit_actor_id_users", "users", ["actor_id"], ["id"], ondelete="RESTRICT")
    op.drop_table("photo_deletions")
    op.drop_column("account_tokens", "destination_email")
    op.drop_column("users", "pending_email")
