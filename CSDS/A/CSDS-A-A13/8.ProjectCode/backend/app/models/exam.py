"""Reference data: departments, courses, candidates, halls and the timetable."""
from __future__ import annotations

from datetime import date, time

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), index=True)

    department: Mapped[Department] = relationship(lazy="joined")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    roll_no: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), index=True)
    email: Mapped[str | None] = mapped_column(String(200), default=None)
    date_of_birth: Mapped[date | None] = mapped_column(default=None)
    needs_accessible_seat: Mapped[bool] = mapped_column(Boolean, default=False)

    department: Mapped[Department] = relationship(lazy="joined")
    registrations: Mapped[list[Registration]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("candidate_id", "course_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)

    candidate: Mapped[Candidate] = relationship(back_populates="registrations")
    course: Mapped[Course] = relationship(lazy="joined")


class Hall(Base):
    __tablename__ = "halls"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    building: Mapped[str] = mapped_column(String(120), default="")
    floor: Mapped[str] = mapped_column(String(40), default="")
    rows: Mapped[int] = mapped_column(Integer)
    cols: Mapped[int] = mapped_column(Integer)
    blocked_seats: Mapped[list[str]] = mapped_column(JSON, default=list)
    accessible_seats: Mapped[list[str]] = mapped_column(JSON, default=list)
    aisles_after_cols: Mapped[list[int]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def capacity(self) -> int:
        return self.rows * self.cols - len(self.blocked_seats or [])


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    __table_args__ = (UniqueConstraint("date", "start_time"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    date: Mapped[date]
    start_time: Mapped[time]
    end_time: Mapped[time]
    label: Mapped[str] = mapped_column(String(120), default="")

    papers: Mapped[list[SessionPaper]] = relationship(back_populates="session", cascade="all, delete-orphan")


class SessionPaper(Base):
    __tablename__ = "session_papers"
    __table_args__ = (UniqueConstraint("session_id", "course_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    paper_group: Mapped[str | None] = mapped_column(String(40), default=None)

    session: Mapped[ExamSession] = relationship(back_populates="papers")
    course: Mapped[Course] = relationship(lazy="joined")
