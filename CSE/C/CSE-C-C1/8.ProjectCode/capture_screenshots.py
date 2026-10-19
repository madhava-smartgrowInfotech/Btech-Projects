import time, pathlib, threading, uvicorn, sys
from app.main import app

# Start server in thread
def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

thread = threading.Thread(target=start_server, daemon=True)
thread.start()
time.sleep(3)

from playwright.sync_api import sync_playwright

pathlib.Path("screenshots").mkdir(exist_ok=True)

def shot(page, path, wait=1000):
    page.wait_for_timeout(wait)
    page.screenshot(path=path, full_page=True)
    print(f"saved {path}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    # 1 login
    page.goto("http://localhost:8000/login")
    shot(page, "screenshots/01_login.png")

    # login as admin
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "Admin@123")
    page.click('button[type="submit"]')
    page.wait_for_timeout(2000)
    shot(page, "screenshots/02_admin_dashboard.png")

    # election management
    page.goto("http://localhost:8000/admin/elections")
    shot(page, "screenshots/03_election_management.png")

    # election detail
    page.goto("http://localhost:8000/admin/elections/1")
    shot(page, "screenshots/04_election_detail.png")

    # logout and voter flow
    page.goto("http://localhost:8000/logout")
    page.goto("http://localhost:8000/login")
    page.fill('input[name="username"]', "voter1")
    page.fill('input[name="password"]', "Voter@01pass")
    page.click('button[type="submit"]')
    page.wait_for_timeout(1500)
    # voter home
    shot(page, "screenshots/05_voter_home.png")

    # voter verify screen
    page.goto("http://localhost:8000/voter/verify/1")
    shot(page, "screenshots/06_voter_aadhaar_verification.png")

    # Need real aadhaar for voter1
    import json, pathlib
    syn = json.loads(pathlib.Path("data/synthetic_identities.json").read_text())
    voter1 = syn[0]
    aadhaar = voter1["aadhaar"]
    page.fill('input[name="aadhaar"]', aadhaar)
    page.click('button[type="submit"]')
    page.wait_for_timeout(2000)
    # candidate selection
    shot(page, "screenshots/07_candidate_selection.png")

    # select first candidate and show confirm
    # click first radio
    try:
        page.click('input[type="radio"]')
        page.wait_for_timeout(800)
        shot(page, "screenshots/08_vote_confirmation.png")
        # submit
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        shot(page, "screenshots/09_blockchain_receipt.png")
    except Exception as e:
        print(f"candidate select failed: {e}")
        # if already voted, still capture
        shot(page, "screenshots/08_vote_confirmation_already.png")

    # results - need to close election first as admin, view results
    page.goto("http://localhost:8000/logout")
    page.goto("http://localhost:8000/login")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "Admin@123")
    page.click('button[type="submit"]')
    page.wait_for_timeout(1500)
    page.goto("http://localhost:8000/admin/results/2")
    shot(page, "screenshots/10_results.png")

    # auditor
    page.goto("http://localhost:8000/logout")
    page.goto("http://localhost:8000/login")
    page.fill('input[name="username"]', "auditor")
    page.fill('input[name="password"]', "Audit@123")
    page.click('button[type="submit"]')
    page.wait_for_timeout(1500)
    shot(page, "screenshots/11_auditor_explorer.png")

    # verify integrity
    page.click('button:has-text("Verify Ledger Integrity")')
    page.wait_for_timeout(1500)
    shot(page, "screenshots/12_ledger_integrity.png")

    # performance dashboard via admin? but auditor also has?
    page.goto("http://localhost:8000/logout")
    page.goto("http://localhost:8000/login")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "Admin@123")
    page.click('button[type="submit"]')
    page.wait_for_timeout(1500)
    page.goto("http://localhost:8000/admin/benchmark")
    shot(page, "screenshots/13_performance_dashboard.png")

    browser.close()
    print("all screenshots done")
    sys.exit(0)
