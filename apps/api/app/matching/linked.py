import asyncio
import math
from datetime import timedelta, timezone
import logging
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.analysis.logging import log_event
from app.analysis.prompts import TEXT_PROMPT_VERSION, VISION_PROMPT_VERSION
from app.analysis.service import is_current, utcnow
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import AnalysisJob, FeatureSet, LostCase, Notification, Observation, Pet, Photo

UNKNOWN = {"unknown", "uncertain", "not_visible", ""}
WEIGHTS = {"species": .35, "primary_color": .3, "size": .1, "coat_length": .1, "coat_pattern": .1, "breed_type": .05}
LABELS = {"species": "Especie compatible", "primary_color": "Color compatible", "size": "Tamaño compatible", "coat_length": "Pelaje compatible", "coat_pattern": "Patrón del pelaje compatible", "breed_type": "Tipo o raza compatible"}


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def distance_meters(lat1, lon1, lat2, lon2):
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = lat2 - lat1, math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0, 1 - a)))


def current_jobs(db, owner_type, owner_id, source=None):
    query = select(AnalysisJob).where(AnalysisJob.owner_type == owner_type, AnalysisJob.owner_id == owner_id, AnalysisJob.provider == settings.ai_provider)
    if source:
        query = query.where(AnalysisJob.source_type == source)
    return [job for job in db.scalars(query)
            if job.model == (settings.ai_vision_model if job.source_type == "image" else settings.ai_text_model)
            and job.prompt_version == (VISION_PROMPT_VERSION if job.source_type == "image" else TEXT_PROMPT_VERSION)
            and is_current(db, job)]


def traits_from_result(result: FeatureSet | None):
    traits = {}
    if result:
        for name in WEIGHTS:
            attribute = result.features.get(name, {})
            value = attribute.get("value")
            if isinstance(value, str) and value.lower() not in UNKNOWN and attribute.get("confidence", 0) >= settings.linked_feature_confidence:
                traits[name] = value.strip().casefold()
    return traits


def target_traits(db, case, pet):
    # Explicit owner declarations outrank AI suggestions. The sighting itself never copies these traits.
    traits = {}
    for field, attribute in (("species", "species"), ("primary_color", "primary_color"), ("size", "size"), ("coat_length", "coat_type"), ("breed_type", "breed")):
        value = getattr(pet, attribute)
        if value and value.casefold() not in UNKNOWN:
            traits[field] = value.strip().casefold()
    jobs = current_jobs(db, "lost_case", case.id) + current_jobs(db, "pet", pet.id)
    for job in sorted(jobs, key=lambda item: aware(item.created_at), reverse=True):
        if job.status == "SUCCEEDED":
            result = db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id == job.id))
            for field, value in traits_from_result(result).items():
                traits.setdefault(field, value)
    return traits, jobs


def compare_traits(target: dict, observed: dict):
    available = sum(weight for name, weight in WEIGHTS.items() if name in target and name in observed)
    reasons = [LABELS[name] for name in WEIGHTS if name in target and target.get(name) == observed.get(name)]
    matched = sum(weight for name, weight in WEIGHTS.items() if name in target and target.get(name) == observed.get(name))
    contradiction = "species" in target and "species" in observed and target["species"] != observed["species"]
    # A clear black/white or single-color mismatch is evidence against the proposed identity.
    if target.get("primary_color") not in (None, "multicolor") and observed.get("primary_color") not in (None, "multicolor"):
        contradiction = contradiction or target["primary_color"] != observed["primary_color"]
    score = matched / available if available else 0
    compatible = not contradiction and matched + 1e-9 >= .5 and score >= settings.linked_match_threshold
    return compatible, score, reasons, contradiction


def set_result(db, observation, case, pet, status, reasons, score=None):
    observation.matching_status = status
    observation.matching_score = score
    observation.matching_reasons = reasons
    notification = db.scalar(select(Notification).where(Notification.observation_id == observation.id))
    notify = status in {"UNVERIFIED", "POSSIBLE_MATCH"} and observation.author_id != pet.owner_id
    if not notify:
        if notification:
            notification.is_active = False
        return status
    kind = "REPORTED_SIGHTING" if status == "UNVERIFIED" else "POSSIBLE_MATCH"
    title = f"Posible avistamiento de {pet.name}"[:180]
    if status == "UNVERIFIED":
        has_photo = db.scalar(select(Photo.id).where(Photo.owner_type == "observation", Photo.owner_id == observation.id).limit(1)) is not None
        body = "Una persona indicó que vio a tu animal cerca de la zona de búsqueda. " + ("Las fotos no aportaron suficientes rasgos para comparar; revisá el reporte. La identidad está por confirmar." if has_photo else "No adjuntó fotos; la identidad está por confirmar.")
    else:
        body = "Las características de la foto son compatibles con tu aviso, junto con la ubicación y la fecha. Podría tratarse de tu animal; revisá el avistamiento."
    if notification is None:
        notification = Notification(owner_id=pet.owner_id, lost_case_id=case.id, observation_id=observation.id, kind=kind, title=title, body=body)
        db.add(notification)
    else:
        notification.kind, notification.title, notification.body, notification.is_active = kind, title, body, True
    return status


def evaluate_sighting(db: Session, observation_id: UUID) -> str:
    observation = db.get(Observation, observation_id)
    if observation is None or observation.linked_case_id is None:
        return "NOT_REQUESTED"
    # All evaluators lock the case first, then its sighting, to serialize notification creation.
    case = db.scalar(select(LostCase).where(LostCase.id == observation.linked_case_id).with_for_update())
    observation = db.scalar(select(Observation).where(Observation.id == observation_id).with_for_update().execution_options(populate_existing=True))
    if case is None or observation is None:
        return "INACTIVE"
    pet = db.get(Pet, case.pet_id)
    if case.status != "ACTIVE":
        return set_result(db, observation, case, pet, "INACTIVE", ["El aviso ya no está activo"])
    if aware(observation.observed_at) < aware(case.lost_at) or aware(observation.observed_at) > utcnow() + timedelta(minutes=1):
        return set_result(db, observation, case, pet, "NOT_COMPATIBLE", ["La fecha no es compatible con el aviso"])
    coordinates = (case.latitude, case.longitude, observation.latitude, observation.longitude)
    if any(value is None or not math.isfinite(value) for value in coordinates):
        return set_result(db, observation, case, pet, "NEEDS_REVIEW", ["Falta una ubicación para comparar"])
    distance = distance_meters(*coordinates)
    allowance = min(case.location_accuracy_meters or 0, 1000) + min(observation.location_accuracy_meters or 0, 1000)
    if distance > case.search_radius_meters + allowance:
        return set_result(db, observation, case, pet, "NOT_COMPATIBLE", ["El avistamiento está fuera del radio de búsqueda"])
    geographic = ["Fecha compatible con el aviso", "Ubicación dentro de la zona de búsqueda"]
    photos = list(db.scalars(select(Photo).where(Photo.owner_type == "observation", Photo.owner_id == observation.id)))
    if not photos:
        return set_result(db, observation, case, pet, "UNVERIFIED", geographic + ["Avistamiento declarado por una persona, sin foto"])
    jobs = current_jobs(db, "observation", observation.id, "image")
    expected = target_traits(db, case, pet)
    target, target_jobs = expected
    pending = {"PENDING", "DISPATCHING", "QUEUED", "RUNNING"}
    if any(job.status in pending for job in jobs + target_jobs):
        return set_result(db, observation, case, pet, "PENDING", ["Analizando las fotos y las características del aviso"])
    observed_results = []
    for photo in photos:
        photo_jobs = [job for job in jobs if job.photo_id == photo.id and job.status == "SUCCEEDED"]
        photo_jobs.sort(key=lambda item: aware(item.created_at), reverse=True)
        result = db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id == photo_jobs[0].id)) if photo_jobs else None
        traits = traits_from_result(result)
        if traits:
            observed_results.append(traits)
    if not observed_results:
        return set_result(db, observation, case, pet, "UNVERIFIED", geographic + ["Las fotos necesitan revisión por una persona"])
    comparisons = [compare_traits(target, traits) for traits in observed_results]
    if any(item[3] for item in comparisons):
        return set_result(db, observation, case, pet, "NOT_COMPATIBLE", ["Las fotos muestran una especie o un color diferente al aviso"])
    positives = [item for item in comparisons if item[0]]
    if positives:
        _, score, reasons, _ = max(positives, key=lambda item: item[1])
        return set_result(db, observation, case, pet, "POSSIBLE_MATCH", geographic + reasons, score)
    return set_result(db, observation, case, pet, "UNVERIFIED", geographic + ["Las fotos no aportaron suficientes rasgos para una comparación automática"])


def related_ids(db, owner_type, owner_id):
    if owner_type == "observation":
        return [owner_id]
    cases = [owner_id] if owner_type == "lost_case" else list(db.scalars(select(LostCase.id).where(LostCase.pet_id == owner_id)))
    return list(db.scalars(select(Observation.id).where(Observation.linked_case_id.in_(cases)).order_by(Observation.linked_case_id, Observation.id)))


def mark_related_pending(db, owner_type, owner_id):
    identities = related_ids(db, owner_type, owner_id)
    if identities:
        db.execute(update(Observation).where(Observation.id.in_(identities), Observation.linked_case_id.is_not(None)).values(matching_status="PENDING"))
        db.execute(update(Notification).where(Notification.observation_id.in_(identities)).values(is_active=False))


def reconcile_related(owner_type, owner_id, session_factory=None):
    factory = session_factory or SessionLocal
    with factory() as db:
        identities = related_ids(db, owner_type, owner_id)
    for identity in identities:
        with factory() as db:
            evaluate_sighting(db, identity)
            db.commit()


def reconcile_pending(session_factory=None):
    factory = session_factory or SessionLocal
    with factory() as db:
        identities = list(db.scalars(select(Observation.id).where(Observation.linked_case_id.is_not(None), Observation.matching_status == "PENDING").order_by(Observation.created_at).limit(50)))
    for identity in identities:
        with factory() as db:
            evaluate_sighting(db, identity)
            db.commit()


async def reconciliation_loop():
    while True:
        try:
            await asyncio.to_thread(reconcile_pending)
        except Exception:
            log_event("linked_matching_unavailable", level=logging.WARNING)
        await asyncio.sleep(5)
