"""API tests through FastAPI's TestClient (the real app and the real engine, no mocks)."""
import time

import pytest
from fastapi.testclient import TestClient

from backend import auth, config
from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        for _ in range(90):  # the predictor trains in a background thread on first start
            if c.get("/api/health").json()["predictor_ready"]:
                break
            time.sleep(1)
        yield c


@pytest.fixture(scope="module")
def hdr(client):
    demo = client.get("/api/auth/demo").json()
    tok = client.post("/api/auth/login", json=demo).json()["token"]
    return {"Authorization": "Bearer " + tok}


def test_health_is_public(client):
    d = client.get("/api/health").json()
    assert d["ok"] and d["predictor_ready"]


def test_protected_routes_reject_anonymous(client):
    for path in ("/api/live", "/api/meta", "/api/prediction", "/api/violations"):
        assert client.get(path).status_code == 401


def test_bad_login_gives_message(client):
    r = client.post("/api/auth/login", json={"email": "x@y.io", "password": "nope"})
    assert r.status_code == 401 and r.json()["detail"]["message"]


def test_login_validation_error_is_readable(client):
    r = client.post("/api/auth/login", json={"email": "a"})
    assert r.status_code == 422 and "Invalid input" in r.json()["detail"]["message"]


def test_token_roundtrip_tamper_and_expiry(monkeypatch):
    t = auth.make_token("a@b.co", "A")
    assert auth.read_token(t)["sub"] == "a@b.co"
    assert auth.read_token(t[:-3] + "xyz") is None
    monkeypatch.setattr(config, "TOKEN_HOURS", -1)
    assert auth.read_token(auth.make_token("a@b.co", "A")) is None


def test_meta_lists_four_controllers(client, hdr):
    assert len(client.get("/api/meta", headers=hdr).json()["controllers"]) == 4


def test_live_reset_step_and_config(client, hdr):
    assert client.post("/api/live/reset", headers=hdr).json()["t"] == 0
    d = client.put("/api/live/config", headers=hdr, json={"controller": "advanced", "demand": 1.4}).json()
    assert d["config"]["demand"] == 1.4
    d = client.post("/api/live/step", headers=hdr, json={"seconds": 120}).json()
    assert d["t"] == 120 and len(d["junctions"]) == 4 and len(d["map"]["signals"]) == 16


def test_step_range_and_unknown_controller_rejected(client, hdr):
    assert client.post("/api/live/step", headers=hdr, json={"seconds": 5000}).status_code == 422
    assert client.put("/api/live/config", headers=hdr, json={"controller": "magic"}).status_code == 422
    assert client.put("/api/live/config", headers=hdr, json={"demand": 9}).status_code == 422


def test_ambulance_raises_banner_and_fixed_ignores_it(client, hdr):
    client.put("/api/live/config", headers=hdr, json={"controller": "advanced"})
    d = client.post("/api/live/ambulance", headers=hdr).json()
    assert d["kpis"]["emg_active"] >= 1 and d["banner"]["kind"] == "preempt"
    d = client.put("/api/live/config", headers=hdr, json={"controller": "fixed"}).json()
    assert d["banner"]["kind"] == "ignored"


def test_grid_switch_restarts_sim(client, hdr):
    d = client.put("/api/live/config", headers=hdr, json={"grid": "3x3"}).json()
    assert d["t"] == 0 and len(d["junctions"]) == 9
    client.put("/api/live/config", headers=hdr, json={"grid": "2x2"})


def test_benchmark_and_range_check(client, hdr):
    r = client.post("/api/benchmark", headers=hdr, json={"grid": "2x2", "seconds": 600, "demand": 1.2, "seeds": 2, "start_hour": 8, "use_ml": True})
    d = r.json()
    assert r.status_code == 200 and len(d["table"]) == 4 and d["kpis"]["d_fixed"] > 0
    bad = client.post("/api/benchmark", headers=hdr, json={"seconds": 10})
    assert bad.status_code == 422 and bad.json()["detail"]["hint"]


def test_prediction_endpoint(client, hdr):
    d = client.get("/api/prediction", headers=hdr).json()
    assert d["kpis"]["vs_persistence"] > 0 and len(d["scatter"]) > 100 and len(d["metrics"]) == 3


def test_vision_synthetic_and_upload_errors(client, hdr):
    d = client.get("/api/vision/synthetic?vehicles=9&ambulance=true", headers=hdr).json()
    assert d["report"]["emergency"] and d["annotated"].startswith("data:image/jpeg")
    r = client.post("/api/vision/analyze", headers=hdr, files={"file": ("x.png", b"not an image", "image/png")}, data={"conf": "0.3"})
    assert r.status_code in (415, 503) and r.json()["detail"]["message"]


def test_violations_after_traffic(client, hdr):
    client.put("/api/live/config", headers=hdr, json={"controller": "fixed", "demand": 1.6})
    client.post("/api/live/step", headers=hdr, json={"seconds": 900})
    d = client.get("/api/violations", headers=hdr).json()
    assert d["empty"] or (d["log"][0]["plate"] and d["kpis"]["total"] > 0)
