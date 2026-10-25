"""Extra screens for the documentation: low-risk results, a validation error, an out-of-range warning and a phone layout.

Needs the app running.  Usage:  python scripts/capture_extra.py   (writes docs/screenshots/13_* .. 20_*)
"""
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
FRONT = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5303")


def shot(page, name):
    page.screenshot(path=os.path.join(OUT, f"{name}.png"))
    print("saved", name)


def dismiss(page):
    for close in page.get_by_role("button", name="Dismiss notification").all():
        close.click()
    page.wait_for_timeout(500)


with sync_playwright() as p:
    try:
        browser = p.chromium.launch(channel="chrome")
    except Exception:
        browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script("try{localStorage.setItem('mdp-theme','dark')}catch(e){}")
    page = ctx.new_page()
    n = 13
    for key in ("diabetes", "heart", "liver", "kidney"):
        page.goto(f"{FRONT}/app/predict/{key}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(600)
        # draw label-0 records until the model also says Low Risk (a label-0 record the model calls High Risk
        # is a genuine false positive; the first such case is kept as 20_predict-heart-false-positive)
        for _attempt in range(10):
            page.get_by_role("button", name="Negative sample").click()
            page.wait_for_timeout(900)
            page.get_by_role("button", name="Predict risk").click()
            title = page.get_by_role("heading", level=3).filter(has_text="Risk").first
            title.wait_for(timeout=8000)
            page.wait_for_timeout(900)
            if "Low Risk" in title.inner_text():
                break
            page.get_by_role("button", name="Clear").click()
        dismiss(page)
        shot(page, f"{n:02d}_predict-{key}-low-risk")
        n += 1

    # validation error: submit an empty form
    page.goto(f"{FRONT}/app/predict/diabetes")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(600)
    page.get_by_role("button", name="Predict risk").click()
    page.wait_for_timeout(700)
    shot(page, "17_validation-error")

    # out-of-range warning: fill one field far outside the training range
    page.get_by_role("button", name="Positive sample").click()
    page.wait_for_timeout(900)
    page.locator("#f-Glucose").fill("900")
    page.wait_for_timeout(500)
    dismiss(page)
    shot(page, "18_out-of-range-warning")
    ctx.close()

    # phone layout
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    ctx.add_init_script("try{localStorage.setItem('mdp-theme','dark')}catch(e){}")
    page = ctx.new_page()
    page.goto(f"{FRONT}/app/predict/heart")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    page.get_by_role("button", name="Positive sample").click()
    page.wait_for_timeout(900)
    dismiss(page)
    shot(page, "19_predict-heart-mobile")
    ctx.close()
    browser.close()
