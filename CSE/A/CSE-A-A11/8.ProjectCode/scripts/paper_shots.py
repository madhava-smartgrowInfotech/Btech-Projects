"""Narrow (700 px wide) captures of the running app for the IEEE paper, so text stays readable at one-column width.

Needs the stack running (run.bat) and at least one saved review in History (the screenshot run leaves some).
    python scripts/paper_shots.py      -> docs/paper/shot_review.png, docs/paper/shot_finding.png
"""
import re
import sys
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "paper"
OUT.mkdir(parents=True, exist_ok=True)
PORT = 5311
BACK = "http://127.0.0.1:8311"
BASE = f"http://127.0.0.1:{PORT}"


def demo_review_id():
    creds = httpx.get(f"{BACK}/api/auth/demo").json()
    tok = httpx.post(f"{BACK}/api/auth/login", json=creds).json()["token"]
    rows = httpx.get(f"{BACK}/api/reviews", headers={"Authorization": f"Bearer {tok}"}).json()
    rows = [r for r in rows if r["verdict"] == "BLOCK" and r["findings"] >= 15]
    return rows[0]["id"]


def main():
    rid = demo_review_id()
    with sync_playwright() as p:
        try:
            br = p.chromium.launch()
        except Exception:
            br = p.chromium.launch(channel="chrome")
        ctx = br.new_context(viewport={"width": 700, "height": 1000}, color_scheme="light", device_scale_factor=2)
        page = ctx.new_page()
        page.goto(BASE + "/login")
        page.get_by_text("Use the demo account").click()
        page.wait_for_url("**/app")
        page.goto(f"{BASE}/app/review/{rid}")
        page.get_by_role("tab", name=re.compile("Findings")).wait_for()
        page.wait_for_timeout(1500)
        # hide the sticky top bar so it never covers the banner
        page.add_style_tag(content="header{position:static !important}")
        # the phone-width layout has a floating bottom navigation that would cover the screenshot
        page.evaluate("document.querySelectorAll('nav').forEach(n => { if (getComputedStyle(n).position === 'fixed') n.style.display = 'none'; })")
        h1 = page.get_by_role("heading", level=1).first
        box = h1.bounding_box()
        page.screenshot(path=str(OUT / "shot_review.png"), clip={"x": 0, "y": max(0, box["y"] - 20), "width": 700, "height": 560})
        # expanded SQL-injection finding card
        btn = page.locator("main button[aria-expanded][aria-controls]").filter(has_text=re.compile("SQL injection")).first
        btn.click()
        page.wait_for_timeout(800)
        card = btn.locator("xpath=ancestor::*[contains(@class,'glass') or self::article or self::li][1]")
        try:
            card.screenshot(path=str(OUT / "shot_finding.png"))
        except Exception:
            b = btn.bounding_box()
            page.screenshot(path=str(OUT / "shot_finding.png"), clip={"x": 0, "y": b["y"] - 10, "width": 700, "height": 620})
        br.close()
    print("saved", OUT)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print("failed:", e)
        sys.exit(1)
