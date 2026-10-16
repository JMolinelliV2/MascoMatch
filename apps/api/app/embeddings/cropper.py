"""Local dog/cat detection, conservative crop and non-rejecting quality estimates."""
from functools import lru_cache
from io import BytesIO
import math
import threading
from PIL import Image, ImageOps
from app.core.config import settings
from app.analysis.providers import ProviderError
from app.embeddings.model_manifest import model_path, verify_artifact


def decode_image(payload):
    if not payload or len(payload) > settings.max_photo_size_bytes:
        raise ProviderError("INVALID_IMAGE", retryable=False)
    try:
        with Image.open(BytesIO(payload)) as source:
            if source.width * source.height > 24_000_000 or source.format not in {"JPEG","PNG","WEBP"}:
                raise ValueError()
            image = ImageOps.exif_transpose(source)
            image.load()
            rgba = image.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, "white")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
            return rgb
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        raise ProviderError("INVALID_IMAGE", retryable=False) from exc


@lru_cache(maxsize=3)
def onnx_session(kind, threads):
    if not verify_artifact(kind):
        raise ProviderError("EMBEDDING_MODEL_NOT_INSTALLED", retryable=False)
    try:
        import onnxruntime as ort
        ort.disable_telemetry_events()
    except ImportError as exc:
        raise ProviderError("EMBEDDING_DEPENDENCIES_MISSING", retryable=False) from exc
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    return ort.InferenceSession(str(model_path(kind)), sess_options=options, providers=["CPUExecutionProvider"])


def imagenet_tensor(image, size):
    import numpy as np
    pixels = np.asarray(image.resize((size,size), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    pixels = (pixels - np.array([.485,.456,.406],dtype=np.float32)) / np.array([.229,.224,.225],dtype=np.float32)
    return np.transpose(pixels, (2,0,1))[None].copy()


def run_onnx(session, tensor, timeout):
    import onnxruntime as ort
    options = ort.RunOptions()
    expired = threading.Event()
    def cancel():
        expired.set()
        options.terminate = True
    timer = threading.Timer(timeout, cancel)
    timer.daemon = True
    timer.start()
    try:
        return session.run(None, {session.get_inputs()[0].name: tensor}, options)
    except Exception as exc:
        raise ProviderError("EMBEDDING_TIMEOUT" if expired.is_set() else "EMBEDDING_INFERENCE_FAILED", retryable=expired.is_set()) from exc
    finally:
        timer.cancel()


def image_quality(image, metadata=None):
    """Heuristic evidence weight, not a quality classifier or rejection rule."""
    import numpy as np
    metadata = dict(metadata or {})
    gray = np.asarray(image.convert("L").resize((min(256,image.width),min(256,image.height))),dtype=np.float32)
    laplacian = -4*gray[1:-1,1:-1]+gray[:-2,1:-1]+gray[2:,1:-1]+gray[1:-1,:-2]+gray[1:-1,2:]
    blur = float(laplacian.var()) if laplacian.size else 0.0
    reliability = min(1.0,min(image.size)/224) * min(1.0,max(.35,blur/80))
    if not metadata.get("crop_used"):
        reliability *= .75
    if metadata.get("crop_reason") == "multiple_animals":
        reliability *= .4
    if metadata.get("animal_ratio",1) < .03:
        reliability *= .6
    return {**metadata,"width":image.width,"height":image.height,"blur_variance":round(blur,3),
            "visual_reliability":round(max(.1,min(1,reliability)),4)}


class PetCropper:
    def detect(self, image, species):
        import numpy as np
        session = onnx_session("detector", settings.embedding_cpu_threads)
        outputs = run_onnx(session, imagenet_tensor(image,384), settings.pet_crop_timeout_seconds)
        boxes = next((x for x in outputs if x.shape[-1] == 4), None)
        logits = next((x for x in outputs if x.shape[-1] == 91), None)
        if boxes is None or logits is None:
            raise ProviderError("DETECTOR_SCHEMA_INVALID", retryable=False)
        classes = {"cat":17,"dog":18}
        target = [classes[species]] if species in classes else [17,18]
        probabilities = 1 / (1 + np.exp(-np.clip(logits[0], -50, 50)))
        hits = []
        for index in range(len(boxes[0])):
            category = int(np.argmax(probabilities[index]))
            confidence = float(probabilities[index,category])
            if category not in target or confidence < settings.pet_crop_confidence:
                continue
            cx,cy,w,h = [float(x) for x in boxes[0,index]]
            if not all(math.isfinite(x) for x in (cx,cy,w,h)) or min(w,h) <= 0:
                continue
            box = (max(0,(cx-w/2)*image.width), max(0,(cy-h/2)*image.height),
                   min(image.width,(cx+w/2)*image.width), min(image.height,(cy+h/2)*image.height))
            if box[2]-box[0] >= 16 and box[3]-box[1] >= 16:
                hits.append((confidence,box))
        hits.sort(reverse=True)
        if not hits:
            return None, {"detected":False,"detection_confidence":0.0,"crop_reason":"not_detected"}
        # Multiple distinct animals make selecting an individual unsafe. Overlapping queries are duplicates.
        best, box = hits[0]
        for confidence, other in hits[1:]:
            overlap = max(0,min(box[2],other[2])-max(box[0],other[0])) * max(0,min(box[3],other[3])-max(box[1],other[1]))
            area = (box[2]-box[0])*(box[3]-box[1])
            other_area = (other[2]-other[0])*(other[3]-other[1])
            if overlap/max(1,min(area,other_area)) < .5:
                return None, {"detected":True,"detection_confidence":best,"crop_reason":"multiple_animals"}
        return box, {"detected":True,"detection_confidence":best,"crop_reason":"detected"}

    def prepare(self, payload, species):
        image = decode_image(payload)
        metadata = {"detected":False,"crop_used":False,"image_input":"original","detection_confidence":0.0}
        box = None
        if settings.pet_crop_enabled and species in {"dog","cat","unknown"}:
            try:
                box, details = self.detect(image, species)
                metadata.update(details)
            except ProviderError as exc:
                metadata["crop_reason"] = exc.code
            except Exception:
                metadata["crop_reason"] = "DETECTOR_UNAVAILABLE"
        selected = image
        if box:
            x1,y1,x2,y2 = box
            metadata["animal_ratio"] = (x2-x1)*(y2-y1)/(image.width*image.height)
            dx,dy = (x2-x1)*settings.pet_crop_margin,(y2-y1)*settings.pet_crop_margin
            bounds = (max(0,math.floor(x1-dx)),max(0,math.floor(y1-dy)),
                      min(image.width,math.ceil(x2+dx)),min(image.height,math.ceil(y2+dy)))
            selected = image.crop(bounds)
            metadata.update(crop_used=True,image_input="animal_crop",bbox=list(bounds))
        metadata = image_quality(selected, metadata)
        output=BytesIO()
        selected.save(output,format="JPEG",quality=95,exif=b"")
        return output.getvalue(),metadata
