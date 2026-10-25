"""Measure the combined cost of one protected transfer: ThreatSense scoring + SecureChannel encryption + cloud decryption.

Part A runs in-process against the shipped models. Part B (optional, needs the backend running on 127.0.0.1)
times the same operations through the HTTP API. Output: experiments/pipeline/metrics.json

    python scripts/measure_pipeline.py            # part A only
    python scripts/measure_pipeline.py --api      # part A + part B (backend must be running)
"""
import torch  # noqa: F401  (must be the first heavy import on this Windows host)
import argparse
import base64
import json
import os
import statistics
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cipherguard.crypto.secure_channel import KeyPair, SecureChannel  # noqa: E402
from cipherguard.ids.features import FEATURE_NAMES  # noqa: E402
from cipherguard.ids.inference import ThreatSenseEngine  # noqa: E402

ATTACK = {"proto": "tcp", "service": "ftp", "state": "RST", "dur": 3.5, "sbytes": 85000, "dbytes": 1200, "rate": 95000,
          "spkts": 35, "dpkts": 4, "ct_srv_src": 12, "ct_dst_ltm": 15}
NORMAL = {"proto": "tcp", "service": "http", "state": "CON", "dur": 0.3, "sbytes": 900, "dbytes": 700, "rate": 12000,
          "spkts": 7, "dpkts": 5, "ct_srv_src": 1, "ct_dst_ltm": 1}


def stats(ts):
    ts = sorted(ts)
    return {"median_ms": statistics.median(ts), "p95_ms": ts[int(0.95 * (len(ts) - 1))], "min_ms": ts[0], "n": len(ts)}


def timed(fn, reps):
    out = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        out.append((time.perf_counter() - t0) * 1000)
    return stats(out)


def full(rec):
    base = {f: 0 for f in FEATURE_NAMES}
    base.update({"proto": "tcp", "service": "http", "state": "CON"})
    base.update(rec)
    return base


def part_a():
    eng = ThreatSenseEngine(models_dir=ROOT / "models")
    t0 = time.perf_counter()
    eng.load()
    load_ms = (time.perf_counter() - t0) * 1000
    cloud = KeyPair.generate()
    payload = os.urandom(100 * 1024)
    rec = full(NORMAL)
    for _ in range(5):  # warm-up
        eng.score_single(rec)
    enc = SecureChannel.encrypt_with_ephemeral(payload, cloud.public_key)

    def decrypt():
        eph = KeyPair.load_public_from_bytes(base64.b64decode(enc["ephemeral_public"]))
        key = SecureChannel.derive_session_key(cloud.private_key, eph)
        SecureChannel.decrypt(base64.b64decode(enc["ciphertext"]), base64.b64decode(enc["nonce"]), base64.b64decode(enc["tag"]), key)

    def transfer():
        eng.score_single(rec)
        SecureChannel.encrypt_with_ephemeral(payload, cloud.public_key)
        decrypt()

    res = {"engine_load_ms": load_ms,
           "ids_score_single": timed(lambda: eng.score_single(rec), 200),
           "encrypt_100kb": timed(lambda: SecureChannel.encrypt_with_ephemeral(payload, cloud.public_key), 200),
           "decrypt_100kb": timed(decrypt, 200),
           "protected_transfer_100kb": timed(transfer, 200)}
    sample = pd.read_csv(ROOT / "frontend" / "public" / "samples" / "sample_flows.csv")
    res["ids_batch_120_rows"] = timed(lambda: eng.predict_proba(sample.copy()), 30)
    syn = pd.read_csv(ROOT / "data" / "raw" / "synthetic_demo.csv").head(1000)
    res["ids_batch_1000_rows"] = timed(lambda: eng.predict_proba(syn.copy()), 10)
    ids, e, d = (res[k]["median_ms"] for k in ("ids_score_single", "encrypt_100kb", "decrypt_100kb"))
    res["share_of_transfer_median"] = {"ids": ids / (ids + e + d), "encrypt": e / (ids + e + d), "decrypt": d / (ids + e + d)}
    return res


def part_b(base):
    import httpx
    c = httpx.Client(base_url=base, timeout=120)
    res = {}
    c.get("/api/health")
    res["health"] = timed(lambda: c.get("/api/health"), 100)
    res["score_single"] = timed(lambda: c.post("/api/ids/score", json=ATTACK), 100)
    c.delete("/api/alerts")
    msg = "x" * 1024
    res["encrypt_1kb_text"] = timed(lambda: c.post("/api/crypto/encrypt", json={"plaintext": msg}), 100)
    e = c.post("/api/crypto/encrypt", json={"plaintext": msg}).json()
    fields = {k: e[k] for k in ("ciphertext", "nonce", "tag", "ephemeral_public")}
    res["decrypt_1kb_text"] = timed(lambda: c.post("/api/crypto/decrypt", json=fields), 100)
    blob = os.urandom(1024 * 1024)
    res["encrypt_file_1mb"] = timed(lambda: c.post("/api/crypto/encrypt-file", files={"file": ("blob.bin", blob, "application/octet-stream")}), 20)
    sample = (ROOT / "frontend" / "public" / "samples" / "sample_flows.csv").read_bytes()
    res["score_batch_120_rows"] = timed(lambda: c.post("/api/ids/score-batch", files={"file": ("s.csv", sample, "text/csv")}), 30)

    def seq():
        c.post("/api/ids/score", json=NORMAL)
        r = c.post("/api/crypto/encrypt", json={"plaintext": msg}).json()
        c.post("/api/crypto/decrypt", json={k: r[k] for k in ("ciphertext", "nonce", "tag", "ephemeral_public")})

    res["protected_transfer_via_api_1kb"] = timed(seq, 60)
    c.delete("/api/alerts")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", action="store_true")
    ap.add_argument("--port", default="8305")
    a = ap.parse_args()
    out = {"in_process": part_a()}
    if a.api:
        out["api_127_0_0_1"] = part_b(f"http://127.0.0.1:{a.port}")
    dest = ROOT / "experiments" / "pipeline"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))
