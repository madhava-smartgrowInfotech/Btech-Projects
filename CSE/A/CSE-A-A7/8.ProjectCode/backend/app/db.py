import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
if _url.startswith("sqlite:///./"):
    _url = "sqlite:///" + str(ROOT / _url[len("sqlite:///./"):]).replace("\\", "/")
(ROOT / "data").mkdir(exist_ok=True)
engine = create_engine(_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default="clinician")


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), default="Unnamed patient")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="live")  # live | sample
    vitals: Mapped[dict] = mapped_column(JSON)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fused: Mapped[dict] = mapped_column(JSON)
    model_priority: Mapped[int] = mapped_column(Integer)
    priority: Mapped[int] = mapped_column(Integer, index=True)  # current (after any override)
    risk_level: Mapped[str] = mapped_column(String(12))
    confidence: Mapped[float] = mapped_column(Float)
    probabilities: Mapped[dict] = mapped_column(JSON)
    shap: Mapped[list] = mapped_column(JSON)
    ocr_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    model_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    total_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_outcome: Mapped[int | None] = mapped_column(Integer, nullable=True)  # known clinician priority (sample cases)
    overrides: Mapped[list["Override"]] = relationship(back_populates="patient", order_by="Override.id")


class Override(Base):
    __tablename__ = "overrides"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_name: Mapped[str] = mapped_column(String(80), default="")
    old_priority: Mapped[int] = mapped_column(Integer)
    new_priority: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(10))  # accept | change
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    patient: Mapped[Patient] = relationship(back_populates="overrides")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
