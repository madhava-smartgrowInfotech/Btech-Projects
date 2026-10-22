"""Capture a 1440x900 screenshot of every screen into docs/screenshots/ with real data on it.

Needs the app running (run.bat) and Playwright:
    pip install playwright && playwright install chromium
    python scripts/capture_screens.py                 # all screens
    python scripts/capture_screens.py --with-retrain  # also trains once for the "finished" screen
                                                      # (this REPLACES models/msvm_model.pkl)

The app has no login, so there is nothing to sign in to. Uses the local Chrome if Playwright's own
Chromium is not installed.
"""
import argparse
import json
import os
import tempfile
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
SIZE = {"width": 1440, "height": 900}


def read_port():
    port = "5406"
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.startswith("FRONTEND_PORT="):
                port = line.split("=", 1)[1].strip()
    return port


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def settle(page, ms=1800):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def csv_of_samples(base, path, copies=1):
    samples = json.load(urllib.request.urlopen(f"{base}/api/samples"))["samples"]
    rows = ["text,label"]
    for _ in range(copies):
        rows += ['"%s",%s' % (s["text"].replace('"', '""'), s["label"]) for s in samples]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-retrain", action="store_true")
    args = ap.parse_args()
    base = f"http://localhost:{read_port()}"
    os.makedirs(OUT, exist_ok=True)
    work = tempfile.mkdtemp(prefix="fn_cap_")
    example_csv = os.path.join(work, "example_articles.csv")
    csv_of_samples(base, example_csv)
    train_csv = os.path.join(work, "labelled.csv")
    csv_of_samples(base, train_csv, copies=10)

    def shot(page, name, top=False):
        if top:
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
        path = os.path.join(OUT, name)
        page.screenshot(path=path)
        print("saved", os.path.relpath(path, ROOT))

    with sync_playwright() as p:
        browser = launch(p)
        for theme in ("dark", "light"):
            ctx = browser.new_context(viewport=SIZE, color_scheme=theme)
            ctx.add_init_script(f"localStorage.setItem('truthglow-theme','{theme}')")
            page = ctx.new_page()
            page.goto(base + "/")
            settle(page, 3000)
            shot(page, f"01_landing_{theme}.png")

            if theme == "dark":
                # the pinned "How it works" section needs a real scroll to play its animation
                page.evaluate("document.querySelector('#how-it-works').scrollIntoView()")
                page.mouse.wheel(0, 700)
                page.wait_for_timeout(2000)
                shot(page, "02_landing_how_it_works.png")

                # ---- Detect: run the clickbait example for a real verdict
                page.goto(base + "/app")
                settle(page)
                page.get_by_role("button", name="Clickbait example").click()
                page.get_by_text("Class probabilities").wait_for()
                settle(page, 2200)
                shot(page, "03_detect_result.png")

                # ---- Batch: upload the example CSV and run it
                page.goto(base + "/app/batch")
                settle(page, 1200)
                page.set_input_files("input[type=file]", example_csv)
                page.get_by_role("button", name="Run batch detection").wait_for()
                page.get_by_role("button", name="Run batch detection").click()
                page.get_by_text("Batch verdict distribution").wait_for()
                settle(page, 2200)
                shot(page, "04_batch_results.png")

                # ---- Analytics: top, then the charts
                page.goto(base + "/app/analytics")
                page.get_by_text("Confusion matrix").first.wait_for()
                settle(page, 2200)
                shot(page, "05_analytics.png")
                page.mouse.wheel(0, 650)
                page.wait_for_timeout(1500)
                shot(page, "05b_analytics_charts.png")

                # ---- Retrain: a CSV attached and sliders moved
                page.goto(base + "/app/retrain")
                settle(page, 1200)
                page.set_input_files("input[type=file]", train_csv)
                page.get_by_label("Generations").fill("6")
                page.wait_for_timeout(600)
                shot(page, "06_retrain.png", top=True)
                if args.with_retrain:
                    page.get_by_role("button", name="Retrain model").click()
                    page.get_by_role("button", name="Retrain and replace").click()
                    page.get_by_text("Training PCA + Firefly + MSVM").wait_for()
                    shot(page, "07_retrain_running.png", top=True)
                    page.get_by_text("Retrained successfully").wait_for(timeout=300_000)
                    settle(page, 1500)
                    shot(page, "08_retrain_done.png", top=True)

                # ---- About
                page.goto(base + "/app/about")
                page.get_by_text("The loaded model").wait_for()
                settle(page, 2000)
                shot(page, "09_about.png")
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
