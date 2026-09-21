from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._common import utcnow

PRESENT = "present"
ABSENT = "absent"


class AttendanceMark(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("plan_id", "candidate_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(10))
    method: Mapped[str] = mapped_column(String(10), default="tap")
    marked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None)
    marked_at: Mapped[datetime] = mapped_column(default=utcnow)


class HallSubmission(Base):
    __tablename__ = "hall_submissions"
    __table_args__ = (UniqueConstraint("plan_id", "hall_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="CASCADE"))
    submitted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None)
    submitted_at: Mapped[datetime] = mapped_column(default=utcnow)
