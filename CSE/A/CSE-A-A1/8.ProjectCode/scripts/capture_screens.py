"""
Walks every screen of the React app with real data and saves 1440x900 PNGs to docs/screenshots/.
Also reports console errors, page errors and failed requests (404s etc.) seen along the way.

Needs both servers running (run.bat) and:  pip install playwright  (uses the installed Chrome).

    python scripts/capture_screens.py            # captures + console check
    python scripts/capture_screens.py --responsive   # also 360 / 768 widths into a temp folder
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get("APP_URL", "http://localhost:5301")
OUT = os.path.join(ROOT, "docs", "screenshots")
SAMPLE = os.path.join(ROOT, "sample_data", "sample_notes_data_structures.txt")
RESPONSIVE = "--responsive" in sys.argv
RESP_OUT = os.environ.get("RESPONSIVE_OUT", os.path.join(ROOT, "docs", "screenshots", "_responsive"))

problems = []


def watch(page, label):
    page.on("console", lambda m: m.type == "error" and problems.append(f"[{label}] console error: {m.text} ({m.location.get('url', '')})"))
    page.on("pageerror", lambda e: problems.append(f"[{label}] page error: {e}"))
    page.on(
        "response",
        lambda r: r.status >= 400 and r.status != 401 and problems.append(f"[{label}] HTTP {r.status} {r.request.method} {r.url}"),
    )
    page.on("requestfailed", lambda r: problems.append(f"[{label}] request failed: {r.url} {r.failure}"))


def settle(page, ms=1200):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def shot(page, name, full=False):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print("saved", os.path.relpath(path, ROOT))


def set_theme(page, theme):
    page.evaluate(f"localStorage.setItem('alip-theme', '{theme}')")
    page.reload()
    settle(page)


def take_quiz(page, pattern):
    page.goto(f"{BASE}/app/quiz")
    settle(page, 600)
    page.get_by_role("button", name="Start quiz on sample_notes_data_structures.txt").first.click()
    page.wait_for_selector("fieldset")
    page.wait_for_timeout(800)
    n = page.locator("fieldset").count()
    for i in range(n):
        page.locator(f"#q{i}o{pattern[i % len(pattern)]}").check()


def main():
    user = f"student_{int(time.time())}"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page = ctx.new_page()
        watch(page, "desktop")

        # ---- public screens
        page.goto(BASE)
        settle(page, 2200)
        set_theme(page, "light")
        page.wait_for_timeout(1800)
        shot(page, "01_landing-light")
        set_theme(page, "dark")
        page.wait_for_timeout(1800)
        shot(page, "02_landing-dark")
        set_theme(page, "light")  # the rest of the app is captured in light mode

        page.goto(f"{BASE}/login")
        settle(page)
        shot(page, "03_login")
        page.goto(f"{BASE}/register")
        settle(page)
        page.get_by_label("Username").fill(user)
        page.get_by_label("Password", exact=True).fill("StudyHard#1")
        page.get_by_label("Interests / goals (optional)").fill("Data Structures")
        shot(page, "04_register")
        page.get_by_role("button", name="Create account").click()
        page.wait_for_url("**/app/upload")
        settle(page)

        # ---- upload with a real file
        page.set_input_files("input[type=file]", SAMPLE)
        page.wait_for_timeout(600)
        page.get_by_label("Subject").fill("Data Structures")
        shot(page, "05_upload-ready")
        page.get_by_role("button", name="Upload & process").click()
        page.get_by_text("Document processed").wait_for()
        page.wait_for_timeout(900)
        shot(page, "06_upload-done")

        # ---- ask a few questions
        page.goto(f"{BASE}/app/ask")
        settle(page, 600)
        for q in ["What is the LIFO principle?", "What is a binary search tree?", "How does a queue work?"]:
            page.get_by_label("Your question").fill(q)
            page.get_by_role("button", name="Ask", exact=True).click()
            page.get_by_text("Sources", exact=True).wait_for()
            page.wait_for_timeout(500)
        page.get_by_text("Sources", exact=True).scroll_into_view_if_needed()
        page.locator("details summary").first.click()
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(300)
        shot(page, "09_ask")

        # ---- two quizzes so the dashboard and roadmap have real numbers
        page.goto(f"{BASE}/app/quiz")
        settle(page, 800)
        shot(page, "10_quiz-picker")
        take_quiz(page, [0, 1, 2, 3, 0])
        shot(page, "11_quiz-taking")
        page.get_by_role("button", name="Submit quiz").click()
        page.get_by_text("Your result").wait_for()
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(1800)
        shot(page, "12_quiz-result")
        page.get_by_role("button", name="New quiz on this document").click()
        page.wait_for_selector("fieldset")
        page.wait_for_timeout(600)
        for i in range(page.locator("fieldset").count()):
            page.locator(f"#q{i}o{(i + 1) % 4}").check()
        page.get_by_role("button", name="Submit quiz").click()
        page.get_by_text("Your result").wait_for()
        page.wait_for_timeout(800)

        # ---- the rest of the app, now populated
        page.goto(f"{BASE}/app")
        settle(page, 2000)
        shot(page, "07_dashboard")
        page.goto(f"{BASE}/app/documents")
        settle(page)
        shot(page, "08_documents")
        page.goto(f"{BASE}/app/roadmap")
        settle(page, 1600)
        shot(page, "13_roadmap")

        # dark mode dashboard through the topbar toggle
        page.goto(f"{BASE}/app")
        settle(page, 800)
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(2000)
        shot(page, "14_dashboard-dark")

        if RESPONSIVE:
            os.makedirs(RESP_OUT, exist_ok=True)
            for w, h in ((360, 780), (768, 1024)):
                for theme in ("light", "dark"):
                    rc = browser.new_context(viewport={"width": w, "height": h}, color_scheme=theme)
                    # reuse the session cookie
                    rc.add_cookies(ctx.cookies())
                    rp = rc.new_page()
                    watch(rp, f"{w}px {theme}")
                    rp.goto(BASE)
                    rp.evaluate(f"localStorage.setItem('alip-theme', '{theme}')")
                    for route, name in (("/", "landing"), ("/app", "dashboard"), ("/app/documents", "documents"), ("/app/ask", "ask"), ("/app/quiz", "quiz"), ("/app/roadmap", "roadmap"), ("/app/upload", "upload"), ("/login", "login")):
                        rp.goto(BASE + route)
                        settle(rp, 1500)
                        overflow = rp.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
                        if overflow:
                            problems.append(f"[{w}px {theme}] horizontal overflow on {route}")
                        rp.screenshot(path=os.path.join(RESP_OUT, f"{w}_{theme}_{name}.png"), full_page=(name == "landing"))
                    rc.close()

        browser.close()

    print()
    if problems:
        print(f"{len(problems)} problem(s):")
        for x in dict.fromkeys(problems):
            print(" -", x)
        sys.exit(1)
    print("Console clean: no errors, page errors or failed requests.")


if __name__ == "__main__":
    main()
