"""Local visual embeddings and ranked observation candidates."""
from alembic import op
import sqlalchemy as sa
from app.db.base import Base
from app import models

revision = "0006_embeddings_matching"
down_revision = "0005_linked_sightings"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[models.Embedding.__table__, models.Match.__table__])
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
    models.Match.__table__.drop(bind=bind)
    models.Embedding.__table__.drop(bind=bind)
