"""Platform database (SQLite, created on first run)."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DATA_DIR

DATA_DIR.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{DATA_DIR / 'app.db'}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(16))  # patient | doctor | staff | admin
    display_name: Mapped[str] = mapped_column(String(128))
    hospital_key: Mapped[str | None] = mapped_column(String(4), nullable=True)  # doctor/staff employer, patient registration
    local_patient_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # patient's record at hospital_key


class Person(Base):
    """Master Patient Index golden record: one real person."""
    __tablename__ = "persons"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128))
    birth_date: Mapped[str] = mapped_column(String(10))
    gender: Mapped[str] = mapped_column(String(10))


class MpiLink(Base):
    __tablename__ = "mpi_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[str] = mapped_column(ForeignKey("persons.id"), index=True)
    hospital_key: Mapped[str] = mapped_column(String(4))
    local_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(128))
    birth_date: Mapped[str] = mapped_column(String(10))
    gender: Mapped[str] = mapped_column(String(10))
    phone: Mapped[str] = mapped_column(String(32))
    score: Mapped[float] = mapped_column(Float)


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    person_id: Mapped[str] = mapped_column(String(20), index=True)
    grantee_hospital: Mapped[str] = mapped_column(String(4))
    categories: Mapped[str] = mapped_column(Text)  # JSON list
    status: Mapped[str] = mapped_column(String(12))  # active | inactive
    expires: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fhir_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow)
    updated_at: Mapped[str] = mapped_column(String(32), default=utcnow)


class AccessRequest(Base):
    __tablename__ = "access_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[str] = mapped_column(String(20), index=True)
    doctor_username: Mapped[str] = mapped_column(String(64))
    doctor_name: Mapped[str] = mapped_column(String(128))
    hospital_key: Mapped[str] = mapped_column(String(4))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12))  # granted | blocked
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow)


class LedgerEntry(Base):
    """Hash-chained, tamper-evident audit and consent log."""
    __tablename__ = "ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(48))
    person_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    detail: Mapped[str] = mapped_column(Text)  # canonical JSON
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64))


class SyncedSummary(Base):
    __tablename__ = "synced_summaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    hospital_key: Mapped[str] = mapped_column(String(4))
    local_id: Mapped[str] = mapped_column(String(32))
    bundle_json: Mapped[str] = mapped_column(Text)
    entries: Mapped[int] = mapped_column(Integer)
    received_at: Mapped[str] = mapped_column(String(32), default=utcnow)


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[str] = mapped_column(String(20), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # medication | follow-up | custom
    text: Mapped[str] = mapped_column(Text)
    due: Mapped[str] = mapped_column(String(10))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    source_key: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
