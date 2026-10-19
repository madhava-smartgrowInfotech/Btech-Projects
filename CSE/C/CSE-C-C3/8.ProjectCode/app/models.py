"""ParkSure relational schema."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import (Column, Integer, String, Float, DateTime, ForeignKey, Text)
from sqlalchemy.orm import relationship
from .database import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="driver")  # driver | admin
    trust_score = Column(Float, nullable=False, default=3.0)
    benefit_streak = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    account_credit = Column(Float, nullable=False, default=0.0)
    suspended_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    reservations = relationship("Reservation", back_populates="user", cascade="all, delete-orphan")
    trust_events = relationship("TrustEvent", back_populates="user", cascade="all, delete-orphan")


class ParkingLocation(Base):
    __tablename__ = "parking_locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False)
    address = Column(String(255), nullable=False, default="")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)          # total slots
    buffer_size = Column(Integer, nullable=False, default=1)  # hold-back buffer (dynamic)
    price_per_hour = Column(Float, nullable=False, default=3.0)
    last_buffer_reset = Column(DateTime(timezone=True), default=_now)
    created_at = Column(DateTime(timezone=True), default=_now)

    reservations = relationship("Reservation", back_populates="location", cascade="all, delete-orphan")


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("parking_locations.id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="reserved")
    # reserved | active (checked in) | completed | cancelled | failed | declined
    fee = Column(Float, nullable=False, default=0.0)
    fee_multiplier = Column(Float, nullable=False, default=1.0)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    decline_reason = Column(Text, nullable=True, default="")
    parent_id = Column(Integer, nullable=True)  # set when auto-created as alternate
    created_at = Column(DateTime(timezone=True), default=_now)

    user = relationship("User", back_populates="reservations")
    location = relationship("ParkingLocation", back_populates="reservations")
    payment = relationship("Payment", back_populates="reservation", uselist=False, cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="usd")
    provider = Column(String(20), nullable=False, default="demo")  # stripe | demo
    stripe_session_id = Column(String(200), nullable=True)
    stripe_payment_intent = Column(String(200), nullable=True)
    status = Column(String(30), nullable=False, default="pending")  # pending|paid|refunded|failed
    created_at = Column(DateTime(timezone=True), default=_now)

    reservation = relationship("Reservation", back_populates="payment")


class TrustEvent(Base):
    __tablename__ = "trust_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String(20), nullable=False)  # benefit | warning | reward | penalty
    detail = Column(String(255), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), default=_now)

    user = relationship("User", back_populates="trust_events")
