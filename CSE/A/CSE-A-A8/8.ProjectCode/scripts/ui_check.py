"""
Browser QA for LabLens: responsive layout, themes, reduced motion, drawer, keyboard, error states.

    python scripts/ui_check.py [--base http://localhost:5308] [--shots <folder>]

Run it against a running app that already has reports (use "Load sample reports" first). It signs in
with the demo account. Exit code 1 if any check fails. Needs: pip install playwright
"""

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

EMAIL, PASSWORD = "demo@lablens.com", "Demo@1234"
PAGES = ["/", "/login", "/app", "/app/upload", "/app/analysis", "/app/reports", "/app/trends", "/app/compare", "/app/insights", "/app/about"]
WIDTHS = [360, 768, 1440]
failures = []


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def sign_in(page, base):
    page.goto(base + "/login")
    page.click("button:has-text('Sign in as demo user')")
    page.wait_for_url("**/app")


def settle(page):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(900)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:5308")
    ap.add_argument("--shots", default=None)
    args = ap.parse_args()
    shots = Path(args.shots) if args.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = launch(p)

        print("Layout at 360 / 768 / 1440 px, light and dark (no horizontal overflow, no console errors)")
        for scheme in ("dark", "light"):
            for width in WIDTHS:
                ctx = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme)
                page = ctx.new_page()
                errors = []
                page.on("console", lambda m: m.type == "error" and errors.append(m.text))
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("response", lambda r: r.status >= 400 and r.status != 401 and errors.append(f"HTTP {r.status} {r.url}"))
                sign_in(page, args.base)
                for path in PAGES:
                    page.goto(args.base + path)
                    settle(page)
                    over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                    theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
                    check(f"{scheme:5} {width:4}px {path}", over <= 1 and theme == scheme and not errors, f"overflow={over} theme={theme} errors={errors[:2]}")
                    errors.clear()
                    if shots and width != 1440:
                        name = ("landing" if path == "/" else path.strip("/").replace("/", "_")) + f"_{width}_{scheme}.png"
                        page.screenshot(path=str(shots / name))
                ctx.close()

        print("Mobile drawer")
        ctx = browser.new_context(viewport={"width": 360, "height": 800})
        page = ctx.new_page()
        sign_in(page, args.base)
        page.goto(args.base + "/app")
        settle(page)
        check("sidebar hidden at 360px, menu button shown", page.locator("aside.sidebar").first.is_visible() is False and page.locator(".menu-btn").is_visible())
        page.click(".menu-btn")
        page.wait_for_selector("[role=dialog] nav")
        check("menu opens the navigation drawer", page.locator("[role=dialog] a:has-text('Health trends')").is_visible())
        page.keyboard.press("Escape")
        page.wait_for_selector("[role=dialog]", state="detached")
        check("Escape closes the drawer", True)
        page.click(".menu-btn")
        page.click("[role=dialog] a:has-text('Health trends')")
        page.wait_for_url("**/app/trends")
        try:
            page.wait_for_selector("[role=dialog]", state="detached", timeout=3000)  # exit animation
            closed = True
        except Exception:
            closed = False
        check("choosing a link navigates and closes the drawer", closed)
        ctx.close()

        print("Theme persistence")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
        page = ctx.new_page()
        sign_in(page, args.base)
        page.click("button[aria-label='Switch to light mode']")
        page.reload()
        settle(page)
        check("light theme survives a reload", page.evaluate("document.documentElement.getAttribute('data-theme')") == "light")
        check("choice stored in localStorage", page.evaluate("localStorage.getItem('ll-theme')") == "light")
        ctx.close()

        print("Reduced motion")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = ctx.new_page()
        page.goto(args.base + "/")
        settle(page)
        check("landing shows the static hero (no WebGL canvas)", page.locator(".hero canvas").count() == 0 and page.locator("img.hero-fallback").count() >= 1)
        check("how-it-works copy is visible without scroll animation", page.locator(".how-step").first.is_visible())
        ctx.close()

        print("Keyboard and focus")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        sign_in(page, args.base)
        page.goto(args.base + "/app/upload")
        settle(page)
        page.keyboard.press("Tab")
        check("first Tab stop is the skip link", page.evaluate("document.activeElement.classList.contains('skip-link')"))
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        ring = page.evaluate(
            "(() => { const s = getComputedStyle(document.activeElement); return s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0 || s.boxShadow !== 'none' })()"
        )
        check("focused control has a visible ring", ring)
        unlabelled = page.evaluate(
            """() => [...document.querySelectorAll('input,select,textarea')].filter(e => e.type !== 'hidden')
                 .filter(e => !(e.labels && e.labels.length) && !e.getAttribute('aria-label') && !e.getAttribute('aria-labelledby')).map(e => e.outerHTML.slice(0, 80))"""
        )
        check("every input has a label", not unlabelled, str(unlabelled))
        ctx.close()

        print("Error state when the API is unreachable")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        sign_in(page, args.base)
        page.route("**/api/dashboard", lambda route: route.abort())
        page.goto(args.base + "/app")
        page.wait_for_selector("text=Could not load the dashboard", timeout=15000)
        check("error says what failed and what to do", page.locator("text=Cannot reach the LabLens backend").count() == 1 and page.locator("button:has-text('Try again')").count() == 1)
        page.unroute("**/api/dashboard")
        page.click("button:has-text('Try again')")
        page.wait_for_selector("text=Recent reports", timeout=15000)
        check("Try again recovers once the API is back", True)
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED")
        sys.exit(1)
    print("All UI checks passed.")


if __name__ == "__main__":
    main()
