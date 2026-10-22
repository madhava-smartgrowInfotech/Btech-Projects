"""Measure API latency and batch throughput of the running product, on 127.0.0.1 (localhost adds ~2 s per call here).

    .venv\\Scripts\\python scripts\\measure_api.py [model.pkl ...]

For each model it starts its own backend on port 8498 (FAKENEWS_MODEL=<model>), measures start-up time to /api/health,
then 300 sequential POST /api/predict calls (client round trip + the latency_ms the server reports), then batch runs of
100 / 1,000 / 2,296 real LIAR2 test statements. Writes experiments/liar2/latency.json. Run it while the PC is idle.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8498
URL = f"http://127.0.0.1:{PORT}"


def post_json(path, body):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def post_csv(path, csv_bytes, column):
    boundary = uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="column"\r\n\r\n{column}\r\n').encode()
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="b.csv"\r\nContent-Type: text/csv\r\n\r\n').encode() + csv_bytes + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(URL + path, data=body, method="POST", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def measure(model_path):
    env = dict(os.environ, FAKENEWS_MODEL=model_path)
    t0 = time.time()
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(PORT)], cwd=ROOT, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(180):
            try:
                urllib.request.urlopen(URL + "/api/health", timeout=2).read()
                break
            except Exception:
                time.sleep(0.25)
        startup = time.time() - t0
        te = pd.read_csv(os.path.join(ROOT, "data", "liar2", "test.csv"))
        texts = te["statement"].fillna("").astype(str).tolist()
        for t in texts[:10]:  # warm-up
            post_json("/api/predict", {"text": t})
        client, server = [], []
        for t in texts[:300]:
            a = time.perf_counter()
            r = post_json("/api/predict", {"text": t})
            client.append((time.perf_counter() - a) * 1000)
            server.append(r["latency_ms"])
        out = {"model": os.path.basename(model_path), "startup_s": round(startup, 2),
               "predict_client_ms": {"n": len(client), "mean": float(np.mean(client)), "p50": float(np.percentile(client, 50)), "p95": float(np.percentile(client, 95)), "max": float(np.max(client))},
               "predict_server_ms": {"mean": float(np.mean(server)), "p50": float(np.percentile(server, 50)), "p95": float(np.percentile(server, 95)), "max": float(np.max(server))}}
        batches = {}
        for n in (100, 1000, 2296):
            df = pd.DataFrame({"statement": texts[:n]})
            a = time.perf_counter()
            r = post_csv("/api/batch/run", df.to_csv(index=False).encode(), "statement")
            batches[str(n)] = {"client_s": round(time.perf_counter() - a, 2), "server_s": r["seconds"], "rows": r["n_rows"]}
        out["batch"] = batches
        return out
    finally:
        srv.terminate()
        time.sleep(1)


def main():
    models = sys.argv[1:] or [os.path.join(ROOT, "models", "liar2_msvm_model.pkl"), os.path.join(ROOT, "models", "msvm_model.pkl")]
    res = [measure(m) for m in models]
    for r in res:
        print(json.dumps(r, indent=1))
    json.dump(res, open(os.path.join(ROOT, "experiments", "liar2", "latency.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
