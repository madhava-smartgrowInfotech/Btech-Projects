"""Capture a 1440x900 PNG of every FINJARVIS screen into docs/screenshots/<nn>_<screen>.png.

Uses the fictional demo account (demo / Demo@1234), whose transactions, budgets, goals and investments are
generated for the current month, so no screen is empty. If the app is not already running on the ports in
.env, this script starts a backend (with a throw-away database) and the Vite dev server itself, then stops them.

    pip install playwright        (once)
    playwright install chromium   (once; falls back to your installed Google Chrome if that is missing)
    python scripts/capture_screens.py
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from datetime import date

from playwright.sync_api import Page, sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")


def read_env() -> dict[str, str]:
    env = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env


def listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for(port: int, seconds: int = 90) -> None:
    for _ in range(seconds):
        if listening(port):
            return
        time.sleep(1)
    raise RuntimeError(f"nothing is listening on port {port}")


def python_exe() -> str:
    venv = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    return venv if os.path.exists(venv) else sys.executable


def main() -> int:
    env = read_env()
    be_port, fe_port = int(env.get("BACKEND_PORT", 8411)), int(env.get("FRONTEND_PORT", 5411))
    started: list[subprocess.Popen] = []
    tmp = tempfile.mkdtemp(prefix="finjarvis_shots_")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    if not listening(be_port):
        print(f"Starting the backend on {be_port} with a temporary database ...")
        started.append(subprocess.Popen(
            [python_exe(), "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(be_port)],
            cwd=ROOT, env={**os.environ, "FINJARVIS_DB": os.path.join(tmp, "shots.db")},
            stdout=open(os.path.join(tmp, "be.log"), "w"), stderr=subprocess.STDOUT, creationflags=flags))
        wait_for(be_port)
    if not listening(fe_port):
        print(f"Starting the web app on {fe_port} ...")
        vite = os.path.join(ROOT, "frontend", "node_modules", "vite", "bin", "vite.js")
        started.append(subprocess.Popen(
            ["node", vite], cwd=os.path.join(ROOT, "frontend"),
            stdout=open(os.path.join(tmp, "fe.log"), "w"), stderr=subprocess.STDOUT, creationflags=flags))
        wait_for(fe_port)

    base = f"http://localhost:{fe_port}"
    os.makedirs(OUT, exist_ok=True)
    taken: list[str] = []

    def shot(page: Page, name: str) -> None:
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1200)
        path = os.path.join(OUT, f"{len(taken) + 1:02d}_{name}.png")
        page.screenshot(path=path)  # viewport = 1440x900
        taken.append(path)
        print("saved", os.path.relpath(path, ROOT))

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception:
                browser = p.chromium.launch(channel="chrome")
            # reduced motion makes counters and charts settle instantly, so every capture shows final numbers
            light = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light", reduced_motion="reduce")
            dark = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark", reduced_motion="reduce")

            for ctx, name in ((dark, "landing-dark"), (light, "landing-light")):
                page = ctx.new_page()
                page.goto(base + "/")
                shot(page, name)
                page.close()

            page = dark.new_page()
            page.goto(base + "/login")
            shot(page, "login")
            page.goto(base + "/signup")
            shot(page, "signup")
            page.goto(base + "/login")
            page.get_by_role("button", name="Try the demo account").click()
            page.wait_for_url("**/app")

            shot(page, "dashboard")
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(500)
            shot(page, "dashboard-charts")

            page.goto(base + "/app/transactions")
            shot(page, "transactions-add")
            page.goto(base + "/app/transactions?tab=manage")
            shot(page, "transactions-manage")

            csv = os.path.join(tmp, "statement.csv")
            m = date.today().strftime("%Y-%m")
            with open(csv, "w") as f:
                f.write("date,description,amount,category,type\n"
                        f"{m}-02,Zomato order,640,,expense\n{m}-03,Metro card recharge,500,,expense\n"
                        f"{m}-04,Amazon purchase,2399,Shopping,expense\n{m}-05,Freelance payment,12000,Salary,income\nnot-a-date,Broken row,10,Food,expense\n")
            page.goto(base + "/app/transactions?tab=import")
            page.locator("input[type=file]").set_input_files(csv)
            page.get_by_text("Preview:").wait_for()
            shot(page, "transactions-import")

            page.goto(base + "/app/analytics")
            shot(page, "analytics")
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(500)
            shot(page, "analytics-prediction")
            page.goto(base + "/app/budgets")
            shot(page, "budgets")
            page.goto(base + "/app/goals")
            shot(page, "goals")
            page.goto(base + "/app/investments")
            shot(page, "investments")

            page.goto(base + "/app/assistant")
            page.get_by_role("button", name="Where am I spending the most money?").click()
            page.get_by_text("Your biggest spending category").wait_for()
            page.get_by_role("button", name="What is my financial health?").click()
            page.get_by_text("financial health score is").wait_for()
            shot(page, "assistant")

            page.goto(base + "/app/reports")
            shot(page, "reports")
            page.goto(base + "/app/notifications")
            shot(page, "notifications")
            page.goto(base + "/app/profile")
            shot(page, "profile")

            page.goto(base + "/app")
            page.get_by_role("button", name="Switch to light mode").click()
            shot(page, "dashboard-light")
            browser.close()
    finally:
        for proc in started:
            proc.terminate()
    print(f"\n{len(taken)} screenshots in docs/screenshots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
