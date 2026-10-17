"""End-to-end smoke test for CipherGuard Shield.

Usage (backend running; add the React dev server to also check the /api proxy):
    python scripts/smoke_test.py                      # backend on BACKEND_PORT from .env (8305)
    python scripts/smoke_test.py --frontend           # also checks the Vite proxy on FRONTEND_PORT (5305)
Exit code 0 = every check passed.
"""
import argparse
import base64
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def env_value(key: str, default: str) -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return default


results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))


def run(base: str, label: str) -> None:
    c = httpx.Client(base_url=base, timeout=60)
    print(f"\n== {label}: {base} ==")

    r = c.get("/api/health")
    check("GET /api/health", r.status_code == 200 and r.json().get("status") == "ok")
    check("engine loaded", r.json().get("engine_loaded") is True, "models/ artifacts load with the installed scikit-learn")

    r = c.get("/api/metrics")
    m = r.json() if r.status_code == 200 else {}
    check("GET /api/metrics", r.status_code == 200 and 0.5 < m.get("accuracy", 0) <= 1, f"accuracy={m.get('accuracy')}")

    c.delete("/api/alerts")
    attack = {"proto": "tcp", "service": "ftp", "state": "RST", "dur": 3.5, "sbytes": 85000, "dbytes": 1200, "rate": 95000,
              "spkts": 35, "dpkts": 4, "ct_srv_src": 12, "ct_dst_ltm": 15}
    normal = {"proto": "tcp", "service": "http", "state": "CON", "dur": 0.3, "sbytes": 900, "dbytes": 700, "rate": 12000,
              "spkts": 7, "dpkts": 5, "ct_srv_src": 1, "ct_dst_ltm": 1}
    r = c.post("/api/ids/score", json=attack)
    check("score attack preset -> attack", r.status_code == 200 and r.json()["label"] == "attack", str(r.json().get("severity")))
    r = c.post("/api/ids/score", json=normal)
    check("score normal preset -> normal", r.status_code == 200 and r.json()["label"] == "normal")

    sample = ROOT / "frontend" / "public" / "samples" / "sample_flows.csv"
    with open(sample, "rb") as f:
        r = c.post("/api/ids/score-batch", files={"file": ("sample_flows.csv", f, "text/csv")})
    b = r.json() if r.status_code == 200 else {}
    check("POST /api/ids/score-batch", r.status_code == 200 and b.get("total") == 120, f"{b.get('attack_count')} attacks / {b.get('normal_count')} normal")
    r = c.post("/api/ids/score-batch", files={"file": ("x.txt", b"hello", "text/plain")})
    check("batch rejects non-CSV (400)", r.status_code == 400)

    r = c.get("/api/alerts", params={"limit": 500})
    check("GET /api/alerts has entries", r.status_code == 200 and r.json()["total"] >= 1, f"total={r.json().get('total')}")
    r = c.delete("/api/alerts")
    check("DELETE /api/alerts", r.status_code == 200 and c.get("/api/alerts").json()["total"] == 0)

    msg = "smoke test payload"
    r = c.post("/api/crypto/encrypt", json={"plaintext": msg})
    e = r.json() if r.status_code == 200 else {}
    check("POST /api/crypto/encrypt", r.status_code == 200 and len(base64.b64decode(e["nonce"])) == 12 and len(base64.b64decode(e["tag"])) == 16)
    r = c.post("/api/crypto/decrypt", json={k: e[k] for k in ("ciphertext", "nonce", "tag", "ephemeral_public")})
    check("decrypt round-trip", r.status_code == 200 and r.json()["plaintext"] == msg and r.json()["verified"] is True)
    bad = base64.b64decode(e["ciphertext"])
    bad = base64.b64encode(bytes([bad[0] ^ 1]) + bad[1:]).decode()
    r = c.post("/api/crypto/decrypt", json={"ciphertext": bad, "nonce": e["nonce"], "tag": e["tag"], "ephemeral_public": e["ephemeral_public"]})
    check("tampered ciphertext rejected (400)", r.status_code == 400)
    r = c.post("/api/crypto/encrypt", json={"plaintext": ""})
    check("empty plaintext rejected (400)", r.status_code == 400)
    r = c.post("/api/crypto/encrypt-file", files={"file": ("note.txt", b"file bytes to protect", "text/plain")})
    fe = r.json() if r.status_code == 200 else {}
    check("POST /api/crypto/encrypt-file", r.status_code == 200 and fe.get("original_size") == 21)
    r = c.post("/api/crypto/decrypt", json={k: fe[k] for k in ("ciphertext", "nonce", "tag", "ephemeral_public")})
    check("file decrypt round-trip", r.status_code == 200 and r.json()["plaintext"] == "file bytes to protect")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontend", action="store_true", help="also test through the Vite dev/preview proxy")
    a = ap.parse_args()
    run(f"http://127.0.0.1:{env_value('BACKEND_PORT', '8305')}", "backend")
    if a.frontend:
        fp = env_value("FRONTEND_PORT", "5305")
        run(f"http://127.0.0.1:{fp}", "frontend proxy")
        r = httpx.get(f"http://127.0.0.1:{fp}/")
        check("React app served", r.status_code == 200 and '<div id="root">' in r.text)
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)
