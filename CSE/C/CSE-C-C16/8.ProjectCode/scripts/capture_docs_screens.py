"""Extra screenshots for the documentation (docs/screenshots/15..19): a correct diagnosis, the crop-hint failure, the Hindi interface and a phone-width screen.

Needs both servers running (run.bat, or backend 8416 + `vite preview` 5416). Re-uses the helpers of capture_screens.py.
Scans created here are removed again so the demo account stays as it was.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import capture_screens as C  # noqa: E402

TEST = ROOT / "datasets" / "plantdoc-images" / "test"
CORRECT = TEST / "Potato_leaf_early_blight" / "02448_earlyblightpotato.jpg"
BLUEBERRY = TEST / "Blueberry_leaf"


def diagnose(img: Path, crop: str, name: str, lang: str | None = None):
    def run(page):
        if lang:
            page.add_init_script(f"try{{localStorage.setItem('agrivision-lang','{lang}')}}catch(e){{}}")
        page.goto(f"{C.BASE}/detect?crop={crop}", wait_until="domcontentloaded")
        page.set_input_files("input[aria-label='Leaf image file']", str(img))
        page.wait_for_selector("img[alt='Preview of the chosen leaf']")
        btn = page.locator("button:has-text('Diagnose now'), button:has-text('निदान करें')").first
        btn.click()
        page.wait_for_url("**/result/*", timeout=C.TIMEOUT)
        page.wait_for_selector("h1")
        page.wait_for_timeout(1500)
        C.shot(page, name)

    return run


def blueberry_error(page):
    img = sorted(p for p in BLUEBERRY.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))[0]
    page.goto(f"{C.BASE}/detect?crop=blueberry", wait_until="domcontentloaded")
    page.set_input_files("input[aria-label='Leaf image file']", str(img))
    page.wait_for_selector("img[alt='Preview of the chosen leaf']")
    page.get_by_role("button", name="Diagnose now").click()
    page.wait_for_selector("text=could not be read", timeout=C.TIMEOUT)
    page.wait_for_timeout(800)
    C.shot(page, "16_error_blueberry")


def hindi_dashboard(page):
    page.goto(f"{C.BASE}/dashboard", wait_until="domcontentloaded")
    page.wait_for_selector("text=Recent detections")
    page.wait_for_selector("img[alt^='Leaf scanned']")
    page.get_by_role("button", name="Language: English").click()
    page.get_by_role("menuitem", name="हिन्दी").click()
    page.wait_for_selector("text=नमस्ते")
    page.wait_for_timeout(1200)
    C.shot(page, "17_dashboard_hindi")


def restore_english(token):
    import json
    import urllib.request

    me = json.loads(urllib.request.urlopen(urllib.request.Request(C.BASE + "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})).read())
    body = json.dumps({"full_name": me["full_name"], "region": me["region"], "language": "en", "crops": me["crops"]}).encode()
    urllib.request.urlopen(urllib.request.Request(C.BASE + "/api/v1/profile", data=body, method="PUT",
                                                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})).read()


def phone(page):
    page.goto(f"{C.BASE}/dashboard", wait_until="domcontentloaded")
    page.wait_for_selector("text=Recent detections")
    page.wait_for_selector("img[alt^='Leaf scanned']")
    C.shot(page, "18_mobile_dashboard")


def scenario_viewport(label, fn, token, width, height):
    """Like C.scenario but with a custom viewport."""
    from playwright.sync_api import sync_playwright

    last = None
    for attempt in range(1, 4):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="chrome", headless=True, args=C.CHROME_ARGS)
                ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme="dark", reduced_motion=C.RM)
                ctx.set_default_timeout(C.TIMEOUT)
                ctx.add_init_script(f"try{{localStorage.setItem('agrivision-token','{token}')}}catch(e){{}}")
                page = ctx.new_page()
                fn(page)
                browser.close()
            return
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  retry {attempt}/3 for {label}: {str(e)[:120]}", flush=True)
    raise RuntimeError(f"{label}: {last}")


def seed(token):
    """Upload the six sample photos of capture_screens.py through the API so the dashboard and history are not empty."""
    import json
    import urllib.request

    from smoke_test import multipart

    for folder, crop in C.SAMPLES:
        img = C.first_image(folder)
        if not img:
            continue
        body, hdr = multipart(img.name, img.read_bytes(), {"crop_type": crop})
        urllib.request.urlopen(urllib.request.Request(C.BASE + "/api/v1/detect/upload", data=body, method="POST",
                                                      headers={**hdr, "Authorization": f"Bearer {token}"}), timeout=60).read()


def main() -> int:
    token = C.api_token()
    before = C.history_ids(token)
    try:
        seed(token)
        C.scenario("correct", diagnose(CORRECT, "potato", "15_result_correct"), token=token)
        C.scenario("blueberry", blueberry_error, token=token)
        C.scenario("hindi", hindi_dashboard, token=token)
        scenario_viewport("phone", phone, token, 390, 844)
    finally:
        restore_english(token)
        C.forget(token, C.history_ids(token) - before)
    return 0


if __name__ == "__main__":
    sys.exit(main())
