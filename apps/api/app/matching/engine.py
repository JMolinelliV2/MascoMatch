import asyncio
from datetime import timedelta
import math
from sqlalchemy import and_, or_, select, text, update
from app.analysis.service import is_current, utcnow
from app.analysis.logging import log_event
from app.analysis.prompts import TEXT_PROMPT_VERSION, VISION_PROMPT_VERSION
from app.core.config import settings
from app.db.session import SessionLocal
from app.embeddings.specs import EmbeddingSpec,compatible
from app.matching.linked import aware, distance_meters
from app.matching.scoring import WEIGHTS, known, normalized, feature_similarity, combine, cosine, aggregate_visual_similarity, notification_evidence
from app.matching.tracking import record_recommendation
from app.models import AnalysisJob, Embedding, FeatureSet, LostCase, Match, Notification, Observation, Pet, Photo, User
from app.species import SUPPORTED_SPECIES, is_supported_species, owner_is_supported
from app.report_details import COLOR_LABELS, color_value

PENDING = {"PENDING", "DISPATCHING", "QUEUED", "RUNNING"}


def declared_traits(item):
    """General matching only: feed the same declared fields on either side."""
    fields = {"species": "species", "sex": "sex", "primary_color": "primary_color",
              "secondary_colors": "secondary_colors", "size": "size", "breed_type": "breed",
              "coat_length": "coat_type", "distinctive_features": "distinctive_features"}
    traits = {}
    for name, field in fields.items():
        value = getattr(item, field, None)
        if isinstance(value, str):
            value = value.strip()
        elif isinstance(value, list):
            value = [v.strip() if isinstance(v, str) else v for v in value
                     if known(v.strip() if isinstance(v, str) else v)]
        if known(value):
            traits[name] = value
    return traits


ACCESSORY_NAMES = {
    "collar": {"collar"},
    "clothing": {"ropa", "prenda", "camiseta", "remera", "abrigo", "chaleco", "arnes",
                 "bandana", "panuelo", "campera", "clothing", "shirt", "coat", "jacket", "harness"},
}
ACCESSORY_COLOR_ALIASES = {
    "rojo": "red", "roja": "red", "colorado": "red", "colorada": "red", "cafe": "brown",
    "negra": "black", "blanca": "white", "grey": "gray", "azul": "blue", "verde": "green",
    "amarillo": "yellow", "amarilla": "yellow", "rosa": "pink", "rosado": "pink", "rosada": "pink",
    "morado": "purple", "morada": "purple", "violeta": "purple",
}
ACCESSORY_UNCERTAIN = {
    "sin", "no", "not", "without", "unknown", "uncertain", "incierto", "incierta",
    "desconocido", "desconocida", "quiza", "quizas", "posible", "posiblemente", "podria",
    "parece", "parecido", "maybe", "possibly", "ningun", "ninguna", "ausente", "dudoso", "dudosa",
}
ACCESSORY_DETAILS = {"de", "con", "color", "tela", "cuero", "nylon", "placa", "chapa",
                     "claro", "clara", "oscuro", "oscura", "light", "dark"}


def accessory_color(value):
    if not isinstance(value, str) or not known(value.strip()):
        return None
    value = normalized(color_value(value))
    return ACCESSORY_COLOR_ALIASES.get(value, value) or None


def accessory_facts(item, inferred):
    """Recognize bounded labels, then let each explicit subfield override inference."""
    facts, colors = {}, {}
    basic_colors = set(COLOR_LABELS) | {"blue", "green", "yellow", "pink", "purple"}
    for label in inferred if isinstance(inferred, list) else []:
        if not isinstance(label, str) or "?" in label:
            continue
        words = normalized(label).split()
        if words and words[0] in {"un", "una", "a", "an"}:
            words = words[1:]
        if not words or set(words) & ACCESSORY_UNCERTAIN:
            continue
        kinds = [kind for kind, names in ACCESSORY_NAMES.items() if set(words) & names]
        if len(kinds) != 1:
            continue  # One label naming multiple items cannot assign a color safely.
        kind = kinds[0]
        if words[0] not in ACCESSORY_NAMES[kind] and not (
                words[-1] in ACCESSORY_NAMES[kind] and accessory_color(" ".join(words[:-1])) in basic_colors):
            continue
        if any(word not in ACCESSORY_NAMES[kind] | ACCESSORY_DETAILS
               and accessory_color(word) not in basic_colors for word in words):
            continue  # Unrecognized prose must not turn an uncertain label into presence.
        facts[kind] = ("yes", None)
        colors.setdefault(kind, set()).update(c for word in words if (c := accessory_color(word)) in basic_colors)
    for kind, values in colors.items():
        facts[kind] = ("yes", next(iter(values)) if len(values) == 1 else None)
    for kind in ACCESSORY_NAMES:
        status = getattr(item, f"{kind}_status", None)
        if status == "no":
            facts[kind] = ("no", None)
        elif status == "yes" or kind in facts:
            inferred_color = facts.get(kind, (None, None))[1]
            facts[kind] = ("yes", accessory_color(getattr(item, f"{kind}_color", None)) or inferred_color)
    return facts


def comparable_traits(left_item, left, right_item, right):
    # Do not reinterpret legacy inferred labels when neither report adds structured accessories.
    if not any(getattr(item, f"{kind}_status", None) in {"yes", "no"}
               or accessory_color(getattr(item, f"{kind}_color", None)) is not None
               for item in (left_item, right_item) for kind in ACCESSORY_NAMES):
        return left, right
    parts = (accessory_facts(left_item, left.get("accessories")),
             accessory_facts(right_item, right.get("accessories")))
    tokens = ([], [])
    for kind in ACCESSORY_NAMES:
        a, b = parts[0].get(kind), parts[1].get(kind)
        if a is None or b is None or a[0] == b[0] == "no":
            continue  # Unknowns and shared absences supply no comparable evidence.
        for output, fact in zip(tokens, (a, b)):
            output.append(f"{kind} {fact[0]}")
        if a[0] == b[0] == "yes" and a[1] and b[1]:
            for output, fact in zip(tokens, (a, b)):
                output.append(f"{kind} color {fact[1]}")
    result = (dict(left), dict(right))
    for traits, values in zip(result, tokens):
        traits.pop("accessories", None)
        if values:
            traits["accessories"] = values
    return result


def should_wait(job):
    enabled=settings.embeddings_enabled if job.source_type=="embedding" else settings.ai_enabled
    return (enabled and job.status in PENDING and job.attempts==0 and
            (utcnow()-aware(job.created_at)).total_seconds()<settings.matching_analysis_wait_seconds)


def request_matching(db, owner_type, owner_id):
    supported = owner_is_supported(db, owner_type, owner_id)
    if owner_type == "observation":
        scope = Observation.id == owner_id
        affected = Match.observation_id == owner_id
    else:
        # Candidate retrieval will restrict each comparison by species, area and date.
        scope = True
        affected = Match.lost_case_id == owner_id if owner_type == "lost_case" else Match.lost_case_id.in_(select(LostCase.id).where(LostCase.pet_id == owner_id))
    if supported:
        db.execute(update(Observation).where(scope, Observation.species.in_(SUPPORTED_SPECIES), Observation.linked_case_id.is_(None)).values(matching_status="PENDING", matching_checked_at=None))
    general_affected = and_(affected, Match.observation_id.in_(select(Observation.id).where(Observation.linked_case_id.is_(None))))
    db.execute(update(Match).where(general_affected).values(is_active=False))
    db.execute(update(Notification).where(Notification.match_id.in_(select(Match.id).where(general_affected))).values(is_active=False))


def evidence(db, owner_type, owner_id, declared):
    traits = {key: value for key, value in declared.items() if known(value)}
    pending = False
    jobs = list(db.scalars(select(AnalysisJob).where(AnalysisJob.owner_type == owner_type, AnalysisJob.owner_id == owner_id).order_by(AnalysisJob.created_at.desc())))
    for job in jobs:
        if not is_current(db, job):
            continue
        if job.source_type == "embedding":
            pending = pending or should_wait(job)
            continue
        if job.provider != settings.ai_provider or job.model != (settings.ai_vision_model if job.source_type == "image" else settings.ai_text_model) or job.prompt_version != (VISION_PROMPT_VERSION if job.source_type == "image" else TEXT_PROMPT_VERSION):
            continue
        pending = pending or should_wait(job)
        if job.status != "SUCCEEDED":
            continue
        result = db.scalar(select(FeatureSet).where(FeatureSet.analysis_job_id == job.id))
        if result:
            for key in WEIGHTS:
                attribute = result.features.get(key, {})
                if known(attribute.get("value")) and attribute.get("confidence", 0) >= settings.linked_feature_confidence:
                    if key=="species" and (attribute["value"]=="unsupported" or (
                        job.source_type=="image" and known(traits.get("species")) and
                        traits["species"]!=attribute["value"] and attribute.get("confidence",0)>=.9)):
                        traits["_species_conflict"]=True
                    traits.setdefault(key, attribute["value"])
    return traits, pending


def candidates(db, observation):
    if not is_supported_species(observation.species):
        return
    query = select(LostCase, Pet).join(Pet).join(User,Pet.owner_id==User.id).where(LostCase.status == "ACTIVE",LostCase.moderation_status=="VISIBLE",User.status=="ACTIVE", LostCase.lost_at <= observation.observed_at,
        LostCase.latitude.is_not(None), LostCase.longitude.is_not(None))
    query = query.where(Pet.species.in_(SUPPORTED_SPECIES), Pet.species == observation.species)
    radius = settings.matching_max_radius_meters + 2000
    lat_delta = radius / 111000
    lon_delta = min(180, lat_delta / max(.01, math.cos(math.radians(observation.latitude))))
    query = query.where(LostCase.latitude.between(observation.latitude - lat_delta, observation.latitude + lat_delta))
    # Longitude wraps at the antimeridian. The precise distance test remains authoritative.
    if observation.longitude - lon_delta >= -180 and observation.longitude + lon_delta <= 180:
        query = query.where(LostCase.longitude.between(observation.longitude - lon_delta, observation.longitude + lon_delta))
    if db.bind.dialect.name == "postgresql":
        query = query.where(text("ST_DWithin(ST_SetSRID(ST_MakePoint(lost_cases.longitude,lost_cases.latitude),4326)::geography, ST_SetSRID(ST_MakePoint(:obs_lon,:obs_lat),4326)::geography, LEAST(lost_cases.search_radius_meters,:max_radius) + LEAST(COALESCE(lost_cases.location_accuracy_meters,0),1000) + :obs_accuracy)")).params(
            obs_lon=observation.longitude, obs_lat=observation.latitude, max_radius=settings.matching_max_radius_meters,
            obs_accuracy=min(observation.location_accuracy_meters or 0,1000))
    for case, pet in db.execute(query):
        distance = distance_meters(case.latitude, case.longitude, observation.latitude, observation.longitude)
        radius = min(case.search_radius_meters, settings.matching_max_radius_meters)
        accuracy = min(case.location_accuracy_meters or 0,1000) + min(observation.location_accuracy_meters or 0,1000)
        if distance <= radius + accuracy:
            yield case, pet, distance, radius, accuracy


def vectors(db, scope):
    rows = db.execute(select(Embedding, Photo, AnalysisJob).join(Photo, Embedding.photo_id == Photo.id).join(AnalysisJob, Embedding.analysis_job_id == AnalysisJob.id).where(
        scope, Embedding.dimension == 512, Embedding.space_id != "legacy", AnalysisJob.status == "SUCCEEDED"))
    return [item[0] for item in rows if is_current(db,item[2]) and row_spec(item[0]).space_id==item[0].space_id
            and row_spec(item[0]).to_dict()==item[2].input_snapshot.get("spec")]


def row_spec(row):
    return EmbeddingSpec(row.provider,row.model,row.revision,row.dimension,row.preprocessing_version)


def visual_similarity(db, observed, case):
    return visual_evidence(db,observed,case)[0]


def visual_evidence(db,observed,case):
    if not observed:
        return None,None,0.0
    scope = or_(and_(Photo.owner_type == "lost_case", Photo.owner_id == case.id), and_(Photo.owner_type == "pet", Photo.owner_id == case.pet_id))
    eligible = vectors(db, scope)
    if not eligible:
        return None,None,0.0
    groups={}
    for left in observed:
        for right in eligible:
            if not compatible(row_spec(left),row_spec(right)):
                continue
            quality=min((left.quality or {}).get("visual_reliability",.5),(right.quality or {}).get("visual_reliability",.5))
            groups.setdefault(left.space_id,[]).append((cosine(left.vector,right.vector),quality,left.provider))
    if not groups:
        return None,None,0.0
    # Current selection normally yields one space. If there are several, do not combine raw cosines.
    if len(groups)!=1:
        return None,None,0.0
    pairs=sorted(next(iter(groups.values())),reverse=True)
    raw=aggregate_visual_similarity([item[0] for item in pairs])
    weight=settings.visual_best_weight
    quality=pairs[0][1] if len(pairs)==1 else weight*pairs[0][1]+(1-weight)*pairs[1][1]
    return raw,pairs[0][2],quality


def evaluate_observation(db, identity):
    observation = db.scalar(select(Observation).where(Observation.id == identity, Observation.linked_case_id.is_(None)).with_for_update(skip_locked=True))
    if observation is None:
        return
    observation.matching_checked_at = utcnow()
    prior = {item.lost_case_id: item for item in db.scalars(select(Match).where(Match.observation_id == identity))}
    for match in prior.values():
        match.is_active = False
    db.execute(update(Notification).where(Notification.match_id.in_([item.id for item in prior.values()])).values(is_active=False))
    if not is_supported_species(observation.species) or observation.moderation_status!="VISIBLE":
        observation.matching_status="INACTIVE"
        return
    if observation.latitude is None or observation.longitude is None or aware(observation.observed_at) > utcnow() + timedelta(minutes=1):
        observation.matching_status = "INSUFFICIENT"
        return
    observed_traits, waiting = evidence(db, "observation", identity, declared_traits(observation))
    observed_vectors = None
    if observed_traits.get("_species_conflict"):
        observation.matching_status="INSUFFICIENT"
        return
    if waiting:
        observation.matching_status = "WAITING_ANALYSIS"
        return
    ranked = []
    for case, pet, distance, radius, accuracy in candidates(db, observation):
        target, case_waiting = evidence(db, "lost_case", case.id, declared_traits(pet))
        target, pet_waiting = evidence(db, "pet", pet.id, target)
        if target.get("_species_conflict"):
            continue
        if case_waiting or pet_waiting:
            waiting = True
            continue
        expected, observed = comparable_traits(pet, target, observation, observed_traits)
        feature, coverage, reasons, contradiction = feature_similarity(expected, observed)
        if contradiction or feature < .5:
            continue
        if observed_vectors is None:
            observed_vectors = vectors(db, and_(Photo.owner_type == "observation", Photo.owner_id == identity)) if settings.embeddings_enabled else []
        raw_visual,visual_provider,visual_quality = visual_evidence(db, observed_vectors, case)
        if coverage < (.25 if raw_visual is not None else .35):
            continue
        days = (aware(observation.observed_at) - aware(case.lost_at)).total_seconds() / 86400
        score, visual, geo, temporal = combine(feature, raw_visual, distance, radius, days, accuracy,provider=visual_provider or "open_clip",quality=visual_quality)
        if score < settings.matching_candidate_threshold:
            continue
        reasons += [f"Avistamiento a {distance / 1000:.1f} km de la última ubicación", "Fecha posterior a la pérdida"]
        if raw_visual is not None:
            reasons.append("Similitud visual entre las fotos" if visual >= .5 else "Las fotos aportan similitud visual limitada")
        match = prior.get(case.id)
        if match is None:
            match = Match(lost_case_id=case.id, observation_id=identity)
            db.add(match)
        for field, value in {"feature_score": feature, "visual_score": visual, "visual_similarity": raw_visual, "geo_score": geo,
            "temporal_score": temporal, "final_score": score, "evidence_coverage": coverage, "distance_meters": distance, "explanation": reasons, "is_active": True}.items():
            setattr(match,field,value)
        record_recommendation(match, "GENERAL",visual_provider=visual_provider,db=db)
        db.flush()
        ranked.append(match)
        if notification_evidence(score,coverage,feature,geo) and match.status not in {"FALSE_MATCH", "RESOLVED"} and observation.author_id != pet.owner_id:
            notification = db.scalar(select(Notification).where(Notification.lost_case_id == case.id, Notification.observation_id == identity))
            if notification is None:
                notification = Notification(owner_id=pet.owner_id,lost_case_id=case.id,observation_id=identity,match_id=match.id,kind="POSSIBLE_MATCH",
                    title=f"Posible avistamiento de {pet.name}"[:180],body="Encontramos un reporte compatible con las características, la ubicación y la fecha de tu aviso. Revisá los motivos y la evidencia; la identidad está por confirmar.", email_available_at=utcnow()+timedelta(seconds=settings.mail_group_seconds))
                db.add(notification)
            notification.is_active = True
            if match.status == "NEW":
                match.status = "NOTIFIED"
    observation.matching_status = "WAITING_ANALYSIS" if waiting else "MATCHES_FOUND" if ranked else "NO_MATCHES"
    best = max(ranked, key=lambda item: item.final_score) if ranked else None
    observation.matching_score = best.final_score if best else None
    observation.matching_reasons = best.explanation if best else []


def reconcile_general(session_factory=None):
    factory = session_factory or SessionLocal
    with factory() as db:
        identities = list(db.scalars(select(Observation.id).where(Observation.linked_case_id.is_(None), Observation.matching_status.in_(["PENDING","WAITING_ANALYSIS"]),
            or_(Observation.matching_checked_at.is_(None), Observation.matching_checked_at < utcnow() - timedelta(seconds=20))).order_by(Observation.matching_checked_at.asc().nullsfirst(), Observation.created_at).limit(30)))
    for identity in identities:
        with factory() as db:
            evaluate_observation(db,identity)
            db.commit()


async def general_matching_loop():
    while True:
        try:
            await asyncio.to_thread(reconcile_general)
        except Exception:
            log_event("general_matching_deferred")
        await asyncio.sleep(5)
