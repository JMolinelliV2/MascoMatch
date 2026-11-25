"""One current editable review per account; preserve older reviews as history."""
from alembic import op
import sqlalchemy as sa

revision = "0034_account_reviews"
down_revision = "0033_found_report_contacts"
branch_labels = depends_on = None


def upgrade():
    op.add_column("case_reviews", sa.Column("is_current", sa.Boolean(), server_default=sa.true(), nullable=False))
    # Legacy aliases never authorize publishing the account's actual name.
    op.add_column("case_reviews", sa.Column("is_anonymous", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("case_reviews", sa.Column("moderation_hidden", sa.Boolean(), server_default=sa.false(), nullable=False))
    # Withdrawal used to replace HIDDEN, so recover the latest moderation
    # decision from its audit trail without making any review public.
    op.execute("""UPDATE case_reviews AS review SET moderation_hidden = true
        WHERE review.visibility = 'HIDDEN' OR (review.visibility = 'WITHDRAWN' AND (
            SELECT audit.action FROM admin_audit AS audit
            WHERE audit.target_type = 'case_review' AND audit.target_id = review.id
              AND audit.action IN ('HIDE_REVIEW', 'RESTORE_REVIEW')
            ORDER BY audit.created_at DESC, audit.id DESC LIMIT 1
        ) = 'HIDE_REVIEW')""")
    op.execute("""UPDATE case_reviews SET is_current = false WHERE id IN (
        SELECT id FROM (SELECT id, ROW_NUMBER() OVER (
            PARTITION BY author_id ORDER BY created_at DESC, id DESC
        ) AS position FROM case_reviews) ranked WHERE position > 1
    )""")
    op.create_index("uq_case_review_current_author", "case_reviews", ["author_id"], unique=True,
                    postgresql_where=sa.text("is_current = true"), sqlite_where=sa.text("is_current = 1"))
    connection = op.get_bind()
    foreign_key = next(key["name"] for key in sa.inspect(connection).get_foreign_keys("case_reviews")
                       if key["constrained_columns"] == ["lost_case_id"])
    op.drop_constraint(foreign_key, "case_reviews", type_="foreignkey")
    op.alter_column("case_reviews", "lost_case_id", existing_type=sa.Uuid(), nullable=True)
    op.create_foreign_key("fk_case_review_origin", "case_reviews", "lost_cases", ["lost_case_id"], ["id"], ondelete="SET NULL")


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM case_reviews WHERE lost_case_id IS NULL")):
        raise RuntimeError("Reviews without an origin notice require an explicit data migration before downgrading.")
    op.drop_constraint("fk_case_review_origin", "case_reviews", type_="foreignkey")
    op.alter_column("case_reviews", "lost_case_id", existing_type=sa.Uuid(), nullable=False)
    op.create_foreign_key("case_reviews_lost_case_id_fkey", "case_reviews", "lost_cases", ["lost_case_id"], ["id"], ondelete="CASCADE")
    op.drop_index("uq_case_review_current_author", table_name="case_reviews")
    for column in ("moderation_hidden", "is_anonymous", "is_current"):
        op.drop_column("case_reviews", column)
