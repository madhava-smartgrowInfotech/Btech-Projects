"""Walk every PeerScope screen in a real browser, put real data on it, and save 1440x900 PNGs.

Needs the API (8408) and web app (5408) running - start them with run.bat first.
    pip install playwright && playwright install chromium
    python scripts/capture_screens.py

Also reports console errors, page errors and failed requests seen during the walk (exit code 1 if any).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
DEMO = ROOT / "data" / "demo" / "demo_paper.pdf"
WEB = os.environ.get("PEERSCOPE_WEB", "http://127.0.0.1:5408")
VIEW = {"width": 1440, "height": 900}


def launch(p):
    """Prefer the installed Chrome; fall back to Playwright's bundled Chromium."""
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return 2
    if not DEMO.exists():
        print(f"Demo PDF missing: {DEMO}. Run python scripts/make_demo_pdf.py first.")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    n = 0

    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport=VIEW, color_scheme="dark")
        page = ctx.new_page()
        page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url} {r.failure}"))
        page.on("response", lambda r: problems.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 and "/api/analyses/999999" not in r.url else None)

        def shot(name: str, full: bool = False) -> None:
            nonlocal n
            n += 1
            page.wait_for_timeout(1800)  # let count-up numbers and entrance motion settle
            path = OUT / f"{n:02d}_{name}.png"
            if full:
                # grow the viewport instead of using full_page, so the sticky sidebar is not repeated mid-image
                h = page.evaluate("document.documentElement.scrollHeight")
                page.set_viewport_size({"width": VIEW["width"], "height": min(max(h, VIEW["height"]), 4200)})
                page.wait_for_timeout(500)
                page.screenshot(path=str(path))
                page.set_viewport_size(VIEW)
            else:
                page.screenshot(path=str(path))
            print("saved", path.relative_to(ROOT))

        def theme(mode: str) -> None:
            page.evaluate(f"document.documentElement.setAttribute('data-theme','{mode}')")

        def go(path: str) -> None:
            page.goto(f"{WEB}{path}", wait_until="load")
            page.wait_for_timeout(1200)  # let the first API calls and lazy chunks land

        # landing, dark then light (hero is the WebGL scene)
        go("/")
        page.wait_for_timeout(1500)
        shot("landing_dark")
        page.mouse.wheel(0, 1500)
        shot("landing_how_it_works_dark")
        theme("light")
        page.evaluate("window.scrollTo(0,0)")
        shot("landing_light")
        theme("dark")

        go("/app")
        shot("dashboard")

        # analyze: upload the demo paper and wait for a real result
        go("/app/analyze")
        shot("analyze_empty")
        page.set_input_files("input[type=file]", str(DEMO))
        page.wait_for_timeout(400)
        page.get_by_role("button", name="Analyze paper").click()
        t0 = time.time()
        page.get_by_role("tab", name="Overview", exact=True).wait_for(timeout=180_000)
        print(f"analysis finished in {time.time() - t0:.0f}s")
        shot("analyze_result_overview", full=True)
        for tab, name in [("Review", "result_review"), ("Literature", "result_literature"), ("Reviewers", "result_reviewers"), ("Audit & export", "result_audit")]:
            page.get_by_role("tab", name=tab, exact=True).click()
            if tab == "Reviewers":
                # open the first audit breakdown so the screenshot shows the score maths
                first = page.locator("details.audit summary").first
                if first.count():
                    first.click()
            shot(name, full=True)

        go("/app/reviewers")
        shot("reviewers")
        page.get_by_role("button", name="Add reviewer").first.click()
        shot("reviewers_add_modal")
        page.keyboard.press("Escape")

        go("/app/model")
        shot("model_performance", full=True)

        go("/app/history")
        shot("history")
        page.locator("tbody tr").first.click()
        page.wait_for_url("**/app/analyses/*")
        page.get_by_role("tab", name="Overview", exact=True).wait_for()
        shot("saved_analysis", full=True)

        go("/app/about")
        shot("about", full=True)

        theme("light")
        go("/app")
        theme("light")
        shot("dashboard_light")
        browser.close()

    if problems:
        print("\nPROBLEMS SEEN DURING WALK:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        return 1
    print(f"\n{n} screenshots saved to {OUT.relative_to(ROOT)}; console clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
