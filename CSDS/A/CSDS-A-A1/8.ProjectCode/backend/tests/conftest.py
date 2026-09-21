"""Test setup: an isolated data folder, a test Gemini configuration and shared fixtures.

Settings are read once at import time, so the environment is prepared here before the
application package is imported. The local models are the real ones from models/hf.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEST_DATA = Path(tempfile.mkdtemp(prefix="policylens-test-"))
os.environ["DATA_DIR"] = str(TEST_DATA)
os.environ["GEMINI_API_KEY"] = ""  # tests never call the real API; AI steps are replaced where needed
os.environ["JWT_SECRET"] = "test-secret-for-policylens-unit-tests-only"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["DEMO_EMAIL"] = "demo@policylens.app"
os.environ["DEMO_PASSWORD"] = "Demo@12345"
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import make_policy_pdf  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _cleanup():
    yield
    shutil.rmtree(TEST_DATA, ignore_errors=True)


@pytest.fixture(scope="session")
def policy_pdf(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("pdf") / "sample-policy-wording.pdf"
    make_policy_pdf(path)
    return path


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    import uuid

    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/register", json={"full_name": "Test User", "email": email, "password": "Secret123"})
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
