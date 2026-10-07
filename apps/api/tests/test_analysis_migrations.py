import importlib

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect


def test_fresh_and_existing_core_database_migrations(monkeypatch):
    core = importlib.import_module("migrations.versions.0001_initial_core")
    extraction = importlib.import_module("migrations.versions.0002_ai_extraction")
    public = importlib.import_module("migrations.versions.0003_public_lost_dogs")
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        monkeypatch.setattr(core, "op", operations)
        monkeypatch.setattr(extraction, "op", operations)
        monkeypatch.setattr(public, "op", operations)
        # SQLite cannot install PostgreSQL extensions; table migrations remain real DDL.
        monkeypatch.setattr(operations, "execute", lambda statement: None)
        core.upgrade()
        assert set(inspect(connection).get_table_names()) == set(core.CORE_TABLE_NAMES)
        extraction.upgrade()
        assert set(inspect(connection).get_table_names()) == set(core.CORE_TABLE_NAMES) | {"analysis_jobs", "feature_sets"}
        extraction.downgrade()
        assert set(inspect(connection).get_table_names()) == set(core.CORE_TABLE_NAMES)
        extraction.upgrade()
        assert "feature_sets" in inspect(connection).get_table_names()
        assert "public_location" not in {column["name"] for column in inspect(connection).get_columns("lost_cases")}
        public.upgrade()
        assert "public_location" in {column["name"] for column in inspect(connection).get_columns("lost_cases")}
        public.downgrade()
        assert "public_location" not in {column["name"] for column in inspect(connection).get_columns("lost_cases")}
        public.upgrade()
    engine.dispose()
