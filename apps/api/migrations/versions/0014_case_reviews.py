"""Optional public reviews from owners of retired lost notices."""
from alembic import op
import sqlalchemy as sa

revision = "0014_case_reviews"
down_revision = "0013_account_recovery"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "case_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("lost_case_id", sa.Uuid(), sa.ForeignKey("lost_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(800), nullable=False),
        sa.Column("visibility", sa.String(24), server_default="VISIBLE", nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("lost_case_id", name="uq_case_review_case"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_case_review_rating"),
    )
    op.create_index("ix_case_reviews_author_id", "case_reviews", ["author_id"])


def downgrade():
    op.drop_table("case_reviews")
