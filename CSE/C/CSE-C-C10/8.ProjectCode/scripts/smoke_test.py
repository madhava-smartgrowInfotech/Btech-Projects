"""End-to-end smoke test of the VenturePulse API (in-process, no ports needed).

    python scripts/smoke_test.py            # backend checks
    python scripts/smoke_test.py --live     # also checks the running Vite proxy on the frontend port

Exit code 0 = every check passed.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail and not ok else ''}")
    if not ok:
        failures.append(name)


def main() -> int:
    h = client.get("/api/health")
    check("GET /api/health", h.status_code == 200 and h.json()["status"] == "ok", h.text)

    cfg = client.get("/api/config")
    j = cfg.json() if cfg.status_code == 200 else {}
    check("GET /api/config", cfg.status_code == 200 and j.get("ks") == [10, 20, 30, 50] and "Software" in j.get("industries", []), cfg.text[:200])

    m = client.get("/api/model-metrics").json()
    check("GET /api/model-metrics", len(m.get("models", {})) == 4 and m["best_model"] in m["models"])

    i = client.get("/api/insights").json()
    check("GET /api/insights", i.get("total", 0) > 200 and i["success"] + i["failure"] == i["total"])

    fi = client.get("/api/feature-importance?top=5").json()
    check("GET /api/feature-importance", len(fi.get("features", [])) == 5 and fi["features"][0]["value"] >= fi["features"][-1]["value"])

    bad = client.post("/api/auth/login", json={"email": "demo@venturepulse.com", "password": "wrong"})
    check("login rejects a wrong password (401)", bad.status_code == 401)
    ok = client.post("/api/auth/login", json={"email": "demo@venturepulse.com", "password": "Demo@1234"})
    token = ok.json().get("token") if ok.status_code == 200 else None
    check("login accepts the demo account", token is not None, ok.text)
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    check("GET /api/auth/me with token", me.status_code == 200 and me.json()["email"] == "demo@venturepulse.com")
    check("GET /api/auth/me without token (401)", client.get("/api/auth/me").status_code == 401)

    payload = {"funding_total_usd": 2500000, "funding_rounds": 2, "industry_type": "Software", "state": "CA",
               "description": "A subscription analytics platform for small retailers using demand forecasting.", "k": 20}
    p = client.post("/predict", json=payload)
    pj = p.json() if p.status_code == 200 else {}
    check("POST /predict", p.status_code == 200 and pj.get("outcome") in ("SUCCESS", "FAILURE") and len(pj.get("similar", [])) == 20
          and abs(pj["probability_success"] + pj["probability_failure"] - 1) < 1e-6, p.text[:200])
    check("POST /predict rejects invalid input", client.post("/predict", json={"funding_total_usd": -5, "k": 999}).status_code == 422)

    for path in ("/dashboard", "/predict", "/performance", "/insights"):
        check(f"legacy page {path} still renders", client.get(path).status_code == 200)

    if "--live" in sys.argv:
        port = "5410"
        try:
            for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
                if line.startswith("FRONTEND_PORT="):
                    port = line.split("=", 1)[1].strip()
        except OSError:
            pass
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=8) as r:
                check(f"frontend proxy :{port} -> /api/health", r.status == 200)
        except Exception as e:  # noqa: BLE001
            check(f"frontend proxy :{port} -> /api/health", False, str(e))

    print(f"\n{'ALL CHECKS PASSED' if not failures else 'FAILED: ' + ', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
