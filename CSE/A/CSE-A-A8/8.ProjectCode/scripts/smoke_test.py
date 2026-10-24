"""
End-to-end smoke test for LabLens.

    python scripts/smoke_test.py            # API flow, plus a browser flow when Playwright and frontend/dist exist
    python scripts/smoke_test.py --no-ui    # API flow only

The test copies the product modules into a temporary folder and starts its own server there on a
spare port, so your real database in data/ is never touched. Needs: pip install fastapi uvicorn
python-multipart (the backend requirements); the UI part also needs `pip install playwright`
and a built frontend (cd frontend && npm run build).
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8398
BASE = f"http://127.0.0.1:{PORT}"
EMAIL, PASSWORD = "demo@lablens.com", "Demo@1234"

failures = []


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def call(method, path, body=None, token=None, files=None):
    headers = {}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if files:
        boundary = uuid.uuid4().hex
        parts = []
        for field, (fname, content) in files.items():
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{fname}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n".encode() + content + b"\r\n"
            )
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="use_llm"\r\n\r\nfalse\r\n'.encode())
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw.decode(errors="replace")


def start_server(workdir: Path):
    log = open(workdir / "server.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "-W", "ignore", "-m", "uvicorn", "backend.main:app", "--port", str(PORT), "--host", "127.0.0.1"],
        cwd=workdir,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    for _ in range(60):
        try:
            if call("GET", "/api/health")[0] == 200:
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.kill()
    raise SystemExit("server did not start - see " + str(workdir / "server.log"))


def api_flow():
    print("API")
    sys.path.insert(0, str(ROOT))
    from backend.demo_data import render_pdf

    check("health", call("GET", "/api/health")[1] == {"status": "ok"})
    st, cfg = call("GET", "/api/config")
    check("config has disclaimer + formats", st == 200 and cfg["disclaimer"] and ".pdf" in cfg["supported_extensions"] and len(cfg["known_tests"]) > 40)
    check("protected route rejects anonymous", call("GET", "/api/dashboard")[0] == 401)
    check("bad login rejected", call("POST", "/api/auth/login", {"email": EMAIL, "password": "nope"})[0] == 401)
    st, res = call("POST", "/api/auth/login", {"email": EMAIL, "password": PASSWORD})
    check("demo login", st == 200 and res["token"])
    tok = res["token"]
    check("me", call("GET", "/api/auth/me", token=tok)[1]["email"] == EMAIL)

    st, dash = call("GET", "/api/dashboard", token=tok)
    check("empty dashboard", st == 200 and dash["stats"]["total_reports"] == 0 and dash["recent"] == [])
    check("compare/trends empty states", call("GET", "/api/tests", token=tok)[1] == [] and call("GET", "/api/insights", token=tok)[1] == [])

    st, seeded = call("POST", "/api/demo/seed", token=tok)
    check("sample reports seeded through the pipeline", st == 200 and len(seeded["created"]) == 5 and all(c["status"] == "Completed" for c in seeded["created"]))
    check("seeding twice is refused", call("POST", "/api/demo/seed", token=tok)[0] == 409)

    st, dash = call("GET", "/api/dashboard", token=tok)
    stats = dash["stats"]
    check("dashboard stats", stats["total_reports"] == 5 and stats["total_tests"] == 70 and stats["abnormal"] > 0 and stats["critical"] >= 1, str(stats))

    st, reports = call("GET", "/api/reports", token=tok)
    check("report list newest first", st == 200 and len(reports) == 5 and reports[0]["file_name"].endswith("Oct2026.pdf"))
    newest, oldest = reports[0]["id"], reports[-1]["id"]
    st, det = call("GET", f"/api/reports/{oldest}", token=tok)
    low = [r for r in det["results"] if r["status"] == "LOW"]
    check("report detail with insights", st == 200 and low and all(r["insight"] and r["insight"]["explanation"] for r in low))
    check("unknown report is 404", call("GET", "/api/reports/9999", token=tok)[0] == 404)

    st, tr = call("GET", "/api/trends?test=Hemoglobin", token=tok)
    check("trend is ordered and increasing", st == 200 and tr["direction"] == "increasing" and [p["value"] for p in tr["points"]] == [10.8, 11.2, 11.9, 12.6, 13.1])
    st, cmp_ = call("GET", f"/api/compare?a={oldest}&b={newest}", token=tok)
    row = next(r for r in cmp_["rows"] if r["test"] == "Hemoglobin")
    check("compare change = report 2 - report 1", st == 200 and len(cmp_["rows"]) == 14 and row["change"] == 2.3, str(row))
    check("compare same report rejected", call("GET", f"/api/compare?a={oldest}&b={oldest}", token=tok)[0] == 400)
    st, ins = call("GET", "/api/insights", token=tok)
    check("insights cover every abnormal result", st == 200 and len(ins) == stats["abnormal"] and all(i["insight"] for i in ins))

    # a fresh upload through the real endpoint
    st, up = call("POST", "/api/reports", token=tok, files={"file": ("Upload_Test.pdf", render_pdf(1, datetime(2026, 10, 24)))})
    check("PDF upload processed", st == 200 and up["status"] == "Completed" and len(up["results"]) == 14 and "AI health insights" in up["stages_completed"])
    st, bad = call("POST", "/api/reports", token=tok, files={"file": ("notes.txt", b"hello")})
    check("unsupported file gives a readable error", st == 200 and bad["status"] == "Failed" and "Unsupported file format" in bad["error"])
    st, empty = call("POST", "/api/reports", token=tok, files={"file": ("empty.pdf", b"")})
    check("empty file gives a readable error", empty["status"] == "Failed" and "empty" in empty["error"].lower())
    st, det = call("GET", f"/api/reports/{bad['report_id']}", token=tok)
    check("failed report keeps its error message", det["report"]["processing_status"] == "Failed" and det["report"]["error_message"])

    check("delete", call("DELETE", f"/api/reports/{up['report_id']}", token=tok)[1] == {"deleted": up["report_id"]})
    check("delete twice is 404", call("DELETE", f"/api/reports/{up['report_id']}", token=tok)[0] == 404)
    call("DELETE", f"/api/reports/{bad['report_id']}", token=tok)
    call("DELETE", f"/api/reports/{empty['report_id']}", token=tok)


def ui_flow():
    print("Browser (built frontend served by the backend)")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  skipped: playwright is not installed")
        return
    problems = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: m.type == "error" and problems.append(m.text))
        page.on("pageerror", lambda e: problems.append(str(e)))
        page.goto(BASE + "/app/trends")
        check("anonymous visit is sent to the login page", page.wait_for_url("**/login", timeout=10000) is None)
        page.click("button:has-text('Sign in as demo user')")
        page.wait_for_url("**/app/trends", timeout=15000)
        page.wait_for_selector(".recharts-line", timeout=20000)
        check("trend chart renders from the API", page.locator(".recharts-line").count() >= 1)
        page.goto(BASE + "/app/compare")
        page.wait_for_selector(".recharts-bar", timeout=20000)
        check("compare chart renders", page.locator(".recharts-bar").count() >= 1)
        page.goto(BASE + "/app/insights")
        page.wait_for_selector(".insight-card", timeout=20000)
        check("insight cards render", page.locator(".insight-card").count() > 0)
        page.goto(BASE + "/app/upload")
        page.set_input_files("input[type=file]", {"name": "notes.txt", "mimeType": "text/plain", "buffer": b"hi"})
        check("wrong file type is rejected in the browser", page.locator("[role=alert]:has-text('not a supported file type')").count() == 1)
        page.goto(BASE + "/app/reports")
        page.wait_for_selector("button[aria-expanded]")
        page.click("button:has-text('Delete') >> nth=0")
        page.wait_for_selector("[role=dialog]")
        page.keyboard.press("Escape")
        page.wait_for_selector("[role=dialog]", state="detached")
        check("Escape closes the delete dialog", True)
        browser.close()
    check("no console errors in the browser", not problems, "; ".join(problems[:3]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ui", action="store_true")
    args = ap.parse_args()

    work = Path(tempfile.mkdtemp(prefix="lablens_smoke_"))
    for f in ROOT.glob("*.py"):
        shutil.copy(f, work)
    shutil.copytree(ROOT / "backend", work / "backend", ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    (work / "data").mkdir()
    dist = ROOT / "frontend" / "dist"
    if dist.is_dir() and not args.no_ui:
        shutil.copytree(dist, work / "frontend" / "dist")
    proc = start_server(work)
    try:
        api_flow()
        if not args.no_ui and dist.is_dir():
            ui_flow()
        elif not args.no_ui:
            print("Browser flow skipped: run `npm run build` in frontend/ first")
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except Exception:
            proc.kill()
        shutil.rmtree(work, ignore_errors=True)
    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: " + ", ".join(failures))
        sys.exit(1)
    print("All smoke checks passed.")


if __name__ == "__main__":
    main()
