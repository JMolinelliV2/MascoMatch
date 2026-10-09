"""Verified email and single-use account recovery messages."""
from alembic import op
import sqlalchemy as sa
revision="0013_account_recovery"
down_revision="0012_auth_sessions"
branch_labels=None
depends_on=None


def upgrade():
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True)))
    op.create_table("account_tokens",
        sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),
        sa.Column("kind",sa.String(24),nullable=False),
        sa.Column("token_hash",sa.String(64),nullable=False,unique=True),
        sa.Column("encrypted_token",sa.String(512),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("consumed_at",sa.DateTime(timezone=True)),
        sa.Column("email_status",sa.String(24),nullable=False),
        sa.Column("email_attempts",sa.Integer(),nullable=False),
        sa.Column("email_available_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_account_tokens_user_id","account_tokens",["user_id"])


def downgrade():
    op.drop_table("account_tokens")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("email_verified_at")
