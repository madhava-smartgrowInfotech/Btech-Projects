"""Capture real screenshots of the running PhishGuard app (1440x900) into docs/screenshots/.

Start the app (run.bat) and load usage into it first (scripts/demo_scenario.py), then:

    python scripts/capture_screenshots.py before     # screens that need no state change
    python scripts/capture_screenshots.py sync       # public-feed sync dialog + resulting list
    python scripts/capture_screenshots.py retrain    # retrain from the Models screen, then capture version 2

Needs Playwright with a Chrome channel (pip install playwright). The app is opened on http://localhost:5103
(Vite listens on localhost, not 127.0.0.1).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
WEB = "http://localhost:5103"
PHISH = "http://secure-paypal-login.account-verify.tk/signin?user=a"
ZERO_DAY = "https://docs-share.cloudhost-files.com/drive/view?id=44"
FALSE_POSITIVE = "https://docs.python.org/3/library/urllib.html"
SAFE = "https://www.wikipedia.org/wiki/Phishing"
BATCH = "\n".join([
    "http://paypal.com.verify-login.tk/signin?user=a&pwd=b", "https://github.com/anthropics",
    "http://192.168.1.5/wp-admin/bank/update.php", "https://stackoverflow.com/questions/11227809",
    "http://apple-id-locked.support-center.xyz/unlock/account.html", "https://www.irctc.co.in/nget/train-search",
    "http://free-prize-winner-lucky.top/claim.exe", "https://www.wikipedia.org/wiki/Phishing",
    "http://netflix-billing-update.com/payment/verify", "https://docs.python.org/3/library/urllib.html",
])


def shot(page: Page, name: str, full: bool = False, wait: int = 1200) -> None:
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


def settle(page: Page) -> None:
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(600)


def before(page: Page) -> None:
    page.goto(WEB)
    shot(page, "01_landing", wait=7500)               # count-up figures need a few seconds
    page.goto(f"{WEB}/app/check")
    settle(page)
    shot(page, "02_check_home")
    page.goto(f"{WEB}/app/check?url={PHISH}")
    settle(page)
    shot(page, "03_check_phishing", wait=2000)
    shot(page, "03b_check_phishing_full", full=True, wait=400)
    page.goto(f"{WEB}/app/check?url={SAFE}")
    settle(page)
    shot(page, "04_check_safe", wait=2000)
    page.goto(f"{WEB}/app/check?url={ZERO_DAY}")
    settle(page)
    shot(page, "05_check_community_override", wait=2000)
    page.goto(f"{WEB}/app/check?url={FALSE_POSITIVE}")
    settle(page)
    shot(page, "06_check_false_positive_corrected", wait=2000)
    # batch mode
    page.goto(f"{WEB}/app/check?mode=batch")
    settle(page)
    page.get_by_role("tab", name="Batch").click()
    page.wait_for_timeout(500)
    page.get_by_label("Or paste URLs").fill(BATCH)
    page.get_by_role("button", name="Check 10 URLs").click()
    page.wait_for_timeout(4000)
    shot(page, "07_batch_results", full=True, wait=800)
    # report form
    page.goto(f"{WEB}/app/report?url=http://sbi-netbanking-kyc-update.top/login.php&verdict=phishing")
    settle(page)
    shot(page, "08_report_form")
    # intelligence board
    page.goto(f"{WEB}/app/intel")
    settle(page)
    shot(page, "09_intel", wait=1800)
    row = page.get_by_text("docs-share.cloudhost-files.com").first
    row.click()
    page.wait_for_timeout(1200)
    shot(page, "10_intel_detail", wait=600)
    page.keyboard.press("Escape")
    # models
    page.goto(f"{WEB}/app/models")
    settle(page)
    shot(page, "11_models", wait=2000)
    shot(page, "12_models_full", full=True, wait=400)
    page.goto(f"{WEB}/app/activity")
    settle(page)
    shot(page, "13_activity", wait=2000)
    shot(page, "14_activity_full", full=True, wait=300)


def sync(page: Page) -> None:
    page.goto(f"{WEB}/app/intel")
    settle(page)
    page.get_by_role("button", name="Sync feeds").first.click() if page.get_by_role("button", name="Sync feeds").count() else \
        page.get_by_role("button", name="Sync public feeds").first.click()
    page.wait_for_timeout(800)
    shot(page, "15_intel_sync_dialog", wait=500)
    page.get_by_role("button", name="Start sync").click()
    page.wait_for_selector("text=Done", timeout=120000)
    shot(page, "16_intel_sync_result", wait=800)
    page.get_by_role("button", name="Done").click()
    page.wait_for_timeout(1500)
    shot(page, "17_intel_after_sync", wait=1000)


def retrain(page: Page) -> None:
    page.goto(f"{WEB}/app/models")
    settle(page)
    page.get_by_role("button", name="Retrain now").first.click()
    page.wait_for_timeout(700)
    shot(page, "18_retrain_confirm", wait=300)
    page.get_by_role("button", name="Start retraining").click()
    page.wait_for_timeout(2500)
    shot(page, "19_retrain_running", wait=500)
    t0 = time.time()
    while time.time() - t0 < 900:
        page.wait_for_timeout(5000)
        page.reload()
        settle(page)
        if page.get_by_text("Retraining").count() == 0:
            break
    shot(page, "20_models_after_retrain", wait=2500)
    shot(page, "21_models_after_retrain_full", full=True, wait=400)
    page.goto(f"{WEB}/app/intel")
    settle(page)
    shot(page, "22_intel_after_retrain", wait=1500)


def after(page: Page) -> None:
    """Capture the Models and Threat intelligence screens once a retrain has finished."""
    page.goto(f"{WEB}/app/models")
    settle(page)
    shot(page, "20_models_after_retrain", wait=2500)
    shot(page, "21_models_after_retrain_full", full=True, wait=400)
    page.goto(f"{WEB}/app/intel")
    settle(page)
    shot(page, "22_intel_after_retrain", wait=1500)
    page.goto(f"{WEB}/app/check?url=https://docs.python.org/3/library/urllib.html")
    settle(page)
    page.get_by_role("button", name="Switch to dark theme").click() if page.get_by_role("button", name="Switch to dark theme").count() else None
    shot(page, "23_check_dark", wait=1500)


def main() -> int:
    phase = sys.argv[1] if len(sys.argv) > 1 else "before"
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        {"before": before, "sync": sync, "retrain": retrain, "after": after}[phase](page)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
