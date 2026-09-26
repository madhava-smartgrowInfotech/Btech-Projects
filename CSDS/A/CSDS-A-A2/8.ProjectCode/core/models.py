"""SQLAlchemy ORM models for Attendance Magic."""
from __future__ import annotations

from datetime import datetime

from core.timeutil import utcnow

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class User(Base):
    """Faculty or student account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # 'faculty' | 'student'
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # email or roll no
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    roll_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    # 512-d float32 ArcFace embedding of the enrolled reference face (students).
    face_embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    sessions: Mapped[list["AttendanceSession"]] = relationship(back_populates="faculty")
    devices: Mapped[list["DeviceBinding"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AttendanceSession(Base):
    """A time-bound, geo-fenced attendance window created by faculty."""

    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(32), nullable=False)
    course_name: Mapped[str] = mapped_column(String(128), nullable=False)
    section: Mapped[str] = mapped_column(String(32), default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[float] = mapped_column(Float, nullable=False)
    # Comma-separated roll-number patterns, e.g. "23K91A67*,24K95A6704"
    allowed_rolls: Mapped[str] = mapped_column(Text, default="*")
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    faculty: Mapped[User] = relationship(back_populates="sessions", lazy="joined")
    records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["VerificationAttempt"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    # ---- convenience -------------------------------------------------------
    def status(self, now: datetime | None = None) -> str:
        now = now or utcnow()
        if self.is_closed:
            return "closed"
        if now < self.starts_at:
            return "upcoming"
        if now > self.ends_at:
            return "expired"
        return "live"

    def is_open(self, now: datetime | None = None) -> bool:
        return self.status(now) == "live"


class AttendanceRecord(Base):
    """A successfully verified attendance entry."""

    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="uq_session_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("attendance_sessions.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(32), nullable=False)
    student_name: Mapped[str] = mapped_column(String(128), nullable=False)
    marked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    gps_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_m: Mapped[float] = mapped_column(Float)

    device_hash: Mapped[str] = mapped_column(String(64))
    challenge: Mapped[str] = mapped_column(String(32))
    liveness_score: Mapped[float] = mapped_column(Float)
    identity_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_duplicate_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    face_embedding: Mapped[bytes] = mapped_column(LargeBinary)

    session: Mapped[AttendanceSession] = relationship(back_populates="records")
    student: Mapped[User] = relationship(lazy="joined")


class DeviceBinding(Base):
    """Devices a student has used; enforces MAX_DEVICES_PER_STUDENT."""

    __tablename__ = "device_bindings"
    __table_args__ = (UniqueConstraint("user_id", "device_hash", name="uq_user_device"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    device_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    device_label: Mapped[str] = mapped_column(String(256), default="")
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="devices")


class VerificationAttempt(Base):
    """Audit log of every check-in attempt (success or blocked), for evaluation."""

    __tablename__ = "verification_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("attendance_sessions.id"), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(32))
    stage: Mapped[str] = mapped_column(String(32))  # eligibility | location | liveness | face | success
    passed: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str] = mapped_column(Text, default="")
    device_hash: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    session: Mapped[AttendanceSession] = relationship(back_populates="attempts")
