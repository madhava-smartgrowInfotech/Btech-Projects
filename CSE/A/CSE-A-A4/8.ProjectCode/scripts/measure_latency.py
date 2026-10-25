"""
Latency of the running API. Writes experiments/latency.json.

Start the backend first (python backend/app.py), then:  python scripts/measure_latency.py [http://127.0.0.1:8304]
Uses 127.0.0.1 rather than localhost (the name lookup adds about 2 s per call on this PC).
"""
import json
import pathlib
import statistics
import sys
import time
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8304").rstrip("/")

FRAUD = {"Amount": 1200, "Merchant_Category": "Online", "Transaction_Type": "Online", "Card_Present": 0,
         "Country_Match": 0, "Time": 54000, "V3": 1.8, "V14": -1.1, "V17": 1.4, "mode": "ensemble"}
LEGIT = {"Amount": 80, "Merchant_Category": "Grocery", "Transaction_Type": "Chip", "Card_Present": 1,
         "Country_Match": 1, "Time": 54000, "V3": 0, "V14": 0, "V17": 0, "mode": "ensemble"}


def post_json(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()
    return (time.perf_counter() - t) * 1000


def get(path):
    t = time.perf_counter()
    with urllib.request.urlopen(BASE + path, timeout=120) as r:
        r.read()
    return (time.perf_counter() - t) * 1000


def post_csv(path, csv_path):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"f.csv\"\r\n"
            f"Content-Type: text/csv\r\n\r\n").encode() + pathlib.Path(csv_path).read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        r.read()
    return (time.perf_counter() - t) * 1000


def summarise(xs):
    xs = sorted(xs)
    return {"n": len(xs), "mean_ms": statistics.mean(xs), "median_ms": statistics.median(xs),
            "p95_ms": xs[int(0.95 * (len(xs) - 1))], "min_ms": xs[0], "max_ms": xs[-1]}


def main():
    out = {"base": BASE}
    for _ in range(5):
        post_json("/api/predict_single", FRAUD)  # warm-up
    for label, payload in (("predict_single_fraud_example", FRAUD), ("predict_single_legit_example", LEGIT)):
        out[label] = summarise([post_json("/api/predict_single", payload) for _ in range(100)])
    for m in ("classical", "sa", "qa"):
        out[f"predict_single_{m}"] = summarise([post_json("/api/predict_single", {**FRAUD, "mode": m}) for _ in range(50)])
    out["predict_batch_20_rows"] = summarise([post_csv("/api/predict_batch", ROOT / "data" / "sample_batch.csv") for _ in range(20)])
    out["health"] = summarise([get("/api/health") for _ in range(50)])
    out["dataset_stats"] = summarise([get("/api/dataset_stats") for _ in range(10)])
    out["model_history"] = summarise([get("/api/model_history") for _ in range(20)])
    out["feature_importance"] = summarise([get("/api/feature_importance") for _ in range(20)])
    (ROOT / "experiments").mkdir(exist_ok=True)
    (ROOT / "experiments" / "latency.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        if isinstance(v, dict):
            print(f"{k:34s} median {v['median_ms']:8.1f} ms   p95 {v['p95_ms']:8.1f} ms")


if __name__ == "__main__":
    main()
