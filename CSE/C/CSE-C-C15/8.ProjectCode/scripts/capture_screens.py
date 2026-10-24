"""Capture a 1440x900 screenshot of every SentinelFlow screen with real data on it.

Usage (backend on 8415 and UI on 5415 already running, e.g. via run.bat):
    python scripts/capture_screens.py

What it does:
  1. landing page in light and dark mode (WebGL backdrop),
  2. the login page, then a real sign-in with the demo account,
  3. starts a simulation through the API (real model, synthetic traffic) and waits until windows are scored and
     quarantines exist, so no dashboard is empty,
  4. visits every console screen and saves docs/screenshots/<nn>_<name>.png,
  5. stops the simulation.
Each screen uses its own short-lived browser (the simulation runs server-side), which keeps the run robust on
machines where a long-lived headless Chromium gets killed. It reports any browser console error, page error,
failed request or HTTP >= 400 and exits 1 if there were any.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
BASE = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5415")
EMAIL, PASSWORD = "demo@sentinelflow.com", "Demo@1234"
SESSION_JS = "try{localStorage.setItem('sf_session',JSON.stringify({email:'%s',name:'Demo Analyst'}))}catch(e){}" % EMAIL

problems = []


def api(path, body=None):
    req = urllib.request.Request(BASE + "/api" + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def watch(page, label):
    page.on("console", lambda m: problems.append("[%s] console.%s: %s" % (label, m.type, m.text)) if m.type == "error" else None)
    page.on("pageerror", lambda e: problems.append("[%s] pageerror: %s" % (label, e)))
    page.on("crash", lambda: problems.append("[%s] page crashed" % label))
    # ERR_ABORTED is just an in-flight poll cancelled by our own navigation.
    page.on("requestfailed", lambda r: problems.append("[%s] request failed: %s %s" % (label, r.url, r.failure))
            if "ERR_ABORTED" not in str(r.failure) else None)
    page.on("response", lambda r: problems.append("[%s] HTTP %s %s" % (label, r.status, r.url)) if r.status >= 400 else None)


def scroll_through(page):
    """Wheel-scroll the page once so scroll-triggered reveals have fired, then return to the top."""
    height = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < height:
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(120)
        y += 500
    page.wait_for_timeout(600)
    page.mouse.wheel(0, -height)
    page.wait_for_timeout(900)


def session(p, scheme="dark", logged_in=True, label="console"):
    """Fresh browser per block: `with session(p) as page:`."""
    class _S:
        def __enter__(self):
            try:
                self.b = p.chromium.launch()
            except Exception:
                self.b = p.chromium.launch(channel="chrome")
            self.ctx = self.b.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
            page = self.ctx.new_page()
            watch(page, label)
            init = "try{localStorage.setItem('sf_theme','%s')}catch(e){}" % scheme
            page.add_init_script(init + (SESSION_JS if logged_in else ""))
            return page

        def __exit__(self, *exc):
            try:
                self.b.close()
            except Exception:
                pass
    return _S()


def retry(fn, tries=5):
    for i in range(tries):
        try:
            return fn()
        except Exception as exc:  # browser killed mid-run: start a fresh one
            print("  retry %d/%d after: %s" % (i + 1, tries, str(exc).splitlines()[0][:90]))
            if i == tries - 1:
                raise


def shot(page, n, name):
    path = OUT / ("%02d_%s.png" % (n, name))
    page.screenshot(path=str(path))
    print("saved", path.relative_to(ROOT))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        api("/status")
    except Exception as exc:
        print("Cannot reach %s/api/status (%s). Start the servers with run.bat first." % (BASE, exc))
        return 2

    with sync_playwright() as p:
        # 1. landing page, light and dark
        for n, scheme in ((1, "light"), (2, "dark")):
            def landing(n=n, scheme=scheme):
                with session(p, scheme, logged_in=False, label="landing-" + scheme) as page:
                    page.goto(BASE + "/", wait_until="networkidle")
                    page.wait_for_timeout(2800)
                    scroll_through(page)
                    shot(page, n, "landing_" + scheme)
            retry(landing)

        # 2. login page + real sign-in with the demo account
        def login():
            with session(p, "dark", logged_in=False, label="login") as page:
                page.goto(BASE + "/login", wait_until="networkidle")
                page.wait_for_timeout(800)
                shot(page, 3, "login")
                page.get_by_label("Email").fill(EMAIL)
                page.get_by_label("Password").fill(PASSWORD)
                page.get_by_role("button", name="Sign in").click()
                page.wait_for_url("**/app")
                print("signed in as", EMAIL)
        retry(login)

        # 3. real data: a simulation scored by the real model
        for kind in ("demo", "monitor"):
            try:
                api("/%s/stop" % kind, {})
            except Exception:
                pass
        time.sleep(1)
        before = sum(api("/detections?limit=1")["by_prediction"].values())
        api("/demo/start", {"window_seconds": 2})
        print("simulation running; collecting windows ...")
        deadline = time.time() + 150
        while time.time() < deadline:
            scored = sum(api("/detections?limit=1")["by_prediction"].values()) - before
            if scored >= 12 and api("/mitigations")["active"]:
                break
            time.sleep(2)
        time.sleep(2)

        # 4. every console screen
        def visit(n, name, path, wait=2600, action=None):
            def go():
                with session(p, "dark") as page:
                    page.goto(BASE + path, wait_until="networkidle")
                    page.wait_for_timeout(wait)
                    if action:
                        action(page)
                    shot(page, n, name)
            retry(go)

        visit(4, "overview", "/app", wait=3200)
        visit(5, "detections", "/app/detections")
        first_id = api("/detections?limit=1")["detections"][0]["id"]
        visit(6, "threat_detail", "/app/detections?id=%s" % first_id, wait=3000)
        visit(7, "analytics", "/app/analytics", wait=3000)
        visit(8, "network_health", "/app/health", wait=3000)
        visit(9, "mitigation", "/app/mitigation", wait=3000)
        visit(10, "model", "/app/model", wait=3000)
        visit(11, "settings", "/app/settings")

        def palette(page):
            page.keyboard.press("/")
            page.keyboard.type("attack")
            page.wait_for_timeout(600)
        visit(12, "command_palette", "/app", wait=2000, action=palette)

        # 5. leave the backend idle
        api("/demo/stop", {})

    if problems:
        print("\nPROBLEMS (%d):" % len(problems))
        for line in problems:
            print(" ", line)
        return 1
    print("\nconsole clean: no errors, no failed requests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
