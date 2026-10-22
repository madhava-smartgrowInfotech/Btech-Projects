"""Capture real VenturePulse screenshots with Playwright."""
import time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
OUT = "screenshots"

PAGES = [
    ("dashboard", f"{BASE}/", "01-dashboard.png", None),
    ("predict", f"{BASE}/predict", "02-predict-form.png", None),
    ("performance", f"{BASE}/performance", "04-model-performance.png", None),
    ("insights", f"{BASE}/insights", "05-insights.png", None),
]

DESC = ("A subscription analytics platform for small retailers using demand forecasting, "
        "with 40 paying stores, growing monthly revenue and partnerships with two distributors.")

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    for name, url, fname, _ in PAGES:
        pg.goto(url, wait_until="networkidle", timeout=60000)
        time.sleep(1)
        pg.screenshot(path=f"{OUT}/{fname}", full_page=True)
        print("saved", fname)
    # prediction result flow
    pg.goto(f"{BASE}/predict", wait_until="networkidle", timeout=60000)
    pg.fill('textarea[name="description"]', DESC)
    pg.fill('input[name="funding_total_usd"]', "2500000")
    pg.check('input[name="has_VC"]')
    pg.check('input[name="has_roundA"]')
    pg.click('button[type="submit"]')
    pg.wait_for_load_state("networkidle", timeout=60000)
    time.sleep(1)
    pg.screenshot(path=f"{OUT}/03-prediction-result.png", full_page=True)
    print("saved 03-prediction-result.png")
    # similar-startups close-up: scroll to table
    try:
        pg.evaluate("document.querySelector('table.tbl').scrollIntoView()")
        time.sleep(0.5)
        pg.screenshot(path=f"{OUT}/06-similar-startups.png")
        print("saved 06-similar-startups.png")
    except Exception as e:
        print("similar close-up skipped:", e)
    b.close()
print("done")
