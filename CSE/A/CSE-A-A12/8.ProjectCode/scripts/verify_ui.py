"""
Responsive / theme / keyboard / reduced-motion checks against the running app.

    python scripts/verify_ui.py [--base http://localhost:5312] [--shots <dir>]

For 360, 768 and 1440 px in light and dark mode it opens every screen and fails on
horizontal overflow or console errors. It then checks Escape closes the delete dialog,
the theme choice survives a reload, and the landing page renders with reduced motion.
"""

import argparse
import os
import sys

from playwright.sync_api import sync_playwright

DEMO = {"email": "demo@pneumodetect.ai", "password": "Pneumo@123"}
SIZES = [(360, 740), (768, 1024), (1440, 900)]


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:5312")
    ap.add_argument("--shots", default=None)
    args = ap.parse_args()
    base = args.base
    problems = []
    if args.shots:
        os.makedirs(args.shots, exist_ok=True)

    with sync_playwright() as p:
        browser = launch(p)

        def new_page(w, h, scheme="light", reduced="no-preference"):
            ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, reduced_motion=reduced)
            page = ctx.new_page()
            page.on("console", lambda m: m.type == "error" and problems.append(f"{w}px {scheme} console: {m.text}"))
            page.on("pageerror", lambda e: problems.append(f"{w}px {scheme} pageerror: {e}"))
            page.on("response", lambda r: r.status >= 400 and problems.append(f"{w}px http {r.status}: {r.url}"))
            return ctx, page

        def login(page):
            page.goto(base + "/login")
            page.get_by_role("button", name="Fill demo credentials").click()
            page.get_by_role("button", name="Sign in", exact=True).click()
            page.wait_for_url("**/app")

        for w, h in SIZES:
            for scheme in ("light", "dark"):
                ctx, page = new_page(w, h, scheme)
                page.goto(base + "/")
                page.wait_for_load_state("networkidle")
                login(page)
                page.goto(base + "/app/history")
                page.wait_for_load_state("networkidle")
                rid = page.locator("a[href^='/app/result/']").first.get_attribute("href").rsplit("/", 1)[1]
                routes = ["/", "/login", "/app", "/app/detect", f"/app/result/{rid}", "/app/history", "/app/about", "/missing-page"]
                for r in routes:
                    page.goto(base + r)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1200)
                    over = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                    if over > 1:
                        problems.append(f"{w}px {scheme} {r}: horizontal overflow {over}px")
                    if args.shots:
                        name = (r.strip("/").replace("/", "_") or "landing")[:30]
                        page.screenshot(path=os.path.join(args.shots, f"{w}_{scheme}_{name}.png"), full_page=(r in ("/", "/app/history")))
                print(f"checked {w}px {scheme}")
                ctx.close()

        # mobile drawer + Escape
        ctx, page = new_page(360, 740)
        login(page)
        page.get_by_role("button", name="Open navigation").click()
        page.wait_for_timeout(500)
        if page.get_by_role("dialog").count() != 1:
            problems.append("mobile drawer did not open")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        if page.get_by_role("dialog").count() != 0:
            problems.append("Escape did not close the mobile drawer")
        ctx.close()

        # delete dialog: Escape closes it, focus lands inside it
        ctx, page = new_page(1440, 900)
        login(page)
        page.goto(base + "/app/history")
        page.wait_for_load_state("networkidle")
        page.locator("a[href^='/app/result/']").first.click()
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="Delete scan").click()
        page.wait_for_timeout(500)
        dlg = page.get_by_role("dialog")
        if dlg.count() != 1 or not page.evaluate("document.activeElement.closest('[role=dialog]') !== null"):
            problems.append("delete dialog missing or focus not inside it")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        if page.get_by_role("dialog").count() != 0:
            problems.append("Escape did not close the delete dialog")

        # theme persists across reloads
        page.get_by_role("button", name="Switch to dark mode").click()
        page.reload()
        page.wait_for_load_state("networkidle")
        if page.evaluate("document.documentElement.getAttribute('data-theme')") != "dark":
            problems.append("dark theme did not persist after reload")

        # visible focus ring on keyboard focus
        page.keyboard.press("Tab")
        outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
        if outline in ("none", ""):
            problems.append("no visible focus outline after Tab")
        ctx.close()

        # reduced motion: content must still be visible
        ctx, page = new_page(1440, 900, reduced="reduce")
        page.goto(base + "/")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        vis = page.evaluate("Number(getComputedStyle(document.querySelector('.cta-block')).opacity)")
        if vis < 0.99:
            problems.append(f"reduced motion: CTA block not fully visible (opacity {vis})")
        ctx.close()
        browser.close()

    if problems:
        print("\nPROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        return 1
    print("\nAll responsive, theme, keyboard and reduced-motion checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
