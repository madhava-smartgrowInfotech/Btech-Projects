"""Capture the output screens used in the project documents (real app, real answers, 1440x900).

Needs the app running (backend 8412, frontend 5412). Typical use for the documents:
    python scripts/capture_docs_screens.py          # all screens, answers from whichever generator the backend loaded
    python scripts/capture_docs_screens.py --echo   # one extra screen: the answer text of the default local generator
Writes docs/screenshots/<nn>_<screen>.png and exits non-zero when a console error or an HTTP error is seen.
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

QUERIES = [
    ("I have high fever, headache and body pain since yesterday", "07_assistant_answer"),
    ("Burning when I pee, going to the toilet every few minutes and the urine looks cloudy", "18_assistant_lay_query"),
    ("I am pregnant and have mild nausea in the mornings", "19_assistant_caution"),
    ("I have severe chest pain and difficulty breathing", "08_assistant_emergency"),
]
EXTRA = [
    "Dry cough, sore throat and runny nose for three days",
    "Itchy red eyes with watery discharge in the morning",
    "Frequent urination, constant thirst and blurred vision",
    "Pain started near the belly button and moved to the lower right side with nausea",
]


def shot(page, name, wait=900):
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
    print("saved", name, flush=True)


def set_theme(page, theme):
    page.evaluate(f"localStorage.setItem('am.theme','{theme}'); document.documentElement.setAttribute('data-theme','{theme}')")


def login(page):
    page.goto(URL + "/login")
    page.wait_for_selector("form")
    page.fill('input[name="email"]', DEMO[0])
    page.fill('input[name="password"]', DEMO[1])
    page.click('form button[type="submit"]')
    page.wait_for_url("**/assistant")


def ask(page, q, timeout=180000):
    page.goto(URL + "/assistant")
    page.wait_for_selector("textarea")
    page.fill("textarea", q)
    page.keyboard.press("Enter")
    page.wait_for_selector(".msg-ai .answer", timeout=timeout)
    page.wait_for_timeout(700)


def main():
    from playwright.sync_api import sync_playwright

    echo_only = "--echo" in sys.argv
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="no-preference")
        page = ctx.new_page()
        current = {"screen": "?"}
        page.on("console", lambda m: problems.append((current["screen"], "console", m.text)) if m.type == "error" else None)
        page.on("pageerror", lambda e: problems.append((current["screen"], "pageerror", str(e))))
        page.on("response", lambda r: problems.append((current["screen"], f"http {r.status}", r.url)) if r.status >= 400 and "/api/auth/me" not in r.url else None)

        if echo_only:
            current["screen"] = "echo"
            login(page)
            ask(page, QUERIES[0][0])
            page.evaluate("document.querySelector('.chat-log').scrollTo(0, 0)")
            shot(page, "21_assistant_generator_echo")
            browser.close()
            return finish()

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

        current["screen"] = "register"
        page.goto(URL + "/register")
        page.wait_for_selector("form")
        shot(page, "04_register")
        current["screen"] = "login"
        page.goto(URL + "/login")
        page.wait_for_selector("form")
        shot(page, "05_login")
        login(page)

        current["screen"] = "assistant"
        page.wait_for_selector("textarea")
        shot(page, "06_assistant_empty")
        for q, name in QUERIES:
            current["screen"] = name
            ask(page, q)
            shot(page, name, 400)
            if name == "07_assistant_answer":
                page.evaluate("const l=document.querySelector('.chat-log'); l.scrollTo(0, l.scrollHeight)")
                shot(page, "20_assistant_evidence", 500)
        for q in EXTRA:
            ask(page, q)

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
        page.wait_for_selector("[role=dialog]", state="detached", timeout=3000)

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

        current["screen"] = "404"
        page.goto(URL + "/nope")
        page.wait_for_selector("text=404")
        shot(page, "17_not_found")
        browser.close()
    finish()


def finish():
    real = [x for x in problems if not (x[1] == "http 404" and x[0] == "404")]
    if real:
        print("\nPROBLEMS:")
        for s, k, m in real:
            print(f"  [{s}] {k}: {m[:200]}")
        sys.exit(2)
    print("\nAll screens captured; console clean.")


if __name__ == "__main__":
    main()
