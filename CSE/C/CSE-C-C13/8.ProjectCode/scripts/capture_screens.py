"""Capture 1440x900 screenshots of every CipherVault screen into docs/screenshots/.

Needs the app running (run.bat). Uses the built-in demo accounts, so every screen shows real data:
the demo owner has files, shares and audit history; the demo viewer shows "Shared with me".

    python scripts/capture_screens.py [--app http://127.0.0.1:5413]
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
GL = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default="http://127.0.0.1:5413")
    args = ap.parse_args()
    app = args.app

    def shot(page, name, wait=1400, full=False):
        page.wait_for_timeout(wait)
        path = OUT / f"{name}.png"
        page.screenshot(path=str(path), full_page=full)
        print("saved", path.relative_to(ROOT))

    def theme_ctx(browser, scheme, w=1440, h=900):
        ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
        ctx.add_init_script(f"try{{localStorage.setItem('cv-theme','{scheme}')}}catch(e){{}}")
        return ctx

    def demo(page, role):
        page.goto(app + "/login")
        page.get_by_role("button", name=role, exact=True).click()
        page.wait_for_url("**/app", timeout=180000)
        page.wait_for_timeout(1500)

    def nav(page, label):
        page.get_by_role("link", name=label).first.click()
        page.wait_for_timeout(1200)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=GL)

        # landing in both modes
        for scheme in ("light", "dark"):
            ctx = theme_ctx(browser, scheme)
            page = ctx.new_page()
            page.goto(app + "/")
            shot(page, f"01_landing-{scheme}", wait=3000)
            if scheme == "dark":
                page.mouse.wheel(0, 1500)
                shot(page, "02_landing-how-it-works-dark", wait=1800)
                page.mouse.wheel(0, 2600)
                shot(page, "03_landing-features-dark", wait=1800)
            ctx.close()

        # auth screens + app, dark
        ctx = theme_ctx(browser, "dark")
        page = ctx.new_page()
        page.goto(app + "/login")
        shot(page, "04_sign-in")
        page.goto(app + "/register")
        shot(page, "05_register")

        demo(page, "Owner")
        shot(page, "06_dashboard", wait=2200)
        nav(page, "My files")
        shot(page, "07_my-files")
        # file detail of the memo (shared, edited by the editor, denied delete by the viewer)
        page.get_by_role("button", name="Open details for Q3-board-memo.txt").first.click()
        page.wait_for_url("**/app/files/*")
        shot(page, "08_file-detail", wait=1800, full=True)
        page.get_by_role("button", name="Share", exact=True).click()
        shot(page, "09_share-access", wait=1200)
        page.keyboard.press("Escape")
        nav(page, "Audit log")
        page.get_by_role("button", name="Verify audit chain").click()
        shot(page, "10_audit-log", wait=1800)
        nav(page, "Security")
        shot(page, "11_security")
        page.get_by_role("button", name="Lock vault now").click()
        page.get_by_role("button", name="Unlock vault").click()
        shot(page, "12_unlock-vault", wait=700)
        ctx.close()

        # viewer: shared-with-me
        ctx = theme_ctx(browser, "dark")
        page = ctx.new_page()
        demo(page, "Viewer")
        nav(page, "Shared with me")
        shot(page, "13_shared-with-me")
        ctx.close()

        # app in light mode (dashboard)
        ctx = theme_ctx(browser, "light")
        page = ctx.new_page()
        demo(page, "Owner")
        shot(page, "14_dashboard-light", wait=2200)
        ctx.close()

        # mobile 360px
        ctx = theme_ctx(browser, "dark", 360, 740)
        page = ctx.new_page()
        demo(page, "Owner")
        shot(page, "15_mobile-dashboard-360", wait=1800)
        page.get_by_role("button", name="Open navigation").click()
        shot(page, "16_mobile-nav-drawer-360", wait=700)
        browser.close()


if __name__ == "__main__":
    main()
