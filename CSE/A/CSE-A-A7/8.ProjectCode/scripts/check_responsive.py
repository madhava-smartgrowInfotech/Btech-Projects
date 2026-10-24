"""Layout, theme, reduced-motion and keyboard checks against the running app.

For widths 360 / 768 / 1440 in light and dark: every screen must not scroll sideways and must log no
console errors. Also checks: theme toggle persists across reload, reduced-motion renders, mobile drawer
opens and closes with Escape, the override modal closes with Escape, and tab focus is visible.
Optional second argument: a folder to save screenshots into.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5307"
SHOTS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
problems = []


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        problems.append(msg)


def launch(p):
    try:
        return p.chromium.launch(channel="chrome", headless=True)
    except Exception:
        return p.chromium.launch(headless=True)


def row_sel(w):
    # the kit Table renders cards below 640px and a real table above
    return ".row-card" if w < 640 else "tbody tr"


def settle(page, ms=1200):
    page.wait_for_timeout(ms)


def overflow(page):
    return page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")


def main():
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = launch(p)
        errors = []
        for scheme in ("light", "dark"):
            for w, h in ((360, 740), (768, 1024), (1440, 900)):
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                page = ctx.new_page()
                page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(BASE + "/")
                page.wait_for_selector(".checks-stack")
                settle(page, 2200)
                ok(overflow(page) <= 0, f"landing {w}px {scheme}: no horizontal scroll (over by {overflow(page)})")
                if SHOTS:
                    page.screenshot(path=str(SHOTS / f"landing_{w}_{scheme}.png"))
                page.goto(BASE + "/login")
                page.get_by_role("button", name="Clinician").click()
                page.wait_for_url("**/app/queue")
                page.wait_for_selector(row_sel(w))
                for route, ready in (("/app/queue", "h1:has-text('Triage queue')"), ("/app/new", "h1:has-text('New patient')"), ("/app/performance", "h2:has-text('Confusion matrix')")):
                    page.goto(BASE + route)
                    page.wait_for_selector(ready)
                    settle(page)
                    ok(overflow(page) <= 0, f"{route} {w}px {scheme}: no horizontal scroll (over by {overflow(page)})")
                    if SHOTS and w == 360:
                        page.screenshot(path=str(SHOTS / f"{route.strip('/').replace('/', '_')}_{w}_{scheme}.png"))
                page.goto(BASE + "/app/queue")
                page.wait_for_selector(row_sel(w))
                page.locator(row_sel(w)).first.click()
                page.wait_for_selector("text=Why this priority")
                settle(page)
                ok(overflow(page) <= 0, f"result {w}px {scheme}: no horizontal scroll (over by {overflow(page)})")
                if SHOTS and w == 360:
                    page.screenshot(path=str(SHOTS / f"result_{w}_{scheme}.png"))
                ctx.close()
        ok(not errors, f"no console errors across all sizes {sorted(set(errors))[:3]}")

        # theme toggle persists
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page = ctx.new_page()
        page.goto(BASE + "/")
        page.wait_for_selector(".checks-stack")
        page.get_by_role("button", name="Switch to dark mode").click()
        ok(page.evaluate("document.documentElement.dataset.theme") == "dark", "toggle switches to dark")
        page.reload()
        page.wait_for_selector(".checks-stack")
        ok(page.evaluate("document.documentElement.dataset.theme") == "dark", "dark theme persists after reload")
        ctx.close()

        # reduced motion
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = ctx.new_page()
        page.goto(BASE + "/")
        page.wait_for_selector(".checks-stack")
        settle(page, 1500)
        anim = page.evaluate("getComputedStyle(document.querySelector('.marquee-track')).animationName")
        ok(anim == "none", f"reduced motion: marquee animation off (got {anim})")
        ok("EVERY PRIORITY" in page.inner_text("h1").upper(), "reduced motion: headline visible")
        ctx.close()

        # keyboard: mobile drawer + modal Escape + focus ring
        ctx = browser.new_context(viewport={"width": 360, "height": 740})
        page = ctx.new_page()
        page.goto(BASE + "/login")
        page.get_by_role("button", name="Clinician").click()
        page.wait_for_url("**/app/queue")
        page.wait_for_timeout(600)
        page.get_by_role("button", name="Open navigation").click()
        page.wait_for_selector("role=dialog")
        ok(True, "drawer opens at 360px")
        page.keyboard.press("Escape")
        settle(page, 600)
        ok(page.locator("role=dialog").count() == 0, "Escape closes the drawer")
        page.wait_for_selector(row_sel(360))
        page.locator(row_sel(360)).first.click()
        page.wait_for_selector("text=Why this priority")
        page.get_by_role("button", name="Accept or change").first.click()
        page.wait_for_selector("role=dialog")
        page.keyboard.press("Escape")
        settle(page, 600)
        ok(page.locator("role=dialog").count() == 0, "Escape closes the override modal")
        page.keyboard.press("Tab")
        outline = page.evaluate("(() => { const e = document.activeElement; return e ? getComputedStyle(e).outlineStyle + ' ' + getComputedStyle(e).outlineWidth : '' })()")
        ok(outline.startswith("solid") and not outline.endswith(" 0px"), f"focused element shows a focus ring ({outline})")
        ctx.close()
        browser.close()

    print("\nRESPONSIVE CHECK", "FAILED" if problems else "PASSED")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
