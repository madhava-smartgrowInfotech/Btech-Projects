"""Walk every LearnPathIQ screen in a real browser, put real data on it, and save 1440x900 PNGs.

Needs both servers running (run.bat). Usage:  python scripts/capture_screens.py
Screenshots land in docs/screenshots/<nn>_<screen>.png. The script also fails if the console shows
errors, unhandled exceptions or any 4xx/5xx response, so it doubles as a console-clean check.
"""
import sys
import time
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"


def env_port(name, default):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return default


BASE = f"http://127.0.0.1:{env_port('FRONTEND_PORT', '5407')}"
problems = []


def watch(page):
    page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    page.on("response", lambda r: problems.append(f"HTTP {r.status} {r.url}") if r.status >= 400 else None)


def settle(page, ms=1400):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def shot(page, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved", path.relative_to(ROOT))


def go(page, path, ms=1400):
    page.goto(BASE + path)
    settle(page, ms)


def main():
    stamp = uuid.uuid4().hex[:6]
    email = f"capture_{stamp}@example.com"
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light", reduced_motion="no-preference")
        page = ctx.new_page()
        watch(page)

        # ---- public screens ----
        go(page, "/", 2200)
        shot(page, "01_landing_light")
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(500)
        shot(page, "02_landing_dark")
        page.get_by_role("button", name="Switch to light mode").click()
        go(page, "/login")
        shot(page, "03_login")
        go(page, "/register")
        shot(page, "04_register")
        go(page, "/courses")
        shot(page, "05_catalog")

        # ---- register through the UI ----
        go(page, "/register")
        page.get_by_label("Full name").fill("Capture Learner")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password", exact=True).fill("secret123")
        page.get_by_label("Confirm password").fill("secret123")
        page.get_by_role("button", name="Create account").click()
        page.wait_for_url("**/app/profile")
        settle(page)

        # ---- profile through the UI ----
        page.get_by_label("Education / background").select_option("Bachelor's Degree")
        page.get_by_label("Skill level").select_option("Beginner")
        page.get_by_label("Interests").fill("python, data science, machine learning")
        page.get_by_label("Preferred topics").fill("Machine Learning, Data Analysis")
        page.get_by_label("Learning goals").fill("get a data job, build portfolio")
        page.get_by_label("Course preferences").fill("hands-on labs, short videos")
        page.get_by_label("Weekly study hours").fill("6")
        shot(page, "06_profile_first_run")
        page.get_by_role("button", name="Save and get recommendations").click()
        page.wait_for_url(f"{BASE}/app")

        # ---- put real activity on the account (same API the UI uses) ----
        recs = ctx.request.get(BASE + "/api/recommendations?top_n=8").json()["recommendations"]
        ids = [r["course"]["id"] for r in recs]
        events = [(0, "open"), (0, "start"), (0, "quiz"), (0, "quiz"), (0, "content"), (0, "complete"), (1, "view"), (1, "start"), (1, "forum"),
                  (2, "save"), (3, "dismiss"), (4, "open")]
        for idx, ev in events:
            r = ctx.request.post(BASE + "/api/interactions", data={"course_id": ids[idx], "event_type": ev, "value": 1.0})
            assert r.ok, r.text()
        ctx.request.get(BASE + "/api/recommendations?top_n=12")  # logs a second history batch

        # ---- signed-in screens ----
        go(page, "/app")
        shot(page, "07_dashboard")
        go(page, "/app/recommendations")
        shot(page, "08_recommendations")
        go(page, "/app/path")
        shot(page, "09_learning_path")
        go(page, "/app/insights")
        shot(page, "10_insights")
        go(page, "/app/activity")
        shot(page, "11_activity_interactions")
        page.get_by_role("tab", name="Recommendation history").click()
        page.wait_for_timeout(500)
        shot(page, "12_activity_history")
        go(page, "/courses")
        shot(page, "13_catalog_signed_in")
        go(page, f"/courses/{ids[0]}")
        shot(page, "14_course_detail")
        go(page, "/app/profile")
        shot(page, "15_profile")
        go(page, "/analytics")
        shot(page, "16_analytics_models")
        for i, (tab, name) in enumerate([("Diagnostics", "17_analytics_diagnostics"), ("Offline policy", "18_analytics_policy"), ("Fairness audit", "19_analytics_fairness")]):
            page.get_by_role("tab", name=tab).click()
            page.wait_for_timeout(1300)
            shot(page, name)

        # dark mode on a data screen
        go(page, "/app")
        page.get_by_role("button", name="Switch to dark mode").click()
        page.wait_for_timeout(600)
        shot(page, "20_dashboard_dark")
        browser.close()

    time.sleep(0.2)
    if problems:
        print("\nCONSOLE / NETWORK PROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        sys.exit(1)
    print("\nAll screens captured; console clean.")


if __name__ == "__main__":
    main()
