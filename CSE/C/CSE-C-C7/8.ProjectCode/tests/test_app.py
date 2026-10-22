from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"] is True

def test_homepage():
    r = client.get("/")
    assert r.status_code == 200 and "LearnPathIQ" in r.text

def _reg():
    email = f"t{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"name": "Test Learner", "email": email, "password": "secret123", "confirm_password": "secret123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]

def test_auth_profile_recs_interactions():
    tok = _reg()
    h = {"X-Token": tok}
    r = client.put("/api/profile", json={"education": "Bachelor's Degree", "skill_level": "Beginner", "interests": "python, data science", "preferred_topics": "Machine Learning", "learning_style": "Self-paced", "goals": "get a data job", "course_preferences": "hands-on", "weekly_hours": 6, "age_band": "25-34", "gender": "F"}, headers=h)
    assert r.status_code == 200
    r = client.get("/api/courses", headers=h)
    assert r.status_code == 200 and r.json()["count"] > 5
    cid = r.json()["courses"][0]["id"]
    r = client.get(f"/api/courses/{cid}", headers=h)
    assert r.status_code == 200
    r = client.get("/api/recommendations?top_n=5", headers=h)
    assert r.status_code == 200 and len(r.json()["recommendations"]) > 0
    before = [x["course"]["id"] for x in r.json()["recommendations"]]
    r = client.post("/api/interactions", json={"course_id": before[0], "event_type": "quiz", "value": 1.0}, headers=h)
    assert r.status_code == 200
    r = client.post("/api/recommendations/refresh", headers=h)
    assert r.status_code == 200
    for ep in ["/api/learning-path", "/api/insights", "/api/activity", "/api/history", "/api/metrics", "/api/fairness"]:
        rr = client.get(ep, headers=h)
        assert rr.status_code in (200, 503), (ep, rr.text)

def test_invalid_inputs():
    r = client.post("/api/auth/register", json={"name": "x", "email": "bad", "password": "123", "confirm_password": "456"})
    assert r.status_code == 422
    tok = _reg()
    r = client.post("/api/interactions", json={"course_id": "X", "event_type": "nope"}, headers={"X-Token": tok})
    assert r.status_code == 400
    r = client.get("/api/courses/NOPE123", headers={"X-Token": tok})
    assert r.status_code == 404

def test_artifacts_load():
    from pathlib import Path
    assert (Path("artifacts/metrics/model_metrics.json").exists() or Path("LearnPathIQ/artifacts/metrics/model_metrics.json").exists())
