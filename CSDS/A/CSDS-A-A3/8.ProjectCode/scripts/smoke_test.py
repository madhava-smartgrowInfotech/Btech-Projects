"""End-to-end smoke test for the API the React frontend uses.

    python scripts/smoke_test.py

Drives backend/server.py (the original Flask app plus the read-only additions)
through the main flow: check a URL -> report it twice -> community verdict
overrides the model -> the entry shows up in threat intel, the check log and
the stats. Uses a throwaway threat-intel database so real data is untouched.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from phishguard import config  # noqa: E402

config.TI_DATABASE = Path(tempfile.gettempdir()) / "phishguard_smoke.db"
config.AUTO_RETRAIN_EVERY = 10 ** 9          # never retrain during the smoke test
if config.TI_DATABASE.exists():
    os.remove(config.TI_DATABASE)

from backend.server import build_app  # noqa: E402

PHISH = "http://secure-paypal-login.account-verify.tk/signin?user=a"
SAFE = "https://github.com/anthropics"


def step(name, cond, detail=""):
    print(f"{'ok  ' if cond else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
    if not cond:
        raise SystemExit(1)


def main():
    c = build_app().test_client()

    h = c.get("/api/health").get_json()
    step("health", h["ok"] and h["model_ready"], f"model={h['model']} v{h['model_version']}")

    cfg = c.get("/api/config").get_json()
    groups = cfg["feature_groups"]
    step("config + feature groups", sum(len(v) for v in groups.values()) == cfg["feature_count"] == 47)

    r = c.get("/api/check", query_string={"url": PHISH})
    j = r.get_json()
    step("check phishing URL", r.status_code == 200 and j["verdict"] == "phishing" and j["decided_by"] == "ml",
         f"p={j['probability']}")
    step("CORS header on API", r.headers.get("Access-Control-Allow-Origin") == "*")
    step("check safe URL", c.get("/api/check", query_string={"url": SAFE}).get_json()["verdict"] == "safe")
    step("empty URL rejected", c.get("/api/check?url=").status_code == 400)

    for who in ("alice", "bob"):
        e = c.post("/api/report", json={"url": SAFE, "verdict": "phishing", "reporter": who, "note": "smoke"}).get_json()
    step("two reports confirm phishing", e["status"] == "confirmed_phishing", f"votes={e['phishing_votes']}")
    step("invalid verdict rejected", c.post("/api/report", json={"url": SAFE, "verdict": "maybe"}).status_code == 400)

    j = c.get("/api/check", query_string={"url": SAFE}).get_json()
    step("community overrides the model", j["verdict"] == "phishing" and j["decided_by"] == "community")

    intel = c.get("/api/intel").get_json()
    step("threat-intel list", len(intel) == 1 and intel[0]["status"] == "confirmed_phishing")
    step("threat-intel status filter", c.get("/api/intel?status=pending").get_json() == [])
    step("unknown status rejected", c.get("/api/intel?status=bogus").status_code == 400)

    look = c.get("/api/intel/lookup", query_string={"url": SAFE}).get_json()["entry"]
    step("lookup returns report history", look and len(look["reports"]) == 2)
    step("lookup of unknown URL", c.get("/api/intel/lookup?url=http://nothing.example").get_json()["entry"] is None)

    checks = c.get("/api/checks?limit=10").get_json()
    step("check log", len(checks) == 3 and checks[0]["decided_by"] == "community")

    s = c.get("/api/stats").get_json()
    ti = s["threat_intel"]
    step("stats", ti["checks"] == 3 and ti["reports"] == 2 and ti["confirmed_phishing"] == 1 and s["metrics"]["best_model"])

    for path in ("/", "/report", "/community", "/models"):
        step(f"original Flask page {path}", c.get(path).status_code == 200)

    dist = ROOT / "frontend" / "dist" / "index.html"
    print(f"info  frontend build {'present' if dist.exists() else 'not built (run npm run build in frontend/)'}")
    print("smoke test passed")


if __name__ == "__main__":
    main()
