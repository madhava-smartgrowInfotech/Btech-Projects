"""End-to-end smoke test of the main LearnPathIQ flow, through the frontend dev server's proxy
(so it proves the React app can reach every endpoint it uses). Needs both servers running (run.bat).

Usage:  python scripts/smoke_test.py
"""
import sys
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def env_port(name, default):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return default


WEB = f"http://127.0.0.1:{env_port('FRONTEND_PORT', '5407')}"
API = f"http://127.0.0.1:{env_port('BACKEND_PORT', '8407')}"
failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def main():
    s = requests.Session()
    r = s.get(WEB + "/")
    check("frontend serves the React app", r.status_code == 200 and '<div id="root">' in r.text)
    check("backend health", s.get(API + "/api/health").json().get("ok") is True)
    check("proxy reaches the API", s.get(WEB + "/api/health").json().get("models_ready") is True)

    email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(WEB + "/api/auth/register", json={"name": "Smoke Test", "email": email, "password": "secret123", "confirm_password": "secret123"})
    check("register", r.status_code == 200 and r.json()["ok"], r.text)
    check("register rejects duplicate email", s.post(WEB + "/api/auth/register", json={"name": "Smoke Test", "email": email, "password": "secret123", "confirm_password": "secret123"}).status_code == 400)
    check("session cookie restores user", s.get(WEB + "/api/me").json()["user"]["email"] == email)

    profile = {"education": "Bachelor's Degree", "skill_level": "Beginner", "interests": "python, data science", "preferred_topics": "Machine Learning",
               "learning_style": "Self-paced", "goals": "get a data job", "course_preferences": "hands-on", "weekly_hours": 6, "age_band": "25-34", "gender": "F"}
    check("save profile", s.put(WEB + "/api/profile", json=profile).json()["ok"])
    check("read profile back", s.get(WEB + "/api/profile").json()["interests"] == "python, data science")

    cat = s.get(WEB + "/api/courses").json()
    check("catalog lists courses", cat["count"] >= 20, str(cat["count"]))
    check("catalog filter by category", all(c["category"] == "Design" for c in s.get(WEB + "/api/courses", params={"category": "Design"}).json()["courses"]))
    check("catalog search", s.get(WEB + "/api/courses", params={"q": "python"}).json()["count"] >= 1)

    recs = s.get(WEB + "/api/recommendations", params={"top_n": 6}).json()
    ids = [x["course"]["id"] for x in recs["recommendations"]]
    check("recommendations ranked with explanations", len(ids) == 6 and all(x["explanation"] for x in recs["recommendations"]))
    top = ids[0]
    before = {x["course"]["id"]: x["score"] for x in s.get(WEB + "/api/recommendations", params={"top_n": 24}).json()["recommendations"]}
    for ev in ("open", "start", "quiz", "complete"):
        check(f"interaction {ev}", s.post(WEB + "/api/interactions", json={"course_id": top, "event_type": ev, "value": 1.0}).json()["ok"])
    check("bad event type rejected", s.post(WEB + "/api/interactions", json={"course_id": top, "event_type": "nope"}).status_code == 400)
    after = {x["course"]["id"]: x["score"] for x in s.get(WEB + "/api/recommendations", params={"top_n": 24}).json()["recommendations"]}
    check("feedback loop changes the ranking score", after[top] != before[top], f"{before[top]} -> {after[top]}")
    check("refresh endpoint", "recommendations" in s.post(WEB + "/api/recommendations/refresh").json())

    detail = s.get(WEB + f"/api/courses/{top}").json()
    check("course detail with match score", "match_score" in detail and detail["explanation"])
    check("unknown course is 404", s.get(WEB + "/api/courses/NOPE").status_code == 404)

    check("activity log", len(s.get(WEB + "/api/activity").json()["events"]) >= 4)
    check("recommendation history", len(s.get(WEB + "/api/history").json()["history"]) >= 1)
    path = s.get(WEB + "/api/learning-path").json()
    check("learning path steps", 1 <= len(path["steps"]) <= 6 and path["next_action"])
    ins = s.get(WEB + "/api/insights").json()
    check("insights", ins["strengths"] and set(ins["uplift"]) == {"quiz", "content", "forum", "homepage", "continue_course"})
    check("insights success probability responds to activity", ins["success_probability"] != 0.55, str(ins["success_probability"]))

    m = s.get(WEB + "/api/metrics").json()
    check("metrics: three models + confusion matrices", set(m["models"]) == {"logistic_regression", "random_forest", "xgboost"} and all(len(v["confusion_matrix"]) == 2 for v in m["models"].values()))
    check("fairness audit", "age_band" in s.get(WEB + "/api/fairness").json()["fairness"])
    check("ROC plot served", s.get(WEB + "/static/roc_curve.png").headers.get("content-type", "").startswith("image/"))

    check("logout", s.post(WEB + "/api/auth/logout").json()["ok"])
    check("protected call is 401 after logout", requests.get(WEB + "/api/recommendations").status_code == 401)
    check("login with bad password is 401", requests.post(WEB + "/api/auth/login", json={"email": email, "password": "wrong-pass"}).status_code == 401)
    check("login works", requests.post(WEB + "/api/auth/login", json={"email": email, "password": "secret123"}).status_code == 200)

    print(f"\n{len(failures)} failure(s)" if failures else "\nSmoke test passed.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
