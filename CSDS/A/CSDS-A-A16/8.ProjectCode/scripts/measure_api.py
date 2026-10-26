"""Measures the Mosaic REST API over real HTTP on 127.0.0.1 and runs malformed-input probes.

    python scripts/measure_api.py [http://127.0.0.1:8116]

Uses 127.0.0.1 on purpose ("localhost" adds ~2 s per call on this machine). Registers its own throw-away users.
Writes experiments/api_measurements/metrics.json.
"""
import io
import json
import statistics
import sys
import time
import uuid
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8116"
OUT = ROOT / "experiments" / "api_measurements" / "metrics.json"
S = requests.Session()
FACE = (ROOT / "docs/screenshots/inputs/happy_01.jpg").read_bytes()
NATIVE = (ROOT / "docs/screenshots/inputs/native48_happy.png").read_bytes()


def timed(label, fn, n):
    ms, code = [], None
    for _ in range(n):
        t = time.perf_counter()
        r = fn()
        ms.append((time.perf_counter() - t) * 1e3)
        code = r.status_code
    ms.sort()
    return {"label": label, "n": n, "status": code, "mean_ms": statistics.mean(ms), "p50_ms": ms[len(ms) // 2],
            "p95_ms": ms[max(int(len(ms) * 0.95) - 1, 0)], "max_ms": ms[-1]}


def probe(name, expect, fn):
    try:
        r = fn()
        ok = r.status_code in expect
        return {"name": name, "status": r.status_code, "expected": list(expect), "ok": bool(ok), "body": r.text[:140].replace("\n", " ")}
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "status": None, "expected": list(expect), "ok": False, "body": str(exc)[:140]}


def jpeg(w, h):
    b = io.BytesIO()
    Image.new("RGB", (w, h), (120, 120, 120)).save(b, format="JPEG")
    return b.getvalue()


def main():
    tag = uuid.uuid4().hex[:8]
    email, pw = f"probe_{tag}@example.com", "probe-pass-1"
    r = S.post(f"{BASE}/api/auth/register", json={"name": "Probe", "email": email, "password": pw})
    tok = r.json()["token"]
    H = {"Authorization": f"Bearer {tok}"}
    res = {"base": BASE}
    lat = [
        timed("GET /api/health", lambda: S.get(f"{BASE}/api/health"), 100),
        timed("POST /api/auth/login (bcrypt)", lambda: S.post(f"{BASE}/api/auth/login", json={"email": email, "password": pw}), 20),
        timed("GET /api/auth/me", lambda: S.get(f"{BASE}/api/auth/me", headers=H), 100),
        timed("POST /api/analyze anonymous (face)", lambda: S.post(f"{BASE}/api/analyze", files={"image": ("f.jpg", FACE, "image/jpeg")}), 60),
        timed("POST /api/analyze authenticated (face, persisted)", lambda: S.post(f"{BASE}/api/analyze", files={"image": ("f.jpg", FACE, "image/jpeg")}, headers=H), 60),
        timed("POST /api/analyze (no face found)", lambda: S.post(f"{BASE}/api/analyze", files={"image": ("n.png", NATIVE, "image/png")}), 40),
        timed("GET /api/history?limit=20", lambda: S.get(f"{BASE}/api/history?limit=20", headers=H), 60),
    ]
    big = jpeg(2000, 1500)
    lat.append(timed("POST /api/analyze (2000x1500 JPEG, no face)", lambda: S.post(f"{BASE}/api/analyze", files={"image": ("b.jpg", big, "image/jpeg")}), 10))
    res["latency"] = lat

    one = S.post(f"{BASE}/api/analyze", files={"image": ("f.jpg", FACE, "image/jpeg")}, headers=H).json()
    other = S.post(f"{BASE}/api/auth/register", json={"name": "Other", "email": f"other_{tag}@example.com", "password": pw}).json()["token"]
    OH = {"Authorization": f"Bearer {other}"}
    P = [
        probe("register duplicate email -> 409", [409], lambda: S.post(f"{BASE}/api/auth/register", json={"name": "P", "email": email, "password": pw})),
        probe("register 5-char password -> 422", [422], lambda: S.post(f"{BASE}/api/auth/register", json={"name": "P", "email": f"x{tag}@e.com", "password": "12345"})),
        probe("register missing field -> 422", [422], lambda: S.post(f"{BASE}/api/auth/register", json={"email": "a@b.com"})),
        probe("register with e-mail 'not-an-email' accepted?", [201, 422], lambda: S.post(f"{BASE}/api/auth/register", json={"name": "P", "email": f"not-an-email-{tag}", "password": pw})),
        probe("login wrong password -> 401", [401], lambda: S.post(f"{BASE}/api/auth/login", json={"email": email, "password": "wrong-pass"})),
        probe("login SQL-looking e-mail -> 401", [401], lambda: S.post(f"{BASE}/api/auth/login", json={"email": "' OR 1=1 --", "password": "x"})),
        probe("malformed JSON -> 422", [422], lambda: S.post(f"{BASE}/api/auth/login", data="{oops", headers={"Content-Type": "application/json"})),
        probe("/me without token -> 401", [401], lambda: S.get(f"{BASE}/api/auth/me")),
        probe("/me tampered token -> 401", [401], lambda: S.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {tok[:-4]}abcd"})),
        probe("history without token -> 401", [401], lambda: S.get(f"{BASE}/api/history")),
        probe("history item of another user -> 404", [404], lambda: S.get(f"{BASE}/api/history/{one['id']}", headers=OH)),
        probe("delete item of another user -> 404", [404], lambda: S.delete(f"{BASE}/api/history/{one['id']}", headers=OH)),
        probe("history limit=-5", [200, 422, 500], lambda: S.get(f"{BASE}/api/history?limit=-5", headers=H)),
        probe("history limit=100000", [200], lambda: S.get(f"{BASE}/api/history?limit=100000", headers=H)),
        probe("history limit=abc -> 422", [422], lambda: S.get(f"{BASE}/api/history?limit=abc", headers=H)),
        probe("analyze without file -> 422", [422], lambda: S.post(f"{BASE}/api/analyze")),
        probe("analyze with a text file", [200, 400, 415, 422, 500], lambda: S.post(f"{BASE}/api/analyze", files={"image": ("x.txt", b"hello", "text/plain")})),
        probe("analyze with an empty file", [200, 400, 415, 422, 500], lambda: S.post(f"{BASE}/api/analyze", files={"image": ("e.jpg", b"", "image/jpeg")})),
        probe("analyze with truncated JPEG", [200, 400, 415, 422, 500], lambda: S.post(f"{BASE}/api/analyze", files={"image": ("t.jpg", FACE[:200], "image/jpeg")})),
        probe("analyze 6000x6000 JPEG (decode cost)", [200], lambda: S.post(f"{BASE}/api/analyze", files={"image": ("h.jpg", jpeg(6000, 6000), "image/jpeg")})),
        probe("path traversal in thumbnail URL", [400, 404], lambda: S.get(f"{BASE}/api/media/thumbs/..%2f..%2fapp%2fconfig.py")),
        probe("unknown endpoint -> 404", [404], lambda: S.get(f"{BASE}/api/nope")),
        probe("wrong method on /api/health -> 405", [405], lambda: S.post(f"{BASE}/api/health")),
        probe("CORS preflight from an unlisted origin", [200, 400], lambda: S.options(f"{BASE}/api/analyze", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})),
    ]
    cors = S.options(f"{BASE}/api/analyze", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    res["cors_unlisted_origin_allow_origin_header"] = cors.headers.get("access-control-allow-origin")
    cors2 = S.options(f"{BASE}/api/analyze", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    res["cors_listed_origin_allow_origin_header"] = cors2.headers.get("access-control-allow-origin")
    res["probes"] = P
    res["probes_ok"] = sum(p["ok"] for p in P)
    res["probes_total"] = len(P)
    res["healthy_after_probes"] = S.get(f"{BASE}/api/health").status_code == 200
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print("probes ok %d/%d healthy=%s" % (res["probes_ok"], res["probes_total"], res["healthy_after_probes"]))
    for l in lat:
        print("%-55s p50 %.1f ms p95 %.1f ms" % (l["label"], l["p50_ms"], l["p95_ms"]))
    for p in P:
        print(("ok  " if p["ok"] else "FAIL"), p["name"], p["status"], p["body"][:60])


if __name__ == "__main__":
    main()
