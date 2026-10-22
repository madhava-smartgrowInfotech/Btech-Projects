"""Shared pytest fixtures: isolated SQLite DB + temp storage + TestClient."""

import base64
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
_db_path = Path(_tmp.name) / "test.db"
_storage = Path(_tmp.name) / "enc"
_storage.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["STORAGE_DIR"] = str(_storage)
os.environ["JWT_SECRET"] = "test-secret-for-automated-tests-only"

from backend.app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from fastapi.testclient import TestClient  # noqa: E402
from backend.app.db.database import init_db  # noqa: E402
from backend.app.main import app  # noqa: E402

init_db()


@pytest.fixture()
def client():
    return TestClient(app)


def _register(client, name, email_prefix, password, idx="k"):
    # Unique email per registration so tests stay isolated on a shared test DB.
    email = f"{email_prefix}-{uuid.uuid4().hex[:8]}@example.com"
    pub = base64.b64encode(b"public-" + idx.encode()).decode()
    bundle = '{"salt":"%s","iv":"%s","data":"%s"}' % (
        base64.b64encode(b"salt-" + idx.encode()).decode(),
        base64.b64encode(b"iv1234567890").decode(),
        base64.b64encode(b"encpriv-" + idx.encode()).decode(),
    )
    r = client.post("/api/auth/register", json={
        "name": name, "email": email, "password": password,
        "public_key": pub, "encrypted_private_key": bundle,
        "private_key_salt": base64.b64encode(b"salt-" + idx.encode()).decode(),
    })
    assert r.status_code == 201, r.text
    r2 = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200, r2.text
    user = r.json()
    user["_password"] = password  # handy for re-login in tests
    return user, r2.json()["access_token"]


@pytest.fixture()
def owner(client):
    return _register(client, "Olivia Owner", "olivia.owner", "OwnerPass123", "o1")


@pytest.fixture()
def editor_user(client):
    return _register(client, "Eddie Editor", "eddie.editor", "EditorPass123", "e1")


@pytest.fixture()
def viewer_user(client):
    return _register(client, "Vera Viewer", "vera.viewer", "ViewerPass123", "v1")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def login_as(client, user):
    r = client.post("/api/auth/login", json={"email": user["email"], "password": user["_password"]})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def upload_ciphertext(client, token, filename="note.txt", size=11, sha="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"):
    import io
    ct = b"X" * 32  # fake ciphertext bytes for API-level tests
    r = client.post(
        "/api/files/upload",
        headers=auth(token),
        files={"ciphertext": ("ciphertext.bin", io.BytesIO(ct), "application/octet-stream")},
        data={"original_filename": filename, "mime_type": "text/plain",
              "original_size": str(size), "iv": base64.b64encode(b"012345678901").decode(),
              "wrapped_fek": base64.b64encode(b"W" * 256).decode(), "plaintext_sha256": sha},
    )
    assert r.status_code == 201, r.text
    return r.json()
