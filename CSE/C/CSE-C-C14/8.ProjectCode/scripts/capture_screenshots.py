"""Capture real browser screenshots of the running VeriVision AI app."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8414"
SHOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")

fake_imgs = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "test", "fake", "*")))
upload_img = fake_imgs[0]
print("uploading:", upload_img, flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(SHOT, "01_home.png"))
    print("01_home.png", flush=True)

    page.set_input_files("#file-input", upload_img)
    page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(SHOT, "02_upload.png"))
    print("02_upload.png", flush=True)

    with page.expect_navigation(wait_until="networkidle", timeout=300000):
        page.click("#analyze-btn")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SHOT, "03_result_real_or_fake.png"), full_page=True)
    print("03_result done", flush=True)

    # Grad-CAM close-up: scroll to explanation section
    page.evaluate("document.querySelector('.cam-wrap').scrollIntoView({block: 'center'})")
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOT, "04_gradcam_explanation.png"))
    # Branch votes close-up
    page.evaluate("document.querySelector('.grid2').scrollIntoView({block: 'center'})")
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOT, "05_model_details.png"))
    print("04/05 done", flush=True)

    page.goto(BASE + "/insights", wait_until="networkidle")
    page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(SHOT, "06_evaluation_metrics.png"), full_page=True)
    print("06 done", flush=True)
    browser.close()
print("All screenshots captured.", flush=True)
