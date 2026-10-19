"""
Shared fixtures. Every test runs against a throw-away SQLite file and throw-away
upload / heatmap folders, so the real history is never touched.
"""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SAMPLES = os.path.join(ROOT, "dataset_sample")
SAMPLE_FILES = {
    "normal": os.path.join(SAMPLES, "normal_pa.jpg"),
    "bacterial": os.path.join(SAMPLES, "lobar_pneumonia.jpg"),
    "viral": os.path.join(SAMPLES, "influenza_pa.jpg"),
}


@pytest.fixture(scope="session")
def flask_module():
    import app as flask_app

    flask_app.get_model()  # loads the trained model, or the demo network when no weights exist
    return flask_app


@pytest.fixture()
def sandbox(tmp_path, monkeypatch, flask_module):
    """Redirect the database and image folders into tmp_path."""
    from database import db

    uploads = tmp_path / "uploads"
    heatmaps = tmp_path / "heatmaps"
    uploads.mkdir()
    heatmaps.mkdir()
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(flask_module, "UPLOAD_FOLDER", str(uploads))
    monkeypatch.setattr(flask_module, "HEATMAP_FOLDER", str(heatmaps))
    db.init_db()
    return tmp_path


@pytest.fixture()
def client(sandbox):
    from fastapi.testclient import TestClient

    from backend.main import api

    return TestClient(api)


@pytest.fixture()
def authed(client):
    r = client.post("/api/auth/login", json={"email": "demo@pneumodetect.ai", "password": "Pneumo@123"})
    assert r.status_code == 200
    return client


@pytest.fixture()
def sample_bytes():
    def read(kind="normal"):
        with open(SAMPLE_FILES[kind], "rb") as f:
            return f.read()

    return read
