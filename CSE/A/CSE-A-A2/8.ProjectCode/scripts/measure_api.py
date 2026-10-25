"""Measure ResQAI API latency on 127.0.0.1 (not "localhost": on this Windows box the IPv6 fallback adds ~2 s per call).

Usage:  python scripts/measure_api.py [host_port]        default 127.0.0.1:8302 (Flask backend, REQUIRE_AUTH=0)
Writes experiments/resqai_eval/api_latency.json.

The Flask server is `app.run(debug=True)` (Werkzeug development server) - the numbers describe that server, not a
production WSGI deployment.
"""
import http.client
import json
import statistics
import sys
import time
from pathlib import Path

HOSTPORT = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8302"
OUT = Path(__file__).resolve().parent.parent / "experiments" / "resqai_eval"
OUT.mkdir(parents=True, exist_ok=True)


def stats(ms):
    ms = sorted(ms)
    q = lambda p: ms[min(len(ms) - 1, int(round(p / 100 * (len(ms) - 1))))]
    return {"n": len(ms), "mean": round(statistics.mean(ms), 2), "p50": round(q(50), 2), "p95": round(q(95), 2), "p99": round(q(99), 2), "max": round(ms[-1], 2)}


def main():
    conn = http.client.HTTPConnection(HOSTPORT, timeout=20)

    def call(method, path, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        t = time.perf_counter()
        conn.request(method, path, json.dumps(body) if body is not None else None, headers)
        r = conn.getresponse()
        data = r.read()
        return (time.perf_counter() - t) * 1000, r.status, json.loads(data or b"{}")

    for _ in range(20):  # warm-up
        call("GET", "/api/simulate?scenario=severe")
    res = {"host": HOSTPORT, "server": "Flask 3 / Werkzeug development server, debug=True, one process", "endpoints": {}}
    N = 300
    t_sim, t_pred, t_hosp, t_em = [], [], [], []
    reading = call("GET", "/api/simulate?scenario=moderate")[2]
    for _ in range(N):
        t_sim.append(call("GET", "/api/simulate?scenario=random")[0])
    for _ in range(N):
        ms, st, _ = call("POST", "/api/predict", reading)
        assert st == 200
        t_pred.append(ms)
    for _ in range(N):
        t_hosp.append(call("GET", "/api/hospitals?lat=17.41&lon=78.45&k=3")[0])
    for _ in range(N):
        t_em.append(call("POST", "/api/emergency", {"severity_label": "Severe", "confidence": 0.93, "lat": 17.41, "lon": 78.45})[0])
    res["endpoints"] = {"GET /api/simulate": stats(t_sim), "POST /api/predict": stats(t_pred), "GET /api/hospitals?k=3": stats(t_hosp), "POST /api/emergency": stats(t_em)}

    # The path one alert takes after the occupant fails to cancel: sensor reading -> predict -> emergency dispatch.
    # The 15 s confirmation window is a deliberate design delay and is NOT included here.
    e2e = []
    for _ in range(150):
        t = time.perf_counter()
        _, _, rd = call("GET", "/api/simulate?scenario=severe")
        _, _, pr = call("POST", "/api/predict", rd)
        call("POST", "/api/emergency", {"severity_label": pr["severity_label"], "confidence": pr["confidence"], "lat": 17.41, "lon": 78.45})
        e2e.append((time.perf_counter() - t) * 1000)
    res["alert_path_ms"] = {**stats(e2e), "note": "simulate + predict + emergency, three sequential HTTP calls on loopback; excludes the 15 s confirmation countdown and any real SMS / network delivery"}
    res["design_confirmation_window_s"] = 15

    # A fresh TCP connection per call, like a client without keep-alive.
    fresh = []
    for _ in range(100):
        c = http.client.HTTPConnection(HOSTPORT, timeout=20)
        t = time.perf_counter()
        c.request("POST", "/api/predict", json.dumps(reading), {"Content-Type": "application/json"})
        c.getresponse().read()
        fresh.append((time.perf_counter() - t) * 1000)
        c.close()
    res["predict_new_connection_ms"] = stats(fresh)

    # Sequential throughput on /api/predict (single client).
    t = time.perf_counter()
    n = 0
    while time.perf_counter() - t < 5:
        call("POST", "/api/predict", reading)
        n += 1
    res["predict_throughput_req_per_s_single_client"] = round(n / (time.perf_counter() - t), 1)
    (OUT / "api_latency.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
