"""Measure end-to-end API latency against the RUNNING backend (127.0.0.1:8315, standard library only).

Each call is repeated and the median and 95th percentile are written to experiments/extra/api_latency.json.
Uses 127.0.0.1 rather than localhost: on this Windows machine localhost adds about 2 s per call to a Python client.
"""
import json
import os
import statistics
import time
import urllib.request
import uuid
from pathlib import Path

BASE = os.getenv("CIPHERVEIL_URL", "http://127.0.0.1:8315")
ROOT = Path(__file__).resolve().parents[1]
token = None


def call(method, path, body=None, fields=None, files=None, raw=False):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = None
    if fields is not None or files is not None:
        boundary = uuid.uuid4().hex
        parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                 for k, v in (fields or {}).items()]
        for k, (fname, content) in (files or {}).items():
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{fname}"\r\n'
                          "Content-Type: application/octet-stream\r\n\r\n").encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=300) as resp:
        content = resp.read()
        return content if raw else json.loads(content)


def timed(fn, n):
    ms = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        ms.append((time.perf_counter() - t) * 1000)
    ms.sort()
    return {"n": n, "median_ms": round(statistics.median(ms), 1), "p95_ms": round(ms[min(len(ms) - 1, int(0.95 * len(ms)))], 1),
            "min_ms": round(ms[0], 1), "max_ms": round(ms[-1], 1)}


def main():
    global token
    results = {}
    results["login"] = timed(lambda: call("POST", "/api/auth/login", {"username": "demo", "password": "Demo@12345"}), 10)
    token = call("POST", "/api/auth/login", {"username": "demo", "password": "Demo@12345"})["token"]
    results["health"] = timed(lambda: call("GET", "/api/health"), 20)
    for bits in (2048, 3072):
        results[f"keys/generate {bits}"] = timed(lambda b=bits: call("POST", "/api/keys/generate", {"name": f"lat{b}", "bits": b}), 5)
    results["keys/generate 4096"] = timed(lambda: call("POST", "/api/keys/generate", {"name": "lat4096", "bits": 4096}), 3)
    key = call("POST", "/api/keys/generate", {"name": "latency key", "bits": 3072})
    results["keys list"] = timed(lambda: call("GET", "/api/keys"), 10)

    sent = {}

    def send():
        sent.update(call("POST", "/api/send", fields={"key_id": key["id"], "payload_sample": "confidential_memo.pdf",
                                                      "cover_sample": "astronaut_512x512.png"}))
    results["send (21 KiB memo, 512x512 cover, RSA-3072)"] = timed(send, 10)

    def send_big():
        call("POST", "/api/send", fields={"key_id": key["id"], "payload_sample": "confidential_memo.pdf",
                                          "cover_sample": "generated_landscape_1280x720.png"})
    results["send (21 KiB memo, 1280x720 cover)"] = timed(send_big, 10)

    stego = call("GET", f"/api/ops/{sent['op_id']}/stego", raw=True)
    results["download stego PNG"] = timed(lambda: call("GET", f"/api/ops/{sent['op_id']}/stego", raw=True), 10)
    results["receive (RSA-3072)"] = timed(lambda: call("POST", "/api/receive", fields={"key_id": key["id"]},
                                                        files={"stego": ("r.png", stego)}), 10)
    results["analysis metrics"] = timed(lambda: call("GET", f"/api/analysis/{sent['op_id']}"), 10)
    fresh = []
    for _ in range(3):
        s = call("POST", "/api/send", fields={"key_id": key["id"], "payload_sample": "accounts.csv", "cover_sample": "rocket_640x427.png"})
        t = time.perf_counter()
        call("GET", f"/api/analysis/{s['op_id']}/histogram.png", raw=True)
        call("GET", f"/api/analysis/{s['op_id']}/bitplanes.png", raw=True)
        fresh.append((time.perf_counter() - t) * 1000)
    results["histogram + bit planes, first render"] = {"n": 3, "median_ms": round(statistics.median(fresh), 1), "max_ms": round(max(fresh), 1)}
    results["robustness (9 attacks)"] = timed(lambda: call("POST", f"/api/robustness/{sent['op_id']}"), 5)
    results["benchmark/capacity"] = timed(lambda: call("GET", "/api/benchmark/capacity"), 5)
    results["benchmark/run (6 covers x 3 sizes, RSA-2048)"] = timed(lambda: call("POST", "/api/benchmark/run"), 2)
    results["log (100 rows)"] = timed(lambda: call("GET", "/api/log?limit=100"), 10)

    out = ROOT / "experiments" / "extra"
    out.mkdir(parents=True, exist_ok=True)
    (out / "api_latency.json").write_text(json.dumps(results, indent=2))
    for k, v in results.items():
        print(f"{k:55s} median {v['median_ms']:9.1f} ms   n={v['n']}")


if __name__ == "__main__":
    main()
