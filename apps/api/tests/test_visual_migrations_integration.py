"""Real PostgreSQL upgrade tests; disposable databases only, explicitly enabled."""
import os
from pathlib import Path
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
import psycopg
from psycopg import sql
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from app.core.config import settings


@pytest.mark.skipif(os.getenv("RUN_VISUAL_MIGRATION_TESTS")!="1",reason="Requires disposable PostgreSQL with pgvector/PostGIS")
def test_fresh_and_existing_postgres_preserve_historical_vectors(monkeypatch):
    base=os.environ["MIGRATION_TEST_DATABASE_URL"]
    assert os.environ.get("DISPOSABLE_STACK")=="mascomatch-ai-upgrade"
    control=psycopg.connect(base.replace("postgresql+psycopg://","postgresql://"),autocommit=True)
    root=Path(__file__).resolve().parents[1]
    cfg=Config(str(root/"alembic.ini"));cfg.set_main_option("script_location",str(root/"migrations"))
    try:
        for existing in (False,True):
            name="mascomatch_upgrade_"+uuid4().hex
            control.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
            url=make_url(base).set(database=name).render_as_string(hide_password=False)
            monkeypatch.setattr(settings,"database_url",url)
            engine=sa.create_engine(url)
            try:
                if existing:
                    command.upgrade(cfg,"0021_admin_operations")
                    owner,photo,job=uuid4(),uuid4(),uuid4()
                    with engine.begin() as connection:
                        metadata=sa.MetaData()
                        photos=sa.Table("photos",metadata,autoload_with=connection)
                        jobs=sa.Table("analysis_jobs",metadata,autoload_with=connection)
                        connection.execute(photos.insert().values(id=photo,owner_type="observation",owner_id=owner,storage_key="historical.jpg",mime_type="image/jpeg"))
                        connection.execute(jobs.insert().values(id=job,deduplication_key="historic",owner_type="observation",owner_id=owner,photo_id=photo,
                            source_type="embedding",provider="open_clip",model="ViT-B-32:openai",prompt_version="old",input_hash="original",input_snapshot={},status="SUCCEEDED"))
                        connection.execute(sa.text("INSERT INTO embeddings (analysis_job_id,photo_id,model,dimension,input_hash,vector) VALUES (:j,:p,'ViT-B-32:openai',512,'original',CAST(:v AS vector))"),
                            {"j":job,"p":photo,"v":"[1,"+",".join(["0"]*511)+"]"})
                command.upgrade(cfg,"head")
                command.upgrade(cfg,"head")  # Safe repeated deploy.
                with engine.connect() as connection:
                    assert connection.scalar(sa.text("SELECT version_num FROM alembic_version"))=="0022_visual_spaces"
                    assert {"vector","postgis"}<=set(connection.scalars(sa.text("SELECT extname FROM pg_extension")))
                    assert {"priority","preprocessing_version","metrics"}<=set(c["name"] for c in sa.inspect(connection).get_columns("analysis_jobs"))
                    if existing:
                        row=connection.execute(sa.text("SELECT provider,revision,space_id,input_hash,vector_dims(vector),vector::text FROM embeddings")).one()
                        assert tuple(row[:5])==("legacy","legacy","legacy","original",512)
                        assert row[5].startswith("[1,0,0,")
                        assert connection.scalar(sa.text("SELECT priority FROM analysis_jobs"))==50
            finally:
                engine.dispose()
                control.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
    finally:
        control.close()
