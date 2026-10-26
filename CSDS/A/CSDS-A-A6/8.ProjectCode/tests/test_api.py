"""HTTP API: authentication, upload pipeline, report, clause detail, graph, ownership, evaluation endpoint."""
import time

import jwt
import pytest

from app.config import JWT_SECRET
from conftest import SAMPLE_CONTRACT


def upload(client, headers, content, name="agreement.docx"):
    ctype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return client.post("/api/contracts/upload", headers=headers, files={"file": (name, content, ctype)})


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok" and r.json()["port"] == 8106


# ------------------------------------------------------------------ authentication
def test_register_login_roundtrip(client):
    r = client.post("/api/auth/register", json={"email": "a@example.com", "password": "abcdef"})
    assert r.status_code == 200 and r.json()["token"] and r.json()["email"] == "a@example.com"
    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "abcdef"})
    assert r.status_code == 200 and r.json()["user_id"] == 1


def test_duplicate_email_rejected(client):
    body = {"email": "dup@example.com", "password": "abcdef"}
    assert client.post("/api/auth/register", json=body).status_code == 200
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 400 and "already exists" in r.json()["detail"]


@pytest.mark.parametrize("body", [{"email": "x@example.com", "password": "12345"}, {"email": "not-an-email", "password": "abcdef"}, {"email": "x@example.com"}])
def test_invalid_registration_is_422(client, body):
    assert client.post("/api/auth/register", json=body).status_code == 422


def test_wrong_password_and_unknown_user_are_401(client):
    client.post("/api/auth/register", json={"email": "b@example.com", "password": "abcdef"})
    assert client.post("/api/auth/login", json={"email": "b@example.com", "password": "wrong-pw"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "abcdef"}).status_code == 401


def test_password_is_stored_hashed(client):
    from app import db as app_db
    from app.main import app

    client.post("/api/auth/register", json={"email": "c@example.com", "password": "abcdef"})
    s = next(app.dependency_overrides[app_db.get_session]())
    user = s.query(app_db.User).one()
    assert user.password_hash != "abcdef" and user.password_hash.startswith("$2")


def test_protected_routes_need_a_valid_token(client):
    assert client.get("/api/contracts").status_code in (401, 403)
    assert client.get("/api/contracts", headers={"Authorization": "Bearer garbage"}).status_code == 401
    expired = jwt.encode({"sub": "1", "exp": int(time.time()) - 10}, JWT_SECRET, algorithm="HS256")
    assert client.get("/api/contracts", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 600}, "another-secret", algorithm="HS256")
    assert client.get("/api/contracts", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_token_for_deleted_user_is_rejected(client):
    token = jwt.encode({"sub": "999", "exp": int(time.time()) + 600}, JWT_SECRET, algorithm="HS256")
    r = client.get("/api/contracts", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401 and "User not found" in r.json()["detail"]


# ------------------------------------------------------------------ upload and report
def test_upload_runs_the_whole_pipeline(client, auth, docx_bytes):
    headers, _ = auth
    r = upload(client, headers, docx_bytes())
    assert r.status_code == 200, r.text
    rep = r.json()
    assert len(rep["clauses"]) == 5  # five numbered clauses; the title line before clause 1 is not kept
    assert rep["complexity_grade"] in list("ABCDF")
    assert rep["plain_summary"] and rep["key_obligations"]
    flagged = [c for c in rep["clauses"] if c["flag_count"]]
    assert len(flagged) == 3 and {c["max_severity"] for c in flagged} == {"high", "medium"}
    assert [x["combo_id"] for x in rep["combo_flags"]] == ["termination_norefund_penalty"]


def test_report_listing_clause_detail_and_graph(client, auth, docx_bytes):
    headers, _ = auth
    rep = upload(client, headers, docx_bytes()).json()
    cid = rep["id"]
    lst = client.get("/api/contracts", headers=headers).json()
    assert [c["id"] for c in lst] == [cid] and lst[0]["flag_count"] == 3
    assert client.get(f"/api/contracts/{cid}", headers=headers).json()["plain_summary"] == rep["plain_summary"]
    flagged = next(c for c in rep["clauses"] if c["flag_count"])
    det = client.get(f"/api/contracts/{cid}/clauses/{flagged['id']}", headers=headers).json()
    assert det["flags"][0]["safer_wording"] and det["flags"][0]["rule_id"]
    g = client.get(f"/api/contracts/{cid}/graph", headers=headers).json()
    assert len(g["nodes"]) == 5 and len(g["edges"]) == 3 and len(g["risky_combinations"]) == 1


def test_other_users_cannot_see_a_contract(client, auth, docx_bytes):
    headers, _ = auth
    cid = upload(client, headers, docx_bytes()).json()["id"]
    r = client.post("/api/auth/register", json={"email": "intruder@example.com", "password": "abcdef"})
    other = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.get(f"/api/contracts/{cid}", headers=other).status_code == 404
    assert client.get(f"/api/contracts/{cid}/graph", headers=other).status_code == 404
    assert client.get(f"/api/contracts/{cid}/clauses/1", headers=other).status_code == 404
    assert client.get("/api/contracts", headers=other).json() == []


def test_unknown_contract_and_clause_are_404(client, auth, docx_bytes):
    headers, _ = auth
    assert client.get("/api/contracts/12345", headers=headers).status_code == 404
    cid = upload(client, headers, docx_bytes()).json()["id"]
    assert client.get(f"/api/contracts/{cid}/clauses/99999", headers=headers).status_code == 404


def test_upload_rejects_wrong_extension_and_empty_text(client, auth, docx_bytes):
    headers, _ = auth
    r = client.post("/api/contracts/upload", headers=headers, files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400 and "PDF and DOCX" in r.json()["detail"]
    assert upload(client, headers, docx_bytes("Hi")).status_code == 400


def test_upload_without_api_key_is_503(client, auth, docx_bytes, monkeypatch):
    from app.routes import contracts

    monkeypatch.setattr(contracts, "gemini_configured", lambda: False)
    headers, _ = auth
    r = upload(client, headers, docx_bytes())
    assert r.status_code == 503 and "GEMINI_API_KEY" in r.json()["detail"]


def test_upstream_failure_becomes_502_and_temp_file_is_removed(client, auth, docx_bytes, monkeypatch, tmp_path):
    from app.services import gemini_client

    def boom(*a, **k):
        raise RuntimeError("Gemini generate_content failed after 3 attempts: 429")

    monkeypatch.setattr(gemini_client, "generate_json", boom)
    headers, _ = auth
    r = upload(client, headers, docx_bytes())
    assert r.status_code == 502 and "429" in r.json()["detail"]
    assert list(tmp_path.glob("*.docx")) == []


def test_failed_upload_leaves_no_contract(client, auth, docx_bytes, monkeypatch):
    from app.services import gemini_client

    monkeypatch.setattr(gemini_client, "generate_json", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("quota")))
    headers, _ = auth
    upload(client, headers, docx_bytes())
    assert client.get("/api/contracts", headers=headers).json() == []


def test_evaluation_endpoint_serves_the_metrics_file(client):
    r = client.get("/api/eval/metrics")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert body["predatory_detection"]["num_examples"] == 40


@pytest.mark.xfail(reason="malformed JSON from Gemini raises JSONDecodeError (a ValueError), which the route maps to HTTP 400 instead of 502", strict=True)
def test_malformed_gemini_json_is_a_502(client, auth, docx_bytes, monkeypatch):
    import json

    from app.services import gemini_client

    def bad(*a, **k):
        raise json.JSONDecodeError("Expecting value", "", 0)

    monkeypatch.setattr(gemini_client, "generate_json", bad)
    headers, _ = auth
    assert upload(client, headers, docx_bytes()).status_code == 502
