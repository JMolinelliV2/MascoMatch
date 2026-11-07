from datetime import timedelta
from copy import deepcopy
from uuid import UUID, uuid4
import math
from types import SimpleNamespace
import pytest
from sqlalchemy import select
from app.analysis.service import schedule_text, schedule_photo, utcnow, purge_photo
from app.core.config import settings
from app.embeddings.provider import normalize, DIMENSION
from app.matching.engine import evaluate_observation, request_matching
from app.matching import engine
from app.matching.scoring import feature_similarity, combine
from app.models import AnalysisJob, Embedding, FeatureSet, LostCase, Match, MatchFeedbackEvent, Notification, Observation, Pet, Photo, User


def setup_evidence(db, monkeypatch, far=False):
    monkeypatch.setattr(settings,"ai_enabled",True)
    owner=User(email="match-owner@example.test",name="Owner",password_hash="unused",email_verified_at=utcnow())
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


def test_private_contact_requires_explicit_consent(client,auth_headers,db_factory,confirm_account):
    pet=client.post("/api/v1/pets",headers=auth_headers,json={"name":"Luna","species":"dog","primary_color":"brown","size":"medium"}).json()
    case=client.post("/api/v1/lost-cases",headers=auth_headers,json={"pet_id":pet["id"],"lost_at":(utcnow()-timedelta(hours=1)).isoformat(),"latitude":-34.9,"longitude":-56.1}).json()
    reporter=client.post("/api/v1/auth/register",json={"email":"reporter-consent@example.test","password":"test-only-passphrase","name":"Reporter"}).json()
    headers={"Authorization":f"Bearer {reporter['access_token']}"}
    confirm_account("reporter-consent@example.test")
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
    monkeypatch.setattr(queue, "get_queue", lambda *args: LocalQueue())
    monkeypatch.setattr(settings, "ai_enabled", False)
    assert queue.dispatch_pending() == 1
    assert len(calls) == 1
    with db_factory() as db:
        assert db.get(AnalysisJob, UUID(calls[0][1])).source_type == "embedding"
        assert all(job.status == "PENDING" for job in db.scalars(
            select(AnalysisJob).where(AnalysisJob.source_type != "embedding")))


def declared_reports(db, monkeypatch, pet_values=None, observation_values=None):
    """No photos or model results: only the declarations should drive these cases."""
    monkeypatch.setattr(settings, "ai_enabled", False)
    monkeypatch.setattr(settings, "embeddings_enabled", False)
    owner = User(email="declared-owner@example.test", name="Owner", password_hash="unused", email_verified_at=utcnow())
    reporter = User(email="declared-reporter@example.test", name="Reporter", password_hash="unused")
    db.add_all([owner, reporter]); db.flush()
    values = {"species": "dog", "primary_color": "brown", "size": "medium"}
    pet = Pet(owner_id=owner.id, name="Luna", **(values | (pet_values or {})))
    db.add(pet); db.flush()
    case = LostCase(pet_id=pet.id, lost_at=utcnow()-timedelta(hours=2), latitude=-34.9, longitude=-56.1, search_radius_meters=15000)
    observation = Observation(author_id=reporter.id, description="Reported pet", observed_at=utcnow(),
                              latitude=-34.9, longitude=-56.1, **(values | (observation_values or {})))
    db.add_all([case, observation]); db.flush()
    return pet, case, observation


def test_declared_traits_accept_different_models_and_ignore_unknown_or_private_fields():
    pet = SimpleNamespace(species="dog", sex="unknown", primary_color="brown", size="medium",
                          breed="Labrador", coat_type="short", secondary_colors=["white"],
                          distinctive_features=["pecho blanco"], name="Private name", phone="Private phone")
    observation = SimpleNamespace(species="dog", sex="not_visible", primary_color="brown", size="medium",
                                  breed="Labrador", secondary_colors=["white"])
    assert engine.declared_traits(pet) == {
        "species": "dog", "primary_color": "brown", "size": "medium", "breed_type": "Labrador",
        "coat_length": "short", "secondary_colors": ["white"], "distinctive_features": ["pecho blanco"],
    }
    assert engine.declared_traits(observation) == {
        "species": "dog", "primary_color": "brown", "size": "medium", "breed_type": "Labrador", "secondary_colors": ["white"],
    }
    assert engine.declared_traits(SimpleNamespace(breed=" uncertain ", secondary_colors=["unknown", "", "not_visible"])) == {}


@pytest.mark.parametrize("left,right,similarity,coverage", [
    ({"collar_status": "yes", "collar_color": "red"}, {"collar_status": "yes", "collar_color": "Rojo"}, 1, .48),
    ({"collar_status": "yes", "collar_color": "red"}, {"collar_status": "yes", "collar_color": "blue"}, .455/.48, .48),
    ({"collar_status": "yes"}, {"collar_status": "no"}, .43/.48, .48),
    ({"collar_status": "no"}, {"collar_status": "no"}, 1, .43),
    ({"collar_status": "yes"}, {"collar_status": "unknown"}, 1, .43),
    ({"collar_status": "yes", "collar_color": "red"}, {"collar_status": "yes"}, 1, .48),
    ({"clothing_status": "yes", "clothing_color": "azul"}, {"clothing_status": "yes", "clothing_color": "blue"}, 1, .48),
    ({"clothing_status": "yes", "clothing_color": "blue"}, {"clothing_status": "yes", "clothing_color": "green"}, .455/.48, .48),
    ({"clothing_status": "no"}, {"clothing_status": "no"}, 1, .43),
    ({"collar_status": "yes"}, {"clothing_status": "yes"}, 1, .43),
    ({"collar_status": "yes", "collar_color": "Azul petróleo"},
     {"collar_status": "yes", "collar_color": "azul petroleo"}, 1, .48),
    ({"collar_status": "yes", "collar_color": "unknown"}, {"collar_status": "yes", "collar_color": "red"}, 1, .48),
])
def test_structured_accessories_compare_only_shared_known_parts(left, right, similarity, coverage):
    traits = {"species": "dog", "primary_color": "brown", "size": "medium"}
    a, b = engine.comparable_traits(SimpleNamespace(**left), traits, SimpleNamespace(**right), traits)
    score, available, _, contradiction = feature_similarity(a, b)
    assert score == pytest.approx(similarity)
    assert available == pytest.approx(coverage)
    assert not contradiction
    assert "accessories" not in traits  # Preparation must not change the original evidence.
    assert feature_similarity(b, a)[:2] == pytest.approx((score, available))


@pytest.mark.parametrize("label", ["collar rojo", "collar colorado", "collar rojo de tela", "red collar"])
def test_declared_accessories_are_compatible_with_bounded_model_labels(label):
    base = {"species": "dog", "primary_color": "brown", "size": "medium"}
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_status="yes", collar_color="red"), base,
        SimpleNamespace(), base | {"accessories": [label]})
    assert feature_similarity(left, right)[:2] == pytest.approx((1, .48))


def test_accessory_declarations_override_each_subfield_but_allow_missing_color():
    base = {"species": "dog", "primary_color": "brown", "size": "medium"}
    inferred = base | {"accessories": ["collar rojo", "camiseta azul"]}
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_status="yes", collar_color="blue", clothing_status="yes"), inferred,
        SimpleNamespace(collar_status="yes", collar_color="blue", clothing_status="yes", clothing_color="blue"), base)
    assert feature_similarity(left, right)[:2] == pytest.approx((1, .48))
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_status="no"), inferred,
        SimpleNamespace(collar_status="yes", collar_color="red"), base)
    assert feature_similarity(left, right)[:2] == pytest.approx((.43/.48, .48))


def test_declared_color_overrides_inference_without_inventing_presence():
    base = {"species": "dog", "primary_color": "brown", "size": "medium"}
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_status="unknown", collar_color="blue"), base | {"accessories": ["collar rojo"]},
        SimpleNamespace(collar_color="blue"), base | {"accessories": ["collar azul"]})
    assert feature_similarity(left, right)[:2] == pytest.approx((1, .48))
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_color="red"), base,
        SimpleNamespace(collar_status="yes", collar_color="red"), base)
    assert feature_similarity(left, right)[:2] == pytest.approx((1, .43))


@pytest.mark.parametrize("label", ["sin collar", "no collar", "collar incierto", "posiblemente collar rojo",
                                  "collar not_visible", "pelaje rojo", "parece un collar", "collar rojo y camiseta azul",
                                  "collar invisible", "collar rojo?", "collar pendiente de confirmar"])
def test_unrecognized_negated_or_uncertain_model_labels_supply_no_accessory_coverage(label):
    base = {"species": "dog", "primary_color": "brown", "size": "medium"}
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_status="yes", collar_color="red"), base,
        SimpleNamespace(), base | {"accessories": [label]})
    assert feature_similarity(left, right)[:2] == pytest.approx((1, .43))


def test_accessory_colors_stay_with_their_item_and_conflicting_colors_stay_unknown():
    base = {"species": "dog", "primary_color": "brown", "size": "medium"}
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_status="yes", collar_color="red", clothing_status="yes", clothing_color="blue"), base,
        SimpleNamespace(), base | {"accessories": ["collar rojo", "camiseta azul"]})
    assert feature_similarity(left, right)[:2] == pytest.approx((1, .48))
    left, right = engine.comparable_traits(
        SimpleNamespace(collar_status="yes", collar_color="red"), base,
        SimpleNamespace(), base | {"accessories": ["collar rojo", "collar azul"]})
    assert feature_similarity(left, right)[:2] == pytest.approx((1, .48))  # Presence only, no guessed color.


def test_without_structured_accessories_legacy_inferred_scores_are_unchanged():
    left = {"species": "dog", "primary_color": "brown", "accessories": ["collar rojo"]}
    right = {"species": "dog", "primary_color": "brown", "accessories": ["collar colorado"]}
    prepared = engine.comparable_traits(SimpleNamespace(), left, SimpleNamespace(collar_status="unknown"), right)
    assert prepared == (left, right)
    assert feature_similarity(*prepared) == feature_similarity(left, right)
    assert feature_similarity(*prepared)[:2] == pytest.approx((.33/.38, .38))


@pytest.mark.parametrize("details,coverage", [
    ({}, .43),
    ({"secondary_colors": ["white"]}, .51),
    ({"breed": "Labrador retriever"}, .45),
    ({"collar_status": "yes", "collar_color": "red"}, .48),
    ({"clothing_status": "yes", "clothing_color": "blue"}, .48),
    ({"collar_status": "no", "clothing_status": "no"}, .43),
])
def test_general_matching_uses_symmetric_declarations_without_ai_or_photos(db_factory, monkeypatch, details, coverage):
    with db_factory() as db:
        _, case, observation = declared_reports(db, monkeypatch, details, details)
        evaluate_observation(db, observation.id); db.flush()
        match = db.scalar(select(Match))
        assert match is not None and match.feature_score == pytest.approx(1)
        assert match.evidence_coverage == pytest.approx(coverage)
        assert match.visual_similarity is None
        days = (observation.observed_at-case.lost_at).total_seconds()/86400
        assert match.final_score == pytest.approx(combine(1, None, 0, case.search_radius_meters, days)[0])
        assert len(list(db.scalars(select(Notification)))) == 1
        assert not list(db.scalars(select(AnalysisJob)))
        assert not list(db.scalars(select(Photo)))


def test_known_breed_compared_with_unknown_breed_does_not_penalize(db_factory, monkeypatch):
    with db_factory() as db:
        _, _, observation = declared_reports(db, monkeypatch, {"breed": "Labrador"})
        evaluate_observation(db, observation.id); db.flush()
        match = db.scalar(select(Match))
        assert match.feature_score == pytest.approx(1)
        assert match.evidence_coverage == pytest.approx(.43)


def test_structured_observation_colors_and_breed_outrank_model_inference(db_factory, monkeypatch):
    with db_factory() as db:
        details = {"breed": "Labrador", "secondary_colors": ["white"]}
        _, _, observation = declared_reports(db, monkeypatch, details, details)
        monkeypatch.setattr(settings, "ai_enabled", True)
        job = schedule_text(db, "observation", observation.id); job.status = "SUCCEEDED"
        db.add(FeatureSet(analysis_job_id=job.id, features={name: {"value": value, "confidence": .99, "source": "text"}
            for name, value in {"primary_color": "black", "size": "large", "breed_type": "Caniche", "secondary_colors": ["black"]}.items()}))
        db.flush(); evaluate_observation(db, observation.id); db.flush()
        match = db.scalar(select(Match))
        assert match.feature_score == pytest.approx(1)
        assert match.evidence_coverage == pytest.approx(.53)


@pytest.mark.parametrize("side", ["observation", "lost_case"])
def test_strong_image_species_conflict_remains_excluding_with_declared_traits(db_factory, monkeypatch, side):
    with db_factory() as db:
        _, case, observation = declared_reports(db, monkeypatch)
        monkeypatch.setattr(settings, "ai_enabled", True)
        photo = Photo(owner_type=side, owner_id=observation.id if side == "observation" else case.id,
                      storage_key="isolated-conflict.jpg", mime_type="image/jpeg")
        db.add(photo); db.flush()
        job = schedule_photo(db, photo); job.status = "SUCCEEDED"
        db.add(FeatureSet(analysis_job_id=job.id, features={"species": {"value": "cat", "confidence": .99, "source": "image"}}))
        db.flush(); evaluate_observation(db, observation.id)
        assert not list(db.scalars(select(Match)))
        assert not list(db.scalars(select(Notification)))


@pytest.mark.parametrize("contradiction", [True, False])
def test_definitive_feature_rejection_does_not_load_or_compare_vectors(db_factory, monkeypatch, contradiction):
    with db_factory() as db:
        pet_values = {"sex": "female"} if contradiction else {}
        observed_values = {"sex": "male"} if contradiction else {"primary_color": "white", "size": "large"}
        _, _, observation = declared_reports(db, monkeypatch, pet_values, observed_values)
        monkeypatch.setattr(settings, "embeddings_enabled", True)
        def unexpected(*args):
            pytest.fail("A definitive feature rejection must precede vector queries and comparisons")
        monkeypatch.setattr(engine, "vectors", unexpected)
        monkeypatch.setattr(engine, "visual_evidence", unexpected)
        evaluate_observation(db, observation.id)
        assert not list(db.scalars(select(Match)))


@pytest.mark.parametrize("color,size,coverage", [("unknown", "unknown", .15), ("unknown", "medium", .25), ("brown", "unknown", .33)])
@pytest.mark.parametrize("visual", [None, 1.0])
def test_coverage_is_checked_after_visual_availability(db_factory, monkeypatch, color, size, coverage, visual):
    with db_factory() as db:
        details = {"primary_color": color, "size": size}
        _, _, observation = declared_reports(db, monkeypatch, details, details)
        calls = []
        def compare(*args):
            calls.append(True)
            return visual, "open_clip" if visual is not None else None, 1
        monkeypatch.setattr(engine, "visual_evidence", compare)
        evaluate_observation(db, observation.id); db.flush()
        assert calls == [True]
        match = db.scalar(select(Match))
        assert (match is not None) == (visual is not None and coverage >= .25)
        if match:
            assert match.evidence_coverage == pytest.approx(coverage)
        assert not list(db.scalars(select(Notification)))  # Still below the automatic-alert coverage gate.


@pytest.mark.parametrize("status,should_alert", [("unknown", False), ("no", False), ("yes", True)])
def test_accessory_coverage_can_enable_alerts_but_shared_absence_cannot(db_factory, monkeypatch, status, should_alert):
    with db_factory() as db:
        details = {"size": "unknown", "collar_status": status, "collar_color": "red" if status == "yes" else None}
        _, _, observation = declared_reports(db, monkeypatch, details, details)
        evaluate_observation(db, observation.id); db.flush()
        assert bool(list(db.scalars(select(Notification)))) == should_alert
        if should_alert:
            assert db.scalar(select(Match)).evidence_coverage == pytest.approx(.38)


@pytest.mark.parametrize("pet_details,observed_details,feature,coverage", [
    ({"collar_status": "yes", "collar_color": "red"}, {"collar_status": "yes", "collar_color": "blue"}, .355/.38, .38),
    ({"collar_status": "yes"}, {"collar_status": "no"}, .33/.38, .38),
    ({"secondary_colors": ["white"]}, {"secondary_colors": ["black"]}, .33/.41, .41),
    ({"breed": "Labrador"}, {"breed": "Caniche"}, .33/.35, .35),
])
def test_additional_disagreements_adjust_score_without_new_exclusions(db_factory, monkeypatch, pet_details, observed_details, feature, coverage):
    with db_factory() as db:
        _, case, observation = declared_reports(db, monkeypatch,
            {"size": "unknown"} | pet_details, {"size": "unknown"} | observed_details)
        evaluate_observation(db, observation.id); db.flush()
        match = db.scalar(select(Match))
        assert match.feature_score == pytest.approx(feature)
        assert match.evidence_coverage == pytest.approx(coverage)
        days = (observation.observed_at-case.lost_at).total_seconds()/86400
        assert match.final_score == pytest.approx(combine(feature, None, 0, case.search_radius_meters, days)[0])
        assert len(list(db.scalars(select(Notification)))) == 1  # Existing gates still decide the alert.


def test_all_optional_declarations_empty_remain_insufficient_without_models(db_factory, monkeypatch):
    with db_factory() as db:
        empty = {"sex": "unknown", "size": "unknown", "primary_color": "unknown", "breed": "",
                 "secondary_colors": [], "collar_status": "unknown", "clothing_status": "unknown"}
        _, _, observation = declared_reports(db, monkeypatch, empty, empty)
        evaluate_observation(db, observation.id); db.flush()
        assert not list(db.scalars(select(Match)))
        assert not list(db.scalars(select(Notification)))
        assert not list(db.scalars(select(AnalysisJob)))


def test_observation_vectors_are_loaded_once_for_surviving_candidates(db_factory, monkeypatch):
    with db_factory() as db:
        pet, case, observation = declared_reports(db, monkeypatch)
        second = LostCase(pet_id=pet.id, lost_at=case.lost_at, latitude=case.latitude, longitude=case.longitude)
        db.add(second); db.flush()
        monkeypatch.setattr(settings, "embeddings_enabled", True)
        loads, comparisons = [], []
        monkeypatch.setattr(engine, "vectors", lambda *args: loads.append(True) or [])
        monkeypatch.setattr(engine, "visual_evidence", lambda db, vectors, candidate: comparisons.append(candidate.id) or (1, "pet_reid", 1))
        evaluate_observation(db, observation.id)
        assert loads == [True]
        assert set(comparisons) == {case.id, second.id}


@pytest.mark.parametrize("status", ["FALSE_MATCH", "RESOLVED", "NOTIFIED"])
def test_rescoring_preserves_feedback_receipts_and_sent_email(db_factory, monkeypatch, status):
    with db_factory() as db:
        pet, _, observation = declared_reports(db, monkeypatch)
        evaluate_observation(db, observation.id); db.flush()
        match, notification = db.scalar(select(Match)), db.scalar(select(Notification))
        if status != "NOTIFIED":
            db.add(MatchFeedbackEvent(match_id=match.id, actor_id=pet.owner_id, previous_status=match.status,
                status=status, score=match.final_score, context_snapshot={"recommendation": deepcopy(match.recommendation_snapshot)}))
            match.feedback_at = utcnow()
        match.status = status
        match.first_viewed_at = utcnow(); match.first_viewed_rank = 2; match.viewed_snapshot = {"score": match.final_score}
        notification.read_at = notification.archived_at = utcnow(); notification.email_status = "SENT"
        db.flush()
        history = [(event.id, event.status, event.score, deepcopy(event.context_snapshot)) for event in db.scalars(select(MatchFeedbackEvent))]
        previous = (match.id, match.feedback_at, match.recommended_at, deepcopy(match.recommendation_snapshot),
                    notification.id, notification.read_at, notification.archived_at,
                    match.first_viewed_at, match.first_viewed_rank, deepcopy(match.viewed_snapshot))
        request_matching(db, "observation", observation.id)
        evaluate_observation(db, observation.id); db.flush()
        assert (match.id, match.feedback_at, match.recommended_at, match.recommendation_snapshot,
                notification.id, notification.read_at, notification.archived_at,
                match.first_viewed_at, match.first_viewed_rank, match.viewed_snapshot) == previous
        assert [(event.id, event.status, event.score, event.context_snapshot) for event in db.scalars(select(MatchFeedbackEvent))] == history
        assert match.status == status and notification.email_status == "SENT"
        assert len(list(db.scalars(select(Notification)))) == 1
        if status != "NOTIFIED":
            assert not notification.is_active


def test_completed_history_is_not_automatically_reprocessed(db_factory, monkeypatch):
    with db_factory() as db:
        _, _, observation = declared_reports(db, monkeypatch)
        evaluate_observation(db, observation.id)
        observation.matching_checked_at = utcnow()-timedelta(days=1)
        db.commit()
    calls = []
    monkeypatch.setattr(engine, "evaluate_observation", lambda *args: calls.append(True))
    engine.reconcile_general(db_factory)
    assert not calls
