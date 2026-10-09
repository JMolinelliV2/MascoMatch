"""Private, locally encoded labeled-photo evaluation. No invented accuracy figures."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from app.embeddings.provider import get_embedding_provider, model_id
from app.matching.scoring import cosine, feature_similarity, combine
from app.core.config import settings


def evaluate(path):
    path=Path(path).resolve()
    root=path.parent
    dataset=json.loads(path.read_text())
    if dataset.get("schema")!=1 or not dataset.get("candidates") or not dataset.get("queries"):
        raise ValueError("A schema-1 labeled dataset is required")
    provider=get_embedding_provider()
    cache={}
    reference_hashes=set()
    query_hashes={}
    def vectors(record, split=None):
        result=[]
        for relative in record.get("photos",[]):
            photo=(root/relative).resolve()
            if not photo.is_relative_to(root) or not photo.is_file():
                raise ValueError("Photo paths must remain within the private dataset folder")
            if photo.stat().st_size>10*1024*1024:
                raise ValueError("Photo exceeds 10 MB")
            payload=photo.read_bytes()
            digest=sha256(payload).hexdigest()
            if split:
                if digest in reference_hashes or (digest in query_hashes and query_hashes[digest]!=split):
                    raise ValueError("Reference, calibration and holdout photos must not overlap")
                query_hashes[digest]=split
            else:
                if digest in reference_hashes:
                    raise ValueError("Duplicate reference photos")
                reference_hashes.add(digest)
            if digest not in cache:
                cache[digest]=provider.encode(payload)
            result.append(cache[digest])
        return result
    candidates=dataset["candidates"]
    if len({item["id"] for item in candidates})!=len(candidates):
        raise ValueError("Candidate identifiers must be unique")
    known_ids={item["id"] for item in candidates}
    for candidate in candidates:
        candidate["vectors"]=vectors(candidate)
    outcomes=[]
    default_context_used=False
    for query in dataset["queries"]:
        expected=set(query["expected_ids"])
        if not expected<=known_ids:
            raise ValueError("Every ground-truth candidate must exist")
        if query.get("split") not in {"calibration","holdout"}:
            raise ValueError("Queries must declare calibration or holdout")
        observed=vectors(query, query["split"])
        ranked=[]
        for candidate in candidates:
            feature,coverage,_,contradiction=feature_similarity(candidate["features"],query["features"])
            visual=max((cosine(a,b) for a in observed for b in candidate["vectors"]),default=None)
            evidence=query.get("context",{}).get(candidate["id"],{})
            default_context_used |= "distance_meters" not in evidence or "days_after_loss" not in evidence
            distance=evidence.get("distance_meters",100)
            days=evidence.get("days_after_loss",1)
            radius=candidate.get("radius_meters",15000)
            if contradiction or distance>radius or days<0 or coverage<(.25 if visual is not None else .35) or feature<.5:
                continue
            score=combine(feature,visual,distance,radius,days)[0]
            if score>=settings.matching_candidate_threshold:
                ranked.append((score,candidate["id"]))
        ranked.sort(reverse=True)
        outcomes.append((query["split"],expected,ranked))
    result={"dataset_source":dataset.get("dataset_source","unverified"),"model":model_id(),"features_source":"provided", "photos_encoded":len(cache),
            "default_context_used":default_context_used,
            "candidate_threshold":settings.matching_candidate_threshold,"notify_threshold":settings.matching_notify_threshold,"splits":{}}
    for split in ("calibration","holdout"):
        rows=[row for row in outcomes if row[0]==split]
        positive=[row for row in rows if row[1]]
        negative=[row for row in rows if not row[1]]
        alerts=[(expected,identity) for _,expected,ranked in rows for score,identity in ranked if score>=settings.matching_notify_threshold]
        result["splits"][split]={"queries":len(rows),"positive_queries":len(positive),"negative_queries":len(negative),
          "precision_at_1":sum(bool(ranked and ranked[0][1] in expected) for _,expected,ranked in positive)/len(positive) if positive else None,
          "recall_at_5":sum(len(expected & {identity for _,identity in ranked[:5]})/len(expected) for _,expected,ranked in positive)/len(positive) if positive else None,
          "false_positive_query_rate":sum(bool(ranked) for _,_,ranked in negative)/len(negative) if negative else None,
          "alert_precision":sum(identity in expected for expected,identity in alerts)/len(alerts) if alerts else None,"alerts":len(alerts)}
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=evaluate(args.dataset)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Aggregate evaluation saved. Keep holdout photos separate from threshold calibration.")
