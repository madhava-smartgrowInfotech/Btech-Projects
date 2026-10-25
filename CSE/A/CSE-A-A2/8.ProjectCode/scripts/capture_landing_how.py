"""Re-capture 03_landing_how_it_works.png after the landing page counters have finished their count-up animation (about 7 s)."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5302").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots" / "03_landing_how_it_works.png"

with sync_playwright() as p:
    try:
        b = p.chromium.launch(channel="chrome")
    except Exception:
        b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.goto(BASE + "/")
    page.wait_for_selector("h1")
    page.evaluate("t => { document.documentElement.setAttribute('data-theme', t); localStorage.setItem('resqai.theme', t) }", "light")
    page.wait_for_timeout(1500)
    page.evaluate("window.scrollTo(0, 1100)")
    page.wait_for_timeout(8000)
    page.screenshot(path=str(OUT))
    print("saved", OUT)
    b.close()
