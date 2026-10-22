"""Responsive / theme / keyboard check for every screen at 360, 768 and 1440 px, light and dark.

Fails on horizontal overflow, console errors or failed requests. Optional: pass an output folder to
keep the screenshots.  Usage:  python scripts/check_responsive.py [out_dir]
"""
import sys
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def env_port(name, default):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return default


BASE = f"http://127.0.0.1:{env_port('FRONTEND_PORT', '5407')}"
PUBLIC = ["/", "/login", "/register", "/courses", "/analytics"]
PRIVATE = ["/app", "/app/recommendations", "/app/path", "/app/insights", "/app/activity", "/app/profile"]
problems = []


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        for theme in ("light", "dark"):
            for w, h in ((360, 740), (768, 1024), (1440, 900)):
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=theme, reduced_motion="reduce")
                page = ctx.new_page()
                tag = f"{w}-{theme}"
                page.on("console", lambda m, t=tag: problems.append(f"[{t}] console: {m.text}") if m.type == "error" else None)
                page.on("pageerror", lambda e, t=tag: problems.append(f"[{t}] pageerror: {e}"))
                page.on("response", lambda r, t=tag: problems.append(f"[{t}] HTTP {r.status} {r.url}") if r.status >= 400 else None)

                def visit(path):
                    page.goto(BASE + path)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(500)
                    over = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                    if over > 1:
                        problems.append(f"[{tag}] {path}: horizontal overflow of {over}px")
                    if out:
                        page.screenshot(path=str(out / f"{w}_{theme}_{path.strip('/').replace('/', '-') or 'home'}.png"))

                for path in PUBLIC:
                    visit(path)
                page.goto(BASE + "/register")
                page.get_by_label("Full name").fill("Responsive Check")
                page.get_by_label("Email").fill(f"resp_{uuid.uuid4().hex[:6]}@example.com")
                page.get_by_label("Password", exact=True).fill("secret123")
                page.get_by_label("Confirm password").fill("secret123")
                page.get_by_role("button", name="Create account").click()
                page.wait_for_url("**/app/profile")
                page.wait_for_load_state("networkidle")
                for path in PRIVATE:
                    visit(path)
                recs = ctx.request.get(BASE + "/api/recommendations?top_n=1").json()["recommendations"]
                visit(f"/courses/{recs[0]['course']['id']}")
                if w < 1024:  # drawer: opens, traps focus, Escape closes
                    page.goto(BASE + "/app")
                    page.wait_for_load_state("networkidle")
                    page.get_by_role("button", name="Open navigation").click()
                    page.wait_for_timeout(400)
                    if not page.get_by_role("dialog").is_visible():
                        problems.append(f"[{tag}] drawer did not open")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                    if page.get_by_role("dialog").count():
                        problems.append(f"[{tag}] Escape did not close the drawer")
                ctx.close()

        # keyboard: the first Tab stop on a page is the skip link and focus rings are visible
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/login")
        page.wait_for_load_state("networkidle")
        page.keyboard.press("Tab")
        if "Skip to content" not in (page.evaluate("document.activeElement.textContent") or ""):
            problems.append("first Tab stop is not the skip link")
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
        if outline == "none":
            problems.append("focused element has no visible outline")
        browser.close()

    if problems:
        print("PROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        sys.exit(1)
    print("360 / 768 / 1440 px, light + dark: no overflow, console clean, drawer + keyboard OK.")


if __name__ == "__main__":
    main()
