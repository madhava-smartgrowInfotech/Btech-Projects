from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.settings import RulesIn


class PlanGenerateIn(BaseModel):
    rules: RulesIn = Field(default_factory=RulesIn)
    hall_ids: list[int] | None = Field(None, description="Halls to use; empty = every available hall")
    seed: int | None = Field(None, ge=1, le=2**31 - 1, description="Random seed; empty = drawn automatically")


class SessionRef(BaseModel):
    id: int
    code: str
    label: str
    date: date
    start_time: str
    end_time: str


class PersonRef(BaseModel):
    id: int
    full_name: str


class PlanHall(BaseModel):
    hall_id: int
    code: str
    name: str
    building: str
    capacity: int
    placed: int
    utilisation: float
    papers: dict[str, int]
    same_department_pairs: int
    invigilators: list[PersonRef]


class PlanSummary(BaseModel):
    id: int
    session: SessionRef
    version: int
    status: str
    seed: int
    solve_ms: int
    swaps: int
    created_at: datetime
    created_by: str | None
    published_at: datetime | None
    candidates: int
    halls_used: int
    utilisation: float
    same_paper_pairs: int
    roll_gap_violations: int
    accessible_violations: int
    same_department_pairs: int
    hard_ok: bool
    conflicts_avoided: int | None


class PlanOut(PlanSummary):
    rules: RulesIn
    hall_ids: list[int]
    engine_version: str
    data_fingerprint: str
    solver_hash: str
    assignment_hash: str
    scorecard: dict
    baseline: dict
    stats: dict
    halls: list[PlanHall]


class VerifyOut(BaseModel):
    plan_id: int
    seed: int
    data_unchanged: bool
    reproduced: bool
    stored_solver_hash: str
    recomputed_hash: str | None
    manual_moves: int
    engine_version: str
    solve_ms: int | None


class InvigilatorAssignmentIn(BaseModel):
    hall_id: int
    user_ids: list[int]


class InvigilatorsIn(BaseModel):
    assignments: list[InvigilatorAssignmentIn]


class SwapIn(BaseModel):
    hall_id: int
    from_seat: str = Field(..., examples=["C4"])
    to_seat: str = Field(..., examples=["D6"])


class AuditOut(BaseModel):
    id: int
    at: datetime
    action: str
    summary: str
    actor: str | None
    plan_id: int | None
    details: dict
