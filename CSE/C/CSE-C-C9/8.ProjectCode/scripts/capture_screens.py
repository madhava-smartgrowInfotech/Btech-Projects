"""Walk every screen of the running app, put real data on it and save 1440x900 PNGs.

Servers must be running (run.bat). Output: docs/screenshots/<nn>_<screen-name>.png
The same walk records console errors, page errors and failed/404 requests and exits
non-zero if it sees any, so it doubles as a console-clean check.

Usage:  python scripts/capture_screens.py [--base http://127.0.0.1:5409]
"""
import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"

PROFILE = {
    "age": "39", "workclass": "State-gov", "education": "Bachelors",
    "marital-status": "Never-married", "occupation": "Adm-clerical",
    "relationship": "Not-in-family", "race": "White", "sex": "Male",
    "native-country": "United-States", "capital-gain": "2174",
    "capital-loss": "0", "hours-per-week": "40",
}


def fill_profile(page, prefix):
    for key, val in PROFILE.items():
        sel = page.locator(f"#{prefix}-{key}")
        if key in ("age", "capital-gain", "capital-loss", "hours-per-week"):
            sel.fill(val)
        else:
            sel.select_option(val)


def launch(p):
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5409")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    OUT.mkdir(parents=True, exist_ok=True)
    problems = []

    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text} @ {page.url}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e} @ {page.url}"))
        page.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url}"))
        page.on("response", lambda r: problems.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 else None)

        def shot(name):
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)  # let entry animations and count-ups settle
            path = OUT / f"{name}.png"
            page.screenshot(path=str(path))
            print("saved", path.relative_to(ROOT))

        # 01/02 landing, light then dark (toggle, then reload to prove it persisted)
        page.goto(base + "/")
        page.evaluate("localStorage.setItem('finsight-theme','light')")
        page.reload()
        shot("01_landing-light")
        page.get_by_role("button", name="Switch to dark mode").click()
        page.reload()
        assert page.evaluate("document.documentElement.dataset.theme") == "dark", "dark mode did not persist"
        shot("02_landing-dark")
        page.get_by_role("button", name="Switch to light mode").click()

        # 03 login (sample account), then sign in through the UI; a guarded URL must redirect here first
        page.evaluate("localStorage.removeItem('finsight-auth')")
        page.goto(base + "/app/forecast")
        page.wait_for_url("**/login")
        page.wait_for_selector("#login-email")
        shot("03_login")
        page.get_by_role("button", name="Use demo credentials").click()
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url("**/app/forecast")  # returned to the page that was asked for
        page.wait_for_selector("text=Forecast values")

        # 04 dashboard
        page.goto(base + "/app")
        shot("04_dashboard")

        # 05 assessment form, filled with the sample profile; 06 result after a real analysis
        page.goto(base + "/app/assess")
        page.wait_for_selector("#assess-age")
        fill_profile(page, "assess")
        shot("05_assessment")
        page.get_by_role("button", name="Analyse my profile").click()
        page.wait_for_url("**/app/result")
        page.wait_for_selector("text=Strengthening factors")
        shot("06_result")

        # 07 explainability, 08 forecast
        page.goto(base + "/app/explain")
        page.wait_for_selector("text=Ranked features")
        shot("07_explainability")
        page.goto(base + "/app/forecast")
        page.wait_for_selector("text=Forecast values")
        shot("08_forecast")

        # 09 what-if: baseline is prefilled from the assessment; change two scenario fields
        page.goto(base + "/app/whatif")
        page.wait_for_selector("#wi-age")
        assert page.locator("#wi-age").input_value() == PROFILE["age"], "what-if baseline was not prefilled"
        page.locator("#wi-sg").fill("80000")
        page.locator("#wi-sh").fill("50")
        page.get_by_role("button", name="Compare scenarios").click()
        page.wait_for_selector("text=Change in score")
        shot("09_whatif")

        # 10 performance, 11 about, 12 not-found
        page.goto(base + "/app/performance")
        page.wait_for_selector("text=Statistical analysis")
        shot("10_performance")
        page.goto(base + "/app/about")
        shot("11_about")
        page.goto(base + "/app/does-not-exist")
        page.wait_for_selector("text=Page not found")
        shot("12_not-found")

        browser.close()

    if problems:
        print("\nCONSOLE / NETWORK PROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        return 1
    print("\nConsole clean: no errors, warnings, page errors or failed requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
