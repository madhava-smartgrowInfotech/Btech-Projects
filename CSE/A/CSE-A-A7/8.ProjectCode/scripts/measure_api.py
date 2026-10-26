"""Measure API response times on a running server (use 127.0.0.1: 'localhost' adds ~2 s of IPv6 fallback on Windows).

Writes experiments/extra/api_latency.json.   Run:  venv\\Scripts\\python scripts\\measure_api.py [base_url]
"""
import json
import statistics
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8307"
VIT = dict(age=58, heart_rate=112, sbp=96, dbp=60, spo2=93, temp_c=36.9, resp_rate=22, arrival_mode="ambulance")


def timed(fn, n):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        r = fn()
        assert r.ok, r.text[:200]
        ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    return {"n": n, "median_ms": round(statistics.median(ts), 1), "p95_ms": round(ts[int(0.95 * (n - 1))], 1),
            "mean_ms": round(statistics.mean(ts), 1), "max_ms": round(ts[-1], 1)}


def main():
    tok = requests.post(f"{BASE}/api/auth/login", json={"email": "clinician@athena.health", "password": "Athena@123"}).json()["access_token"]
    H = {"Authorization": f"Bearer {tok}"}
    sd = ROOT / "data" / "sample_reports"
    pdf = (sd / "report_01_chest_pain_stemi.pdf").read_bytes()
    png = (sd / "scan_09_asthma.png").read_bytes()
    rep = requests.post(f"{BASE}/api/reports/extract", headers=H, files={"file": ("r.pdf", pdf, "application/pdf")}).json()
    pid = requests.post(f"{BASE}/api/patients", headers=H, json={"vitals": VIT, "report": rep}).json()["id"]
    requests.post(f"{BASE}/api/reports/extract", headers=H, files={"file": ("s.png", png, "image/png")})  # warm OCR
    out = {
        "base_url": BASE,
        "health": timed(lambda: requests.get(f"{BASE}/api/health"), 50),
        "login": timed(lambda: requests.post(f"{BASE}/api/auth/login", json={"email": "clinician@athena.health", "password": "Athena@123"}), 10),
        "queue_list": timed(lambda: requests.get(f"{BASE}/api/patients", headers=H), 30),
        "extract_pdf": timed(lambda: requests.post(f"{BASE}/api/reports/extract", headers=H, files={"file": ("r.pdf", pdf, "application/pdf")}), 30),
        "extract_scan_png": timed(lambda: requests.post(f"{BASE}/api/reports/extract", headers=H, files={"file": ("s.png", png, "image/png")}), 10),
        "create_patient": timed(lambda: requests.post(f"{BASE}/api/patients", headers=H, json={"vitals": VIT, "report": rep}), 30),
        "summary_pdf": timed(lambda: requests.get(f"{BASE}/api/patients/{pid}/summary.pdf", headers=H), 20),
        "metrics": timed(lambda: requests.get(f"{BASE}/api/metrics", headers=H), 20),
    }
    # whole flow: extract the PDF then create the patient
    def flow():
        r = requests.post(f"{BASE}/api/reports/extract", headers=H, files={"file": ("r.pdf", pdf, "application/pdf")})
        return requests.post(f"{BASE}/api/patients", headers=H, json={"vitals": VIT, "report": r.json()})
    out["flow_pdf_then_triage"] = timed(flow, 20)
    def flow_scan():
        r = requests.post(f"{BASE}/api/reports/extract", headers=H, files={"file": ("s.png", png, "image/png")})
        return requests.post(f"{BASE}/api/patients", headers=H, json={"vitals": VIT, "report": r.json()})
    out["flow_scan_then_triage"] = timed(flow_scan, 10)
    dest = ROOT / "experiments" / "extra"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "api_latency.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
