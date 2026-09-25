from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Department, PriorityEnum, Visit, VisitStatusEnum

PRIORITY_RANK = {PriorityEnum.critical: 0, PriorityEnum.urgent: 1, PriorityEnum.normal: 2}

ACTIVE_STATUSES = [
    VisitStatusEnum.waiting,
    VisitStatusEnum.in_consultation,
    VisitStatusEnum.lab_pending,
    VisitStatusEnum.lab_in_progress,
    VisitStatusEnum.pharmacy,
]


def next_token_number(db: Session, department_id: str) -> int:
    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count = (
        db.query(func.count(Visit.id))
        .filter(Visit.current_department_id == department_id, Visit.created_at >= start_of_day)
        .scalar()
    )
    return int(count or 0) + 1


def make_token_code(department: Department, token_number: int) -> str:
    return f"{department.code}-{token_number:03d}"


def queue_ahead_count(db: Session, department_id: str, priority: PriorityEnum) -> int:
    """How many waiting patients in this department rank ahead of a new arrival at this priority."""
    query = db.query(func.count(Visit.id)).filter(
        Visit.current_department_id == department_id,
        Visit.status == VisitStatusEnum.waiting,
    )
    if priority == PriorityEnum.critical:
        return 0  # critical patients jump the queue
    if priority == PriorityEnum.urgent:
        query = query.filter(Visit.priority.in_([PriorityEnum.critical, PriorityEnum.urgent]))
    return int(query.scalar() or 0)


def sort_key(visit: Visit):
    return (PRIORITY_RANK.get(visit.priority, 3), visit.token_number)
