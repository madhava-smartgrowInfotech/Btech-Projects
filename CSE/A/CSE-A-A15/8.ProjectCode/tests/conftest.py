"""Shared fixtures: backend on sys.path, a scratch database and scratch output folder per test session."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cv")
    os.environ["DATABASE_URL"] = "sqlite:///" + (tmp / "test.db").as_posix()
    from fastapi.testclient import TestClient
    from app.routes import analysis, ops
    from app import main
    out = tmp / "outputs"
    out.mkdir()
    ops.OUTPUTS_DIR = out          # keep test artefacts out of data/outputs
    analysis.OUTPUTS_DIR = out
    with TestClient(main.app) as c:
        r = c.post("/api/auth/login", json={"username": "demo", "password": "Demo@12345"})
        c.headers["Authorization"] = "Bearer " + r.json()["token"]
        yield c


@pytest.fixture(scope="session")
def keypair():
    from app.services import crypto
    return crypto.generate_keypair(2048)


@pytest.fixture(scope="session")
def cover():
    from app.services import lsb
    return lsb.load_rgb(str(ROOT / "data" / "covers" / "coffee_600x400.png"))
