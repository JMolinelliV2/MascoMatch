"""Install the exact existing Gemma 3 4B artifact; never follow a mutable model tag."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request

GEMMA_DIGEST="a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a"
# Public OCI manifest read from the existing installation. Order is significant for its digest.
MANIFEST={"schemaVersion":2,"mediaType":"application/vnd.docker.distribution.manifest.v2+json",
    "config":{"mediaType":"application/vnd.docker.container.image.v1+json","digest":"sha256:b6ae5839783f2ba248e65e4b960ab15f9c4b7118db285827dba6cba9754759e2","size":489},
    "layers":[
        {"mediaType":"application/vnd.ollama.image.model","digest":"sha256:aeda25e63ebd698fab8638ffb778e68bed908b960d39d0becc650fa981609d25","size":3338792448},
        {"mediaType":"application/vnd.ollama.image.template","digest":"sha256:e0a42594d802e5d31cdc786deb4823edb8adff66094d49de8fffe976d753e348","size":358},
        {"mediaType":"application/vnd.ollama.image.license","digest":"sha256:dd084c7d92a3c1c14cc09ae77153b903fd2024b64a100a0cc8ec9316063d2dbc","size":8432},
        {"mediaType":"application/vnd.ollama.image.params","digest":"sha256:3116c52250752e00dd06b16382e952bd33c34fd79fc4fe3a5d2c77cf7de1b14b","size":77}]}


def manifest_bytes():
    payload=json.dumps(MANIFEST,separators=(",",":")).encode()
    if hashlib.sha256(payload).hexdigest()!=GEMMA_DIGEST:
        raise ValueError("Pinned Gemma manifest digest mismatch")
    return payload


def valid(path,item):
    if not path.is_file() or path.stat().st_size!=item["size"]:
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()==item["digest"].split(":")[1]


def install(root,*,check=False,accepted=False):
    payload=manifest_bytes()
    manifest=root/"models/manifests/registry.ollama.ai/library/gemma3/4b"
    if not check and not accepted:
        raise ValueError("Read https://ai.google.dev/gemma/terms and pass --accept-gemma-terms before installation")
    for item in [MANIFEST["config"],*MANIFEST["layers"]]:
        target=root/"models/blobs"/item["digest"].replace(":","-")
        if valid(target,item):
            continue
        if check:
            raise ValueError("Missing/corrupt Gemma blob: "+item["digest"])
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent,prefix=".gemma-",delete=False) as output:
                temporary=Path(output.name)
                request=urllib.request.Request("https://registry.ollama.ai/v2/library/gemma3/blobs/"+item["digest"],
                                               headers={"User-Agent":"MascoMatch-model-setup"})
                size=0
                with urllib.request.urlopen(request,timeout=120) as response:
                    while chunk:=response.read(1024*1024):
                        size+=len(chunk)
                        if size>item["size"]:
                            raise ValueError("Gemma blob exceeds pinned size")
                        output.write(chunk)
                output.flush();os.fsync(output.fileno())
            if not valid(temporary,item):
                raise ValueError("Gemma blob checksum mismatch")
            temporary.replace(target)
            target.chmod(0o444)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
    if check:
        if not manifest.is_file() or manifest.read_bytes()!=payload:
            raise ValueError("Installed Gemma revision does not match pinned manifest")
    else:
        manifest.parent.mkdir(parents=True,exist_ok=True)
        temporary=manifest.with_suffix(".installing")
        temporary.write_bytes(payload)
        temporary.replace(manifest)
        manifest.chmod(0o444)
    return {"model":"gemma3:4b","digest":GEMMA_DIGEST,"bytes":sum(i["size"] for i in [MANIFEST["config"],*MANIFEST["layers"]]),"verified":True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path("/ollama"))
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--accept-gemma-terms",action="store_true")
    args=parser.parse_args()
    print(json.dumps(install(args.root,check=args.check,accepted=args.accept_gemma_terms)))


if __name__=="__main__":
    main()
