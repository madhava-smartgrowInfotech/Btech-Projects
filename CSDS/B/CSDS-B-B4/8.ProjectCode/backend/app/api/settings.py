from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.holds import approver_for

router = APIRouter(prefix="/settings", tags=["settings"])

HOLD_CHOICES = (1, 2, 5, 10, 15, 30, 60, 120)


class SettingsOut(BaseModel):
    language: Literal["en", "hi", "te"]
    voice_enabled: bool
    auto_speak: bool
    hold_minutes: int
    hold_choices: list[int]
    trusted_approval_required: bool
    has_trusted_approver: bool
    sandbox_clock: str | None


class SettingsIn(BaseModel):
    language: Literal["en", "hi", "te"] | None = None
    voice_enabled: bool | None = None
    auto_speak: bool | None = None
    hold_minutes: int | None = Field(default=None, ge=1, le=120)
    trusted_approval_required: bool | None = None
    sandbox_clock: str | None = Field(default=None, description='"HH:MM" to simulate the time of day, "" to use the real clock')

    @field_validator("sandbox_clock")
    @classmethod
    def _clock(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v):
            raise ValueError("use HH:MM, for example 01:30")
        return v


def _out(user: User, db: Session) -> dict:
    s = user.settings
    return {
        "language": s.language,
        "voice_enabled": s.voice_enabled,
        "auto_speak": s.auto_speak,
        "hold_minutes": s.hold_minutes,
        "hold_choices": list(HOLD_CHOICES),
        "trusted_approval_required": s.trusted_approval_required,
        "has_trusted_approver": approver_for(db, user) is not None,
        "sandbox_clock": s.sandbox_clock,
    }


@router.get("", response_model=SettingsOut)
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return _out(user, db)


@router.put("", response_model=SettingsOut)
def update_settings(body: SettingsIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    s = user.settings
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "sandbox_clock":
            s.sandbox_clock = value or None
        elif value is not None:
            setattr(s, key, value)
    db.commit()
    db.refresh(user)
    return _out(user, db)
