import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
STORE_DIR = DATA_DIR / "store"
SAMPLE_DIR = DATA_DIR / "sample"
STORE_DIR.mkdir(parents=True, exist_ok=True)

_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
if _url.startswith("sqlite:///./"):
    _url = "sqlite:///" + str(ROOT / _url[len("sqlite:///./"):]).replace("\\", "/")
engine = create_engine(_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Job(Base):
    """One encrypted image. The key itself is never stored - only its fingerprint."""
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(40))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    channels: Mapped[int] = mapped_column(Integer)
    nonce: Mapped[str] = mapped_column(String(32))
    key_fp: Mapped[str] = mapped_column(String(12))
    plain_sha256: Mapped[str] = mapped_column(String(64))
    cipher_sha256: Mapped[str] = mapped_column(String(64))
    enc_ms: Mapped[float] = mapped_column(Float)
    plain_path: Mapped[str] = mapped_column(String(300))
    cipher_path: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    image_name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), default="security")
    data_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    @property
    def data(self):
        return json.loads(self.data_json)


class BenchRun(Base):
    __tablename__ = "bench_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    data_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


def init_db():
    DATA_DIR.mkdir(exist_ok=True)
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
