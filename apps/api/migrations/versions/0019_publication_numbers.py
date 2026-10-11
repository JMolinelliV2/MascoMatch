"""Stable public numbers shared by lost notices and observations."""
from alembic import op
import sqlalchemy as sa

revision = "0019_publication_numbers"
down_revision = "0018_notification_archive"
branch_labels = None
depends_on = None


def upgrade():
    number_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
    numbers = op.create_table(
        "publication_numbers",
        sa.Column("id", number_type, primary_key=True, autoincrement=True),
        sqlite_autoincrement=True,
    )
    tables = {}
    for name in ("lost_cases", "observations"):
        op.add_column(name, sa.Column("public_number", number_type, nullable=True))
        tables[name] = sa.table(
            name, sa.column("id", sa.Uuid()),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("public_number", number_type),
        )

    reports = sa.union_all(*(
        sa.select(table.c.id, table.c.created_at, sa.literal(name).label("source"))
        for name, table in tables.items()
    )).subquery()
    connection = op.get_bind()
    existing = connection.execute(sa.select(reports).order_by(reports.c.created_at, reports.c.source, reports.c.id)).all()
    for report in existing:
        number = connection.execute(numbers.insert().values()).inserted_primary_key[0]
        table = tables[report.source]
        connection.execute(table.update().where(table.c.id == report.id).values(public_number=number))

    for name in tables:
        with op.batch_alter_table(name) as batch:
            batch.alter_column("public_number", existing_type=number_type, nullable=False)
            batch.create_unique_constraint(f"uq_{name}_public_number", ["public_number"])
            batch.create_foreign_key(f"fk_{name}_publication_number", "publication_numbers", ["public_number"], ["id"])


def downgrade():
    for name in ("observations", "lost_cases"):
        with op.batch_alter_table(name) as batch:
            batch.drop_constraint(f"fk_{name}_publication_number", type_="foreignkey")
            batch.drop_constraint(f"uq_{name}_public_number", type_="unique")
            batch.drop_column("public_number")
    op.drop_table("publication_numbers")
