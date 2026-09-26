"""Test setup: a throw-away database and a signed-in client per role."""
from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="seatwise-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))
os.environ["SEED_DEMO_USERS"] = "true"
os.environ["LOOKUP_RATE_LIMIT_PER_MINUTE"] = "1000"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = get_settings().demo_password


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _token(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin_headers(client: TestClient) -> dict[str, str]:
    return _token(client, get_settings().demo_admin_email)


@pytest.fixture(scope="session")
def invigilator_headers(client: TestClient) -> dict[str, str]:
    return _token(client, get_settings().demo_invigilator_email)
