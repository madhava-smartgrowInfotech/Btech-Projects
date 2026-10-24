"""Walk every AgriVision screen with real data and save 1440x900 PNGs to docs/screenshots/.

Needs both servers running (run.bat) and Playwright:  pip install playwright && playwright install chromium
Usage:  python scripts/capture_screens.py            (uses ports from .env, or AGRIVISION_URL)

It signs in as the demo farmer, uploads real PlantDoc test leaves from datasets/plantdoc-images/test so the
dashboard, history and analytics are not empty, then screenshots each screen. The landing page is captured in
light and dark mode. Console errors and failed requests seen during the walk are printed at the end.

Each screen runs in its own short-lived browser and is retried, because a long headless session can be killed
by the OS on a busy PC. Signing in is done once through the API and the token is placed in localStorage; the
real login form is still exercised for the dashboard screen.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def env_port(name: str, default: str) -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return default


BASE = os.environ.get("AGRIVISION_URL", f"http://localhost:{env_port('FRONTEND_PORT', '5416')}")
DEMO = ("demo@agrivision.ai", "demo1234")
TEST_DIR = ROOT / "datasets" / "plantdoc-images" / "test"
# Headless Chrome paints blurred glass in software; frozen animations keep screenshots quick and stable.
RM = "no-preference" if os.environ.get("AGRIVISION_MOTION") else "reduce"
# Software GL that works in headless Chrome on machines without a usable GPU process.
CHROME_ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
TIMEOUT = 90_000

# (folder in the PlantDoc test set, crop to choose on the detect screen)
SAMPLES = [
    ("Tomato_leaf_late_blight", "tomato"),
    ("Potato_leaf_early_blight", "potato"),
    ("Corn_rust_leaf", "corn"),
    ("grape_leaf_black_rot", "grape"),
    ("Apple_Scab_Leaf", "apple"),
    ("Tomato_leaf", "tomato"),
]

problems: list[str] = []


def first_image(folder: str) -> Path | None:
    d = TEST_DIR / folder
    if not d.is_dir():
        return None
    imgs = sorted(p for p in d.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp") and p.stat().st_size < 9_000_000)
    return imgs[0] if imgs else None


def api_token() -> str:
    req = urllib.request.Request(
        BASE + "/api/v1/auth/login",
        data=json.dumps({"email": DEMO[0], "password": DEMO[1]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["token"]


def watch(page, label: str) -> None:
    page.on("console", lambda m: problems.append(f"[{label}] console {m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: problems.append(f"[{label}] pageerror: {e}"))
    page.on("response", lambda r: problems.append(f"[{label}] HTTP {r.status} {r.url}") if r.status >= 400 else None)


def shot(page, name: str) -> None:
    page.wait_for_timeout(900)  # let entrance animations settle
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), timeout=TIMEOUT)
    print("saved", path.relative_to(ROOT), flush=True)


def scenario(label: str, fn, scheme: str = "dark", token: str | None = None, retries: int = 3) -> None:
    """Run fn(page) in a fresh browser; retry if the browser dies. Problems are only kept from the successful try."""
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        mark = len(problems)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="chrome", headless=True, args=CHROME_ARGS)
                ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme, reduced_motion=RM)
                ctx.set_default_timeout(TIMEOUT)
                if token:
                    ctx.add_init_script(f"try{{localStorage.setItem('agrivision-token','{token}')}}catch(e){{}}")
                page = ctx.new_page()
                watch(page, label)
                fn(page)
                browser.close()
            return
        except Exception as e:  # noqa: BLE001
            last = e
            del problems[mark:]
            print(f"  retry {attempt}/{retries} for {label}: {str(e)[:120]}", flush=True)
    raise RuntimeError(f"{label} failed after {retries} tries: {last}")


def scroll_through(page) -> None:
    height = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < height:
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(120)
        y += 700
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


# ------------------------------------------------------------------ scenarios
def landing(scheme: str):
    def run(page):
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.wait_for_selector("text=From the disease guide")
        page.wait_for_selector("text=Classes recognised")
        shot(page, f"01_landing_{scheme}")
        if scheme == "dark":
            scroll_through(page)
            page.evaluate("document.querySelector('#how-it-works')?.scrollIntoView()")
            shot(page, "02_landing_how_it_works")

    return run


def public_page(path: str, ready: str, name: str):
    def run(page):
        page.goto(BASE + path, wait_until="domcontentloaded")
        page.wait_for_selector(ready)
        shot(page, name)

    return run


def detect_one(folder: str, crop: str, name: str | None):
    img = first_image(folder)

    def run(page):
        page.goto(f"{BASE}/detect?crop={crop}", wait_until="domcontentloaded")
        page.set_input_files("input[aria-label='Leaf image file']", str(img))
        page.wait_for_selector("img[alt='Preview of the chosen leaf']")
        if name:
            shot(page, "07_detect_ready")
        page.get_by_role("button", name="Diagnose now").click()
        page.wait_for_url("**/result/*", timeout=TIMEOUT)
        page.wait_for_selector("text=Top-3 predictions")
        if name:
            shot(page, name)

    return run, img


def login_flow(page):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.wait_for_selector("text=Demo account")
    shot(page, "06_login")
    page.get_by_label("Email").fill(DEMO[0])
    page.get_by_label("Password", exact=True).fill(DEMO[1])
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_url("**/dashboard")
    page.wait_for_selector("text=Recent detections")
    page.wait_for_selector("img[alt^='Leaf scanned']")
    shot(page, "09_dashboard")


def authed(path: str, ready: str, name: str, scroll: int = 0):
    def run(page):
        page.goto(BASE + path, wait_until="domcontentloaded")
        page.wait_for_selector(ready)
        if scroll:
            page.mouse.wheel(0, scroll)
        shot(page, name)

    return run


def light_dashboard(page):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.get_by_label("Email").fill(DEMO[0])
    page.get_by_label("Password", exact=True).fill(DEMO[1])
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_url("**/dashboard")
    page.wait_for_selector("img[alt^='Leaf scanned']")
    shot(page, "14_dashboard_light")


def history_ids(token: str) -> set[str]:
    req = urllib.request.Request(BASE + "/api/v1/history?limit=100", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return {x["result_id"] for x in json.loads(r.read())["results"]}


def forget(token: str, ids: set[str]) -> None:
    for rid in ids:
        req = urllib.request.Request(BASE + f"/api/v1/history/{rid}", method="DELETE", headers={"Authorization": f"Bearer {token}"})
        try:
            urllib.request.urlopen(req, timeout=30).read()
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    token0 = api_token()
    before = history_ids(token0)
    try:
        return walk()
    finally:
        # keep the demo account as it was: remove the scans this walk created (set KEEP_SEEDED=1 to leave them)
        if not os.environ.get("KEEP_SEEDED"):
            forget(token0, history_ids(token0) - before)


def walk() -> int:
    scenario("landing-light", landing("light"), scheme="light")
    scenario("landing-dark", landing("dark"), scheme="dark")
    scenario("register", public_page("/register", "text=Join AgriVision", "03_register"))
    scenario("encyclopedia", public_page("/encyclopedia", "h2:has-text('Late blight')", "04_encyclopedia"))
    scenario("disease", public_page("/disease/Tomato___Late_blight", "h1:has-text('Late blight')", "05_disease_detail"))

    token = api_token()
    for i, (folder, crop) in enumerate(SAMPLES):
        fn, img = detect_one(folder, crop, "08_result" if i == 0 else None)
        if not img:
            print("skip (no dataset image):", folder)
            continue
        scenario(f"detect-{folder}", fn, token=token)

    scenario("login-dashboard", login_flow)
    scenario("history", authed("/history", "text=saved scan", "10_history"), token=token)
    scenario("analytics", authed("/analytics", "text=Disease distribution", "11_analytics"), token=token)
    scenario("profile", authed("/profile", "text=Edit profile", "12_profile"), token=token)
    scenario("light-dashboard", light_dashboard, scheme="light")

    if problems:
        print("\nPROBLEMS during the walk:")
        for line in problems:
            print(" -", line)
        return 1
    print("\nNo console errors, page errors or failed requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
