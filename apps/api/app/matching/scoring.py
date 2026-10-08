import math
import re
import unicodedata
from app.core.config import settings

WEIGHTS = {"species": .15, "primary_color": .18, "secondary_colors": .08, "size": .10,
    "coat_length": .07, "coat_pattern": .10, "distinctive_features": .25, "accessories": .05, "breed_type": .02}
LABELS = {"species": "Misma especie", "primary_color": "Color principal compatible", "secondary_colors": "Colores secundarios compatibles",
    "size": "Tamaño compatible", "coat_length": "Pelaje compatible", "coat_pattern": "Patrón del pelaje compatible",
    "distinctive_features": "Rasgos distintivos similares", "accessories": "Accesorios similares", "breed_type": "Tipo o raza compatible"}
UNKNOWN = {"", "unknown", "not_visible", "uncertain"}


def normalized(value):
    text = unicodedata.normalize("NFKD", str(value).casefold())
    return re.sub(r"[^a-z0-9]+", " ", "".join(char for char in text if not unicodedata.combining(char))).strip()


def known(value):
    return value is not None and bool(value) and (not isinstance(value, str) or value.casefold() not in UNKNOWN)


def feature_similarity(expected, observed):
    if expected.get("species") and observed.get("species") and expected["species"] != observed["species"]:
        return 0, 0, [], True
    if expected.get("sex") and observed.get("sex") and expected["sex"] != observed["sex"]:
        return 0, 0, [], True
    coverage = matched = 0
    reasons = []
    for name, weight in WEIGHTS.items():
        left, right = expected.get(name), observed.get(name)
        if not known(left) or not known(right):
            continue
        coverage += weight
        if isinstance(left, list) or isinstance(right, list):
            left = {normalized(item) for item in (left if isinstance(left, list) else [left]) if known(item)}
            right = {normalized(item) for item in (right if isinstance(right, list) else [right]) if known(item)}
            # Missing a detail in an incomplete description is not evidence against that detail.
            similarity = len(left & right) / min(len(left), len(right)) if left and right else 0
        else:
            similarity = float(normalized(left) == normalized(right))
        matched += weight * similarity
        if similarity > 0:
            reasons.append(LABELS[name])
    return matched / coverage if coverage else 0, coverage, reasons, False


def cosine(left, right):
    numerator = sum(float(a) * float(b) for a, b in zip(left, right, strict=True))
    norm = math.sqrt(sum(float(a) ** 2 for a in left) * sum(float(b) ** 2 for b in right))
    return max(-1, min(1, numerator / norm)) if norm else 0


def combine(feature, raw_visual, distance, radius, days, accuracy=0):
    geo = math.exp(-2 * max(0, distance - accuracy) / max(1, radius))
    temporal = max(.2, math.exp(-max(0, days) / settings.matching_temporal_days))
    visual = None if raw_visual is None else max(0, min(1, (raw_visual - settings.matching_visual_floor) / (settings.matching_visual_ceiling - settings.matching_visual_floor)))
    score = .50 * feature + .30 * geo + .20 * temporal if visual is None else .45 * visual + .25 * feature + .20 * geo + .10 * temporal
    return score, visual, geo, temporal
