from __future__ import annotations

import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.ml.predictor import DEFAULT_VITALS, predict_triage, predict_wait_minutes
from app.models.models import (
    Department,
    MovementLog,
    Patient,
    PriorityEnum,
    RoleEnum,
    User,
    Visit,
    VisitStatusEnum,
)
from app.schemas.schemas import (
    AssignDoctorRequest,
    VisitCreate,
    VisitOut,
    VisitStatusUpdate,
)
from app.services.deps import get_current_user, require_roles
from app.services.queue_service import make_token_code, next_token_number, queue_ahead_count, sort_key
from app.services.ws_manager import manager

router = APIRouter(prefix="/api/visits", tags=["visits"])


def _gen_mrn(db: Session) -> str:
    while True:
        candidate = f"MRN{random.randint(100000, 999999)}"
        if not db.query(Patient).filter(Patient.mrn == candidate).first():
            return candidate


@router.post("", response_model=VisitOut, status_code=status.HTTP_201_CREATED)
async def create_visit(
    payload: VisitCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(RoleEnum.reception, RoleEnum.admin, RoleEnum.nurse)),
):
    department = db.query(Department).filter(Department.id == payload.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    patient = None
    if payload.patient.phone:
        patient = db.query(Patient).filter(Patient.phone == payload.patient.phone).first()
    if not patient:
        patient = Patient(
            mrn=_gen_mrn(db),
            name=payload.patient.name,
            age=payload.patient.age,
            gender=payload.patient.gender,
            phone=payload.patient.phone,
            blood_group=payload.patient.blood_group,
        )
        db.add(patient)
        db.flush()

    vitals_dict = payload.vitals.model_dump() if payload.vitals else None
    triage_source = {**DEFAULT_VITALS, **{k: v for k, v in (vitals_dict or {}).items() if v is not None}}

    priority_label, confidence = predict_triage(
        age=patient.age,
        heart_rate=triage_source["heart_rate"],
        systolic_bp=triage_source["systolic_bp"],
        spo2=triage_source["spo2"],
        temperature_c=triage_source["temperature_c"],
        respiratory_rate=triage_source["respiratory_rate"],
    )
    priority = PriorityEnum(priority_label)

    token_number = next_token_number(db, department.id)
    token_code = make_token_code(department, token_number)
    ahead = queue_ahead_count(db, department.id, priority)
    predicted_wait = predict_wait_minutes(
        department_type=department.type.value,
        queue_ahead=ahead,
        priority=priority.value,
        avg_service_minutes=department.avg_service_minutes,
    )

    visit = Visit(
        patient_id=patient.id,
        token_number=token_number,
        token_code=token_code,
        chief_complaint=payload.chief_complaint,
        vitals=vitals_dict,
        status=VisitStatusEnum.waiting,
        priority=priority,
        current_department_id=department.id,
        predicted_wait_minutes=predicted_wait,
        triage_score=confidence,
    )
    db.add(visit)
    db.flush()
    db.add(MovementLog(visit_id=visit.id, from_department_id=None, to_department_id=department.id, note="Registered"))
    db.commit()
    db.refresh(visit)

    visit_out = VisitOut.model_validate(visit)
    await manager.broadcast("visit_created", visit_out.model_dump())
    return visit


@router.get("", response_model=list[VisitOut])
def list_visits(
    department_id: str | None = None,
    status_in: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Visit).options(joinedload(Visit.patient))
    if department_id:
        query = query.filter(Visit.current_department_id == department_id)
    if status_in:
        statuses = [VisitStatusEnum(s) for s in status_in.split(",")]
        query = query.filter(Visit.status.in_(statuses))
    visits = query.all()
    visits.sort(key=sort_key)
    return visits


@router.get("/{visit_id}", response_model=VisitOut)
def get_visit(visit_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    visit = db.query(Visit).options(joinedload(Visit.patient)).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


@router.patch("/{visit_id}/status", response_model=VisitOut)
async def update_visit_status(
    visit_id: str,
    payload: VisitStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(
        require_roles(RoleEnum.doctor, RoleEnum.nurse, RoleEnum.lab_tech, RoleEnum.admin, RoleEnum.reception)
    ),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    old_department_id = visit.current_department_id
    visit.status = payload.status

    if payload.department_id and payload.department_id != old_department_id:
        visit.current_department_id = payload.department_id
        db.add(
            MovementLog(
                visit_id=visit.id,
                from_department_id=old_department_id,
                to_department_id=payload.department_id,
                note=payload.note,
            )
        )
        new_department = db.query(Department).filter(Department.id == payload.department_id).first()
        if new_department:
            ahead = queue_ahead_count(db, new_department.id, visit.priority)
            visit.predicted_wait_minutes = predict_wait_minutes(
                department_type=new_department.type.value,
                queue_ahead=ahead,
                priority=visit.priority.value,
                avg_service_minutes=new_department.avg_service_minutes,
            )

    if payload.status == VisitStatusEnum.discharged:
        visit.discharged_at = datetime.utcnow()

    visit.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(visit)

    visit_out = VisitOut.model_validate(visit)
    await manager.broadcast("visit_updated", visit_out.model_dump())
    return visit


@router.patch("/{visit_id}/assign-doctor", response_model=VisitOut)
async def assign_doctor(
    visit_id: str,
    payload: AssignDoctorRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(RoleEnum.doctor, RoleEnum.admin, RoleEnum.nurse, RoleEnum.reception)),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    doctor = db.query(User).filter(User.id == payload.doctor_id, User.role == RoleEnum.doctor).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    visit.assigned_doctor_id = doctor.id
    visit.status = VisitStatusEnum.in_consultation
    db.commit()
    db.refresh(visit)

    visit_out = VisitOut.model_validate(visit)
    await manager.broadcast("visit_updated", visit_out.model_dump())
    return visit


@router.get("/{visit_id}/movements")
def get_movements(visit_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    logs = db.query(MovementLog).filter(MovementLog.visit_id == visit_id).order_by(MovementLog.timestamp).all()
    return [
        {
            "id": log.id,
            "from_department_id": log.from_department_id,
            "to_department_id": log.to_department_id,
            "note": log.note,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]
