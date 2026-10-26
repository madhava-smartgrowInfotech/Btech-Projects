"""Capture real screenshots of the running ForgetSafe app (API 8109, UI 5109) at 1440x900.

Drives the UI by clicking, so the state shown is produced by the real application:
train -> sample text -> unlearn two clients -> audit.  Start the servers first (run.bat).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
UI = "http://127.0.0.1:5109"
API = "http://127.0.0.1:8109"


def shot(page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(900)
    page.screenshot(path=str(OUT / name), full_page=full)
    print("saved", name)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True, args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        # fresh session so the capture starts from a known state (audit history is kept by the API)
        ctx.request.post(f"{API}/api/session")

        page.goto(UI + "/", wait_until="networkidle")
        page.wait_for_timeout(7000)  # count-up animations
        shot(page, "01_landing.png")
        page.mouse.wheel(0, 900)
        shot(page, "02_landing_how_it_works.png")

        # train through the UI
        page.goto(UI + "/app/training", wait_until="networkidle")
        page.wait_for_timeout(1500)
        shot(page, "03_training_before.png")
        page.get_by_role("button", name="Train federated model").first.click()
        page.wait_for_timeout(3500)
        shot(page, "04_training_trained.png")
        page.screenshot(path=str(OUT / "04b_training_full.png"), full_page=True)

        page.goto(UI + "/app", wait_until="networkidle")
        page.wait_for_timeout(4500)
        shot(page, "05_dashboard_trained.png")

        # explorer
        page.goto(UI + "/app/explorer", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.get_by_role("button", name="Generate sample").click()
        page.wait_for_timeout(2500)
        shot(page, "06_explorer_before_unlearning.png")

        # unlearning request 1 (Finance)
        page.goto(UI + "/app/unlearning", wait_until="networkidle")
        page.wait_for_timeout(1500)
        shot(page, "07_unlearning_request.png")
        page.get_by_role("button", name="Execute & certify").first.click()
        page.wait_for_timeout(900)
        shot(page, "08_unlearning_confirm.png")
        dialog = page.get_by_role("dialog")
        dialog.get_by_role("button", name="Remove & certify").click()
        page.wait_for_timeout(4000)
        shot(page, "09_unlearning_certificate.png")
        page.screenshot(path=str(OUT / "09b_certificate_full.png"), full_page=True)

        # explorer after
        page.goto(UI + "/app/explorer", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.get_by_role("button", name="Generate sample").click()
        page.wait_for_timeout(2500)
        shot(page, "10_explorer_after_unlearning.png")

        # second request (Healthcare)
        page.goto(UI + "/app/unlearning", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.locator("select").first.select_option(index=0)
        page.get_by_role("button", name="Execute & certify").first.click()
        page.wait_for_timeout(700)
        page.get_by_role("dialog").get_by_role("button", name="Remove & certify").click()
        page.wait_for_timeout(4000)
        shot(page, "11_second_certificate.png")

        page.goto(UI + "/app", wait_until="networkidle")
        page.wait_for_timeout(4500)
        shot(page, "12_dashboard_after_unlearning.png")

        page.goto(UI + "/app/audit", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Verify hash chain").click()
        page.wait_for_timeout(1500)
        shot(page, "13_audit_ledger.png")

        page.goto(UI + "/app/training", wait_until="networkidle")
        page.wait_for_timeout(3500)
        shot(page, "14_training_after_unlearning.png")

        # dark mode + mobile + legacy UI
        page.goto(UI + "/app", wait_until="networkidle")
        page.get_by_role("button", name="Switch to dark mode").first.click()
        page.wait_for_timeout(4500)
        shot(page, "15_dashboard_dark.png")
        page.get_by_role("button", name="Switch to light mode").first.click()

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        mp = mobile.new_page()
        mp.goto(UI + "/app/unlearning", wait_until="networkidle")
        mp.wait_for_timeout(2500)
        mp.screenshot(path=str(OUT / "16_unlearning_mobile.png"))
        print("saved 16_unlearning_mobile.png")

        legacy = ctx.new_page()
        legacy.goto(API + "/", wait_until="networkidle")
        legacy.wait_for_timeout(1000)
        legacy.screenshot(path=str(OUT / "17_legacy_ui.png"))
        print("saved 17_legacy_ui.png")

        print("console errors:", errors)
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
