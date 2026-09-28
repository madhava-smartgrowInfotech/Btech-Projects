"""End-to-end smoke test against the running API (default http://127.0.0.1:8214)."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.getenv("AQUAVISION_API", f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8214')}")
TOKEN = None
FAILED = []


def call(method, path, body=None, token=True, expect=200):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token and TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status, payload = r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        status, payload = e.code, json.loads(e.read() or b"null")
    if status != expect:
        raise AssertionError(f"{method} {path} -> {status} (expected {expect}): {payload}")
    return payload


def step(name, fn):
    t = time.time()
    try:
        info = fn()
        print(f"PASS  {name:<38} {time.time() - t:5.1f}s  {info or ''}")
    except Exception as e:  # noqa: BLE001
        FAILED.append(name)
        print(f"FAIL  {name:<38} {e}")


def login():
    global TOKEN
    call("POST", "/api/auth/login", {"email": "engineer@aquavision.local", "password": "wrong"}, token=False, expect=401)
    r = call("POST", "/api/auth/login", {"email": "engineer@aquavision.local", "password": "engineer123"}, token=False)
    TOKEN = r["token"]
    assert call("GET", "/api/auth/me")["role"] == "engineer"
    return "engineer signed in"


def quality():
    samples = call("GET", "/api/quality/samples")
    a = samples[0]
    r = call("POST", "/api/quality/predict", {"sample_name": a["name"], **a["values"]})
    assert r["label"] == "Not potable", r["label"]
    assert len(r["reasons"]) == 9 and len(r["limits"]) == 9
    assert any(x["status"] == "exceeds" for x in r["limits"])
    r2 = call("POST", "/api/quality/predict", {"sample_name": "partial sample", "ph": 7.1, "Turbidity": 3.0})
    assert 0 <= r2["probability_potable"] <= 1
    assert len(call("GET", "/api/quality/history")) >= 2
    return f"{r['label']} {round(r['confidence'] * 100)}%, top reason {r['reasons'][0]['label']}"


def network():
    g = call("GET", "/api/network")
    assert len(g["nodes"]) >= 50 and len(g["links"]) >= 80
    assert all(n["pressure"] is not None for n in g["nodes"] if n["type"] == "Junction")
    return f"{len(g['nodes'])} nodes, {len(g['links'])} links, NRW {g['summary']['nrw_pct']}%"


def forecast():
    zones = call("GET", "/api/forecast/zones")
    assert len(zones) == 5
    f = call("GET", "/api/forecast?zone=Z3")
    assert len(f["forecast"]) == 7 and all(x["forecast_m3"] > 0 for x in f["forecast"])
    return f"Z3 peak {f['peak']['date']} {f['peak']['forecast_m3']} m3 at {f['peak']['tmax']} C ({f['weather_source']})"


def leak():
    call("POST", "/api/leaks/clear")
    pipes = call("GET", "/api/leaks/pipes")
    target = next(p["pipe"] for p in pipes if p["pipe"] == "P40")
    r = call("POST", "/api/leaks/inject", {"pipe": target, "leak_lps": 15})
    assert r["detected"], r["leak_probability"]
    assert r["true_rank"] is not None and r["true_rank"] <= 3, r["true_rank"]
    g = call("GET", "/api/network")
    assert g["active_leaks"] and g["suspects"]
    alerts = call("GET", "/api/alerts")
    assert any(a["kind"] == "leak" for a in alerts)
    call("POST", "/api/leaks/inject", {"pipe": "P01", "leak_lps": 5}, expect=400)
    return f"p={r['leak_probability']}, ranked #{r['true_rank']}, top {r['ranking'][0]['pipe']}"


def imbalance():
    r = call("GET", "/api/imbalance")
    assert len(r["zones"]) == 5 and "equity_score" in r["current"]
    w = call("POST", "/api/imbalance/whatif", {"pump_speed": 1.1})
    assert w["equity_score"] >= 0
    return f"equity {r['current']['equity_score']}, worst {r['worst_zone']}, suggestion: {r['suggestion']['improves']}"


def anomalies():
    r = call("GET", "/api/anomalies")
    assert r["meters"], "no flagged meters"
    nf = [m for m in r["meters"] if m["type"] == "night_flow"]
    assert nf, "no night-flow meter flagged"
    s = call("GET", f"/api/anomalies/meter/{nf[0]['meter_id']}")
    assert len(s["hourly"]) > 100
    return f"{len(r['meters'])} flagged, night-flow meter {nf[0]['meter_id']}"


def dashboard():
    d = call("GET", "/api/dashboard")
    k = d["kpis"]
    assert k["active_leaks"] >= 1 and k["nrw_pct"] > 0 and len(d["hourly_pressure"]) == 24
    assert len(d["forecast_week"]) == 7 and d["alerts"]
    return f"NRW {k['nrw_pct']}%, alerts {k['open_alerts']}, quality {k['quality_potable_pct']}% potable"


def metrics():
    m = call("GET", "/api/metrics")
    assert {"quality", "demand", "leak", "anomaly"} <= set(m)
    return "all model metrics present"


def roles():
    global TOKEN
    r = call("POST", "/api/auth/login", {"email": "manager@aquavision.local", "password": "manager123"}, token=False)
    eng, TOKEN = TOKEN, r["token"]
    call("POST", "/api/leaks/inject", {"pipe": "P50", "leak_lps": 5}, expect=403)
    call("GET", "/api/dashboard")
    TOKEN = eng
    call("POST", "/api/leaks/clear")
    return "manager can view, cannot inject"


def main():
    call("GET", "/api/health", token=False)
    for name, fn in [("login", login), ("water-quality prediction", quality), ("network model", network),
                     ("demand forecast", forecast), ("leak inject + detect", leak), ("distribution imbalance", imbalance),
                     ("abnormal consumption", anomalies), ("dashboard", dashboard), ("metrics", metrics),
                     ("roles + twin reset", roles)]:
        step(name, fn)
    if FAILED:
        print(f"\n{len(FAILED)} step(s) failed: {', '.join(FAILED)}")
        sys.exit(1)
    print("\nSmoke test passed")


if __name__ == "__main__":
    main()
