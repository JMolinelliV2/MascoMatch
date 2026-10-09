from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Response,Query
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy import select
from app.db.session import get_db
from app.dependencies import current_user,optional_user
from app.models import AdminAudit,LostCase,ModerationReport,Observation,Pet,User,Notification,AnalysisJob,Match,Photo
from app.matching.linked import mark_related_pending
router=APIRouter(tags=["moderation"])


class ReportInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    target_type:Literal["lost_case","observation"]
    target_id:UUID
    reason:Literal["SPAM","FALSE_INFORMATION","INAPPROPRIATE_PHOTO","OTHER"]
    detail:str=Field(default="",max_length=1000)


class ReviewInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    action:Literal["DISMISS","HIDE","RESTORE","BLOCK_AUTHOR"]


class CorrectionInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    description:str=Field(min_length=1,max_length=4000)


class UserStatusInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status:Literal["ACTIVE","BLOCKED"]


def admin(user=Depends(current_user)):
    if user.role!="ADMIN":raise HTTPException(status_code=403,detail="Acceso reservado a administradores.")
    return user


@router.post("/reports",status_code=201)
def create_report(payload:ReportInput,db=Depends(get_db),user=Depends(optional_user)):
    target=db.get(LostCase if payload.target_type=="lost_case" else Observation,payload.target_id)
    if target is None or target.moderation_status!="VISIBLE":raise HTTPException(status_code=404,detail="Publicación no encontrada.")
    report=ModerationReport(reporter_id=user.id if user else None,**payload.model_dump())
    db.add(report);db.commit()
    return {"id":report.id,"status":report.status}


@router.get("/admin/reports")
def reports(response:Response,status:str=Query(default="OPEN",max_length=24),db=Depends(get_db),user=Depends(admin)):
    response.headers["Cache-Control"]="no-store"
    query=select(ModerationReport).order_by(ModerationReport.created_at.desc())
    if status:query=query.where(ModerationReport.status==status)
    items=[]
    for report in db.scalars(query.limit(100)):
        target=db.get(LostCase if report.target_type=="lost_case" else Observation,report.target_id)
        title=db.get(Pet,target.pet_id).name if isinstance(target,LostCase) else "Avistamiento" if target else "Publicación eliminada"
        items.append({"id":report.id,"target_type":report.target_type,"target_id":report.target_id,"title":title,"reason":report.reason,"detail":report.detail,"status":report.status,"created_at":report.created_at,"visibility":target.moderation_status if target else None})
        if target:
            from sqlalchemy import and_,or_
            scope=Photo.owner_id==target.id
            scope=or_(and_(Photo.owner_type=="lost_case",Photo.owner_id==target.id),and_(Photo.owner_type=="pet",Photo.owner_id==target.pet_id)) if isinstance(target,LostCase) else and_(Photo.owner_type=="observation",Photo.owner_id==target.id)
            items[-1]["publication"]={"description":target.description,"photo_ids":list(db.scalars(select(Photo.id).where(scope)))}
    return {"items":items}


@router.patch("/admin/reports/{report_id}")
def review(report_id:UUID,payload:ReviewInput,db=Depends(get_db),user=Depends(admin)):
    report=db.scalar(select(ModerationReport).where(ModerationReport.id==report_id).with_for_update())
    if report is None:raise HTTPException(status_code=404,detail="Denuncia no encontrada.")
    target=db.get(LostCase if report.target_type=="lost_case" else Observation,report.target_id)
    if payload.action!="DISMISS" and target is None:raise HTTPException(status_code=404,detail="Publicación no encontrada.")
    if payload.action=="DISMISS":report.status="DISMISSED"
    else:
        target.moderation_status="VISIBLE" if payload.action=="RESTORE" else "HIDDEN"
        db.flush()
        mark_related_pending(db,report.target_type,target.id)
        if payload.action=="BLOCK_AUTHOR":
            author_id=db.get(Pet,target.pet_id).owner_id if isinstance(target,LostCase) else target.author_id
            if author_id==user.id:raise HTTPException(status_code=409,detail="No podés bloquear tu propia cuenta.")
            if author_id:
                author=db.get(User,author_id);author.status="BLOCKED"
                for case in db.scalars(select(LostCase).join(Pet).where(Pet.owner_id==author_id)):
                    case.moderation_status="HIDDEN";db.flush();mark_related_pending(db,"lost_case",case.id)
                for obs in db.scalars(select(Observation).where(Observation.author_id==author_id)):
                    obs.moderation_status="HIDDEN";db.flush();mark_related_pending(db,"observation",obs.id)
        report.status="ACTION_TAKEN"
    db.add(AdminAudit(actor_id=user.id,action=payload.action,target_type=report.target_type,target_id=report.target_id,report_id=report.id))
    db.commit()
    return {"id":report.id,"status":report.status}


@router.get("/admin/overview")
def overview(response:Response,db=Depends(get_db),user=Depends(admin)):
    from sqlalchemy import func
    response.headers["Cache-Control"]="no-store"
    counts={model.__tablename__:db.scalar(select(func.count()).select_from(model)) for model in (User,Pet,LostCase,Observation,Match,ModerationReport)}
    failures=[{"id":job.id,"source":job.source_type,"error_code":job.error_code,"finished_at":job.finished_at} for job in db.scalars(select(AnalysisJob).where(AnalysisJob.status=="FAILED").order_by(AnalysisJob.finished_at.desc()).limit(50))]
    audits=[{"action":item.action,"target_type":item.target_type,"target_id":item.target_id,"created_at":item.created_at} for item in db.scalars(select(AdminAudit).order_by(AdminAudit.created_at.desc()).limit(50))]
    return {"counts":counts,"ai_failures":failures,"audit":audits}


@router.get("/admin/records/{kind}")
def records(kind:Literal["users","pets","lost_cases","observations","matches"],response:Response,limit:int=Query(default=50,ge=1,le=100),offset:int=Query(default=0,ge=0,le=10000),db=Depends(get_db),user=Depends(admin)):
    config={"users":(User,["id","name","status","role"]),"pets":(Pet,["id","name","species","owner_id"]),
        "lost_cases":(LostCase,["id","status","moderation_status","description","pet_id"]),"observations":(Observation,["id","source_type","moderation_status","description","author_id"]),
        "matches":(Match,["id","status","lost_case_id","observation_id","final_score","explanation"])}
    model,fields=config[kind]
    response.headers["Cache-Control"]="no-store"
    return {"items":[{field:getattr(item,field) for field in fields} for item in db.scalars(select(model).order_by(model.created_at.desc()).offset(offset).limit(limit))]}


@router.patch("/admin/publications/{kind}/{identity}")
def correct(kind:Literal["lost_case","observation"],identity:UUID,payload:CorrectionInput,db=Depends(get_db),user=Depends(admin)):
    target=db.get(LostCase if kind=="lost_case" else Observation,identity)
    if target is None:raise HTTPException(status_code=404,detail="Publicación no encontrada.")
    previous=target.description;target.description=payload.description
    db.add(AdminAudit(actor_id=user.id,action="CORRECT_DESCRIPTION",target_type=kind,target_id=identity,details={"previous_description":previous,"new_description":payload.description}))
    db.flush()
    from app.analysis.service import schedule_text
    schedule_text(db,kind,identity);mark_related_pending(db,kind,identity);db.commit()
    return {"id":target.id,"description":target.description}


@router.patch("/admin/users/{identity}/status")
def user_status(identity:UUID,payload:UserStatusInput,db=Depends(get_db),user=Depends(admin)):
    target=db.get(User,identity)
    if target is None:raise HTTPException(status_code=404,detail="Cuenta no encontrada.")
    if identity==user.id and payload.status!="ACTIVE":raise HTTPException(status_code=409,detail="No podés bloquear tu propia cuenta.")
    target.status=payload.status
    if payload.status=="BLOCKED":
        for case in db.scalars(select(LostCase).join(Pet).where(Pet.owner_id==identity)):
            case.moderation_status="HIDDEN";db.flush();mark_related_pending(db,"lost_case",case.id)
        for obs in db.scalars(select(Observation).where(Observation.author_id==identity)):
            obs.moderation_status="HIDDEN";db.flush();mark_related_pending(db,"observation",obs.id)
    db.add(AdminAudit(actor_id=user.id,action="BLOCK_USER" if payload.status=="BLOCKED" else "UNBLOCK_USER",target_type="user",target_id=identity))
    db.commit();return {"id":target.id,"status":target.status}


@router.get("/admin/reports/{report_id}/photos/{photo_id}")
def report_photo(report_id:UUID,photo_id:UUID,db=Depends(get_db),user=Depends(admin)):
    from sqlalchemy import and_,or_
    from app.core.image_storage import load_analysis_image
    report=db.get(ModerationReport,report_id)
    target=db.get(LostCase if report and report.target_type=="lost_case" else Observation,report.target_id) if report else None
    if target is None:raise HTTPException(status_code=404,detail="Publicación no encontrada.")
    scope=or_(and_(Photo.owner_type=="lost_case",Photo.owner_id==target.id),and_(Photo.owner_type=="pet",Photo.owner_id==target.pet_id)) if isinstance(target,LostCase) else and_(Photo.owner_type=="observation",Photo.owner_id==target.id)
    photo=db.scalar(select(Photo).where(Photo.id==photo_id,scope))
    if photo is None:raise HTTPException(status_code=404,detail="Foto no encontrada.")
    try:payload,mime=load_analysis_image(photo.storage_key,photo.mime_type)
    except Exception as exc:raise HTTPException(status_code=503,detail="La foto no está disponible.") from exc
    return Response(payload,media_type=mime,headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"})
