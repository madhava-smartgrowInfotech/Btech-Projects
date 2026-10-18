"""Extra screenshots for Appendix C: dark theme, tablet and phone layouts (real data, same running app).

    python scripts/capture_extra.py [base_url]       # needs the API and the web app running with data loaded and a saved model

Writes docs/screenshots/17_dashboard_dark.png, 18_risk_tablet.png, 19_customer360_phone.png, 20_dashboard_phone.png
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5314").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
problems = []


def launch(p):
    try:
        return p.chromium.launch(channel="chrome", headless=True)
    except Exception:
        return p.chromium.launch(headless=True)


def new_page(browser, w, h, scheme):
    ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, device_scale_factor=1)
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and problems.append(f"console error: {m.text}"))
    page.on("pageerror", lambda e: problems.append(f"page error: {e}"))
    page.goto(BASE + "/login")
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="One-click demo sign in").click()
    page.wait_for_url("**/app")
    page.wait_for_load_state("networkidle")
    return page


def shot(page, name, wait=2500):
    for b in page.get_by_role("button", name="Dismiss notification").all():
        b.click()
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


with sync_playwright() as p:
    br = launch(p)
    pg = new_page(br, 1440, 900, "dark")
    pg.goto(BASE + "/app")
    pg.get_by_role("heading", name="Customers most at risk").wait_for(timeout=60000)
    shot(pg, "17_dashboard_dark")
    pg = new_page(br, 768, 1024, "light")
    pg.goto(BASE + "/app/risk")
    pg.get_by_role("heading", name="At-risk customer table").wait_for(timeout=60000)
    shot(pg, "18_risk_tablet")
    pg = new_page(br, 360, 780, "light")
    pg.goto(BASE + "/app/customer")
    pg.wait_for_load_state("networkidle")
    shot(pg, "19_customer360_phone", 3500)
    pg.goto(BASE + "/app")
    pg.get_by_role("heading", name="Customers most at risk").wait_for(timeout=60000)
    shot(pg, "20_dashboard_phone")
    br.close()
print("problems:", problems or "none")
