from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.analysis.service import purge_owner, schedule_text
from app.dependencies import current_user
from app.models import LostCase, Pet, User
from app.schemas import LostCaseCreate, LostCaseRead, LostCaseUpdate

router = APIRouter(prefix="/lost-cases", tags=["lost-cases"])


def owned_case(db: Session, case_id: UUID, user: User) -> LostCase:
    case = db.scalar(select(LostCase).join(Pet).where(LostCase.id == case_id, Pet.owner_id == user.id))
    if case is None:
        raise HTTPException(status_code=404, detail="Lost case not found")
    return case


@router.post("", response_model=LostCaseRead, status_code=status.HTTP_201_CREATED)
def create_lost_case(payload: LostCaseCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pet = db.scalar(select(Pet).where(Pet.id == payload.pet_id, Pet.owner_id == user.id))
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    case = LostCase(**payload.model_dump())
    db.add(case)
    db.flush()
    schedule_text(db, "lost_case", case.id)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[LostCaseRead])
def list_lost_cases(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(LostCase).join(Pet).where(Pet.owner_id == user.id).order_by(LostCase.created_at.desc()).limit(limit)
    return list(db.scalars(query))


@router.get("/{case_id}", response_model=LostCaseRead)
def get_lost_case(case_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return owned_case(db, case_id, user)


@router.patch("/{case_id}", response_model=LostCaseRead)
def update_lost_case(case_id: UUID, payload: LostCaseUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    case = owned_case(db, case_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.flush()
    schedule_text(db, "lost_case", case.id)
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lost_case(case_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    case = owned_case(db, case_id, user)
    purge_owner(db, "lost_case", case_id)
    db.delete(case)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

