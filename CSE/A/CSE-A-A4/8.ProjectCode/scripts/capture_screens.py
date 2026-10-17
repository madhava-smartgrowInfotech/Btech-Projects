"""
Walk every SecurePay AI screen in a real browser, put real data on it and save 1440x900 PNGs to
docs/screenshots/<nn>_<screen>.png. Also fails on console errors, unhandled rejections and 4xx/5xx.

Run with backend + frontend up:   python scripts/capture_screens.py [base_url]
Needs:  pip install playwright   then either `playwright install chromium` or an installed Chrome
(the script tries Chrome first, then bundled Chromium). Does not retrain or regenerate anything.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5304").rstrip("/")
problems = []


def launch(p):
    for kw in ({"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def new_page(browser, theme, width=1440, height=900):
    ctx = browser.new_context(viewport={"width": width, "height": height})
    ctx.add_init_script(f"try{{localStorage.setItem('securepay-theme','{theme}')}}catch(e){{}}")
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and problems.append(f"console error: {m.text} @ {page.url}"))
    page.on("pageerror", lambda e: problems.append(f"page error: {e} @ {page.url}"))
    page.on("response", lambda r: r.status >= 400 and "/api/predict_batch" not in r.url and problems.append(f"HTTP {r.status}: {r.url}"))
    page.on("requestfailed", lambda r: problems.append(f"request failed: {r.url}"))
    return page


def shot(page, name, full=False):
    if full:  # scroll through so whileInView / ScrollTrigger reveals fire before the capture
        h = page.evaluate("document.documentElement.scrollHeight")
        for y in range(0, h, 500):
            page.evaluate(f"window.scrollTo(0,{y})")
            page.wait_for_timeout(120)
        page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(900)  # let spring / chart animations settle
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=full)
    print("saved", path.relative_to(ROOT))


def goto(page, path):
    page.goto(BASE + path, wait_until="networkidle")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = launch(p)

        # landing, both themes
        for n, theme in (("01_landing-light", "light"), ("02_landing-dark", "dark")):
            page = new_page(browser, theme)
            goto(page, "/")
            page.wait_for_selector(".hero-card canvas, .hero-card svg.recharts-surface")
            shot(page, n, full=True)
            page.context.close()

        page = new_page(browser, "light")

        goto(page, "/app")
        page.wait_for_selector(".stat-card")
        shot(page, "03_dashboard")

        goto(page, "/app/verify")
        page.get_by_role("button", name="Run fraud check").click()
        page.wait_for_selector(".verdict")
        shot(page, "04_verify")

        goto(page, "/app/bulk")
        page.get_by_role("button", name="Try the sample file").first.click()
        page.wait_for_selector("table.tbl")
        shot(page, "05_bulk")

        goto(page, "/app/analytics")
        page.wait_for_selector(".recharts-surface")
        shot(page, "06_analytics-where")
        for i, tab in enumerate(("When", "How much", "Card signals"), start=7):
            page.get_by_role("tab", name=tab).click()
            page.wait_for_selector(".recharts-surface")
            shot(page, f"{i:02d}_analytics-{tab.lower().replace(' ', '-')}")

        goto(page, "/app/models")
        page.wait_for_selector("table.tbl")
        shot(page, "10_models-comparison")
        page.get_by_role("tab", name="Training curves").click()
        page.wait_for_selector(".recharts-line")
        shot(page, "11_models-curves")
        page.get_by_role("tab", name="Features").click()
        page.wait_for_selector(".recharts-bar")
        shot(page, "12_models-features")
        page.get_by_role("tab", name="QUBO matrix").click()
        page.wait_for_selector("svg.heat")
        shot(page, "13_models-qubo")

        goto(page, "/app/lab")
        page.wait_for_selector(".stepper")
        shot(page, "14_lab", full=True)
        page.context.close()

        # dark app screens
        page = new_page(browser, "dark")
        goto(page, "/app")
        page.wait_for_selector(".stat-card")
        shot(page, "15_dashboard-dark")
        goto(page, "/app/verify")
        page.get_by_role("button", name="Run fraud check").click()
        page.wait_for_selector(".verdict")
        shot(page, "16_verify-dark")
        page.context.close()
        browser.close()

    if problems:
        print("\nPROBLEMS:")
        for x in dict.fromkeys(problems):
            print(" -", x)
        sys.exit(1)
    print("\nAll screens captured, console clean.")


if __name__ == "__main__":
    main()
