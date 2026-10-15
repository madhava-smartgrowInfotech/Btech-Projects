"""Capture real screenshots of the running SeatWise app (1440x900) into docs/screenshots/.

Run with SeatWise started (run.bat) and the sample data loaded (scripts/demo_scenario.py):

    venv\\Scripts\\python scripts\\capture_screenshots.py

Needs Playwright with a Chrome channel:  pip install playwright
Standard flows only; nothing here changes data except marking a few attendance entries.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
WEB = "http://localhost:5113"
API = "http://127.0.0.1:8113/api"
ADMIN = ("admin@seatwise.local", "SeatWise@2026")
INVIG = ("invigilator@seatwise.local", "SeatWise@2026")
SAMPLE = ROOT / "data" / "sample" / "seatwise_sample_workbook.xlsx"


def api(path: str, token: str | None = None, method: str = "GET", body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read())


def shot(page: Page, name: str, full: bool = False, wait: int = 900) -> None:
    page.wait_for_timeout(wait)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=full)
    print("saved", path.name)


def login(page: Page, who: tuple[str, str]) -> None:
    page.goto(f"{WEB}/login")
    page.fill("#email", who[0])
    page.fill("#password", who[1])
    page.click("button[type=submit]")
    page.wait_for_url("**/app**", timeout=20000)
    page.wait_for_timeout(1200)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    token = api("/auth/login", method="POST", body={"email": ADMIN[0], "password": ADMIN[1]})["access_token"]
    plans = [p for p in api("/plans", token) if p["status"] == "published"]
    if not plans:
        print("No published plan - run scripts/demo_scenario.py first")
        return 1
    plan = sorted(plans, key=lambda p: p["id"])[0]
    plan_detail = api(f"/plans/{plan['id']}", token)
    hall = max(plan_detail["halls"], key=lambda h: h["placed"])
    sessions = api("/sessions", token)
    session_id = plan["session_id"] if "session_id" in plan else sessions[0]["id"]
    print("plan", plan["id"], "hall", hall["hall_id"], hall["code"], "session", session_id)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()

        # ---- public pages
        page.goto(WEB)
        shot(page, "01_landing", wait=7000)  # let the count-up figures finish
        page.goto(f"{WEB}/login")
        shot(page, "02_login")
        page.goto(f"{WEB}/register")
        shot(page, "03_register")

        # ---- administrator
        login(page, ADMIN)
        shot(page, "04_dashboard", wait=2200)

        page.goto(f"{WEB}/app/import")
        shot(page, "05_import_empty")
        page.set_input_files("input[type=file]", str(SAMPLE))
        page.wait_for_timeout(3500)
        shot(page, "06_import_validated")

        page.goto(f"{WEB}/app/data")
        shot(page, "07_data", wait=1800)

        page.goto(f"{WEB}/app/sessions")
        shot(page, "08_sittings", wait=1800)

        page.goto(f"{WEB}/app/sessions/{session_id}")
        shot(page, "09_plan", wait=2500)
        shot(page, "09b_plan_full", full=True, wait=500)

        page.goto(f"{WEB}/app/plans/{plan['id']}/halls/{hall['hall_id']}")
        shot(page, "10_seatmap", wait=2500)

        page.goto(f"{WEB}/app/exports")
        shot(page, "12_exports", wait=1800)
        page.goto(f"{WEB}/app/analytics")
        shot(page, "13_analytics_plans", wait=2500)
        page.goto(f"{WEB}/app/audit")
        shot(page, "15_audit", wait=1800)
        page.goto(f"{WEB}/app/team")
        shot(page, "16_team", wait=1500)
        page.goto(f"{WEB}/app/settings")
        shot(page, "17_settings", wait=1500)

        # ---- seat map: pick up a candidate, see green/red targets, try an illegal move
        page.goto(f"{WEB}/app/plans/{plan['id']}/halls/{hall['hall_id']}")
        page.wait_for_timeout(2000)
        hall_map = api(f"/plans/{plan['id']}/halls/{hall['hall_id']}", token)
        first = next(s for s in hall_map["seats"] if s.get("candidate"))
        seat_label = first.get("seat") or first.get("label")
        page.click(f'[aria-label^="{seat_label}:"]')
        page.wait_for_timeout(1800)
        shot(page, "11_seatmap_targets", wait=500)
        options = api(f"/plans/{plan['id']}/halls/{hall['hall_id']}/swap-check?seat={seat_label}", token)
        bad = next((t for t in options["targets"] if t["occupied"] and not t["ok"]), None)
        if bad:
            page.click(f'[aria-label^="{bad["seat"]}:"]')
            shot(page, "11b_swap_refused", wait=1200)

        # ---- verify
        page.goto(f"{WEB}/app/sessions/{session_id}")
        page.wait_for_timeout(1800)
        page.get_by_role("button", name="Verify").first.click()
        shot(page, "09c_verify", wait=3500)

        # ---- engine performance tab
        page.goto(f"{WEB}/app/analytics")
        page.wait_for_timeout(1500)
        page.get_by_role("tab", name="Engine performance").click()
        shot(page, "14_analytics_engine", wait=2500)
        shot(page, "14b_analytics_engine_full", full=True, wait=300)

        # ---- dark theme
        page.evaluate("localStorage.setItem('seatwise.theme','dark')")
        page.goto(f"{WEB}/app/sessions/{session_id}")
        shot(page, "19_plan_dark", wait=2500)
        page.evaluate("localStorage.setItem('seatwise.theme','light')")

        # ---- public seat lookup
        roll = first["candidate"]["roll_no"]
        page.goto(f"{WEB}/lookup")
        shot(page, "18a_lookup", wait=1200)
        page.goto(f"{WEB}/lookup/{roll}")
        shot(page, "18_lookup_result", wait=2500)

        # ---- invigilator attendance
        inv_token = api("/auth/login", method="POST", body={"email": INVIG[0], "password": INVIG[1]})["access_token"]
        mine = api("/attendance/assignments", inv_token)
        target = mine[0] if mine else None
        if target:
            pid, hid = target["plan_id"], target["hall"]["id"]
            hall_view = api(f"/plans/{pid}/halls/{hid}", inv_token)
            people = [s for s in hall_view["seats"] if s.get("candidate")]
            for i, seat in enumerate(people[:60]):
                status = "absent" if i % 17 == 16 else "present"
                api(f"/plans/{pid}/halls/{hid}/attendance/{seat['candidate']['id']}", inv_token, "PUT", {"status": status})
            page.evaluate("localStorage.clear()")
            login(page, INVIG)
            page.goto(f"{WEB}/app/attendance")
            shot(page, "20_attendance_halls", wait=1800)
            page.goto(f"{WEB}/app/attendance/{pid}/{hid}")
            shot(page, "21_attendance_list", wait=2200)
            page.get_by_role("button", name="Seat map view").click()
            shot(page, "22_attendance_map", wait=1500)

        # ---- dashboard again, now that attendance has been marked
        page.evaluate("localStorage.clear()")
        login(page, ADMIN)
        shot(page, "04_dashboard", wait=2800)
        page.goto(f"{WEB}/app/analytics")
        shot(page, "13_analytics_plans", wait=2800)

        browser.close()
    render_pdfs()
    return 0


def render_pdfs() -> None:
    """Render the first page of each generated PDF (charts, sheets, slips) as a screen image."""
    import pymupdf

    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not src or not src.exists():
        return
    for name, out in [("seating-charts.pdf", "23_pdf_seating_chart"), ("invigilator-sheets.pdf", "24_pdf_invigilator_sheet"),
                      ("qr-slips.pdf", "25_pdf_qr_slips")]:
        pdf = src / name
        if pdf.exists():
            doc = pymupdf.open(pdf)
            doc[0].get_pixmap(dpi=110).save(str(OUT / f"{out}.png"))
            print("saved", out, "pages:", len(doc))


if __name__ == "__main__":
    sys.exit(main())
