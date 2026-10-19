"""ParkSure end-to-end smoke test.

Runs the main flow the frontend uses against a throwaway database (your parksure.db is untouched):
register -> search -> reserve -> pay -> check in -> check out -> trust -> cancel, then the admin screens.
If the frontend dev server is running on 5403 it also checks that /api is proxied to the backend.

    python scripts/smoke_test.py
"""
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_tmp = tempfile.mkdtemp(prefix="parksure_smoke_")
os.environ["PARKSURE_DB"] = "sqlite:///" + (Path(_tmp) / "smoke.db").as_posix()

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def auth(token):
    return {"Authorization": "Bearer " + token}


now = datetime.now(timezone.utc)
iso = lambda dt: dt.isoformat()  # noqa: E731

with TestClient(app) as c:
    # ---- auth
    r = c.post("/api/auth/login", json={"email": "driver1@parksure.app", "password": "wrong"})
    check("login rejects a bad password", r.status_code == 401 and "Incorrect" in r.json()["detail"])
    r = c.post("/api/auth/register", json={"name": "Smoke Driver", "email": "smoke@example.com", "password": "secret123"})
    check("register creates a driver", r.status_code == 200 and r.json()["user"]["role"] == "driver")
    H = auth(r.json()["token"])
    check("register rejects a duplicate email", c.post("/api/auth/register", json={"name": "Smoke Driver", "email": "smoke@example.com", "password": "secret123"}).status_code == 400)
    check("me returns the profile", c.get("/api/auth/me", headers=H).json()["email"] == "smoke@example.com")

    # ---- locations + search
    locs = c.get("/api/locations").json()
    check("seeded locations exist", len(locs) >= 1, str(len(locs)))
    start, end = now + timedelta(days=3), now + timedelta(days=3, hours=2)
    found = c.get("/api/search", params={"start_time": iso(start), "end_time": iso(end)}).json()
    check("search annotates availability", all({"bookable", "available"} <= set(x) for x in found))
    check("search rejects end before start", c.get("/api/search", params={"start_time": iso(end), "end_time": iso(start)}).status_code == 400)
    loc = next(x for x in found if x["available"])

    # ---- reserve -> pay -> check in -> check out
    r = c.post("/api/reservations", json={"location_id": loc["id"], "start_time": iso(now + timedelta(minutes=5)), "end_time": iso(now + timedelta(hours=2))}, headers=H)
    check("reserve succeeds", r.status_code == 200 and r.json()["status"] == "reserved", r.text[:120])
    res = r.json()
    check("reserve returns a checkout", res["amount_due"] > 0 and res["checkout"]["provider"] in ("demo", "stripe"))
    check("confirm demo payment", c.post(f"/api/payments/{res['id']}/confirm", headers=H).json()["status"] == "paid")
    r = c.post(f"/api/reservations/{res['id']}/checkin", headers=H)
    check("check in", r.status_code == 200 and r.json()["reservation"]["status"] == "active", r.text[:120])
    r = c.post(f"/api/reservations/{res['id']}/checkout", headers=H)
    check("check out on time", r.status_code == 200 and r.json()["on_time"] is True, r.text[:120])
    t = c.get("/api/trust", headers=H).json()
    check("trust records the on-time checkout", t["benefit_streak"] >= 1 and any(e["kind"] == "benefit" for e in t["events"]))

    # ---- second booking: cancel, and a refund credit for a paid one
    r = c.post("/api/reservations", json={"location_id": loc["id"], "start_time": iso(start), "end_time": iso(end)}, headers=H)
    rid = r.json()["id"]
    c.post(f"/api/payments/{rid}/confirm", headers=H)
    r = c.post(f"/api/reservations/{rid}/cancel", headers=H)
    check("cancel a paid reservation", r.status_code == 200 and r.json()["status"] == "cancelled" and r.json()["payment_status"] == "refunded")
    check("cancel credits the account", c.get("/api/auth/me", headers=H).json()["account_credit"] > 0)
    check("cancel twice is refused", c.post(f"/api/reservations/{rid}/cancel", headers=H).status_code == 400)
    mine = c.get("/api/reservations", headers=H).json()
    check("my reservations lists both", len(mine) == 2)
    check("window over 30 days is refused", c.post("/api/reservations", json={"location_id": loc["id"], "start_time": iso(now), "end_time": iso(now + timedelta(days=31))}, headers=H).status_code == 400)
    check("driver cannot reach admin", c.get("/api/admin/overview", headers=H).status_code in (401, 403))

    # ---- admin screens
    a = c.post("/api/auth/login", json={"email": "admin@parksure.app", "password": "admin123"}).json()
    AH = auth(a["token"])
    ov = c.get("/api/admin/overview", headers=AH).json()
    check("admin overview", {"users", "locations", "reservations", "revenue", "unable_to_park", "declined"} <= set(ov))
    check("admin users", len(c.get("/api/admin/users", headers=AH).json()) >= 2)
    check("admin bookings", len(c.get("/api/admin/bookings", headers=AH).json()) >= 2)
    ins = c.get("/api/admin/insights", params={"window_days": 60}, headers=AH).json()
    check("admin insights has all four strategies", set(ins["totals"]) == {"fixed_0", "fixed_1", "fixed_3", "dynamic"})
    body = {"name": "Smoke Lot", "address": "1 Test Way", "latitude": 12.9, "longitude": 77.5, "capacity": 10, "price_per_hour": 3.5, "buffer_size": 1}
    r = c.post("/api/locations", json=body, headers=AH)
    check("admin adds a location", r.status_code == 200, r.text[:120])
    lid = r.json()["id"]
    r = c.put(f"/api/locations/{lid}", json={**body, "capacity": 12}, headers=AH)
    check("admin edits a location", r.status_code == 200 and r.json()["capacity"] == 12)
    check("admin deletes a location", c.delete(f"/api/locations/{lid}", headers=AH).json() == {"ok": True})
    check("admin resets buffers", "forced" in c.post("/api/admin/reset-buffers", headers=AH).json())

# ---- optional: frontend proxy
try:
    with urllib.request.urlopen("http://127.0.0.1:5403/api/locations", timeout=2) as resp:
        check("frontend (5403) proxies /api to the backend (8403)", resp.status == 200)
except Exception:
    print("SKIP frontend proxy check (dev server on 5403 is not running, or backend on 8403 is down)")

print()
if failures:
    print(f"SMOKE-FAILED ({len(failures)}): " + ", ".join(failures))
    sys.exit(1)
print("SMOKE-OK")
