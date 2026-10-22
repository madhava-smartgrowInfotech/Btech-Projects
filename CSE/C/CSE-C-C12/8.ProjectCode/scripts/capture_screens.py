"""Walk every screen of the running app, put real data on it and save 1440x900 PNGs to docs/screenshots/.

Needs the app running (run.bat) and: pip install playwright (uses the installed Chrome, or `playwright install chromium`).
Also records console errors / failed requests per screen and exits non-zero if any are found.
"""
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
URL = os.getenv("CARELENS_WEB", "http://localhost:5412")
DEMO = ("demo@carelens.ai", "Demo@1234")
problems = []


def shot(page, name):
    page.wait_for_timeout(900)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
    print("saved", name)


def set_theme(page, theme):
    page.evaluate(f"localStorage.setItem('am.theme','{theme}'); document.documentElement.setAttribute('data-theme','{theme}')")


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright missing: pip install playwright")
        sys.exit(1)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="no-preference")
        page = ctx.new_page()
        current = {"screen": "?"}

        def on_console(msg):
            if msg.type == "error":
                problems.append((current["screen"], "console", msg.text))

        page.on("console", on_console)
        page.on("pageerror", lambda e: problems.append((current["screen"], "pageerror", str(e))))
        page.on("response", lambda r: problems.append((current["screen"], f"http {r.status}", r.url)) if r.status >= 400 and "/api/auth/me" not in r.url else None)

        # --- landing, light + dark
        current["screen"] = "landing"
        page.goto(URL)
        set_theme(page, "light")
        page.reload()
        page.wait_for_selector("h1")
        page.wait_for_timeout(1800)
        shot(page, "01_landing_light")
        set_theme(page, "dark")
        page.reload()
        page.wait_for_selector("h1")
        page.wait_for_timeout(1800)
        shot(page, "02_landing_dark")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        shot(page, "03_landing_bottom_dark")
        set_theme(page, "light")

        # --- auth screens
        current["screen"] = "register"
        page.goto(URL + "/register")
        page.wait_for_selector("form")
        shot(page, "04_register")
        current["screen"] = "login"
        page.goto(URL + "/login")
        page.wait_for_selector("form")
        shot(page, "05_login")

        # --- sign in with the demo account through the real form
        page.fill('input[name="email"]', DEMO[0])
        page.fill('input[name="password"]', DEMO[1])
        page.click('form button[type="submit"]')
        page.wait_for_url("**/assistant")

        # --- assistant: normal + emergency query
        current["screen"] = "assistant"
        page.wait_for_selector("textarea")
        shot(page, "06_assistant_empty")
        page.fill("textarea", "I have high fever, headache and body pain since yesterday")
        page.keyboard.press("Enter")
        page.wait_for_selector(".msg-ai .answer", timeout=120000)
        page.wait_for_timeout(600)
        shot(page, "07_assistant_answer")
        page.fill("textarea", "I have severe chest pain and difficulty breathing")
        page.keyboard.press("Enter")
        page.wait_for_selector(".alert-error", timeout=120000)
        page.wait_for_timeout(600)
        shot(page, "08_assistant_emergency")

        # --- history, detail, delete confirm
        current["screen"] = "history"
        page.goto(URL + "/history")
        page.wait_for_selector("table tbody tr")
        shot(page, "09_history")
        page.fill('input[type="search"]', "fever")
        page.wait_for_timeout(900)
        shot(page, "10_history_search")
        page.fill('input[type="search"]', "")
        page.wait_for_selector("table tbody tr")
        current["screen"] = "detail"
        page.click("table tbody tr >> nth=0")
        page.wait_for_selector(".ev-card")
        shot(page, "11_consultation_detail")
        page.click("text=Delete >> nth=0")
        page.wait_for_selector("[role=dialog]")
        shot(page, "12_delete_confirm")
        page.keyboard.press("Escape")
        page.wait_for_selector("[role=dialog]", state="detached", timeout=3000)  # Escape closes the overlay

        # --- about + metrics (dark too)
        current["screen"] = "about"
        page.goto(URL + "/about")
        page.wait_for_selector(".stat-value")
        page.wait_for_timeout(1800)
        shot(page, "13_about_metrics")
        set_theme(page, "dark")
        page.reload()
        page.wait_for_selector(".stat-value")
        page.wait_for_timeout(1800)
        shot(page, "14_about_dark")
        set_theme(page, "light")

        # --- mobile views
        mctx = browser.new_context(viewport={"width": 390, "height": 844})
        mp = mctx.new_page()
        mp.on("console", lambda m: problems.append(("mobile", "console", m.text)) if m.type == "error" else None)
        mp.goto(URL + "/login")
        mp.fill('input[name="email"]', DEMO[0])
        mp.fill('input[name="password"]', DEMO[1])
        mp.click('form button[type="submit"]')
        mp.wait_for_url("**/assistant")
        mp.wait_for_timeout(900)
        mp.screenshot(path=str(OUT / "15_mobile_assistant.png"))
        mp.goto(URL + "/history")
        mp.wait_for_selector(".row-card")
        mp.wait_for_timeout(600)
        mp.screenshot(path=str(OUT / "16_mobile_history.png"))
        print("saved mobile shots")

        # --- 404
        current["screen"] = "404"
        page.goto(URL + "/nope")
        page.wait_for_selector("text=404")
        shot(page, "17_not_found")
        browser.close()

    real = [x for x in problems if not (x[1] == "http 404" and x[0] == "404")]
    if real:
        print("\nPROBLEMS:")
        for s, k, m in real:
            print(f"  [{s}] {k}: {m[:200]}")
        sys.exit(2)
    print("\nAll screens captured; console clean.")


if __name__ == "__main__":
    main()
