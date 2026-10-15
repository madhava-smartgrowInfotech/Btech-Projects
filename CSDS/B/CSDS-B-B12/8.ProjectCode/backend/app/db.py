from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))  # doctor | technician
    password_hash: Mapped[str] = mapped_column(String(100))


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name_enc: Mapped[str] = mapped_column(Text)  # Fernet-encrypted
    phone_enc: Mapped[str] = mapped_column(Text, default="")
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String(10))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    scans: Mapped[list["Scan"]] = relationship(back_populates="patient", order_by="Scan.created_at.desc()")


class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255))
    modality: Mapped[str] = mapped_column(String(10))  # xray | ct
    modality_score: Mapped[float] = mapped_column(Float)
    prediction: Mapped[str] = mapped_column(String(60))
    confidence: Mapped[float] = mapped_column(Float)
    probabilities: Mapped[dict] = mapped_column(JSON)
    severity: Mapped[str] = mapped_column(String(20))
    affected_pct: Mapped[float] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSON)  # preprocessing stats, image keys
    reports: Mapped[dict] = mapped_column(JSON, default=dict)  # cached AI report text per language
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    patient: Mapped[Patient] = relationship(back_populates="scans")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"))
    role: Mapped[str] = mapped_column(String(10))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(60), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_email: Mapped[str] = mapped_column(String(120), default="")
    action: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def audit(db, user, action, target=""):
    db.add(AuditLog(user_id=user.id if user else None, user_email=user.email if user else "", action=action, target=str(target)))
    db.commit()


def init_db():
    from .auth import hash_password

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.query(User).first():
            db.add_all([
                User(email="doctor@pulmovision.app", name="Demo Doctor", role="doctor", password_hash=hash_password("Doctor@123")),
                User(email="tech@pulmovision.app", name="Demo Technician", role="technician", password_hash=hash_password("Tech@123")),
            ])
            db.commit()


def as_utc(dt):
    """SQLite drops tzinfo; stored values are UTC."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def iso(dt):
    return as_utc(dt).isoformat()
