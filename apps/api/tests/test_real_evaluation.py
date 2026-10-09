import json
import pytest
from app.matching.real_evaluate import evaluate


def dataset(tmp_path,photos):
    path=tmp_path/"labels.json"
    path.write_text(json.dumps({"schema":1,"dataset_source":"synthetic","candidates":[{"id":"a","features":{"species":"dog","primary_color":"brown","size":"medium"},"photos":[photos[0]]}],"queries":[{"id":"q","split":"holdout","expected_ids":["a"],"features":{"species":"dog","primary_color":"brown","size":"medium"},"photos":[photos[1]]}]}))
    return path


def test_evaluator_detects_photo_leakage(tmp_path,monkeypatch):
    (tmp_path/"a.jpg").write_bytes(b"same-example")
    (tmp_path/"b.jpg").write_bytes(b"same-example")
    class Encoder:
        def encode(self,payload):return [1.0]+[0.0]*511
    monkeypatch.setattr("app.matching.real_evaluate.get_embedding_provider",lambda:Encoder())
    with pytest.raises(ValueError,match="overlap"):
        evaluate(dataset(tmp_path,["a.jpg","b.jpg"]))


def test_evaluator_keeps_source_and_context_limits_visible(tmp_path,monkeypatch):
    (tmp_path/"a.jpg").write_bytes(b"reference-example")
    (tmp_path/"b.jpg").write_bytes(b"query-example")
    class Encoder:
        def encode(self,payload):return [1.0]+[0.0]*511
    monkeypatch.setattr("app.matching.real_evaluate.get_embedding_provider",lambda:Encoder())
    result=evaluate(dataset(tmp_path,["a.jpg","b.jpg"]))
    assert result["dataset_source"]=="synthetic"
    assert result["default_context_used"] and result["features_source"]=="provided"
    assert result["splits"]["holdout"]["positive_queries"]==1
