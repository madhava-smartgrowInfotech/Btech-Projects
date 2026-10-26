import pytest

from app.config import CLASSIFIER_CHECKPOINT

needs_model = pytest.mark.skipif(not CLASSIFIER_CHECKPOINT.exists(), reason="classifier checkpoint not trained")


def _register(client, email="ada@example.com", name="Ada", pw="secret12"):
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": pw})
    return r


def _auth(r):
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


@needs_model
def test_health_reports_model_loaded(client):
    assert client.get("/api/health").json()["model_loaded"] is True


def test_register_login_me(client):
    r = _register(client)
    assert r.status_code == 201 and r.json()["user"]["email"] == "ada@example.com"
    assert "password" not in r.text
    r2 = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "secret12"})
    assert r2.status_code == 200
    me = client.get("/api/auth/me", headers=_auth(r2))
    assert me.status_code == 200 and me.json()["name"] == "Ada"


def test_duplicate_email_conflict(client):
    _register(client)
    assert _register(client).status_code == 409


def test_short_password_rejected(client):
    assert _register(client, pw="123").status_code == 422


def test_bad_login(client):
    _register(client)
    assert client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong-pass"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "secret12"}).status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_history_requires_token(client):
    assert client.get("/api/history").status_code == 401


@needs_model
def test_analyze_anonymous_not_persisted(client, face_png):
    r = client.post("/api/analyze", files={"image": ("f.png", face_png, "image/png")})
    body = r.json()
    assert r.status_code == 200 and body["face_detected"] is True and body["id"] is None
    assert len(body["basic_emotions"]) == 7 and len(body["compound_emotions"]) == 11
    confs = [e["confidence"] for e in body["basic_emotions"]]
    assert confs == sorted(confs, reverse=True) and all(0 <= c <= 1 for c in confs)
    assert body["dominant"]["kind"] in ("basic", "compound")


@needs_model
def test_analyze_persists_and_history_roundtrip(client, face_png):
    auth = _auth(_register(client))
    r = client.post("/api/analyze", files={"image": ("f.png", face_png, "image/png")}, headers=auth)
    aid = r.json()["id"]
    assert aid and r.json()["thumbnail_url"].endswith(f"{aid}.jpg")
    lst = client.get("/api/history", headers=auth).json()
    assert lst["total"] == 1 and lst["items"][0]["id"] == aid
    assert client.get(f"/api/history/{aid}", headers=auth).status_code == 200
    assert client.delete(f"/api/history/{aid}", headers=auth).status_code == 204
    assert client.get(f"/api/history/{aid}", headers=auth).status_code == 404


@needs_model
def test_history_is_private_per_user(client, face_png):
    a = _auth(_register(client, "a@example.com"))
    b = _auth(_register(client, "b@example.com"))
    aid = client.post("/api/analyze", files={"image": ("f.png", face_png, "image/png")}, headers=a).json()["id"]
    assert client.get(f"/api/history/{aid}", headers=b).status_code == 404
    assert client.delete(f"/api/history/{aid}", headers=b).status_code == 404
    assert client.get("/api/history", headers=b).json()["total"] == 0


@needs_model
def test_no_face_returns_200_with_empty_result(client, blank_png):
    """Characterisation: API_CONTRACT.md says 422, the implementation answers 200 with face_detected=false."""
    r = client.post("/api/analyze", files={"image": ("b.png", blank_png, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["face_detected"] is False and body["basic_emotions"] == [] and body["dominant"] is None


def test_missing_file_field_is_422(client):
    assert client.post("/api/analyze").status_code == 422


@needs_model
def test_non_image_upload_is_unhandled_500(client):
    """Characterisation of a known defect: undecodable bytes are not caught and surface as HTTP 500."""
    r = client.post("/api/analyze", files={"image": ("x.txt", b"not an image", "text/plain")})
    assert r.status_code == 500
