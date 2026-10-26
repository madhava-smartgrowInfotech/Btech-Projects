"""Measures SentinelFlow's REST API over real HTTP on 127.0.0.1 and runs a battery of malformed-input probes.

    python scripts/measure_api.py [http://127.0.0.1:8415]

Point it at a SCRATCH copy of the backend (it posts settings and starts/stops the simulator). Writes
results/experiments/api_measurements.json. 127.0.0.1 is used on purpose: "localhost" adds ~2 s per call on this machine (IPv6 fallback).
"""
import json
import os
import statistics
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8415"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "experiments", "api_measurements.json")
S = requests.Session()


def timed(method, path, n, **kw):
    ms = []
    code = None
    for _ in range(n):
        t = time.perf_counter()
        r = S.request(method, BASE + path, timeout=30, **kw)
        ms.append((time.perf_counter() - t) * 1e3)
        code = r.status_code
    ms.sort()
    return {"path": path, "method": method, "n": n, "status": code, "mean_ms": statistics.mean(ms),
            "p50_ms": ms[len(ms) // 2], "p95_ms": ms[int(len(ms) * 0.95) - 1], "max_ms": ms[-1]}


def probe(name, method, path, expect, **kw):
    try:
        r = S.request(method, BASE + path, timeout=30, **kw)
        ok = r.status_code in expect if isinstance(expect, (list, tuple, set)) else r.status_code == expect
        body = r.text[:160].replace("\n", " ")
        return {"name": name, "method": method, "path": path, "status": r.status_code, "expected": expect, "ok": bool(ok), "body": body}
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "method": method, "path": path, "status": None, "expected": expect, "ok": False, "body": str(exc)[:160]}


def main():
    res = {"base": BASE}
    S.post(BASE + "/api/demo/stop")
    S.post(BASE + "/api/monitor/stop")
    time.sleep(0.5)
    # ---- latency (idle backend, empty database -> then with data)
    lat = []
    for path in ("/api/status", "/api/health", "/api/interfaces", "/api/settings", "/api/mitigations", "/api/model/metrics", "/api/detections/latest"):
        lat.append(timed("GET", path, 100))
    lat.append(timed("GET", "/", 30))
    lat.append(timed("GET", "/static/results/confusion_matrix.png", 30))
    lat.append(timed("POST", "/api/settings", 50, json={"window_seconds": 10, "quarantine_seconds": 40}))

    # ---- run the simulator at 2 s windows for a while so the database has rows, then measure the data-bearing endpoints
    t0 = time.time()
    S.post(BASE + "/api/demo/start", json={"window_seconds": 2})
    seen_first = None
    deadline = time.time() + 40
    while time.time() < deadline:
        d = S.get(BASE + "/api/detections?limit=1").json()["detections"]
        if d and seen_first is None:
            seen_first = time.time() - t0
        if len(S.get(BASE + "/api/detections?limit=500").json()["detections"]) >= 12:
            break
        time.sleep(1)
    res["first_detection_after_start_seconds"] = seen_first
    for path in ("/api/detections?limit=50", "/api/detections?limit=500", "/api/detections/latest", "/api/mitigations", "/api/status"):
        lat.append(timed("GET", path + ("" if "?" in path else ""), 60))
    stat = S.get(BASE + "/api/status").json()
    res["status_during_simulation"] = {k: stat.get(k) for k in ("mode", "windows_completed", "active_mitigations", "window_seconds")}
    dets = S.get(BASE + "/api/detections?limit=500").json()
    res["live_sim_windows_scored"] = len(dets["detections"])
    res["live_sim_by_prediction"] = dets["by_prediction"]
    res["live_sim_by_severity"] = dets["by_severity"]
    mit = S.get(BASE + "/api/mitigations").json()
    res["live_sim_quarantines_recorded"] = len(mit["history"])
    S.post(BASE + "/api/demo/stop")
    res["latency"] = lat

    # ---- malformed-input / abuse probes
    P = []
    P.append(probe("limit not a number", "GET", "/api/detections?limit=abc", 400))
    P.append(probe("limit SQL-looking string", "GET", "/api/detections?limit=1;DROP TABLE detections", 400))
    P.append(probe("limit negative clamps to 1", "GET", "/api/detections?limit=-5", 200))
    P.append(probe("limit huge clamps to 500", "GET", "/api/detections?limit=99999999999", 200))
    P.append(probe("unknown endpoint -> JSON 404", "GET", "/api/does-not-exist", 404))
    P.append(probe("window_seconds below range", "POST", "/api/settings", 400, json={"window_seconds": 1}))
    P.append(probe("window_seconds above range", "POST", "/api/settings", 400, json={"window_seconds": 121}))
    P.append(probe("window_seconds as text", "POST", "/api/settings", 400, json={"window_seconds": "ten"}))
    P.append(probe("window_seconds float string", "POST", "/api/settings", 400, json={"window_seconds": "1e9"}))
    P.append(probe("quarantine_seconds below range", "POST", "/api/settings", 400, json={"quarantine_seconds": 1}))
    P.append(probe("quarantine_seconds above range", "POST", "/api/settings", 400, json={"quarantine_seconds": 99999}))
    P.append(probe("malformed JSON body tolerated", "POST", "/api/settings", 200, data="{not json", headers={"Content-Type": "application/json"}))
    P.append(probe("array JSON body", "POST", "/api/settings", [200, 400, 500], json=[1, 2, 3]))
    P.append(probe("path traversal in results route", "GET", "/static/results/..%2f..%2fapp.py", [400, 404]))
    P.append(probe("path traversal (plain ..)", "GET", "/static/results/../../app.py", [400, 404]))
    P.append(probe("missing results file", "GET", "/static/results/nope.png", 404))
    P.append(probe("wrong method on /api/status", "POST", "/api/status", 405))
    P.append(probe("wrong method on /api/detections", "DELETE", "/api/detections", 405))
    P.append(probe("monitor/start bad window", "POST", "/api/monitor/start", 400, json={"window_seconds": 0}))
    P.append(probe("demo/start bad window", "POST", "/api/demo/start", 400, json={"window_seconds": 5000}))
    P.append(probe("demo/start twice -> 409", "POST", "/api/demo/start", 200, json={"window_seconds": 2}))
    P.append(probe("second start while running", "POST", "/api/demo/start", 409, json={}))
    P.append(probe("monitor/start while simulation runs", "POST", "/api/monitor/start", 409, json={}))
    S.post(BASE + "/api/demo/stop")
    P.append(probe("very long interface name accepted but not echoed unsafely", "POST", "/api/settings", 200, json={"interface": "A" * 5000}))
    # Live capture without Npcap: reports the real reason instead of crashing
    time.sleep(0.5)
    r = probe("live capture start without Npcap", "POST", "/api/monitor/start", [200, 500], json={"interface": "default", "window_seconds": 2})
    time.sleep(6)
    st = S.get(BASE + "/api/status").json()
    r["capture_error_after_6s"] = st.get("capture_error")
    r["mode_after_6s"] = st.get("mode")
    P.append(r)
    S.post(BASE + "/api/monitor/stop")
    res["probes"] = P
    res["probes_ok"] = sum(1 for p in P if p["ok"])
    res["probes_total"] = len(P)
    # backend still healthy after abuse
    res["healthy_after_probes"] = S.get(BASE + "/api/status").status_code == 200
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=2)
    print("probes ok %d/%d" % (res["probes_ok"], res["probes_total"]), "healthy:", res["healthy_after_probes"])
    for p in P:
        if not p["ok"]:
            print("PROBE FAIL", p)


if __name__ == "__main__":
    main()
