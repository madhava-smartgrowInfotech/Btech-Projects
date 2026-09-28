"""End-to-end smoke test against the running API (start it with run.bat or uvicorn first).

  venv\\Scripts\\python scripts\\smoke_test.py
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
PORT = os.getenv("BACKEND_PORT", "8210")
API = f"http://127.0.0.1:{PORT}/api"
WS = f"ws://127.0.0.1:{PORT}/api"


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        sys.exit(1)


def flip_bit(key_hex):
    b = bytearray(bytes.fromhex(key_hex))
    b[0] ^= 1
    return b.hex()


def main():
    check(requests.get(f"{API}/health", timeout=5).json()["status"] == "ok", "backend is healthy")
    r = requests.post(f"{API}/auth/login", json={"email": os.getenv("DEMO_EMAIL", "demo@skycipher.app"),
                                                 "password": os.getenv("DEMO_PASSWORD", "SkyCipher@2026")})
    check(r.status_code == 200, "demo login")
    token = r.json()["token"]
    H = {"Authorization": f"Bearer {token}"}

    email = f"op{int(time.time())}@skycipher.app"
    r = requests.post(f"{API}/auth/register", json={"name": "Field Operator", "email": email, "password": "secret123"})
    check(r.status_code == 200 and requests.get(f"{API}/auth/me", headers={"Authorization": "Bearer " + r.json()["token"]}).ok,
          "register + /me")

    samples = requests.get(f"{API}/samples").json()
    drone = [s for s in samples if s["kind"] == "visdrone"]
    sipi = [s for s in samples if s["kind"] == "sipi"]
    check(len(drone) >= 50 and len(sipi) >= 3, f"samples available ({len(drone)} drone, {len(sipi)} test images)")

    # F1/F2 encrypt -> decrypt, checksum must match
    r = requests.post(f"{API}/studio/encrypt", headers=H, data={"sample_kind": "visdrone", "sample_name": drone[0]["name"]})
    check(r.status_code == 200, f"encrypt drone image ({r.status_code})")
    enc = r.json()
    job, key = enc["job"], enc["key"]
    check(set(enc["subbands"]) == {"LL", "LH", "HL", "HH"} and "cipher" in enc["histograms"], "sub-bands + histograms returned")
    r = requests.post(f"{API}/studio/decrypt", headers=H, data={"job_id": job["id"], "key": key}).json()
    check(r["match"] is True and r["sha256"] == job["plain_sha256"], "decrypt with right key is bit-identical")
    r = requests.post(f"{API}/studio/decrypt", headers=H, data={"job_id": job["id"], "key": flip_bit(key)}).json()
    check(r["match"] is False, "1-bit wrong key fails to decrypt")
    png = requests.get(f"{API}/studio/jobs/{job['id']}/cipher.png", headers=H)
    r = requests.post(f"{API}/studio/decrypt", headers=H, data={"key": key, "nonce": job["nonce"]},
                      files={"file": ("cipher.png", png.content, "image/png")}).json()
    check(r["sha256"] == job["plain_sha256"], "downloaded cipher PNG decrypts to the same checksum")

    # F3 security lab + export
    r = requests.post(f"{API}/lab/analyze", headers=H, data={"sample_kind": "sipi", "sample_name": sipi[0]["name"]})
    check(r.status_code == 200, "security analysis")
    rep = r.json()
    print(f"     entropy={rep['entropy']['cipher']['mean']:.4f} NPCR={rep['differential']['npcr']:.3f} "
          f"UACI={rep['differential']['uaci']:.3f} corr_h={rep['correlation']['cipher']['horizontal']:.4f}")
    check(rep["entropy"]["cipher"]["mean"] > 7.99, "cipher entropy > 7.99")
    check(rep["differential"]["npcr"] > 99.5 and 33.0 < rep["differential"]["uaci"] < 34.0, "NPCR / UACI near ideal")
    check(all(abs(rep["correlation"]["cipher"][d]) < 0.01 for d in ("horizontal", "vertical", "diagonal")), "cipher correlation ~ 0")
    check(rep["quality"]["decrypted"]["identical"] and not rep["key_sensitivity"]["wrong_key_recovers"], "lossless + key sensitive")

    # F4 attacks
    r = requests.post(f"{API}/attacks/run", headers=H, data={"sample_kind": "visdrone", "sample_name": drone[1]["name"],
                                                             "report_id": rep["id"]}).json()
    check(len(r["results"]) >= 5, "attack suite ran")
    for a in r["results"]:
        print(f"     {a['label']:<28} PSNR={a['recovered']['psnr']:.2f} dB intact={a['recovered']['intact_pct']:.1f}%")
    html = requests.get(f"{API}/lab/reports/{rep['id']}/export?fmt=html", headers=H)
    js = requests.get(f"{API}/lab/reports/{rep['id']}/export?fmt=json", headers=H)
    check(html.ok and "NPCR" in html.text and "Attack tests" in html.text and js.ok and "attacks" in js.json(), "report export (HTML + JSON)")

    # F6 benchmark
    r = requests.post(f"{API}/bench/run", headers=H, json={"size": 256, "images": 2, "repeats": 1})
    check(r.ok and {x["algorithm"] for x in r.json()["results"]} == {"SkyCipher", "AES-256-CTR", "ChaCha20"}, "benchmark vs AES / ChaCha20")

    # F5 live link: ground station connects, built-in UAV sender streams a sequence
    seqs = requests.get(f"{API}/live/sequences", headers=H).json()
    check(len(seqs) >= 2, "drone sequences available")
    frames = []
    with connect(f"{WS}/live/ground?token={token}", max_size=None) as ws:
        ws.send(json.dumps({"key": key}))
        check(json.loads(ws.recv()).get("ready"), "ground station ready")
        r = requests.post(f"{API}/live/start", headers=H, json={"sequence": seqs[0]["name"], "key": key, "fps": 15, "width": 480})
        check(r.ok, "UAV sender started")
        t0 = time.time()
        while len(frames) < 20 and time.time() - t0 < 30:
            frames.append(json.loads(ws.recv(timeout=10)))
    requests.post(f"{API}/live/stop", headers=H)
    last = frames[-1]
    print(f"     frames={len(frames)} fps={last['fps']:.1f} latency={last['latency_ms']:.1f} ms "
          f"throughput={last['throughput_mbps']:.1f} Mbit/s enc={last['enc_ms']:.1f} ms dec={last['dec_ms']:.1f} ms")
    check(len(frames) == 20 and all(f["key_match"] for f in frames) and last["fps"] > 5, "live encrypted stream decoded at ground station")

    print("\nALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
