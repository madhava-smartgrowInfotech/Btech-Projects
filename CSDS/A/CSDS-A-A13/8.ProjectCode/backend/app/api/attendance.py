from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.deps import DB, CurrentUser
from app.services import attendance

router = APIRouter(tags=["attendance"])


class MarkIn(BaseModel):
    status: Literal["present", "absent"] | None = Field(None, description="null clears the mark")


class ScanIn(BaseModel):
    code: str = Field(..., max_length=500, description="A scanned slip (URL) or a typed roll number")


@router.get("/attendance/assignments", summary="Halls to take attendance in (mine, or all for administrators)")
def my_assignments(db: DB, user: CurrentUser) -> list[dict]:
    return attendance.assignments(db, user)


@router.put("/plans/{plan_id}/halls/{hall_id}/attendance/{candidate_id}", summary="Mark one candidate")
def mark(plan_id: int, hall_id: int, candidate_id: int, body: MarkIn, db: DB, user: CurrentUser) -> dict:
    return attendance.mark(db, plan_id, hall_id, candidate_id, body.status, user)


@router.post("/plans/{plan_id}/halls/{hall_id}/attendance/scan", summary="Mark present from a scanned slip or typed roll number")
def scan(plan_id: int, hall_id: int, body: ScanIn, db: DB, user: CurrentUser) -> dict:
    return attendance.scan(db, plan_id, hall_id, body.code, user)


@router.post("/plans/{plan_id}/halls/{hall_id}/attendance/mark-remaining-absent", summary="Mark everyone not yet marked as absent")
def remaining_absent(plan_id: int, hall_id: int, db: DB, user: CurrentUser) -> dict:
    return attendance.mark_remaining_absent(db, plan_id, hall_id, user)


@router.post("/plans/{plan_id}/halls/{hall_id}/attendance/submit", summary="Submit and lock the hall register")
def submit(plan_id: int, hall_id: int, db: DB, user: CurrentUser) -> dict:
    return attendance.submit(db, plan_id, hall_id, user)


@router.post("/plans/{plan_id}/halls/{hall_id}/attendance/reopen", summary="Reopen a submitted register (administrators)")
def reopen(plan_id: int, hall_id: int, db: DB, user: CurrentUser) -> dict:
    return attendance.reopen(db, plan_id, hall_id, user)
