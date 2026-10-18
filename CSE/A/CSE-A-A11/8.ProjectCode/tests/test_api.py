"""API tests: FastAPI TestClient against the real engine (no server needed).  python -m pytest tests -q"""
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import auth
from backend.main import app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    # accounts live in a throwaway database so the tests never touch data/app.db
    auth.DB = Path(tempfile.mkdtemp()) / "app.db"
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def headers(client):
    creds = client.get("/api/auth/demo").json()
    token = client.post("/api/auth/login", json=creds).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def wait(client, headers, job_id):
    for _ in range(300):
        j = client.get(f"/api/jobs/{job_id}", headers=headers).json()
        if j["status"] != "running":
            return j
        time.sleep(0.2)
    raise AssertionError("job did not finish")


def test_protected_routes_need_a_token(client):
    assert client.get("/api/reviews").status_code == 401
    assert client.get("/api/reviews", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_demo_account_signs_in_and_bad_password_does_not(client):
    creds = client.get("/api/auth/demo").json()
    assert client.post("/api/auth/login", json=creds).status_code == 200
    assert client.post("/api/auth/login", json={**creds, "password": "wrong"}).status_code == 401


def test_register_validates_and_rejects_duplicates(client):
    body = {"name": "Test User", "email": "t@example.com", "password": "longenough1"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409
    assert client.post("/api/auth/register", json={**body, "email": "bad"}).status_code == 422
    assert client.post("/api/auth/register", json={**body, "email": "x@example.com", "password": "short"}).status_code == 422


def test_demo_review_blocks_and_is_saved(client, headers):
    job = client.post("/api/reviews", headers=headers, json={"kind": "demo-diff"}).json()["job_id"]
    done = wait(client, headers, job)
    assert done["status"] == "done" and done["result"]["verdict"] == "BLOCK"
    rid = done["result"]["review_id"]
    r = client.get(f"/api/reviews/{rid}", headers=headers).json()
    assert len(r["trace"]) == 7 and any(f["rule_id"] == "SQLI" for f in r["findings"])
    assert client.get(f"/api/reviews/{rid}/export/sarif", headers=headers).json()["version"] == "2.1.0"
    assert client.delete(f"/api/reviews/{rid}", headers=headers).status_code == 200
    assert client.get(f"/api/reviews/{rid}", headers=headers).status_code == 404


def test_review_input_is_validated(client, headers):
    assert client.post("/api/reviews", headers=headers, json={"kind": "diff", "diff": "  "}).status_code == 422
    assert client.post("/api/reviews", headers=headers, json={"kind": "diff", "diff": "not a diff"}).status_code == 422
    assert client.post("/api/reviews", headers=headers, json={"kind": "folder", "folder": "Z:/missing"}).status_code == 422


def test_codebase_index_and_ask(client, headers):
    ix = client.post("/api/codebase/index", headers=headers, json={"source": "demo"}).json()
    assert ix["graph"]["nodes"]
    a = client.post(f"/api/codebase/{ix['index_id']}/ask", headers=headers, json={"question": "where is login handled?"}).json()
    assert a["hits"]


def test_lab_analyze(client, headers):
    out = client.post("/api/lab/analyze", headers=headers, json={"code": 'def f(n):\n    cur.execute(f"SELECT * FROM t WHERE a=\'{n}\'")\n'}).json()
    assert any(f["rule_id"] == "SQLI" for f in out["findings"])
    assert client.post("/api/lab/analyze", headers=headers, json={"code": "def ("}).status_code == 422
