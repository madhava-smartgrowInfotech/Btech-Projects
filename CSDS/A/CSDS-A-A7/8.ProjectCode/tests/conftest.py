"""Test fixtures: a throw-away SQLite database and evidence folder, with every outside service
(OSRM, Gemini, Telegram, Gmail) replaced by a stub so the suite is offline and repeatable."""
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_TMP = Path(tempfile.mkdtemp(prefix="sheguard_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"

from fastapi.testclient import TestClient  # noqa: E402

from backend.app import config  # noqa: E402

config.EVIDENCE_DIR = _TMP / "evidence"
config.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
config.DATA_DIR = _TMP  # evidence paths are stored relative to DATA_DIR
shutil.copy(ROOT / "data" / "district_risk.csv", _TMP / "district_risk.csv")  # the app seeds its table from here

from backend.app.main import app  # noqa: E402
from backend.app.routes import ai as ai_routes  # noqa: E402
from backend.app.services import email as email_service  # noqa: E402
from backend.app.services import osrm, telegram  # noqa: E402

SENT = {"telegram": [], "email": []}


@pytest.fixture(scope="session")
def tmp_root():
    return _TMP


@pytest.fixture(autouse=True)
def stub_outside_world(monkeypatch):
    async def fake_routes(a, b, c, d):
        return [
            {"distance_m": 10000, "duration_s": 900, "coordinates": [[17.0 + i * 0.01, 78.0] for i in range(60)]},
            {"distance_m": 11000, "duration_s": 960, "coordinates": [[28.6 + i * 0.01, 77.2] for i in range(60)]},
        ]

    async def fake_ask(question, lat=None, lng=None):
        return f"Stub answer for: {question}"

    async def fake_tg(chat_id, text):
        SENT["telegram"].append((chat_id, text))
        return True

    def fake_mail(to, subject, body):
        SENT["email"].append((to, subject, body))
        return True

    monkeypatch.setattr(osrm, "get_route_alternatives", fake_routes)
    monkeypatch.setattr(ai_routes, "ask_gemini", fake_ask)
    monkeypatch.setattr(telegram, "send_telegram_message", fake_tg)
    monkeypatch.setattr(email_service, "send_email", fake_mail)
    SENT["telegram"].clear()
    SENT["email"].clear()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _register(client, tag="u"):
    email = f"{tag}_{uuid.uuid4().hex[:8]}@test.app"
    r = client.post("/api/auth/register", json={"name": f"User {tag}", "email": email, "password": "Passw0rd!"})
    assert r.status_code == 200, r.text
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def user_a(client):
    return _register(client, "a")


@pytest.fixture()
def user_b(client):
    return _register(client, "b")


@pytest.fixture()
def sos(client, user_a):
    _, h = user_a
    r = client.post("/api/sos/start", json={"lat": 17.385, "lng": 78.4867, "trigger": "manual"}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()
