from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import DATA_DIR, DATABASE_URL

DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))  # clinician | technician
    password_hash: Mapped[str] = mapped_column(String(100))


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    screenings: Mapped[list["Screening"]] = relationship(back_populates="patient", order_by="Screening.id.desc()")


class Screening(Base):
    __tablename__ = "screenings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    eye: Mapped[str] = mapped_column(String(10), default="")
    image_name: Mapped[str] = mapped_column(String(200), default="")
    quality: Mapped[dict] = mapped_column(JSON, default=dict)
    retina_prob: Mapped[float | None] = mapped_column(Float, nullable=True)
    retina_findings: Mapped[dict] = mapped_column(JSON, default=dict)
    clinical: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    heart_prob: Mapped[float | None] = mapped_column(Float, nullable=True)
    heart_factors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    stage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    patient: Mapped[Patient] = relationship(back_populates="screenings")
    user: Mapped[User] = relationship()


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
