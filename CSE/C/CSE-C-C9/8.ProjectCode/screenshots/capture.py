"""Capture real FinSight AI screenshots via Playwright."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"
OUT = "screenshots"
FORM = {
    "age": "39", "workclass": "State-gov", "education": "Bachelors",
    "marital-status": "Never-married", "occupation": "Adm-clerical",
    "relationship": "Not-in-family", "race": "White", "sex": "Male",
    "native-country": "United-States", "capital-gain": "2174",
    "capital-loss": "0", "hours-per-week": "40",
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1366, "height": 900})
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.screenshot(path=f"{OUT}/01_dashboard.png", full_page=True)
    print("01 ok")
    pg.goto(BASE + "/assess", wait_until="networkidle")
    pg.screenshot(path=f"{OUT}/02_assess.png", full_page=True)
    print("02 ok")
    for k, v in FORM.items():
        el = pg.locator(f'[name="{k}"]')
        if el.get_attribute("type") == "number":
            el.fill(v)
        else:
            el.select_option(v)
    pg.locator('form button[type="submit"]').click()
    pg.wait_for_timeout(2500)
    pg.screenshot(path=f"{OUT}/03_result.png", full_page=True)
    print("03 ok", pg.url)
    pg.goto(BASE + "/explain", wait_until="networkidle")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=f"{OUT}/04_explain.png", full_page=True)
    print("04 ok")
    pg.goto(BASE + "/forecast", wait_until="networkidle")
    pg.wait_for_timeout(2500)
    pg.screenshot(path=f"{OUT}/05_forecast.png", full_page=True)
    print("05 ok")
    pg.goto(BASE + "/whatif", wait_until="networkidle")
    for k, v in FORM.items():
        el = pg.locator(f'[name="{k}"]')
        try:
            if el.get_attribute("type") == "number":
                el.fill(v)
            else:
                el.select_option(v)
        except Exception:
            pass
    pg.locator('[name="scenario_capital_gain"]').fill("20000")
    pg.locator('[name="scenario_hours"]').fill("50")
    pg.locator('form button[type="submit"]').click()
    pg.wait_for_timeout(2500)
    pg.screenshot(path=f"{OUT}/06_whatif.png", full_page=True)
    print("06 ok")
    pg.goto(BASE + "/performance", wait_until="networkidle")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=f"{OUT}/07_performance.png", full_page=True)
    print("07 ok")
    b.close()
print("done")
