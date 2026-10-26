"""Capture a 1440x900 PNG of every QuantPulse screen into docs/screenshots/.

QuantPulse has no login, so the script just walks the screens with real API data on them.
Requires the stack to be running (run.bat) and Playwright:
    pip install playwright
    playwright install chromium
    python scripts/capture_screens.py
"""
from __future__ import annotations
import os
import sys
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")


def env_port(name: str, default: int) -> int:
    try:
        for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
            if line.startswith(name + "="):
                return int(line.split("=", 1)[1].strip())
    except (OSError, ValueError):
        pass
    return default


API = f"http://127.0.0.1:{env_port('BACKEND_PORT', 8404)}"
WEB = f"http://localhost:{env_port('FRONTEND_PORT', 5404)}"

# (file name, route, selector to wait for, selector to scroll to, theme, pixels left above the scrolled-to element)
SCREENS = [
    ("01_landing_light", "/", ".hero-card .recharts-line", None, "light", 0),
    ("02_landing_dark", "/", ".hero-card .recharts-line", None, "dark", 0),
    ("03_dashboard", "/app", ".ticker-card", None, "light", 0),
    ("04_forecast_5day", "/app/forecast?t=TSLA&h=short", ".chart-box .recharts-line", ".chart-box", "light", 110),
    ("05_forecast_30day", "/app/forecast?t=MSFT&h=long", ".chart-box .recharts-line", ".chart-box", "light", 110),
    ("06_models_comparison", "/app/models?t=NVDA", ".chart-box .recharts-bar-rectangle", None, "light", 0),
    ("07_models_training", "/app/models?t=NVDA&tab=training", ".chart-box .recharts-line", ".chart-box", "light", 110),
    ("08_sentiment", "/app/sentiment?t=TSLA", ".headline", None, "light", 0),
    ("09_about", "/app/about", ".tbl", None, "light", 0),
    ("10_dashboard_dark", "/app", ".ticker-card", None, "dark", 0),
    ("11_forecast_dark", "/app/forecast?t=AAPL", ".chart-box .recharts-line", ".chart-box", "dark", 110),
    ("12_models_table", "/app/models?t=NVDA", ".tbl", ".tbl", "light", 150),
    ("13_sentiment_headlines", "/app/sentiment?t=TSLA", ".headline", ".chart-box", "light", 110),
    ("14_forecast_table", "/app/forecast?t=TSLA&h=short", ".tbl", ".tbl", "light", 150),
    ("16_forecast_top", "/app/forecast?t=NVDA&h=short", ".chart-box .recharts-line", None, "light", 0),
    ("15_dashboard_tickers", "/app", ".ticker-card", ".ticker-card", "light", 120),
]


def main():
    try:
        urllib.request.urlopen(API + "/api/health", timeout=10)
        urllib.request.urlopen(WEB + "/", timeout=10)
    except OSError as e:
        sys.exit(f"The stack is not running ({e}). Start it with run.bat first.")
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:  # no downloaded Chromium: use the installed Chrome
            browser = p.chromium.launch(channel="chrome")
        for name, route, ready, scroll_to, scheme, offset in SCREENS:
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
            page = ctx.new_page()
            page.goto(WEB + route, wait_until="networkidle", timeout=240000)
            page.wait_for_selector(ready, timeout=240000)  # the first sentiment call loads FinBERT, so it can take a while
            # play the scroll reveals on the landing page, then come back to the top
            height = page.evaluate("document.documentElement.scrollHeight")
            for y in range(0, height, 450):
                page.evaluate(f"window.scrollTo(0, {y})")
                page.wait_for_timeout(100)
            page.evaluate("window.scrollTo(0, 0)")
            if scroll_to:
                page.evaluate(f"window.scrollTo(0, document.querySelector('{scroll_to}').getBoundingClientRect().top + window.scrollY - {offset})")
            page.wait_for_timeout(1800)  # let chart animations finish
            path = os.path.join(OUT, f"{name}.png")
            page.screenshot(path=path)
            print("saved", os.path.relpath(path, ROOT))
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
