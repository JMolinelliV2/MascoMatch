"""Sightings from a specific lost notice and private owner notifications."""
from alembic import op
import sqlalchemy as sa

revision = "0005_linked_sightings"
down_revision = "0004_observation_sex"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("observations") as batch:
        batch.add_column(sa.Column("linked_case_id", sa.Uuid()))
        batch.create_foreign_key("fk_observations_linked_case_id", "lost_cases", ["linked_case_id"], ["id"], ondelete="SET NULL")
        batch.add_column(sa.Column("submission_hash", sa.String(64)))
        batch.add_column(sa.Column("public_location", sa.String(350)))
        batch.add_column(sa.Column("matching_status", sa.String(32), nullable=False, server_default="NOT_REQUESTED"))
        batch.add_column(sa.Column("matching_score", sa.Float()))
        batch.add_column(sa.Column("matching_reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
        batch.create_index("ix_observations_linked_case_id", ["linked_case_id"])
        batch.create_index("ix_observations_matching_status", ["matching_status"])
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lost_case_id", sa.Uuid(), sa.ForeignKey("lost_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observation_id", sa.Uuid(), sa.ForeignKey("observations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("body", sa.String(1000), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("email_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("email_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("email_available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("email_sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name in ("owner_id", "lost_case_id"):
        op.create_index(f"ix_notifications_{name}", "notifications", [name])


def downgrade() -> None:
    op.drop_table("notifications")
    with op.batch_alter_table("observations") as batch:
        batch.drop_index("ix_observations_matching_status")
        batch.drop_index("ix_observations_linked_case_id")
        batch.drop_constraint("fk_observations_linked_case_id", type_="foreignkey")
        for name in ("matching_reasons", "matching_score", "matching_status", "public_location", "submission_hash", "linked_case_id"):
            batch.drop_column(name)
