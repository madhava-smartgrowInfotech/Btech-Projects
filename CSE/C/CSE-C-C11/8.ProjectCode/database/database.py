"""
Database engine + session management for FINJARVIS.

Uses a local SQLite file. Call init_db() once at app startup to create all
tables if they don't already exist (idempotent, safe to call every run).
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from database.models import Base

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "finjarvis.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for Streamlit's threading model
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables if they do not already exist. Safe to call repeatedly."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """Context-managed session: commits on success, rolls back on error, always closes."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
