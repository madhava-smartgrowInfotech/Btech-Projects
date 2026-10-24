"""
Walk every LabLens screen in a real browser and save 1440x900 screenshots.

    python scripts/capture_screens.py [--base http://localhost:5308] [--out docs/screenshots]

Needs: pip install playwright && playwright install chromium
The app must be running (run.bat). The script signs in with the demo account, loads the synthetic
sample reports if the library is empty, and uploads one more generated PDF through the Upload screen
so that every screen shows real, processed data. Console errors, page errors and failed requests
are listed at the end (exit code 1 if there are any).
"""

import argparse
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEMO_EMAIL = "demo@lablens.com"
DEMO_PASSWORD = "Demo@1234"


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def scroll_through(page):
    """GSAP ScrollTrigger sections stay hidden until scrolled into view."""
    height = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < height:
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(120)
        y += 700
        height = page.evaluate("document.documentElement.scrollHeight")
    page.wait_for_timeout(400)
    # smooth-scroll (Lenis) ignores scrollTo: wheel back up instead
    while page.evaluate("window.scrollY") > 5:
        page.mouse.wheel(0, -1400)
        page.wait_for_timeout(120)
    page.wait_for_timeout(600)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:5308")
    ap.add_argument("--out", default=str(ROOT / "docs" / "screenshots"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    problems = []

    def shot(page, name, full=False):
        page.wait_for_timeout(900)
        path = out / f"{name}.png"
        page.screenshot(path=str(path), full_page=full)
        print("saved", path.name)

    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and problems.append(f"console: {m.text}"))
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on("response", lambda r: r.status >= 400 and r.status != 401 and problems.append(f"HTTP {r.status}: {r.url}"))

        # landing, dark then light
        page.goto(args.base + "/")
        page.wait_for_selector("h1")
        scroll_through(page)
        shot(page, "01_landing_dark")
        page.click("button[aria-label='Switch to light mode']")
        page.wait_for_timeout(500)
        shot(page, "02_landing_light")
        page.click("button[aria-label='Switch to dark mode']")

        # sign in
        page.goto(args.base + "/login")
        page.wait_for_selector("text=Sign in as demo user")
        shot(page, "03_login")
        page.fill("input[type=email]", DEMO_EMAIL)
        page.fill("input[type=password]", DEMO_PASSWORD)
        page.click("form button[type=submit]")
        page.wait_for_url("**/app")

        # empty library -> load the synthetic samples through the real pipeline
        page.wait_for_selector("h1:has-text('Dashboard')")
        page.wait_for_timeout(800)
        if page.locator("text=No reports uploaded yet").count():
            shot(page, "13_dashboard_empty_state")
            page.click("button:has-text('Load sample reports')")
            page.wait_for_selector("text=Recent reports", timeout=60000)

        # upload one more report through the UI
        sys.path.insert(0, str(ROOT / "backend"))
        from backend.demo_data import render_pdf  # noqa: E402
        from datetime import datetime  # noqa: E402

        pdf = Path(tempfile.mkdtemp()) / "Quarterly_Panel_Oct2026.pdf"
        pdf.write_bytes(render_pdf(4, datetime(2026, 10, 24)))
        page.goto(args.base + "/app/upload")
        page.wait_for_selector("input[type=file]", state="attached")
        shot(page, "05_upload_empty")
        page.set_input_files("input[type=file]", str(pdf))
        page.click("button:has-text('Process report')")
        page.wait_for_selector("text=Report processed successfully", timeout=60000)
        page.wait_for_selector(".toast", state="hidden", timeout=15000)
        shot(page, "06_upload_done", full=True)

        page.goto(args.base + "/app")
        page.wait_for_selector("text=Recent reports")
        shot(page, "04_dashboard")

        # the newest report is all-normal; show the August check-up, which has abnormal results and insights
        page.goto(args.base + "/app/analysis")
        page.wait_for_selector("select")
        aug = page.locator("select option", has_text="Health_Checkup_Aug2026").first.get_attribute("value")
        page.select_option("select", aug)
        page.wait_for_selector("text=Health insights for abnormal results", timeout=20000)
        shot(page, "07_report_analysis", full=True)

        page.goto(args.base + "/app/reports")
        page.wait_for_selector("button[aria-expanded]")
        page.locator("button[aria-expanded]").first.click()
        page.wait_for_selector("table", timeout=15000)
        shot(page, "08_my_reports")

        page.goto(args.base + "/app/trends")
        page.wait_for_selector(".recharts-line-dots circle", timeout=20000)  # dots appear when the draw animation ends
        shot(page, "09_health_trends", full=True)

        # compare the first and the latest check-up so the change column has something to show
        page.goto(args.base + "/app/compare")
        page.wait_for_selector("select")
        apr = page.locator("select option", has_text="Health_Checkup_Apr2026").first.get_attribute("value")
        oct_ = page.locator("select option", has_text="Health_Checkup_Oct2026").first.get_attribute("value")
        page.select_option("select >> nth=0", apr)
        page.select_option("select >> nth=1", oct_)
        page.wait_for_selector(".recharts-bar", timeout=20000)
        shot(page, "10_compare_reports", full=True)

        page.goto(args.base + "/app/insights")
        page.wait_for_selector(".insight-card", timeout=20000)
        shot(page, "11_health_insights", full=True)

        page.goto(args.base + "/app/about")
        page.wait_for_selector("text=Technology stack")
        shot(page, "12_about")

        browser.close()

    if problems:
        print("\nPROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        sys.exit(1)
    print("\nAll screens captured, console clean.")


if __name__ == "__main__":
    main()
