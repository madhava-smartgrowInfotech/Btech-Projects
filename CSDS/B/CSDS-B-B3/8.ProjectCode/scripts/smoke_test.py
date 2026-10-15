"""
Smoke test for the SkillVerse web API.

Start the backend first (run.bat, or:  python -m uvicorn backend.main:app --port 8203), then run:
    python scripts/smoke_test.py

Walks the main flow for all three roles against the seeded demo accounts and exits non-zero on any failure.
"""
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

PORT = os.getenv("BACKEND_PORT", "8203")
BASE = f"http://127.0.0.1:{PORT}/api"
PASSWORD = os.getenv("DEMO_PASSWORD", "Demo@1234")

failures = []


def call(method, path, body=None, token=None, expect=200):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    data = json.loads(raw) if raw else None
    if status not in (expect if isinstance(expect, tuple) else (expect,)):
        failures.append(f"{method} {path} -> {status} (wanted {expect}): {str(data)[:200]}")
        print(f"FAIL  {method:6} {path} -> {status}")
    else:
        print(f"ok    {method:6} {path}")
    return data


def login(email, password=PASSWORD):
    data = call("POST", "/auth/login", {"email": email, "password": password})
    return data["token"] if data else None


def student_flow():
    t = login("student@example.com")
    call("GET", "/auth/me", token=t)
    d = call("GET", "/student/dashboard", token=t)
    assert d and d["points"]["level"], "dashboard missing points"

    items = call("GET", "/learning/assessments", token=t)
    detail = call("GET", f"/learning/assessments/{items[0]['id']}", token=t)
    answers = {str(q["id"]): "A" for q in detail["questions"]}
    r = call("POST", f"/learning/assessments/{items[0]['id']}/submit", {"answers": answers}, token=t)
    assert 0 <= r["score"] <= 100
    call("POST", f"/learning/assessments/{items[0]['id']}/submit", {"answers": {}}, token=t, expect=422)

    road = call("POST", "/learning/roadmap", {"career_goal": "Machine Learning Engineer"}, token=t)
    assert road["roadmap"], "roadmap is empty"
    call("GET", "/learning/roadmap", token=t)
    topics = call("GET", "/learning/topics", token=t)
    call("POST", "/learning/progress", {"topic_id": topics[0]["id"], "completion_percent": 50}, token=t)
    g = call("GET", "/graph", token=t)
    assert g["nodes"] and g["edges"], "graph is empty"
    c = call("GET", "/career/recommendations?top_n=3", token=t)
    assert c["recommendations"]
    call("POST", "/career/goal", {"title": c["recommendations"][0]["title"]}, token=t)

    m = call("GET", "/marketplace/resources?only_free=true", token=t)
    free = next((x for x in m["resources"] if not x["owned"] and not x["is_own"]), None)
    if free:
        call("POST", f"/marketplace/resources/{free['id']}/purchase", token=t)
        call("POST", f"/marketplace/resources/{free['id']}/purchase", token=t, expect=422)
    call("GET", "/marketplace/purchases", token=t)
    call("POST", "/marketplace/resources", {"title": f"Smoke {uuid.uuid4().hex[:6]}", "description": "test",
                                            "category": "Notes", "resource_type": "Notes", "price": 0,
                                            "skill_tags": "Python"}, token=t)
    call("GET", "/marketplace/seller", token=t)

    ms = call("POST", "/mentors/recommend", {"required_skill": "Machine Learning", "career_goal": "", "domain": ""}, token=t)
    assert ms, "no mentor matches"
    call("POST", "/mentors/requests", {"mentor_id": ms[-1]["mentor_id"], "message": "Smoke test request"}, token=t,
         expect=(200, 422))  # 422 on re-runs: a request to this mentor is already pending
    call("GET", "/mentors/requests", token=t)
    sessions = call("GET", "/mentors/sessions", token=t)
    scheduled = next((s for s in sessions if s["status"] == "scheduled"), None)
    if scheduled:
        call("POST", f"/mentors/sessions/{scheduled['id']}/complete", {"rating": 5}, token=t)

    meta = call("GET", "/interview/meta", token=t)
    qs = call("POST", "/interview/start", {"role": meta["roles"][0], "interview_type": "Mixed",
                                          "difficulty": "Mixed", "num_questions": 3}, token=t)["questions"]
    rep = call("POST", "/interview/submit", {"role": meta["roles"][0], "interview_type": "Mixed", "difficulty": "Mixed",
                                            "answers": [{"question_id": q["id"], "answer": "I would explain the core idea clearly with an example."} for q in qs]}, token=t)
    assert 0 <= rep["overall_score"] <= 100
    call("GET", "/interview/history", token=t)

    probs = call("GET", "/coding/problems", token=t)
    p = call("GET", f"/coding/problems/{probs[0]['id']}", token=t)
    bad = call("POST", f"/coding/problems/{p['id']}/submit", {"code": p["starter_code"]}, token=t)
    assert bad["passed"] is False
    forbidden = call("POST", f"/coding/problems/{p['id']}/submit", {"code": "import os\n"}, token=t)
    assert forbidden["error"], "sandbox should reject forbidden code"
    good = call("POST", f"/coding/problems/{probs[0]['id']}/submit",
                {"code": "def solve(a, b):\n    return a + b\n"}, token=t)
    assert good["passed"] is True, good
    call("GET", "/coding/stats", token=t)

    call("GET", "/progress/analytics", token=t)
    call("GET", "/profile", token=t)
    call("PUT", "/profile", {"bio": "Smoke test bio"}, token=t)
    prof = call("GET", "/profile", token=t)
    call("PUT", "/profile/skills", {"skills": {str(prof["skills"][0]["skill_id"]): 70}}, token=t)
    call("GET", "/gamification/leaderboard?limit=5", token=t)
    call("GET", "/admin/overview", token=t, expect=403)


def mentor_flow():
    t = login("mentor@example.com")
    p = call("GET", "/mentor/panel", token=t)
    for req in p["pending"]:
        call("POST", f"/mentor/requests/{req['id']}/respond", {"accept": True}, token=t)
    if p["sessions"]:
        call("POST", f"/mentor/sessions/{p['sessions'][0]['id']}/feedback", {"feedback": "Great progress."}, token=t)
    call("GET", "/marketplace/resources", token=t)
    call("GET", "/profile", token=t)
    call("GET", "/student/dashboard", token=t, expect=403)


def admin_flow():
    t = login("admin@example.com")
    call("GET", "/admin/overview", token=t)
    users = call("GET", "/admin/users", token=t)
    admin = next(u for u in users if u["role"] == "admin")
    call("POST", f"/admin/users/{admin['id']}/toggle", token=t, expect=422)  # admins can't be deactivated
    call("GET", "/admin/mentors/pending", token=t)
    call("GET", "/admin/resources", token=t)
    call("GET", "/admin/reports", token=t)


def auth_flow():
    call("POST", "/auth/login", {"email": "student@example.com", "password": "wrong"}, expect=401)
    call("GET", "/student/dashboard", expect=401)
    email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
    call("POST", "/auth/register", {"name": "Smoke Test", "email": email, "password": "Smoke@123", "role": "student"})
    call("POST", "/auth/register", {"name": "Smoke Test", "email": email, "password": "Smoke@123", "role": "student"},
         expect=422)
    t = login(email, "Smoke@123")
    call("GET", "/student/dashboard", token=t)


if __name__ == "__main__":
    call("GET", "/health")
    for flow in (auth_flow, student_flow, mentor_flow, admin_flow):
        try:
            flow()
        except Exception as e:  # noqa: BLE001
            failures.append(f"{flow.__name__}: {type(e).__name__}: {e}")
    print()
    if failures:
        print(f"{len(failures)} problem(s):")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("All smoke checks passed.")
