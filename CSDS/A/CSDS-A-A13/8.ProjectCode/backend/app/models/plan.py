"""Seating plans, their seat assignments and hall invigilators."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._common import utcnow

PLAN_DRAFT = "draft"
PLAN_PUBLISHED = "published"
PLAN_ARCHIVED = "archived"


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("session_id", "version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default=PLAN_DRAFT)
    seed: Mapped[int] = mapped_column(BigInteger)
    rules: Mapped[dict] = mapped_column(JSON)
    hall_ids: Mapped[list[int]] = mapped_column(JSON)
    engine_version: Mapped[str] = mapped_column(String(20))
    data_fingerprint: Mapped[str] = mapped_column(String(64))
    solver_hash: Mapped[str] = mapped_column(String(64))
    assignment_hash: Mapped[str] = mapped_column(String(64))
    solve_ms: Mapped[int] = mapped_column(Integer)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    scorecard: Mapped[dict] = mapped_column(JSON, default=dict)
    baseline: Mapped[dict] = mapped_column(JSON, default=dict)
    swaps: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(default=None)

    session = relationship("ExamSession", lazy="joined")
    seats: Mapped[list[SeatAssignment]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class SeatAssignment(Base):
    __tablename__ = "seat_assignments"
    __table_args__ = (
        UniqueConstraint("plan_id", "candidate_id"),
        UniqueConstraint("plan_id", "hall_id", "row", "col"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="CASCADE"), index=True)
    row: Mapped[int] = mapped_column(Integer)
    col: Mapped[int] = mapped_column(Integer)
    seat_label: Mapped[str] = mapped_column(String(10))

    plan: Mapped["Plan"] = relationship(back_populates="seats")
    candidate = relationship("Candidate", lazy="joined")
    course = relationship("Course", lazy="joined")


class InvigilatorAssignment(Base):
    __tablename__ = "invigilator_assignments"
    __table_args__ = (UniqueConstraint("plan_id", "hall_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    user = relationship("User", lazy="joined")
