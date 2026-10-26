"""Measures the running ParkSure API: latency, throughput, an over-booking race and a few security probes.

    # start a backend on a THROW-AWAY database first, e.g.
    #   set PARKSURE_DB=sqlite:///C:/temp/perf.db & set PARKSURE_PORT=8503
    #   .venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8503
    .venv\\Scripts\\python.exe scripts/measure_api.py --base http://127.0.0.1:8503

Writes experiments/api_latency/metrics.json, experiments/concurrency_race/metrics.json and
experiments/security_probes/metrics.json.  Always use 127.0.0.1 (not localhost): on this Windows box
'localhost' adds about 2 s per call through an IPv6 fallback.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments"
NOW = datetime.now(timezone.utc)


def iso(d):
    return d.isoformat()


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def stats(ms):
    return {"n": len(ms), "mean_ms": round(statistics.mean(ms), 2), "p50_ms": round(pct(ms, 0.5), 2),
            "p95_ms": round(pct(ms, 0.95), 2), "p99_ms": round(pct(ms, 0.99), 2), "max_ms": round(max(ms), 2)}


def save(name, obj):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print("wrote", d / "metrics.json")


class Api:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.s = requests.Session()

    def call(self, method, path, token=None, **kw):
        h = {"Authorization": "Bearer " + token} if token else {}
        t0 = time.perf_counter()
        r = self.s.request(method, self.base + path, headers=h, timeout=30, **kw)
        return r, (time.perf_counter() - t0) * 1000.0


def register(api, tag):
    r, _ = api.call("POST", "/api/auth/register", json={"name": f"Perf {tag}", "email": f"{tag}@perf.example.com", "password": "secret123"})
    return r.json()["token"]


def admin_token(api):
    r, _ = api.call("POST", "/api/auth/login", json={"email": "admin@parksure.app", "password": "admin123"})
    return r.json()["token"]


def new_location(api, adm, name, cap, buf, lat=12.9, lon=77.5):
    r, _ = api.call("POST", "/api/locations", adm, json={"name": name, "address": "perf", "latitude": lat, "longitude": lon,
                                                         "capacity": cap, "price_per_hour": 3.0, "buffer_size": buf})
    return r.json()


def latency(api, n=200):
    adm = admin_token(api)
    big = new_location(api, adm, "Perf Big Lot", 5000, 0)
    tok = register(api, "lat")
    res = {}

    def run(label, fn):
        ms = []
        for i in range(n):
            r, t = fn(i)
            assert r.status_code < 500, (label, r.status_code, r.text[:200])
            ms.append(t)
        res[label] = stats(ms)

    q = {"start_time": iso(NOW + timedelta(days=3)), "end_time": iso(NOW + timedelta(days=3, hours=2))}
    run("GET /api/locations", lambda i: api.call("GET", "/api/locations"))
    run("GET /api/search", lambda i: api.call("GET", "/api/search", params=q))
    run("POST /api/auth/login (bcrypt, cost 12)", lambda i: api.call("POST", "/api/auth/login", json={"email": "driver1@parksure.app", "password": "driver123"}))
    run("GET /api/auth/me", lambda i: api.call("GET", "/api/auth/me", tok))
    run("POST /api/reservations", lambda i: api.call("POST", "/api/reservations", tok, json={
        "location_id": big["id"], "start_time": iso(NOW + timedelta(days=5, minutes=i)), "end_time": iso(NOW + timedelta(days=5, minutes=i, hours=2))}))
    run("GET /api/reservations (own bookings)", lambda i: api.call("GET", "/api/reservations", tok))
    run("GET /api/trust", lambda i: api.call("GET", "/api/trust", tok))
    # check-in / check-out need windows that include 'now'
    ids = []
    for i in range(n):
        r, _ = api.call("POST", "/api/reservations", tok, json={"location_id": big["id"], "start_time": iso(datetime.now(timezone.utc) + timedelta(minutes=1)),
                                                                "end_time": iso(datetime.now(timezone.utc) + timedelta(hours=2))})
        ids.append(r.json()["id"])
    run("POST /api/reservations/{id}/checkin", lambda i: api.call("POST", f"/api/reservations/{ids[i]}/checkin", tok))
    run("POST /api/reservations/{id}/checkout", lambda i: api.call("POST", f"/api/reservations/{ids[i]}/checkout", tok))
    run("GET /api/admin/overview", lambda i: api.call("GET", "/api/admin/overview", adm))
    run("GET /api/admin/insights (60-day replay)", lambda i: api.call("GET", "/api/admin/insights", adm, params={"window_days": 60}))
    run("GET /api/admin/bookings", lambda i: api.call("GET", "/api/admin/bookings", adm))

    # throughput: 8 threads x 60 GET /api/search
    done, lock, lat = [0], threading.Lock(), []

    def worker():
        a = Api(api.base)
        for _ in range(60):
            r, t = a.call("GET", "/api/search", params=q)
            with lock:
                done[0] += r.status_code == 200
                lat.append(t)

    ths = [threading.Thread(target=worker) for _ in range(8)]
    t0 = time.perf_counter()
    [t.start() for t in ths]
    [t.join() for t in ths]
    el = time.perf_counter() - t0
    res["throughput_search_8_threads"] = {"requests": done[0], "seconds": round(el, 2), "req_per_s": round(done[0] / el, 1), **stats(lat)}
    meta = {"machine": {"platform": platform.platform(), "python": platform.python_version(), "processor": platform.processor()},
            "server": "uvicorn single process, SQLite file DB, 127.0.0.1", "requests_per_endpoint": n,
            "measured_at": datetime.now().isoformat(timespec="seconds"), "endpoints": res}
    save("api_latency", meta)
    return meta


def race(api, trials=10, threads=20):
    adm = admin_token(api)
    tokens = [register(api, f"race{i}") for i in range(threads)]
    outcomes = []
    for tr in range(trials):
        loc = new_location(api, adm, f"Race Lot {tr}", 2, 1)       # capacity 2 - buffer 1 = exactly one bookable bay
        s, e = NOW + timedelta(days=9 + tr), NOW + timedelta(days=9 + tr, hours=2)
        results = []
        gate = threading.Barrier(threads)

        def go(tok):
            a = Api(api.base)
            gate.wait()
            r, _ = a.call("POST", "/api/reservations", tok, json={"location_id": loc["id"], "start_time": iso(s), "end_time": iso(e)})
            results.append(r.status_code)

        ths = [threading.Thread(target=go, args=(t,)) for t in tokens]
        [t.start() for t in ths]
        [t.join() for t in ths]
        outcomes.append({"accepted": results.count(200), "refused_409": results.count(409), "other": len(results) - results.count(200) - results.count(409)})
    over = sum(1 for o in outcomes if o["accepted"] > 1)
    save("concurrency_race", {"trials": trials, "simultaneous_requests_per_trial": threads, "bookable_bays_per_trial": 1,
                              "trials_with_overbooking": over, "max_accepted_in_a_trial": max(o["accepted"] for o in outcomes),
                              "per_trial": outcomes})


def probes(api):
    adm = admin_token(api)
    out = {}
    tok = register(api, "probe")
    loc = new_location(api, adm, "Probe Lot", 50, 0)
    # a. unauthenticated payment confirmation
    s, e = NOW + timedelta(days=20), NOW + timedelta(days=20, hours=2)
    r, _ = api.call("POST", "/api/reservations", tok, json={"location_id": loc["id"], "start_time": iso(s), "end_time": iso(e)})
    rid = r.json()["id"]
    before = r.json()["payment_status"]
    c, _ = requests.get(api.base + "/api/payments/demo-confirm", params={"reservation_id": rid, "session_id": "forged"}, timeout=10), 0
    after = next(x for x in api.call("GET", "/api/reservations", tok)[0].json() if x["id"] == rid)["payment_status"]
    out["unauthenticated_demo_confirm_marks_paid"] = {"status_before": before, "http_status": c.status_code, "status_after": after,
                                                      "vulnerable": before == "pending" and after == "paid"}
    # b. booking window in the past
    r, _ = api.call("POST", "/api/reservations", tok, json={"location_id": loc["id"], "start_time": iso(NOW - timedelta(days=2)), "end_time": iso(NOW - timedelta(days=2) + timedelta(hours=1))})
    out["past_window_accepted"] = {"http_status": r.status_code, "accepted": r.status_code == 200}
    # c. check-in days before the booked window
    r, _ = api.call("POST", "/api/reservations", tok, json={"location_id": loc["id"], "start_time": iso(NOW + timedelta(days=25)), "end_time": iso(NOW + timedelta(days=25, hours=1))})
    r2, _ = api.call("POST", f"/api/reservations/{r.json()['id']}/checkin", tok)
    out["early_checkin_accepted"] = {"days_early": 25, "http_status": r2.status_code, "accepted": r2.status_code == 200}
    # d. forged admin token with the shipped development secret
    from jose import jwt
    forged = jwt.encode({"sub": "1", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "parksure-dev-secret-change-in-production", algorithm="HS256")
    r, _ = api.call("GET", "/api/admin/overview", forged)
    out["forged_token_with_default_secret"] = {"http_status": r.status_code, "accepted": r.status_code == 200}
    # e. brute-force login: 30 wrong passwords in a row, then the right one
    codes = [api.call("POST", "/api/auth/login", json={"email": "driver2@parksure.app", "password": f"wrong{i}"})[0].status_code for i in range(30)]
    ok, _ = api.call("POST", "/api/auth/login", json={"email": "driver2@parksure.app", "password": "driver123"})
    out["login_has_no_lockout_or_rate_limit"] = {"wrong_attempts": 30, "all_401": set(codes) == {401}, "correct_login_after": ok.status_code}
    # f. SQL injection style inputs
    r1, _ = api.call("POST", "/api/auth/login", json={"email": "' OR 1=1 --", "password": "x"})
    r2, _ = api.call("GET", "/api/search", params={"start_time": "2030-01-01' OR '1'='1", "end_time": "2030-01-02"})
    r3, _ = api.call("POST", "/api/auth/login", json={"email": "a@b.co' OR '1'='1", "password": "' OR '1'='1"})
    out["injection_inputs"] = {"login_email_payload": r1.status_code, "search_param_payload": r2.status_code, "login_password_payload": r3.status_code,
                               "any_server_error": any(x >= 500 for x in (r1.status_code, r2.status_code, r3.status_code))}
    # g. cross-user access
    other = register(api, "probe2")
    r, _ = api.call("POST", f"/api/reservations/{rid}/cancel", other)
    out["cross_user_cancel_blocked"] = {"http_status": r.status_code, "blocked": r.status_code == 404}
    # h. markup in a name
    r, _ = api.call("POST", "/api/auth/register", json={"name": "<script>alert(1)</script>", "email": "xss@perf.example.com", "password": "secret123"})
    out["markup_in_name"] = {"http_status": r.status_code, "stored_verbatim": r.status_code == 200 and r.json()["user"]["name"] == "<script>alert(1)</script>"}
    save("security_probes", out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8503")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    api = Api(a.base)
    if "127.0.0.1" not in a.base:
        sys.exit("use 127.0.0.1 so the numbers are not inflated by the localhost IPv6 fallback")
    if not a.only or "latency" in a.only:
        latency(api)
    if not a.only or "race" in a.only:
        race(api)
    if not a.only or "probes" in a.only:
        probes(api)
