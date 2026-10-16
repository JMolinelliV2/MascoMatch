"""Bounded, metadata-free visual-language-model inputs, independent of embeddings."""
from dataclasses import dataclass
from io import BytesIO
import math
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

VLM_PREPROCESSING_VERSION = "vlm_rgb_exif_lanczos_v2"
SUPPORTED_FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
MAX_PIXELS = 24_000_000


@dataclass(frozen=True)
class PreparedImage:
    data: bytes
    mime_type: str
    metadata: dict


def preprocessing_id() -> str:
    return f"{VLM_PREPROCESSING_VERSION}:{settings.vlm_image_max_side}:{settings.vlm_image_jpeg_quality}"


def prepare_vlm_image(payload: bytes, mime_type: str, *, max_side: int | None = None,
                      jpeg_quality: int | None = None, crop_bbox: tuple | None = None,
                      crop_confidence: float | None = None, crop_margin: float = .15,
                      minimum_crop_confidence: float = .75) -> PreparedImage:
    """Crop coordinates refer to the EXIF-oriented original; weak/invalid crops fall back.

    The optional detector supplies coordinates, never a user-controlled file or URL.
    A margin retains ears/tail/accessories and full-frame fallback preserves evidence.
    """
    max_side = max_side if max_side is not None else settings.vlm_image_max_side
    jpeg_quality = jpeg_quality if jpeg_quality is not None else settings.vlm_image_jpeg_quality
    if not 224 <= max_side <= 4096 or not 70 <= jpeg_quality <= 95:
        raise ValueError("Invalid VLM image configuration")
    expected = SUPPORTED_FORMATS.get(mime_type)
    if expected is None or not payload or len(payload) > settings.max_photo_size_bytes:
        raise ValueError("Invalid VLM image input")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(payload)) as original:
                if original.format != expected or original.width * original.height > MAX_PIXELS:
                    raise ValueError("Invalid VLM image format or dimensions")
                oriented = ImageOps.exif_transpose(original)
                oriented.load()
                source_size = oriented.size
                selected = oriented
                input_kind = "original"
                if crop_bbox and crop_confidence is not None and math.isfinite(crop_confidence) and crop_confidence >= minimum_crop_confidence:
                    if len(crop_bbox) == 4 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in crop_bbox):
                        x1, y1, x2, y2 = crop_bbox
                        if 0 <= x1 < x2 <= oriented.width and 0 <= y1 < y2 <= oriented.height and 0 <= crop_margin <= .5:
                            dx, dy = (x2 - x1) * crop_margin, (y2 - y1) * crop_margin
                            box = (max(0, math.floor(x1-dx)), max(0, math.floor(y1-dy)),
                                   min(oriented.width, math.ceil(x2+dx)), min(oriented.height, math.ceil(y2+dy)))
                            if box[2]-box[0] >= 64 and box[3]-box[1] >= 64:
                                selected = oriented.crop(box)
                                input_kind = "animal_crop"
                selected.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                rgba = selected.convert("RGBA")
                clean = Image.new("RGB", rgba.size, "white")
                clean.paste(rgba, mask=rgba.getchannel("A"))
                output = BytesIO()
                clean.save(output, format="JPEG", quality=jpeg_quality, optimize=True, exif=b"")
                data = output.getvalue()
                return PreparedImage(data, "image/jpeg", {
                    "preprocessing_version": VLM_PREPROCESSING_VERSION,
                    "image_input": input_kind, "input_bytes": len(payload), "output_bytes": len(data),
                    "original_width": source_size[0], "original_height": source_size[1],
                    "width": clean.width, "height": clean.height,
                    "max_side": max_side, "jpeg_quality": jpeg_quality,
                })
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("Invalid VLM image input") from exc


# Public alias retained for callers that use the preprocessing terminology.
preprocess_vlm_image = prepare_vlm_image
