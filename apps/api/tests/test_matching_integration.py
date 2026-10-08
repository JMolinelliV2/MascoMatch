"""Real PostgreSQL/PostGIS/pgvector, local CLIP, MinIO and an isolated RQ worker.

All evidence lives in a newly created random database schema. Only its own objects
and queue are removed. No email is sent and no real publication is modified.
"""
from datetime import timedelta
from io import BytesIO
import os
from pathlib import Path
from uuid import uuid4
import pytest
from PIL import Image, ImageOps
from rq import Queue, SpawnWorker
from rq.serializers import JSONSerializer
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from app.analysis import queue, tasks
from app.analysis.service import schedule_photo, utcnow
from app.core.config import settings
from app.core.image_storage import store_private_image, delete_private_image
from app.db.base import Base
from app.matching.engine import evaluate_observation
from app.models import Embedding, LostCase, Match, Notification, Observation, Pet, Photo, User


@pytest.mark.skipif(os.getenv("RUN_MATCHING_INTEGRATION")!="1",reason="Requires PostgreSQL, Redis, MinIO and installed local CLIP weights")
def test_real_visual_candidates_and_text_only_reports(monkeypatch):
    image_path=os.getenv("AI_SMOKE_IMAGE_PATH")
    assert image_path
    image=Path(image_path).read_bytes()
    with Image.open(BytesIO(image)) as source:
        buffer=BytesIO();ImageOps.mirror(source).save(buffer,format="JPEG");other=buffer.getvalue()
    schema="matching_check_"+uuid4().hex
    control=create_engine(settings.database_url)
    with control.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url=make_url(settings.database_url).update_query_dict({"options":f"-csearch_path={schema},public"})
    engine=create_engine(url)
    factory=sessionmaker(bind=engine)
    real=queue.get_queue()
    isolated=Queue("mascomatch-visual-check-"+uuid4().hex,connection=real.connection,serializer=JSONSerializer)
    stored=[]
    try:
        # checkfirst sees public tables through search_path and would skip creation.
        # The schema is newly created, so create every test table explicitly.
        Base.metadata.create_all(engine, checkfirst=False)
        with engine.begin() as connection:
            assert connection.scalar(text("SELECT current_schema()")) == schema
            assert connection.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_schema=:schema"), {"schema":schema}) == len(Base.metadata.tables)
            connection.execute(text("CREATE INDEX embedding_test_cosine ON embeddings USING hnsw (vector vector_cosine_ops)"))
        monkeypatch.setenv("DATABASE_URL",url.render_as_string(hide_password=False))
        monkeypatch.setenv("EMBEDDINGS_ENABLED","true")
        monkeypatch.setattr(settings,"embeddings_enabled",True)
        monkeypatch.setattr(settings,"ai_enabled",False)
        monkeypatch.setattr(queue,"SessionLocal",factory)
        monkeypatch.setattr(tasks,"SessionLocal",factory)
        monkeypatch.setattr(queue,"get_queue",lambda:isolated)
        with factory() as db:
            owner=User(email="owner@example.test",name="Owner",password_hash="unused")
            reporter=User(email="reporter@example.test",name="Reporter",password_hash="unused")
            db.add_all([owner,reporter]);db.flush()
            pet=Pet(owner_id=owner.id,name="Luna",species="dog",primary_color="brown",size="medium")
            db.add(pet);db.flush()
            case=LostCase(pet_id=pet.id,lost_at=utcnow()-timedelta(hours=1),latitude=-34.9,longitude=-56.1)
            observation=Observation(author_id=reporter.id,species="dog",primary_color="brown",size="medium",description="Brown medium dog",observed_at=utcnow(),latitude=-34.901,longitude=-56.101)
            no_photo=Observation(author_id=reporter.id,species="dog",primary_color="brown",size="medium",description="Same traits without a photo",observed_at=utcnow(),latitude=-34.902,longitude=-56.102)
            db.add_all([case,observation,no_photo]);db.flush()
            identities=(case.id,observation.id,no_photo.id)
            for kind,identity,payload in [("lost_case",case.id,image),("observation",observation.id,other)]:
                key,width,height=store_private_image(kind,identity,"image/jpeg",payload);stored.append(key)
                photo=Photo(owner_type=kind,owner_id=identity,storage_key=key,mime_type="image/jpeg",width=width,height=height)
                db.add(photo);db.flush();schedule_photo(db,photo)
            db.commit()
        assert queue.dispatch_pending()==2
        SpawnWorker([isolated],connection=isolated.connection,serializer=JSONSerializer).work(burst=True)
        with factory() as db:
            embeddings=list(db.scalars(select(Embedding)))
            assert len(embeddings)==2
            assert all(item.dimension==512 for item in embeddings)
            evaluate_observation(db,identities[1]);evaluate_observation(db,identities[2]);db.commit()
            matches=list(db.scalars(select(Match).order_by(Match.final_score.desc())))
            assert len(matches)==2
            visual=next(item for item in matches if item.observation_id==identities[1])
            assert visual.visual_similarity>.75
            assert visual.visual_score is not None
            assert next(item for item in matches if item.observation_id==identities[2]).visual_score is None
            assert len(list(db.scalars(select(Notification))))==2
            print(f"Local CLIP cosine={visual.visual_similarity:.4f}; PostgreSQL ranking and text-only alerts passed")
    finally:
        isolated.delete(delete_jobs=True)
        for key in stored:delete_private_image(key)
        engine.dispose()
        with control.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()
