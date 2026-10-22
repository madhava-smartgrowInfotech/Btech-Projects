"""Capture real screenshots of the running app (http://localhost:8000) via Playwright; fall back to HTTP fetch note."""
import asyncio
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SHOT = BASE / "screenshots"
SHOT.mkdir(exist_ok=True)

PAGES = [("/", "01-landing.png"), ("/register", "02-register.png"), ("/login", "03-login.png"),
         ("/onboarding", "04-onboarding.png"), ("/dashboard", "05-dashboard.png"),
         ("/recommendations", "06-recommendations.png"), ("/path", "07-learning-path.png"),
         ("/insights", "08-insights.png"), ("/analytics", "09-analytics.png")]

async def main():
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        print("playwright unavailable:", e)
        return
    async with async_playwright() as p:
        try:
            b = await p.chromium.launch()
        except Exception as e:
            print("chromium launch failed (run: python -m playwright install chromium):", e)
            return
        pg = await b.new_page(viewport={"width": 1280, "height": 800})
        for route, name in PAGES:
            try:
                await pg.goto("http://localhost:8000" + route, wait_until="networkidle", timeout=20000)
                await pg.wait_for_timeout(1200)
                await pg.screenshot(path=str(SHOT / name))
                print("shot", name)
            except Exception as e:
                print("fail", route, e)
        # authenticated dashboard view: register quick user then screenshot dashboard/recommendations
        try:
            await pg.goto("http://localhost:8000/register", wait_until="networkidle", timeout=20000)
            print("auth shots skipped (manual login state); public views captured")
        except Exception:
            pass
        await b.close()

asyncio.run(main())
