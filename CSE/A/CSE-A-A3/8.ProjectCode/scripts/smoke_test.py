"""Smoke test for the JSON API (backend must be running on BACKEND_PORT, default 8303).

    venv\\Scripts\\python scripts\\smoke_test.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

PORT = os.environ.get("BACKEND_PORT", "8303")
BASE = f"http://127.0.0.1:{PORT}"
DISEASES = ["diabetes", "heart", "liver", "kidney"]
failures = []


def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def check(name, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  {extra}" if extra else ""))
    if not ok:
        failures.append(name)


status, body = call("/api/health")
check("health", status == 200 and body["status"] == "ok")

status, body = call("/api/diseases")
check("diseases list", status == 200 and [d["key"] for d in body] == DISEASES)

status, rep = call("/api/report")
check("report has 4 algorithms per disease", status == 200 and all(len(rep[d]["all_results"]) == 4 for d in DISEASES))

status, ds = call("/api/datasets")
check("datasets rows", status == 200 and all(d["rows"] > 0 and d["positive"] + d["negative"] == d["rows"] for d in ds))

for d in DISEASES:
    status, info = call(f"/api/diseases/{d}")
    check(f"{d}: form metadata", status == 200 and len(info["fields"]) == info["n_features"])
    for outcome in (0, 1):
        status, sample = call(f"/api/diseases/{d}/sample?outcome={outcome}")
        ok = status == 200 and sample["label"] == outcome
        check(f"{d}: sample outcome={outcome}", ok)
        status, res = call(f"/api/predict/{d}", {"values": sample["values"]})
        check(
            f"{d}: predict from sample {outcome}",
            status == 200 and res["result"] in ("Positive (High Risk)", "Negative (Low Risk)") and 0 < (res["probability"] or 0) <= 100,
            f"{res.get('result')} {res.get('probability')}%",
        )

status, res = call("/api/predict/diabetes", {"values": {"Glucose": "abc"}})
check("invalid input -> 422 with message", status == 422 and "valid number" in res["detail"])
status, res = call("/api/predict/nope", {"values": {}})
check("unknown disease -> 404", status == 404)

print(f"\n{'ALL PASSED' if not failures else str(len(failures)) + ' FAILED'}")
sys.exit(1 if failures else 0)
