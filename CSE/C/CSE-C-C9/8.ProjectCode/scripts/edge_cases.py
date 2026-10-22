"""Edge-case and input-security probe against the running API (default http://127.0.0.1:8409).

Sends malformed, boundary and hostile inputs to POST /api/predict and POST /api/whatif and records the
real HTTP status and message in artifacts/edge_cases.json (used by docs/ch7 at build time).

    python scripts/edge_cases.py [--api http://127.0.0.1:8409]
"""
import argparse
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "edge_cases.json"

BASE = {"age": 39, "workclass": "State-gov", "education": "Bachelors", "marital-status": "Never-married",
        "occupation": "Adm-clerical", "relationship": "Not-in-family", "race": "White", "sex": "Male",
        "native-country": "United-States", "capital-gain": 2174, "capital-loss": 0, "hours-per-week": 40}


def without(d, k):
    return {a: b for a, b in d.items() if a != k}


def cases():
    """(id, group, endpoint, description, kind, payload)  kind: json | raw-json | raw-text | empty"""
    P, W = "/api/predict", "/api/whatif"
    c = [
        ("E01", "Required fields", P, "Missing field (workclass omitted)", "json", without(BASE, "workclass")),
        ("E02", "Required fields", P, "Empty JSON object {}", "json", {}),
        ("E03", "Required fields", P, "Empty request body (no content)", "empty", None),
        ("E04", "Required fields", P, "Body is not JSON (plain text)", "raw-text", "age=39&sex=Male"),
        ("E05", "Required fields", P, "Malformed JSON (truncated)", "raw-json", '{"age": 39, "workclass": '),
        ("E06", "Numeric range", P, "Age 15 (below minimum 16)", "json", {**BASE, "age": 15}),
        ("E07", "Numeric range", P, "Age 101 (above maximum 100)", "json", {**BASE, "age": 101}),
        ("E08", "Numeric range", P, "Age 16 (lower boundary)", "json", {**BASE, "age": 16}),
        ("E09", "Numeric range", P, "Age 100 (upper boundary)", "json", {**BASE, "age": 100}),
        ("E10", "Numeric range", P, "Hours 0 (below minimum 1)", "json", {**BASE, "hours-per-week": 0}),
        ("E11", "Numeric range", P, "Hours 100 (above maximum 99)", "json", {**BASE, "hours-per-week": 100}),
        ("E12", "Numeric range", P, "Negative investment gains (-5)", "json", {**BASE, "capital-gain": -5}),
        ("E13", "Numeric range", P, "Negative investment losses (-1)", "json", {**BASE, "capital-loss": -1}),
        ("E14", "Numeric range", P, "Investment gains 1,000,000 (upper boundary)", "json", {**BASE, "capital-gain": 1000000}),
        ("E15", "Numeric range", P, "Investment gains 1,000,001 (above maximum)", "json", {**BASE, "capital-gain": 1000001}),
        ("E16", "Numeric range", P, "Age given as text ('abc')", "json", {**BASE, "age": "abc"}),
        ("E17", "Allowed values", P, "Unknown workclass ('Hacker')", "json", {**BASE, "workclass": "Hacker"}),
        ("E18", "Allowed values", P, "Unknown country ('Atlantis')", "json", {**BASE, "native-country": "Atlantis"}),
        ("E19", "Hostile input", P, "Script text in a field (occupation)", "json", {**BASE, "occupation": "<script>alert(1)</script>"}),
        ("E20", "Hostile input", P, "SQL-style text in a field (sex)", "json", {**BASE, "sex": "Male'; DROP TABLE users;--"}),
        ("E21", "Hostile input", P, "Extra unknown field added (is_admin)", "json", {**BASE, "is_admin": True}),
        ("E22", "Hostile input", P, "Very long string (10,000 characters) in race", "json", {**BASE, "race": "A" * 10000}),
        ("E23", "Scenario", W, "What-if with no scenario field changed", "json", dict(BASE)),
        ("E24", "Scenario", W, "What-if with gains 1,000,001 (above maximum)", "json", {**BASE, "scenario_capital_gain": "1000001"}),
        ("E25", "Scenario", W, "What-if with hours 500", "json", {**BASE, "scenario_hours": "500"}),
        ("E26", "Scenario", W, "What-if with unknown education", "json", {**BASE, "scenario_education": "Wizard"}),
        ("E27", "Scenario", W, "What-if with valid change (hours 40 to 50)", "json", {**BASE, "scenario_hours": "50"}),
        ("E28", "Scenario", W, "What-if with same value as baseline (hours 40)", "json", {**BASE, "scenario_hours": "40"}),
        ("E29", "Scenario", W, "What-if with extreme gains 1,000,000", "json", {**BASE, "scenario_capital_gain": "1000000"}),
    ]
    return c


def send(api, ep, kind, payload):
    url = api + ep
    t0 = time.perf_counter()
    if kind == "json":
        r = requests.post(url, json=payload, timeout=60)
    elif kind == "raw-json":
        r = requests.post(url, data=payload, headers={"Content-Type": "application/json"}, timeout=60)
    elif kind == "raw-text":
        r = requests.post(url, data=payload, headers={"Content-Type": "text/plain"}, timeout=60)
    else:
        r = requests.post(url, timeout=60)
    ms = (time.perf_counter() - t0) * 1000
    try:
        body = r.json()
    except ValueError:
        body = None
    return r, body, ms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8409")
    a = ap.parse_args()
    rows = []
    for cid, group, ep, desc, kind, payload in cases():
        r, body, ms = send(a.api, ep, kind, payload)
        msg, outcome = "", ""
        if isinstance(body, dict) and body.get("errors"):
            msg = "; ".join(body["errors"])[:160]
        elif isinstance(body, dict) and body.get("ok") and "result" in body:
            res = body["result"]
            if "delta" in res:
                outcome = f"delta {res['delta_pct']:+.2f} pp, {res['baseline']['profile']} -> {res['scenario']['profile']}"
            else:
                outcome = f"p {res['proba']:.4f}, {res['profile']} / {res['risk']}"
        elif body is None:
            msg = "non-JSON response: " + r.text[:80].replace("\n", " ")
        rows.append({"id": cid, "group": group, "endpoint": ep, "case": desc, "status": r.status_code,
                     "message": msg, "outcome": outcome, "ms": round(ms, 1)})
        print(cid, r.status_code, desc, "|", msg or outcome)
    # GET probes: file-access attempts through the artifact route and common sensitive paths
    gets = [("G01", "Path probes", "/artifacts/confusion_matrix.png", "Allowed artifact image"),
            ("G02", "Path probes", "/artifacts/metrics.json", "Artifact not on the allow-list (metrics.json)"),
            ("G03", "Path probes", "/artifacts/best_model.pkl", "Model file requested through the artifact route"),
            ("G04", "Path probes", "/artifacts/..%2fmodels%2fbest_model.pkl", "Encoded path traversal to models/best_model.pkl"),
            ("G05", "Path probes", "/models/best_model.pkl", "Direct path to the model file"),
            ("G06", "Path probes", "/.env", "Environment file"),
            ("G07", "Path probes", "/no-such-page", "Unknown page")]
    for gid, group, path, desc in gets:
        t0 = time.perf_counter()
        r = requests.get(a.api + path, timeout=30)
        ms = (time.perf_counter() - t0) * 1000
        rows.append({"id": gid, "group": group, "endpoint": "GET " + path, "case": desc, "status": r.status_code,
                     "message": r.headers.get("content-type", "").split(";")[0], "outcome": "", "ms": round(ms, 1)})
        print(gid, r.status_code, desc)
    # the server must still be healthy after the hostile inputs
    h = requests.get(a.api + "/health", timeout=30)
    out = {"api": a.api, "date": time.strftime("%Y-%m-%d"), "cases": rows,
           "health_after": {"status": h.status_code, "body": h.json()}}
    OUT.write_text(json.dumps(out, indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
