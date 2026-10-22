"""Browser checks for the React frontend: responsive widths, light/dark, reduced motion, keyboard, error states.

Needs the backend and frontend running (run.bat). Usage: python scripts/ui_checks.py
Exit code 0 = every check passed.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ROUTES = ["/app", "/app/analyze", "/app/performance", "/app/insights"]
results: list[tuple[bool, str]] = []
problems: list[str] = []


def env_port(name: str, default: str) -> str:
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return default


BASE = f"http://127.0.0.1:{env_port('FRONTEND_PORT', '5410')}"


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((ok, name))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + str(detail)) if detail and not ok else ''}")


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(channel="chrome")


def make_page(browser, width, height, scheme="dark", reduced="no-preference"):
    ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, reduced_motion=reduced)
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and problems.append(f"console: {m.text}"))
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    return ctx, page


def sign_in(page):
    page.goto(BASE + "/login")
    page.get_by_text("click to fill").click()
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_url("**/app")


def overflow(page) -> int:
    return page.evaluate("document.documentElement.scrollWidth - window.innerWidth")


def main() -> int:
    with sync_playwright() as p:
        browser = launch(p)

        # ---- responsive + theme matrix
        for scheme in ("dark", "light"):
            for w, h in ((360, 740), (768, 1024), (1440, 900)):
                ctx, page = make_page(browser, w, h, scheme)
                page.goto(BASE + "/")
                page.wait_for_selector("text=curl /api/health")
                page.wait_for_timeout(600)
                check(f"landing {w}px {scheme}: no horizontal overflow", overflow(page) <= 0, overflow(page))
                sign_in(page)
                for r in ROUTES:
                    page.goto(BASE + r)
                    page.wait_for_selector("main h1")
                    page.wait_for_timeout(1400)
                    check(f"{r} {w}px {scheme}: no horizontal overflow", overflow(page) <= 0, overflow(page))
                if w == 360:
                    check("360px: sidebar is hidden", not page.locator("aside").is_visible())
                    page.get_by_role("button", name="Open navigation").click()
                    page.wait_for_selector("role=dialog")
                    check("360px: menu opens a drawer", page.get_by_role("link", name="Model performance").is_visible())
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(800)
                    check("Escape closes the drawer", page.locator("role=dialog").count() == 0)
                ctx.close()

        # ---- theme toggle persists
        ctx, page = make_page(browser, 1440, 900, "dark")
        sign_in(page)
        page.get_by_role("button", name="Switch to light mode").click()
        page.reload()
        page.wait_for_selector("main h1")
        check("light theme persists after reload", page.evaluate("document.documentElement.dataset.theme") == "light")
        ctx.close()

        # ---- reduced motion: static grid fallback, headline shown at once
        ctx, page = make_page(browser, 1440, 900, "dark", reduced="reduce")
        page.goto(BASE + "/")
        page.wait_for_selector("text=curl /api/health")
        check("reduced motion: headline is complete immediately",
              page.get_by_role("heading", level=1).first.inner_text().strip().startswith("Will this startup succeed?"))
        check("reduced motion: no WebGL canvas, CSS grid fallback used",
              page.locator("canvas").count() == 0 and page.locator(".grid-bg").count() > 0)
        ctx.close()

        # ---- keyboard
        ctx, page = make_page(browser, 1440, 900)
        sign_in(page)
        page.wait_for_selector("main h1")
        page.keyboard.press("/")
        page.wait_for_selector("role=dialog")
        check("'/' opens the command palette", page.get_by_role("combobox").is_visible())
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)  # exit animation
        check("Escape closes the palette", page.locator("role=dialog").count() == 0)
        page.keyboard.press("g")
        page.keyboard.press("a")
        page.wait_for_url("**/app/analyze")
        check("'g a' navigates to Analyze", True)
        page.keyboard.press("Tab")
        outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
        check("focus ring visible on first Tab stop", outline != "none", outline)
        unlabeled = page.evaluate("""[...document.querySelectorAll('main input, main select, main textarea')]
            .filter(e => !e.labels?.length && !e.getAttribute('aria-label')).length""")
        check("every form control has a label", unlabeled == 0, unlabeled)
        ctx.close()

        # ---- error + validation states
        ctx, page = make_page(browser, 1440, 900)
        page.goto(BASE + "/login")
        page.get_by_label("Email").fill("demo@venturepulse.com")
        page.get_by_label("Password").fill("not-the-password")
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.wait_for_selector("text=Sign-in failed")
        check("wrong password shows what failed and what to do", page.get_by_text("Incorrect email or password.").is_visible())
        page.get_by_text("click to fill").click()
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.wait_for_url("**/app")

        page.goto(BASE + "/app/analyze")
        page.wait_for_selector("text=Funding & traction")
        page.get_by_role("button", name="Predict startup success").click()
        page.wait_for_selector("text=Some values need attention.")
        check("empty description is rejected with a message", page.get_by_text("Describe the startup in a few sentences").is_visible())
        page.get_by_label("Total funding (USD)").fill("-5")
        page.get_by_role("button", name="Predict startup success").click()
        check("out-of-range number is rejected", page.get_by_text("Between 0 and").first.is_visible())

        page.get_by_role("button", name="Fill an example").click()
        page.route("**/predict", lambda r: r.abort())
        page.get_by_role("button", name="Predict startup success").click()
        page.wait_for_selector("text=Prediction failed")
        check("API down on predict: error state with hint", page.get_by_text("Cannot reach the VenturePulse API").is_visible())
        page.unroute("**/predict")
        page.get_by_role("button", name="Predict startup success").click()
        page.wait_for_selector("text=estimated outcome", timeout=90000)
        check("prediction succeeds after retry (success feedback)", page.get_by_text("Estimated outcome:", exact=False).count() > 0)

        page.route("**/api/model-metrics", lambda r: r.abort())
        page.goto(BASE + "/app/performance")
        page.wait_for_selector("text=Could not load the model metrics")
        check("Performance error state offers Retry", page.get_by_role("button", name="Retry").is_visible())
        page.unroute("**/api/model-metrics")
        page.get_by_role("button", name="Retry").click()
        page.wait_for_selector("text=Confusion matrix")
        check("Retry recovers the screen", True)

        # session guard
        ctx2, page2 = make_page(browser, 1440, 900)
        page2.goto(BASE + "/app/insights")
        page2.wait_for_url("**/login")
        check("signed-out visitor is redirected to /login", True)
        ctx2.close()
        ctx.close()
        browser.close()

    # the deliberately failed requests above show up as console errors; anything else is a real problem
    expected = ("ERR_FAILED", "ERR_INTERNET_DISCONNECTED", "401 (Unauthorized)", "Failed to load resource")
    real = [x for x in dict.fromkeys(problems) if not any(e in x for e in expected)]
    check("no unexpected console errors", not real, "; ".join(real)[:400])
    failed = [n for ok, n in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
