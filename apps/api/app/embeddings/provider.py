from abc import ABC, abstractmethod
from functools import lru_cache
from io import BytesIO
import math
from pathlib import Path

from PIL import Image
from app.analysis.providers import ProviderError
from app.core.config import settings

DIMENSION = 512
VERSION = "clip-image-preprocess-v1"


def model_id():
    return f"{settings.embedding_model}:{settings.embedding_pretrained}"


def normalize(vector):
    if len(vector) != DIMENSION or any(not math.isfinite(float(value)) for value in vector):
        raise ProviderError("INVALID_EMBEDDING", retryable=False)
    norm = math.sqrt(sum(float(value) ** 2 for value in vector))
    if norm < 1e-12:
        raise ProviderError("INVALID_EMBEDDING", retryable=False)
    return [float(value) / norm for value in vector]


class ImageEmbeddingProvider(ABC):
    @abstractmethod
    def encode(self, image: bytes) -> list[float]:
        """Return a finite normalized image vector without sending the image remotely."""


def checkpoint_path():
    return Path(settings.embedding_cache_dir) / "clip-vit-b-32-openai-state.pt"


@lru_cache(maxsize=1)
def load_model():
    try:
        import torch
        import open_clip
    except ImportError as exc:
        raise ProviderError("EMBEDDING_DEPENDENCIES_MISSING", retryable=False) from exc
    path = checkpoint_path()
    if not path.is_file():
        raise ProviderError("EMBEDDING_MODEL_NOT_INSTALLED", retryable=False)
    torch.set_num_threads(settings.embedding_cpu_threads)
    model, _, preprocess = open_clip.create_model_and_transforms(settings.embedding_model, pretrained=str(path), device="cpu", force_quick_gelu=True)
    model.eval()
    return model, preprocess


class OpenClipProvider(ImageEmbeddingProvider):
    def encode(self, image):
        model, preprocess = load_model()
        import torch
        with Image.open(BytesIO(image)) as source:
            tensor = preprocess(source.convert("RGB")).unsqueeze(0)
        with torch.inference_mode():
            vector = model.encode_image(tensor).float()[0].tolist()
        return normalize(vector)


def get_embedding_provider():
    return OpenClipProvider()
