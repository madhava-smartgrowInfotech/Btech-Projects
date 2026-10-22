"""PeerScope screenshot capture: drives the real running app and saves PNGs."""
from __future__ import annotations

import time
from pathlib import Path

BASE_URL = "http://localhost:8408"
OUT = Path(__file__).resolve().parent.parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        raise SystemExit(1)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1400, "height": 900})
        pg.goto(BASE_URL, wait_until="networkidle")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=str(OUT / "01_dashboard.png"))
        print("saved 01_dashboard.png")
        # Analyze view
        pg.click("text=Analyze Paper")
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(OUT / "02_analyze.png"))
        print("saved 02_analyze.png")
        # Upload demo paper + analyze via UI file input if present
        demo = Path(__file__).resolve().parent.parent / "data" / "demo" / "demo_paper.pdf"
        if demo.exists():
            try:
                pg.set_input_files("#file", str(demo))
                pg.wait_for_timeout(500)
                pg.click("#btn-analyze")
                pg.wait_for_timeout(25000)
                pg.screenshot(path=str(OUT / "03_results.png"), full_page=True)
                print("saved 03_results.png")
                pg.screenshot(path=str(OUT / "04_reviewers_match.png"), full_page=False)
            except Exception as exc:
                print("analysis screenshot step failed:", exc)
        pg.click("text=Reviewers")
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(OUT / "05_reviewers.png"))
        pg.click("text=Model Performance")
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(OUT / "06_model.png"))
        b.close()
    print(f"Screenshots in {OUT}")


if __name__ == "__main__":
    main()
