"""Walk the running app (frontend 5307, backend 8307) and save a 1440x900 PNG of every screen.

Puts real data on each screen: signs in with the demo clinician, loads a sample report through the
UI, assigns a priority, overrides it, then captures the queue and performance pages.
Also reports console errors, page errors and failed network requests seen during the walk.

Run (from 8.ProjectCode, servers running):  python scripts/capture_screens.py
Needs:  pip install playwright   (uses the installed Chrome; falls back to bundled Chromium)
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5307"
SAMPLE = "report_01_chest_pain_stemi.pdf"
problems = []


def watch(page):
    page.on("console", lambda m: problems.append(f"console {m.type}: {m.text}") if m.type in ("error",) else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    page.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url}"))
    page.on("response", lambda r: problems.append(f"http {r.status}: {r.url}") if r.status >= 400 and r.status != 401 else None)


def scroll_through(page):
    h = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < h:
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(120)
        y += 600
    page.wait_for_timeout(1800)  # let smooth scrolling settle before jumping back
    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    page.wait_for_timeout(1200)


def shot(page, name):
    page.wait_for_timeout(900)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved", path.name)


def launch(p):
    try:
        return p.chromium.launch(channel="chrome", headless=True)
    except Exception:
        return p.chromium.launch(headless=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = launch(p)

        # landing in light and dark
        for scheme, name in (("light", "01_landing_light"), ("dark", "02_landing_dark")):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
            page = ctx.new_page()
            watch(page)
            page.goto(BASE + "/")
            page.wait_for_selector(".checks-stack")
            scroll_through(page)
            shot(page, name)
            ctx.close()

        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page = ctx.new_page()
        watch(page)
        page.goto(BASE + "/login")
        page.wait_for_selector("text=Demo accounts")
        shot(page, "03_login")
        page.get_by_role("button", name="Clinician").click()
        page.wait_for_url("**/app/queue")
        page.wait_for_selector("text=Triage queue")
        page.wait_for_selector("table")
        shot(page, "04_queue")

        page.goto(BASE + "/app/new")
        page.wait_for_selector("text=Or try a sample report")
        shot(page, "05_new_patient_empty")
        page.select_option("select >> nth=0", SAMPLE)
        page.wait_for_selector("text=Lab values", timeout=60000)
        page.wait_for_selector("text=Troponin")
        page.mouse.wheel(0, 0)
        shot(page, "06_new_patient_filled")
        page.get_by_role("button", name="Assign priority").click()
        page.wait_for_url("**/app/patients/*", timeout=30000)
        page.wait_for_selector("text=Why this priority")
        shot(page, "07_result")
        page.get_by_text("Why this priority").first.scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        shot(page, "08_result_why")

        page.get_by_role("button", name="Accept or change").first.click()
        page.wait_for_selector("role=dialog")
        page.select_option("role=dialog >> select", "2")
        page.fill("role=dialog >> textarea", "Pain controlled and stable on the monitor after treatment; stepping down to emergent.")
        shot(page, "09_override_modal")
        page.get_by_role("button", name="Save change").click() if page.get_by_role("button", name="Save change").count() else page.get_by_role("button", name="Accept priority").click()
        page.wait_for_selector("text=Clinician decisions")
        page.wait_for_selector("text=stepping down to emergent")
        shot(page, "10_result_decision")

        page.goto(BASE + "/app/queue")
        page.wait_for_selector("table")
        shot(page, "11_queue_updated")
        page.goto(BASE + "/app/performance")
        page.wait_for_selector("text=Confusion matrix")
        page.wait_for_timeout(1200)
        shot(page, "12_performance")
        ctx.close()
        browser.close()

    if problems:
        print("\nPROBLEMS SEEN:")
        for x in dict.fromkeys(problems):
            print(" -", x)
        sys.exit(1)
    print("\nconsole clean: no errors, page errors or failed requests")


if __name__ == "__main__":
    main()
