"""Captures every screen of the running app at 1440x900 into docs/screenshots/<nn>_<screen>.png.

    python scripts\\capture_screens.py public        # landing / sign-up / login (no API quota used)
    python scripts\\capture_screens.py freelance     # registers the demo user, uploads the freelance DOCX, captures the report screens
    python scripts\\capture_screens.py others        # balanced DOCX, real CUAD PDF, error state, list, evaluation

Needs the app on http://localhost:5106 (backend 8106) and a working GEMINI_API_KEY. Each upload makes one
Gemini call per flagged clause plus one for the summary, so run the upload steps once. Uses system Python
with Playwright (channel="chrome"). State (demo user, contract ids, upload timings) is kept in
experiments/ui/state.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
SAMPLES = ROOT / "docs" / "sample_inputs"
STATE = ROOT / "experiments" / "ui" / "state.json"
BASE = "http://localhost:5106"
EMAIL, PASSWORD = "neha.legal@example.com", "clauseguard-demo-1"

SHOTS.mkdir(parents=True, exist_ok=True)
STATE.parent.mkdir(parents=True, exist_ok=True)
state = json.loads(STATE.read_text()) if STATE.exists() else {"uploads": {}}


def save_state():
    STATE.write_text(json.dumps(state, indent=2))


def shot(page, name, full=False, delay=0.8):
    time.sleep(delay)
    page.screenshot(path=str(SHOTS / name), full_page=full)
    print("captured", name, flush=True)


def new_page(p):
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--disable-gpu", "--use-gl=swiftshader", "--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(30000)
    return browser, page


def login(page):
    page.goto(f"{BASE}/login")
    page.get_by_label("Email").fill(EMAIL)
    page.locator("input[type=password]").fill(PASSWORD)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/app**")


def step_public(p):
    browser, page = new_page(p)
    page.goto(BASE)
    page.wait_for_timeout(7500)  # landing counters animate
    shot(page, "01_landing.png", delay=0.5)
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(1800)
    shot(page, "02_landing_how_it_works.png", delay=0.5)
    page.goto(f"{BASE}/register")
    page.get_by_label("Email").fill(EMAIL)
    page.locator("input[type=password]").fill(PASSWORD)
    shot(page, "03_register.png")
    page.goto(f"{BASE}/login")
    shot(page, "04_login.png")
    browser.close()


def register_or_login(page):
    page.goto(f"{BASE}/register")
    page.get_by_label("Email").fill(EMAIL)
    page.locator("input[type=password]").fill(PASSWORD)
    page.get_by_role("button", name="Sign up").click()
    try:
        page.wait_for_url("**/app/upload", timeout=8000)
    except Exception:  # noqa: BLE001 - already registered on an earlier run
        login(page)


def do_upload(page, path: Path, label: str, timeout_s=300):
    page.goto(f"{BASE}/app/upload")
    page.wait_for_timeout(1200)
    page.locator("input[type=file]").set_input_files(str(path))
    page.wait_for_timeout(600)
    if label == "freelance":
        shot(page, "06_upload_file_selected.png")
    t0 = time.time()
    page.get_by_role("button", name="Analyse contract").click()
    if label == "freelance":
        page.wait_for_timeout(2500)
        shot(page, "07_upload_analysing.png", delay=0.1)
    page.wait_for_url("**/app/contracts/*", timeout=timeout_s * 1000)
    secs = round(time.time() - t0, 1)
    cid = int(page.url.rstrip("/").split("/")[-1])
    state["uploads"][label] = {"contract_id": cid, "seconds": secs, "file": path.name}
    save_state()
    print(f"{label}: contract {cid} in {secs}s", flush=True)
    page.wait_for_timeout(2500)
    return cid


def step_freelance(p):
    browser, page = new_page(p)
    register_or_login(page)
    page.goto(f"{BASE}/app/upload")
    page.wait_for_timeout(1200)
    shot(page, "05_upload_empty.png")
    cid = do_upload(page, SAMPLES / "freelance_services_agreement.docx", "freelance")
    shot(page, "08_report_freelance_top.png", delay=1.5)
    page.mouse.wheel(0, 800)
    page.wait_for_timeout(1200)
    shot(page, "09_report_freelance_clauses.png", delay=0.5)
    page.mouse.wheel(0, 900)
    shot(page, "10_report_freelance_table.png", delay=1.0)
    browser.close()


def step_detail(p):
    cid = state["uploads"]["freelance"]["contract_id"]
    browser, page = new_page(p)
    login(page)
    page.goto(f"{BASE}/app/contracts/{cid}")
    page.wait_for_timeout(2500)
    page.mouse.wheel(0, 1000)
    shot(page, "10_report_freelance_table.png", delay=1.0)
    links = page.locator("a[href*='/clauses/']")
    n = links.count()
    print("clause links:", n)
    # open the first flagged clause (the table lists flagged ones with a risk badge); use the 2nd clause (termination)
    hrefs = [links.nth(i).get_attribute("href") for i in range(n)]
    state["freelance_clause_hrefs"] = hrefs
    save_state()
    for idx, name in ((1, "11_clause_detail_termination.png"), (3, "12_clause_detail_penalty.png"), (4, "13_clause_detail_noncompete.png")):
        if idx < len(hrefs):
            page.goto(BASE + hrefs[idx])
            page.wait_for_timeout(2500)
            shot(page, name)
    page.goto(f"{BASE}/app/contracts/{cid}/graph")
    page.wait_for_timeout(4000)
    shot(page, "14_clause_graph.png", delay=1.0)
    browser.close()


def step_others(p):
    browser, page = new_page(p)
    login(page)
    do_upload(page, SAMPLES / "balanced_consulting_agreement.docx", "balanced")
    shot(page, "15_report_balanced.png", delay=1.5)
    do_upload(page, SAMPLES / "supply_agreement_cuad.pdf", "cuad_pdf")
    shot(page, "16_report_cuad_pdf.png", delay=1.5)
    page.mouse.wheel(0, 900)
    shot(page, "17_report_cuad_pdf_table.png", delay=1.0)
    page.goto(f"{BASE}/app/upload")
    page.wait_for_timeout(1200)
    bad = ROOT / "docs" / "sample_inputs" / "not_a_contract.txt"
    bad.write_text("This is plain text, not a PDF or DOCX contract.")
    page.locator("input[type=file]").set_input_files(str(bad))
    page.wait_for_timeout(800)
    shot(page, "18_upload_wrong_type.png")
    bad.unlink()
    page.goto(f"{BASE}/app")
    page.wait_for_timeout(2500)
    shot(page, "19_contracts_list.png")
    step_eval_page(page)
    browser.close()


def step_eval_page(page):
    page.goto(f"{BASE}/evaluation")
    page.wait_for_timeout(9000)  # the stat cards count up
    shot(page, "20_evaluation.png", delay=1.0)
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(3000)
    shot(page, "21_evaluation_lower.png", delay=1.0)


def step_eval(p):
    browser, page = new_page(p)
    login(page)
    step_eval_page(page)
    browser.close()


if __name__ == "__main__":
    steps = {"public": step_public, "freelance": step_freelance, "detail": step_detail, "others": step_others, "eval": step_eval}
    with sync_playwright() as p:
        for name in sys.argv[1:] or ["public"]:
            steps[name](p)
