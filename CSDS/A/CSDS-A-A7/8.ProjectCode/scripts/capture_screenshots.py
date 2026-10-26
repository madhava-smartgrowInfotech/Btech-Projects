"""Capture real screenshots of the running SHEGUARD app (1440x900) into docs/screenshots/.

Needs the API on 127.0.0.1:8107 and the Vite dev server on localhost:5107, plus Playwright with the installed Chrome:

    venv\\Scripts\\python scripts/capture_screenshots.py

A fresh account is registered through the UI, guardians are added through the profile form, then the whole flow is
driven in the browser: route planning (live OSRM + Nominatim), the AI assistant (live Gemini), SafePhrase settings,
a real SOS with live location, a photo and a recorded audio clip as evidence, the guardian's tracking page in a
second logged-out browser context, and hold-to-cancel. Geolocation is set by Playwright to fixed city centres; the
microphone is Chrome's built-in fake device (a test tone), the photo is one of the app's own screenshots.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
WEB = "http://localhost:5107"
HYD = {"latitude": 17.3850, "longitude": 78.4867}
DEL = {"latitude": 28.6139, "longitude": 77.2090}
EMAIL = f"asha.demo{int(time.time()) % 100000}@sheguard.app"
PASSWORD = "Demo@1234"
log: list[dict] = []


def shot(page: Page, name: str, note: str, wait: int = 1800, full: bool = False) -> None:
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    log.append({"file": f"{name}.png", "shows": note})
    print("saved", name, flush=True)


def nav(page: Page, label: str) -> None:
    page.get_by_role("button", name=label, exact=True).first.click()
    page.wait_for_timeout(1200)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True, args=[
            "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            "--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, geolocation=DEL,
                                  permissions=["geolocation", "microphone"], locale="en-IN")
        page = ctx.new_page()

        # 01 landing (signed out)
        page.goto(WEB)
        shot(page, "01_landing", "Landing page, signed out", wait=3000)

        # 02 register -> account created through the UI
        page.get_by_role("button", name="Sign up", exact=False).first.click() if page.get_by_role("button", name="Sign up", exact=False).count() else None
        page.wait_for_timeout(1000)
        if page.locator("#name").count() == 0:
            page.get_by_text("Get started", exact=False).first.click()
            page.wait_for_timeout(1000)
        page.locator("#name").fill("Asha Reddy")
        page.locator("#email").fill(EMAIL)
        page.locator("#password").fill(PASSWORD)
        page.locator("input[type=checkbox]").check()
        shot(page, "02_register", "Registration form with the details filled in", wait=800)
        page.get_by_role("button", name="Create account", exact=False).click()
        page.wait_for_timeout(2500)

        # 03 profile: add three guardians through the form
        nav(page, "Profile & Guardians")
        guardians = [("Meena Reddy (mother)", "+919000000001", "meena@example.com", ""),
                     ("Karthik Reddy (brother)", "+919000000002", "", "100200301"),
                     ("Divya Rao (friend)", "+919000000003", "divya@example.com", "100200302")]
        for name, phone, mail, tg in guardians:
            page.locator("#g-name").fill(name)
            page.locator("#g-phone").fill(phone)
            page.locator("#g-email").fill(mail)
            page.locator("#g-tg").fill(tg)
            page.get_by_role("button", name="Add guardian", exact=False).click()
            page.wait_for_timeout(900)
        shot(page, "03_profile_guardians", "Profile with three trusted guardians saved", wait=1200)

        # 04 dashboard
        nav(page, "Dashboard")
        shot(page, "04_dashboard", "Dashboard: SOS, status tiles, risk areas loaded from the model", wait=6500)

        # 05 safe route Delhi -> Jaipur (two alternatives)
        nav(page, "Safe Routes")
        page.wait_for_timeout(2500)
        box = page.locator("#place-search")
        box.fill("Jaipur")
        page.wait_for_timeout(2500)
        shot(page, "05_route_search", "Safe Routes: destination search (Nominatim) with suggestions", wait=500)
        page.locator("ul li button, [role=listbox] button").first.click()
        page.wait_for_timeout(9000)
        shot(page, "06_route_delhi_jaipur", "Delhi to Jaipur: two real OSRM alternatives scored by district risk", wait=2500)
        page.mouse.wheel(0, 700)
        shot(page, "07_route_details", "Route cards: distance, duration, risk tier shares, AI route advice", wait=1500)

        # 08 route in Hyderabad
        ctx.set_geolocation(HYD)
        page.reload()
        page.wait_for_timeout(3000)
        nav(page, "Safe Routes")
        page.wait_for_timeout(2500)
        page.locator("#place-search").fill("Vijayawada")
        page.wait_for_timeout(2500)
        page.locator("ul li button, [role=listbox] button").first.click()
        page.wait_for_timeout(9000)
        shot(page, "08_route_hyderabad_vijayawada", "Hyderabad to Vijayawada route with the risk heat layer", wait=2500)

        # 09 AI assistant
        nav(page, "AI Guardian")
        page.locator("#ai-input").fill("What should I do if I feel unsafe walking alone at night?")
        page.get_by_role("button", name="Send", exact=False).click()
        page.wait_for_timeout(15000)
        shot(page, "09_ai_assistant", "AI Guardian chat: question sent to the Gemini-backed endpoint", wait=1500)

        # 10 SafePhrase
        nav(page, "SafePhrase")
        shot(page, "10_safephrase", "SafePhrase settings: phrases, fingerprints, sensitivity", wait=1500)
        page.locator("#new-phrase").fill("bring my blue bag")
        page.locator("#new-label").fill("casual cover")
        page.get_by_role("button", name="Save SafePhrase").click()
        page.wait_for_timeout(1500)
        shot(page, "11_safephrase_added", "A second cover phrase added; only a SHA-256 fingerprint is shown", wait=500)

        # 12 SOS
        nav(page, "Dashboard")
        page.get_by_role("button", name="TRIGGER EMERGENCY SOS").first.click()
        page.wait_for_timeout(4000)
        shot(page, "12_emergency_started", "Emergency screen right after SOS: tracking link, delivery status, live map", wait=2500)

        # evidence: photo from file, audio from the fake microphone
        photo = OUT / "04_dashboard.png"
        page.locator("input[type=file]").first.set_input_files(str(photo))
        page.wait_for_timeout(2500)
        rec = page.get_by_role("button", name="Record", exact=False)
        if rec.count():
            rec.first.click()
            page.wait_for_timeout(3000)
            rec.first.click()
            page.wait_for_timeout(2500)
        # move the device so the live path grows
        for lat, lng in [(17.3895, 78.4905), (17.3950, 78.4960), (17.4010, 78.5020), (17.4075, 78.5075)]:
            ctx.set_geolocation({"latitude": lat, "longitude": lng})
            page.wait_for_timeout(4500)
        shot(page, "13_emergency_evidence", "Emergency screen with a photo and an audio clip saved (SHA-256 shown) and the path so far", wait=2000)
        link = page.locator("text=/\\/track\\//").first.inner_text()
        print("tracking link text:", link)

        # guardian view in a clean context
        g_ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        g_page = g_ctx.new_page()
        track_url = link.strip()
        if track_url.startswith("http"):
            track_url = track_url.replace("http://127.0.0.1", "http://localhost")
        else:
            track_url = f"{WEB}{track_url if track_url.startswith('/') else '/' + track_url}"
        g_page.goto(track_url)
        g_page.wait_for_timeout(2500)
        ctx.set_geolocation({"latitude": 17.4120, "longitude": 78.5120})
        g_page.wait_for_timeout(6000)
        shot(g_page, "14_guardian_tracking", "Guardian's tracking page, no login: live position and path over WebSocket", wait=1500)

        # cancel by holding the button for 3 s
        btn = page.get_by_text("Hold 3 seconds", exact=False).first
        btn.scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        bb = btn.bounding_box()
        page.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        page.mouse.down()
        page.wait_for_timeout(1500)
        shot(page, "15_hold_to_cancel", "Hold-to-cancel progress ring half full", wait=100)
        page.wait_for_timeout(2200)
        page.wait_for_timeout(1200)
        page.mouse.up()
        page.wait_for_timeout(3500)
        page.mouse.move(900, 400)
        page.mouse.wheel(0, -3000)
        page.wait_for_timeout(800)
        shot(page, "16_dashboard_after_sos", "Dashboard after cancelling: the emergency is logged in recent activity", wait=1500)
        g_page.wait_for_timeout(2000)
        shot(g_page, "17_guardian_cancelled", "Guardian's page after the user confirmed safe (cancelled)", wait=1000)

        nav(page, "Profile & Guardians")
        shot(page, "18_profile_activity", "Profile with guardians and recent activity", wait=1500)
        browser.close()
    (OUT / "_inventory.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
