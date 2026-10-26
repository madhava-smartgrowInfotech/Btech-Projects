"""Captures every ParkSure screen (1440x900) for the project documents into docs/screenshots/.

Start the app on a FRESH database first (seeded 60-day demo history), backend 8403, frontend 5403:
    set PARKSURE_DB=sqlite:///C:/temp/docs.db & .venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8403
    cd frontend & npm run dev
    python scripts/capture_docs_screens.py

The script drives the real UI and API: a driver reserves, checks in and out; a second driver is moved to the
nearest alternate when a one-bay lot is occupied; the admin screens are shot afterwards, so every screen
shows data produced by the running application.
"""
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
BASE = "http://127.0.0.1:5403"
API = "http://127.0.0.1:8403"


def api(path, body=None, token=None, method=None):
    req = urllib.request.Request(API + "/api" + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"_status": e.code, **json.loads(e.read() or b"{}")}


def login(email, pw):
    return api("/auth/login", {"email": email, "password": pw})["token"]


def local_input(dt):
    return dt.astimezone().strftime("%Y-%m-%dT%H:%M")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.png"):
        f.unlink()
    now = datetime.now(timezone.utc)
    adm = login("admin@parksure.app", "admin123")
    d1 = login("driver1@parksure.app", "driver123")
    d2 = login("driver2@parksure.app", "driver123")

    # one-bay lot right next to Central Station Garage, used for the occupied-on-arrival scenario
    kiosk = api("/locations", {"name": "Kiosk Bay", "address": "1 Kiosk Lane", "latitude": 12.9720, "longitude": 77.5950,
                               "capacity": 1, "price_per_hour": 6.0, "buffer_size": 0}, adm)
    stations = [x for x in api("/locations") if x["name"] == "Central Station Garage"][0]
    # driver 1: a booking he will check in to and out of through the UI, and the Kiosk booking that occupies the bay
    cur = api("/reservations", {"location_id": stations["id"], "start_time": (now + timedelta(minutes=2)).isoformat(),
                                "end_time": (now + timedelta(hours=2)).isoformat()}, d1)
    api("/reservations", {"location_id": stations["id"], "start_time": (now + timedelta(days=2)).isoformat(),
                          "end_time": (now + timedelta(days=2, hours=3)).isoformat()}, d1)
    k1 = api("/reservations", {"location_id": kiosk["id"], "start_time": (now + timedelta(minutes=2)).isoformat(),
                               "end_time": (now + timedelta(hours=2)).isoformat()}, d2)
    api(f"/reservations/{k1['id']}/checkin", None, d2, method="POST")      # the single bay is now occupied
    # driver 1 books Kiosk Bay for a later window (admission passes: bookings do not overlap) ...
    k2 = api("/reservations", {"location_id": kiosk["id"], "start_time": (now + timedelta(hours=3)).isoformat(),
                               "end_time": (now + timedelta(hours=4)).isoformat()}, d1)
    assert k2.get("id"), k2

    n = [0]

    def shot(page, name, wait=1500, full=False):
        page.wait_for_timeout(wait)
        n[0] += 1
        p = OUT / f"{n[0]:02d}_{name}.png"
        page.screenshot(path=str(p), full_page=full)
        print("saved", p.name)

    def sign_in(page, email=None, pw=None, button=None):
        page.goto(BASE + "/login")
        if button:
            page.get_by_role("button", name=button).click()
        else:
            page.get_by_label("Email").fill(email)
            page.get_by_label("Password").first.fill(pw)
        page.get_by_role("button", name="Log in", exact=True).last.click()
        page.wait_for_url("**/app/**")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for scheme in ("dark", "light"):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
            page = ctx.new_page()
            page.goto(BASE + "/")
            page.wait_for_selector("h1")
            shot(page, f"landing_{scheme}", wait=7000)
            if scheme == "dark":
                page.evaluate("document.getElementById('how').scrollIntoView()")
                shot(page, "landing_how_it_works", wait=2000)
                page.evaluate("document.getElementById('why').scrollIntoView()")
                shot(page, "landing_features", wait=2000)
            ctx.close()

        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
        page = ctx.new_page()
        page.goto(BASE + "/login")
        shot(page, "login", wait=1000)

        # ---------------- driver 1
        sign_in(page, button="Driver demo")
        page.goto(BASE + "/app/find")
        page.wait_for_selector(".loc-card")
        shot(page, "find_parking")
        # a window that overlaps driver 2's occupied one-bay lot: Kiosk Bay shows as full
        page.get_by_label("Arrival").fill(local_input(now + timedelta(minutes=10)))
        page.get_by_label("Departure").fill(local_input(now + timedelta(hours=1, minutes=30)))
        page.get_by_role("button", name="Search availability").click()
        shot(page, "search_full_lot", wait=2500)
        page.get_by_label("Arrival").fill(local_input(now + timedelta(days=1, hours=2)))
        page.get_by_label("Departure").fill(local_input(now + timedelta(days=1, hours=5)))
        page.get_by_role("button", name="Search availability").click()
        page.wait_for_timeout(2000)
        page.get_by_role("button", name="Reserve", exact=True).first.click()
        page.wait_for_selector("[role=dialog]")
        shot(page, "reserve_dialog", wait=1000)
        page.get_by_role("button", name="Reserve for").click()
        shot(page, "reservation_confirmed", wait=1800)
        page.keyboard.press("Escape")
        page.goto(BASE + "/app/bookings")
        page.wait_for_selector("table tbody tr")
        shot(page, "my_bookings")
        page.locator("tr", has_text=f"#{cur['id']}").get_by_role("button", name="Check in").click()
        shot(page, "check_in_toast", wait=1200)
        page.wait_for_timeout(1500)
        page.locator("tr", has_text=f"#{cur['id']}").get_by_role("button", name="Check out").click()
        shot(page, "check_out_toast", wait=1200)
        page.goto(BASE + "/app/trust")
        page.wait_for_selector(".timeline")
        shot(page, "trust_score")
        page.get_by_role("button", name="Log out").first.click()

        # ---------------- driver 2: the one-bay lot is occupied by their own earlier booking, so book + arrive elsewhere
        d3 = api("/auth/register", {"name": "Neha Rao", "email": "neha.rao@parksure.app", "password": "driver123"})
        sign_in(page, "neha.rao@parksure.app", "driver123")
        late = api("/reservations", {"location_id": kiosk["id"], "start_time": (now + timedelta(hours=5)).isoformat(),
                                     "end_time": (now + timedelta(hours=6)).isoformat()}, d3["token"])
        page.goto(BASE + "/app/bookings")
        page.wait_for_selector("table tbody tr")
        shot(page, "bookings_before_arrival")
        page.get_by_role("button", name="Check in").first.click()
        shot(page, "moved_to_alternate", wait=1500)
        page.goto(BASE + "/app/bookings")
        page.wait_for_selector("table tbody tr")
        shot(page, "bookings_after_move")
        page.get_by_role("button", name="Log out").first.click()

        # ---------------- admin
        sign_in(page, button="Admin demo")
        for route, name, ready in (
            ("/app/admin", "admin_overview", "text=Buffer strategy comparison"),
            ("/app/admin/locations", "admin_locations", "table tbody tr"),
            ("/app/admin/insights", "admin_insights", "text=Per location"),
            ("/app/admin/bookings", "admin_bookings", "table tbody tr"),
            ("/app/admin/users", "admin_users", "table tbody tr"),
        ):
            page.goto(BASE + route)
            page.wait_for_selector(ready)
            shot(page, name, wait=2500)
        page.goto(BASE + "/app/admin/insights")
        page.wait_for_selector("text=Per location")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.evaluate("document.querySelector('main')?.scrollTo(0, 99999)")
        shot(page, "admin_insights_table", wait=1200)
        ctx.close()

        # ---------------- responsive and API docs
        mob = browser.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark", device_scale_factor=2)
        mp = mob.new_page()
        mp.goto(BASE + "/login")
        mp.get_by_role("button", name="Driver demo").click()
        mp.get_by_role("button", name="Log in", exact=True).last.click()
        mp.wait_for_url("**/app/**")
        mp.goto(BASE + "/app/find")
        mp.wait_for_selector(".loc-card")
        shot(mp, "mobile_find_parking")
        mob.close()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(API + "/docs")
        page.wait_for_selector(".opblock", timeout=20000)
        shot(page, "api_docs", wait=2000)
        browser.close()
    print(f"done: {n[0]} screenshots in {OUT}")


if __name__ == "__main__":
    sys.exit(main())
