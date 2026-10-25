"""Functional, validation, consistency and latency tests for the JSON API (backend must be running).

    venv\\Scripts\\python scripts\\api_tests.py        ->  docs/experiments/api_tests.json
Uses 127.0.0.1 (not localhost) so the latency numbers do not include IPv6 fallback delay.
"""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
PORT = os.environ.get("BACKEND_PORT", "8303")
BASE = f"http://127.0.0.1:{PORT}"
DISEASES = ["diabetes", "heart", "liver", "kidney"]
results = []


def call(path, body=None, method=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except Exception:
            return e.code, {}


def check(group, name, ok, extra=""):
    results.append({"group": group, "name": name, "passed": bool(ok), "detail": extra})
    print(("PASS " if ok else "FAIL ") + f"[{group}] {name}  {extra}")


def sample(d, outcome):
    return call(f"/api/diseases/{d}/sample?outcome={outcome}")[1]["values"]


# ---- functional: every endpoint, every disease, both classes
check("functional", "health", call("/api/health")[0] == 200)
s, body = call("/api/diseases")
check("functional", "four diseases listed", s == 200 and [x["key"] for x in body] == DISEASES)
s, rep = call("/api/report")
check("functional", "report: 4 algorithms x 4 diseases", s == 200 and all(len(rep[d]["all_results"]) == 4 for d in DISEASES))
s, ds = call("/api/datasets")
check("functional", "datasets: rows = positive + negative", s == 200 and all(x["rows"] == x["positive"] + x["negative"] for x in ds))
for d in DISEASES:
    s, info = call(f"/api/diseases/{d}")
    check("functional", f"{d}: form metadata matches feature count", s == 200 and len(info["fields"]) == info["n_features"])
    for o in (0, 1):
        s, smp = call(f"/api/diseases/{d}/sample?outcome={o}")
        check("functional", f"{d}: sample outcome={o} has that label", s == 200 and smp["label"] == o)
        s, res = call(f"/api/predict/{d}", {"values": smp["values"]})
        check("functional", f"{d}: predict from sample {o}",
              s == 200 and res["result"] in ("Positive (High Risk)", "Negative (Low Risk)") and 50 <= res["probability"] <= 100,
              f"{res.get('result')} {res.get('probability')}%")

# ---- agreement of API with the original Flask pages (same bundles, same maths)
import numpy as np  # noqa: E402
import app as flask_app  # noqa: E402

agree = 0
total = 0
for d in DISEASES:
    model, scaler, feats = flask_app.BUNDLES[d]
    for o in (0, 1):
        for _ in range(5):
            vals = sample(d, o)
            pred = int(model.predict(scaler.transform(np.array([vals[f] for f in feats]).reshape(1, -1)))[0])
            s, res = call(f"/api/predict/{d}", {"values": vals})
            total += 1
            agree += int((res["positive"]) == (pred == 1))
check("consistency", "API prediction equals direct model.predict on 40 sampled rows", agree == total, f"{agree}/{total}")
a = call("/api/predict/heart", {"values": sample("heart", 1)})
v = sample("heart", 1)
r1 = call("/api/predict/heart", {"values": v})[1]
r2 = call("/api/predict/heart", {"values": v})[1]
check("consistency", "same input twice gives identical output", r1 == r2)

# ---- validation and error handling
base_ok = sample("diabetes", 1)
miss = dict(base_ok)
miss.pop("Glucose")
s, r = call("/api/predict/diabetes", {"values": miss})
check("validation", "missing field -> 422 naming the field", s == 422 and "Glucose" in r["detail"], r.get("detail", ""))
s, r = call("/api/predict/diabetes", {"values": {}})
check("validation", "empty values -> 422", s == 422)
for label, bad in (("non-numeric text", "abc"), ("NaN", "nan"), ("Infinity", "inf"), ("null", None), ("empty string", "")):
    vals = dict(base_ok)
    vals["Glucose"] = bad
    s, r = call("/api/predict/diabetes", {"values": vals})
    check("validation", f"Glucose = {label} -> 422", s == 422, str(r.get("detail", ""))[:70])
vals = dict(base_ok)
vals["Glucose"] = "120"
s, r = call("/api/predict/diabetes", {"values": vals})
check("validation", "numeric string '120' accepted", s == 200)
vals = dict(base_ok)
vals["unknown_extra"] = 5
s, r = call("/api/predict/diabetes", {"values": vals})
check("validation", "unknown extra field ignored", s == 200)
s, r = call("/api/predict/nope", {"values": {}})
check("validation", "unknown disease -> 404", s == 404)
s, r = call("/api/diseases/nope")
check("validation", "unknown disease detail -> 404", s == 404)
s, r = call("/api/predict/diabetes", raw=b"{not json")
check("validation", "malformed JSON -> 422", s == 422)
s, r = call("/api/predict/diabetes", method="GET")
check("validation", "GET on predict -> 405", s == 405)
s, r = call("/api/nothing-here")
check("validation", "unknown route -> 404", s == 404)

# ---- documented limits: no clinical range validation (recorded as observations, not failures)
vals = dict(base_ok)
vals["Glucose"] = 100000
s, r = call("/api/predict/diabetes", {"values": vals})
results.append({"group": "observation", "name": "Glucose = 100000 mg/dL is accepted (no range check)", "passed": s == 200,
                "detail": f"HTTP {s}, {r.get('result')} {r.get('probability')}%"})
vals = dict(base_ok)
vals["Age"] = -5
s, r = call("/api/predict/diabetes", {"values": vals})
results.append({"group": "observation", "name": "Age = -5 is accepted (no range check)", "passed": s == 200,
                "detail": f"HTTP {s}, {r.get('result')} {r.get('probability')}%"})
vals = dict(base_ok)
vals.update({"Glucose": 60, "BMI": 20, "Age": 25, "DiabetesPedigreeFunction": 0.1, "BloodPressure": 60})
low = call("/api/predict/diabetes", {"values": vals})[1]
vals.update({"Glucose": 220, "BMI": 45, "Age": 65, "DiabetesPedigreeFunction": 1.8, "BloodPressure": 100})
high = call("/api/predict/diabetes", {"values": vals})[1]
check("sanity", "clinically extreme low-risk vs high-risk diabetes input", low["positive"] is False and high["positive"] is True,
      f"low={low['result']} high={high['result']}")

# ---- latency on 127.0.0.1 (sequential, then 4 concurrent clients)
def timed(path, body=None):
    t0 = time.perf_counter()
    call(path, body)
    return (time.perf_counter() - t0) * 1000


lat = {}
for label, path, body in (("GET /api/health", "/api/health", None), ("GET /api/diseases", "/api/diseases", None),
                          ("GET /api/diseases/diabetes", "/api/diseases/diabetes", None),
                          ("POST /api/predict/diabetes", "/api/predict/diabetes", {"values": base_ok}),
                          ("POST /api/predict/heart", "/api/predict/heart", {"values": sample("heart", 1)})):
    for _ in range(10):
        timed(path, body)  # warm-up
    xs = sorted(timed(path, body) for _ in range(200))
    lat[label] = {"n": len(xs), "p50_ms": statistics.median(xs), "p95_ms": xs[int(0.95 * len(xs)) - 1], "max_ms": xs[-1],
                  "mean_ms": statistics.mean(xs)}
    print(label, {k: round(v, 2) for k, v in lat[label].items() if k != "n"})
with ThreadPoolExecutor(4) as ex:
    t0 = time.perf_counter()
    xs = list(ex.map(lambda _: timed("/api/predict/diabetes", {"values": base_ok}), range(200)))
    wall = time.perf_counter() - t0
xs.sort()
lat["POST /api/predict/diabetes (4 concurrent clients)"] = {"n": 200, "p50_ms": statistics.median(xs), "p95_ms": xs[189],
                                                           "max_ms": xs[-1], "mean_ms": statistics.mean(xs),
                                                           "throughput_rps": 200 / wall}

passed = sum(r["passed"] for r in results if r["group"] != "observation")
total = sum(1 for r in results if r["group"] != "observation")
print(f"\n{passed}/{total} checks passed")
json.dump({"passed": passed, "total": total, "checks": results, "latency": lat},
          open(os.path.join(ROOT, "docs", "experiments", "api_tests.json"), "w"), indent=1)
sys.exit(0 if passed == total else 1)
