"""Walk every VenturePulse screen against the running app and save 1440x900 PNGs.

Needs the backend and frontend running (run.bat). Usage:
    python scripts/capture_screens.py            # ports from .env (8410 / 5410)
    python scripts/capture_screens.py --check    # also fail on console errors / bad requests

Output: docs/screenshots/<nn>_<screen-name>.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"

DEMO = {"email": "demo@venturepulse.com", "password": "Demo@1234"}

def env_port(name: str, default: str) -> str:
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return default


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def scroll_through(page):
    """GSAP scroll-triggered sections only render once they have been scrolled into view."""
    h = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < h:
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(120)
        y += 700
    page.mouse.wheel(0, -h)
    page.wait_for_timeout(500)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit non-zero on console errors or failed requests")
    ap.add_argument("--base", default=f"http://127.0.0.1:{env_port('FRONTEND_PORT', '5410')}")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []

    with sync_playwright() as p:
        browser = launch(p)

        def new_page(scheme: str):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
            page = ctx.new_page()
            page.on("console", lambda m: m.type == "error" and problems.append(f"console: {m.text}"))
            page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
            page.on("response", lambda r: r.status >= 400 and "/api/auth/login" not in r.url and problems.append(f"{r.status} {r.url}"))
            return ctx, page

        def shot(page, name: str, full: bool = True):
            page.wait_for_timeout(900)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
            print("saved", name)

        # --- landing, dark then light
        ctx, page = new_page("dark")
        page.goto(args.base + "/")
        page.wait_for_selector("text=curl /api/health")
        page.wait_for_selector("text=best_model")
        page.wait_for_timeout(2600)  # let the headline finish typing
        scroll_through(page)
        shot(page, "01_landing_dark")
        page.get_by_role("button", name="Switch to light mode").click()
        page.wait_for_timeout(500)
        shot(page, "02_landing_light")
        ctx.close()

        # --- everything else in dark mode (the control-room look)
        ctx, page = new_page("dark")
        page.goto(args.base + "/login")
        page.get_by_text("click to fill").click()
        shot(page, "03_login", full=False)
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.wait_for_url("**/app")
        page.wait_for_selector("text=Best validated model")
        page.wait_for_selector("text=Historical startups")
        page.wait_for_timeout(1500)
        shot(page, "04_dashboard")

        page.goto(args.base + "/app/analyze")
        page.wait_for_selector("text=Funding & traction")
        shot(page, "05_analyze_form_empty")
        page.get_by_role("button", name="Fill an example").click()
        page.wait_for_timeout(300)
        shot(page, "06_analyze_form_filled")
        page.get_by_role("button", name="Predict startup success").click()
        page.wait_for_selector("text=estimated outcome", timeout=90000)
        page.wait_for_selector("text=Similar historical startups")
        shot(page, "07_result")

        page.goto(args.base + "/app/performance")
        page.wait_for_selector("text=Confusion matrix")
        page.wait_for_selector("text=Feature importance")
        page.wait_for_timeout(1500)
        shot(page, "08_performance")

        page.goto(args.base + "/app/insights")
        page.wait_for_selector("text=Success rate by industry")
        page.wait_for_timeout(1500)
        shot(page, "09_insights")
        ctx.close()
        browser.close()

    if problems:
        print("\nPROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        return 1 if args.check else 0
    print("\nconsole clean, no failed requests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
