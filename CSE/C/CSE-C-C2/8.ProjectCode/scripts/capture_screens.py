"""Capture documentation screenshots (1440x900) of every StoryVox screen into docs/screenshots/.

Needs the app running (run.bat) and Playwright:  pip install playwright   (uses the installed Chrome, no download)
  python scripts/capture_screens.py [http://localhost:5402]
If the library is empty it writes one real story first, so no screen is captured empty.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5402").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def api(path: str, body: dict | None = None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as res:
        return json.load(res)


stories = api("/api/stories?limit=50")
if not stories:
    api("/api/stories/generate", {"prompt": "A young inventor discovers a hidden library beneath her school.",
                                  "language_code": "en", "style": "Adventure", "length_option": "Medium", "synthesize": True})
    stories = api("/api/stories?limit=50")
first = stories[0]["id"]


def scroll_through(page) -> None:
    """Scroll the whole page once so scroll-triggered reveals have played, then return to the top."""
    for _ in range(14):
        page.mouse.wheel(0, 450)
        page.wait_for_timeout(250)
    page.evaluate("window.scrollTo(0, 0)")


def shot(page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(1400)  # let reveal animations and count-ups settle
    if full:
        scroll_through(page)
        page.wait_for_timeout(900)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)

    for scheme in ("light", "dark"):
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
        page = ctx.new_page()
        page.goto(BASE + "/", wait_until="networkidle")
        shot(page, f"01_landing_{scheme}")
        if scheme == "light":
            shot(page, "09_landing_full_page", full=True)
        ctx.close()

    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
    page = ctx.new_page()

    page.goto(BASE + "/studio", wait_until="networkidle")
    shot(page, "02_studio_empty")

    page.goto(BASE + f"/studio?story={first}", wait_until="networkidle")
    shot(page, "03_studio_result")

    page.goto(BASE + "/stories", wait_until="networkidle")
    shot(page, "04_history")

    page.goto(BASE + f"/stories/{first}", wait_until="networkidle")
    shot(page, "05_story_detail")

    # Show the fullest saved run (most samples with measured speech), not a quick skip-narration run.
    runs = api("/api/evaluations")
    best = max(range(len(runs)), key=lambda i: (runs[i]["metrics_json"].get("averages", {}).get("rtf") is not None, runs[i]["sample_count"]))
    page.goto(BASE + "/evaluation", wait_until="networkidle")
    if len(runs) > 1:
        page.get_by_label("Evaluation run").select_option(str(best))
    shot(page, "06_evaluation")

    page.locator(".tabs").scroll_into_view_if_needed()
    page.evaluate("document.querySelector('.shell-content').scrollIntoView(); window.scrollBy(0, document.querySelector('.tabs').getBoundingClientRect().top - 90)")
    shot(page, "07_evaluation_chart")

    page.get_by_role("tab", name="Samples").click()
    page.evaluate("window.scrollBy(0, document.querySelector('.tabs').getBoundingClientRect().top - 90)")
    shot(page, "08_evaluation_samples")

    browser.close()
print("done ->", OUT)
