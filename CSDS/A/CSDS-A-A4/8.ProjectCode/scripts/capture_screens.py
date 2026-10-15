"""Capture the HubOptima screens for the project documents (needs the app running).

    python scripts/capture_screens.py            # web http://localhost:5104, API http://127.0.0.1:8104

Writes docs/screenshots/<nn>_<screen>.png at a 1440x900 viewport. Real data only: the planning screens
are filled by actually running the optimiser through the UI. Saved comparison / rolling / scalability
results in results/ are shown as they are - nothing here re-runs those long jobs.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
WEB = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5104"
OUT.mkdir(parents=True, exist_ok=True)


_n = [0]


def _name(name):
    _n[0] += 1
    return f"{_n[0]:02d}_{name}"


def shot(page, name, full=False, settle=1.2):
    time.sleep(settle)
    name = _name(name)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


def goto(page, route, wait=2.5):
    page.goto(WEB + route, wait_until="networkidle")
    time.sleep(wait)


def to_results(page):
    page.get_by_text("Plan for").first.evaluate("e => e.scrollIntoView({block: 'start'})")
    page.mouse.wheel(0, -90)


def run_plan(page, period, method="matheuristic", hubs=None, name="plan"):
    goto(page, "/app/plan", 1.5)
    page.select_option("select.select", period)
    if hubs:
        page.fill("input[type=number] >> nth=0", str(hubs))
    if method == "exact":
        page.get_by_text("Exact MIP (traditional)").click()
    else:
        page.get_by_text("Matheuristic (proposed)").first.click()
    page.get_by_role("button", name="Optimise network").click()
    page.wait_for_selector("text=Network map", timeout=240_000)
    time.sleep(4.5)                                   # let the celebration / count-ups finish
    page.evaluate("window.scrollTo(0, 0)")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        ctx.add_init_script("try{localStorage.setItem('theme','light')}catch(e){}")
        page = ctx.new_page()

        goto(page, "/", 8)                            # landing counters animate (count-up)
        shot(page, "landing")
        page.mouse.wheel(0, 900)
        shot(page, "landing_pipeline", settle=2)

        goto(page, "/app", 7)
        shot(page, "dashboard")
        shot(page, "dashboard_full", full=True, settle=0.5)

        goto(page, "/app/forecast", 5)
        shot(page, "forecast")
        shot(page, "forecast_full", full=True, settle=0.5)

        goto(page, "/app/regions", 3)
        shot(page, "regions")

        # planning: realised-demand month used in the report (October 2025, 6 hubs)
        run_plan(page, "2025-10", "matheuristic", 6)
        shot(page, "plan_parameters")
        to_results(page)
        shot(page, "plan_kpis", settle=1.5)
        shot(page, "plan_full", full=True, settle=0.5)
        kpi_map = page.get_by_text("Network map").first
        kpi_map.scroll_into_view_if_needed()
        shot(page, "plan_map", settle=1.5)
        page.get_by_text("Search log").first.scroll_into_view_if_needed()
        shot(page, "plan_searchlog", settle=1.0)

        # planning the next (forecast) month
        run_plan(page, "2026-01", "matheuristic", 6)
        to_results(page)
        shot(page, "plan_next_month", settle=1.5)

        # the traditional exact MIP on the same month, for the side-by-side
        run_plan(page, "2025-10", "exact", 6)
        to_results(page)
        shot(page, "plan_exact", settle=1.5)

        goto(page, "/app/compare", 5)
        shot(page, "compare")
        shot(page, "compare_full", full=True, settle=0.5)
        page.get_by_role("tab", name="Scalability").click()
        shot(page, "compare_scalability", settle=2.5)
        shot(page, "compare_scalability_full", full=True, settle=0.5)

        goto(page, "/app/rolling", 5)
        shot(page, "rolling")
        shot(page, "rolling_full", full=True, settle=0.5)

        # dark theme and a not-found route
        dark = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
        dp = dark.new_page()
        dp.goto(WEB + "/app", wait_until="networkidle")
        time.sleep(7)
        nm = _name("dashboard_dark")
        dp.screenshot(path=str(OUT / f"{nm}.png"))
        print("saved", nm)
        dp.goto(WEB + "/app/does-not-exist", wait_until="networkidle")
        time.sleep(2)
        nm = _name("not_found")
        dp.screenshot(path=str(OUT / f"{nm}.png"))
        print("saved", nm)
        browser.close()


if __name__ == "__main__":
    main()
