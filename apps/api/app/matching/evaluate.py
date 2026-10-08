"""Model-independent synthetic ranking regressions; no real-world precision claim."""
import json
from pathlib import Path
from app.core.config import settings
from app.matching.scoring import feature_similarity,combine


def evaluate(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    positive=correct_top=recall_hits=false_positive=negative=precision_five=0
    for observation in data["observations"]:
        ranked=[]
        distance=observation.get("distance_meters",100)
        hours=observation.get("hours_after_loss",1)
        for candidate in data["candidates"]:
            feature,coverage,_,contradiction=feature_similarity(candidate["features"],observation["features"])
            visual=observation.get("visual",{}).get(candidate["id"])
            if contradiction or distance>15000 or hours<0 or coverage<(.25 if visual is not None else .35) or feature<.5:continue
            score=combine(feature,visual,distance,15000,hours/24)[0]
            if score>=settings.matching_candidate_threshold:ranked.append((score,candidate["id"]))
        ranked.sort(reverse=True)
        expected=set(observation["expected"])
        if expected:
            positive+=1
            correct_top+=bool(ranked and ranked[0][1] in expected)
            hits=len(expected & {item[1] for item in ranked[:5]})
            recall_hits+=hits/len(expected)
            precision_five+=hits/5
        else:
            negative+=1;false_positive+=bool(ranked)
    return {"synthetic":True,"scenarios":len(data["observations"]),"positive_queries":positive,"negative_queries":negative,"precision_at_1":correct_top/positive if positive else None,"precision_at_5":precision_five/positive if positive else None,"recall_at_5":recall_hits/positive if positive else None,"false_positive_rate":false_positive/negative if negative else None}


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("path")
    print(json.dumps(evaluate(parser.parse_args().path),indent=2))
