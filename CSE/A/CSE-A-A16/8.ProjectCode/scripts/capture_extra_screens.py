"""Extra screenshots for the documentation appendix: light theme and phone-width layouts of real screens.

Needs the app running (run.bat) and a trained model. Writes to docs/screenshots/.
    python scripts/capture_extra_screens.py [--base http://127.0.0.1:5316]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5316")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        shots = [
            ("09_dashboard_light", "/app", 1440, 900, "light"),
            ("10_model_light", "/app/model", 1440, 900, "light"),
            ("11_mobile_dashboard", "/app", 390, 844, "dark"),
            ("12_mobile_recognize", "/app/recognize", 390, 844, "dark"),
        ]
        for name, path, w, h, scheme in shots:
            ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
            pg = ctx.new_page()
            problems: list[str] = []
            pg.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
            pg.on("response", lambda r: problems.append(f"HTTP {r.status} {r.url}") if r.status >= 400 else None)
            pg.goto(args.base + path, wait_until="networkidle")
            pg.wait_for_timeout(1500)
            pg.screenshot(path=str(OUT / f"{name}.png"))
            print("saved", name, "| problems:", problems or "none")
            ctx.close()
        b.close()


if __name__ == "__main__":
    main()
