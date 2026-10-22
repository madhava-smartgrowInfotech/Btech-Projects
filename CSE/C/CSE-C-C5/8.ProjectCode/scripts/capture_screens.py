"""Capture 1440x900 screenshots of every screen with real data on it.

Needs both servers running (run.bat). One-time setup:  pip install playwright  (uses the installed Chrome;
or `playwright install chromium`).  Usage:  python scripts/capture_screens.py
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
PORT = os.environ.get("FRONTEND_PORT", "5405")
BASE = f"http://localhost:{PORT}"
os.makedirs(OUT, exist_ok=True)


def shot(page, name):
    page.wait_for_timeout(700)
    path = os.path.join(OUT, name + ".png")
    page.screenshot(path=path)
    print("saved", path)


def landing(page, name):
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(4200)  # headline typing + terminal log
    shot(page, name)


def launch(p):
    try:
        return p.chromium.launch(channel="chrome", headless=True)
    except Exception:
        return p.chromium.launch(headless=True)


with sync_playwright() as p:
    b = launch(p)
    for scheme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
        page = ctx.new_page()
        landing(page, f"01_landing_{scheme}")
        if scheme == "light":
            ctx.close()
            continue

        # Eligibility with a real prediction
        page.goto(BASE + "/predict?company=Microsoft", wait_until="networkidle")
        page.fill("#f-cgpa", "8.4"); page.fill("#f-aptitude", "84"); page.fill("#f-technical", "79")
        page.fill("#f-internships", "1"); page.fill("#f-projects", "3")
        page.get_by_role("button", name="Run prediction").click()
        page.get_by_text("Profile vs company cutoffs").wait_for()
        page.wait_for_timeout(1200)
        shot(page, "02_predict")

        # Recommendations for a student below the dream company's cutoff
        page.goto(BASE + "/recommend", wait_until="networkidle")
        page.get_by_role("button", name="Recommend", exact=True).click()
        page.get_by_text("Ranked alternatives").wait_for(timeout=30000)
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 430)")
        shot(page, "03_recommend")

        # Officer dashboard: overview + SHAP tab
        page.goto(BASE + "/dashboard", wait_until="networkidle")
        page.wait_for_timeout(1800)
        shot(page, "04_dashboard")
        page.get_by_role("tab", name="SHAP importance").click()
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, 560)")
        shot(page, "05_dashboard_shap")

        # Recruiter shortlist
        page.goto(BASE + "/recruiter", wait_until="networkidle")
        page.get_by_role("button", name="Filter").click()
        page.wait_for_timeout(1500)
        shot(page, "06_recruiter")

        # Companies
        page.goto(BASE + "/companies", wait_until="networkidle")
        page.wait_for_timeout(1000)
        shot(page, "07_companies")

        # Command palette + activity log (real API calls from this session)
        page.keyboard.press("/")
        page.keyboard.type("hyd")
        page.wait_for_timeout(600)
        shot(page, "08_command_palette")
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        page.keyboard.press("g"); page.keyboard.press("l")
        page.wait_for_timeout(800)
        shot(page, "09_activity_log")
        ctx.close()
    b.close()
print("done")
