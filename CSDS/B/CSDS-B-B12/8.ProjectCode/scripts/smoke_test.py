"""End-to-end smoke test against the running API (start it with run.bat first).

python scripts/smoke_test.py
"""
import glob
import os
import pathlib
import sqlite3
import sys

import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8212')}/api"
failures = []


def check(name, cond, info=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {info}")
    if not cond:
        failures.append(name)


def login(email, pw):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pw}, timeout=30)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def upload(headers, pid, path):
    with open(path, "rb") as f:
        return requests.post(f"{BASE}/scans", headers=headers, data={"patient_id": pid}, files={"file": (os.path.basename(path), f)}, timeout=300)


def main():
    r = requests.get(f"{BASE}/health", timeout=10)
    check("health", r.ok, r.text)
    check("wrong password rejected", requests.post(f"{BASE}/auth/login", json={"email": "doctor@pulmovision.app", "password": "x"}).status_code == 401)
    check("unauthenticated request rejected", requests.get(f"{BASE}/patients").status_code == 401)
    doc = login("doctor@pulmovision.app", "Doctor@123")
    tech = login("tech@pulmovision.app", "Tech@123")

    r = requests.post(f"{BASE}/patients", headers=tech, json={"name": "Sample Patient A", "phone": "9000000001", "age": 46, "sex": "Male"})
    check("technician registers patient", r.ok, r.text[:120])
    pid = r.json()["id"]

    tb = sorted(glob.glob(str(ROOT / "data/sample/xray/Tuberculosis/*")))[0]
    r = upload(tech, pid, tb)
    check("X-ray upload analysed", r.ok, r.text[:200])
    xr = r.json()
    check("X-ray routed to X-ray model", xr.get("modality") == "xray", xr.get("modality"))
    print(f"       -> {xr.get('prediction')} {xr.get('confidence', 0) * 100:.1f}% severity {xr.get('severity')} ({xr.get('affected_pct')}%)")
    check("TB sample classified as Tuberculosis", xr.get("prediction") == "Tuberculosis")
    for kind in ("original", "resized", "denoised", "enhanced", "mask", "heatmap"):
        im = requests.get(f"{BASE}/scans/{xr['id']}/image/{kind}", headers=tech)
        check(f"image {kind}", im.ok and im.content[:4] == b"\x89PNG")

    ct = sorted(glob.glob(str(ROOT / "data/chest_ct/test/adenocarcinoma/*")))[0]
    r = upload(tech, pid, ct)
    check("CT upload analysed", r.ok, r.text[:200])
    c = r.json()
    check("CT routed to CT model", c.get("modality") == "ct", c.get("modality"))
    print(f"       -> {c.get('prediction')} {c.get('confidence', 0) * 100:.1f}% severity {c.get('severity')}")

    other = sorted(glob.glob(str(ROOT / "data/sample/other/*")))[0]
    r = upload(tech, pid, other)
    check("non-chest image rejected", r.status_code == 422, r.text[:160])
    r = requests.post(f"{BASE}/scans", headers=tech, data={"patient_id": pid}, files={"file": ("notes.txt", b"hello world" * 20)})
    check("non-image file rejected", r.status_code == 422, r.text[:120])

    check("technician cannot use assistant", requests.post(f"{BASE}/scans/{xr['id']}/assistant", headers=tech, json={"question": "hi"}).status_code == 403)
    r = requests.post(f"{BASE}/scans/{xr['id']}/assistant", headers=doc, json={"question": "What should happen next?"}, timeout=120)
    check("assistant answers", r.ok and len(r.json().get("answer", "")) > 20, (r.json().get("model", "") if r.ok else r.text[:200]))

    for lang in ("en", "te"):
        r = requests.get(f"{BASE}/scans/{xr['id']}/report", headers=doc, params={"lang": lang}, timeout=180)
        check(f"{lang} PDF report", r.ok and r.content[:4] == b"%PDF", f"{len(r.content)} bytes, AI: {r.headers.get('X-AI-Status')}")
    check("technician cannot download report", requests.get(f"{BASE}/scans/{xr['id']}/report", headers=tech).status_code == 403)

    p = requests.get(f"{BASE}/patients/{pid}", headers=doc).json()
    check("patient history lists both scans", len(p["scans"]) >= 2 and p["name"] == "Sample Patient A")
    audit = requests.get(f"{BASE}/audit", headers=doc).json()
    actions = {a["action"] for a in audit}
    check("audit log records actions", {"login", "scan_upload", "scan_rejected", "report_download"} <= actions, sorted(actions))
    r = requests.get(f"{BASE}/metrics", headers=doc)
    check("metrics available", r.ok, "" if r.ok else r.text[:100])

    con = sqlite3.connect(ROOT / "data" / "app.db")
    raw = con.execute("select name_enc from patients where id=?", (pid,)).fetchone()[0]
    check("patient name encrypted at rest", "Sample Patient" not in raw and raw.startswith("gAAAA"))
    stored = list((ROOT / "data" / "store").glob("*.enc"))
    check("scan files encrypted at rest", stored and not stored[0].read_bytes().startswith((b"\x89PNG", b"\xff\xd8")))

    print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
