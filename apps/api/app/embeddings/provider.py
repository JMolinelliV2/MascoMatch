from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
import math
from app.analysis.providers import ProviderError
from app.core.config import settings
from app.embeddings.specs import EmbeddingSpec, openclip_spec, pet_reid_spec
from app.embeddings.model_manifest import model_path, verify_artifact
from app.embeddings.cropper import decode_image, imagenet_tensor, onnx_session, run_onnx, PetCropper, image_quality

DIMENSION = 512
VERSION = "clip-rgb-exif-center224-v2"


def model_id():
    return openclip_spec().model


def normalize(vector):
    if len(vector) != DIMENSION or any(not math.isfinite(float(x)) for x in vector):
        raise ProviderError("INVALID_EMBEDDING", retryable=False)
    norm = math.sqrt(sum(float(x)**2 for x in vector))
    if norm < 1e-12:
        raise ProviderError("INVALID_EMBEDDING", retryable=False)
    return [float(x)/norm for x in vector]


@dataclass
class EmbeddingResult:
    vector: list[float]
    spec: EmbeddingSpec
    metadata: dict


class ImageEmbeddingProvider(ABC):
    @abstractmethod
    def encode(self, image: bytes) -> list[float]: ...


def checkpoint_path():
    return model_path("open_clip")


@lru_cache(maxsize=1)
def load_model():
    if not verify_artifact("open_clip"):
        raise ProviderError("EMBEDDING_MODEL_NOT_INSTALLED", retryable=False)
    try:
        import torch
        import open_clip
    except ImportError as exc:
        raise ProviderError("EMBEDDING_DEPENDENCIES_MISSING", retryable=False) from exc
    torch.set_num_threads(settings.embedding_cpu_threads)
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained=str(checkpoint_path()),
                                                                device="cpu", force_quick_gelu=True)
    model.eval()
    return model,preprocess


class OpenClipProvider(ImageEmbeddingProvider):
    spec = property(lambda self: openclip_spec())

    def encode(self,image):
        model,preprocess = load_model()
        import torch
        tensor = preprocess(decode_image(image)).unsqueeze(0)
        with torch.inference_mode():
            return normalize(model.encode_image(tensor).float()[0].tolist())

    def encode_result(self,image,species="unknown"):
        quality=image_quality(decode_image(image),{"crop_used":False,"image_input":"original"})
        return EmbeddingResult(self.encode(image),self.spec,quality)


class PetReIDProvider(ImageEmbeddingProvider):
    spec = property(lambda self: pet_reid_spec())

    def encode(self,image):
        session=onnx_session("pet_reid",settings.embedding_cpu_threads)
        output=run_onnx(session,imagenet_tensor(decode_image(image),224),settings.embedding_request_timeout_seconds)[0]
        return normalize(output[0].tolist())

    def encode_result(self,image,species="unknown"):
        cropped,metadata=PetCropper().prepare(image,species)
        return EmbeddingResult(self.encode(cropped),self.spec,metadata)


def get_embedding_provider(spec=None):
    spec = spec or openclip_spec()
    if spec == openclip_spec():
        return OpenClipProvider()
    if spec == pet_reid_spec():
        return PetReIDProvider()
    raise ProviderError("EMBEDDING_SPEC_UNSUPPORTED",retryable=False)
