"""Measure each installed visual component in a fresh CPU process, without a database."""
import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys
from time import monotonic,process_time


def current_rss():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def measure(kind,image):
    initial=current_rss()
    from app.embeddings.provider import PetReIDProvider,OpenClipProvider
    from app.embeddings.cropper import PetCropper
    payload=image.read_bytes()
    latencies=[];cpu=[]
    provider=PetReIDProvider() if kind=="pet_reid" else OpenClipProvider() if kind=="open_clip" else PetCropper()
    for _ in range(3):
        start=monotonic();cpu_start=process_time()
        if kind=="detector":
            provider.prepare(payload,"dog")
        else:
            provider.encode(payload)
        latencies.append(monotonic()-start);cpu.append(process_time()-cpu_start)
    return {"component":kind,"initial_rss_kib":initial,"loaded_rss_kib":current_rss(),
            "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "seconds_cold_then_warm":latencies,"cpu_seconds":cpu}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image",type=Path,required=True)
    parser.add_argument("--single",choices=["detector","pet_reid","open_clip"])
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.single:
        print(json.dumps(measure(args.single,args.image)))
        return
    report={"environment":"local CPU; component RSS includes Python/runtime/image decoding, not additive", "components":[]}
    for kind in ("detector","pet_reid","open_clip"):
        process=subprocess.run([sys.executable,"-m","app.embeddings.benchmark","--image",str(args.image),"--single",kind],capture_output=True,text=True,check=True)
        report["components"].append(json.loads(process.stdout))
    rendered=json.dumps(report,indent=2)
    if args.output:
        args.output.write_text(rendered,encoding="utf-8")
    print(rendered)


if __name__=="__main__":
    main()
