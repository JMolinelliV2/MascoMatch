from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import current_user
from app.models import Observation, User
from app.schemas import ObservationCreate, ObservationRead, ObservationUpdate

router = APIRouter(prefix="/observations", tags=["observations"])


@router.post("", response_model=ObservationRead, status_code=status.HTTP_201_CREATED)
def create_observation(payload: ObservationCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    observation = Observation(author_id=user.id, **payload.model_dump())
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@router.get("", response_model=list[ObservationRead])
def list_observations(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    query = select(Observation).order_by(Observation.created_at.desc()).limit(limit)
    return list(db.scalars(query))


@router.get("/{observation_id}", response_model=ObservationRead)
def get_observation(observation_id: UUID, db: Session = Depends(get_db)):
    observation = db.get(Observation, observation_id)
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation


@router.patch("/{observation_id}", response_model=ObservationRead)
def update_observation(observation_id: UUID, payload: ObservationUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    observation = db.get(Observation, observation_id)
    if observation is None or observation.author_id != user.id:
        raise HTTPException(status_code=404, detail="Observation not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(observation, field, value)
    db.commit()
    db.refresh(observation)
    return observation


@router.delete("/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observation(observation_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    observation = db.get(Observation, observation_id)
    if observation is None or observation.author_id != user.id:
        raise HTTPException(status_code=404, detail="Observation not found")
    db.delete(observation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

