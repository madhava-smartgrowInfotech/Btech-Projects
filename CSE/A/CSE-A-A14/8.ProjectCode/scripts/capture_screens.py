"""Walk every screen of the running app with real data and save 1440x900 PNGs.

Needs the API (8314) and the frontend (5314) running, e.g. via run.bat.
    pip install playwright   (and `playwright install chromium` once, unless Chrome is installed)
    python scripts/capture_screens.py [base_url]

Output: docs/screenshots/<nn>_<screen>.png. Exits 1 if the console shows errors or any request fails.
"""
import os
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5314").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
problems = []


def launch(p):
    try:
        return p.chromium.launch(channel="chrome", headless=True)
    except Exception:
        return p.chromium.launch(headless=True)


def settle(page, ms=1400):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def scroll_to(locator, offset=96):
    """Bring an element near the top of the viewport (below the sticky top bar)."""
    locator.evaluate(f"e => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - {offset})")


def shot(page, name):
    for b in page.get_by_role("button", name="Dismiss notification").all():
        b.click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


def scroll_through(page):
    """Trigger scroll-based reveals on the landing page, then return to the top."""
    h = page.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h, 500):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(120)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def main():
    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and problems.append(f"console error: {m.text}"))
        page.on("pageerror", lambda e: problems.append(f"page error: {e}"))
        page.on("requestfailed", lambda r: problems.append(f"request failed: {r.url} {r.failure}"))
        page.on("response", lambda r: r.status >= 400 and r.status != 409 and problems.append(f"HTTP {r.status}: {r.url}"))

        # --- landing, light then dark
        page.goto(BASE + "/")
        settle(page)
        scroll_through(page)
        shot(page, "01_landing_light")
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(700)
        scroll_through(page)
        shot(page, "02_landing_dark")
        page.get_by_role("button", name="Switch to light mode").click()

        # --- sign in with the demo account
        page.goto(BASE + "/login")
        settle(page, 800)
        shot(page, "03_login")
        page.get_by_role("button", name="One-click demo sign in").click()
        page.wait_for_url("**/app")
        settle(page, 800)

        # --- quick start (sample data -> prepare -> train -> save) when the workspace is empty
        qs = page.get_by_role("button", name="Quick start with sample data")
        if qs.count():
            qs.first.click()
        page.get_by_role("heading", name="Customers most at risk").wait_for(timeout=120000)
        settle(page, 2200)
        shot(page, "04_dashboard")

        token = page.evaluate("localStorage.getItem('churniq-token')")
        auth = {"Authorization": f"Bearer {token}"}
        tmp = Path(tempfile.mkdtemp())
        tpl = tmp / "sample_batch.csv"
        tpl.write_bytes(page.request.get(BASE + "/api/batch/template", headers=auth).body())

        # --- data
        page.goto(BASE + "/app/data")
        page.get_by_role("heading", name="Dataset preview").wait_for()
        settle(page, 900)
        scroll_to(page.get_by_role("heading", name="3. Data quality report"))
        page.wait_for_timeout(2000)
        shot(page, "05_data")

        # --- exploration
        page.goto(BASE + "/app/eda")
        page.get_by_role("heading", name="Churn rate by customer attribute").wait_for()
        settle(page, 1800)
        shot(page, "06_explore")

        # --- training (retrain to show a fresh comparison)
        page.goto(BASE + "/app/train")
        page.get_by_role("button", name="Train models").click()
        page.get_by_role("heading", name="Model comparison").wait_for(timeout=120000)
        scroll_to(page.get_by_role("heading", name="Model comparison"))
        settle(page, 1200)
        shot(page, "07_train")

        # --- evaluation
        page.goto(BASE + "/app/evaluation")
        page.get_by_role("heading", name="ROC curves").wait_for()
        settle(page, 1800)
        shot(page, "08_evaluation")

        # --- risk
        page.goto(BASE + "/app/risk")
        page.get_by_role("heading", name="At-risk customer table").wait_for()
        settle(page, 1800)
        shot(page, "09_risk")

        # --- customer 360
        page.goto(BASE + "/app/customer")
        page.get_by_role("heading", name="Top churn drivers").first.wait_for()
        settle(page, 1800)
        shot(page, "10_customer360")

        # --- explain
        page.goto(BASE + "/app/explain")
        page.get_by_role("heading", name="Global explanation").wait_for()
        settle(page, 2200)
        shot(page, "11_explain")

        # --- what-if (change the contract to show a real delta)
        page.goto(BASE + "/app/whatif")
        page.get_by_role("heading", name="Scenario result").wait_for()
        settle(page, 1000)
        sel = page.locator("select#wi-Contract")
        sel.select_option("Two year")
        page.wait_for_timeout(1500)
        scroll_to(page.get_by_role("heading", name="Scenario result"), 140)
        page.wait_for_timeout(1500)
        shot(page, "12_whatif")

        # --- retention
        page.goto(BASE + "/app/retention")
        page.get_by_role("heading", name="Suggested actions").first.wait_for()
        settle(page, 1200)
        shot(page, "13_retention")

        # --- batch
        page.goto(BASE + "/app/batch")
        page.locator("input[type=file]").set_input_files(str(tpl))
        page.get_by_role("button", name="Run batch prediction").click()
        page.get_by_text("Customers scored", exact=True).wait_for(timeout=60000)
        settle(page, 1500)
        scroll_to(page.get_by_text("Customers scored", exact=True), 140)
        page.wait_for_timeout(1800)
        shot(page, "14_batch")

        # --- monitoring
        page.goto(BASE + "/app/monitoring")
        page.get_by_role("heading", name="Data drift check").wait_for()
        page.locator("input[type=file]").set_input_files(str(tpl))
        page.get_by_role("button", name="Compare with training data").click()
        page.get_by_text("Training mean").first.wait_for(timeout=60000)
        scroll_to(page.get_by_role("heading", name="Data drift check"))
        settle(page, 1200)
        shot(page, "15_monitoring")

        # --- about
        page.goto(BASE + "/app/about")
        page.get_by_role("heading", name="System architecture").wait_for()
        scroll_through(page)
        settle(page, 800)
        shot(page, "16_about")

        browser.close()

    ignore = ("net::ERR_ABORTED",)
    real = [x for x in problems if not any(i in x for i in ignore)]
    if real:
        print("\nPROBLEMS:")
        for x in dict.fromkeys(real):
            print(" -", x)
        sys.exit(1)
    print("\nAll screens captured with a clean console.")


if __name__ == "__main__":
    os.environ.setdefault("MSYS_NO_PATHCONV", "1")
    main()
