"""Integration tests for the FastAPI layer (auth, validation, prediction, history, files)."""

import io
import os

import numpy as np
import pytest


def _upload(client, data, name="scan.jpg", ctype="image/jpeg"):
    return client.post("/api/predict", files={"xray_image": (name, io.BytesIO(data), ctype)})


# ---------------------------------------------------------------- health / auth
def test_health_is_public_and_reports_classes(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["classes"] == ["Normal", "Bacterial Pneumonia", "Viral Pneumonia"]
    assert body["max_upload_mb"] == 8
    assert body["allowed_types"] == ["jpeg", "jpg", "png"]


def test_me_is_null_when_signed_out(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 200 and r.json() is None


def test_login_rejects_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "demo@pneumodetect.ai", "password": "nope"})
    assert r.status_code == 401


def test_login_rejects_wrong_email(client):
    r = client.post("/api/auth/login", json={"email": "someone@else.com", "password": "Pneumo@123"})
    assert r.status_code == 401


def test_login_sets_httponly_cookie(client):
    r = client.post("/api/auth/login", json={"email": " DEMO@pneumodetect.ai ", "password": "Pneumo@123"})
    assert r.status_code == 200
    assert "httponly" in r.headers["set-cookie"].lower()
    assert client.get("/api/auth/me").json()["email"] == "demo@pneumodetect.ai"


def test_logout_clears_session(authed):
    assert authed.post("/api/auth/logout").status_code == 200
    assert authed.get("/api/auth/me").json() is None


@pytest.mark.parametrize("method,path", [
    ("get", "/api/predictions"), ("get", "/api/predictions/1"), ("delete", "/api/predictions/1"),
    ("get", "/api/stats"), ("get", "/api/files/uploads/x.jpg"), ("post", "/api/predict"),
])
def test_protected_routes_need_a_session(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_forged_cookie_is_rejected(client):
    client.cookies.set("pneumo_session", "abc.def")
    assert client.get("/api/predictions").status_code == 401


# ------------------------------------------------------------------ validation
def test_predict_without_file_is_400(authed):
    assert authed.post("/api/predict").status_code == 400


def test_predict_rejects_unsupported_extension(authed, sample_bytes):
    r = _upload(authed, sample_bytes("normal"), name="scan.gif", ctype="image/gif")
    assert r.status_code == 400 and "Unsupported" in r.json()["detail"]


def test_predict_rejects_file_without_extension(authed, sample_bytes):
    assert _upload(authed, sample_bytes("normal"), name="scan").status_code == 400


def test_predict_rejects_corrupt_image_and_cleans_up(authed, sandbox):
    r = _upload(authed, b"definitely not a jpeg")
    assert r.status_code == 400 and "could not be read" in r.json()["detail"]
    assert os.listdir(sandbox / "uploads") == []


def test_predict_rejects_oversize_upload(authed):
    r = _upload(authed, b"0" * (8 * 1024 * 1024 + 10))
    assert r.status_code == 413


# ------------------------------------------------------------------ prediction
@pytest.mark.parametrize("kind", ["normal", "bacterial", "viral"])
def test_predict_returns_a_complete_record(authed, sample_bytes, kind):
    r = _upload(authed, sample_bytes(kind), name=f"{kind}.jpg")
    assert r.status_code == 201
    rec = r.json()
    probs = rec["probabilities"]
    assert set(probs) == {"Normal", "Bacterial Pneumonia", "Viral Pneumonia"}
    assert abs(sum(probs.values()) - 1.0) < 1e-3
    assert rec["prediction"] == max(probs, key=probs.get)
    assert abs(rec["confidence"] - max(probs.values())) < 1e-6
    assert rec["original_url"].startswith("/api/files/uploads/")
    assert rec["heatmap_url"].startswith("/api/files/heatmaps/")
    assert rec["created_at"].endswith("Z")


def test_predict_saves_both_images_and_serves_them(authed, sample_bytes, sandbox):
    rec = _upload(authed, sample_bytes("bacterial")).json()
    assert len(os.listdir(sandbox / "uploads")) == 1
    assert len(os.listdir(sandbox / "heatmaps")) == 1
    for url in (rec["original_url"], rec["heatmap_url"]):
        r = authed.get(url)
        assert r.status_code == 200 and r.headers["content-type"].startswith("image/")


def test_same_image_gives_the_same_probabilities(authed, sample_bytes):
    a = _upload(authed, sample_bytes("normal")).json()["probabilities"]
    b = _upload(authed, sample_bytes("normal")).json()["probabilities"]
    assert np.allclose(list(a.values()), list(b.values()), atol=1e-5)


def test_png_upload_is_accepted(authed, sample_bytes):
    import cv2

    img = cv2.imdecode(np.frombuffer(sample_bytes("normal"), np.uint8), cv2.IMREAD_GRAYSCALE)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    assert _upload(authed, buf.tobytes(), name="scan.PNG", ctype="image/png").status_code == 201


# --------------------------------------------------------------------- history
def test_history_lists_newest_first_and_get_by_id(authed, sample_bytes):
    first = _upload(authed, sample_bytes("normal"), name="one.jpg").json()
    second = _upload(authed, sample_bytes("viral"), name="two.jpg").json()
    rows = authed.get("/api/predictions").json()
    assert [r["id"] for r in rows] == [second["id"], first["id"]]
    one = authed.get(f"/api/predictions/{first['id']}")
    assert one.status_code == 200 and one.json()["filename"] == "one.jpg"


def test_unknown_prediction_is_404_json(authed):
    r = authed.get("/api/predictions/424242")
    assert r.status_code == 404 and r.json()["detail"] == "Prediction not found."


def test_limit_is_clamped_to_at_least_one(authed, sample_bytes):
    _upload(authed, sample_bytes("normal"))
    _upload(authed, sample_bytes("viral"))
    assert len(authed.get("/api/predictions?limit=0").json()) == 1


def test_delete_removes_the_record(authed, sample_bytes):
    rec = _upload(authed, sample_bytes("normal")).json()
    assert authed.delete(f"/api/predictions/{rec['id']}").json() == {"deleted": rec["id"]}
    assert authed.get(f"/api/predictions/{rec['id']}").status_code == 404
    assert authed.delete(f"/api/predictions/{rec['id']}").status_code == 404


# ----------------------------------------------------------------------- stats
def test_stats_on_empty_history(authed):
    s = authed.get("/api/stats").json()
    assert s["total"] == 0 and s["avg_confidence"] is None and s["last_scan_at"] is None
    assert len(s["daily"]) == 7


def test_stats_counts_match_history(authed, sample_bytes):
    for kind in ("normal", "bacterial", "viral"):
        _upload(authed, sample_bytes(kind))
    s = authed.get("/api/stats").json()
    assert s["total"] == 3
    assert sum(s["by_class"].values()) == 3
    assert s["pneumonia_total"] == s["by_class"]["Bacterial Pneumonia"] + s["by_class"]["Viral Pneumonia"]
    assert sum(d["count"] for d in s["daily"]) == 3
    assert 0 < s["avg_confidence"] <= 1


# ----------------------------------------------------------------------- files
@pytest.mark.parametrize("path", [
    "/api/files/uploads/missing.jpg", "/api/files/secrets/x.jpg", "/api/files/uploads/..%2Fapp.py",
    "/api/files/heatmaps/..%5Capp.py",
])
def test_files_route_blocks_missing_and_traversal(authed, path):
    assert authed.get(path).status_code == 404
