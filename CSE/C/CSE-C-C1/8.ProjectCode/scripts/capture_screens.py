"""Walk every AegisBallot screen with real data and save 1440x900 PNGs to docs/screenshots/.

Needs both servers running (run.bat): API on BACKEND_PORT (8401) and the web app on FRONTEND_PORT (5401).
    pip install playwright        (then once per machine: playwright install chromium)
    python scripts/capture_screens.py

It also doubles as the browser console check: any console error, page error, failed request or 4xx/5xx on
an asset/API call (other than the expected ones listed in EXPECTED) makes the script exit with code 1.
Voting uses a dedicated "Screenshot Demo Election" so the seeded elections are left alone.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"


def read_env():
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = read_env()
API = f"http://127.0.0.1:{ENV.get('BACKEND_PORT', '8401')}"
WEB = f"http://localhost:{ENV.get('FRONTEND_PORT', '5401')}"
DEMO_TITLE = "Screenshot Demo Election"
ADMIN = ("admin", "Admin@123")
AUDITOR = ("auditor", "Audit@123")
problems = []


def watch(page, label):
    page.on("console", lambda m: m.type == "error" and problems.append(f"[{label}] console: {m.text}"))
    page.on("pageerror", lambda e: problems.append(f"[{label}] pageerror: {e}"))
    page.on("requestfailed", lambda r: problems.append(f"[{label}] request failed: {r.url} {r.failure}"))
    page.on(
        "response",
        lambda r: r.status >= 400 and problems.append(f"[{label}] HTTP {r.status}: {r.url}"),
    )


counter = [0]


def shot(page, name, wait=1800):
    """Save the viewport as docs/screenshots/<nn>_<name>.png (numbers follow the walk order)."""
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(wait)
    counter[0] += 1
    path = OUT / f"{counter[0]:02d}_{name}.png"
    page.screenshot(path=str(path))
    print("saved", path.relative_to(ROOT).as_posix())


def scroll_to(page, selector, offset=-90):
    page.evaluate(
        "([sel, off]) => window.scrollTo(0, document.querySelector(sel).getBoundingClientRect().top + window.scrollY + off)",
        [selector, offset],
    )


def new_page(browser, label, theme="dark", viewport=None):
    ctx = browser.new_context(viewport=viewport or {"width": 1440, "height": 900}, color_scheme=theme)
    ctx.add_init_script(f"try{{localStorage.setItem('aegisballot-theme','{theme}')}}catch(e){{}}")
    page = ctx.new_page()
    watch(page, label)
    return ctx, page


def login(page, creds):
    page.goto(f"{WEB}/login")
    page.get_by_label("Username").fill(creds[0])
    page.get_by_label("Password", exact=True).fill(creds[1])
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.wait_for_url("**/app/**")


def api_login(pw, creds):
    ctx = pw.request.new_context(base_url=API)
    r = ctx.post("/api/auth/login", data={"username": creds[0], "password": creds[1]})
    assert r.ok, r.text()
    return ctx, {"X-CSRF-Token": r.json()["csrf"]}


def ensure_demo_election(admin, h):
    """Find or create the demo election (open, with 3 candidates) and return (id, ballots already cast)."""
    elections = admin.get("/api/admin/elections").json()["elections"]
    found = next((e for e in elections if e["title"] == DEMO_TITLE), None)
    if found:
        if found["status"] != "OPEN":
            admin.post(f"/api/admin/elections/{found['id']}/status", data={"status": "OPEN"}, headers=h)
        return found["id"], found["votes"]
    now = datetime.utcnow()
    r = admin.post(
        "/api/admin/elections",
        data={
            "title": DEMO_TITLE,
            "description": "Used to capture documentation screenshots.",
            "start_time": now.isoformat(timespec="seconds"),
            "end_time": (now + timedelta(days=30)).isoformat(timespec="seconds"),
        },
        headers=h,
    )
    assert r.ok, r.text()
    eid = r.json()["id"]
    for name, party, desc, mani in [
        ("Aarohi Sen", "People's Unity Front", "Focus on education and healthcare access for all.", "Universal education, affordable healthcare."),
        ("Rohan Deshmukh", "National Progress Alliance", "Driving innovation and sustainable growth.", "Green energy, startups, modern infrastructure."),
        ("Meera Krishnan", "Civic Harmony Collective", "Inclusive governance and social equity.", "Social welfare and participatory governance."),
    ]:
        c = admin.post(f"/api/admin/elections/{eid}/candidates", data={"name": name, "party": party, "description": desc, "manifesto": mani}, headers=h)
        assert c.ok, c.text()
    admin.post(f"/api/admin/elections/{eid}/status", data={"status": "OPEN"}, headers=h)
    return eid, 0


def pick_voter(pw, eid, identities, start):
    """A demo voter who has not voted in the demo election yet (None when all have).

    Voters vote in order, so the ballot count is the next index; scan on from there (logins are rate limited).
    """
    for i in range(len(identities)):
        ident = identities[(start + i) % len(identities)]
        ctx, _ = api_login(pw, (ident["username"], ident["password"]))
        mine = ctx.get("/api/voter/elections").json()["elections"]
        e = next((x for x in mine if x["id"] == eid), None)
        if e and not e["voted"]:
            return ident
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    identities = json.loads((ROOT / "data" / "synthetic_identities.json").read_text(encoding="utf-8"))
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()  # Playwright's own Chromium (playwright install chromium)
        except Exception:
            # Fall back to installed Chrome; software rendering avoids GPU hangs in headless screenshots.
            browser = pw.chromium.launch(channel="chrome", args=["--use-gl=swiftshader", "--disable-gpu"])

        admin_api, admin_h = api_login(pw, ADMIN)
        eid, cast_so_far = ensure_demo_election(admin_api, admin_h)
        closed = [e for e in admin_api.get("/api/admin/elections").json()["elections"] if e["status"] == "CLOSED" and e["votes"] > 0]
        closed_id = closed[-1]["id"] if closed else None
        voter = pick_voter(pw, eid, identities, cast_so_far)

        # ---- landing, both themes ----
        for theme in ("dark", "light"):
            ctx, page = new_page(browser, f"landing-{theme}", theme)
            page.goto(WEB)
            shot(page, f"landing_{theme}", 2200)
            scroll_to(page, "section[aria-label='Live figures']", -140)
            shot(page, f"landing_{theme}_stats_and_features", 3200)
            scroll_to(page, "#how-it-works", 0)
            shot(page, f"landing_{theme}_how_it_works", 2000)
            scroll_to(page, "#elections", -60)
            shot(page, f"landing_{theme}_elections", 2500)
            ctx.close()

        # ---- login ----
        ctx, page = new_page(browser, "login")
        page.goto(f"{WEB}/login")
        page.get_by_role("button", name="Admin", exact=False).first.click()
        shot(page, "login")
        ctx.close()

        # ---- admin ----
        ctx, page = new_page(browser, "admin")
        login(page, ADMIN)
        shot(page, "admin_dashboard", 3500)
        page.goto(f"{WEB}/app/admin/elections")
        shot(page, "admin_elections")
        page.get_by_role("button", name="New election").click()
        shot(page, "admin_create_election", 700)
        page.keyboard.press("Escape")
        page.goto(f"{WEB}/app/admin/elections/{eid}")
        shot(page, "admin_election_detail")
        if closed_id:
            page.goto(f"{WEB}/app/results/{closed_id}")
            shot(page, "results", 2000)
        page.goto(f"{WEB}/app/admin/benchmarks")
        shot(page, "admin_benchmarks", 1800)
        ctx.close()

        # ---- voter ----
        if voter:
            ctx, page = new_page(browser, "voter")
            login(page, (voter["username"], voter["password"]))
            shot(page, "voter_elections")
            page.goto(f"{WEB}/app/voter/{eid}/verify")
            page.get_by_label("Enter your 12-digit Aadhaar number").fill(voter["aadhaar"])
            shot(page, "voter_aadhaar_verification", 800)
            page.get_by_role("button", name="Verify identity").click()
            page.get_by_role("radiogroup", name="Candidates").wait_for()
            page.get_by_role("radio").first.click()
            shot(page, "voter_candidate_selection", 900)
            page.get_by_role("button", name="Confirm and submit vote").click()
            page.get_by_role("heading", name="Vote confirmed").wait_for()
            shot(page, "voter_receipt", 900)
            page.goto(f"{WEB}/app/voter")
            shot(page, "voter_elections_after_vote")
            ctx.close()
        else:
            print("All demo voters already voted in the demo election; skipped the voter screens.")

        # ---- auditor ----
        ctx, page = new_page(browser, "auditor")
        login(page, AUDITOR)
        page.get_by_role("button", name="Verify ledger integrity").click()
        page.get_by_text("Verified just now").wait_for()
        page.get_by_role("button", name="Run tamper-detection demo").click()
        page.get_by_text("Tampering detected on the clone").wait_for()
        shot(page, "auditor_dashboard", 900)
        page.goto(f"{WEB}/app/auditor/blocks/1")
        shot(page, "auditor_block_detail")
        ctx.close()

        # ---- phone width, for the docs ----
        ctx, page = new_page(browser, "mobile", viewport={"width": 390, "height": 844})
        login(page, ADMIN)
        shot(page, "mobile_admin_dashboard", 3000)
        ctx.close()
        browser.close()

    if problems:
        print("\nBROWSER PROBLEMS:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("\nAll screens captured; console clean.")


if __name__ == "__main__":
    main()
