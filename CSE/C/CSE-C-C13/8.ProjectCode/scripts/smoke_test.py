"""Smoke test for CipherVault: API end-to-end check, then a real-browser walk of every screen.

Needs the app running (run.bat, or start the backend on 8413 and `npm run dev` in frontend/ on 5413).

    python scripts/smoke_test.py
    python scripts/smoke_test.py --app http://127.0.0.1:5413 --api http://127.0.0.1:8413

Part 1 runs scripts/e2e_check.py against the backend (real encryption, RBAC, audit chain).
Part 2 drives Chromium through the UI: register, upload, download + integrity, details, replace,
share / change role / revoke, audit + chain verification, lock / unlock, sign out, demo roles.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILS = []


def step(name, fn):
    t = time.time()
    try:
        fn()
        print(f"[PASS] {name} ({time.time() - t:.1f}s)")
    except Exception as exc:  # noqa: BLE001
        FAILS.append(name)
        print(f"[FAIL] {name}: {str(exc).splitlines()[0][:300]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default="http://127.0.0.1:5413")
    ap.add_argument("--api", default="http://127.0.0.1:8413")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    print("== Part 1: API end-to-end ==")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e2e_check.py"), "--url", args.api], cwd=str(ROOT))
    if r.returncode != 0:
        FAILS.append("e2e_check.py")

    print("\n== Part 2: browser walk ==")
    from playwright.sync_api import expect, sync_playwright

    stamp = int(time.time())
    email = f"smoke{stamp}@example.com"
    pw = "Smoke-Test-123"
    tmp = ROOT / "storage" / f"_smoke_{stamp}.txt"
    tmp.write_text("synthetic smoke-test payload " + "x" * 200, encoding="utf-8")
    tmp2 = ROOT / "storage" / f"_smoke_{stamp}_v2.txt"
    tmp2.write_text("replacement content for the smoke test", encoding="utf-8")
    name1, name2 = tmp.name, tmp2.name

    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=not args.headed)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        page.set_default_timeout(20000)
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on("console", lambda m: problems.append(f"console.error: {m.text}") if m.type == "error" and "status of 4" not in m.text else None)
        page.on("response", lambda r: problems.append(f"HTTP {r.status} {r.url}") if r.status >= 500 or (r.status == 404 and "/api/" not in r.url) else None)
        app = args.app

        def landing():
            page.goto(app + "/")
            expect(page.get_by_role("heading", level=1)).to_contain_text("before")
            expect(page.get_by_text("API online")).to_be_visible()

        def register():
            page.goto(app + "/register")
            page.get_by_label("Full name").fill("Smoke Tester")
            page.get_by_label("Email").fill(email)
            page.get_by_label("Password", exact=True).fill(pw)
            page.get_by_label("Confirm password").fill(pw)
            page.get_by_role("button", name="Create account").click()
            page.wait_for_url("**/app", timeout=60000)
            expect(page.get_by_role("heading", name="Welcome back, Smoke")).to_be_visible()
            expect(page.get_by_text("Vault unlocked").first).to_be_visible()

        def empty_state():
            page.get_by_role("link", name="My files").first.click()
            expect(page.get_by_text("Your vault is empty").first).to_be_visible()

        def upload():
            page.locator("input[type=file]").first.set_input_files(str(tmp))
            expect(page.get_by_text("Encrypted and uploaded")).to_be_visible()
            expect(page.get_by_role("cell", name=name1).first).to_be_visible()

        def download():
            with page.expect_download() as d:
                page.get_by_role("button", name=f"Decrypt and download {name1}").click()
            saved = Path(d.value.path()).read_text(encoding="utf-8")
            assert saved == tmp.read_text(encoding="utf-8"), "decrypted bytes differ from original"
            expect(page.get_by_text("Integrity verified")).to_be_visible()

        def details():
            page.get_by_role("button", name=f"Open details for {name1}").click()
            page.wait_for_url("**/app/files/*")
            expect(page.get_by_role("heading", level=1)).to_have_text(name1)
            expect(page.get_by_text("SHA-256 of plaintext")).to_be_visible()
            expect(page.get_by_text("File history")).to_be_visible()

        def replace():
            page.locator("input[aria-label='Choose replacement file']").set_input_files(str(tmp2))
            expect(page.get_by_text("Content replaced").first).to_be_visible()
            with page.expect_download() as d:
                page.get_by_role("button", name="Decrypt & download").click()
            assert Path(d.value.path()).read_text(encoding="utf-8") == tmp2.read_text(encoding="utf-8")

        def share():
            page.get_by_role("button", name="Share", exact=True).click()
            dlg = page.get_by_role("dialog")
            dlg.get_by_label("Recipient email").fill("editor@example.com")
            dlg.get_by_label("Role", exact=True).select_option("viewer")
            dlg.get_by_role("button", name="Grant access").click()
            expect(dlg.get_by_text("editor@example.com").first).to_be_visible()
            dlg.get_by_label("Role for editor@example.com").select_option("editor")
            expect(page.get_by_text("Role updated")).to_be_visible()
            dlg.get_by_label("Recipient email").fill("nobody-here@example.com")
            dlg.get_by_role("button", name="Grant access").click()
            expect(dlg.get_by_text("No registered user")).to_be_visible()

        def revoke():
            dlg = page.get_by_role("dialog")
            dlg.get_by_role("button", name="Revoke access for editor@example.com").click()
            dlg.get_by_role("button", name="Confirm revoke").click()
            expect(dlg.get_by_text("Not shared yet")).to_be_visible()
            page.keyboard.press("Escape")
            expect(page.get_by_role("dialog")).to_have_count(0)

        def audit():
            page.get_by_role("link", name="Audit log").first.click()
            expect(page.get_by_role("heading", level=1)).to_have_text("Audit log")
            page.get_by_role("button", name="Verify audit chain").click()
            expect(page.get_by_text("Audit chain valid").first).to_be_visible()
            page.get_by_label("Filter by action").select_option("upload")
            expect(page.get_by_role("cell", name="File uploaded").first).to_be_visible()

        def dashboard():
            page.get_by_role("link", name="Dashboard").first.click()
            expect(page.get_by_text("Security events")).to_be_visible()
            page.get_by_role("button", name="Verify audit chain").click()
            expect(page.get_by_text("Audit chain valid").first).to_be_visible()

        def lock_unlock():
            page.get_by_role("link", name="Security").first.click()
            page.get_by_role("button", name="Lock vault now").click()
            expect(page.get_by_text("Locked").first).to_be_visible()
            page.get_by_role("button", name="Unlock vault").click()
            dlg = page.get_by_role("dialog")
            dlg.get_by_label("Password").fill("wrong-password")
            dlg.get_by_role("button", name="Unlock").click()
            expect(dlg.get_by_text("Wrong password")).to_be_visible()
            dlg.get_by_label("Password").fill(pw)
            dlg.get_by_role("button", name="Unlock").click()
            expect(page.get_by_text("Unlocked in memory")).to_be_visible()

        def delete_file():
            page.get_by_role("link", name="My files").first.click()
            page.get_by_role("button", name=f"Delete {name1}").click()
            page.get_by_role("button", name="Delete permanently").click()
            expect(page.get_by_text("File deleted")).to_be_visible()
            expect(page.get_by_text("Your vault is empty").first).to_be_visible()

        def reload_locks():
            page.reload()
            expect(page.get_by_role("dialog").get_by_text("Unlock your vault")).to_be_visible()
            page.keyboard.press("Escape")
            expect(page.get_by_role("dialog")).to_have_count(0)

        def signout():
            page.get_by_role("button", name="Sign out").first.click()
            page.wait_for_url(app + "/")
            page.goto(app + "/app")
            page.wait_for_url("**/login")

        def bad_login():
            page.get_by_label("Email").fill(email)
            page.get_by_label("Password").fill("not-the-password")
            page.get_by_role("button", name="Sign in", exact=True).click()
            expect(page.get_by_text("Invalid email or password")).to_be_visible()

        def demo_viewer():
            page.get_by_role("button", name="Viewer", exact=True).click()
            page.wait_for_url("**/app", timeout=120000)
            page.get_by_role("link", name="Shared with me").first.click()
            expect(page.get_by_role("heading", level=1)).to_have_text("Shared with me")
            rows = page.get_by_role("row")
            expect(rows.nth(1)).to_be_visible()
            assert page.get_by_role("button", name="Delete", exact=False).count() == 0, "viewer must not see delete"
            assert page.get_by_role("button", name="Share ", exact=False).count() == 0, "viewer must not see share"
            with page.expect_download():
                page.get_by_role("button", name="Decrypt and download").first.click()

        def responsive():
            for w, h in [(360, 740), (768, 1024)]:
                page.set_viewport_size({"width": w, "height": h})
                for route in ["/", "/login", "/app", "/app/files", "/app/shared", "/app/audit", "/app/security"]:
                    page.goto(app + route)
                    page.wait_for_timeout(700)
                    width = page.evaluate("document.documentElement.scrollWidth")
                    assert width <= w + 1, f"horizontal overflow on {route} at {w}px (scrollWidth {width})"

        for n, f in [
            ("landing renders, API online", landing),
            ("register creates keys + unlocks vault", register),
            ("empty state with action", empty_state),
            ("encrypted upload", upload),
            ("download decrypts + verifies SHA-256", download),
            ("file details + history", details),
            ("replace content (PUT) round-trips", replace),
            ("share, change role, unknown user error", share),
            ("revoke access", revoke),
            ("audit log + verify chain", audit),
            ("dashboard + verify chain", dashboard),
            ("lock / wrong password / unlock", lock_unlock),
            ("delete file", delete_file),
            ("reload locks the vault", reload_locks),
            ("sign out + route guard", signout),
            ("wrong password shows error", bad_login),
            ("demo viewer: shared files, RBAC UI", demo_viewer),
            ("no horizontal overflow at 360 / 768", responsive),
        ]:
            step(n, f)
        browser.close()

    tmp.unlink(missing_ok=True)
    tmp2.unlink(missing_ok=True)
    if problems:
        print("\nBrowser problems:")
        for x in dict.fromkeys(problems):
            print("  -", x)
        FAILS.append("browser console/network")
    print("\nSMOKE TEST", "FAILED: " + ", ".join(FAILS) if FAILS else "PASSED")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
