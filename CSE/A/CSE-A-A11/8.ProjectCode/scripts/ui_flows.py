"""Drive the real UI through every feature of the product and assert what happens. Needs the stack running (run.bat).

    python scripts/ui_flows.py
Covers: sign-in errors, register, all five review inputs, filters, exports, delete, codebase sources, lab, settings,
theme persistence, keyboard (Escape / focus), reduced motion and the 'API is down' error state.
"""
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 5311
for line in (ROOT / ".env").read_text().splitlines() if (ROOT / ".env").exists() else []:
    if line.startswith("FRONTEND_PORT="):
        PORT = int(line.split("=", 1)[1])
BASE = f"http://127.0.0.1:{PORT}"

VULN = 'def f(n):\n    cur.execute(f"SELECT * FROM t WHERE a = \'{n}\'")\n'
DIFF = ("diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -0,0 +1,3 @@\n+import os\n+def run(h):\n+    os.system('ping ' + h)\n")

passed, failed = 0, 0
console_errors: list[str] = []


def step(name):
    def deco(fn):
        def run(*a, **k):
            global passed, failed
            try:
                fn(*a, **k)
                passed += 1
                print("PASS ", name)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print("FAIL ", name, "->", str(e).splitlines()[0][:200])
        return run
    return deco


def new_page(browser, **kw):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, **kw)
    page = ctx.new_page()
    page.set_default_timeout(20000)
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" and "401" not in m.text and "409" not in m.text and "422" not in m.text and "Failed to load resource" not in m.text else None)
    page.on("pageerror", lambda e: console_errors.append(str(e)))
    return ctx, page


def demo_login(page):
    page.goto(BASE + "/login")
    page.get_by_text("Use the demo account").click()
    page.wait_for_url(re.compile(r".*/app(/.*)?$"))


def run_review(page):
    page.get_by_role("button", name=re.compile("Run multi-agent review")).click()
    page.wait_for_url(re.compile(r".*/app/review/.+"), timeout=60000)
    page.get_by_role("tab", name=re.compile("Findings")).wait_for()


def main():
    tmp = Path(tempfile.mkdtemp(prefix="autosecai-ui-"))
    (tmp / "vuln.py").write_text(VULN)
    (tmp / "app.diff").write_text(DIFF)
    zp = tmp / "repo.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("repo/app.py", "from flask import Flask, request\napp = Flask(__name__)\n\n@app.route('/login', methods=['POST'])\ndef login():\n    \"\"\"Log in.\"\"\"\n    return 'ok'\n")
        z.writestr("repo/db.py", "import sqlite3\n\ndef get():\n    return sqlite3.connect('x.db')\n")

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------------------------------------------------------------- auth
        ctx, page = new_page(browser, color_scheme="dark")

        @step("protected route redirects to sign-in")
        def _():
            page.goto(BASE + "/app/history")
            page.wait_for_url("**/login")
        _()

        @step("wrong password shows a readable error")
        def _():
            page.goto(BASE + "/login")
            page.get_by_label("Email").fill("demo@autosecai.dev")
            page.get_by_label("Password", exact=True).fill("nope-nope")
            page.get_by_role("button", name="Sign in", exact=True).last.click()
            expect(page.get_by_role("alert")).to_contain_text("incorrect")
        _()

        @step("register a new account lands in the app")
        def _():
            page.goto(BASE + "/login")
            page.get_by_role("tab", name="Create account").click()
            page.get_by_label("Name").fill("UI Flow Tester")
            page.get_by_label("Email").fill(f"ui{abs(hash(tmp))}@example.com")
            page.get_by_label("Password", exact=True).fill("Passw0rd!x")
            page.get_by_role("button", name="Create account").last.click()
            page.wait_for_url(re.compile(r".*/app(/.*)?$"))
            expect(page.get_by_text("UI Flow Tester").first).to_be_visible()
        _()

        @step("sign out returns to sign-in and blocks the app")
        def _():
            page.get_by_role("button", name="Account menu").click()
            page.get_by_role("menuitem", name="Sign out").click()
            page.wait_for_url("**/login")
            page.goto(BASE + "/app")
            page.wait_for_url("**/login")
        _()

        demo_login(page)

        # ---------------------------------------------------------------- reviews
        @step("review: demo diff, filters, search, expand finding")
        def _():
            page.goto(BASE + "/app/review")
            run_review(page)
            expect(page.get_by_text(re.compile(r"Showing \d+ of \d+ findings"))).to_be_visible()
            page.get_by_label("Search findings").fill("sql")
            expect(page.get_by_text(re.compile(r"Showing [1-9]\d* of"))).to_be_visible()
            page.get_by_label("Search findings").fill("zzzz-nothing")
            expect(page.get_by_text("Nothing matches these filters")).to_be_visible()
            page.get_by_role("button", name="Reset filters").click()
            page.locator("main button[aria-expanded][aria-controls]").first.click()
            expect(page.get_by_text("How to fix").first).to_be_visible()
        _()

        @step("review: export tab downloads md / sarif / json / csv")
        def _():
            page.get_by_role("tab", name=re.compile("Export")).click()
            expect(page.get_by_text("PR comment preview")).to_be_visible()
            for label in ("PR comment (.md)", "SARIF 2.1", "Full JSON", "Findings CSV"):
                with page.expect_download() as d:
                    page.get_by_role("button", name=re.compile(re.escape(label))).click()
                assert d.value.suggested_filename.startswith("autosecai-"), d.value.suggested_filename
        _()

        @step("review: compare two versions finds the SQL injection and offers a fixed file")
        def _():
            page.goto(BASE + "/app/review")
            page.get_by_role("tab", name=re.compile("Compare versions")).click()
            page.get_by_label("File name").fill("svc.py")
            page.get_by_label("After").fill(VULN)
            run_review(page)
            expect(page.get_by_text("SQL injection").first).to_be_visible()
            page.get_by_role("tab", name=re.compile("Export")).click()
            with page.expect_download():
                page.get_by_role("button", name=re.compile("svc.py")).click()
        _()

        @step("review: pasted diff (typed) and diff file upload")
        def _():
            page.goto(BASE + "/app/review")
            page.get_by_role("tab", name=re.compile("Paste diff")).click()
            run_btn = page.get_by_role("button", name=re.compile("Run multi-agent review"))
            expect(run_btn).to_be_disabled()
            page.locator("input[type=file]").set_input_files(str(tmp / "app.diff"))
            expect(page.get_by_label("Unified diff (git diff / PR .diff)")).to_have_value(re.compile("os.system"))
            run_review(page)
            expect(page.get_by_text("OS command injection").first).to_be_visible()
        _()

        @step("review: bad pasted diff shows an error, GitHub link error is readable")
        def _():
            page.goto(BASE + "/app/review")
            page.get_by_role("tab", name=re.compile("Paste diff")).click()
            page.get_by_label("Unified diff (git diff / PR .diff)").fill("this is not a diff")
            page.get_by_role("button", name=re.compile("Run multi-agent review")).click()
            expect(page.get_by_text("Could not complete the review")).to_be_visible()
            page.get_by_role("tab", name=re.compile("GitHub PR link")).click()
            page.get_by_label("Pull request URL").fill("https://example.com/not/a/pr")
            page.get_by_role("button", name=re.compile("Run multi-agent review")).click()
            expect(page.get_by_text(re.compile("Not a GitHub pull request URL"))).to_be_visible()
        _()

        @step("review: upload a file and a zip (full scan)")
        def _():
            page.goto(BASE + "/app/review")
            page.get_by_role("tab", name=re.compile("Upload files")).click()
            page.locator("input[type=file]").set_input_files([str(tmp / "vuln.py"), str(zp)])
            expect(page.get_by_text("vuln.py")).to_be_visible()
            run_review(page)
            expect(page.get_by_text("SQL injection").first).to_be_visible()
        _()

        @step("review: local folder path")
        def _():
            page.goto(BASE + "/app/review")
            page.get_by_role("tab", name=re.compile("Upload files")).click()
            page.get_by_label(re.compile("local folder path")).fill(str(ROOT / "tests"))
            run_review(page)
        _()

        @step("review: ML and Files and Agent trace tabs render data")
        def _():
            for t, needle in (("Function risk", "Inspect a function"), ("Files", "Files in the change"), ("Agent trace", "Ingestion Agent")):
                page.get_by_role("tab", name=re.compile(t)).click()
                expect(page.get_by_text(needle).first).to_be_visible()
        _()

        @step("history: open, search, delete with confirm and Escape")
        def _():
            page.goto(BASE + "/app/history")
            expect(page.get_by_text("Risk score over time")).to_be_visible()
            rows_before = page.locator("main tbody tr").count()
            page.get_by_role("button", name=re.compile("^Delete ")).first.click()
            expect(page.get_by_role("dialog")).to_be_visible()
            page.keyboard.press("Escape")
            expect(page.get_by_role("dialog")).to_have_count(0)
            assert page.locator("main tbody tr").count() == rows_before
            page.get_by_role("button", name=re.compile("^Delete ")).first.click()
            page.get_by_role("dialog").get_by_role("button", name="Delete").click()
            expect(page.get_by_text(re.compile("Deleted"))).to_be_visible()
        _()

        # ---------------------------------------------------------------- codebase
        @step("codebase: demo repo index, suggested question, typed question, map, guide")
        def _():
            page.goto(BASE + "/app/codebase")
            expect(page.get_by_text("Index a repository to start asking questions")).to_be_visible()
            page.get_by_role("button", name=re.compile("Index repository")).click()
            expect(page.get_by_role("tab", name="Ask")).to_be_visible()
            page.get_by_label("Ask about the codebase").fill("Where is the database accessed?")
            page.get_by_role("button", name="Send question").click()
            expect(page.locator(".prose-answer").first).to_be_visible()
            page.get_by_text(re.compile(r"\.py")).first.wait_for()
            page.get_by_role("tab", name=re.compile("Repository map")).click()
            expect(page.get_by_role("heading", name="API routes")).to_be_visible()
            page.get_by_role("tab", name=re.compile("Onboarding guide")).click()
            expect(page.get_by_text("Onboarding guide for").first).to_be_visible()
        _()

        @step("codebase: this project, zip upload, bad folder error")
        def _():
            page.goto(BASE + "/app/codebase")
            page.get_by_role("combobox").first.click()
            page.get_by_role("option", name=re.compile("AutoSecAI")).click()
            page.get_by_role("button", name=re.compile("Index repository")).click()
            expect(page.get_by_text(re.compile("Indexed \\d+ files"))).to_be_visible()
            page.get_by_role("combobox").first.click()
            page.get_by_role("option", name="Upload .zip").click()
            page.locator("input[type=file]").set_input_files(str(zp))
            page.get_by_role("button", name=re.compile("Index repository")).click()
            expect(page.get_by_text(re.compile("Indexed 2 files"))).to_be_visible()
            page.get_by_role("combobox").first.click()
            page.get_by_role("option", name="Local folder").click()
            page.get_by_label("Folder path").fill("Z:/definitely/missing")
            page.get_by_role("button", name=re.compile("Index repository")).click()
            expect(page.get_by_text("Indexing failed")).to_be_visible()
        _()

        # ---------------------------------------------------------------- lab, settings, theme
        @step("lab: every tab renders, Try it analyses code, retrain asks first")
        def _():
            page.goto(BASE + "/app/lab")
            expect(page.get_by_text("The 14 metrics")).to_be_visible()
            for t, needle in (("Feature selection", "Importance of each metric"), ("Models", "Nine models"), ("ROC", "Confusion matrix"),
                              ("Vulnerability types", "F1 per vulnerability type"), ("Ablation", "Honest comparison")):
                page.get_by_role("tab", name=re.compile(t)).click()
                expect(page.get_by_text(re.compile(needle)).first).to_be_visible()
            page.get_by_role("tab", name=re.compile("Try it")).click()
            page.get_by_role("button", name=re.compile("Analyse function")).click()
            expect(page.get_by_text("Static findings")).to_be_visible()
            page.get_by_label("Python code").fill("def (")
            page.get_by_role("button", name=re.compile("Analyse function")).click()
            expect(page.get_by_text("Could not parse that as Python")).to_be_visible()
            page.get_by_role("button", name=re.compile("Retrain models")).click()
            expect(page.get_by_role("dialog")).to_contain_text("Retrain all models?")
            page.keyboard.press("Escape")
        _()

        @step("settings persist across reload and change the review options")
        def _():
            page.goto(BASE + "/app/settings")
            page.get_by_label("ML risk agent (base paper)").click()
            page.get_by_label("GitHub token (optional)").fill("ghp_test")
            page.reload()
            expect(page.get_by_label("ML risk agent (base paper)")).to_have_attribute("aria-checked", "false")
            page.goto(BASE + "/app/review")
            expect(page.get_by_text("ML risk agent off")).to_be_visible()
            run_review(page)
            page.get_by_role("tab", name=re.compile("Function risk")).click()
            expect(page.get_by_text("No functions were scored")).to_be_visible()
            page.goto(BASE + "/app/settings")
            page.get_by_role("button", name="Reset settings").click()
        _()

        @step("theme toggle persists across reload")
        def _():
            page.goto(BASE + "/app")
            page.get_by_role("button", name="Switch to light mode").click()
            assert "dark" not in (page.evaluate("document.documentElement.className") or "")
            page.reload()
            assert "dark" not in (page.evaluate("document.documentElement.className") or "")
            page.get_by_role("button", name="Switch to dark mode").click()
            page.reload()
            assert "dark" in page.evaluate("document.documentElement.className")
        _()

        @step("keyboard: skip link, focus ring and mobile drawer closes on Escape")
        def _():
            page.goto(BASE + "/app")
            page.keyboard.press("Tab")
            expect(page.get_by_text("Skip to content")).to_be_visible()
            page.keyboard.press("Tab")
            outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
            assert outline != "none", outline
            ctx.close()
            m_ctx, m = new_page(browser, color_scheme="dark")
            m.set_viewport_size({"width": 360, "height": 740})
            demo_login(m)
            m.get_by_role("button", name="Open menu").click()
            expect(m.get_by_role("dialog")).to_be_visible()
            m.keyboard.press("Escape")
            expect(m.get_by_role("dialog")).to_have_count(0)
            m_ctx.close()
        _()

        # ---------------------------------------------------------------- reduced motion + API down
        @step("reduced motion: landing and app render and the pinned section falls back to a list")
        def _():
            r_ctx, r = new_page(browser, reduced_motion="reduce", color_scheme="dark")
            r.goto(BASE + "/")
            expect(r.get_by_role("heading", level=1)).to_be_visible()
            r.locator("#how-it-works").scroll_into_view_if_needed()
            r.mouse.wheel(0, 300)
            expect(r.get_by_text("Hand over the change").last).to_be_visible()  # the plain list layout
            expect(r.locator(".hiw-card").first).to_be_hidden()  # the pinned desktop layout is not used
            demo_login(r)
            expect(r.get_by_role("heading", level=1)).to_be_visible()
            r_ctx.close()
        _()

        @step("API unreachable: pages say what failed and offer a retry")
        def _():
            e_ctx, e = new_page(browser, color_scheme="dark")
            demo_login(e)
            e.route("**/api/reviews**", lambda route: route.abort())
            e.goto(BASE + "/app/history")
            expect(e.get_by_text("Couldn't load your history")).to_be_visible()
            expect(e.get_by_text(re.compile("Can't reach the AutoSecAI API"))).to_be_visible()
            expect(e.get_by_role("button", name="Try again")).to_be_visible()
            e_ctx.close()
        _()

        @step("unknown routes show a friendly 404")
        def _():
            n_ctx, n = new_page(browser, color_scheme="dark")
            demo_login(n)
            n.goto(BASE + "/app/review/does-not-exist")
            expect(n.get_by_text("Couldn't open this review")).to_be_visible()
            n.goto(BASE + "/app/nope")
            expect(n.get_by_text("That page doesn't exist")).to_be_visible()
            n_ctx.close()
        _()

        browser.close()

    real = [e for e in console_errors if e]
    print(f"\n{passed} passed, {failed} failed; console errors: {len(real)}")
    for e in dict.fromkeys(real):
        print(" -", e[:200])
    sys.exit(1 if failed or real else 0)


if __name__ == "__main__":
    main()
