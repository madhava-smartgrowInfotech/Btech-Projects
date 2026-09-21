from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow


class ClaimCase(Base):
    __tablename__ = "claim_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id", ondelete="CASCADE"), index=True)
    treatment: Mapped[str] = mapped_column(String(300))
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any]] = mapped_column(JSON)
    verdict: Mapped[str] = mapped_column(String(30))  # covered | partly_covered | not_covered | needs_info
    checklist_state: Mapped[dict[str, bool]] = mapped_column(JSON, default=dict)
    language: Mapped[str] = mapped_column(String(8), default="en")
    faithfulness: Mapped[float | None] = mapped_column(Float)
    total_ms: Mapped[int | None] = mapped_column(Integer)
    model: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
