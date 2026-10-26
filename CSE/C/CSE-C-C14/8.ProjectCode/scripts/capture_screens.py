"""Capture real 1440x900 screenshots of every VeriVision AI screen into docs/screenshots/.

Needs the API (8414) and the frontend (5414) running - run.bat starts both.
    pip install playwright   (uses the installed Chrome via channel="chrome"; falls back to bundled chromium)
    python scripts/capture_screens.py
It signs in with the demo account, analyzes a real test image from data/test and
walks every screen, failing loudly on console errors or failed requests.
"""
import glob
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
FRONT = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5414")
EMAIL = os.environ.get("VERIVISION_DEMO_EMAIL", "demo@verivision.ai")
PASSWORD = os.environ.get("VERIVISION_DEMO_PASSWORD", "Demo@1234")


def sample_image():
    for pattern in ("data/cifake/test/fake/*.png", "data/test/fake/*.png", "data/test/real/*.png", "data/test/*/*.jpg"):
        files = sorted(glob.glob(os.path.join(ROOT, pattern)))
        if files:
            return files[0]
    from PIL import Image
    path = os.path.join(OUT, "_sample.png")
    Image.linear_gradient("L").resize((256, 256)).convert("RGB").save(path)
    return path


def launch(p):
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


def main():
    os.makedirs(OUT, exist_ok=True)
    problems = []
    image = sample_image()
    print("analyzing:", image, flush=True)

    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        page = ctx.new_page()
        page.on("console", lambda m: problems.append(f"console {m.type}: {m.text}") if m.type in ("error",) else None)
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on("response", lambda r: problems.append(f"HTTP {r.status} {r.url}") if r.status >= 400 and "/api/auth/me" not in r.url else None)

        def shot(name, full=False):
            page.wait_for_timeout(2200)  # let CountUp / spring animations settle
            path = os.path.join(OUT, f"{name}.png")
            page.screenshot(path=path, full_page=full)
            print("saved", os.path.relpath(path, ROOT), flush=True)

        def set_theme(theme):
            page.evaluate("t => { document.documentElement.dataset.theme = t; localStorage.setItem('verivision-theme', t) }", theme)

        # landing, light + dark (scroll once so scroll-reveal sections are visible)
        page.goto(FRONT + "/", wait_until="networkidle")
        set_theme("light")
        page.wait_for_selector("text=The ensemble")
        shot("01_landing_light")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        set_theme("dark")
        shot("02_landing_dark")
        set_theme("light")
        for anchor, name in (("#features", "15_landing_features"), ("#numbers", "16_landing_numbers")):
            page.evaluate("a => document.querySelector(a).scrollIntoView({ block: 'start' })", anchor)
            page.evaluate("window.scrollBy(0, -80)")
            shot(name)

        # login
        page.goto(FRONT + "/login", wait_until="networkidle")
        page.wait_for_selector("text=Use demo account")
        shot("03_login")
        page.fill("input[type=email]", EMAIL)
        page.fill("input[type=password]", PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_url("**/app")

        # analyze: empty, with preview, running, result
        page.wait_for_selector("text=Choose an image")
        shot("04_analyze_empty")
        page.set_input_files("input[type=file]", image)
        page.wait_for_selector("img[alt^='Preview of']")
        shot("05_analyze_ready")
        page.click("button:has-text('Analyze image')")
        page.wait_for_selector("text=Running 4 detectors")
        shot("06_analyze_running")
        page.wait_for_selector("text=Here is what the ensemble found", timeout=300000)
        page.wait_for_timeout(1500)
        shot("07_result_verdict")
        page.get_by_text("Branch votes", exact=True).first.evaluate("e => e.scrollIntoView({ block: 'start' })")
        page.evaluate("window.scrollBy(0, -100)")
        shot("08_result_votes_robustness")
        page.get_by_text("Visual explanation (Grad-CAM)").evaluate("e => e.scrollIntoView({ block: 'start' })")
        page.evaluate("window.scrollBy(0, -100)")
        shot("09_result_gradcam")
        page.get_by_role("tab", name="ResNet50").click()
        shot("10_result_gradcam_resnet")

        # two more analyses: a real CIFAKE test image and a full-resolution AI image from the cross-domain probe set
        for name, pattern in (("17_result_real", "data/cifake/test/real/*.png"), ("18_result_hires_ai", "data/xdomain/test/fake/*.jpg"), ("19_result_hires_real", "data/xdomain/test/real/*.jpg")):
            files = sorted(glob.glob(os.path.join(ROOT, pattern)))
            if not files:
                continue
            page.get_by_role("button", name="Analyze another image").click()
            page.wait_for_selector("text=Choose an image")
            page.set_input_files("input[type=file]", files[0])
            page.wait_for_selector("img[alt^='Preview of']")
            page.click("button:has-text('Analyze image')")
            page.wait_for_selector("text=Here is what the ensemble found", timeout=300000)
            page.wait_for_timeout(1500)
            shot(name)

        # the other screens
        for path, wait, name in (
            ("/app/insights", "text=Confusion matrix", "11_insights"),
            ("/app/models", "text=Fusion weights", "12_models"),
            ("/app/status", "text=Health response", "13_status"),
        ):
            page.get_by_role("link", name=_nav_label(path)).first.click()
            page.wait_for_selector(wait)
            shot(name)

        # dark mode in-app
        page.get_by_role("link", name="Model insights").first.click()
        page.wait_for_selector("text=Confusion matrix")
        page.get_by_role("button", name="Switch to dark mode").click()
        shot("14_insights_dark")
        browser.close()

    if problems:
        print("\nPROBLEMS:")
        for line in problems:
            print(" -", line)
        sys.exit(1)
    print("\nAll screens captured with a clean console.")


def _nav_label(path):
    return {"/app/insights": "Model insights", "/app/models": "How it works", "/app/status": "System status"}[path]


if __name__ == "__main__":
    main()
