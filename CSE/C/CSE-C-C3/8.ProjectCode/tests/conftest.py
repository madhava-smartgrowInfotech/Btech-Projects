"""Shared pytest fixtures: every test run gets its own throw-away SQLite database."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_tmp = tempfile.mkdtemp(prefix="parksure_tests_")
os.environ["PARKSURE_DB"] = "sqlite:///" + (Path(_tmp) / "tests.db").as_posix()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    """Engine unit tests run against their own in-memory database, separate from the API tests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base
    from app import models  # noqa: F401  (registers the tables)
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=eng)
    s = sessionmaker(bind=eng, autoflush=False, autocommit=False)()
    try:
        yield s
    finally:
        s.close()
        eng.dispose()
