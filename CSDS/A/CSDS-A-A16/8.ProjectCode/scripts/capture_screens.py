"""Captures every product screen at 1440x900 with real data. Needs the API on 8116 and the Next.js UI on 3000
(started with NEXT_PUBLIC_API_URL=http://localhost:8116/api). Run: python scripts/capture_screens.py
"""
import io
import json
import pickle
import time
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "screenshots"
INP = SHOTS / "inputs"
BASE = "http://localhost:3000"
API = "http://127.0.0.1:8116/api"

# a real FER2013 face at its native 48x48 size -> Haar detector finds nothing (documented failure case)
items = pickle.load((ROOT / "backend/data/test.pt").open("rb"))
native = [e for e in items if e["labels"] == "happy"][3]
Image.open(io.BytesIO(native["img_bytes"])).convert("L").save(INP / "native48_happy.png")

log = []


def shot(page, name, wait=1.2, full=False):
    time.sleep(wait)
    path = SHOTS / name
    page.screenshot(path=str(path), full_page=full)
    log.append(name)
    print("saved", name)


def analyze(page, file, name, wait=3.5):
    # a hard reload of /app sends the user back to /login (documented defect), so stay on the client-side router
    if page.locator("text=Retake").count():
        page.click("text=Retake")
    page.wait_for_selector("input[type=file]", state="attached")
    page.set_input_files("input[type=file]", str(INP / file))
    shot(page, name, wait=wait)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--disable-gpu", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page = ctx.new_page()

    page.goto(BASE)
    shot(page, "01_landing_hero.png", wait=8)
    page.evaluate("document.querySelector('#features')?.scrollIntoView()")
    shot(page, "02_landing_features.png", wait=3)
    page.evaluate("document.querySelector('#how-it-works')?.scrollIntoView()")
    shot(page, "03_landing_how_it_works.png", wait=3)

    page.goto(f"{BASE}/login")
    shot(page, "04_login.png", wait=2)
    page.goto(f"{BASE}/register")
    page.wait_for_selector("input[type=email]")
    shot(page, "05_register.png", wait=2)
    page.fill("input[placeholder='Ada Lovelace']", "Demo Analyst")
    page.fill("input[type=email]", "demo.analyst@example.com")
    page.fill("input[type=password]", "demo-pass-2026")
    shot(page, "06_register_filled.png", wait=0.5)
    page.click("button[type=submit]")
    page.wait_for_url("**/app", timeout=30000)

    page.wait_for_selector("input[type=file]", state="attached")
    shot(page, "07_analyze_empty.png", wait=2)

    analyze(page, "happy_01.jpg", "08_result_happy.png")
    analyze(page, "angry_04.jpg", "09_result_angry.png")
    analyze(page, "sad_03.jpg", "10_result_sad.png")
    analyze(page, "fear_05.jpg", "11_result_fear.png")
    analyze(page, "neutral_02.jpg", "12_result_neutral_misread.png")
    analyze(page, "surprise_07.jpg", "13_result_surprise_misread.png")
    analyze(page, "gan_happily_surprised.jpg", "14_result_gan_happily_surprised.png")
    analyze(page, "gan_angrily_disgusted.jpg", "15_result_gan_angrily_disgusted.png")
    analyze(page, "native48_happy.png", "16_result_no_face.png")

    page.click("aside >> text=History")
    page.wait_for_url("**/app/history")
    shot(page, "17_history.png", wait=4)
    # the history list has no link to the detail route, so open it by id (the route exists in the app)
    hid = page.evaluate("""async () => { const t = JSON.parse(localStorage.getItem('mosaic-auth')).state.token;
        const r = await fetch('http://127.0.0.1:8116/api/history?limit=20', {headers: {Authorization: 'Bearer ' + t}});
        const j = await r.json(); return j.items[2].id; }""")
    page.evaluate(f"window.next.router.push('/app/history/{hid}')")
    page.wait_for_url("**/app/history/*")
    shot(page, "18_history_detail.png", wait=4)

    page.click("aside >> text=Analyze")
    page.wait_for_selector("input[type=file]", state="attached")
    page.click("text=Webcam")
    shot(page, "19_webcam_tab.png", wait=2)
    browser.close()

(SHOTS / "inventory.json").write_text(json.dumps(log, indent=1))
