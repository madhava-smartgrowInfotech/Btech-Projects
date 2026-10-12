"""End-to-end smoke test against the RUNNING backend (default http://127.0.0.1:8315).

Flow: login -> generate keypair -> send (sample PDF into a sample cover) -> analysis metrics -> receive via a
fresh upload of the stego PNG -> compare hashes -> robustness report -> wrong-key rejection -> log.
Uses only the standard library so it needs nothing beyond the project venv.
"""
import hashlib
import json
import os
import sys
import urllib.error
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
        parts = []
        for k, v in (fields or {}).items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
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
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            content = resp.read()
            return content if raw else json.loads(content)
    except urllib.error.HTTPError as exc:
        return {"_status": exc.code, "_detail": json.loads(exc.read() or b"{}").get("detail")}


def check(cond, msg):
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        sys.exit(1)


def main():
    global token
    r = call("POST", "/api/auth/login", {"username": "demo", "password": "Demo@12345"})
    token = r.get("token")
    check(bool(token), "login as demo user")

    key = call("POST", "/api/keys/generate", {"name": "smoke receiver", "bits": 3072})
    check(key.get("has_private") and key["bits"] == 3072, f"RSA-3072 keypair generated ({key['fingerprint']})")
    other = call("POST", "/api/keys/generate", {"name": "smoke other", "bits": 2048})

    pdf = ROOT / "data" / "payloads" / "confidential_memo.pdf"
    sent = call("POST", "/api/send", fields={"key_id": key["id"], "payload_sample": pdf.name,
                                             "cover_sample": "astronaut_512x512.png"})
    check("op_id" in sent, f"send: {sent.get('_detail', 'stego image produced')}")
    q = sent["quality"]
    check(q["psnr_db"] > 50, f"PSNR {q['psnr_db']} dB > 50")
    check(q["ssim"] > 0.999, f"SSIM {q['ssim']} close to 1")
    check(q["max_abs_change"] <= 1, "no pixel value moved by more than 1")
    check(sent["input_sha256"] == hashlib.sha256(pdf.read_bytes()).hexdigest(), "input hash recorded")

    ana = call("GET", f"/api/analysis/{sent['op_id']}")
    check(ana["capacity"]["bundle_bytes"] == sent["bundle_bytes"], "analysis endpoint returns capacity and timings")
    for img in ("histogram.png", "bitplanes.png"):
        png = call("GET", f"/api/analysis/{sent['op_id']}/{img}", raw=True)
        check(png[:8] == b"\x89PNG\r\n\x1a\n", f"{img} rendered")

    stego_png = call("GET", f"/api/ops/{sent['op_id']}/stego", raw=True)
    got = call("POST", "/api/receive", fields={"key_id": key["id"]}, files={"stego": ("received.png", stego_png)})
    check("op_id" in got, f"receive: {got.get('_detail', 'decrypted')}")
    restored = call("GET", f"/api/ops/{got['op_id']}/restored", raw=True)
    check(restored == pdf.read_bytes(), "restored file is byte-for-byte identical")
    check(got["output_sha256"] == sent["input_sha256"] == got["embedded_sha256"], "input and output hashes match")

    bad = call("POST", "/api/receive", fields={"key_id": other["id"]}, files={"stego": ("received.png", stego_png)})
    check(bad.get("_status") == 400, f"wrong private key rejected ({bad.get('_detail')})")

    plain = call("POST", "/api/receive", fields={"key_id": key["id"]},
                 files={"stego": ("cover.png", call("GET", f"/api/ops/{sent['op_id']}/cover", raw=True))})
    check(plain.get("_status") == 400, f"image with no payload rejected ({plain.get('_detail')})")

    rob = call("POST", f"/api/robustness/{sent['op_id']}")
    status = {r["attack"]: r["status"] for r in rob["results"]}
    check(status["png_resave"] == "recovered", "lossless re-save: payload survives")
    check(status["jpeg_q95"] == "lost" and status["jpeg_q50"] == "lost", "JPEG recompression: payload lost")
    check(status["noise_s1"] == "lost" and status["crop_left_10"] == "lost", "noise and left crop: payload lost")

    tiny = call("POST", "/api/send", fields={"key_id": key["id"], "payload_sample": pdf.name,
                                             "cover_sample": "coffee_small_200x200.png"})
    check(tiny.get("_status") == 400, f"capacity check blocks an oversized payload ({tiny.get('_detail')})")

    cap = call("GET", "/api/benchmark/capacity")
    check(len(cap) >= 5, f"capacity table for {len(cap)} covers")

    log = call("GET", "/api/log?limit=50")
    ops = {e["op"] for e in log}
    check({"key_generate", "send", "receive", "robustness"} <= ops, f"operation log has {sorted(ops)}")
    blob = json.dumps(log)
    check("PRIVATE KEY" not in blob and "BEGIN" not in blob, "no key material in the log")

    print("\nSMOKE TEST PASSED")


if __name__ == "__main__":
    main()
