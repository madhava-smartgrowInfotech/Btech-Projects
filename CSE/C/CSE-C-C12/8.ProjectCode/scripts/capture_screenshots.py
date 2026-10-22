"""Capture real screenshots from the running app (requires playwright)."""
import sys, time, subprocess, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
SHOT = BASE / "screenshots"
SHOT.mkdir(exist_ok=True)

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)
    url = os.getenv("CARELENS_URL", "http://localhost:8000")
    import uuid
    email = f"demo{uuid.uuid4().hex[:6]}@example.com"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.goto(url); pg.wait_for_timeout(1200); pg.screenshot(path=str(SHOT / "01-landing.png"))
        pg.goto(url + "/register"); pg.wait_for_timeout(800); pg.screenshot(path=str(SHOT / "02-register.png"))
        pg.goto(url + "/login"); pg.wait_for_timeout(800); pg.screenshot(path=str(SHOT / "03-login.png"))
        # register/login
        pg.goto(url + "/register"); pg.wait_for_timeout(500)
        try:
            pg.fill('input[name="email"]', email); pg.fill('input[name="password"]', "Demo1234")
            pg.click('button[type="submit"]'); pg.wait_for_timeout(1500)
        except Exception as e:
            print("register step:", e)
        if "dashboard" not in pg.url:
            pg.goto(url + "/login"); pg.wait_for_timeout(500)
            try:
                pg.fill('input[name="email"]', email); pg.fill('input[name="password"]', "Demo1234")
                pg.click('button[type="submit"]'); pg.wait_for_timeout(1500)
            except Exception as e:
                print("login step:", e)
        pg.wait_for_timeout(1000); pg.screenshot(path=str(SHOT / "04-dashboard.png"))
        # chat query
        try:
            pg.wait_for_selector('#q', timeout=15000)
            pg.fill('#q', 'I have high fever, headache and body pain')
            pg.click('#chat-form button[type="submit"]'); pg.wait_for_timeout(12000)
        except Exception as e:
            print("chat step:", e)
        pg.screenshot(path=str(SHOT / "05-chat-response.png"), full_page=True)
        # safety query
        try:
            pg.fill('#q', 'severe chest pain and difficulty breathing')
            pg.click('#chat-form button[type="submit"]'); pg.wait_for_timeout(12000)
        except Exception as e:
            print("safety step:", e)
        pg.screenshot(path=str(SHOT / "06-safety-warning.png"), full_page=True)
        pg.goto(url + "/history"); pg.wait_for_timeout(1500); pg.screenshot(path=str(SHOT / "07-history.png"), full_page=True)
        try:
            btn = pg.query_selector('.hist-row .btn')
            if btn: btn.click(); pg.wait_for_timeout(1200)
            pg.screenshot(path=str(SHOT / "08-detail.png"), full_page=True)
        except Exception as e:
            print("detail step:", e)
        b.close()
    print("Screenshots saved to", SHOT)

if __name__ == "__main__":
    main()
