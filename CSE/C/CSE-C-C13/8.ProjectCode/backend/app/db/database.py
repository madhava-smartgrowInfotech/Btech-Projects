"""SQLAlchemy engine/session/Base. Works with SQLite (local default) and PostgreSQL."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.core.config import get_settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def _build_engine():
    global _engine, _SessionLocal
    if _engine is not None:
        return _engine
    settings = get_settings()
    url = settings.DATABASE_URL
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        # Ensure parent directory of sqlite file exists
        path_part = url.split("sqlite:///", 1)[-1].split("?")[0]
        if path_part and path_part != ":memory:":
            parent = Path(path_part).parent
            if str(parent) not in ("", "."):
                parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_engine():
    if _engine is None:
        _build_engine()
    return _engine


def get_session_factory():
    if _SessionLocal is None:
        _build_engine()
    return _SessionLocal


def get_db():
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend.app.db import models  # noqa: F401  (register models)

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
