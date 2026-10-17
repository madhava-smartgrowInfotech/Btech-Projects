"""
API smoke test for SecurePay AI. Run with the backend up:  python scripts/smoke_test.py [base_url]
Default base URL is the Vite dev server (so the /api proxy is exercised too); pass
http://127.0.0.1:8304 to hit Flask directly. Read-only unless --full is given
(--full also regenerates a small dataset, preprocesses and trains, which overwrites models/).
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (args[0] if args else "http://127.0.0.1:5304").rstrip("/")
FULL = "--full" in sys.argv
results = []


def call(method, path, body=None, raw=False, headers=None):
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = r.read()
            return r.status, (data if raw else json.loads(data))
    except urllib.error.HTTPError as e:
        data = e.read()
        try:
            return e.code, json.loads(data)
        except ValueError:
            return e.code, data


def post_json(path, payload):
    return call("POST", path, json.dumps(payload).encode(), headers={"Content-Type": "application/json"})


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  - ' + str(detail)) if detail and not ok else ''}")


# ---- read-only endpoints -------------------------------------------------
s, d = call("GET", "/api/health")
check("health", s == 200 and d["status"] == "ok" and d["data_rows"] > 0, d)
models = d.get("models_trained", []) if s == 200 else []

s, d = call("GET", "/api/dataset_info")
check("dataset_info", s == 200 and d["rows"] == d["fraud_count"] + d["legit_count"] and len(d["head"]) == 5, d)

s, d = call("GET", "/api/dataset_stats")
check("dataset_stats", s == 200 and len(d["by_hour"]) == 24 and d["by_merchant"] and d["amount_buckets"], d)

s, d = call("GET", "/api/comparison")
check("comparison", s == 200 and isinstance(d, list) and len(d) >= 1 and "F1-Score" in d[0], d)

s, d = call("GET", "/api/train_status")
check("train_status", s == 200 and set(d) <= {"classical", "sa", "qa"}, d)

s, d = call("GET", "/api/model_history")
check("model_history", s == 200 and all("f1" in v for v in d.values()), d)

s, d = call("GET", "/api/feature_importance")
check("feature_importance", s == 200 and d["importance"] and d["columns"], d)

for m in models:
    s, d = call("GET", f"/api/qubo?mode={m}")
    check(f"qubo {m}", s == 200 and len(d["Q"]) == d["display_size"], d)

# ---- predictions ---------------------------------------------------------
fraud = {"Amount": 1200, "Merchant_Category": "Online", "Transaction_Type": "Online", "Card_Present": 0,
         "Country_Match": 0, "Time": 54000, "V3": 1.8, "V14": -1.1, "V17": 1.4}
legit = {"Amount": 80, "Merchant_Category": "Grocery", "Transaction_Type": "Chip", "Card_Present": 1,
         "Country_Match": 1, "Time": 54000, "V3": 0, "V14": 0, "V17": 0}
s, hi = post_json("/api/predict_single", {**fraud, "mode": "ensemble"})
check("predict_single ensemble (fraud example)", s == 200 and 0 <= hi["fraud_probability"] <= 1 and hi["risk_level"] in ("LOW", "MEDIUM", "HIGH"), hi)
s, lo = post_json("/api/predict_single", {**legit, "mode": "ensemble"})
check("predict_single ensemble (legit example)", s == 200 and lo["fraud_probability"] < hi["fraud_probability"], (lo, hi))
for m in models:
    s, d = post_json("/api/predict_single", {**fraud, "mode": m})
    check(f"predict_single {m}", s == 200 and "fraud_probability" in d, d)
s, d = post_json("/api/predict_single", {**fraud, "mode": "nope"})
check("predict_single unknown mode -> 404 with error", s == 404 and "error" in d, d)

sample = ROOT / "data" / "sample_batch.csv"
boundary = uuid.uuid4().hex
payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"sample_batch.csv\"\r\n"
           f"Content-Type: text/csv\r\n\r\n").encode() + sample.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
s, d = call("POST", "/api/predict_batch", payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
check("predict_batch", s == 200 and d["rows"] == 20 and len(d["preview"]) == 10 and d["metrics"] is not None, d)
s, d = call("POST", "/api/predict_batch", b"", headers={"Content-Type": "application/json"})
check("predict_batch without file -> 400", s == 400 and "error" in d, d)

s, d = call("GET", "/api/export_predictions", raw=True)
check("export_predictions (csv)", s == 200 and b"Fraud_Probability" in d[:4000], s)
s, d = call("GET", "/api/sample_batch", raw=True)
check("sample_batch download", s == 200 and d.startswith(b"Amount,"), s)

# ---- optional mutating flow ----------------------------------------------
if FULL:
    s, d = post_json("/api/generate_dataset", {"n_fraud": 500, "n_legit": 500})
    check("generate_dataset (--full)", s == 200 and d["rows"] == 1000, d)
    s, d = post_json("/api/preprocess", {"method": "manual", "top_k": 18})
    check("preprocess (--full)", s == 200 and len(d["columns"]) == 18, d)
    s, d = post_json("/api/train", {"modes": ["classical"], "epochs": 2})
    check("train (--full)", s == 200 and "classical" in d and "confusion_matrix" in d["classical"]["metrics"], d)

print(f"\n{sum(results)}/{len(results)} checks passed against {BASE}")
sys.exit(0 if all(results) else 1)
