"""Test setup: a throwaway database with the sample data, no network, real trained models."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="upg-tests-"))
os.environ["DATABASE_PATH"] = str(_TMP / "test.db")
os.environ["VOICE_CACHE_DIR"] = str(_TMP / "voice")
os.environ["TTS_ENABLED"] = "false"
os.environ["SEED_SAMPLE_DATA"] = "true"
os.environ.setdefault("JWT_SECRET", "test-secret-for-the-pytest-suite-only-0123456789")
os.environ["LOG_LEVEL"] = "WARNING"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

DEMO = ("demo@upiguardian.app", "Guardian@123")
FAMILY = ("family@upiguardian.app", "Guardian@123")
ADMIN = ("admin@upiguardian.app", "Admin@1234")
PIN = "1234"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _login(client: TestClient, creds: tuple[str, str]) -> dict:
    r = client.post("/api/auth/login", json={"identifier": creds[0], "password": creds[1]})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def demo(client):
    return _login(client, DEMO)


@pytest.fixture(scope="session")
def family(client):
    return _login(client, FAMILY)


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, ADMIN)


@pytest.fixture
def clock(client, demo):
    """Sets the demo user's sandbox clock for one test and restores the real clock afterwards."""

    def set_clock(value: str | None):
        r = client.put("/api/settings", json={"sandbox_clock": value or ""}, headers=demo)
        assert r.status_code == 200, r.text

    yield set_clock
    set_clock(None)
