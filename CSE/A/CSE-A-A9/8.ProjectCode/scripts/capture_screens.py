"""Walk every screen of the running app, save 1440x900 screenshots and report console problems.

    python scripts/capture_screens.py            # app must be running (run.bat)
    python scripts/capture_screens.py --check    # no screenshots, only the console / network check

Moderator decisions made to put real data on the Queue screens are undone again at the end,
so the demo database is left as it was found.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
APP = "http://localhost:5309"
API = "http://127.0.0.1:8309"
MOD = ("moderator@botgraph.app", "Demo@1234")


def api(method: str, path: str, token: str | None = None, body: dict | None = None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not args.check:
        OUT.mkdir(parents=True, exist_ok=True)

    token = api("POST", "/api/auth/login", body={"email": MOD[0], "password": MOD[1]})["token"]
    top = api("GET", "/api/accounts?page_size=6", token)["items"]
    clusters = api("GET", "/api/clusters", token)["items"]
    coordinated = [c for c in clusters if c["kind"] == "coordinated"]
    made: list[int] = []
    existing = api("GET", "/api/decisions", token)["items"]
    if not existing:  # real data on the queue screens
        for a, d in zip(top[:4], ["confirm", "confirm", "dismiss", "confirm"]):
            made.append(api("POST", "/api/queue/decisions", token, {"target_type": "account", "target_id": str(a["id"]), "decision": d, "note": "Posts the same links on a fixed schedule." if d == "confirm" else "Looks like a real, very active user."})["id"])
        made.append(api("POST", "/api/queue/decisions", token, {"target_type": "cluster", "target_id": coordinated[-1]["id"], "decision": "confirm", "note": "Created within days of each other, same peak hour."})["id"])

    problems: list[str] = []
    shots: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        def new_page(dark: bool = False, width: int = 1440, height: int = 900, login: bool = True):
            ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme="dark" if dark else "light")
            ctx.add_init_script(f"try{{localStorage.setItem('botgraph-theme','{'dark' if dark else 'light'}')}}catch(e){{}}")
            page = ctx.new_page()
            where = {"now": "boot"}
            page.on("console", lambda m: m.type in ("error", "warning") and problems.append(f"[{where['now']}] console {m.type}: {m.text[:200]}"))
            page.on("pageerror", lambda e: problems.append(f"[{where['now']}] pageerror: {str(e)[:200]}"))
            page.on("requestfailed", lambda r: problems.append(f"[{where['now']}] request failed: {r.url}"))
            page.on("response", lambda r: r.status >= 400 and problems.append(f"[{where['now']}] HTTP {r.status}: {r.url}"))
            page.where = where
            if login:
                page.goto(f"{APP}/login")
                page.get_by_role("button", name="One-click demo sign in (moderator)").click()
                page.wait_for_url(f"{APP}/app")
            return page

        def snap(page, name: str, wait: float = 1.2):
            page.where["now"] = name
            time.sleep(wait)
            if not args.check:
                path = OUT / f"{name}.png"
                page.screenshot(path=str(path))
                shots.append(path.name)

        def go(page, path: str, name: str, wait: float = 1.4):
            page.where["now"] = name
            page.goto(f"{APP}{path}")
            page.wait_for_load_state("networkidle")
            snap(page, name, wait)

        # landing, both themes (scroll through it once so the reveal animations have run)
        for dark in (False, True):
            page = new_page(dark=dark, login=False)
            page.where["now"] = f"landing-{'dark' if dark else 'light'}"
            page.goto(f"{APP}/")
            page.wait_for_load_state("networkidle")
            for y in range(0, 3200, 400):
                page.mouse.wheel(0, 400)
                time.sleep(0.15)
            page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
            time.sleep(0.6)
            page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
            snap(page, f"{'02' if dark else '01'}_landing_{'dark' if dark else 'light'}", 1.5)
            page.context.close()

        page = new_page(login=False)
        go(page, "/login", "03_login")
        page.context.close()

        page = new_page()
        go(page, "/app", "04_overview", 2.0)
        go(page, "/app/graph", "05_graph_and_features", 1.8)
        go(page, "/app/accounts", "06_accounts")
        go(page, f"/app/accounts/{top[0]['id']}", "07_account_detail", 3.5)
        page.mouse.wheel(0, 760)
        snap(page, "07b_account_reasons_and_neighbourhood", 2.5)
        go(page, "/app/clusters", "08_clusters")
        go(page, f"/app/clusters/{coordinated[0]['id']}", "09_cluster_detail", 3.5)
        page.mouse.wheel(0, 420)
        snap(page, "09b_cluster_graph_and_members", 2.0)
        go(page, "/app/queue", "10_queue_accounts")
        page.get_by_role("tab", name="Botnet clusters").click()
        snap(page, "11_queue_clusters")
        page.get_by_role("tab", name="Decision log").click()
        snap(page, "12_decision_log")
        go(page, "/app/models", "13_models_comparison", 2.2)
        page.get_by_role("tab", name="Scalability").click()
        snap(page, "14_models_scalability", 2.0)
        page.get_by_role("tab", name="Retraining").click()
        snap(page, "15_models_retraining")
        page.context.close()

        # one dark-mode app screen
        page = new_page(dark=True)
        go(page, "/app", "16_overview_dark", 2.0)
        page.context.close()
        browser.close()

    for rid in made:
        api("DELETE", f"/api/queue/decisions/{rid}", token)

    if shots:
        print(f"saved {len(shots)} screenshots to {OUT}")
    if problems:
        print(f"{len(problems)} console / network problem(s):")
        for line in sorted(set(problems)):
            print("  ", line)
        return 1
    print("console clean: no errors, warnings, failed requests or 4xx/5xx responses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
