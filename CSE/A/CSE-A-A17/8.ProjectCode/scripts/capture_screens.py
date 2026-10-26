"""
capture_screens.py
-------------------
Drives the real UI end to end against a running app (frontend 5317, backend 8317), puts real data on every
screen and saves a 1440x900 PNG per screen to docs/screenshots/<nn>_<screen-name>.png.
Also reports console errors, page errors, and failed requests seen along the way.

    python scripts/capture_screens.py [--url http://localhost:5317] [--data data/real_hm] [--rows 0] [--tune]

There is no login in this product. Needs: pip install playwright (uses the installed Chrome, or
`playwright install chromium`). H&M-shaped CSVs come from `python scripts/make_sample_data.py`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:5317")
    ap.add_argument("--data", default=str(ROOT / "data" / "real_hm"))
    ap.add_argument("--tune", action="store_true", help="also exercise hyperparameter tuning (slower)")
    ap.add_argument("--rows", type=int, default=200000, help="value for 'Max transaction rows to load' (0 = no limit)")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    data = Path(args.data)
    OUT.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page: Page = ctx.new_page()

        page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on("response", lambda r: problems.append(f"HTTP {r.status} {r.url}") if r.status >= 400 else None)
        page.on("requestfailed", lambda r: problems.append(f"requestfailed {r.url} {r.failure}"))

        def goto(path: str) -> None:
            page.goto(base + path, wait_until="load")
            page.wait_for_timeout(900)  # let entrance animations settle

        def shot(name: str, scroll_to: str | None = None) -> None:
            if scroll_to:
                page.locator(scroll_to).first.scroll_into_view_if_needed()
                page.evaluate("window.scrollBy(0, -80)")
                page.wait_for_timeout(700)
            else:
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(300)
            path = OUT / f"{name}.png"
            page.screenshot(path=str(path))
            print("saved", path.relative_to(ROOT))

        def click_name(name: str, exact: bool = False) -> None:
            page.get_by_role("button", name=name, exact=exact).click()

        # ---- landing, light and dark ------------------------------------
        goto("/")
        shot("01_landing-light")
        # scroll through so scroll-triggered reveals are rendered, then back to top
        for y in range(0, 4200, 700):
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(250)
        shot("02_landing-light-features", scroll_to="#features")
        page.evaluate("window.scrollTo(0, 0)")
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(500)
        shot("03_landing-dark")
        shot("04_landing-dark-features", scroll_to="#features")
        page.get_by_role("button", name="Switch to light mode").click()

        # ---- upload ------------------------------------------------------
        goto("/app/upload")
        # a chosen file replaces its drop zone, so the next required input is always the first one left
        page.locator('input[type="file"]').first.set_input_files(str(data / "transactions_train.csv"))
        page.locator('input[type="file"]').first.set_input_files(str(data / "articles.csv"))
        if (data / "customers.csv").exists():  # optional third file
            page.locator('input[type="file"]').first.set_input_files(str(data / "customers.csv"))
        page.get_by_label("Max transaction rows to load").fill(str(args.rows))
        shot("05_upload-files-chosen")
        click_name("Load & process data")
        page.get_by_role("heading", name="Data quality report").wait_for(timeout=300000)
        page.wait_for_timeout(2200)  # count-up numbers
        shot("06_upload-quality-report")

        # ---- explore -----------------------------------------------------
        goto("/app/explore")
        page.get_by_text("Daily total demand").first.wait_for(timeout=60000)
        page.wait_for_timeout(1500)
        shot("07_explore")
        shot("08_explore-categories", scroll_to="text=Demand by department")

        # ---- demand ------------------------------------------------------
        goto("/app/demand")
        page.get_by_text("Aggregated daily demand").first.wait_for(timeout=60000)
        shot("09_demand")

        # ---- features ----------------------------------------------------
        goto("/app/features")
        shot("10_features-empty")
        click_name("Build feature table")
        page.get_by_text("Model input features").wait_for(timeout=300000)
        page.wait_for_timeout(1800)
        shot("11_features-built")

        # ---- training ----------------------------------------------------
        goto("/app/training")
        click_name("Run moving-average baseline")
        page.get_by_text("Moving Average: test metrics").wait_for(timeout=120000)
        click_name("Train XGBoost")
        page.get_by_text("XGBoost: test metrics").wait_for(timeout=300000)
        page.wait_for_timeout(1800)
        shot("12_training")
        shot("13_training-comparison", scroll_to="text=Comparison so far")
        if args.tune:
            page.get_by_label("Run hyperparameter tuning (slower, more accurate)").check()
            click_name("Train XGBoost")
            page.get_by_text("Best parameters found").wait_for(timeout=600000)
            shot("13b_training-tuned", scroll_to="text=Best parameters found")

        # ---- domain adaptation --------------------------------------------
        goto("/app/domain")
        page.get_by_label("Source domain value").wait_for(timeout=30000)
        shot("14_domain-form")
        click_name("Run shift analysis & adaptation")
        page.get_by_text("Before vs after adaptation").first.wait_for(timeout=600000)
        page.wait_for_timeout(1800)
        shot("15_domain-shift")
        shot("16_domain-before-after", scroll_to="text=Before vs after adaptation")

        # ---- evaluation ----------------------------------------------------
        goto("/app/evaluation")
        page.get_by_text("Feature importance").first.wait_for(timeout=60000)
        page.wait_for_timeout(1500)
        shot("17_evaluation")
        shot("18_evaluation-importance", scroll_to="text=Feature importance (XGBoost, top 20)")

        # ---- forecast -------------------------------------------------------
        goto("/app/forecast")
        page.get_by_text("Forecast settings").wait_for(timeout=60000)
        page.get_by_role("tab", name="14 days").click()
        click_name("Generate forecast")
        page.get_by_text("History and forecast").wait_for(timeout=120000)
        page.wait_for_timeout(1800)
        shot("19_forecast")
        shot("20_forecast-table", scroll_to="text=Forecast table")

        # ---- AI insights ------------------------------------------------------
        goto("/app/insights")
        page.get_by_label("Your question").fill("Which features matter most, and why?")
        click_name("Get AI explanation")
        try:
            page.get_by_text("Generated by Gemini").wait_for(timeout=90000)
        except Exception:
            problems.append("AI insights: no answer rendered within 90 s")
        shot("21_insights")

        # ---- overview + about ---------------------------------------------------
        goto("/app")
        page.wait_for_timeout(1500)
        shot("22_overview")
        goto("/about")
        shot("23_about")

        # ---- dark mode on an app screen ------------------------------------------
        goto("/app/evaluation")
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(1500)
        shot("24_evaluation-dark")

        browser.close()

    # Known: nothing should be left. Print what the browser saw.
    print("\n--- browser problems ---")
    for line in problems:
        print(line)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
