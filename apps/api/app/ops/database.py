"""Separate the migration owner from the runtime database role."""
import argparse
from pathlib import Path
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.core.config import settings


def connect():
    return psycopg.connect(make_url(settings.database_url).set(drivername="postgresql").render_as_string(hide_password=False))


def provision(action):
    role = sql.Identifier("mascomatch_app")
    with connect() as connection:
        if action == "prepare":
            password = Path("/run/secrets/app_db_password").read_text().strip()
            exists = connection.execute("SELECT 1 FROM pg_roles WHERE rolname='mascomatch_app'").fetchone()
            statement = sql.SQL("ALTER ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}") if exists else sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}")
            connection.execute(statement.format(role, sql.Literal(password)))
            connection.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(connection.info.dbname), role))
        else:
            connection.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
            connection.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}").format(role))
            connection.execute(sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {}").format(role))
            connection.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}").format(role))
            connection.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {}").format(role))
    print("Runtime database role prepared" if action == "prepare" else "Runtime table permissions applied")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare","permissions"])
    provision(parser.parse_args().action)
