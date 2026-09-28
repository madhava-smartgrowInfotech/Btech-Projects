"""SQLite database (SQLAlchemy 2). Created and seeded on first run."""
import json
from datetime import datetime

import bcrypt
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import DATABASE_URL, DATA_DIR, MODELS_DIR, SHIFTS

DATA_DIR.mkdir(exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # admin | doctor
    password_hash: Mapped[str] = mapped_column(String)


class Admission(Base):
    __tablename__ = "admissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    admit_date: Mapped[str] = mapped_column(String)
    patient_ref: Mapped[str] = mapped_column(String)
    facility: Mapped[str] = mapped_column(String)
    ward: Mapped[str] = mapped_column(String)
    features: Mapped[dict] = mapped_column(JSON)
    predicted_days: Mapped[float] = mapped_column(Float)
    long_stay: Mapped[bool] = mapped_column(Boolean)
    long_stay_probability: Mapped[float] = mapped_column(Float)
    prediction: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[str] = mapped_column(String)


class WardCapacity(Base):
    __tablename__ = "ward_capacity"
    facility: Mapped[str] = mapped_column(String, primary_key=True)
    ward: Mapped[str] = mapped_column(String, primary_key=True)
    beds: Mapped[int] = mapped_column(Integer)


class NurseRoster(Base):
    __tablename__ = "nurse_roster"
    facility: Mapped[str] = mapped_column(String, primary_key=True)
    ward: Mapped[str] = mapped_column(String, primary_key=True)
    shift: Mapped[str] = mapped_column(String, primary_key=True)
    nurses: Mapped[int] = mapped_column(Integer)


class EquipmentInventory(Base):
    __tablename__ = "equipment_inventory"
    facility: Mapped[str] = mapped_column(String, primary_key=True)
    item: Mapped[str] = mapped_column(String, primary_key=True)
    units: Mapped[int] = mapped_column(Integer)


class AllocationPlan(Base):
    __tablename__ = "allocation_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String)
    horizon_days: Mapped[int] = mapped_column(Integer)
    planning_level: Mapped[str] = mapped_column(String)
    demand: Mapped[dict] = mapped_column(JSON)
    actions: Mapped[list] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="proposed")  # proposed | accepted
    modified: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted_by: Mapped[str | None] = mapped_column(String, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DEMO_USERS = [
    ("admin@hospisense.app", "Operations Admin", "admin", "Admin@123"),
    ("doctor@hospisense.app", "Ward Doctor", "doctor", "Doctor@123"),
]


def init_db():
    Base.metadata.create_all(engine)
    cfg = json.loads((MODELS_DIR / "hospital_config.json").read_text())
    with Session(engine) as db:
        if not db.scalar(select(User).limit(1)):
            for email, name, role, pw in DEMO_USERS:
                db.add(User(email=email, name=name, role=role,
                            password_hash=bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()))
        if not db.scalar(select(WardCapacity).limit(1)):
            for f, wards in cfg["capacity"].items():
                for w, beds in wards.items():
                    db.add(WardCapacity(facility=f, ward=w, beds=beds))
            for f, wards in cfg["roster"].items():
                for w, shifts in wards.items():
                    for s in SHIFTS:
                        db.add(NurseRoster(facility=f, ward=w, shift=s, nurses=shifts[s]))
            for f, items in cfg["inventory"].items():
                for item, units in items.items():
                    db.add(EquipmentInventory(facility=f, item=item, units=units))
        db.commit()
