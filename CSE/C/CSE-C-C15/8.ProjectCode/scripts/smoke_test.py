"""End-to-end smoke test for SentinelFlow: backend API and the React dev server's /api proxy.

Usage (servers already running, e.g. via run.bat):
    python scripts/smoke_test.py
Env: BACKEND_URL (default http://127.0.0.1:8415), FRONTEND_URL (default http://127.0.0.1:5415)

The main flow it covers: status -> interfaces -> settings round trip + validation -> start simulation (409 on a
second start) -> wait for scored windows -> detections / latest / mitigations shapes -> health -> model metrics ->
result PNGs -> stop. Exits 0 when everything passes.
"""
import os
import sys
import time

import requests

BACKEND = os.environ.get("BACKEND_URL", "http://127.0.0.1:8415")
FRONTEND = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5415")
failures = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("  - " + str(detail)) if detail and not ok else ""))
    if not ok:
        failures.append(name)


def get(base, path, **kw):
    return requests.get(base + path, timeout=15, **kw)


def post(base, path, body=None):
    return requests.post(base + path, json=body or {}, timeout=15)


def main():
    try:
        s = get(BACKEND, "/api/status")
    except requests.RequestException as exc:
        print("Backend not reachable at %s (%s). Start it with run.bat first." % (BACKEND, exc))
        return 2
    check("GET /api/status", s.status_code == 200 and "mode" in s.json() and s.json()["model_trained"] is True, s.text[:200])

    # make sure we start from an idle backend
    post(BACKEND, "/api/monitor/stop")
    post(BACKEND, "/api/demo/stop")
    time.sleep(0.5)

    r = get(BACKEND, "/api/interfaces")
    check("GET /api/interfaces", r.status_code == 200 and isinstance(r.json().get("interfaces"), list) and r.json()["interfaces"], r.text[:200])

    original = get(BACKEND, "/api/settings").json()
    check("GET /api/settings", {"window_seconds", "quarantine_seconds"} <= set(original), original)
    r = post(BACKEND, "/api/settings", {"window_seconds": 1})
    check("POST /api/settings rejects window_seconds=1 (400)", r.status_code == 400 and "error" in r.json(), r.text)
    r = post(BACKEND, "/api/settings", {"quarantine_seconds": 99999})
    check("POST /api/settings rejects quarantine_seconds=99999 (400)", r.status_code == 400, r.text)
    r = post(BACKEND, "/api/settings", {"window_seconds": 12, "quarantine_seconds": 45})
    check("POST /api/settings saves valid values", r.status_code == 200 and r.json().get("quarantine_seconds") == 45, r.text)
    back = get(BACKEND, "/api/settings").json()
    check("settings persisted in the running backend", back["window_seconds"] == 12 and back["quarantine_seconds"] == 45, back)
    post(BACKEND, "/api/settings", {"window_seconds": original["window_seconds"], "quarantine_seconds": original["quarantine_seconds"]})

    before = get(BACKEND, "/api/detections?limit=1").json()
    total_before = sum(before["by_prediction"].values())

    r = post(BACKEND, "/api/demo/start", {"window_seconds": 2})
    check("POST /api/demo/start", r.status_code == 200 and r.json().get("mode") == "simulation", r.text)
    r = post(BACKEND, "/api/demo/start", {"window_seconds": 2})
    check("second start is refused (409)", r.status_code == 409 and "error" in r.json(), r.text)
    r = post(BACKEND, "/api/monitor/start", {"interface": "x"})
    check("live start while simulating is refused (409)", r.status_code == 409, r.text)
    st = get(BACKEND, "/api/status").json()
    check("status reports simulation mode", st["mode"] == "simulation" and st["monitoring"] is True, st)

    deadline = time.time() + 60
    total_now = total_before
    while time.time() < deadline:
        d = get(BACKEND, "/api/detections?limit=50").json()
        total_now = sum(d["by_prediction"].values())
        if total_now - total_before >= 4:
            break
        time.sleep(2)
    check("simulation scored at least 4 new windows", total_now - total_before >= 4, "new=%d" % (total_now - total_before))

    d = get(BACKEND, "/api/detections?limit=5").json()
    row = d["detections"][0]
    keys = {"id", "timestamp", "prediction", "confidence", "severity", "packet_rate", "byte_rate", "source_count",
            "destination_count", "distributed_risk", "mitigation_status", "detail"}
    check("detection row has every field the UI reads", keys <= set(row), keys - set(row))
    check("detection detail has features/distributed/severity/actions", {"features", "distributed", "severity", "actions"} <= set(row["detail"]))
    check("by_severity keys are valid", set(d["by_severity"]) <= {"Low", "Medium", "High", "Critical"})
    lt = get(BACKEND, "/api/detections/latest").json()
    check("GET /api/detections/latest", lt.get("detection") is not None)
    r = get(BACKEND, "/api/detections?limit=abc")
    check("bad limit is a 400", r.status_code == 400, r.text)

    m = get(BACKEND, "/api/mitigations").json()
    check("GET /api/mitigations shape", {"active", "history", "quarantine_seconds"} <= set(m), list(m))

    h = get(BACKEND, "/api/health").json()
    check("GET /api/health has a current sample", h.get("current") and "cpu_percent" in h["current"], h)

    mm = get(BACKEND, "/api/model/metrics").json()
    check("GET /api/model/metrics", mm.get("trained") and {"accuracy", "f1"} <= set(mm["metrics"]) and mm.get("confusion_matrix"), list(mm))
    for png in ("confusion_matrix", "roc_curve", "feature_importance"):
        r = get(BACKEND, "/static/results/%s.png" % png)
        check("result plot %s.png" % png, r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"))

    r = post(BACKEND, "/api/demo/stop")
    check("POST /api/demo/stop", r.status_code == 200)
    time.sleep(0.5)
    check("status is stopped afterwards", get(BACKEND, "/api/status").json()["mode"] == "stopped")

    # React dev server: serves the SPA and proxies the API.
    try:
        r = get(FRONTEND, "/")
        check("frontend serves the app shell", r.status_code == 200 and '<div id="root">' in r.text)
        r = get(FRONTEND, "/api/status")
        check("frontend proxies /api to the backend", r.status_code == 200 and "mode" in r.json())
        r = get(FRONTEND, "/static/results/roc_curve.png")
        check("frontend proxies /static/results", r.status_code == 200)
    except requests.RequestException as exc:
        print("Frontend not reachable at %s (%s) - skipped proxy checks." % (FRONTEND, exc))

    print("\n%d failure(s)" % len(failures) if failures else "\nAll smoke checks passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
