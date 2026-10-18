"""Walk every screen of the running app, put real data on it and save 1440x900 PNGs to docs/screenshots/.

Start the stack first (run.bat, or `python -m backend` + `npm run dev` in frontend/), then:
    python scripts/capture_screens.py
The same walk collects console errors, failed requests and 4xx/5xx responses; it exits 1 if any are found.
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
PORT = 5311
for line in (ROOT / ".env").read_text().splitlines() if (ROOT / ".env").exists() else []:
    if line.startswith("FRONTEND_PORT="):
        PORT = int(line.split("=", 1)[1])
BASE = f"http://127.0.0.1:{PORT}"
SIZE = {"width": 1440, "height": 900}

problems: list[str] = []
count = 0


def shot(page, name, full=False):
    global count
    count += 1
    OUT.mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(700)  # let entrance animations settle
    path = OUT / f"{count:02d}_{name}.png"
    page.screenshot(path=str(path), full_page=full)
    print("saved", path.relative_to(ROOT))


def to_tabs(page):
    """Scroll so the tab strip sits just under the top bar: header, filters and content stay in frame."""
    page.evaluate("window.scrollTo(0, document.querySelector('[role=tablist]').getBoundingClientRect().top + window.scrollY - 90)")


def tab(page, name, under_header=False):
    page.get_by_role("tab", name=re.compile(name)).click()
    page.wait_for_timeout(400)
    if under_header:
        to_tabs(page)
    else:
        page.evaluate("window.scrollTo(0, 0)")


def scroll_through(page):
    h = page.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h, 500):
        page.evaluate(f"window.scrollTo(0,{y})")
        page.wait_for_timeout(120)
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(300)


def watch(page):
    page.on("console", lambda m: problems.append(f"console {m.type}: {m.text}") if m.type in ("error",) else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    page.on("requestfailed", lambda r: problems.append(f"request failed: {r.url} {r.failure}"))
    page.on("response", lambda r: problems.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 and "/api/auth/login" not in r.url else None)


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def main():
    with sync_playwright() as p:
        browser = launch(p)

        # ---- landing, light and dark (signed out)
        for scheme in ("light", "dark"):
            ctx = browser.new_context(viewport=SIZE, color_scheme=scheme)
            page = ctx.new_page()
            watch(page)
            page.goto(BASE + "/")
            page.get_by_role("heading", level=1).wait_for()
            page.wait_for_selector("text=Demo pull request", timeout=15000)
            page.wait_for_timeout(2600)  # example card animates in
            scroll_through(page)
            shot(page, f"landing_{scheme}", full=True)
            if scheme == "dark":
                page.goto(BASE + "/login")
                page.get_by_text("Use the demo account").wait_for()
                shot(page, "login")
            ctx.close()

        # ---- signed-in app (dark, the default look)
        ctx = browser.new_context(viewport=SIZE, color_scheme="dark")
        page = ctx.new_page()
        watch(page)
        page.goto(BASE + "/login")
        page.get_by_text("Use the demo account").click()
        page.wait_for_url("**/app")
        page.get_by_role("heading", level=1).wait_for()

        # a first review through the Overview one-click demo, so every later screen has data
        page.get_by_role("button", name=re.compile("Run demo pull request review")).click()
        page.wait_for_url(re.compile(r".*/app/review/.+"), timeout=60000)
        page.get_by_role("tab", name=re.compile("Findings")).wait_for()
        review_url = page.url

        page.goto(BASE + "/app")
        page.get_by_text("Recent reviews").wait_for()
        shot(page, "overview")

        # ---- a second review (before/after sample) so History has a trend line
        page.goto(BASE + "/app/review")
        page.get_by_text("Preview diff").wait_for()
        page.get_by_role("radio", name="Before / after of one file").click()
        page.get_by_role("button", name=re.compile("Run multi-agent review")).click()
        page.wait_for_url(re.compile(r".*/app/review/.+"), timeout=60000)
        page.get_by_role("tab", name=re.compile("Findings")).wait_for()

        # ---- new review screen
        page.goto(BASE + "/app/review")
        page.get_by_text("Preview diff").wait_for()
        shot(page, "review_new_demo")
        page.get_by_role("tab", name=re.compile("Paste diff")).click()
        page.wait_for_timeout(300)
        shot(page, "review_new_paste_diff")

        # ---- review result tabs
        page.goto(review_url)
        page.get_by_role("tab", name=re.compile("Findings")).wait_for()
        page.get_by_text("Showing").wait_for()
        page.locator("main button[aria-expanded][aria-controls]").first.click()
        to_tabs(page)
        shot(page, "review_findings")
        tab(page, "Function risk", under_header=True)
        page.get_by_text("Inspect a function").wait_for()
        shot(page, "review_function_risk")
        tab(page, "Files", under_header=True)
        shot(page, "review_files")
        tab(page, "Agent trace", under_header=True)
        shot(page, "review_agent_trace")
        tab(page, "Export", under_header=True)
        page.get_by_text("PR comment preview").wait_for()
        page.wait_for_selector(".prose-answer", timeout=15000)
        shot(page, "review_export")

        # ---- codebase assistant
        page.goto(BASE + "/app/codebase")
        page.get_by_role("button", name=re.compile("Index repository")).click()
        page.get_by_role("tab", name=re.compile("Ask")).wait_for(timeout=30000)
        page.get_by_role("button", name="Where is the authentication mechanism implemented?").click()
        page.wait_for_selector(".prose-answer", timeout=30000)
        shot(page, "codebase_ask")
        tab(page, "Repository map")
        page.get_by_text("Module dependency graph").wait_for()
        shot(page, "codebase_map")
        tab(page, "Onboarding guide")
        page.wait_for_selector(".prose-answer")
        shot(page, "codebase_guide")

        # ---- model lab
        page.goto(BASE + "/app/lab")
        page.get_by_text("The 14 metrics").wait_for(timeout=30000)
        page.wait_for_timeout(3000)  # header counters count up
        shot(page, "lab_pipeline")
        for label, name in [("Feature selection", "lab_feature_selection"), ("Models", "lab_models"), ("ROC", "lab_roc_confusion"),
                            ("Vulnerability types", "lab_types"), ("Ablation", "lab_ablation")]:
            tab(page, label)
            shot(page, name)
        tab(page, "Try it")
        page.get_by_role("button", name=re.compile("Analyse function")).click()
        page.get_by_text("Static findings").wait_for()
        shot(page, "lab_try_it")

        # ---- history, settings, about
        page.goto(BASE + "/app/history")
        page.get_by_text("Risk score over time").wait_for()
        shot(page, "history")
        page.goto(BASE + "/app/settings")
        page.get_by_text("Optional integrations").wait_for()
        shot(page, "settings")
        page.goto(BASE + "/app/about")
        page.get_by_role("heading", name="From paper to product").wait_for()
        shot(page, "about")

        # ---- light mode of the app shell
        page.goto(review_url)
        page.get_by_role("tab", name=re.compile("Findings")).wait_for()
        page.get_by_role("button", name="Switch to light mode").click()
        page.wait_for_timeout(500)
        shot(page, "review_light_mode")

        # ---- top of a review (verdict banner, gauge, KPIs) in the default dark look
        page.get_by_role("button", name="Switch to dark mode").click()
        page.evaluate("window.scrollTo(0, 0)")
        shot(page, "review_verdict")

        ctx.close()
        browser.close()

    if problems:
        print("\nPROBLEMS")
        for pr in dict.fromkeys(problems):
            print(" -", pr)
        sys.exit(1)
    print(f"\n{count} screenshots saved, console clean.")


if __name__ == "__main__":
    try:
        main()
    except PWTimeout as e:
        print("Timed out waiting for a screen:", e)
        sys.exit(2)
