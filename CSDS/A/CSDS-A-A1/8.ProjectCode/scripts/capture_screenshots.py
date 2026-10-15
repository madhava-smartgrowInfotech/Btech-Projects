"""Capture real screenshots of the running PolicyLens app (1440x900) into docs/screenshots/.

Prerequisites: run.bat (API 8101 + web 5101) and scripts/seed_docs_demo.py (real chats, claim checks, comparison).

    python scripts/capture_screenshots.py

Needs Playwright with a Chrome channel:  pip install playwright
Standard flows only; the landing and dashboard counters animate, so those pages are given time to settle.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
WEB = "http://localhost:5101"
SEED = json.loads((OUT / "_seed.json").read_text(encoding="utf-8"))
DEMO = ("demo@policylens.app", "Demo@12345")


def api(path: str):
    """GET a JSON endpoint as the demo user (used to look up ids and clause ordinals)."""
    import urllib.request
    body = json.dumps({"email": DEMO[0], "password": DEMO[1]}).encode()
    req = urllib.request.Request("http://127.0.0.1:8101/api/auth/login", data=body, headers={"Content-Type": "application/json"})
    token = json.loads(urllib.request.urlopen(req, timeout=60).read())["access_token"]
    req = urllib.request.Request("http://127.0.0.1:8101/api" + path, headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def shot(page: Page, name: str, full: bool = False, wait: int = 1200) -> None:
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


def login(page: Page) -> None:
    page.goto(f"{WEB}/login")
    page.wait_for_timeout(1200)
    page.get_by_label("Email").fill(DEMO[0])
    page.get_by_label("Password", exact=True).fill(DEMO[1])
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/app**", timeout=20000)
    page.wait_for_timeout(1500)


def tab(page: Page, name: str) -> None:
    page.get_by_role("tab", name=name).first.click()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    star, hdfc = SEED["star"], SEED["hdfc"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        page.add_init_script("try{localStorage.setItem('policylens-theme','light')}catch(e){}")

        # ---- public pages
        page.goto(WEB)
        shot(page, "01_landing", wait=7000)
        shot(page, "01b_landing_full", full=True, wait=500)
        page.goto(f"{WEB}/login")
        shot(page, "02_login")
        page.goto(f"{WEB}/register")
        shot(page, "03_register")
        page.goto(f"{WEB}/app/performance")  # public evaluation page is also reachable signed in
        login(page)

        # ---- dashboard
        page.goto(f"{WEB}/app")
        shot(page, "04_dashboard", wait=5000)
        shot(page, "04b_dashboard_full", full=True, wait=300)

        # ---- library
        page.goto(f"{WEB}/app/policies")
        shot(page, "05_policies", wait=2000)

        # ---- one policy: card, risks, document, clause search
        page.goto(f"{WEB}/app/policies/{star}")
        shot(page, "06_policy_card", wait=3500)
        shot(page, "06b_policy_card_full", full=True, wait=300)
        tab(page, "Risks")
        shot(page, "07_policy_risks", wait=1500)
        shot(page, "07b_policy_risks_full", full=True, wait=300)
        excl02 = next(c["ordinal"] for c in api(f"/policies/{star}/clauses?page=28") if c["clause_ref"] == "Excl02")
        page.goto(f"{WEB}/app/policies/{star}?tab=document&page=28&clause={excl02}")
        shot(page, "08_policy_document", wait=4500)
        page.mouse.wheel(0, 650)
        shot(page, "08b_policy_document_highlight", wait=1200)
        tab(page, "Clause search")
        page.wait_for_timeout(600)
        box = page.get_by_role("searchbox").first if page.get_by_role("searchbox").count() else page.locator("main input[type=text], main input:not([type])").first
        box.fill("cataract waiting period")
        box.press("Enter")
        shot(page, "09_clause_search", wait=4000)

        # ---- chat: policy picker, English answer with citations, not-in-policy, Hindi
        page.goto(f"{WEB}/app/chat")
        shot(page, "10_chat_policy_picker", wait=1800)
        page.goto(f"{WEB}/app/chat/{SEED['conversation']}")
        shot(page, "11_chat_answer", wait=3000)
        try:
            page.locator("main button", has_text="Clause").first.click()
            shot(page, "12_chat_citation", wait=2500)
            page.keyboard.press("Escape")
        except Exception as exc:  # citation chip layout differs - skip rather than fail
            print("citation sheet skipped:", exc)
        page.goto(f"{WEB}/app/chat/{SEED['conversation_copay']}")
        shot(page, "11c_chat_copay", wait=3000)
        page.goto(f"{WEB}/app/chat/{SEED['conversation_fire']}")
        shot(page, "11d_chat_not_in_policy", wait=2500)
        page.goto(f"{WEB}/app/chat/{SEED['conversation_hi']}")
        shot(page, "13_chat_hindi", wait=3000)

        # ---- Claim Copilot: wizard steps and results
        page.goto(f"{WEB}/app/claims")
        shot(page, "14_claim_policy_step", wait=1800)
        page.locator("button", has_text="Family Health Optima").first.click()
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(600)
        page.get_by_role("button", name="Knee replacement").first.click()
        shot(page, "15_claim_treatment_step", wait=800)
        page.goto(f"{WEB}/app/claims/{SEED['claim']}")
        shot(page, "16_claim_result_partly", wait=3500)
        shot(page, "16b_claim_result_partly_full", full=True, wait=300)
        page.goto(f"{WEB}/app/claims/{SEED['claim_failing']}")
        shot(page, "17_claim_result_not_covered", wait=3500)
        shot(page, "17b_claim_result_not_covered_full", full=True, wait=300)

        # ---- Compare
        page.goto(f"{WEB}/app/compare")
        shot(page, "18_compare_form", wait=1800)
        page.goto(f"{WEB}/app/compare/{SEED['comparison']}")
        shot(page, "19_compare_result", wait=3500)
        shot(page, "19b_compare_result_full", full=True, wait=300)

        # ---- Model performance and settings
        page.goto(f"{WEB}/app/performance")
        shot(page, "20_model_performance", wait=4500)
        shot(page, "20b_model_performance_full", full=True, wait=500)
        page.goto(f"{WEB}/app/settings")
        shot(page, "21_settings", wait=1800)

        # ---- translated Policy Card (Telugu) - kept as a limitation screen
        page.goto(f"{WEB}/app/policies/{star}?lang=te")
        shot(page, "25_card_telugu", wait=4500)

        # ---- dark theme (own context so the stored theme is dark from the first paint) and phone width
        dark = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        dp = dark.new_page()
        dp.add_init_script("try{localStorage.setItem('policylens-theme','dark')}catch(e){}")
        login(dp)
        dp.goto(f"{WEB}/app/chat/{SEED['conversation']}")
        shot(dp, "22_chat_dark", wait=3000)
        dp.goto(f"{WEB}/app/policies/{star}")
        shot(dp, "22b_policy_card_dark", wait=3500)
        phone = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
        mp = phone.new_page()
        mp.add_init_script("try{localStorage.setItem('policylens-theme','light')}catch(e){}")
        login(mp)
        mp.goto(f"{WEB}/app/chat/{SEED['conversation']}")
        shot(mp, "23_mobile_chat", wait=3000)
        mp.goto(f"{WEB}/app/policies/{star}")
        shot(mp, "24_mobile_policy_card", wait=3500)

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
