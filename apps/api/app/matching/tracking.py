"""Record actual recommendations once; receipts alone are not recommendations."""
from app.analysis.prompts import TEXT_PROMPT_VERSION, VISION_PROMPT_VERSION
from app.analysis.service import utcnow
from app.core.config import settings
from app.embeddings.provider import VERSION, model_id
from app.models import MatchFeedbackEvent


def record_recommendation(match, source):
    if match.recommended_at is not None:
        return
    match.recommended_at = utcnow()
    match.recommendation_source = source
    match.recommended_score = match.final_score
    match.recommendation_snapshot = {
        "legacy": False, "tracking_version": "matching-tracking-v1",
        "ai_enabled": settings.ai_enabled, "embeddings_enabled": settings.embeddings_enabled,
        "text_model": settings.ai_text_model, "vision_model": settings.ai_vision_model,
        "text_prompt": TEXT_PROMPT_VERSION, "vision_prompt": VISION_PROMPT_VERSION,
        "embedding_model": model_id(), "embedding_version": VERSION,
        "candidate_threshold": settings.matching_candidate_threshold,
        "notify_threshold": settings.matching_notify_threshold,
        "linked_threshold": settings.linked_match_threshold,
    }


def record_feedback(db, match, user, payload):
    if match.feedback_at is None or match.status != payload.status or payload.recovered:
        db.add(MatchFeedbackEvent(match_id=match.id, actor_id=user.id,
            previous_status=match.status, status=payload.status, recovered=payload.recovered,
            score=match.final_score, legacy=False, created_at=utcnow()))
