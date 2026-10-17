"""Walk every screen of the React frontend with real data and save 1440x900 screenshots.

Needs the backend (8305) and the frontend (5305) running, e.g. via run.bat:
    pip install playwright && playwright install chromium
    python scripts/capture_screens.py
Screenshots go to docs/screenshots/<nn>_<screen>.png. Console errors, page errors and failed
requests seen during the walk are printed at the end (exit code 1 if there are any).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"


def env_value(key: str, default: str) -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return default


BASE = f"http://127.0.0.1:{env_value('FRONTEND_PORT', '5305')}"
problems: list[str] = []


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:  # bundled chromium not installed: fall back to the installed Chrome
        return p.chromium.launch(channel="chrome")


def new_page(browser, theme):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script(f"try {{ localStorage.setItem('cg_theme', '{theme}') }} catch (e) {{}}")
    page = ctx.new_page()
    page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    page.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url} {r.failure}"))
    page.on("response", lambda r: problems.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 and "/api/crypto/decrypt" not in r.url else None)
    return page


def shot(page, name):
    OUT.mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


def main() -> int:
    with sync_playwright() as p:
        browser = launch(p)

        # landing page, both themes
        for theme, n in (("dark", "01_landing-dark"), ("light", "02_landing-light")):
            page = new_page(browser, theme)
            page.goto(BASE + "/", wait_until="networkidle")
            page.wait_for_timeout(2600)
            shot(page, n)
            page.context.close()

        page = new_page(browser, "dark")

        # live scoring: attack preset, normal preset, then the bundled sample batch
        page.goto(BASE + "/app", wait_until="networkidle")
        page.get_by_role("button", name="Simulate attack").click()
        page.get_by_text("Attack probability").first.wait_for()
        page.get_by_role("button", name="Simulate normal").click()
        page.wait_for_timeout(600)
        page.get_by_role("button", name="Simulate attack").click()
        page.wait_for_timeout(800)
        page.get_by_role("button", name="Use sample (120 flows)").click()
        page.get_by_text("Rows scored").wait_for()
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(5500)  # let the toasts expire so they do not cover the screenshot
        shot(page, "03_live-scoring")
        page.get_by_text("Per-row batch results").scroll_into_view_if_needed()
        page.get_by_role("heading", name="Batch CSV scoring").scroll_into_view_if_needed()
        shot(page, "04_batch-scoring")
        page.get_by_role("heading", name="Attack vs normal").scroll_into_view_if_needed()
        shot(page, "05_session-charts")

        # secure transfer: encrypt -> verify, then tamper
        page.goto(BASE + "/app/secure", wait_until="networkidle")
        page.get_by_role("button", name="Encrypt and transmit to cloud").click()
        page.get_by_role("button", name="Decrypt and verify at cloud").wait_for()
        page.get_by_role("button", name="Decrypt and verify at cloud").click()
        page.get_by_text("Decrypted and verified").wait_for()
        page.wait_for_timeout(5000)
        shot(page, "06_secure-transfer-verified")
        page.get_by_role("button", name="Tamper ciphertext").click()
        page.get_by_text("Decryption rejected").first.wait_for()
        page.wait_for_timeout(5000)
        shot(page, "07_secure-transfer-tampered")

        # alerts (populated by the batch above), performance
        page.goto(BASE + "/app/alerts", wait_until="networkidle")
        page.wait_for_timeout(1500)
        shot(page, "08_alerts")
        page.goto(BASE + "/app/performance", wait_until="networkidle")
        page.wait_for_timeout(1800)
        shot(page, "09_model-performance")
        browser.close()

    # 400s are the expected tag-failure; "GL Driver Message" is headless software-GL noise, not an app error
    ignore = ("Failed to load resource: the server responded with a status of 400", "GL Driver Message")
    real = [x for x in problems if not any(i in x for i in ignore)]
    print(f"\n{len(real)} problem(s) seen during the walk")
    for x in real:
        print(" -", x)
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
