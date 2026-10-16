"""Private readiness without inference or heavyweight imports."""
import argparse
import json
import urllib.request
from redis import Redis
from app.core.config import settings
from app.embeddings.model_manifest import required_models,verify_artifact


def ai_readiness():
    checks={}
    if settings.embeddings_enabled or settings.ai_enabled:
        kinds=required_models() if settings.embeddings_enabled else (["detector"] if settings.pet_crop_enabled else [])
        for kind in kinds:
            checks["model_"+kind]=verify_artifact(kind,checksum=False)
    try:
        with Redis.from_url(settings.redis_url,socket_connect_timeout=2,socket_timeout=2) as redis:
            if settings.embeddings_enabled:
                checks["worker_visual"]=bool(redis.get("mascomatch:worker:visual"))
            if settings.ai_enabled:
                checks["worker_semantic"]=bool(redis.get("mascomatch:worker:semantic"))
    except Exception:
        checks["worker_connection"]=False
    if settings.ai_enabled:
        checks["ollama"]=checks["gemma"]=False
        try:
            with urllib.request.urlopen(settings.ollama_base_url+"/api/tags",timeout=3) as response:
                models=json.load(response).get("models",[])
            names={item["name"] for item in models}
            checks["ollama"]=True
            from app.analysis.gemma_setup import GEMMA_DIGEST
            checks["gemma"]={settings.ai_text_model,settings.ai_vision_model}<=names
            checks["gemma_revision"]=any(item.get("name")=="gemma3:4b" and item.get("digest")==GEMMA_DIGEST for item in models)
        except Exception:
            pass
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",choices=["visual","semantic"])
    args=parser.parse_args()
    if args.worker:
        with Redis.from_url(settings.redis_url,socket_connect_timeout=2,socket_timeout=2) as redis:
            ready=bool(redis.get("mascomatch:worker:"+args.worker))
        print(json.dumps({"ready":ready}))
    else:
        checks=ai_readiness()
        ready=all(checks.values())
        print(json.dumps({"ready":ready,"checks":checks}))
    raise SystemExit(0 if ready else 1)


if __name__=="__main__":
    main()
