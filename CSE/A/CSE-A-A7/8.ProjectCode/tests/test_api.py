"""API tests through FastAPI's TestClient against a scratch database."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

VIT = dict(age=58, heart_rate=112, sbp=96, dbp=60, spo2=93, temp_c=36.9, resp_rate=22, arrival_mode="ambulance")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    r = client.post("/api/auth/login", json={"email": "clinician@athena.health", "password": "Athena@123"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_health_and_public_stats_need_no_token(client):
    assert client.get("/api/health").json()["model"] is True
    assert client.get("/api/public/stats").json()["available"] is True


def test_wrong_password_rejected(client):
    assert client.post("/api/auth/login", json={"email": "clinician@athena.health", "password": "nope"}).status_code == 401


@pytest.mark.parametrize("path", ["/api/patients", "/api/metrics", "/api/samples", "/api/auth/me"])
def test_protected_routes_require_token(client, path):
    assert client.get(path).status_code == 401


def test_garbage_token_rejected(client):
    assert client.get("/api/patients", headers={"Authorization": "Bearer abc"}).status_code == 401


def test_sample_queue_seeded_and_ordered(client, auth):
    items = client.get("/api/patients", headers=auth).json()["items"]
    assert len(items) >= 12 and all(i["source"] == "sample" for i in items[:12])
    prios = [i["priority"] for i in items]
    assert prios == sorted(prios)


def test_extract_rejects_empty_and_unsupported(client, auth):
    assert client.post("/api/reports/extract", headers=auth, files={"file": ("a.pdf", b"", "application/pdf")}).status_code == 400
    assert client.post("/api/reports/extract", headers=auth, files={"file": ("a.txt", b"hello", "text/plain")}).status_code == 422


def test_create_patient_validates_vitals(client, auth):
    bad = {**VIT, "spo2": 20}
    assert client.post("/api/patients", headers=auth, json={"vitals": bad}).status_code == 422
    assert client.post("/api/patients", headers=auth, json={"vitals": {**VIT, "arrival_mode": "teleport"}}).status_code == 422


def test_create_patient_and_override_flow(client, auth):
    rep = {"flags": {"chest_pain": 1, "st_elevation": 1, "lab_troponin_high": 1}}
    p = client.post("/api/patients", headers=auth, json={"name": "T One", "vitals": VIT, "report": rep}).json()
    assert 1 <= p["priority"] <= 5 and p["shap"] and p["model_priority"] == p["priority"]
    # a change without a reason is refused
    new = 5 if p["priority"] != 5 else 4
    assert client.post(f"/api/patients/{p['id']}/override", headers=auth, json={"priority": new}).status_code == 422
    # accept keeps the priority
    a = client.post(f"/api/patients/{p['id']}/override", headers=auth, json={"priority": p["priority"]}).json()
    assert a["overrides"][-1]["action"] == "accept"
    # change with a reason updates priority, keeps the model's suggestion
    c = client.post(f"/api/patients/{p['id']}/override", headers=auth, json={"priority": new, "reason": "Stable on review"}).json()
    assert c["priority"] == new and c["model_priority"] == p["priority"] and c["overridden"] is True
    assert c["risk_level"] == ("Low" if new >= 4 else "Moderate")


def test_override_priority_out_of_range(client, auth):
    pid = client.get("/api/patients", headers=auth).json()["items"][0]["id"]
    assert client.post(f"/api/patients/{pid}/override", headers=auth, json={"priority": 9}).status_code == 422


def test_missing_patient_is_404(client, auth):
    assert client.get("/api/patients/99999", headers=auth).status_code == 404
    assert client.post("/api/patients/99999/override", headers=auth, json={"priority": 2}).status_code == 404


def test_summary_pdf(client, auth):
    pid = client.get("/api/patients", headers=auth).json()["items"][0]["id"]
    r = client.get(f"/api/patients/{pid}/summary.pdf", headers=auth)
    assert r.status_code == 200 and r.content[:4] == b"%PDF"


def test_sample_download_blocks_path_traversal(client, auth):
    assert client.get("/api/samples/..%2F..%2F.env", headers=auth).status_code == 404
    assert client.get("/api/samples/report_01_chest_pain_stemi.pdf", headers=auth).status_code == 200


def test_metrics_reports_live_counts(client, auth):
    m = client.get("/api/metrics", headers=auth).json()
    assert m["offline"]["accuracy"] > 0 and m["live"]["patients"] >= 12
    assert set(m["live"]["priority_distribution"]) == {"1", "2", "3", "4", "5"}
