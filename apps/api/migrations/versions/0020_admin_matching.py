"""Single operator access, persisted recommendations and owner feedback history."""
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision = "0020_admin_matching"
down_revision = "0019_publication_numbers"
branch_labels = None
depends_on = None


def upgrade():
    access = op.create_table("admin_access",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), unique=True),
        sa.Column("pending_email", sa.String(320)),
        sa.CheckConstraint("id = 1", name="ck_single_admin_access"))
    connection = op.get_bind()
    users = sa.table("users", sa.column("id", sa.Uuid()), sa.column("role", sa.String()))
    administrators = connection.scalars(sa.select(users.c.id).where(users.c.role == "ADMIN")).all()
    # Preserve an unambiguous existing operator; multiple admins require an explicit choice.
    connection.execute(access.insert().values(id=1, user_id=administrators[0] if len(administrators) == 1 else None))
    op.add_column("matches", sa.Column("recommended_at", sa.DateTime(timezone=True)))
    op.add_column("matches", sa.Column("recommendation_source", sa.String(24)))
    op.add_column("matches", sa.Column("recommended_score", sa.Float()))
    op.add_column("matches", sa.Column("recommendation_snapshot", sa.JSON(), server_default="{}", nullable=False))
    op.create_index("ix_matches_recommended_at", "matches", ["recommended_at"])
    events = op.create_table("match_feedback_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("match_id", sa.Uuid(), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("previous_status", sa.String(32)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("recovered", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("legacy", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_match_feedback_events_match_id", "match_feedback_events", ["match_id"])
    op.create_index("ix_match_feedback_latest", "match_feedback_events", ["match_id", "created_at", "id"])
    matches = sa.table("matches", *[
        sa.column("id", sa.Uuid()), sa.column("lost_case_id", sa.Uuid()), sa.column("observation_id", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)), sa.column("feedback_at", sa.DateTime(timezone=True)),
        sa.column("status", sa.String()), sa.column("final_score", sa.Float()),
        sa.column("recommended_at", sa.DateTime(timezone=True)), sa.column("recommendation_source", sa.String()),
        sa.column("recommended_score", sa.Float()), sa.column("recommendation_snapshot", sa.JSON())])
    observations = sa.table("observations", sa.column("id", sa.Uuid()), sa.column("linked_case_id", sa.Uuid()), sa.column("matching_status", sa.String()))
    cases = sa.table("lost_cases", sa.column("id", sa.Uuid()), sa.column("pet_id", sa.Uuid()))
    pets = sa.table("pets", sa.column("id", sa.Uuid()), sa.column("owner_id", sa.Uuid()))
    rows = connection.execute(sa.select(matches, observations.c.linked_case_id, observations.c.matching_status, pets.c.owner_id)
        .join(observations, matches.c.observation_id == observations.c.id)
        .join(cases, matches.c.lost_case_id == cases.c.id).join(pets, cases.c.pet_id == pets.c.id)).all()
    for row in rows:
        source = "GENERAL" if row.linked_case_id is None else "LINKED" if row.matching_status == "POSSIBLE_MATCH" else None
        if source:
            connection.execute(matches.update().where(matches.c.id == row.id).values(
                recommended_at=row.created_at, recommendation_source=source, recommended_score=row.final_score,
                recommendation_snapshot={"legacy": True, "tracking_version": "historical-state", "first_score_unknown": True}))
        if row.feedback_at and row.status in {"RESOLVED", "FALSE_MATCH", "CONFIRMED_RELEVANT"}:
            connection.execute(events.insert().values(id=uuid4(), match_id=row.id, actor_id=row.owner_id,
                previous_status=None, status=row.status, recovered=False, score=row.final_score,
                legacy=True, created_at=row.feedback_at))


def downgrade():
    op.drop_index("ix_match_feedback_latest", table_name="match_feedback_events")
    op.drop_index("ix_match_feedback_events_match_id", table_name="match_feedback_events")
    op.drop_table("match_feedback_events")
    op.drop_index("ix_matches_recommended_at", table_name="matches")
    for name in ("recommendation_snapshot", "recommended_score", "recommendation_source", "recommended_at"):
        op.drop_column("matches", name)
    op.drop_table("admin_access")
