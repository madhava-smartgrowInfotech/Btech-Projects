"""Test fixtures: a throw-away SQLite database, the seeded demo accounts and a synthetic crop photo."""
from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

import pytest

_tmp = tempfile.mkdtemp(prefix="cropsight_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp, 'test.db').as_posix()}"

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

PASSWORD = "cropsight123"


@pytest.fixture(scope="session")
def client():
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    import seed_db

    seed_db.seed()
    with TestClient(app) as c:
        yield c


def _login(client, email):
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def farmer(client):
    return _login(client, "farmer@cropsight.dev")


@pytest.fixture(scope="session")
def buyer(client):
    return _login(client, "buyer1@cropsight.dev")


@pytest.fixture(scope="session")
def distributor(client):
    return _login(client, "distributor@cropsight.dev")


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, "admin@cropsight.dev")


def make_photo(kind="good", size=(480, 360)) -> bytes:
    """A synthetic 'crop on a white table' photo: a green-red ellipse, optionally with dark blemishes."""
    img = Image.new("RGB", size, (250, 250, 250))
    d = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2
    d.ellipse([cx - 150, cy - 110, cx + 150, cy + 110], fill=(190, 40, 35) if kind == "good" else (120, 90, 60))
    if kind == "bad":
        import random

        rnd = random.Random(1)
        for _ in range(60):
            x, y = rnd.randint(cx - 120, cx + 120), rnd.randint(cy - 80, cy + 80)
            r = rnd.randint(4, 14)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(30, 20, 15))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture(scope="session")
def good_photo():
    return make_photo("good")


@pytest.fixture(scope="session")
def bad_photo():
    return make_photo("bad")
