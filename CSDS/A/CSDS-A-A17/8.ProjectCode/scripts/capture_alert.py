"""Capture the live-monitoring page at the moment the cold-chain alert banner appears (and again after it has stayed on).

    venv\\Scripts\\python scripts/capture_alert.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
WEB = "http://127.0.0.1:5190"


def main():
    t0 = time.time()
    info = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
        page.goto(f"{WEB}/login")
        page.get_by_label("Email").fill("distributor@cropsight.dev")
        page.get_by_label("Password").fill("cropsight123")
        page.get_by_role("button", name="Log in").click()
        page.wait_for_url("**/distributor**")
        page.goto(f"{WEB}/distributor/shipments/1")
        t_open = time.time()
        page.wait_for_selector("text=outside the safe range", timeout=400000)
        info["seconds_until_banner"] = round(time.time() - t_open, 1)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "22b_live_alert.png"))
        page.wait_for_timeout(max(0, int((215 - (time.time() - t_open)) * 1000)))
        page.screenshot(path=str(OUT / "22c_live_alert_later.png"))
        info["seconds_at_second_shot"] = round(time.time() - t_open, 1)
        info["banner_visible_at_second_shot"] = page.locator("text=currently outside the safe range").count() > 0
        b.close()
    print(info)
    run = json.loads((OUT / "_run.json").read_text(encoding="utf-8"))
    for s in run["screens"]:
        if s["file"] == "22_live_monitoring.png":
            s["shows"] = "Live monitoring after about one minute of streaming: temperature, humidity and shock traces (a humidity step is visible; readings still inside the alarm band, so no banner yet)"
    run["screens"] += [
        {"file": "22b_live_alert.png", "shows": f"Live monitoring {info['seconds_until_banner']} s after opening the page: the first anomaly (an injected event) raises the red Cold-chain alert toast"},
        {"file": "22c_live_alert_later.png", "shows": f"Live monitoring {info['seconds_at_second_shot']} s after opening the page; red in-page banner shown: {info['banner_visible_at_second_shot']}"},
    ]
    run["alert_timing"] = info
    (OUT / "_run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
