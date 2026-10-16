"""Audited download allowlist. No user inputs become model URLs or filenames."""
import hashlib
from pathlib import Path
from app.core.config import settings
from app.embeddings.specs import PET_REVISION, CLIP_REVISION, DETECTOR_REVISION

ARTIFACTS = {
    "pet_reid": {"repo": "open-noodle/pet-recognition-base", "revision": PET_REVISION,
                 "file": "recognition/model.onnx", "local": "pet-recognition.onnx", "bytes": 348108213,
                 "sha256": "8691f5f6d0cebbd1602d21def63a34f7a58f78e08b3d4914cb81adcc2efd83f8"},
    "detector": {"repo": "open-noodle/rfdetr-nano", "revision": DETECTOR_REVISION,
                 "file": "detection/model.onnx", "local": "rfdetr-nano.onnx", "bytes": 107835234,
                 "sha256": "21045851f3906c7d424874363fe933477fda7210bad0d7a69659fb98f8845890"},
    "open_clip": {"repo": "timm/vit_base_patch32_clip_224.openai", "revision": CLIP_REVISION,
                  "file": "open_clip_model.safetensors", "local": "open_clip_model.safetensors", "bytes": 605143284,
                  "sha256": "e6d1bd7789aa45192b3bf90570a789b478bae1b74ebcce7eddd908e83a2b7c31"},
}


def model_path(kind):
    roots = {"pet_reid": settings.pet_reid_cache_dir, "detector": settings.detector_cache_dir,
             "open_clip": settings.embedding_cache_dir}
    return Path(roots[kind]) / ARTIFACTS[kind]["local"]


def verify_artifact(kind, *, checksum=True):
    path, artifact = model_path(kind), ARTIFACTS[kind]
    if not path.is_file() or path.stat().st_size != artifact["bytes"]:
        return False
    if checksum:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest() == artifact["sha256"]
    return True


def required_models():
    kinds = []
    if settings.openclip_enabled:
        kinds.append("open_clip")
    if settings.pet_reid_enabled:
        kinds.append("pet_reid")
    if settings.pet_crop_enabled:
        kinds.append("detector")
    return kinds
