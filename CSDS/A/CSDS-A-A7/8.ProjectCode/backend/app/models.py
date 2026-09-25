import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from .db import Base


def now_utc():
    return datetime.now(timezone.utc)


def gen_token():
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=now_utc)

    guardians = relationship("Guardian", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("EmergencySession", back_populates="user", cascade="all, delete-orphan")


class Guardian(Base):
    __tablename__ = "guardians"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=now_utc)

    owner = relationship("User", back_populates="guardians")


class EmergencySession(Base):
    __tablename__ = "emergency_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_token = Column(String, unique=True, default=gen_token, index=True)
    status = Column(String, default="active")  # active | cancelled
    trigger = Column(String, default="manual")  # manual | safephrase
    started_at = Column(DateTime, default=now_utc)
    ended_at = Column(DateTime, nullable=True)
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)
    last_update_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    pings = relationship("LocationPing", back_populates="session", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="session", cascade="all, delete-orphan")


class LocationPing(Base):
    __tablename__ = "location_pings"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("emergency_sessions.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    ts = Column(DateTime, default=now_utc)

    session = relationship("EmergencySession", back_populates="pings")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("emergency_sessions.id"), nullable=False)
    kind = Column(String, nullable=False)  # photo | audio
    file_path = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    captured_at = Column(DateTime, default=now_utc)

    session = relationship("EmergencySession", back_populates="evidence")


class DistrictRisk(Base):
    __tablename__ = "district_risk"

    id = Column(Integer, primary_key=True)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    crime_rate = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_tier = Column(String, nullable=False)  # low | medium | high
