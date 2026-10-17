"""Walk every screen with a real browser, report console/network problems and save 1440x900 PNGs.

Needs the app running (run.bat).  Setup once:  pip install playwright  &&  playwright install chromium
Usage:  python scripts/capture_screens.py            (uses installed Chrome if present, else Chromium)
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
FRONT = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5303")
problems = []


def settle(page, ms=1200):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def shot(page, name, full=False):
    os.makedirs(OUT, exist_ok=True)
    page.screenshot(path=os.path.join(OUT, f"{name}.png"), full_page=full)
    print("saved", name)


def run():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()

        def new_page(theme):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            ctx.add_init_script(f"try{{localStorage.setItem('mdp-theme','{theme}')}}catch(e){{}}")
            page = ctx.new_page()
            page.on("console", lambda m: problems.append(f"console {m.type}: {m.text}") if m.type in ("error", "warning") and "THREE.Clock" not in m.text else None)
            page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
            page.on("requestfailed", lambda r: problems.append(f"request failed: {r.url}"))
            page.on("response", lambda r: problems.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 else None)
            return ctx, page

        # landing page, light and dark
        for i, theme in ((1, "dark"), (2, "light")):
            ctx, page = new_page(theme)
            page.goto(FRONT + "/")
            settle(page, 2500)
            shot(page, f"{i:02d}_landing-{theme}")
            if theme == "dark":
                page.evaluate("window.scrollTo(0, 1500)")
                page.wait_for_timeout(1500)
                shot(page, "03_landing-how-it-works")
            ctx.close()

        ctx, page = new_page("dark")
        page.goto(FRONT + "/app")
        settle(page)
        shot(page, "04_overview")

        n = 5
        for key in ("diabetes", "heart", "liver", "kidney"):
            page.goto(f"{FRONT}/app/predict/{key}")
            settle(page, 600)
            page.get_by_role("button", name="Positive sample").click()
            page.wait_for_timeout(900)
            page.get_by_role("button", name="Predict risk").click()
            page.get_by_role("heading", level=3).filter(has_text="Risk").first.wait_for(timeout=8000)
            page.wait_for_timeout(900)
            for close in page.get_by_role("button", name="Dismiss notification").all():
                close.click()
            page.wait_for_timeout(500)
            shot(page, f"{n:02d}_predict-{key}")
            n += 1

        page.goto(FRONT + "/app/models")
        settle(page)
        shot(page, f"{n:02d}_models")
        page.goto(FRONT + "/app/data")
        settle(page)
        shot(page, f"{n + 1:02d}_datasets")
        page.goto(FRONT + "/app/about")
        settle(page)
        shot(page, f"{n + 2:02d}_about")
        page.goto(FRONT + "/app/nope")
        settle(page, 600)
        shot(page, f"{n + 3:02d}_not-found")
        ctx.close()
        browser.close()


if __name__ == "__main__":
    run()
    if problems:
        print("\nPROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        sys.exit(1)
    print("\nconsole clean, all screens captured")
