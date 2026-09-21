from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ClaimIn(BaseModel):
    policy_id: int
    treatment: str = Field(min_length=2, max_length=200)
    hospitalization_type: Literal["planned", "emergency", "day_care", "not_sure"] = "planned"
    claim_mode: Literal["cashless", "reimbursement", "not_sure"] = "cashless"
    policy_start_date: date | None = None
    insured_age: int | None = Field(default=None, ge=0, le=120)
    pre_existing: Literal["yes", "no", "not_sure"] = "not_sure"
    estimated_cost: float | None = Field(default=None, ge=0, le=100_000_000)
    room_type: Literal["general_ward", "shared", "single_private", "deluxe", "icu", "not_sure"] = "not_sure"
    notes: str | None = Field(default=None, max_length=500)
    language: str | None = None

    @field_validator("policy_start_date")
    @classmethod
    def _not_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("The policy start date cannot be in the future")
        return v


class ClaimCaseOut(BaseModel):
    id: int
    policy_id: int
    policy_name: str
    treatment: str
    inputs: dict[str, Any]
    result: dict[str, Any]
    verdict: str
    checklist_state: dict[str, bool]
    language: str
    faithfulness: float | None
    total_ms: int | None
    model: str | None
    created_at: datetime


class ChecklistUpdate(BaseModel):
    item_id: str = Field(min_length=1, max_length=20)
    done: bool
