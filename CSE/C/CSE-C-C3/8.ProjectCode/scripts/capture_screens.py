"""Capture a 1440x900 PNG of every ParkSure screen into docs/screenshots/.

Needs the app running (run.bat) - backend on 8403, frontend on 5403 - and Playwright:
    pip install playwright && playwright install chromium
    python scripts/capture_screens.py [--base http://127.0.0.1:5403]

It signs in as the seeded demo driver and admin, makes one fresh reservation so the bookings screen has
a row you can act on, and saves the landing page in both dark and light mode.
"""
import argparse
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
DRIVER = ("driver1@parksure.app", "driver123")
ADMIN = ("admin@parksure.app", "admin123")


def api(base, path, body=None, token=None):
    req = urllib.request.Request(base + "/api" + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + token} if token else {})})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def seed_reservation(base):
    """Give the driver an upcoming booking so My bookings shows Check in / Cancel."""
    token = api(base, "/auth/login", {"email": DRIVER[0], "password": DRIVER[1]})["token"]
    now = datetime.now(timezone.utc)
    start, end = now + timedelta(days=2), now + timedelta(days=2, hours=3)
    found = api(base, f"/search?start_time={start.isoformat().replace('+', '%2B')}&end_time={end.isoformat().replace('+', '%2B')}")
    loc = next(x for x in found if x["available"])
    api(base, "/reservations", {"location_id": loc["id"], "start_time": start.isoformat(), "end_time": end.isoformat()}, token)


def sign_in(page, base, who, role_button):
    page.goto(base + "/login")
    page.get_by_role("button", name=role_button).click()
    page.get_by_role("button", name="Log in", exact=True).last.click()
    page.wait_for_url("**/app/**")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5403")
    base = ap.parse_args().base.rstrip("/")
    OUT.mkdir(parents=True, exist_ok=True)
    seed_reservation(base)
    n = [0]

    def shot(page, name, full=False, wait=1500):
        page.wait_for_timeout(wait)
        n[0] += 1
        path = OUT / f"{n[0]:02d}_{name}.png"
        page.screenshot(path=str(path), full_page=full)
        print("saved", path.name)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            browser = p.chromium.launch(channel="chrome")

        for scheme in ("dark", "light"):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
            page = ctx.new_page()
            page.goto(base + "/")
            page.wait_for_selector("h1")
            shot(page, f"landing_{scheme}", wait=2500)
            if scheme == "dark":
                page.evaluate("document.getElementById('how').scrollIntoView()")
                shot(page, "landing_how_it_works", wait=1500)
                page.evaluate("document.getElementById('why').scrollIntoView()")
                shot(page, "landing_features", wait=1500)
            ctx.close()

        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
        page = ctx.new_page()
        page.goto(base + "/login")
        shot(page, "login", wait=800)

        sign_in(page, base, DRIVER, "Driver demo")
        page.goto(base + "/app/find")
        page.wait_for_selector(".loc-card")
        shot(page, "find_parking")
        page.get_by_role("button", name="Reserve", exact=True).first.click()
        page.wait_for_selector("[role=dialog]")
        shot(page, "reserve_dialog", wait=800)
        page.keyboard.press("Escape")
        page.goto(base + "/app/bookings")
        page.wait_for_selector("table tbody tr")
        shot(page, "my_bookings")
        page.goto(base + "/app/trust")
        page.wait_for_selector(".timeline")
        shot(page, "trust_score")
        page.get_by_role("button", name="Log out").first.click()

        sign_in(page, base, ADMIN, "Admin demo")
        for route, name, ready in (
            ("/app/admin", "admin_overview", "text=Buffer strategy comparison"),
            ("/app/admin/locations", "admin_locations", "table tbody tr"),
            ("/app/admin/insights", "admin_insights", "text=Per location"),
            ("/app/admin/bookings", "admin_bookings", "table tbody tr"),
            ("/app/admin/users", "admin_users", "table tbody tr"),
        ):
            page.goto(base + route)
            page.wait_for_selector(ready)
            shot(page, name, wait=2000)
        browser.close()
    print(f"done: {n[0]} screenshots in {OUT}")


if __name__ == "__main__":
    main()
