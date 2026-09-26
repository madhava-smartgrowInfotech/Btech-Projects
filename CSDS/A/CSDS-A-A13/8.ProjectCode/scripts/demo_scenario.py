"""Run the SeatWise demo scenario against a running installation and check every step.

    venv\\Scripts\\python scripts\\demo_scenario.py                # uses the sample data (adds/updates it)
    venv\\Scripts\\python scripts\\demo_scenario.py --reset        # clears all exam data first
    venv\\Scripts\\python scripts\\demo_scenario.py --out exports  # also saves the downloaded files

Steps: import the sample workbook -> generate and publish plans for three sittings ->
try an illegal seat swap -> download charts, lists, sheets and slips -> look up a seat
and download its QR slip -> mark attendance as an invigilator.
Standard library only; start SeatWise with run.bat first.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {"adjacency": 8, "roll_gap": 5, "department_mix": True, "fill_strategy": "compact", "accessible_per_hall": 2}


def env_value(key: str, default: str) -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip() or default
    return default


class Client:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.token: str | None = None

    def call(self, method: str, path: str, body=None, raw: bytes | None = None, content_type: str | None = None,
             expect: int | tuple[int, ...] = 200):
        data, headers = None, {}
        if body is not None:
            data, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
        if raw is not None:
            data, headers["Content-Type"] = raw, content_type or "application/octet-stream"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                status, payload, ctype = response.status, response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as err:
            status, payload, ctype = err.code, err.read(), err.headers.get("Content-Type", "")
        expected = expect if isinstance(expect, tuple) else (expect,)
        if status not in expected:
            raise SystemExit(f"FAILED {method} {path}: HTTP {status} {payload[:300]!r}")
        return json.loads(payload) if "json" in ctype else payload

    def upload(self, path: str, filename: str, content: bytes, fields: dict[str, str]):
        boundary = uuid.uuid4().hex
        parts = []
        for name, value in fields.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                     f"Content-Type: application/octet-stream\r\n\r\n".encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        return self.call("POST", path, raw=b"".join(parts), content_type=f"multipart/form-data; boundary={boundary}")


def step(title: str) -> None:
    print(f"\n== {title}")


def ok(text: str) -> None:
    print(f"   OK  {text}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SeatWise demo scenario.")
    parser.add_argument("--url", default=f"http://localhost:{env_value('WEB_PORT', '5113')}/api")
    parser.add_argument("--reset", action="store_true", help="clear all exam data first (accounts are kept)")
    parser.add_argument("--out", type=Path, help="folder to save the downloaded files in")
    args = parser.parse_args()
    password = env_value("DEMO_PASSWORD", "SeatWise@2026")
    admin = Client(args.url)
    started = time.perf_counter()

    step("Sign in")
    admin.call("GET", "/health")
    admin.token = admin.call("POST", "/auth/login", {"email": env_value("DEMO_ADMIN_EMAIL", "admin@seatwise.local"),
                                                     "password": password})["access_token"]
    ok("administrator signed in")
    if args.reset:
        admin.call("POST", "/settings/reset-workspace", {"confirm": "RESET"})
        ok("workspace cleared")

    step("1. Import candidates, halls and timetable")
    workbook = ROOT / "data" / "sample" / "seatwise_sample_workbook.xlsx"
    checked = admin.upload("/imports/workbook/validate", workbook.name, workbook.read_bytes(), {"mode": "update"})
    report = checked["report"]
    if report["errors"]:
        raise SystemExit(f"FAILED validation: {report['issues'][:3]}")
    ok(f"validation passed: {checked['rows_valid']} rows, {report['warnings']} warnings")
    admin.call("POST", f"/imports/{checked['id']}/commit")
    summary = admin.call("GET", "/data/summary")
    ok(f"imported {summary['candidates']} candidates, {summary['courses']} courses, {summary['halls']} halls, "
       f"{summary['sessions']} sittings")

    step("2. Generate plans for three sittings")
    sessions = admin.call("GET", "/sessions")[:3]
    plans = []
    for s in sessions:
        plan = admin.call("POST", f"/sessions/{s['id']}/plans", {"rules": RULES}, expect=201)
        if not plan["hard_ok"] or plan["same_paper_pairs"]:
            raise SystemExit(f"FAILED rules for {s['label']}")
        admin.call("POST", f"/plans/{plan['id']}/publish")
        plans.append(plan)
        ok(f"{s['label']}: {plan['candidates']} candidates in {plan['halls_used']} halls, "
           f"{plan['same_paper_pairs']} same-paper neighbours, {plan['conflicts_avoided']} avoided, "
           f"{plan['solve_ms'] / 1000:.1f} s, seed {plan['seed']} - published")

    step("3. Illegal swap and downloads")
    plan = plans[0]
    hall = plan["halls"][0]
    seat = admin.call("GET", f"/plans/{plan['id']}/halls/{hall['hall_id']}")["seats"][0]["label"]
    options = admin.call("GET", f"/plans/{plan['id']}/halls/{hall['hall_id']}/swap-check?seat={seat}")
    bad = next(t for t in options["targets"] if not t["ok"])
    refused = admin.call("POST", f"/plans/{plan['id']}/swap",
                         {"hall_id": hall["hall_id"], "from_seat": seat, "to_seat": bad["seat"]}, expect=409)
    ok(f"moving {seat} to {bad['seat']} was blocked: {refused['detail']}")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
    for name, magic in [("seating-charts.pdf", b"%PDF"), ("invigilator-sheets.pdf", b"%PDF"), ("qr-slips.pdf", b"%PDF"),
                        ("hall-lists.xlsx", b"PK"), ("attendance.xlsx", b"PK")]:
        content = admin.call("GET", f"/plans/{plan['id']}/exports/{name}")
        if not content.startswith(magic):
            raise SystemExit(f"FAILED download {name}")
        if args.out:
            (args.out / name).write_bytes(content)
        ok(f"{name} ({len(content) // 1024} KB)")

    step("4. Seat lookup, QR slip and attendance")
    public = Client(args.url)
    roll = admin.call("GET", f"/plans/{plan['id']}/halls/{hall['hall_id']}")["seats"][1]["candidate"]["roll_no"]
    found = public.call("GET", f"/public/lookup/{roll}")
    s0 = found["seats"][0]
    ok(f"{roll} ({found['candidate']['name']}) sits in {s0['hall']['code']} seat {s0['seat']['label']}")
    slip = public.call("GET", f"/public/slip/{roll}/{s0['plan_id']}.pdf")
    if not slip.startswith(b"%PDF"):
        raise SystemExit("FAILED slip download")
    if args.out:
        (args.out / f"seat-slip-{roll}.pdf").write_bytes(slip)
    ok(f"QR slip downloaded ({len(slip) // 1024} KB)")

    invigilator = Client(args.url)
    invigilator.token = invigilator.call("POST", "/auth/login", {
        "email": env_value("DEMO_INVIGILATOR_EMAIL", "invigilator@seatwise.local"), "password": password})["access_token"]
    me = invigilator.call("GET", "/auth/me")
    admin.call("PUT", f"/plans/{plan['id']}/invigilators",
               {"assignments": [{"hall_id": hall["hall_id"], "user_ids": [me["id"]]}]})
    seats = invigilator.call("GET", f"/plans/{plan['id']}/halls/{hall['hall_id']}")["seats"]
    invigilator.call("PUT", f"/plans/{plan['id']}/halls/{hall['hall_id']}/attendance/{seats[0]['candidate']['id']}",
                     {"status": "present"})
    scanned = invigilator.call("POST", f"/plans/{plan['id']}/halls/{hall['hall_id']}/attendance/scan", {"code": roll})
    ok(f"{me['full_name']} marked 2 candidates present in {hall['code']} "
       f"({scanned['counts']['present']} present, {scanned['counts']['unmarked']} to mark)")

    print(f"\nDemo scenario passed in {time.perf_counter() - started:.1f} s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
