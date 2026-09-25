from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import LabTest, LabTestStatusEnum, RoleEnum, User, Visit, VisitStatusEnum
from app.schemas.schemas import LabTestCreate, LabTestOut, LabTestStatusUpdate
from app.services.deps import get_current_user, require_roles
from app.services.ws_manager import manager

router = APIRouter(prefix="/api/labs", tags=["labs"])


@router.post("", response_model=LabTestOut, status_code=201)
async def order_lab_test(
    payload: LabTestCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(RoleEnum.doctor, RoleEnum.admin)),
):
    visit = db.query(Visit).filter(Visit.id == payload.visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    lab_test = LabTest(visit_id=visit.id, test_name=payload.test_name)
    db.add(lab_test)
    visit.status = VisitStatusEnum.lab_pending
    db.commit()
    db.refresh(lab_test)

    out = LabTestOut.model_validate(lab_test)
    await manager.broadcast("lab_test_created", out.model_dump())
    return lab_test


@router.get("", response_model=list[LabTestOut])
def list_lab_tests(
    status_in: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(LabTest)
    if status_in:
        statuses = [LabTestStatusEnum(s) for s in status_in.split(",")]
        query = query.filter(LabTest.status.in_(statuses))
    return query.order_by(LabTest.ordered_at).all()


@router.patch("/{lab_test_id}/status", response_model=LabTestOut)
async def update_lab_test_status(
    lab_test_id: str,
    payload: LabTestStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(RoleEnum.lab_tech, RoleEnum.admin)),
):
    lab_test = db.query(LabTest).filter(LabTest.id == lab_test_id).first()
    if not lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")

    lab_test.status = payload.status
    if payload.notes:
        lab_test.notes = payload.notes
    if payload.status == LabTestStatusEnum.scheduled:
        lab_test.scheduled_at = datetime.utcnow()
    if payload.status == LabTestStatusEnum.completed:
        lab_test.completed_at = datetime.utcnow()
        visit = db.query(Visit).filter(Visit.id == lab_test.visit_id).first()
        if visit and visit.status == VisitStatusEnum.lab_in_progress:
            visit.status = VisitStatusEnum.pharmacy

    db.commit()
    db.refresh(lab_test)

    out = LabTestOut.model_validate(lab_test)
    await manager.broadcast("lab_test_updated", out.model_dump())
    return lab_test
