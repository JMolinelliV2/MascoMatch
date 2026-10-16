import json
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import pytest
from PIL import Image
from app.analysis.service import utcnow
from app.analysis.gemma_setup import manifest_bytes,GEMMA_DIGEST
from app.analysis.image_preprocessing import prepare_vlm_image
from app.matching import evaluate_visual
from app.matching.export_labels import collect_labels
from app.models import Match,MatchFeedbackEvent,Photo
from tests.test_visual_upgrade import records,jpeg


def test_pinned_gemma_manifest_and_no_silent_install(tmp_path):
    import hashlib
    from app.analysis.gemma_setup import install
    assert hashlib.sha256(manifest_bytes()).hexdigest()==GEMMA_DIGEST
    with pytest.raises(ValueError,match="accept-gemma-terms"):
        install(tmp_path)
    with pytest.raises(ValueError,match="Missing/corrupt"):
        install(tmp_path,check=True)
    assert not list(tmp_path.iterdir())


def test_labels_require_explicit_owner_and_exclude_uncertainty(db_factory):
    with db_factory() as db:
        pet,case,obs,photos=records(db)
        match=Match(lost_case_id=case.id,observation_id=obs.id,final_score=.99,
                    feature_score=1,geo_score=1,temporal_score=1,evidence_coverage=1,distance_meters=0)
        db.add(match);db.flush()
        report=collect_labels(db)
        assert len(report["labels"])==1 and report["labels"][0]["source"]=="owner_assigned_photos"
        db.add(MatchFeedbackEvent(match_id=match.id,actor_id=pet.owner_id,status="CONFIRMED_RELEVANT",recovered=False,legacy=False,created_at=utcnow()))
        db.flush()
        assert len(collect_labels(db)["labels"])==1
        db.add(MatchFeedbackEvent(match_id=match.id,actor_id=pet.owner_id,status="RESOLVED",recovered=False,legacy=False,created_at=utcnow()+timedelta(seconds=1)))
        db.flush()
        assert len(collect_labels(db)["labels"])==3
        db.add(MatchFeedbackEvent(match_id=match.id,actor_id=pet.owner_id,status="FALSE_MATCH",recovered=False,legacy=False,created_at=utcnow()+timedelta(seconds=2)))
        db.flush()
        report=collect_labels(db)
        assert sum(p["label"]=="DIFFERENT_IDENTITY" for p in report["labels"])==2
        assert "email" not in json.dumps(report) and "vector" not in json.dumps(report)


def dataset(tmp_path):
    rows=[]
    for index,(identity,role) in enumerate((("one","gallery"),("one","query"),("two","gallery"),("two","query"))):
        path=tmp_path/f"{index}.jpg"
        Image.new("RGB",(100+index,100),"brown" if identity=="one" else "black").save(path)
        rows.append({"file":path.name,"identity":identity,"role":role,"species":"dog","split":"test"})
    path=tmp_path/"dataset.json";path.write_text(json.dumps({"images":rows,"hard_negatives":[["0.jpg","2.jpg"]]}))
    return path,rows


def test_evaluator_metrics_and_disjoint_splits(tmp_path,monkeypatch):
    path,rows=dataset(tmp_path)
    loaded,hard=evaluate_visual.load_dataset(path)
    vectors=iter([[1,0],[1,0],[0,1],[0,1]])
    monkeypatch.setattr(evaluate_visual,"get_embedding_provider",lambda spec:SimpleNamespace(encode_result=lambda *_:SimpleNamespace(vector=next(vectors))))
    report=evaluate_visual.evaluate(loaded,hard,"pet_reid")
    assert report["positive_pairs"]==2 and report["negative_pairs"]==4 and report["hard_negatives"]==1
    assert report["top_1"]==report["recall_at_5"]==1 and report["false_positive_rate"]==0
    rows[1]["split"]="train"
    path.write_text(json.dumps({"images":rows}))
    with pytest.raises(ValueError,match="more than one"):
        evaluate_visual.load_dataset(path)


def test_evaluator_rejects_traversal_and_duplicate_bytes(tmp_path):
    path,rows=dataset(tmp_path)
    rows[0]["file"]="../outside.jpg"
    path.write_text(json.dumps({"images":rows}))
    with pytest.raises(ValueError,match="inside"):
        evaluate_visual.load_dataset(path)
    path,rows=dataset(tmp_path)
    (tmp_path/"1.jpg").write_bytes((tmp_path/"0.jpg").read_bytes())
    with pytest.raises(ValueError,match="Repeated"):
        evaluate_visual.load_dataset(path)


def test_vlm_crop_validation_transparency_and_exif():
    output=BytesIO()
    exif=Image.Exif();exif[0x010E]="private fixture note";exif[274]=6
    Image.new("RGB",(1800,1200),"brown").save(output,format="JPEG",exif=exif)
    prepared=prepare_vlm_image(output.getvalue(),"image/jpeg")
    with Image.open(BytesIO(prepared.data)) as image:
        assert image.size==(683,1024) and not image.getexif()
    transparent=BytesIO();Image.new("RGBA",(256,256),(0,0,0,0)).save(transparent,format="PNG")
    prepared=prepare_vlm_image(transparent.getvalue(),"image/png",crop_bbox=(-10,0,200,200),crop_confidence=.99)
    assert prepared.metadata["image_input"]=="original"
    with Image.open(BytesIO(prepared.data)) as image:
        assert image.getpixel((100,100))==(255,255,255)
    with pytest.raises(ValueError):
        prepare_vlm_image(jpeg(),"image/png")


def test_api_import_does_not_load_inference_runtimes():
    import subprocess,sys
    subprocess.run([sys.executable,"-c","import sys;from app.main import app;assert not {'torch','open_clip','onnxruntime'} & set(sys.modules)"],check=True)
