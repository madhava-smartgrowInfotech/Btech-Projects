"""End-to-end smoke test against the running API (default http://127.0.0.1:8215).

Flow: login -> triage 'fever, cough, breathlessness' -> hospital suggestions -> book token ->
live queue over WebSocket (call next, emergency insert) -> full day overflows to the next day ->
referral with consent -> receiving hospital accepts and completes -> district dashboard.
"""
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

import websockets

BASE = os.getenv("MEDIQUEUE_API", "http://127.0.0.1:8215")
PASSED = []


def call(method, path, body=None, token=None, expect=200):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            status, data = r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        status, data = e.code, json.loads(e.read() or b"null")
    assert status == expect, f"{method} {path} -> {status} {data}"
    return data


def ok(msg):
    PASSED.append(msg)
    print(f"  PASS {msg}")


def login(email):
    return call("POST", "/api/auth/login", {"email": email, "password": "demo1234"})


async def next_event(ws, timeout=5):
    return json.loads(await asyncio.wait_for(ws.recv(), timeout))


async def main():
    today = date.today()
    print(f"MediQueue smoke test against {BASE}")
    assert call("GET", "/api/health")["ok"]
    hospitals = call("GET", "/api/hospitals")
    assert len(hospitals) >= 20
    ok(f"district network loaded: {len(hospitals)} hospitals")

    # --- patient: text -> symptoms -> severity -> suggestions -> booking ----------------------
    email = f"smoke{os.getpid()}@example.com"
    patient = call("POST", "/api/auth/register", {"name": "Smoke Test Patient", "email": email,
                                                  "password": "secret123", "age": 41, "gender": "M"})
    pt = patient["token"]
    mapped = call("POST", "/api/triage/map-text", {"text": "fever, cough, breathlessness"})
    assert {"high_fever", "cough", "breathlessness"} <= set(mapped["symptoms"]), mapped
    ok(f"free text mapped via {mapped['source']}: {mapped['symptoms']}")
    tri = call("POST", "/api/triage", {"symptoms": mapped["symptoms"]})
    assert tri["severity"] == "severe", tri
    ok(f"severity {tri['severity']} (likely {tri['condition']}, {tri['specialty']})")
    crit = call("POST", "/api/triage", {"symptoms": ["chest_pain", "breathlessness", "sweating"]})
    assert crit["severity"] == "critical" and crit["emergency"]
    ok("red-flag rule: chest pain + breathlessness -> critical with emergency advice")

    recs = call("POST", "/api/recommend", {"lat": 17.4375, "lon": 78.4483, "severity": tri["severity"],
                                           "specialty": tri["specialty"], "date": today.isoformat(), "limit": 3})
    assert len(recs) == 3 and all(r["specialty_match"] for r in recs)
    ok("3 hospitals suggested: " + ", ".join(f"{r['name']} ({r['distance_km']} km)" for r in recs))
    target = recs[0]

    booking = call("POST", "/api/bookings", {"hospital_id": target["id"], "date": today.isoformat(),
                                             "symptoms": mapped["symptoms"]}, pt)
    assert booking["status"] == "waiting" and booking["position"] >= 1
    ok(f"booked token {booking['token']} at {booking['hospital']}: position {booking['position']}, "
       f"~{booking['wait_min']} min ({booking['allocation']})")

    # --- hospital console with live WebSocket updates ----------------------------------------
    admin = login("admin@mediqueue.app")["token"]
    hid = target["id"]
    async with websockets.connect(BASE.replace("http", "ws") + f"/api/ws/hospital/{hid}") as ws:
        before = call("GET", f"/api/bookings/{booking['id']}", token=pt)
        call("POST", f"/api/console/{hid}/call-next", token=admin)
        ev = await next_event(ws)
        assert ev["type"] == "queue_changed"
        after = call("GET", f"/api/bookings/{booking['id']}", token=pt)
        assert after["position"] == before["position"] - 1, (before, after)
        ok(f"call next pushed live update: position {before['position']} -> {after['position']}, "
           f"wait {before['wait_min']} -> {after['wait_min']} min")
        call("POST", f"/api/console/{hid}/emergency", {"patient_name": "Walk-in emergency", "age": 60,
                                                        "symptoms": ["chest_pain", "sweating"]}, admin)
        await next_event(ws)
        after2 = call("GET", f"/api/bookings/{booking['id']}", token=pt)
        assert after2["position"] == after["position"] + 1
        ok(f"emergency inserted ahead: position {after['position']} -> {after2['position']}")
    q = call("GET", f"/api/console/{hid}", token=admin)
    assert q["waiting"][0]["kind"] == "emergency"
    ok("console queue shows the emergency first")

    # --- full day pushes bookings to the next day --------------------------------------------
    small = next(h for h in hospitals if h["id"] != hid)
    orig = {k: small[k] for k in ("op_limit",)}
    call("PATCH", f"/api/hospitals/{small['id']}", {"op_limit": 2}, admin)
    tomorrow = (today + timedelta(days=1)).isoformat()
    dates = []
    for _ in range(4):
        b = call("POST", "/api/bookings", {"hospital_id": small["id"], "date": tomorrow,
                                           "symptoms": ["itching", "skin_rash"]}, pt)
        dates.append(b["date"])
    assert dates[-1] > tomorrow, dates
    ok(f"OP limit 2 at {small['name']}: bookings for {tomorrow} placed on {dates}")
    call("PATCH", f"/api/hospitals/{small['id']}", orig, admin)

    # --- referral: consent, accept, complete ---------------------------------------------------
    tg = call("GET", f"/api/referrals/targets?booking_id={booking['id']}", token=admin)
    to = tg["hospitals"][0]
    ref = call("POST", "/api/referrals", {"booking_id": booking["id"], "to_hospital_id": to["id"],
                                          "reason": "Needs pulmonology review and chest imaging",
                                          "notes": "SpO2 94% on room air"}, admin)
    assert ref["status"] == "pending_consent"
    desk = login(f"desk{to['id']}@mediqueue.app")["token"]
    hidden = next(r for r in call("GET", "/api/referrals", token=desk) if r["id"] == ref["id"])
    assert hidden["summary"] is None
    ok(f"referral to {to['name']} ({tg['specialty']}) waits for consent; summary hidden from receiver")
    call("POST", f"/api/referrals/{ref['id']}/consent", {"consent": True}, pt)
    shared = next(r for r in call("GET", "/api/referrals", token=desk) if r["id"] == ref["id"])
    assert shared["summary"] and shared["status"] == "sent"
    acc = call("POST", f"/api/referrals/{ref['id']}/accept", token=desk)
    assert acc["status"] == "accepted" and acc["new_booking"]["token"]
    done = call("POST", f"/api/referrals/{ref['id']}/complete", token=desk)
    assert done["status"] == "completed"
    ok(f"consented -> accepted (new token {acc['new_booking']['token']}) -> completed")
    mine = call("GET", "/api/bookings/mine", token=pt)
    assert any(b.get("referral_id") == ref["id"] and b["hospital_id"] == to["id"] for b in mine)
    ok("patient sees the referral booking in My tokens")

    # --- access control -----------------------------------------------------------------------
    call("GET", "/api/dashboard", token=pt, expect=403)
    call("GET", f"/api/console/{hid}", token=desk, expect=403 if to["id"] != hid else 200)
    ok("role checks: patient blocked from dashboard, desk blocked from other consoles")

    # --- district dashboard ----------------------------------------------------------------------
    dash = call("GET", "/api/dashboard", token=admin)
    assert dash["totals"]["bookings"] > 0 and len(dash["hospitals"]) == len(hospitals)
    ok(f"dashboard: {dash['totals']['bookings']} bookings, avg wait {dash['totals']['avg_wait_min']} min, "
       f"severity {dash['severity']}")
    print(f"\nALL {len(PASSED)} CHECKS PASSED")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
