"""Measure real response times of the running API (start it first: run.bat).

    python scripts/measure_api_latency.py [http://localhost:8314]

Writes experiments/churn_synthetic/api_latency.json. Standard library only.
"""
import json
import os
import statistics
import sys
import time
import urllib.request
import uuid

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8314").rstrip("/")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = None


def call(method, path, body=None, multipart=None):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    data = None
    if multipart:
        b = uuid.uuid4().hex
        parts = [f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="x.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode() + multipart + b"\r\n"]
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="include_drivers"\r\n\r\nfalse\r\n'.encode())
        data = b"".join(parts) + f"--{b}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={b}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
    return (time.perf_counter() - t) * 1000, json.loads(raw) if raw[:1] in (b"{", b"[") else raw


env = {}
for line in open(os.path.join(ROOT, ".env"), encoding="utf8"):
    if "=" in line and not line.startswith("#"):
        k, v = line.strip().split("=", 1)
        env[k] = v
_, tok = call("POST", "/api/auth/login", {"email": env["DEMO_EMAIL"], "password": env["DEMO_PASSWORD"]})
TOKEN = tok["token"]

out = {"base": BASE, "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "once_ms": {}, "repeated_ms": {}}
out["once_ms"]["load_sample"] = round(call("POST", "/api/data/sample")[0], 1)
out["once_ms"]["prepare"] = round(call("POST", "/api/data/prepare")[0], 1)
out["once_ms"]["train_3_models"] = round(call("POST", "/api/models/train", {"test_size": 0.2, "imbalance_strategy": "class_weight",
                                          "models": ["Logistic Regression", "Decision Tree", "Random Forest"], "selection_metric": "f1_score"})[0], 1)
out["once_ms"]["save_model"] = round(call("POST", "/api/models/save", {"name": "Logistic Regression"})[0], 1)
time.sleep(4)  # background importance warm-up

_, cust = call("GET", "/api/customers?limit=5")
cid = cust["rows"][0]["id"]
_, tpl = call("GET", "/api/batch/template")
_, big = call("GET", "/api/data/preview?rows=1")  # just to know the endpoint is alive
paths = {
    "health": ("GET", "/api/health", None),
    "state": ("GET", "/api/state", None),
    "dashboard": ("GET", "/api/dashboard", None),
    "risk_table_all": ("GET", "/api/risk", None),
    "customer_360": ("GET", f"/api/customers/{cid}", None),
    "xai_global": ("GET", "/api/xai/global", None),
    "xai_local": ("GET", f"/api/xai/local/{cid}", None),
    "whatif": ("POST", "/api/whatif", {"customer_id": cid, "changes": {"Contract": "Two year"}}),
    "retention": ("GET", "/api/retention?risk=High%20Risk,Critical%20Risk&limit=50", None),
    "eda": ("GET", "/api/eda", None),
    "evaluation": ("GET", "/api/evaluation", None),
}
for name, (m, p, b) in paths.items():
    ts = []
    for _ in range(10):
        ts.append(call(m, p, b)[0])
    out["repeated_ms"][name] = {"median": round(statistics.median(ts), 1), "max": round(max(ts), 1), "runs": 10}
tsb = [call("POST", "/api/batch/predict", multipart=tpl)[0] for _ in range(5)]
out["repeated_ms"]["batch_predict_25_rows_no_drivers"] = {"median": round(statistics.median(tsb), 1), "max": round(max(tsb), 1), "runs": 5}

os.makedirs(os.path.join(ROOT, "experiments", "churn_synthetic"), exist_ok=True)
with open(os.path.join(ROOT, "experiments", "churn_synthetic", "api_latency.json"), "w", encoding="utf8") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps(out, indent=2))
