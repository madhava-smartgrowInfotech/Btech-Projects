"""End-to-end smoke test: API (8409) and the React frontend proxy (5409).

Usage (servers running, e.g. via run.bat):  python scripts/smoke_test.py
Exit code 0 = every check passed.
"""
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def _env():
    vals = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals


ENV = _env()
API = f"http://127.0.0.1:{os.environ.get('PORT', ENV.get('PORT', '8409'))}"
WEB = f"http://127.0.0.1:{os.environ.get('FRONTEND_PORT', ENV.get('FRONTEND_PORT', '5409'))}"

PROFILE = {
    "age": 39, "workclass": "State-gov", "education": "Bachelors",
    "marital-status": "Never-married", "occupation": "Adm-clerical",
    "relationship": "Not-in-family", "race": "White", "sex": "Male",
    "native-country": "United-States", "capital-gain": 2174,
    "capital-loss": 0, "hours-per-week": 40,
}

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail and not ok else ""))


def get(base, path):
    return requests.get(base + path, timeout=60)


def post(base, path, body):
    return requests.post(base + path, json=body, timeout=120)


def main():
    for base, label in ((API, "api"), (WEB, "web-proxy")):
        r = get(base, "/health")
        check(f"{label}: /health ok", r.status_code == 200 and r.json().get("model_loaded") is True, r.text[:120])
        r = get(base, "/api/options")
        o = r.json() if r.ok else {}
        check(f"{label}: /api/options", r.ok and len(o.get("education", [])) == 16 and "limits" in o)
        r = get(base, "/api/dashboard")
        d = r.json() if r.ok else {}
        check(f"{label}: /api/dashboard", r.ok and d.get("metrics", {}).get("roc_auc") and len(d.get("shap_top", [])) == 5)
        r = get(base, "/api/explain")
        check(f"{label}: /api/explain", r.ok and len(r.json().get("features", [])) > 5)
        r = get(base, "/api/performance")
        p = r.json() if r.ok else {}
        check(f"{label}: /api/performance", r.ok and len(p.get("comparison", {}).get("models", {})) == 4)
        r = get(base, "/api/forecast")
        f = r.json() if r.ok else {}
        check(f"{label}: /api/forecast", r.ok and f.get("available") and len(f["forecast"]) == 12)
        for img in ("confusion_matrix.png", "roc_curve.png", "shap_bar.png", "shap_beeswarm.png"):
            r = get(base, f"/artifacts/{img}")
            check(f"{label}: artifact {img}", r.ok and r.headers.get("content-type", "").startswith("image/png"))

        r = post(base, "/api/predict", PROFILE)
        j = r.json() if r.ok else {}
        res = j.get("result", {})
        check(f"{label}: /api/predict valid", r.ok and 0 <= res.get("proba", -1) <= 1 and res.get("shap", {}).get("available"))
        r2 = post(base, "/api/predict", {**PROFILE, "age": 60, "education": "Doctorate", "capital-gain": 50000})
        check(f"{label}: prediction depends on input", r2.ok and r2.json()["result"]["proba"] != res.get("proba"))
        r = post(base, "/api/predict", {**PROFILE, "age": -5})
        check(f"{label}: /api/predict rejects bad age", r.status_code == 400 and r.json().get("errors"))

        r = post(base, "/api/whatif", {**PROFILE, "scenario_capital_gain": "80000", "scenario_hours": "50"})
        w = r.json().get("result", {}) if r.ok else {}
        check(f"{label}: /api/whatif compares", r.ok and w.get("delta") is not None and len(w.get("changed", [])) == 2, r.text[:150])
        r = post(base, "/api/whatif", dict(PROFILE))
        check(f"{label}: /api/whatif needs a change", r.status_code == 400)
        r = post(base, "/api/whatif", {**PROFILE, "scenario_hours": "500"})
        check(f"{label}: /api/whatif rejects bad hours", r.status_code == 400)

    # frontend is served and the SPA fallback works for deep links
    for path in ("/", "/app", "/app/forecast"):
        r = get(WEB, path)
        check(f"web: {path} serves the app", r.ok and '<div id="root">' in r.text)

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.ConnectionError as e:
        print(f"[FAIL] Could not connect - are the API ({API}) and frontend ({WEB}) running? {e}")
        sys.exit(2)
