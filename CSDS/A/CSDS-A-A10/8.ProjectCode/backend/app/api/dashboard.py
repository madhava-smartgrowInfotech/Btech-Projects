from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.models import (
    Bed,
    BedStatusEnum,
    Department,
    DepartmentTypeEnum,
    PriorityEnum,
    User,
    Visit,
    VisitStatusEnum,
)
from app.schemas.schemas import DepartmentLoad, KpiSummary
from app.services.deps import get_current_user
from app.services.queue_service import ACTIVE_STATUSES, sort_key

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard/kpis", response_model=KpiSummary)
def kpis(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    patients_today = db.query(func.count(Visit.id)).filter(Visit.created_at >= start_of_day).scalar() or 0
    active_visits = (
        db.query(func.count(Visit.id)).filter(Visit.status.in_(ACTIVE_STATUSES)).scalar() or 0
    )
    avg_wait = (
        db.query(func.avg(Visit.predicted_wait_minutes))
        .filter(Visit.status == VisitStatusEnum.waiting)
        .scalar()
        or 0.0
    )
    critical_cases = (
        db.query(func.count(Visit.id))
        .filter(Visit.priority == PriorityEnum.critical, Visit.status.in_(ACTIVE_STATUSES))
        .scalar()
        or 0
    )

    total_beds = db.query(func.count(Bed.id)).scalar() or 1
    occupied_beds = db.query(func.count(Bed.id)).filter(Bed.status == BedStatusEnum.occupied).scalar() or 0

    icu_dept_ids = [d.id for d in db.query(Department).filter(Department.type == DepartmentTypeEnum.icu).all()]
    total_icu = db.query(func.count(Bed.id)).filter(Bed.department_id.in_(icu_dept_ids)).scalar() or 1
    occupied_icu = (
        db.query(func.count(Bed.id))
        .filter(Bed.department_id.in_(icu_dept_ids), Bed.status == BedStatusEnum.occupied)
        .scalar()
        or 0
    )

    return KpiSummary(
        patients_today=patients_today,
        active_visits=active_visits,
        avg_wait_minutes=round(float(avg_wait), 1),
        critical_cases=critical_cases,
        bed_occupancy_pct=round((occupied_beds / total_beds) * 100, 1),
        icu_occupancy_pct=round((occupied_icu / total_icu) * 100, 1),
    )


@router.get("/api/dashboard/department-load", response_model=list[DepartmentLoad])
def department_load(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    departments = db.query(Department).all()
    result = []
    for dept in departments:
        waiting = (
            db.query(func.count(Visit.id))
            .filter(Visit.current_department_id == dept.id, Visit.status == VisitStatusEnum.waiting)
            .scalar()
            or 0
        )
        in_progress = (
            db.query(func.count(Visit.id))
            .filter(
                Visit.current_department_id == dept.id,
                Visit.status.in_(
                    [VisitStatusEnum.in_consultation, VisitStatusEnum.lab_in_progress, VisitStatusEnum.pharmacy]
                ),
            )
            .scalar()
            or 0
        )
        avg_wait = (
            db.query(func.avg(Visit.predicted_wait_minutes))
            .filter(Visit.current_department_id == dept.id, Visit.status == VisitStatusEnum.waiting)
            .scalar()
            or 0.0
        )
        result.append(
            DepartmentLoad(
                department=dept.name,
                code=dept.code,
                waiting=waiting,
                in_progress=in_progress,
                avg_wait_minutes=round(float(avg_wait), 1),
            )
        )
    return result


@router.get("/api/dashboard/queue-board")
def queue_board(db: Session = Depends(get_db)):
    """Public endpoint (no auth) that powers the waiting-room display screen."""
    departments = db.query(Department).filter(Department.type != DepartmentTypeEnum.icu).all()
    board = []
    for dept in departments:
        visits = (
            db.query(Visit)
            .options(joinedload(Visit.patient))
            .filter(Visit.current_department_id == dept.id, Visit.status.in_(ACTIVE_STATUSES))
            .all()
        )
        visits.sort(key=sort_key)
        now_serving = next((v for v in visits if v.status != VisitStatusEnum.waiting), None)
        waiting = [v for v in visits if v.status == VisitStatusEnum.waiting]
        board.append(
            {
                "department": dept.name,
                "code": dept.code,
                "now_serving": now_serving.token_code if now_serving else "—",
                "upcoming": [v.token_code for v in waiting[:5]],
                "waiting_count": len(waiting),
                "avg_wait_minutes": round(
                    sum(v.predicted_wait_minutes or 0 for v in waiting) / len(waiting), 1
                )
                if waiting
                else 0,
            }
        )
    return board
