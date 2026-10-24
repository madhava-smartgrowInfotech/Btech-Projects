"""Walks every FlowSense screen in a real browser, puts real data on it and saves 1440x900 screenshots.

Usage:  python scripts/capture_screens.py [frontend_url]     (backend + frontend must be running: run.bat)
Needs:  pip install playwright   (uses the installed Chrome; or `playwright install chromium` and set CHANNEL=)
Output: docs/screenshots/<nn>_<screen>.png  - and a list of any console errors / failed requests it saw.
"""
from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5310").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
CHANNEL = os.environ.get("CHANNEL", "chrome")
problems: list[str] = []


def shot(page, name, scroll=0):
    page.evaluate(f"window.scrollTo(0, {scroll})")
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


def wait_backend():
    for _ in range(90):
        try:
            with urllib.request.urlopen(BASE + "/api/health", timeout=3) as r:
                if b'"predictor_ready":true' in r.read():
                    return
        except Exception:
            pass
        import time
        time.sleep(1)
    raise SystemExit("backend/frontend not ready - start run.bat first")


def main():
    wait_backend()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=CHANNEL, headless=True) if CHANNEL else p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
        page = ctx.new_page()
        page.on("console", lambda m: problems.append(f"[console {m.type}] {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: problems.append(f"[pageerror] {e}"))
        page.on("response", lambda r: problems.append(f"[http {r.status}] {r.url}") if r.status >= 400 and "/api/auth/login" not in r.url else None)

        # ---- landing, dark then light
        page.goto(BASE + "/")
        page.wait_for_timeout(4500)
        shot(page, "01_landing_dark")
        shot(page, "02_landing_features_dark", 900)
        page.evaluate("localStorage.setItem('fs_theme','light')")
        page.reload()
        page.wait_for_timeout(4500)
        shot(page, "03_landing_light")
        page.evaluate("localStorage.setItem('fs_theme','dark')")

        # ---- sign in with the demo account
        page.goto(BASE + "/login")
        page.wait_for_timeout(800)
        shot(page, "04_login")
        page.get_by_role("button", name="Use demo account").click()
        page.wait_for_url("**/app", timeout=15000)
        page.wait_for_timeout(1500)

        # ---- live control: fresh sim, 5 min of traffic, an ambulance
        page.get_by_role("button", name="Reset").click()
        page.wait_for_timeout(1200)
        page.get_by_label("Signal controller").select_option("advanced")
        page.get_by_role("button", name="Skip 5 min").click()
        page.wait_for_timeout(2500)
        page.get_by_role("button", name="Send ambulance").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Run live (60 s)").click()
        page.wait_for_timeout(2500)
        shot(page, "05_live_control")
        page.get_by_role("button", name="Stop").click()
        page.wait_for_timeout(1500)
        shot(page, "06_live_map_and_status", 560)

        # ---- benchmark: run it, then the demand sweep
        page.goto(BASE + "/app/benchmark")
        page.wait_for_timeout(1200)
        page.get_by_role("button", name="Run benchmark").first.click()
        page.get_by_text("Delay vs fixed-time", exact=True).wait_for(timeout=120000)
        page.wait_for_timeout(1500)
        shot(page, "07_benchmark")
        shot(page, "08_benchmark_charts", 520)
        page.get_by_role("button", name="Run demand sweep").click()
        page.get_by_role("figure", name="Average delay against demand").wait_for(timeout=120000)
        page.wait_for_timeout(1200)
        page.get_by_role("figure", name="Average delay against demand").scroll_into_view_if_needed()
        shot(page, "09_benchmark_sweep", page.evaluate("window.scrollY"))

        # ---- vision: synthetic, then YOLOv8 on the sample photo
        page.goto(BASE + "/app/vision")
        page.wait_for_timeout(2500)
        shot(page, "10_vision_synthetic")
        shot(page, "11_vision_density", 560)
        page.get_by_role("tab", name="YOLOv8 · sample photo").click()
        try:
            page.get_by_text("Vehicles detected", exact=True).first.wait_for(timeout=90000)
        except PWTimeout:
            print("YOLO sample did not finish (is ultralytics installed / online?)")
        page.wait_for_timeout(1500)
        shot(page, "12_vision_yolo")

        # ---- prediction
        page.goto(BASE + "/app/prediction")
        page.wait_for_timeout(3500)
        shot(page, "13_prediction")
        shot(page, "14_prediction_forecast", 900)

        # ---- violations: more simulated time on a fixed-time controller so there is plenty to show
        page.goto(BASE + "/app")
        page.wait_for_timeout(1000)
        page.get_by_label("Signal controller").select_option("fixed")
        page.wait_for_timeout(800)
        page.goto(BASE + "/app/violations")
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Simulate 10 more minutes").first.click()
        page.get_by_text("Evidence log", exact=True).wait_for(timeout=60000)
        page.wait_for_timeout(1500)
        shot(page, "15_violations")
        shot(page, "16_violations_log", 560)

        # ---- about
        page.goto(BASE + "/app/about")
        page.wait_for_timeout(1800)
        shot(page, "17_about")
        shot(page, "18_about_pipeline", 560)

        # ---- one dark-mode app screen in light theme
        page.evaluate("localStorage.setItem('fs_theme','light')")
        page.goto(BASE + "/app")
        page.wait_for_timeout(2500)
        shot(page, "19_live_control_light")

        browser.close()
    print("\nconsole / network problems:" if problems else "\nno console or network problems")
    for x in dict.fromkeys(problems):
        print("  ", x)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
