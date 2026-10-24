"""Capture real SentinelFlow screenshots from the running application.

Starts the Flask app, runs Simulation Mode to populate detections, then
captures the dashboard, sections, and states with headless Chromium.
Usage: python screenshots/capture_screenshots.py
"""

import os
import subprocess
import sys
import time

import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(BASE, "screenshots")
URL = "http://localhost:5000"


def wait_for_server(timeout=60):
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        try:
            r = requests.get(URL + "/api/status", timeout=3)
            if r.status_code == 200:
                return True
        except Exception as exc:
            last_error = str(exc)
        time.sleep(1)
    raise RuntimeError("Flask server did not start in time. Last error: %s" % last_error)


def main():
    os.makedirs(SHOT_DIR, exist_ok=True)
    proc = subprocess.Popen([sys.executable, os.path.join(BASE, "app.py")],
                            cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for_server()
        requests.post(URL + "/api/demo/start", json={"window_seconds": 3}, timeout=5)
        print("Simulation Mode started; collecting windows...")
        time.sleep(24)  # several 3s windows -> mixed benign/attack rows
        status = requests.get(URL + "/api/status", timeout=5).json()
        print("windows_completed=%s mode=%s" % (status.get("windows_completed"), status.get("mode")))

        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(6000)
            # Select first detection row to populate the threat-detail panel.
            try:
                page.click("#detTable tbody tr:first-child", timeout=5000)
                page.wait_for_timeout(1500)
            except Exception as exc:
                print("Row click skipped: %s" % exc)
            page.screenshot(path=os.path.join(SHOT_DIR, "01_dashboard.png"), full_page=True)
            print("saved 01_dashboard.png")
            panels = page.locator(".panel").all()
            names = ["02_network_health", "03_detection_analytics", "04_live_table",
                     "05_threat_and_mitigation", "06_model_performance", "07_settings"]
            for loc, name in zip(panels, names):
                try:
                    loc.scroll_into_view_if_needed()
                    page.wait_for_timeout(600)
                    loc.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
                    print("saved %s.png" % name)
                except Exception as exc:
                    print("Skipped %s: %s" % (name, exc))
            # Simulation-mode header state close-up.
            try:
                page.locator(".topbar").screenshot(
                    path=os.path.join(SHOT_DIR, "07_simulation_mode.png"))
                print("saved 07_simulation_mode.png")
            except Exception as exc:
                print("Skipped header shot: %s" % exc)
            browser.close()
        print("Screenshots captured in %s" % SHOT_DIR)
    finally:
        try:
            requests.post(URL + "/api/demo/stop", timeout=5)
        except Exception as exc:
            print("Demo stop notification failed: %s" % exc)
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
