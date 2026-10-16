"""Reselect visual spaces after an owner edit, keeping historical rows intact."""
from sqlalchemy import select
from app.models import LostCase


def reschedule_owner(db,owner_type,owner_id):
    from app.analysis.service import schedule_owner
    from app.matching.linked import mark_related_pending
    schedule_owner(db,owner_type,owner_id)
    mark_related_pending(db,owner_type,owner_id)
    if owner_type=="pet":
        for case in db.scalars(select(LostCase).where(LostCase.pet_id==owner_id)):
            schedule_owner(db,"lost_case",case.id)
            mark_related_pending(db,"lost_case",case.id)
