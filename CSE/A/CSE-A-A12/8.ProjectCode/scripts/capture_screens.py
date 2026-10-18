"""
Walks every screen of the running app (run.bat first), does a real upload so no
page is empty, and saves 1440x900 PNGs to docs/screenshots/<nn>_<name>.png.
It also fails if the browser console shows errors or any request returns 4xx/5xx
that the page did not expect.

    pip install playwright && playwright install chromium
    python scripts/capture_screens.py [--base http://localhost:5312]
"""

import argparse
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
SAMPLES = os.path.join(ROOT, "dataset_sample")
DEMO = {"email": "demo@pneumodetect.ai", "password": "Pneumo@123"}


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def settle(page, ms=1800):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def sweep(page):
    """Scroll down and back so scroll-triggered reveals fire before a full-page shot."""
    h = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < h:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(250)
        y += 500
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:5312")
    base = ap.parse_args().base
    os.makedirs(OUT, exist_ok=True)
    problems = []
    n = [0]

    def shot(page, name, full=False):
        n[0] += 1
        path = os.path.join(OUT, f"{n[0]:02d}_{name}.png")
        page.screenshot(path=path, full_page=full)
        print("saved", os.path.relpath(path, ROOT))

    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and problems.append(f"console: {m.text}"))
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on(
            "response",
            lambda r: r.status >= 400
            and not (r.url.endswith("/api/auth/me") and r.status == 401)
            and problems.append(f"http {r.status}: {r.url}"),
        )

        # --- landing, light and dark
        page.goto(base + "/")
        settle(page, 2500)
        sweep(page)
        shot(page, "landing_light", full=True)
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(500)
        shot(page, "landing_dark", full=True)
        page.get_by_role("button", name="Switch to light mode").click()

        # --- sign in
        page.goto(base + "/login")
        settle(page, 1500)
        shot(page, "login")
        page.get_by_role("button", name="Fill demo credentials").click()
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.wait_for_url("**/app")
        settle(page, 2200)

        # --- real upload through the UI, one file per class-ish sample
        files = sorted(f for f in os.listdir(SAMPLES) if f.lower().endswith((".jpg", ".jpeg", ".png")))
        page.goto(base + "/app/detect")
        settle(page, 1200)
        shot(page, "detect_empty")
        page.set_input_files("input[type=file]", os.path.join(SAMPLES, files[0]))
        page.wait_for_timeout(600)
        shot(page, "detect_preview")
        page.get_by_role("button", name="Analyze X-ray").click()
        page.wait_for_url("**/app/result/*", timeout=120000)
        settle(page, 2000)
        shot(page, "result", full=True)
        page.get_by_role("tab", name="Blend heatmap").click()
        page.wait_for_timeout(500)
        shot(page, "result_blend")
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(500)
        shot(page, "result_dark", full=True)
        page.get_by_role("button", name="Switch to light mode").click()

        # a few more scans so dashboard and history carry real data
        for f in files[1:]:
            page.goto(base + "/app/detect")
            page.set_input_files("input[type=file]", os.path.join(SAMPLES, f))
            page.get_by_role("button", name="Analyze X-ray").click()
            page.wait_for_url("**/app/result/*", timeout=120000)
            page.wait_for_load_state("networkidle")

        page.goto(base + "/app")
        settle(page, 3200)
        shot(page, "dashboard", full=True)
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(500)
        shot(page, "dashboard_dark")
        page.get_by_role("button", name="Switch to light mode").click()

        page.goto(base + "/app/history")
        settle(page, 1500)
        shot(page, "history", full=True)
        page.goto(base + "/app/about")
        settle(page, 1500)
        shot(page, "about", full=True)
        page.goto(base + "/nope")
        settle(page, 1000)
        shot(page, "not_found")

        browser.close()

    if problems:
        print("\nPROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        return 1
    print("\nConsole clean, no failing requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
