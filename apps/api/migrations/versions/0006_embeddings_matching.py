"""Local visual embeddings and ranked observation candidates."""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0006_embeddings_matching"
down_revision = "0005_linked_sightings"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    op.create_table("embeddings",
        sa.Column("analysis_job_id", sa.Uuid(), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("photo_id", sa.Uuid(), sa.ForeignKey("photos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model", sa.String(120), nullable=False), sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("vector", Vector(512).with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_embeddings_photo_id", "embeddings", ["photo_id"])
    op.create_index("ix_embeddings_model", "embeddings", ["model"])
    op.create_table("matches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("lost_case_id", sa.Uuid(), sa.ForeignKey("lost_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observation_id", sa.Uuid(), sa.ForeignKey("observations.id", ondelete="CASCADE"), nullable=False),
        *[sa.Column(name, sa.Float(), nullable=name in {"visual_score","visual_similarity"}) for name in
          ("feature_score","visual_score","visual_similarity","geo_score","temporal_score","final_score","evidence_coverage","distance_meters")],
        sa.Column("explanation", sa.JSON(), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("feedback_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("lost_case_id","observation_id",name="uq_match_case_observation"))
    for name in ("lost_case_id","observation_id","final_score"):
        op.create_index("ix_matches_"+name,"matches",[name])
    with op.batch_alter_table("observations") as batch:
        batch.add_column(sa.Column("matching_checked_at", sa.DateTime(timezone=True)))
    unique = next(item for item in sa.inspect(bind).get_unique_constraints("notifications") if item["column_names"] == ["observation_id"])
    with op.batch_alter_table("notifications", naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"}) as batch:
        batch.drop_constraint(unique["name"] or "uq_notifications_observation_id", type_="unique")
        batch.create_unique_constraint("uq_notification_case_observation", ["lost_case_id", "observation_id"])
        batch.add_column(sa.Column("match_id", sa.Uuid()))
        batch.create_foreign_key("fk_notification_match", "matches", ["match_id"], ["id"], ondelete="CASCADE")
        batch.create_index("ix_notifications_match_id", ["match_id"])
    if bind.dialect.name == "postgresql":
        op.create_index("ix_embeddings_vector_cosine", "embeddings", ["vector"], postgresql_using="hnsw", postgresql_ops={"vector": "vector_cosine_ops"})
        op.execute("CREATE INDEX ix_lost_cases_geography ON lost_cases USING gist ((ST_SetSRID(ST_MakePoint(longitude, latitude),4326)::geography)) WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    op.execute("UPDATE observations SET matching_status='PENDING' WHERE linked_case_id IS NULL")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("ix_lost_cases_geography", table_name="lost_cases")
        op.drop_index("ix_embeddings_vector_cosine", table_name="embeddings")
    # A downgrade requires removing the new multi-candidate alerts first.
    op.execute("DELETE FROM notifications WHERE match_id IS NOT NULL")
    with op.batch_alter_table("notifications") as batch:
        batch.drop_index("ix_notifications_match_id")
        batch.drop_constraint("fk_notification_match", type_="foreignkey")
        batch.drop_column("match_id")
        batch.drop_constraint("uq_notification_case_observation", type_="unique")
        batch.create_unique_constraint("uq_notifications_observation_id", ["observation_id"])
    with op.batch_alter_table("observations") as batch:
        batch.drop_column("matching_checked_at")
    op.drop_table("matches")
    op.drop_table("embeddings")
