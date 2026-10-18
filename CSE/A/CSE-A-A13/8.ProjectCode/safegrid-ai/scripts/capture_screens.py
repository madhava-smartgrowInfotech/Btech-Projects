"""Capture a 1440x900 screenshot of every screen with real data on it.

Needs the backend (8313) and the frontend (5313) running, plus:  pip install playwright && playwright install chromium
Usage:  python scripts/capture_screens.py [frontend_url]
Output: docs/screenshots/<nn>_<screen>.png
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5313").rstrip("/")
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = {"width": 1440, "height": 900}


def shot(page, name, full=False):
    page.wait_for_timeout(2400)  # let chart animations settle
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


with sync_playwright() as p:
    try:
        browser = p.chromium.launch()
    except Exception:
        browser = p.chromium.launch(channel="chrome")

    # landing page in both colour schemes
    for scheme in ("dark", "light"):
        ctx = browser.new_context(viewport=SIZE, color_scheme=scheme)
        pg = ctx.new_page()
        pg.goto(BASE + "/")
        pg.wait_for_timeout(2500)
        shot(pg, f"01_landing_{scheme}")
        if scheme == "dark":
            pg.mouse.wheel(0, 1900)
            pg.wait_for_timeout(1200)
            shot(pg, "02_landing_how_it_works")
        ctx.close()

    ctx = browser.new_context(viewport=SIZE, color_scheme="dark")
    page = ctx.new_page()
    page.goto(BASE + "/login")
    shot(page, "03_login")
    page.get_by_role("button", name="Continue with the demo account").click()
    page.wait_for_url("**/app")
    page.wait_for_timeout(1200)

    # put real data on every screen: play the unsafe-action scenario to the end
    page.get_by_label("Scenario").select_option("unsafe_ai_action")
    page.get_by_label("Playback").select_option("0")
    page.get_by_role("button", name="Reset").click()  # always begin from step 0, whatever state the backend is in
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Start").click()
    page.get_by_text("Run finished").wait_for(timeout=60000)
    page.wait_for_timeout(800)
    shot(page, "04_dashboard")

    page.goto(BASE + "/app/grid"); shot(page, "05_grid_view")
    page.goto(BASE + "/app/agents"); shot(page, "06_agent_monitor")

    page.goto(BASE + "/app/shield")
    page.wait_for_timeout(1000)
    page.get_by_role("button", name="Validate").click()
    page.wait_for_timeout(1200)
    page.mouse.wheel(0, 700)
    shot(page, "07_safety_shield")

    page.goto(BASE + "/app/power-flow"); shot(page, "08_power_flow")

    page.goto(BASE + "/app/scenarios")
    page.wait_for_timeout(800)
    page.get_by_role("button", name="Run comparison").click()
    page.get_by_text("Mean of each metric", exact=False).wait_for(state="attached", timeout=300000)
    page.wait_for_timeout(1000)
    page.get_by_role("button", name="Run comparison").scroll_into_view_if_needed()
    page.mouse.wheel(0, 900)
    shot(page, "09_scenarios")

    page.goto(BASE + "/app/explain"); shot(page, "10_explainability")
    browser.close()
