"""Extra documentation captures (servers must be running): an Established-profile case,
a validation-error case and full-page views. Output: docs/screenshots/13_..png onwards."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = "http://127.0.0.1:5409"

HIGH = {"age": "52", "workclass": "Private", "education": "Masters", "marital-status": "Married-civ-spouse",
        "occupation": "Exec-managerial", "relationship": "Husband", "race": "White", "sex": "Male",
        "native-country": "United-States", "capital-gain": "7688", "capital-loss": "0", "hours-per-week": "50"}
MID = {"age": "34", "workclass": "Local-gov", "education": "Some-college", "marital-status": "Married-civ-spouse",
       "occupation": "Sales", "relationship": "Wife", "race": "White", "sex": "Female",
       "native-country": "United-States", "capital-gain": "0", "capital-loss": "0", "hours-per-week": "42"}


def fill(page, prof):
    for k, v in prof.items():
        loc = page.locator(f"#assess-{k}")
        if k in ("age", "capital-gain", "capital-loss", "hours-per-week"):
            loc.fill(v)
        else:
            loc.select_option(v)


def settle(page, ms=1800):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)
    for b in page.get_by_role("button", name="Close").all():
        try:
            b.click(timeout=500)
        except Exception:
            pass
    page.wait_for_timeout(500)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        try:
            br = p.chromium.launch(channel="chrome")
        except Exception:
            br = p.chromium.launch()
        page = br.new_context(viewport={"width": 1440, "height": 900}).new_page()
        page.goto(BASE + "/login")
        page.wait_for_selector("#login-email")
        page.get_by_role("button", name="Use demo credentials").click()
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url("**/app")

        # 13: validation error (age out of range) on the assessment form
        page.goto(BASE + "/app/assess")
        page.wait_for_selector("#assess-age")
        fill(page, HIGH)
        page.locator("#assess-age").fill("7")
        page.get_by_role("button", name="Analyse my profile").click()
        page.wait_for_timeout(800)
        settle(page, 800)
        page.screenshot(path=str(OUT / "13_validation-error.png"))

        # 14/15: Established-profile case, viewport and full page
        fill(page, HIGH)
        page.get_by_role("button", name="Analyse my profile").click()
        page.wait_for_url("**/app/result")
        page.wait_for_selector("text=Strengthening factors")
        settle(page, 2200)
        page.screenshot(path=str(OUT / "14_result-established.png"))
        page.screenshot(path=str(OUT / "15_result-established-full.png"), full_page=True)

        # 16: Developing-profile case
        page.goto(BASE + "/app/assess")
        page.wait_for_selector("#assess-age")
        fill(page, MID)
        page.get_by_role("button", name="Analyse my profile").click()
        page.wait_for_url("**/app/result")
        page.wait_for_selector("text=Strengthening factors")
        settle(page, 2200)
        page.screenshot(path=str(OUT / "16_result-developing.png"))

        # 17-19: full-page explainability, forecast and performance
        for route, wait, name in [("explain", "text=Ranked features", "17_explainability-full"),
                                  ("forecast", "text=Forecast values", "18_forecast-full"),
                                  ("performance", "text=Statistical analysis", "19_performance-full")]:
            page.goto(f"{BASE}/app/{route}")
            page.wait_for_selector(wait)
            settle(page, 2200)
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
        br.close()
    print("done")


if __name__ == "__main__":
    sys.exit(main())
