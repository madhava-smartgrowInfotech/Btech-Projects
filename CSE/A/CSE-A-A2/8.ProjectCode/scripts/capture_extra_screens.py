"""Extra documentation screens for ResQAI (15-18), captured from the running app with real data flowing through the real models.

Usage:  python scripts/capture_extra_screens.py [base_url]     (app must be running: run.bat; the demo account exists after capture_screens.py)
15 manual override form at the top of the page, 16 a Minor crash (logged only, no countdown), 17 a Moderate crash result with the
event log after the occupant cancels, 18 the signed-out landing page 'how it works' section is already 03, so 18 is the 404 page.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5302").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
DEMO = {"name": "Demo Responder", "email": "demo@resqai.test", "password": "ResQAI-demo-2026"}


def shot(page, name):
    page.wait_for_timeout(900)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


def main():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, geolocation={"latitude": 17.4126, "longitude": 78.4471}, permissions=["geolocation"])
        page = ctx.new_page()
        page.goto(BASE + "/login")
        page.get_by_label("Email").fill(DEMO["email"])
        page.get_by_label("Password", exact=True).fill(DEMO["password"])
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.wait_for_url("**/monitor")
        page.wait_for_selector("text=Sensor feed")
        page.evaluate("t => { document.documentElement.setAttribute('data-theme', t); localStorage.setItem('resqai.theme', t) }", "light")

        page.get_by_role("link", name="Manual override").first.click()
        page.get_by_label("Acc X (m/s²)").wait_for()
        page.evaluate("window.scrollTo(0, 0)")
        shot(page, "15_manual_form")

        page.get_by_role("link", name="Live monitor").first.click()
        page.wait_for_selector("text=Sensor feed")
        page.get_by_role("button", name="Normal driving", exact=True).click()
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Minor crash", exact=True).click()
        page.wait_for_selector("text=Accident probability")
        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo(0, 420)")
        shot(page, "16_monitor_minor_logged")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)
        for _ in range(6):  # the simulated moderate crash is rated Moderate in 60 of 60 trials; retry only guards against a click landing mid-render
            page.get_by_role("button", name="Moderate crash", exact=True).click()
            if page.get_by_role("dialog", name="Possible accident detected").count() or not page.wait_for_timeout(1500):
                if page.get_by_role("dialog", name="Possible accident detected").count():
                    break
        page.get_by_role("dialog", name="Possible accident detected").wait_for()
        page.get_by_role("button", name="I'm fine, cancel").click()
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 520)")
        shot(page, "17_monitor_moderate_cancelled")

        page.goto(BASE + "/no-such-page")
        page.wait_for_timeout(800)
        shot(page, "18_not_found")
        browser.close()


if __name__ == "__main__":
    main()
