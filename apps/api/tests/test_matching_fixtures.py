from pathlib import Path
from app.matching.evaluate import evaluate


def test_synthetic_ranking_regressions():
    options=[Path("test-data/matching/fixtures.json")]+[parent/"test-data"/"matching"/"fixtures.json" for parent in Path(__file__).resolve().parents]
    path=next(path for path in options if path.is_file())
    result=evaluate(path)
    assert result["synthetic"] is True and result["scenarios"]==12
    assert result["precision_at_1"]==1
    assert result["recall_at_5"]==1
    assert result["false_positive_rate"]==0
