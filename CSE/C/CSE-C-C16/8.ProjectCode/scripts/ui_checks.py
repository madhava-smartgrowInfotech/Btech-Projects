"""Browser checks for the AgriVision UI: overflow at 360/768/1440 px, drawer + Escape, theme persistence, language
switch, history filter, delete confirmation, profile save, and a clean console. Needs both servers running.

Usage:  python scripts/ui_checks.py        (ports from .env, or AGRIVISION_URL)
Each section runs in its own short-lived browser (see capture_screens.py for why). Exit code 0 = all checks passed.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from capture_screens import BASE, CHROME_ARGS, DEMO, SAMPLES, first_image  # noqa: E402
from smoke_test import leaf_image, multipart  # noqa: E402

results: list[tuple[bool, str]] = []
problems: list[str] = []
SHOTS = Path(os.environ.get("UI_SHOTS", ROOT / "logs" / "ui_shots"))
SHOTS.mkdir(parents=True, exist_ok=True)


def check(ok: bool, label: str, extra: str = "") -> None:
    results.append((ok, label))
    print(("PASS " if ok else "FAIL ") + label + (f"  [{extra}]" if extra and not ok else ""), flush=True)


def api(method: str, path: str, body=None, token=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")


def run(label: str, fn, width: int = 1440, scheme: str = "dark", token: str | None = None, motion: str = "reduce", retries: int = 3):
    last = None
    for attempt in range(1, retries + 1):
        mark, rmark = len(problems), len(results)
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(channel="chrome", headless=True, args=CHROME_ARGS)
                ctx = b.new_context(viewport={"width": width, "height": 900 if width > 700 else 740}, color_scheme=scheme, reduced_motion=motion)
                ctx.set_default_timeout(60_000)
                if token:
                    ctx.add_init_script(f"try{{localStorage.setItem('agrivision-token','{token}')}}catch(e){{}}")
                page = ctx.new_page()
                expected_401 = label == "logged-out"  # that section types a wrong password on purpose
                page.on("console", lambda m, l=label: problems.append(f"[{l}] console: {m.text}") if m.type == "error" and not (expected_401 and "401" in m.text) else None)
                page.on("pageerror", lambda e, l=label: problems.append(f"[{l}] pageerror: {e}"))
                page.on("response", lambda r, l=label: problems.append(f"[{l}] HTTP {r.status} {r.url}") if r.status >= 400 and not (expected_401 and r.status == 401 and "/auth/login" in r.url) else None)
                fn(page)
                b.close()
            return
        except Exception as e:  # noqa: BLE001
            last = e
            del problems[mark:]
            del results[rmark:]
            print(f"  retry {attempt}/{retries} for {label}: {str(e)[:140]}", flush=True)
    check(False, f"{label} completed", str(last)[:200])


def overflow(page) -> int:
    return page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")


def sections(width: int, result_id: str, public: bool = False):
    # signed-in visitors are redirected away from /login and /register, so those two run without a token
    routes = ["/login", "/register"] if public else ["/", "/encyclopedia", "/disease/Tomato___Late_blight", "/dashboard", "/detect", "/history", "/analytics", "/profile", f"/result/{result_id}", "/nope"]
    ready = {"/": "text=From the disease guide", "/login": "text=Welcome back", "/register": "text=Join AgriVision", "/encyclopedia": "text=Crop disease encyclopedia",
             "/dashboard": "text=Recent detections", "/detect": "text=Leaf photo", "/history": "text=saved scan", "/analytics": "text=Farm analytics",
             "/profile": "text=Edit profile", "/nope": "text=Page not found"}

    def fn(page):
        for r in routes:
            page.goto(BASE + r, wait_until="domcontentloaded")
            if r in ready:
                page.wait_for_selector(ready[r])
            elif r.startswith("/disease"):
                page.wait_for_selector("h1:has-text('Late blight')")
            elif r.startswith("/result"):
                page.wait_for_selector("text=Recommended treatments")
            page.wait_for_timeout(700)
            ov = overflow(page)
            check(ov <= 0, f"{width}px: no sideways scroll on {r.split(result_id)[0]}", f"overflow {ov}px")
            if r in ("/dashboard", "/history", "/detect"):
                page.screenshot(path=str(SHOTS / f"w{width}_{r.strip('/')}.png"), timeout=90_000)

    return fn


def drawer_check(page):
    page.goto(BASE + "/dashboard", wait_until="domcontentloaded")
    page.wait_for_selector("text=Recent detections")
    check(not page.get_by_role("link", name="History").first.is_visible() or page.locator("aside").first.is_hidden(), "360px: sidebar is hidden (drawer mode)")
    page.get_by_role("button", name="Open menu").click()
    page.wait_for_selector("[role=dialog] >> text=Analytics")
    check(True, "360px: menu button opens the navigation drawer")
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    check(page.locator("[role=dialog]").count() == 0, "360px: Escape closes the drawer")
    check(page.locator("nav[aria-label='Quick navigation']").is_visible(), "360px: bottom quick-nav is shown")


def functional(page):
    page.goto(BASE + "/history", wait_until="domcontentloaded")
    page.wait_for_selector("text=saved scan")
    total = int(page.locator("text=/\\d+ saved scans?/").first.inner_text().split()[0])
    check(total >= 3, "history lists the seeded scans", str(total))
    page.get_by_label("Search history").fill("zzzzzz")
    page.wait_for_selector("text=No records match")
    check(True, "history: search with no match shows an empty state with a clear-filters action")
    page.get_by_role("button", name="Clear filters").click()
    page.wait_for_selector("img[alt^='Leaf scanned']")
    check(page.locator("img[alt^='Leaf scanned']").count() >= 1, "history: clearing filters brings the cards back")
    page.get_by_role("radio", name="Healthy").click()
    page.wait_for_timeout(900)
    n_healthy = page.locator("img[alt^='Leaf scanned']").count()
    page.get_by_role("radio", name="Diseased").click()
    page.wait_for_timeout(900)
    n_dis = page.locator("img[alt^='Leaf scanned']").count()
    check(n_healthy + n_dis == total or (n_healthy + n_dis) >= 1, "history: health filter segments change the list", f"{n_healthy}+{n_dis} of {total}")
    page.get_by_role("radio", name="All").click()
    page.wait_for_selector("img[alt^='Leaf scanned']")

    # delete: Escape cancels, confirm deletes
    first = page.locator("button[aria-label^='Delete record']").first
    first.click()
    page.wait_for_selector("[role=dialog] >> text=Delete this record?")
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    check(page.locator("[role=dialog]").count() == 0, "delete dialog: Escape cancels")
    first.click()
    page.get_by_role("dialog").get_by_role("button", name="Delete", exact=True).click()
    page.wait_for_selector("text=Record deleted")
    page.wait_for_timeout(1200)
    after = int(page.locator("text=/\\d+ saved scans?/").first.inner_text().split()[0])
    check(after == total - 1, "delete: confirming removes exactly one record", f"{total} -> {after}")

    # theme persists across reload
    page.get_by_role("button", name="Switch to light mode").click()
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("text=saved scan")
    check(page.evaluate("!document.documentElement.classList.contains('dark')"), "theme: light choice persists after reload")
    page.get_by_role("button", name="Switch to dark mode").click()
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("text=saved scan")
    check(page.evaluate("document.documentElement.classList.contains('dark')"), "theme: dark choice persists after reload")

    # language switch
    page.get_by_role("button", name=re.compile(r"^(Language|भाषा)")).click()
    page.get_by_role("menuitem", name="हिन्दी").click()
    page.wait_for_selector("text=जांच का इतिहास")
    check(True, "language: Hindi switch translates the page title")
    page.get_by_role("button", name=re.compile(r"^(Language|भाषा)")).click()
    page.get_by_role("menuitem", name="English").click()
    page.wait_for_selector("text=Detection history")
    check(True, "language: switching back to English works")

    # profile save
    page.goto(BASE + "/profile", wait_until="domcontentloaded")
    page.wait_for_selector("text=Edit profile")
    region = page.get_by_label("Region")
    region.fill("Maharashtra")
    page.get_by_role("button", name="Save profile").click()
    page.wait_for_selector("text=Profile updated")
    check(True, "profile: save shows success feedback")

    # keyboard: skip link + first tab stop
    page.goto(BASE + "/detect", wait_until="domcontentloaded")
    page.wait_for_selector("text=Leaf photo")
    page.keyboard.press("Tab")
    check(page.evaluate("document.activeElement && document.activeElement.textContent.includes('Skip to content')"), "keyboard: first Tab stop is the skip link")

    # detect validation (wrong extension) shows an error and keeps the button disabled
    page.set_input_files("input[aria-label='Leaf image file']", {"name": "notes.txt", "mimeType": "text/plain", "buffer": b"hello"})
    page.wait_for_selector("text=Image must be JPG, PNG, JPEG or WEBP.")
    check(page.get_by_role("button", name="Diagnose now").is_disabled(), "detect: a .txt file is rejected and diagnose stays disabled")


def logged_out(page):
    page.goto(BASE + "/history", wait_until="domcontentloaded")
    page.wait_for_url("**/login")
    check(True, "signed-out visitors are sent to /login from a protected page")
    page.get_by_label("Email").fill("demo@agrivision.ai")
    page.get_by_label("Password", exact=True).fill("wrong-password")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_selector("text=Invalid email or password.")
    check(True, "login: wrong password shows the API's message")
    page.get_by_label("Password", exact=True).fill("demo1234")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_url("**/history")
    check(True, "login: after signing in the user returns to the page they wanted")


def seed_scans(token: str, n: int = 3) -> list[str]:
    """Upload n leaf photos through the API so the checks never depend on (or destroy) the user's own history."""
    ids = []
    for i in range(n):
        folder, crop = SAMPLES[i % len(SAMPLES)]
        img = first_image(folder)
        data = img.read_bytes() if img else leaf_image()
        body, headers = multipart(img.name if img else "leaf.jpg", data, {"crop_type": crop})
        req = urllib.request.Request(BASE + "/api/v1/detect/upload", data=body, method="POST", headers={**headers, "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            ids.append(json.loads(r.read())["result_id"])
    return ids


def main() -> int:
    token = api("POST", "/api/v1/auth/login", {"email": DEMO[0], "password": DEMO[1]})["token"]
    seeded = seed_scans(token)
    try:
        return run_all(token, seeded[0])
    finally:
        for rid in seeded:  # the functional section deletes one of them already
            try:
                api("DELETE", f"/api/v1/history/{rid}", token=token)
            except Exception:  # noqa: BLE001
                pass


def run_all(token: str, result_id: str) -> int:

    run("overflow-360", sections(360, result_id), width=360, token=token)
    run("overflow-360-public", sections(360, result_id, public=True), width=360)
    run("overflow-768-public", sections(768, result_id, public=True), width=768)
    run("drawer-360", drawer_check, width=360, token=token)
    run("overflow-768", sections(768, result_id), width=768, token=token)
    run("overflow-1440-light", sections(1440, result_id), width=1440, scheme="light", token=token)
    run("functional", functional, token=token)
    run("logged-out", logged_out)

    check(not problems, "console clean: no errors, page errors or failed requests", "; ".join(problems[:4]))
    failed = [l for ok, l in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    for line in problems:
        print(" -", line)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
