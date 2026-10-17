"""
Layout / accessibility checks for every route at 360, 768 and 1440 px in light and dark mode,
plus reduced-motion, keyboard (drawer + Escape, focus ring) and theme persistence.
Run with backend + frontend up:  python scripts/responsive_check.py [base_url]
Exit code 1 if anything fails.  Writes a few 360px screenshots to docs/screenshots/.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5304").rstrip("/")
ROUTES = ["/", "/app", "/app/verify", "/app/bulk", "/app/analytics", "/app/models", "/app/lab", "/nope"]
SIZES = [(360, 780), (768, 1024), (1440, 900)]
fails, problems = [], []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  ' + str(detail)) if detail and not ok else ''}")
    if not ok:
        fails.append(name)


def launch(p):
    for kw in ({"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def make_page(browser, w, h, theme, reduced=False):
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce" if reduced else "no-preference")
    if theme:  # None = leave storage alone (used to test persistence)
        ctx.add_init_script(f"try{{localStorage.setItem('securepay-theme','{theme}')}}catch(e){{}}")
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and problems.append(f"console error: {m.text} @ {page.url}"))
    page.on("pageerror", lambda e: problems.append(f"page error: {e} @ {page.url}"))
    page.on("response", lambda r: r.status >= 400 and problems.append(f"HTTP {r.status}: {r.url}"))
    return page


with sync_playwright() as p:
    browser = launch(p)

    for theme in ("light", "dark"):
        for w, h in SIZES:
            page = make_page(browser, w, h, theme)
            for route in ROUTES:
                page.goto(BASE + route, wait_until="networkidle")
                page.wait_for_timeout(500)
                over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                check(f"{theme} {w}px {route}: no horizontal scroll", over <= 1, f"overflow {over}px")
                has_theme = page.evaluate("document.documentElement.dataset.theme")
                if route == "/app":
                    check(f"{theme} {w}px: theme applied", has_theme == theme, has_theme)
            if w == 360 and theme == "light":
                for route, name in (("/app", "17_mobile-dashboard"), ("/app/verify", "18_mobile-verify"), ("/app/bulk", "19_mobile-bulk")):
                    page.goto(BASE + route, wait_until="networkidle")
                    page.wait_for_timeout(800)
                    page.screenshot(path=str(OUT / f"{name}.png"))
            page.context.close()

    # drawer + keyboard at phone width
    page = make_page(browser, 360, 780, "light")
    page.goto(BASE + "/app", wait_until="networkidle")
    page.get_by_role("button", name="Open navigation").click()
    page.wait_for_selector("[role=dialog]")
    check("mobile: nav drawer opens", page.locator("[role=dialog] nav").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)
    check("mobile: Escape closes drawer", page.locator("[role=dialog]").count() == 0)
    page.context.close()

    # keyboard: skip link + visible focus ring
    page = make_page(browser, 1440, 900, None)
    page.goto(BASE + "/app/verify", wait_until="networkidle")
    page.keyboard.press("Tab")
    check("keyboard: first Tab lands on skip link", page.evaluate("document.activeElement.className").startswith("skip-link"))
    for _ in range(6):
        page.keyboard.press("Tab")
    outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle + ' ' + getComputedStyle(document.activeElement).outlineWidth")
    check("keyboard: focused control shows an outline", outline.startswith("solid") and not outline.endswith(" 0px"), outline)
    unlabeled = page.evaluate("[...document.querySelectorAll('input,select,textarea')].filter(e => !e.labels.length && !e.getAttribute('aria-label')).length")
    check("verify: every input has a label", unlabeled == 0, unlabeled)

    # theme toggle persists across reload
    page.get_by_role("button", name="Switch to dark mode").click()
    page.reload(wait_until="networkidle")
    check("theme toggle persists after reload", page.evaluate("document.documentElement.dataset.theme") == "dark")
    page.context.close()

    # error state: modal escape on the lab confirm dialog
    page = make_page(browser, 1440, 900, "light")
    page.goto(BASE + "/app/lab", wait_until="networkidle")
    page.get_by_role("button", name="Generate new dataset").click()
    page.wait_for_selector("[role=dialog]")
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    check("lab: Escape closes the confirm dialog", page.locator("[role=dialog]").count() == 0)
    page.context.close()

    # reduced motion: still renders everything, no errors
    page = make_page(browser, 1440, 900, "light", reduced=True)
    for route in ROUTES[:-1]:
        page.goto(BASE + route, wait_until="networkidle")
        page.wait_for_timeout(400)
        check(f"reduced-motion {route}: renders", page.locator("h1").count() >= 1)
    page.context.close()
    browser.close()

# the 404 route is requested on purpose and is not an API failure
real = [x for x in dict.fromkeys(problems)]
check("console clean (no errors, rejections or failed requests)", not real, real[:5])
print(f"\n{'FAILED: ' + str(len(fails)) if fails else 'All checks passed'}")
sys.exit(1 if fails else 0)
