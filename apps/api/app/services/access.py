from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LostCase, Observation, Pet, User


def owner_has_access(owner_type: str, owner_id: UUID, db: Session, user: User) -> bool:
    if owner_type == "pet":
        return db.scalar(select(Pet.id).where(Pet.id == owner_id, Pet.owner_id == user.id)) is not None
    if owner_type == "lost_case":
        return db.scalar(select(LostCase.id).join(Pet).where(LostCase.id == owner_id, Pet.owner_id == user.id)) is not None
    if owner_type == "observation":
        return db.scalar(select(Observation.id).where(Observation.id == owner_id, Observation.author_id == user.id)) is not None
    return False
