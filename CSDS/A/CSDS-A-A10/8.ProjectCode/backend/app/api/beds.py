from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    Bed,
    BedStatusEnum,
    DepartmentTypeEnum,
    RoleEnum,
    User,
    Visit,
    VisitStatusEnum,
)
from app.schemas.schemas import AdmitRequest, BedOut, BedStatusUpdate
from app.services.deps import get_current_user, require_roles
from app.services.ws_manager import manager

router = APIRouter(prefix="/api/beds", tags=["beds"])


@router.get("", response_model=list[BedOut])
def list_beds(department_id: str | None = None, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    query = db.query(Bed)
    if department_id:
        query = query.filter(Bed.department_id == department_id)
    return query.all()


@router.patch("/{bed_id}/status", response_model=BedOut)
async def update_bed_status(
    bed_id: str,
    payload: BedStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(RoleEnum.nurse, RoleEnum.admin)),
):
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    bed.status = payload.status
    if payload.status != BedStatusEnum.occupied:
        bed.current_visit_id = None
    db.commit()
    db.refresh(bed)
    bed_out = BedOut.model_validate(bed)
    await manager.broadcast("bed_updated", bed_out.model_dump())
    return bed


@router.post("/visits/{visit_id}/admit", response_model=BedOut)
async def admit_to_bed(
    visit_id: str,
    payload: AdmitRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(RoleEnum.doctor, RoleEnum.nurse, RoleEnum.admin)),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    bed = db.query(Bed).filter(Bed.id == payload.bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if bed.status != BedStatusEnum.available:
        raise HTTPException(status_code=400, detail="Bed is not available")

    bed.status = BedStatusEnum.occupied
    bed.current_visit_id = visit.id
    visit.bed_id = bed.id
    visit.current_department_id = bed.department_id
    visit.status = (
        VisitStatusEnum.admitted_icu
        if bed.department.type == DepartmentTypeEnum.icu
        else VisitStatusEnum.admitted_ward
    )
    db.commit()
    db.refresh(bed)
    db.refresh(visit)

    bed_out = BedOut.model_validate(bed)
    await manager.broadcast("bed_updated", bed_out.model_dump())
    from app.schemas.schemas import VisitOut

    await manager.broadcast("visit_updated", VisitOut.model_validate(visit).model_dump())
    return bed


@router.post("/visits/{visit_id}/release", response_model=BedOut)
async def release_bed(
    visit_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(RoleEnum.doctor, RoleEnum.nurse, RoleEnum.admin)),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit or not visit.bed_id:
        raise HTTPException(status_code=404, detail="No active bed assignment for this visit")
    bed = db.query(Bed).filter(Bed.id == visit.bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    bed.status = BedStatusEnum.cleaning
    bed.current_visit_id = None
    visit.bed_id = None
    visit.status = VisitStatusEnum.discharged
    db.commit()
    db.refresh(bed)

    bed_out = BedOut.model_validate(bed)
    await manager.broadcast("bed_updated", bed_out.model_dump())
    return bed
