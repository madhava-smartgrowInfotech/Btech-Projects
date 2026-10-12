import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    pw_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class KeyPair(Base):
    __tablename__ = "keypairs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(60))
    bits: Mapped[int] = mapped_column(Integer)
    fingerprint: Mapped[str] = mapped_column(String(40))
    public_pem: Mapped[str] = mapped_column(Text)
    private_pem: Mapped[str | None] = mapped_column(Text, nullable=True)  # None = recipient public key only
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class OpLog(Base):
    __tablename__ = "oplog"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    op: Mapped[str] = mapped_column(String(30))
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    def data(self) -> dict:
        return json.loads(self.details)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_op(db, user_id: int, op: str, ok: bool, details: dict) -> OpLog:
    """Record an operation. Callers must never pass keys, passwords or file contents."""
    row = OpLog(user_id=user_id, op=op, ok=ok, details=json.dumps(details))
    db.add(row)
    db.commit()
    return row
