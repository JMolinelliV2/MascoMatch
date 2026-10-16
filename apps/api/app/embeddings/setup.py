"""Explicit, checksum-verified model installation. Never run from request handlers."""
import argparse
import hashlib
from io import BytesIO
import json
import os
import urllib.request
from PIL import Image
from app.embeddings.model_manifest import ARTIFACTS, model_path, required_models, verify_artifact


def install(kind):
    artifact,path=ARTIFACTS[kind],model_path(kind)
    path.parent.mkdir(parents=True,exist_ok=True)
    if verify_artifact(kind):
        return path
    temporary=path.with_suffix(path.suffix+".download")
    url=f"https://huggingface.co/{artifact['repo']}/resolve/{artifact['revision']}/{artifact['file']}"
    digest=hashlib.sha256()
    try:
        with urllib.request.urlopen(url,timeout=120) as response, temporary.open("wb") as output:
            count=0
            while chunk:=response.read(1024*1024):
                count+=len(chunk)
                if count>artifact["bytes"]:
                    raise ValueError("Model exceeds pinned size")
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if count!=artifact["bytes"] or digest.hexdigest()!=artifact["sha256"]:
            raise ValueError("Model checksum or size mismatch")
        temporary.replace(path)
        path.chmod(0o444)
        return path
    finally:
        temporary.unlink(missing_ok=True)


def check_load(kind):
    if not verify_artifact(kind):
        raise ValueError("Required model missing or checksum mismatch: "+kind)
    from app.embeddings.provider import get_embedding_provider
    from app.embeddings.specs import openclip_spec,pet_reid_spec
    from app.embeddings.cropper import PetCropper
    output=BytesIO()
    Image.new("RGB",(256,256),"gray").save(output,format="PNG")
    if kind=="detector":
        PetCropper().detect(Image.new("RGB",(256,256),"gray"),"dog")
    else:
        vector=get_embedding_provider(pet_reid_spec() if kind=="pet_reid" else openclip_spec()).encode(output.getvalue())
        if len(vector)!=512:
            raise ValueError("Unexpected embedding dimension")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="Verify local files and inference without downloads")
    args=parser.parse_args()
    for kind in required_models():
        if not args.check:
            install(kind)
        check_load(kind)
        print(json.dumps({"model":kind,**ARTIFACTS[kind],"path":str(model_path(kind)),"load":"ok"}))


if __name__=="__main__":
    main()