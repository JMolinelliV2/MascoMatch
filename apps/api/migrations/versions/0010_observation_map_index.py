"""Index public observation area filtering with PostGIS."""
from alembic import op
revision="0010_observation_map_index"
down_revision="0009_admin_corrections"
branch_labels=None
depends_on=None


def upgrade():
    if op.get_bind().dialect.name=="postgresql":
        op.execute("CREATE INDEX ix_observations_geography ON observations USING gist ((ST_SetSRID(ST_MakePoint(longitude,latitude),4326)::geography)) WHERE latitude IS NOT NULL AND longitude IS NOT NULL")


def downgrade():
    if op.get_bind().dialect.name=="postgresql":op.drop_index("ix_observations_geography",table_name="observations")
