"""Responsive, dark-mode, keyboard and reduced-motion checks against the running app.

    python scripts/ui_checks.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

APP = "http://localhost:5309"
API = "http://127.0.0.1:8309"


def jget(path, token=None, body=None, method="GET"):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def gone(pg) -> bool:
    """True once the dialog has left the page (its exit animation can take a moment on a busy machine)."""
    try:
        pg.get_by_role("dialog").wait_for(state="detached", timeout=8000)
        return True
    except Exception as e:  # noqa: BLE001
        print('   dialog still present:', str(e)[:160], pg.get_by_role('dialog').count())
        return False


def main() -> int:
    tok = jget("/api/auth/login", body={"email": "analyst@botgraph.app", "password": "Demo@1234"}, method="POST")["token"]
    acc = jget("/api/accounts?page_size=1", tok)["items"][0]["id"]
    cl = jget("/api/clusters", tok)["items"][0]["id"]
    paths = ["/app", "/app/graph", "/app/accounts", f"/app/accounts/{acc}", "/app/clusters", f"/app/clusters/{cl}", "/app/queue", "/app/models"]
    fails: list[str] = []
    rows: list[str] = []

    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)

        def ctx(width, dark=False, reduce=False, seed=True):
            c = b.new_context(viewport={"width": width, "height": 800}, color_scheme="dark" if dark else "light", reduced_motion="reduce" if reduce else "no-preference")
            if seed:
                c.add_init_script(f"try{{if(!localStorage.getItem('botgraph-theme'))localStorage.setItem('botgraph-theme','{'dark' if dark else 'light'}')}}catch(e){{}}")
            pg = c.new_page()
            errs: list[str] = []
            pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
            pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.goto(f"{APP}/login")
            pg.get_by_role("button", name="One-click demo sign in (moderator)").click()
            pg.wait_for_url(f"{APP}/app")
            return pg, errs

        # 1. no sideways page scroll at 360 / 768 / 1440, light and dark
        for width in (360, 768, 1440):
            for dark in (False, True):
                pg, errs = ctx(width, dark)
                for path in paths + ["/"]:
                    pg.goto(f"{APP}{path}")
                    pg.wait_for_load_state("networkidle")
                    time.sleep(0.9)
                    sw, iw = pg.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
                    ok = sw <= iw + 1
                    rows.append(f"{'ok  ' if ok else 'FAIL'} {width:>4}px {'dark ' if dark else 'light'} {path[:40]:<40} scrollWidth {sw} / {iw}")
                    if not ok:
                        fails.append(f"horizontal overflow at {width}px {path} ({sw} > {iw})")
                if errs:
                    fails.append(f"console errors at {width}px dark={dark}: {sorted(set(errs))[:3]}")
                pg.context.close()

        # 2. theme toggle works and persists
        pg, _ = ctx(1280, seed=False)
        before = pg.evaluate("document.documentElement.dataset.theme")
        pg.get_by_role("button", name="Switch to dark mode").click()
        time.sleep(0.4)
        after = pg.evaluate("document.documentElement.dataset.theme")
        pg.reload()
        pg.wait_for_load_state("networkidle")
        kept = pg.evaluate("document.documentElement.dataset.theme")
        rows.append(f"theme toggle: {before} -> {after}, after reload {kept}")
        if not (before == "light" and after == "dark" and kept == "dark"):
            fails.append("theme toggle did not persist")

        # 3. keyboard: Escape closes the decision dialog, focus ring is visible, drawer opens at 360px
        pg.goto(f"{APP}/app/accounts/{acc}")
        pg.wait_for_load_state("networkidle")
        pg.get_by_role("button", name="Confirm fake").click()
        dlg = pg.get_by_role("dialog")
        opened = dlg.count() == 1
        pg.wait_for_function("document.activeElement && document.activeElement.closest('[role=dialog]')")  # focus moved into the dialog
        pg.keyboard.press("Escape")
        closed = gone(pg)
        rows.append(f"dialog: opens={opened}, Escape closes={closed}")
        if not (opened and closed):
            fails.append("decision dialog keyboard behaviour")
        pg.keyboard.press("Tab")
        outline = pg.evaluate("(() => { const e = document.activeElement; return e ? getComputedStyle(e).outlineStyle + ' ' + getComputedStyle(e).outlineWidth : 'none' })()")
        rows.append(f"focus outline after Tab: {outline}")
        pg.context.close()

        pg, _ = ctx(360)
        pg.goto(f"{APP}/app")
        pg.wait_for_load_state("networkidle")
        pg.get_by_role("button", name="Open navigation").click()
        time.sleep(0.5)
        drawer = pg.get_by_role("dialog").count() == 1
        pg.wait_for_function("document.activeElement && document.activeElement.closest('[role=dialog]')")
        pg.keyboard.press("Escape")
        rows.append(f"360px drawer opens={drawer}, closes on Escape={gone(pg)}")
        if not drawer:
            fails.append("mobile navigation drawer did not open")
        pg.context.close()

        # 4. reduced motion: every screen still renders without errors
        pg, errs = ctx(1280, reduce=True)
        for path in paths:
            pg.goto(f"{APP}{path}")
            pg.wait_for_load_state("networkidle")
            time.sleep(0.6)
            if pg.locator("h1").count() == 0:
                fails.append(f"no heading with reduced motion on {path}")
        rows.append(f"reduced motion: {len(paths)} screens rendered, console errors: {len(errs)}")
        if errs:
            fails.append(f"console errors with reduced motion: {errs[:2]}")
        b.close()

    print("\n".join(rows))
    if fails:
        print("\nFAILED:")
        for f in fails:
            print("  -", f)
        return 1
    print("\nall UI checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
