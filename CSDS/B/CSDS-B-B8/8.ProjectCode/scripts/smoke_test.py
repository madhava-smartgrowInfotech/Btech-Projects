"""End-to-end smoke test against the running API (backend on BACKEND_PORT, default 8208).

Drives the real pipeline with the sample video data/sample/demo_fall.mp4:
login -> contacts/settings -> monitoring (pose + activity) -> fall -> 'I'm OK' cancels ->
second fall -> countdown runs out -> alert dispatched -> daily report -> metrics.

    python scripts/smoke_test.py
"""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8208')}/api"
VIDEO = str(ROOT / "data" / "sample" / "demo_fall.mp4")
S = requests.Session()


def step(msg):
    print(f"-- {msg}", flush=True)


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"   ok: {msg}")


def call(method, path, **kw):
    r = S.request(method, BASE + path, timeout=60, **kw)
    if r.status_code >= 400:
        print(f"FAIL: {method} {path} -> {r.status_code} {r.text[:300]}")
        sys.exit(1)
    return r.json()


def wait_for_alert(seen, timeout=40):
    t0 = time.time()
    acts = set()
    while time.time() - t0 < timeout:
        st = call("GET", "/monitor/state")
        acts.add(st["activity"])
        if st.get("alert") and st["alert"]["id"] not in seen:
            return st, acts
        time.sleep(0.3)
    return None, acts


def main():
    step("health")
    check(call("GET", "/health")["status"] == "ok", "backend is up")

    step("auth")
    email = f"smoke{int(time.time())}@carewatch.app"
    reg = call("POST", "/auth/register", json={"name": "Smoke Test", "email": email, "password": "secret123"})
    check("token" in reg, "register returns a token")
    r = S.post(BASE + "/auth/login", json={"email": email, "password": "wrong"})
    check(r.status_code == 401, "wrong password is rejected")
    tok = call("POST", "/auth/login", json={"email": "demo@carewatch.app", "password": "CareWatch123"})["token"]
    S.headers["Authorization"] = f"Bearer {tok}"
    check(call("GET", "/auth/me")["email"] == "demo@carewatch.app", "demo login works")

    step("contacts and settings")
    c = call("POST", "/contacts", json={"name": "Smoke Contact", "relation": "test", "email": "family@example.com"})
    check(c["id"] > 0, "contact created")
    s = call("PUT", "/settings", json={"countdown_seconds": 5, "confirm_seconds": 3, "privacy_mode": True})
    check(s["countdown_seconds"] == 5, "settings saved")
    r = S.put(BASE + "/settings", json={"countdown_seconds": 1})
    check(r.status_code == 400, "invalid setting rejected")

    seen = {a["id"] for a in call("GET", "/alerts")}

    step("monitoring run 1: fall -> 'I'm OK'")
    check(Path(VIDEO).exists(), "sample video exists (python scripts/make_demo_video.py)")
    call("POST", "/monitor/start", json={"source": VIDEO})
    time.sleep(2.5)
    st = call("GET", "/monitor/state")
    check(st["running"], f"monitor running at {st['fps']} fps")
    check(len(st["keypoints"]) == 17, "skeleton keypoints streamed (17)")
    check("image" not in st and "frame" not in st, "privacy mode: no image in the state")
    r = S.get(BASE + "/monitor/frame.jpg")
    check(r.status_code == 404, "privacy mode: video frame endpoint refuses")
    st, acts = wait_for_alert(seen)
    check(st is not None, f"fall confirmed and countdown started (activities seen: {sorted(acts)})")
    check(bool(acts & {"standing", "walking"}), "upright activity recognised before the fall")
    aid = st["alert"]["id"]
    seen.add(aid)
    ok = call("POST", f"/alerts/{aid}/ok")
    check(ok["status"] == "cancelled", "'I'm OK' cancels the alert")
    check(ok["detection_latency_ms"] > 0, f"impact-to-confirmation latency {ok['detection_latency_ms']} ms")
    call("POST", "/monitor/stop")

    step("monitoring run 2: fall -> countdown expires -> alert dispatched")
    call("POST", "/monitor/start", json={"source": VIDEO})
    st, acts = wait_for_alert(seen)
    check(st is not None, "second fall confirmed")
    aid = st["alert"]["id"]
    check("lying" in acts, "lying recognised after the fall")
    t0 = time.time()
    a = None
    while time.time() - t0 < 30:
        a = next(x for x in call("GET", "/alerts") if x["id"] == aid)
        if a["status"] in ("sent", "undelivered"):
            break
        time.sleep(0.5)
    check(a["status"] in ("sent", "undelivered"), f"alert dispatched after countdown (status {a['status']})")
    check(a["has_snapshot"], "snapshot saved with the alert")
    r = S.get(BASE + f"/alerts/{aid}/snapshot")
    check(r.status_code == 200 and r.headers["content-type"] == "image/jpeg", "snapshot downloadable")
    ch = a["channels"]
    check(len(ch.get("email", [])) >= 1, f"email channel attempted: {ch['email'][0]}")
    check(a["detected_to_sent_ms"] is not None, f"detected-to-sent {a['detected_to_sent_ms']} ms")
    call("POST", "/monitor/stop")

    step("test alert")
    t = call("POST", "/alerts/test")
    check(t["status"] in ("sent", "undelivered"), f"test alert processed ({t['status']})")

    step("daily report and metrics")
    rep = call("GET", "/reports/daily")
    check(rep["monitored_seconds"] > 0 and len(rep["timeline"]) > 0, f"report totals {rep['totals']}")
    check(len(rep["falls"]) >= 2, "falls listed in the report")
    m = call("GET", "/metrics")
    check(m["training"] is not None and m["training"]["test_accuracy"] > 0, "training metrics available")

    step("cleanup")
    call("DELETE", f"/contacts/{c['id']}")
    call("PUT", "/settings", json={"countdown_seconds": 20})
    print("\nSMOKE TEST PASSED")


if __name__ == "__main__":
    main()
