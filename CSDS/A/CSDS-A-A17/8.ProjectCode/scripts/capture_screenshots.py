"""Capture real screenshots of the running CropSight app (1440x900) into docs/screenshots/.

Prerequisites: API on 127.0.0.1:8000 and web on 127.0.0.1:5190 (seeded database, scripts/seed_db.py), real photos in
docs/sample_inputs/ (scripts/pick_sample_photos.py).  Run with a Python that has playwright and httpx:

    venv\\Scripts\\python scripts/capture_screenshots.py

The featured flow (tomato -> grade -> forecast -> delivery plan -> publish -> order -> confirm -> transit -> monitor) is driven through
the browser UI; the extra listings and orders that fill the lists are created through the same API the UI calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
PHOTOS = ROOT / "docs" / "sample_inputs"
WEB = "http://127.0.0.1:5190"
API = "http://127.0.0.1:8000/api"
PW = "cropsight123"
log: dict = {"screens": [], "ids": {}}


def token(email: str) -> dict:
    r = httpx.post(f"{API}/auth/login", json={"email": email, "password": PW}, timeout=60)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def shot(page: Page, name: str, note: str, full: bool = False, wait: int = 1500) -> None:
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    log["screens"].append({"file": f"{name}.png", "shows": note})
    print("saved", name, flush=True)


def login(page: Page, email: str, expect: str) -> None:
    page.goto(f"{WEB}/login")
    page.wait_for_timeout(1000)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(PW)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"**{expect}**", timeout=20000)
    page.wait_for_timeout(1500)


def logout(page: Page) -> None:
    page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
    page.goto(f"{WEB}/login")
    page.wait_for_timeout(800)


def api_listing(h: dict, crop: str, photo: str, qty: int, region: str, price: float | None):
    with open(PHOTOS / photo, "rb") as f:
        r = httpx.post(f"{API}/crops/upload", headers=h, data={"crop_type": crop, "region": region, "quantity_kg": qty},
                       files={"image": (photo, f.read(), "image/jpeg")}, timeout=120)
    r.raise_for_status()
    lid = r.json()["id"]
    if price:
        httpx.post(f"{API}/crops/{lid}/list", headers=h, params={"asking_price": price}, timeout=60).raise_for_status()
    return r.json()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    chosen = json.loads((PHOTOS / "_chosen.json").read_text(encoding="utf-8"))
    kept = {c: v["kept"] for c, v in chosen.items()}
    farmer_h, buyer_h, dist_h = token("farmer@cropsight.dev"), token("buyer1@cropsight.dev"), token("distributor@cropsight.dev")
    region = httpx.get(f"{API}/auth/me", headers=farmer_h).json()["region"]

    # ---- extra listings and orders created through the API so that the lists are populated
    onion = api_listing(farmer_h, "Onion", kept["Onion"][0]["file"], 900, region, 1650)
    potato = api_listing(farmer_h, "Potato", kept["Potato"][-1]["file"], 1200, region, 1100)
    potato2 = api_listing(farmer_h, "Potato", kept["Potato"][0]["file"], 640, region, 1180)
    log["ids"].update({"onion": onion["id"], "potato": potato["id"], "potato2": potato2["id"]})
    # buyer 2 orders the onion (stays 'placed'); buyer 3 orders potato and the farmer confirms it (stays 'confirmed')
    b2, b3 = token("buyer2@cropsight.dev"), token("buyer3@cropsight.dev")
    o1 = httpx.post(f"{API}/marketplace/orders", headers=b2, json={"listing_id": onion["id"], "quantity_kg": 900, "agreed_price": 1640}).json()
    o2 = httpx.post(f"{API}/marketplace/orders", headers=b3, json={"listing_id": potato["id"], "quantity_kg": 1200, "agreed_price": 1090}).json()
    httpx.patch(f"{API}/marketplace/orders/{o2['id']}/status", headers=farmer_h, json={"status": "confirmed"}).raise_for_status()
    log["ids"].update({"order_placed": o1["id"], "order_confirmed": o2["id"]})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()

        # ---- public pages
        page.goto(WEB)
        shot(page, "01_landing", "Landing page: hero, product pitch and platform statistics", wait=7000)
        shot(page, "01b_landing_full", "Landing page, full length", full=True, wait=500)
        page.goto(f"{WEB}/login")
        shot(page, "02_login", "Log-in page with the demo-account shortcuts")
        page.get_by_label("Email").fill("farmer@cropsight.dev")
        page.get_by_label("Password").fill("wrong-password")
        page.get_by_role("button", name="Log in").click()
        shot(page, "03_login_error", "Failure case: wrong password is rejected by the API (HTTP 401) and reported", wait=1500)
        page.goto(f"{WEB}/signup")
        shot(page, "04_signup", "Sign-up page: role choice (farmer, buyer, distributor), region and contact details")

        # ---- farmer: upload and grade a tomato photo through the UI
        login(page, "farmer@cropsight.dev", "/farmer")
        shot(page, "05_farmer_dashboard", "Farmer dashboard before the upload: crop, quantity and photo drop zone, existing listings")
        page.locator("select#crop").select_option("Tomato")
        page.locator("input#qty").fill("620")
        tomato = kept["Tomato"][0]["file"]
        page.set_input_files("input[type=file]", str(PHOTOS / tomato))
        shot(page, "06_upload_preview", f"A real tomato photograph ({tomato}) selected for grading, with preview", wait=800)
        page.get_by_role("button", name="Grade this crop").click()
        page.wait_for_url("**/farmer/listings/**", timeout=90000)
        lid = int(page.url.rstrip("/").split("/")[-1])
        log["ids"]["tomato"] = lid
        shot(page, "07_grading_result", "Grading result: grade, confidence, class probabilities, computer-vision features and SHAP explanation", wait=3500)
        shot(page, "07b_grading_full", "Listing workspace, full length, after grading", full=True, wait=500)

        # ---- forecast and delivery plan
        page.get_by_role("button", name="Forecast price").click()
        page.wait_for_selector("text=Best day to sell", timeout=60000)
        shot(page, "08_price_forecast", "Price forecast: current price, 30-day curve with confidence band, best day to sell and SHAP drivers", wait=3000)
        page.mouse.wheel(0, 600)
        shot(page, "08b_price_forecast_scrolled", "Price forecast panel, lower part", wait=1000)
        page.get_by_role("button", name="Plan delivery").click()
        page.wait_for_timeout(2500)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        shot(page, "09_delivery_planner", "Delivery planner: buyers ranked by price, distance, reliability and spoilage risk, with the best route", wait=2000)
        page.locator("input#ask").fill("2250")
        shot(page, "10_publish_listing", "Asking price entered and the Publish listing action", wait=800)
        page.get_by_role("button", name="Publish listing").click()
        page.wait_for_timeout(2500)
        shot(page, "11_listing_published", "Listing published to the marketplace", wait=1000)
        page.goto(f"{WEB}/farmer")
        shot(page, "12_farmer_listings", "Farmer dashboard with graded listings (tomato, onion, potatoes) and their status", wait=2500)
        page.mouse.wheel(0, 500)
        shot(page, "12b_farmer_listings_scrolled", "Farmer listings, lower part", wait=800)

        # ---- buyer: browse, inspect, order
        logout(page)
        login(page, "buyer1@cropsight.dev", "/buyer")
        shot(page, "13_marketplace", "Buyer marketplace: listed crops with grade, quantity and asking price", wait=2500)
        page.goto(f"{WEB}/buyer/listings/{lid}")
        shot(page, "14_listing_detail", "Listing detail for the buyer: quality breakdown and market price trend", wait=3500)
        page.get_by_role("button", name="Place order").click()
        page.wait_for_timeout(800)
        page.locator("input#q").fill("620")
        page.locator("input#p").fill("2250")
        shot(page, "15_place_order_dialog", "Place-order dialog: quantity and agreed price", wait=500)
        page.get_by_role("button", name="Confirm order").click()
        page.wait_for_timeout(2500)
        page.goto(f"{WEB}/buyer/orders")
        shot(page, "16_buyer_orders", "Buyer orders: the new order is in the placed state", wait=2000)

        # ---- farmer: confirm the order
        logout(page)
        login(page, "farmer@cropsight.dev", "/farmer")
        page.goto(f"{WEB}/farmer/orders")
        shot(page, "17_farmer_orders_placed", "Farmer orders: placed orders waiting for confirmation", wait=2000)
        row = page.locator("div", has_text=f"Order #").filter(has=page.get_by_role("button", name="Confirm"))
        btns = page.get_by_role("button", name="Confirm")
        # confirm the tomato order (the last 'placed' order created through the UI is the newest = first button)
        btns.first.click()
        page.wait_for_timeout(2000)
        shot(page, "18_farmer_orders_confirmed", "Farmer orders after confirming one order", wait=800)

        # ---- distributor: start transit and watch the sensor stream
        logout(page)
        login(page, "distributor@cropsight.dev", "/distributor")
        shot(page, "19_distributor_deliveries", "Distributor: confirmed orders ready to ship", wait=2500)
        start = page.get_by_role("button", name="Start transit")
        n = start.count()
        for i in range(n):
            start.first.click()
            page.wait_for_timeout(1800)
        shot(page, "20_distributor_in_transit", "Distributor: orders in transit with Live monitor and Mark delivered actions", wait=1500)
        page.get_by_role("button", name="Live monitor").first.click()
        page.wait_for_url("**/distributor/shipments/**", timeout=20000)
        log["ids"]["shipment_url"] = page.url
        shot(page, "21_live_monitoring_start", "Live monitoring just after opening the WebSocket", wait=6000)
        page.wait_for_timeout(52000)
        shot(page, "22_live_monitoring", "Live monitoring after about one minute of streaming (temperature, humidity, shock) with the alert banner", wait=500)

        # ---- admin
        logout(page)
        login(page, "admin@cropsight.dev", "/admin")
        shot(page, "23_admin_overview", "Admin overview: users by role, listings, orders and gross volume", wait=5000)
        page.goto(f"{WEB}/admin/models")
        shot(page, "24_model_insights", "Admin model insights: both models, accuracy, MAE/R2, feature importance and training-data disclosure", wait=3500)
        page.mouse.wheel(0, 700)
        shot(page, "24b_model_insights_scrolled", "Model insights, lower part", wait=800)
        browser.close()
    (OUT / "_run.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
