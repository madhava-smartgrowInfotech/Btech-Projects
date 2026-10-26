"""
Capture the application screenshots used by the documents (1440x900) with real data in the app.

Prerequisites (see docs/03_HOW_TO_RUN.md): API on :8102 and the React app on :5102, both started against an
EMPTY database that was seeded with scripts/seed_demo.py, e.g.

    set DATABASE_URL=sqlite:///C:/temp/docs_screens.db
    venv\\Scripts\\python scripts\\seed_demo.py
    venv\\Scripts\\python -m uvicorn backend.api:app --port 8102        (and: cd frontend && npm run dev)

    venv\\Scripts\\python scripts\\docs_personas.py --lfw <dir> --out personas.json
    python scripts\\capture_screenshots.py --personas personas.json

Face photographs: the product holds no student photos, so each demo student is given real photographs of one
identity from the public LFW benchmark (see docs_personas.py). The browser is driven through the real UI;
the "camera" is replaced by the app's own "Upload photo" tab because no camera is attached.
Needs: pip install playwright httpx pillow numpy (system Python is fine).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)
API, UI = "http://127.0.0.1:8102", "http://localhost:5102"
INSIDE = (17.38505, 78.48675)     # ~7 m from the session centre
CENTRE = (17.3850, 78.4867)
OUTSIDE = (17.3900, 78.4867)      # ~550 m away

ap = argparse.ArgumentParser()
ap.add_argument("--personas", required=True)
ap.add_argument("--only", default="", help="comma list of phases: seed,faculty,students,tour,screens,misc")
args = ap.parse_args()
PHASES = set(args.only.split(",")) if args.only else {"seed", "faculty", "students", "tour", "screens", "misc"}
P = {p["name"]: p for p in json.loads(Path(args.personas).read_text())}
TMP = Path(tempfile.mkdtemp(prefix="am_docs_"))

# roll -> (display name, LFW persona)
STUDENTS = {
    "23K91A6706": ("A. Greeshma", "Venus_Williams"),
    "23K91A6740": ("B. Vinay", "Arnold_Schwarzenegger"),
    "23K91A6757": ("G. Sriram", "Andre_Agassi"),
    "24K95A6704": ("B. Sai Kumar", "Tiger_Woods"),
}
PROXY = ("23K91A6799", "Proxy Demo")      # enrolled with the same face as 23K91A6706 -> duplicate-face demo
VISITOR = ("24K95A6710", "Visitor Demo", "Jennifer_Lopez")   # roll number outside the allowed list
MIRRORED = True
CH_TEXT: dict[str, str] = {}


def shot(page, name: str, full: bool = True, wait: int = 900):
    """Viewport screenshot; for tall pages the viewport is stretched to the document height first, so sticky
    sidebars/headers stay at the top instead of floating mid-page as they do in a stitched full-page capture."""
    page.wait_for_timeout(wait)
    path = SHOTS / f"{name}.png"
    if full:
        page.evaluate("window.scrollTo(0, 0)")
        h = page.evaluate("Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)")
        page.set_viewport_size({"width": 1440, "height": max(900, int(h))})
        page.wait_for_timeout(700)
        page.screenshot(path=str(path))
        page.set_viewport_size({"width": 1440, "height": 900})
    else:
        page.screenshot(path=str(path))
    print("  shot", path.name, flush=True)


def rotated(src: str, angle: float) -> str:
    """Rotate a still photo (edge-replicated border), as scripts/smoke_test.py does with OpenCV."""
    img = Image.open(src).convert("RGB")
    w, h = img.size
    pad = max(w, h)
    arr = np.pad(np.asarray(img), ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    big = Image.fromarray(arr).rotate(angle, resample=Image.BICUBIC)
    out = big.crop((pad, pad, pad + w, pad + h))
    p = TMP / f"rot_{abs(hash((src, angle)))}.jpg"
    out.save(p, quality=95)
    return str(p)


def challenge_photos(persona: dict, code: str, mode: str = "genuine") -> tuple[str, str]:
    """(photo 1, photo 2) for a challenge. mode: genuine | static."""
    n = persona["neutral"]
    if mode == "static":
        return n, n
    if code in persona["challenge"]:
        return n, persona["challenge"][code]
    angle = {"TILT_LEFT": -20, "TILT_RIGHT": 20}.get(code)
    if angle is None:
        raise KeyError(code)
    return n, rotated(n, -angle if MIRRORED else angle)


# --------------------------------------------------------------------------- #
# API client (seeding)
# --------------------------------------------------------------------------- #
class Api:
    def __init__(self, device: str):
        self.c = httpx.Client(base_url=API, timeout=180, headers={"X-Device-Id": device, "User-Agent": f"seed/{device}"})
        self.tok = None

    def _h(self):
        return {"Authorization": f"Bearer {self.tok}"} if self.tok else {}

    def get(self, p, **k):
        return self.c.get(p, headers=self._h(), **k)

    def post(self, p, **k):
        return self.c.post(p, headers=self._h(), **k)

    def login(self, u, pw, role=None):
        r = self.post("/api/auth/login", json={"username": u, "password": pw, "role": role})
        r.raise_for_status()
        self.tok = r.json()["token"]


def fileparts(**paths):
    return {k: (Path(v).name, Path(v).read_bytes(), "image/jpeg") for k, v in paths.items()}


def api_checkin(roll, persona, token, loc=INSIDE, mode="genuine", face_of=None):
    """One student's wizard through the HTTP API. Returns (stage, reason)."""
    c = Api(f"seed-{roll}")
    c.login(roll, "student123", "student")
    c.post(f"/api/checkin/{token}/reset")
    r = c.post(f"/api/checkin/{token}/start").json()
    if not r["ok"]:
        return "eligibility", r["reason"]
    r = c.post(f"/api/checkin/{token}/location", json={"lat": loc[0], "lon": loc[1], "accuracy": 12}).json()
    if not r["inside"]:
        return "location", r["reason"]
    pers = P[face_of or persona]
    for _ in range(6):
        code = r["state"]["challenge"]
        try:
            a, b = challenge_photos(pers, code, mode)
        except KeyError:
            a = b = pers["neutral"]
        r = c.post(f"/api/checkin/{token}/liveness", files=fileparts(neutral=a, challenge=b)).json()
        if r["passed"] or mode == "static":
            break
    if not r["passed"]:
        return "liveness", r["reason"]
    r = c.post(f"/api/checkin/{token}/face").json()
    return ("success" if r["passed"] else "face"), r["reason"]


def seed():
    print("== seed", flush=True)
    fac = Api("seed-faculty")
    fac.login("faculty@college.edu", "faculty123", "faculty")
    # reference faces
    studs = {s["roll_number"]: s for s in fac.get("/api/students").json()}
    for roll, (_, per) in STUDENTS.items():
        r = fac.post(f"/api/students/{studs[roll]['id']}/enroll", files={"face": ("f.jpg", Path(P[per]["enroll"]).read_bytes(), "image/jpeg")})
        assert r.status_code == 200, r.text
    reg = Api("seed-anon")
    for roll, name, per in [(PROXY[0], PROXY[1], "Venus_Williams"), (VISITOR[0], VISITOR[1], VISITOR[2])]:
        r = reg.post("/api/auth/register", data={"role": "student", "full_name": name, "roll_number": roll, "password": "student123"},
                     files={"face": ("f.jpg", Path(P[per]["enroll"]).read_bytes(), "image/jpeg")})
        assert r.status_code == 200, r.text
    # an earlier, closed session with a realistic mix of passes and blocks
    now = datetime.fromisoformat(reg.get("/api/config").json()["now_local"])
    s1 = fac.post("/api/sessions", json={
        "course_code": "CS601", "course_name": "Machine Learning", "section": "CSDS-A",
        "start_local": (now - timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M"), "duration_min": 120,
        "latitude": CENTRE[0], "longitude": CENTRE[1], "radius_m": 60, "allowed_rolls": "23K91A67*,24K95A6704"})
    s1 = s1.json()
    t = s1["token"]
    plan = [
        ("23K91A6706", dict()),
        ("23K91A6740", dict(loc=OUTSIDE)), ("23K91A6740", dict()),
        ("23K91A6757", dict(mode="static")), ("23K91A6757", dict()),
        ("24K95A6704", dict()),
        (PROXY[0], dict(face_of="Venus_Williams")),
        (VISITOR[0], dict()),
    ]
    for roll, kw in plan:
        per = STUDENTS.get(roll, (None, "Andre_Agassi"))[1] if roll in STUDENTS else ("Venus_Williams" if roll == PROXY[0] else VISITOR[2])
        print("  ", roll, kw, api_checkin(roll, per, t, **kw), flush=True)
    fac.post(f"/api/sessions/{s1['id']}/close")
    # let the browser device bind fresh for the UI flows
    for s in fac.get("/api/students").json():
        fac.post(f"/api/students/{s['id']}/reset-devices")
    cfg = reg.get("/api/config").json()
    for ch in cfg["challenges"]:
        CH_TEXT[ch["text"]] = ch["code"]


# --------------------------------------------------------------------------- #
# UI helpers
# --------------------------------------------------------------------------- #
def new_ctx(browser, lat_lon=INSIDE):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1,
                              geolocation={"latitude": lat_lon[0], "longitude": lat_lon[1], "accuracy": 12},
                              permissions=["geolocation"], locale="en-IN")
    ctx.set_default_timeout(60000)
    return ctx


def ui_login(page, username, password, role):
    page.goto(f"{UI}/login?role={role}")
    page.get_by_label(re.compile("Roll number or username|Username / email")).fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in").click()


def challenge_code(page, cfg_texts) -> str:
    page.wait_for_selector("text=YOUR RANDOM CHALLENGE")
    txt = page.locator(".challenge-card .display-sm").inner_text().strip()
    return cfg_texts[txt]


def anon(src: str, label: str) -> str:
    """Copy a photo under a neutral file name so screenshots never show the LFW identity."""
    d = TMP / "anon"
    d.mkdir(exist_ok=True)
    dst = d / label
    dst.write_bytes(Path(src).read_bytes())
    return str(dst)


def upload_two(page, a, b):
    a, b = anon(a, "photo1_neutral.jpg"), anon(b, "photo2_challenge.jpg")
    tabs = page.get_by_role("tab", name="Upload photo")
    for i in range(tabs.count()):
        tabs.nth(i).click()
    page.wait_for_timeout(300)
    inputs = page.locator("input[type=file]")
    inputs.nth(0).set_input_files(a)
    page.wait_for_timeout(2500)   # neutral-frame check
    page.locator("input[type=file]").last.set_input_files(b)
    page.wait_for_timeout(600)


def wait_text(page, pattern, timeout=90000):
    page.get_by_text(re.compile(pattern)).first.wait_for(timeout=timeout)


def student_location(page, name=None, outside=False, ctx=None):
    page.wait_for_selector("text=Step 2")
    if name:
        shot(page, name)
    page.get_by_role("button", name="Get my location").click()
    page.wait_for_selector("text=Location:")
    page.wait_for_timeout(500)


# --------------------------------------------------------------------------- #
def run_ui(cfg_texts):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # ---------------- public pages ----------------
        if "tour" in PHASES:
            print("== public pages", flush=True)
            ctx = new_ctx(browser)
            page = ctx.new_page()
            page.goto(UI + "/")
            page.wait_for_timeout(7500)          # count-up animations
            shot(page, "01_landing", full=False, wait=200)
            page.mouse.wheel(0, 900)
            shot(page, "02_landing_how_it_works", full=False, wait=1500)
            page.goto(UI + "/about")
            shot(page, "03_about", wait=2000)
            page.goto(UI + "/login?role=faculty")
            shot(page, "04_login_faculty", full=False, wait=1500)
            page.goto(UI + "/login?role=student")
            shot(page, "05_login_student", full=False, wait=1200)
            page.goto(UI + "/register")
            page.wait_for_timeout(1500)
            try:
                page.get_by_label("Full name").fill("A. Greeshma")
                page.get_by_label(re.compile("Roll number")).fill("23K91A6706")
                page.get_by_label(re.compile("Password")).fill("student123")
                tabs = page.get_by_role("tab", name="Upload photo")
                if tabs.count():
                    tabs.first.click()
                    page.locator("input[type=file]").first.set_input_files(anon(P["Venus_Williams"]["enroll"], "reference_face.jpg"))
            except Exception as exc:  # noqa: BLE001
                print("  register fill skipped:", exc)
            shot(page, "06_register_student", wait=1200)
            page.goto(UI + "/checkin")
            shot(page, "07_checkin_portal", full=False, wait=1500)
            ctx.close()

        # ---------------- faculty: create the live session ----------------
        fac_ctx = new_ctx(browser, CENTRE)
        fac = fac_ctx.new_page()
        token = None
        f0 = Api("seed-faculty")
        f0.login("faculty@college.edu", "faculty123", "faculty")
        already = [x for x in f0.get("/api/sessions").json() if x["course_code"] == "CS604"]
        if "faculty" in PHASES and not already:
            print("== faculty create session", flush=True)
            ui_login(fac, "faculty@college.edu", "faculty123", "faculty")
            fac.wait_for_url(re.compile("/app"))
            fac.goto(UI + "/app/sessions/new")
            fac.get_by_label("Course code").fill("CS604")
            fac.get_by_label("Course name").fill("Data Visualization")
            fac.get_by_label("Section").fill("CSDS-A")
            fac.get_by_label("Duration (minutes)").fill("60")
            fac.locator("input.input[value='*']").fill("23K91A6706,23K91A6740,23K91A6757,24K95A6704,23K91A6799")
            fac.get_by_role("button", name="Get my location").click()
            fac.wait_for_selector("text=Location:")
            fac.wait_for_timeout(2500)
            shot(fac, "09_create_session", wait=1500)
            fac.get_by_role("button", name="Create session").click()
            fac.wait_for_selector("text=Share this link with students")
            fac.wait_for_timeout(2500)
            shot(fac, "10_session_share_qr", wait=800)
            token = None
        if token is None:
            token = [x for x in f0.get("/api/sessions").json() if x["course_code"] == "CS604"][0]["token"]
        if already:
            ui_login(fac, "faculty@college.edu", "faculty123", "faculty")
            fac.wait_for_url(re.compile("/app"))
        print("  live session token", token, flush=True)

        # ---------------- students ----------------
        if "students" in PHASES:
            print("== student flows", flush=True)
            url = f"{UI}/checkin/{token}"
            for st in f0.get("/api/students").json():      # fresh browsers bind fresh devices
                f0.post(f"/api/students/{st['id']}/reset-devices")

            def flow_student(roll, pw="student123"):
                ctx = new_ctx(browser)
                page = ctx.new_page()
                page.goto(url)
                return ctx, page

            # --- A: the full happy path, every step captured
            ctx, pg = flow_student("23K91A6706")
            pg.wait_for_timeout(1500)
            shot(pg, "20_checkin_signin", wait=1200)
            pg.get_by_label(re.compile("Roll number or username")).fill("23K91A6706")
            pg.get_by_label("Password").fill("student123")
            pg.get_by_role("button", name="Sign in").click()
            pg.wait_for_selector("text=Step 2")
            pg.wait_for_timeout(2500)
            shot(pg, "21_checkin_location_step", wait=800)
            pg.get_by_role("button", name="Get my location").click()
            pg.wait_for_selector("text=Location:")
            pg.wait_for_timeout(2500)
            pg.get_by_role("button", name="Verify my location").click()
            pg.wait_for_selector("text=Step 3")
            pg.wait_for_timeout(1500)
            code = challenge_code(pg, cfg_texts)
            shot(pg, "22_checkin_challenge", wait=500)
            a, b = challenge_photos(P["Venus_Williams"], code)
            upload_two(pg, a, b)
            shot(pg, "23_checkin_photos_ready", wait=800)
            pg.get_by_role("button", name="Verify challenge").click()
            wait_text(pg, "Marked\\.|Challenge failed")
            pg.wait_for_timeout(3500)
            shot(pg, "24_checkin_marked", wait=1500)
            ctx.close()

            # --- B: outside geo-fence, static-photo spoof (x3 -> locked), then genuine
            ctx, pg = flow_student("23K91A6740")
            pg.get_by_label(re.compile("Roll number or username")).fill("23K91A6740")
            pg.get_by_label("Password").fill("student123")
            pg.get_by_role("button", name="Sign in").click()
            pg.wait_for_selector("text=Step 2")
            ctx.set_geolocation({"latitude": OUTSIDE[0], "longitude": OUTSIDE[1], "accuracy": 12})
            pg.get_by_role("button", name="Get my location").click()
            pg.wait_for_selector("text=Location:")
            pg.wait_for_timeout(2000)
            pg.get_by_role("button", name="Verify my location").click()
            pg.wait_for_selector("text=Outside geo-fence")
            pg.wait_for_timeout(2500)
            shot(pg, "25_checkin_outside_geofence", wait=800)
            ctx.set_geolocation({"latitude": INSIDE[0], "longitude": INSIDE[1], "accuracy": 12})
            pg.get_by_role("button", name="Get my location").click()
            pg.wait_for_timeout(2500)
            pg.get_by_role("button", name="Verify my location").click()
            pg.wait_for_selector("text=Step 3")
            pg.wait_for_timeout(1200)
            for attempt in range(3):
                code = challenge_code(pg, cfg_texts)
                a, b = challenge_photos(P["Arnold_Schwarzenegger"], code, "static")
                upload_two(pg, a, b)
                pg.get_by_role("button", name="Verify challenge").click()
                if attempt < 2:
                    pg.wait_for_selector("text=Challenge failed")
                    pg.wait_for_timeout(1200)
                    if attempt == 0:
                        shot(pg, "26_checkin_static_photo_rejected", wait=500)
                else:
                    pg.wait_for_selector("text=Check-in locked")
                    pg.wait_for_timeout(1200)
                    shot(pg, "27_checkin_locked", wait=500)
            pg.get_by_role("button", name="Start over").click()
            pg.wait_for_selector("text=Step 2")
            pg.get_by_role("button", name="Get my location").click()
            pg.wait_for_timeout(2500)
            pg.get_by_role("button", name="Verify my location").click()
            pg.wait_for_selector("text=Step 3")
            pg.wait_for_timeout(1200)
            for _ in range(3):
                code = challenge_code(pg, cfg_texts)
                a, b = challenge_photos(P["Arnold_Schwarzenegger"], code)
                upload_two(pg, a, b)
                pg.get_by_role("button", name="Verify challenge").click()
                wait_text(pg, "Marked\\.|Challenge failed")
                if pg.get_by_text("Marked.").count():
                    break
                pg.wait_for_timeout(1200)
            ctx.close()

            # --- C: somebody else's face for this roll number -> identity mismatch
            ctx, pg = flow_student("23K91A6757")
            pg.get_by_label(re.compile("Roll number or username")).fill("23K91A6757")
            pg.get_by_label("Password").fill("student123")
            pg.get_by_role("button", name="Sign in").click()
            pg.wait_for_selector("text=Step 2")
            pg.get_by_role("button", name="Get my location").click()
            pg.wait_for_timeout(2500)
            pg.get_by_role("button", name="Verify my location").click()
            pg.wait_for_selector("text=Step 3")
            pg.wait_for_timeout(1200)
            code = challenge_code(pg, cfg_texts)
            a, b = challenge_photos(P["Venus_Williams"], code)     # photos of a different person
            upload_two(pg, a, b)
            pg.get_by_role("button", name="Verify challenge").click()
            wait_text(pg, "does not match|Challenge failed")
            pg.wait_for_timeout(2000)
            shot(pg, "28_checkin_identity_mismatch", wait=800)
            ctx.close()

            # --- Proxy: enrolled with A's face; presents A's face -> duplicate-face block
            ctx, pg = flow_student(PROXY[0])
            pg.get_by_label(re.compile("Roll number or username")).fill(PROXY[0])
            pg.get_by_label("Password").fill("student123")
            pg.get_by_role("button", name="Sign in").click()
            pg.wait_for_selector("text=Step 2")
            pg.get_by_role("button", name="Get my location").click()
            pg.wait_for_timeout(2500)
            pg.get_by_role("button", name="Verify my location").click()
            pg.wait_for_selector("text=Step 3")
            pg.wait_for_timeout(1200)
            code = challenge_code(pg, cfg_texts)
            a, b = challenge_photos(P["Venus_Williams"], code)
            upload_two(pg, a, b)
            pg.get_by_role("button", name="Verify challenge").click()
            wait_text(pg, "already marked attendance|does not match|Challenge failed")
            pg.wait_for_timeout(2500)
            shot(pg, "29_checkin_duplicate_face_blocked", wait=800)
            ctx.close()

            # --- Visitor: roll number not on the session's list -> eligibility block
            ctx, pg = flow_student(VISITOR[0])
            pg.get_by_label(re.compile("Roll number or username")).fill(VISITOR[0])
            pg.get_by_label("Password").fill("student123")
            pg.get_by_role("button", name="Sign in").click()
            pg.wait_for_selector("text=Step 1")
            pg.wait_for_timeout(2500)
            shot(pg, "31_checkin_roll_not_allowed", wait=500)
            ctx.close()

            # --- D: fourth genuine student
            ctx, pg = flow_student("24K95A6704")
            pg.get_by_label(re.compile("Roll number or username")).fill("24K95A6704")
            pg.get_by_label("Password").fill("student123")
            pg.get_by_role("button", name="Sign in").click()
            pg.wait_for_selector("text=Step 2")
            pg.get_by_role("button", name="Get my location").click()
            pg.wait_for_timeout(2500)
            pg.get_by_role("button", name="Verify my location").click()
            pg.wait_for_selector("text=Step 3")
            pg.wait_for_timeout(1200)
            for _ in range(3):
                code = challenge_code(pg, cfg_texts)
                a, b = challenge_photos(P["Tiger_Woods"], code)
                upload_two(pg, a, b)
                pg.get_by_role("button", name="Verify challenge").click()
                wait_text(pg, "Marked\\.|Challenge failed")
                if pg.get_by_text("Marked.").count():
                    break
                pg.wait_for_timeout(1200)
            ctx.close()

        # ---------------- faculty screens ----------------
        if "screens" in PHASES:
            print("== faculty screens", flush=True)
            ui_login(fac, "faculty@college.edu", "faculty123", "faculty") if "faculty" not in PHASES and "students" not in PHASES else None
            fac.goto(UI + "/app")
            fac.wait_for_timeout(5500)
            shot(fac, "11_faculty_dashboard", wait=500)
            fac.goto(UI + "/app/sessions")
            shot(fac, "12_sessions_list", wait=2500)
            ids = sorted(x["id"] for x in f0.get("/api/sessions").json())
            print("  session ids", ids)
            live_id = max(ids)
            fac.goto(f"{UI}/app/sessions/{live_id}")
            fac.wait_for_timeout(3500)
            shot(fac, "13_session_records", wait=500)
            for tab, nm in (("Map", "14_session_map"), ("Verification log", "15_session_log"), ("Analytics", "16_session_analytics")):
                fac.get_by_role("tab", name=re.compile(tab)).click()
                shot(fac, nm, wait=3000)
            fac.goto(f"{UI}/app/sessions/{min(ids)}")
            fac.wait_for_timeout(3000)
            shot(fac, "17_session_closed_records", wait=500)
            fac.get_by_role("tab", name=re.compile("Verification log")).click()
            shot(fac, "18_session_closed_log", wait=1500)
            fac.goto(UI + "/app/students")
            shot(fac, "19_students", wait=2500)
            fac.get_by_role("button", name=re.compile("Manage")).first.click()
            shot(fac, "19b_students_manage", wait=1500)
        fac_ctx.close()

        # ---------------- misc: API docs ----------------
        if "misc" in PHASES:
            ctx = new_ctx(browser)
            page = ctx.new_page()
            page.goto(API + "/docs")
            shot(page, "30_api_docs", wait=3000)
            ctx.close()
        browser.close()


def main():
    cfg = httpx.get(API + "/api/config").json()
    texts = {c["text"]: c["code"] for c in cfg["challenges"]}
    global MIRRORED
    MIRRORED = cfg["camera_mirrored"]
    if "seed" in PHASES:
        seed()
    run_ui(texts)


if __name__ == "__main__":
    main()
