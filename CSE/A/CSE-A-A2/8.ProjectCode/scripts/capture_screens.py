"""Walk every ResQAI screen with real data and save 1440x900 PNGs to docs/screenshots/.

Usage:  python scripts/capture_screens.py [base_url]     (app must be running: run.bat)
Also fails (exit 1) if the browser console shows errors, failed requests or 404s on assets.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5302").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
problems = []


def shot(page, name):
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


def set_theme(page, theme):
    page.evaluate("t => { document.documentElement.setAttribute('data-theme', t); localStorage.setItem('resqai.theme', t) }", theme)


def settle(page):
    """A Moderate/Severe result opens the confirmation countdown; answer it so the next click is not blocked."""
    page.wait_for_timeout(400)
    if page.get_by_role("dialog", name="Possible accident detected").count():
        page.get_by_role("button", name="I'm fine, cancel").click()
        page.wait_for_timeout(500)


def scenario(page, label):
    page.get_by_role("button", name=label, exact=True).click()
    page.wait_for_timeout(500)


def main():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            geolocation={"latitude": 17.4126, "longitude": 78.4471},
            permissions=["geolocation", "clipboard-read", "clipboard-write"],
        )
        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and problems.append(f"console error: {m.text}"))
        page.on("pageerror", lambda e: problems.append(f"page error: {e}"))
        page.on("response", lambda r: r.status >= 400 and problems.append(f"HTTP {r.status}: {r.url}"))

        # 01-02 landing, light and dark
        page.goto(BASE + "/")
        set_theme(page, "light")
        page.wait_for_selector("h1")
        shot(page, "01_landing_light")
        set_theme(page, "dark")
        shot(page, "02_landing_dark")
        page.evaluate("window.scrollTo(0, 1100)")
        shot(page, "03_landing_how_it_works")
        set_theme(page, "light")

        # 04 live monitor with a populated chart, result and log
        page.goto(BASE + "/monitor")
        page.wait_for_selector("text=Sensor feed")
        shot(page, "04_monitor_empty")
        for label in ("Normal driving", "Harsh brake", "Minor crash"):
            scenario(page, label)
            settle(page)
        page.get_by_role("button", name="Start live monitoring").click()
        page.wait_for_timeout(7000)
        settle(page)  # a live random reading may have started a countdown (which also pauses live mode)
        if page.get_by_role("button", name="Stop live monitoring").count():
            page.get_by_role("button", name="Stop live monitoring").click()
        shot(page, "05_monitor_live")

        # 06-07 confirmation countdown, then dispatched alert
        scenario(page, "Severe crash")
        page.get_by_role("dialog", name="Possible accident detected").wait_for()
        page.wait_for_timeout(3000)
        shot(page, "06_alert_countdown")
        page.get_by_role("button", name="Send alert now").click()
        page.get_by_role("dialog", name="Emergency alert dispatched").wait_for()
        shot(page, "07_alert_dispatched")
        page.get_by_role("button", name="View on map").click()

        # 08 response map after dispatch
        page.wait_for_selector(".leaflet-marker-icon")
        page.wait_for_timeout(1500)
        shot(page, "08_response_dispatched")

        # 09 manual override with a result
        page.goto(BASE + "/manual")
        page.get_by_label("Acc X (m/s²)").fill("32")
        page.get_by_label("Acc Y (m/s²)").fill("18")
        page.get_by_label("Speed change (km/h)").fill("-45")
        page.get_by_label("Jerk").fill("40")
        page.get_by_role("button", name="Run detection").click()
        page.wait_for_selector("text=Accident probability")
        settle(page)
        shot(page, "09_manual_result")

        # 10 dark-mode monitor
        page.goto(BASE + "/monitor")
        set_theme(page, "dark")
        scenario(page, "Normal driving")
        settle(page)
        shot(page, "10_monitor_dark")

        # 11 response map before any dispatch (fresh load)
        page.goto(BASE + "/response")
        page.wait_for_selector(".leaflet-marker-icon")
        page.wait_for_timeout(1500)
        shot(page, "11_response_directory_dark")
        browser.close()

    ignore = ("tile.openstreetmap.org",)  # third-party map tiles may be blocked offline
    real = [x for x in problems if not any(i in x for i in ignore)]
    if real:
        print("\nPROBLEMS:")
        for x in dict.fromkeys(real):
            print(" -", x)
        return 1
    print("\nConsole clean: no errors, no failed requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
