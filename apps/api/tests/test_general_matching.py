from datetime import timedelta
from uuid import UUID, uuid4
import math
import pytest
from sqlalchemy import select
from app.analysis.service import schedule_text, schedule_photo, utcnow, purge_photo
from app.core.config import settings
from app.embeddings.provider import normalize, DIMENSION
from app.matching.engine import evaluate_observation, request_matching
from app.matching.scoring import feature_similarity, combine
from app.models import AnalysisJob, Embedding, FeatureSet, LostCase, Match, Notification, Observation, Pet, Photo, User


def setup_evidence(db, monkeypatch, far=False):
    monkeypatch.setattr(settings,"ai_enabled",True)
    owner=User(email="match-owner@example.test",name="Owner",password_hash="unused")
    reporter=User(email="match-reporter@example.test",name="Reporter",password_hash="unused")
    db.add_all([owner,reporter]);db.flush()
    pet=Pet(owner_id=owner.id,name="Luna",species="dog",primary_color="brown",size="medium")
    db.add(pet);db.flush()
    case=LostCase(pet_id=pet.id,lost_at=utcnow()-timedelta(hours=2),latitude=-34.9,longitude=-56.1,search_radius_meters=15000)
    observation=Observation(author_id=reporter.id,species="dog",description="Brown medium dog",observed_at=utcnow(),latitude=-34.901,longitude=-56.101 if not far else -55.0)
    db.add_all([case,observation]);db.flush()
    job=schedule_text(db,"observation",observation.id);job.status="SUCCEEDED"
    db.add(FeatureSet(analysis_job_id=job.id,features={name:{"value":value,"confidence":.95,"source":"text"} for name,value in {"species":"dog","primary_color":"brown","size":"medium"}.items()}));db.flush()
    return owner,reporter,pet,case,observation


def test_text_only_matching_notifies_and_deduplicates(db_factory,monkeypatch):
    with db_factory() as db:
        _,_,_,case,observation=setup_evidence(db,monkeypatch)
        evaluate_observation(db,observation.id);db.commit()
        assert observation.matching_status=="MATCHES_FOUND"
        match=db.scalar(select(Match));assert match.visual_score is None
        assert match.final_score>=settings.matching_notify_threshold
        assert len(match.explanation)>=3
        evaluate_observation(db,observation.id);db.commit()
        assert len(list(db.scalars(select(Notification))))==1
        assert db.scalar(select(Notification)).match_id==match.id


@pytest.mark.parametrize("change",["far","future_loss","different_species","closed","missing_location","different_sex","insufficient"])
def test_incompatible_and_insufficient_evidence_is_not_notified(db_factory,monkeypatch,change):
    with db_factory() as db:
        _,_,pet,case,observation=setup_evidence(db,monkeypatch,far=change=="far")
        if change=="future_loss":case.lost_at=utcnow()+timedelta(hours=1)
        if change=="different_species":pet.species="cat"
        if change=="closed":case.status="CLOSED"
        if change=="missing_location":observation.latitude=None
        if change=="different_sex":pet.sex="female";observation.sex="male"
        if change=="insufficient":observation.description="Changed evidence";pet.primary_color="unknown";pet.size="unknown"
        db.flush();evaluate_observation(db,observation.id);db.commit()
        assert not list(db.scalars(select(Notification)))


def test_one_report_can_match_multiple_cases(db_factory,monkeypatch):
    with db_factory() as db:
        _,_,pet,case,observation=setup_evidence(db,monkeypatch)
        second=LostCase(pet_id=pet.id,lost_at=case.lost_at,latitude=case.latitude,longitude=case.longitude)
        db.add(second);db.flush();evaluate_observation(db,observation.id);db.commit()
        assert len(list(db.scalars(select(Match))))==2
        assert len(list(db.scalars(select(Notification))))==2


def test_feedback_survives_rescoring_and_prevents_realert(db_factory,monkeypatch):
    with db_factory() as db:
        _,_,_,case,observation=setup_evidence(db,monkeypatch)
        evaluate_observation(db,observation.id);db.flush()
        match=db.scalar(select(Match));match.status="FALSE_MATCH"
        request_matching(db,"lost_case",case.id);evaluate_observation(db,observation.id);db.commit()
        assert match.status=="FALSE_MATCH"
        assert not db.scalar(select(Notification)).is_active


def test_pending_extraction_waits_then_recovers(db_factory,monkeypatch):
    with db_factory() as db:
        _,_,_,_,observation=setup_evidence(db,monkeypatch)
        job=db.scalar(select(AnalysisJob));job.status="PENDING";db.flush()
        evaluate_observation(db,observation.id);assert observation.matching_status=="WAITING_ANALYSIS"
        assert not list(db.scalars(select(Notification)))
        job.status="SUCCEEDED";db.flush();evaluate_observation(db,observation.id)
        assert observation.matching_status=="MATCHES_FOUND"


def test_embedding_schedule_is_independent_and_removed_with_photo(db_factory,monkeypatch):
    monkeypatch.setattr(settings,"embeddings_enabled",True)
    monkeypatch.setattr(settings,"ai_enabled",False)
    with db_factory() as db:
        user=User(email="embedding@example.test",name="Owner",password_hash="unused");db.add(user);db.flush()
        pet=Pet(owner_id=user.id,name="Animal",species="dog");db.add(pet);db.flush()
        photo=Photo(owner_type="pet",owner_id=pet.id,storage_key="test.jpg",mime_type="image/jpeg");db.add(photo);db.flush()
        schedule_photo(db,photo);schedule_photo(db,photo)
        jobs=list(db.scalars(select(AnalysisJob)));assert len(jobs)==1 and jobs[0].source_type=="embedding"
        db.add(Embedding(analysis_job_id=jobs[0].id,photo_id=photo.id,model=jobs[0].model,dimension=512,input_hash=jobs[0].input_hash,vector=[1.0]+[0.0]*511));db.flush()
        purge_photo(db,photo.id);assert not list(db.scalars(select(Embedding)))


@pytest.mark.parametrize("vector",[[0.0]*512,[float("nan")]+[0.0]*511,[1.0]*3])
def test_invalid_visual_vectors_are_rejected(vector):
    from app.analysis.providers import ProviderError
    with pytest.raises(ProviderError):normalize(vector)


def test_normalized_vectors_and_scores_are_finite():
    vector=normalize([1.0]*DIMENSION)
    assert math.isclose(sum(value**2 for value in vector),1)
    same=combine(1,.99,0,15000,0)[0]
    different=combine(1,.2,0,15000,0)[0]
    assert same>different
    assert feature_similarity({"species":"dog"},{"species":"cat"})[3]


def test_feedback_and_results_are_scoped_to_their_users(client,auth_headers,db_factory,monkeypatch):
    # Use real route authentication, without relying on tokens stored outside the test.
    session=client.post("/api/v1/auth/login",json={"email":"owner@example.com","password":"a-strong-passphrase"}).json()
    with db_factory() as db:
        owner,reporter,pet,case,observation=setup_evidence(db,monkeypatch)
        pet.owner_id=UUID(session["user"]["id"])
        db.flush();evaluate_observation(db,observation.id);db.commit()
        match=db.scalar(select(Match));mid=str(match.id);oid=str(observation.id);cid=str(case.id)
    assert client.get(f"/api/v1/matches/observations/{oid}",headers=auth_headers).status_code==404
    result=client.get(f"/api/v1/matches/lost-cases/{cid}",headers=auth_headers)
    assert result.status_code==200 and len(result.json()["items"])==1
    assert client.patch(f"/api/v1/matches/{mid}/feedback",headers=auth_headers,json={"status":"FALSE_MATCH"}).status_code==200
    assert client.patch(f"/api/v1/matches/{mid}/feedback",headers=auth_headers,json={"status":"NOT_A_STATUS"}).status_code==422
    assert client.patch(f"/api/v1/matches/{mid}/feedback",json={"status":"RESOLVED"}).status_code==401


def test_private_contact_requires_explicit_consent(client,auth_headers,db_factory):
    pet=client.post("/api/v1/pets",headers=auth_headers,json={"name":"Luna","species":"dog","primary_color":"brown","size":"medium"}).json()
    case=client.post("/api/v1/lost-cases",headers=auth_headers,json={"pet_id":pet["id"],"lost_at":(utcnow()-timedelta(hours=1)).isoformat(),"latitude":-34.9,"longitude":-56.1}).json()
    reporter=client.post("/api/v1/auth/register",json={"email":"reporter-consent@example.test","password":"test-only-passphrase","name":"Reporter"}).json()
    headers={"Authorization":f"Bearer {reporter['access_token']}"}
    for consent in (False,True):
        obs=client.post("/api/v1/observations",headers=headers,json={"species":"dog","primary_color":"brown","size":"medium","description":"Matching dog","observed_at":utcnow().isoformat(),"latitude":-34.901,"longitude":-56.101,"share_contact":consent}).json()
        with db_factory() as db:evaluate_observation(db,UUID(obs["id"]));db.commit()
        assert "share_contact" not in client.get(f"/api/v1/observations/{obs['id']}").json()
    notices=client.get("/api/v1/notifications",headers=auth_headers).json()["items"]
    assert len(notices)==2
    assert {item["reporter_contact"] for item in notices}=={None,"reporter-consent@example.test"}


def test_email_groups_reports_for_the_same_case(client,auth_headers,db_factory,monkeypatch):
    with db_factory() as db:
        _,_,_,case,observation=setup_evidence(db,monkeypatch)
        evaluate_observation(db,observation.id)
        second=Observation(author_id=observation.author_id,species="dog",primary_color="brown",size="medium",description="Another compatible report",observed_at=utcnow(),latitude=-34.902,longitude=-56.102)
        db.add(second);db.flush();evaluate_observation(db,second.id);db.commit()
    from app.notifications import email
    from datetime import timedelta
    messages=[]
    monkeypatch.setattr(settings,"mail_delivery_mode","preview")
    monkeypatch.setattr(email,"send_message",lambda message:messages.append(message))
    with db_factory() as db:
        for item in db.scalars(select(Notification)):item.email_available_at=utcnow()-timedelta(seconds=1)
        db.commit()
    assert email.deliver_pending(db_factory)==1
    assert len(messages)==1 and "2 reportes nuevos" in messages[0]["Subject"]
    assert email.deliver_pending(db_factory)==0


def test_conflicting_image_species_does_not_trigger_automatic_alert(db_factory, monkeypatch):
    monkeypatch.setattr(settings, "embeddings_enabled", False)
    with db_factory() as db:
        _, _, _, _, observation = setup_evidence(db, monkeypatch)
        photo = Photo(owner_type="observation", owner_id=observation.id,
                      storage_key="conflicting-example.jpg", mime_type="image/jpeg")
        db.add(photo)
        db.flush()
        job = schedule_photo(db, photo)
        job.status = "SUCCEEDED"
        db.add(FeatureSet(analysis_job_id=job.id, features={
            "species": {"value": "cat", "confidence": .95, "source": "image"},
        }))
        db.flush()
        evaluate_observation(db, observation.id)
        assert observation.matching_status == "INSUFFICIENT"
        assert not list(db.scalars(select(Notification)))


def test_dispatcher_queues_only_enabled_sources(db_factory, monkeypatch):
    from app.analysis import queue
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    with db_factory() as db:
        _, _, _, _, observation = setup_evidence(db, monkeypatch)
        db.scalar(select(AnalysisJob)).status = "PENDING"
        photo = Photo(owner_type="observation", owner_id=observation.id,
                      storage_key="embedding-example.jpg", mime_type="image/jpeg")
        db.add(photo)
        db.flush()
        schedule_photo(db, photo)
        db.commit()
    calls = []
    class LocalQueue:
        def enqueue(self, *args, **kwargs):
            calls.append(args)
    monkeypatch.setattr(queue, "SessionLocal", db_factory)
    monkeypatch.setattr(queue, "get_queue", lambda: LocalQueue())
    monkeypatch.setattr(settings, "ai_enabled", False)
    assert queue.dispatch_pending() == 1
    assert len(calls) == 1
    with db_factory() as db:
        assert db.get(AnalysisJob, UUID(calls[0][1])).source_type == "embedding"
        assert all(job.status == "PENDING" for job in db.scalars(
            select(AnalysisJob).where(AnalysisJob.source_type != "embedding")))
