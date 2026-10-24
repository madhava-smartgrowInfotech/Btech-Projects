"""UI acceptance checks in a real browser: every route at 360 / 768 / 1440 px in light and dark mode
(no horizontal scroll, clean console), the mobile drawer, keyboard navigation, theme persistence and reduced motion.

Usage:  python scripts/check_ui.py [frontend_url]     (run.bat must be running)
"""
from __future__ import annotations

import os
import sys

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5310").rstrip("/")
CHANNEL = os.environ.get("CHANNEL", "chrome")
ROUTES = ["/", "/login", "/app", "/app/benchmark", "/app/vision", "/app/prediction", "/app/violations", "/app/about"]
fails: list[str] = []
problems: list[str] = []


def check(name, ok, extra=""):
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{extra}]" if extra and not ok else ""))
    if not ok:
        fails.append(name)


def new_page(browser, w, h, theme, reduced=False, token=None):
    ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=theme, reduced_motion="reduce" if reduced else "no-preference")
    page = ctx.new_page()
    page.on("console", lambda m: problems.append(f"[{w}px {theme}] console {m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: problems.append(f"[{w}px {theme}] pageerror {e}"))
    page.on("response", lambda r: problems.append(f"[{w}px {theme}] http {r.status} {r.url}") if r.status >= 400 and "/auth/login" not in r.url else None)
    page.goto(BASE + "/login")
    page.evaluate(f"localStorage.setItem('fs_theme','{theme}')")
    if token:
        page.evaluate(f"localStorage.setItem('fs_token','{token}')")
    return ctx, page


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=CHANNEL, headless=True) if CHANNEL else p.chromium.launch(headless=True)
        # sign in once through the UI to get a token
        ctx, page = new_page(browser, 1440, 900, "dark")
        page.reload()
        page.get_by_role("button", name="Use demo account").click()
        page.wait_for_url("**/app")
        token = page.evaluate("localStorage.getItem('fs_token')")
        check("demo sign-in stores a token", bool(token))
        ctx.close()

        # ---- every route x width x theme
        for theme in ("dark", "light"):
            for w, h in ((360, 780), (768, 1024), (1440, 900)):
                ctx, page = new_page(browser, w, h, theme, token=token)
                for r in ROUTES:
                    page.goto(BASE + r)
                    page.wait_for_timeout(1400 if r != "/" else 2200)
                    over = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                    shown = page.evaluate("document.documentElement.dataset.theme")
                    check(f"{theme} {w}px {r}: no horizontal scroll, theme applied", over <= 1 and shown == theme, f"overflow {over}, theme {shown}")
                ctx.close()

        # ---- mobile drawer + keyboard
        ctx, page = new_page(browser, 360, 780, "dark", token=token)
        page.goto(BASE + "/app")
        page.wait_for_timeout(1200)
        page.get_by_role("button", name="Open navigation").click()
        page.wait_for_timeout(600)
        check("360px: sidebar becomes a drawer", page.get_by_role("dialog", name="Navigation").is_visible())
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        check("Escape closes the drawer", page.get_by_role("dialog").count() == 0)
        ctx.close()

        ctx, page = new_page(browser, 1440, 900, "dark", token=token)
        page.goto(BASE + "/app")
        page.wait_for_timeout(1200)
        page.keyboard.press("g")
        page.keyboard.press("b")
        page.wait_for_url("**/app/benchmark", timeout=5000)
        check("keyboard: g b opens Benchmark", True)
        page.keyboard.press("/")
        page.wait_for_timeout(500)
        check("keyboard: / opens the screen switcher", page.get_by_role("dialog", name="Jump to screen").is_visible())
        page.keyboard.type("vis")
        page.keyboard.press("Enter")
        page.wait_for_url("**/app/vision", timeout=5000)
        check("palette: typing 'vis' + Enter opens Vision", True)
        page.wait_for_timeout(900)
        page.keyboard.press("Shift+Slash")
        page.wait_for_timeout(500)
        check("keyboard: ? shows shortcuts", page.get_by_role("dialog", name="Keyboard shortcuts").is_visible())
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        check("Escape closes the shortcuts dialog", page.get_by_role("dialog").count() == 0)
        page.keyboard.press("Tab")
        ring = page.evaluate("(() => { const e = document.activeElement; return e ? getComputedStyle(e).outlineStyle + ' ' + getComputedStyle(e).outlineWidth : '' })()")
        check("keyboard focus shows a visible ring", "solid" in ring and not ring.endswith(" 0px"), ring)
        unlabelled = page.evaluate("""() => [...document.querySelectorAll('input, select, textarea')].filter(e => {
            if (e.type === 'file') return false
            const id = e.id; const hasFor = id && document.querySelector('label[for="' + id + '"]')
            return !(hasFor || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby') || e.closest('label'))
        }).length""")
        check("every input on Vision is labelled", unlabelled == 0, str(unlabelled))
        # theme toggle persists across a reload
        page.get_by_role("button", name="Switch to light mode").click()
        page.reload()
        page.wait_for_timeout(800)
        check("theme toggle persists after reload", page.evaluate("document.documentElement.dataset.theme") == "light")
        ctx.close()

        # ---- reduced motion: no WebGL canvas, content still there
        ctx, page = new_page(browser, 1440, 900, "dark", reduced=True, token=token)
        page.goto(BASE + "/")
        page.wait_for_timeout(2500)
        check("reduced motion: no animated three.js canvas", page.locator("canvas").count() == 0)
        check("reduced motion: headline fully visible", page.get_by_role("heading", level=1).inner_text().replace("\n", " ").strip().endswith("Coordinate."))
        ctx.close()

        # ---- normal motion: canvas is present on the landing page
        ctx, page = new_page(browser, 1440, 900, "dark", token=token)
        page.goto(BASE + "/")
        page.wait_for_timeout(2500)
        check("normal motion: three.js wire-grid canvas renders", page.locator("canvas").count() >= 1)
        ctx.close()
        browser.close()

    if problems:
        print("\nconsole / network problems:")
        for x in dict.fromkeys(problems):
            print("  ", x)
    print("\n%d failed" % (len(fails) + (1 if problems else 0)) if (fails or problems) else "\nALL UI CHECKS PASSED")
    sys.exit(1 if (fails or problems) else 0)


if __name__ == "__main__":
    main()
