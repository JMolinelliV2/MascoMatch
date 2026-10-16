"""Immutable vector spaces. Importing this module never imports inference runtimes."""
from dataclasses import asdict, dataclass
import hashlib
import json
from app.core.config import settings

PET_REVISION = "fa30eb7785ceb764d5c2840c4585fb89821be385"
CLIP_REVISION = "a6f597a30f7b82c51704746581f9a4e41421e878"
DETECTOR_REVISION = "1618db5f22919339f4347d436da8c43afaf91926"


@dataclass(frozen=True)
class EmbeddingSpec:
    provider: str
    model: str
    revision: str
    dimension: int
    preprocessing_version: str

    @property
    def space_id(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        return cls(**value)


def crop_version():
    return f"rf-nano-{DETECTOR_REVISION[:12]}:{int(settings.pet_crop_enabled)}:{settings.pet_crop_confidence:g}:{settings.pet_crop_margin:g}"


def openclip_spec():
    return EmbeddingSpec("open_clip", "ViT-B-32:openai", CLIP_REVISION, 512, "clip-rgb-exif-center224-v2")


def pet_reid_spec():
    return EmbeddingSpec("pet_reid", "open-noodle/pet-recognition-base", PET_REVISION, 512,
                         "pet-rgb-exif-imagenet224-v1:" + crop_version())


def select_spec(species):
    if settings.pet_reid_enabled and species in {"dog", "cat"}:
        return pet_reid_spec()
    return openclip_spec() if settings.openclip_enabled else None


def photo_species(db, photo):
    from app.models import Pet, LostCase, Observation
    if photo.owner_type == "pet":
        owner = db.get(Pet, photo.owner_id)
    elif photo.owner_type == "lost_case":
        case = db.get(LostCase, photo.owner_id)
        owner = case.pet if case else None
    elif photo.owner_type == "observation":
        owner = db.get(Observation, photo.owner_id)
    else:
        owner = None
    return owner.species if owner else None


def spec_for_photo(db, photo):
    species = photo_species(db, photo)
    return select_spec(species) if species is not None else None


def compatible(left, right):
    return left is not None and right is not None and left == right
