from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .common import ORMModel, UTCDateTime

Status = Literal["detected", "registered", "acknowledged", "in_progress", "resolved", "verified", "dismissed"]


class ComplaintEventOut(ORMModel):
    id: int
    ts: UTCDateTime
    kind: str
    from_status: str | None
    to_status: str | None
    actor_label: str
    note: str | None


class ComplaintOut(ORMModel):
    id: int
    ref_code: str
    h3_cell: str
    operator: str
    lat: float
    lon: float
    status: Status
    severity: str
    origin: str
    source: str
    reporter_user_id: int | None
    assigned_to_id: int | None
    assigned_to_name: str | None = None
    reporter_name: str | None = None
    summary: str | None
    reopen_count: int
    detected_at: UTCDateTime
    registered_at: UTCDateTime | None
    acknowledged_at: UTCDateTime | None
    in_progress_at: UTCDateTime | None
    resolved_at: UTCDateTime | None
    verified_at: UTCDateTime | None
    dismissed_at: UTCDateTime | None
    updated_at: UTCDateTime
    readings: int = 0
    bad_share: float | None = None
    verification: dict | None = None


class ComplaintDetail(ComplaintOut):
    evidence: dict
    suggestion: dict | None = None
    boundary: list[list[float]] = []
    events: list[ComplaintEventOut] = []


class ComplaintPage(BaseModel):
    items: list[ComplaintOut]
    total: int
    counts: dict[str, int]


class TransitionIn(BaseModel):
    to: Literal["registered", "acknowledged", "in_progress", "resolved", "verified", "dismissed"]
    note: str | None = Field(default=None, max_length=2000)


class AssignIn(BaseModel):
    user_id: int | None = None


class NoteIn(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class ReportIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    operator: str | None = Field(default=None, max_length=80)
    note: str = Field(min_length=3, max_length=2000, description="What the user experienced")
