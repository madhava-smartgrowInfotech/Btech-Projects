"""Shared pytest fixtures. Redirects the app's DB engine to a temp SQLite
file per test session so tests never touch a real finjarvis.db."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.database as db_module
from database.models import Base


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Point the app at a fresh temp SQLite DB for every test function."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)

    yield

    os.remove(path)
