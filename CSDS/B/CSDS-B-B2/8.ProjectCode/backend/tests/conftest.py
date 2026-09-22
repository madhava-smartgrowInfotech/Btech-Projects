"""Test setup: a throw-away SQLite database per test session, never the real data/app.db."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="signalscout-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40
os.environ["SEED_DEMO_USERS"] = "true"
os.environ["SEED_SAMPLE_DATA"] = "false"
os.environ["ESP32_SIMULATOR"] = "false"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import DEMO_PASSWORD  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:   # runs the lifespan: tables + demo accounts
        yield c


def _login(client: TestClient, email: str) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def user_headers(client):
    return _login(client, "user@signalscout.demo")


@pytest.fixture(scope="session")
def engineer_headers(client):
    return _login(client, "engineer@signalscout.demo")


@pytest.fixture(scope="session")
def admin_headers(client):
    return _login(client, "admin@signalscout.demo")
