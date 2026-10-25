"""Screens that show the console working on REAL UNSW-NB15 flows (data/samples/real_unsw_nb15_sample_120.csv).

    python scripts/capture_real_screens.py shipped   # API running with the shipped (synthetic-trained) models
    python scripts/capture_real_screens.py real      # API running with the real-trained bundle (see make_real_bundle.py)
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
SAMPLE = ROOT / "data" / "samples" / "real_unsw_nb15_sample_120.csv"
BASE = "http://127.0.0.1:5305"


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def main(mode):
    names = {"shipped": ["10_real-flows-shipped-model", None], "real": ["12_real-flows-real-model", "11_real-model-performance"]}[mode]
    with sync_playwright() as p:
        b = launch(p)
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        ctx.add_init_script("try { localStorage.setItem('cg_theme', 'dark') } catch (e) {}")
        page = ctx.new_page()
        page.goto(BASE + "/app", wait_until="networkidle")
        page.locator("input[type=file]").first.set_input_files(str(SAMPLE))
        page.get_by_role("button", name="Upload and score").click()
        page.get_by_text("Rows scored").wait_for()
        page.get_by_role("heading", name="Batch CSV scoring").scroll_into_view_if_needed()
        page.wait_for_timeout(5500)
        page.screenshot(path=str(OUT / f"{names[0]}.png"))
        print("saved", names[0])
        if names[1]:
            page.goto(BASE + "/app/performance", wait_until="networkidle")
            page.wait_for_timeout(2200)
            page.screenshot(path=str(OUT / f"{names[1]}.png"))
            print("saved", names[1])
        b.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "shipped")
