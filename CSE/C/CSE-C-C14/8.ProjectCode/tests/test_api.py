"""Tests for the JSON API the React frontend uses (/api/auth, /api/config, /api/insights, /api/analyze)."""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app import config, create_app  # noqa: E402


@pytest.fixture()
def client():
    return create_app().test_client()


def _login(client):
    resp = client.post("/api/auth/login", json={"email": config.DEMO_EMAIL, "password": config.DEMO_PASSWORD})
    assert resp.status_code == 200
    return {"Authorization": "Bearer " + resp.get_json()["token"]}


def test_login_rejects_wrong_password(client):
    resp = client.post("/api/auth/login", json={"email": config.DEMO_EMAIL, "password": "nope"})
    assert resp.status_code == 401
    assert "error" in resp.get_json()


def test_login_rejects_missing_body(client):
    assert client.post("/api/auth/login").status_code == 401


def test_demo_login_and_me(client):
    headers = _login(client)
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == config.DEMO_EMAIL
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_config_describes_the_ensemble(client):
    data = client.get("/api/config").get_json()
    assert [b["key"] for b in data["branches"]] == ["a1", "a2", "b", "c"]
    assert data["max_mb"] == config.MAX_UPLOAD_MB
    assert set(data["gates"]) == {"tau_b", "tau_c", "correction"}


def test_insights_shape(client):
    data = client.get("/api/insights").get_json()
    assert "available" in data and "confusion_exists" in data
    if data["available"]:
        assert 0.0 <= data["ensemble"]["accuracy"] <= 1.0


def test_analyze_requires_login(client):
    data = {"image": (io.BytesIO(b"x"), "a.png")}
    resp = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert resp.status_code == 401


def test_analyze_rejects_bad_upload_with_json_error(client):
    headers = _login(client)
    data = {"image": (io.BytesIO(b"not an image"), "bad.txt")}
    resp = client.post("/api/analyze", data=data, headers=headers, content_type="multipart/form-data")
    assert resp.status_code in (400, 503)
    assert "error" in resp.get_json()


def test_oversize_upload_returns_json_on_api_paths(client):
    headers = _login(client)
    big = io.BytesIO(b"\0" * (config.MAX_CONTENT_LENGTH + 1024))
    resp = client.post("/api/analyze", data={"image": (big, "big.png")}, headers=headers, content_type="multipart/form-data")
    assert resp.status_code == 413
    assert "MB" in resp.get_json()["error"]
