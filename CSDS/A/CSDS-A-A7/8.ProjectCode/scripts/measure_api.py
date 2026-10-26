"""Measure the running SHEGUARD API: latency, WebSocket push delay, access control, input handling and evidence
integrity. Writes experiments/study/api_metrics.json. Needs the backend on 127.0.0.1:8107 (use 127.0.0.1, not
localhost: on this machine localhost adds ~2 s of IPv6 fallback per call).

    venv\\Scripts\\python.exe scripts\\measure_api.py
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import statistics as st
import time
import uuid
from pathlib import Path

import httpx
import websockets

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "study"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8107"
WS = "ws://127.0.0.1:8107"
N = 30


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def summarise(ms):
    return {"n": len(ms), "mean_ms": round(st.mean(ms), 1), "median_ms": round(st.median(ms), 1),
            "p95_ms": round(pct(ms, 95), 1), "max_ms": round(max(ms), 1)}


def timed(fn, n=N):
    out = []
    for _ in range(n):
        t = time.perf_counter()
        r = fn()
        out.append((time.perf_counter() - t) * 1000)
    return out, r


def new_user(c, tag):
    email = f"{tag}_{uuid.uuid4().hex[:8]}@sheguard-test.app"
    r = c.post("/api/auth/register", json={"name": f"Study {tag}", "email": email, "password": "StudyPass1"})
    r.raise_for_status()
    return email, r.json()["access_token"]


def main():
    res = {"base": BASE}
    c = httpx.Client(base_url=BASE, timeout=60)
    email_a, tok_a = new_user(c, "a")
    email_b, tok_b = new_user(c, "b")
    ha = {"Authorization": f"Bearer {tok_a}"}
    hb = {"Authorization": f"Bearer {tok_b}"}

    # ------------------------------------------------------------- latency
    lat = {}
    lat["GET /api/health"] = summarise(timed(lambda: c.get("/api/health"))[0])
    lat["GET /api/risk/areas (467 rows)"] = summarise(timed(lambda: c.get("/api/risk/areas"))[0])
    lat["POST /api/auth/login (bcrypt)"] = summarise(timed(lambda: c.post("/api/auth/login", json={"email": email_a, "password": "StudyPass1"}), 15)[0])
    lat["GET /api/auth/me"] = summarise(timed(lambda: c.get("/api/auth/me", headers=ha))[0])
    gj = {"name": "G", "phone": "+910000000001", "email": None, "telegram_chat_id": None}
    lat["POST /api/guardians"] = summarise(timed(lambda: c.post("/api/guardians", json=gj, headers=ha))[0])
    lat["GET /api/guardians"] = summarise(timed(lambda: c.get("/api/guardians", headers=ha))[0])
    sos_ms, r = timed(lambda: c.post("/api/sos/start", json={"lat": 17.385, "lng": 78.4867, "trigger": "manual"}, headers=ha), 15)
    lat["POST /api/sos/start (30 guardians, no channel configured)"] = summarise(sos_ms)
    sess = r.json()
    sid, token = sess["session_id"], sess["share_token"]
    lat["POST /api/sos/{id}/location"] = summarise(timed(lambda: c.post(f"/api/sos/{sid}/location", json={"lat": 17.386, "lng": 78.487}, headers=ha))[0])
    lat["GET /api/track/{token} (public)"] = summarise(timed(lambda: c.get(f"/api/track/{token}"))[0])
    for label, size in (("100 KB", 100_000), ("1 MB", 1_000_000), ("5 MB", 5_000_000)):
        blob = os.urandom(size)
        ms, _ = timed(lambda: c.post(f"/api/sos/{sid}/evidence", data={"kind": "photo", "lat": "17.386", "lng": "78.487"},
                                     files={"file": ("p.jpg", blob, "image/jpeg")}, headers=ha), 10)
        lat[f"POST /api/sos/{{id}}/evidence ({label})"] = summarise(ms)
    ms, _ = timed(lambda: c.get(f"/api/sos/{sid}/evidence", headers=ha))
    lat["GET /api/sos/{id}/evidence"] = summarise(ms)
    ms, rr = timed(lambda: c.post("/api/routes/plan", json={"origin_lat": 17.385, "origin_lng": 78.4867, "dest_lat": 16.5062, "dest_lng": 80.648}, headers=ha), 5)
    lat["POST /api/routes/plan (live OSRM + 467-district scoring)"] = summarise(ms)
    res["latency"] = lat

    # ------------------------------------------------------------- websocket push delay
    async def ws_test(viewers):
        conns = []
        for _ in range(viewers):
            conns.append(await websockets.connect(f"{WS}/ws/track/{token}"))
        delays = []
        async with httpx.AsyncClient(base_url=BASE, timeout=30, headers=ha) as ac:
            for i in range(N):
                t0 = time.perf_counter()
                await ac.post(f"/api/sos/{sid}/location", json={"lat": 17.4 + i * 1e-4, "lng": 78.5})
                msgs = await asyncio.gather(*[asyncio.wait_for(w.recv(), 5) for w in conns])
                delays.append((time.perf_counter() - t0) * 1000)
                assert all(json.loads(m)["type"] == "location" for m in msgs)
        for w in conns:
            await w.close()
        return delays

    res["websocket"] = {"one_viewer_post_to_receive": summarise(asyncio.run(ws_test(1))),
                        "five_viewers_post_to_all_received": summarise(asyncio.run(ws_test(5)))}

    async def ws_unknown():
        try:
            w = await websockets.connect(f"{WS}/ws/track/{'0' * 32}")
            await w.close()
            return "accepted"
        except Exception as e:  # noqa: BLE001
            return f"rejected: {e!r}"
    res["websocket"]["unknown_token_connection"] = asyncio.run(ws_unknown())

    # ------------------------------------------------------------- access control
    ac = {}
    sx = lambda rsp: rsp.status_code  # noqa: E731
    ac["no token: GET /api/guardians"] = sx(c.get("/api/guardians"))
    ac["no token: POST /api/sos/start"] = sx(c.post("/api/sos/start", json={"lat": 1, "lng": 1}))
    ac["no token: POST /api/ai/ask"] = sx(c.post("/api/ai/ask", json={"question": "hi"}))
    ac["no token: POST /api/routes/plan"] = sx(c.post("/api/routes/plan", json={"origin_lat": 1, "origin_lng": 1, "dest_lat": 2, "dest_lng": 2}))
    ac["forged token: GET /api/auth/me"] = sx(c.get("/api/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}))
    ac["tampered signature: GET /api/auth/me"] = sx(c.get("/api/auth/me", headers={"Authorization": f"Bearer {tok_a[:-4]}AAAA"}))
    ac["user B reads user A session"] = sx(c.get(f"/api/sos/{sid}", headers=hb))
    ac["user B pushes location to A session"] = sx(c.post(f"/api/sos/{sid}/location", json={"lat": 1, "lng": 1}, headers=hb))
    ac["user B cancels A session"] = sx(c.post(f"/api/sos/{sid}/cancel", headers=hb))
    ac["user B lists A evidence"] = sx(c.get(f"/api/sos/{sid}/evidence", headers=hb))
    ac["user B uploads evidence to A session"] = sx(c.post(f"/api/sos/{sid}/evidence", data={"kind": "photo"}, files={"file": ("a.jpg", b"x", "image/jpeg")}, headers=hb))
    gid = c.get("/api/guardians", headers=ha).json()[0]["id"]
    ac["user B edits A guardian"] = sx(c.put(f"/api/guardians/{gid}", json=gj, headers=hb))
    ac["user B deletes A guardian"] = sx(c.delete(f"/api/guardians/{gid}", headers=hb))
    ac["user B sees A guardians in own list (count)"] = len(c.get("/api/guardians", headers=hb).json())
    ac["public track with wrong token"] = sx(c.get("/api/track/" + "f" * 32))
    ac["public track with right token"] = sx(c.get(f"/api/track/{token}"))
    ac["public GET /api/risk/areas without login"] = sx(c.get("/api/risk/areas"))
    # evidence file URL
    ev = c.get(f"/api/sos/{sid}/evidence", headers=ha).json()[0]
    rel = None
    for p in (ROOT / "data" / "evidence" / str(sid)).glob("*"):
        rel = f"/evidence-files/{sid}/{p.name}"
        break
    ac["GET stored evidence file with no token"] = sx(c.get(rel)) if rel else None
    ac["guessing evidence file with session id only"] = sx(c.get(f"/evidence-files/{sid}/0000000000000000.jpg"))
    res["access_control"] = ac

    # ------------------------------------------------------------- input handling
    ih = {}
    ih["register: 5-char password"] = sx(c.post("/api/auth/register", json={"name": "x", "email": "a@b.co", "password": "12345"}))
    ih["register: 6-char password 'aaaaaa' (accepted = no strength rule)"] = sx(c.post("/api/auth/register", json={"name": "x", "email": f"w{uuid.uuid4().hex[:6]}@b.co", "password": "aaaaaa"}))
    ih["register: bad email"] = sx(c.post("/api/auth/register", json={"name": "x", "email": "nope", "password": "123456"}))
    ih["register: duplicate email"] = sx(c.post("/api/auth/register", json={"name": "x", "email": email_a, "password": "StudyPass1"}))
    ih["login: wrong password"] = sx(c.post("/api/auth/login", json={"email": email_a, "password": "wrong"}))
    wrong = [c.post("/api/auth/login", json={"email": email_a, "password": f"guess{i}"}).status_code for i in range(25)]
    ih["login: 25 consecutive wrong passwords (status set)"] = sorted(set(wrong))
    ih["sos/start: latitude 999 (accepted = no range check)"] = sx(c.post("/api/sos/start", json={"lat": 999, "lng": 999, "trigger": "whatever"}, headers=ha))
    ih["sos/start: missing lat"] = sx(c.post("/api/sos/start", json={"lng": 1}, headers=ha))
    ih["evidence: kind=video"] = sx(c.post(f"/api/sos/{sid}/evidence", data={"kind": "video"}, files={"file": ("a.mp4", b"x", "video/mp4")}, headers=ha))
    ih["evidence: empty file"] = sx(c.post(f"/api/sos/{sid}/evidence", data={"kind": "photo"}, files={"file": ("a.jpg", b"", "image/jpeg")}, headers=ha))
    big = os.urandom(20_000_000)
    t = time.perf_counter()
    rbig = c.post(f"/api/sos/{sid}/evidence", data={"kind": "audio"}, files={"file": ("a.webm", big, "audio/webm")}, headers=ha)
    ih["evidence: 20 MB upload (accepted = no size limit)"] = {"status": rbig.status_code, "seconds": round(time.perf_counter() - t, 2)}
    html = b"<html><script>document.title='x'</script></html>"
    rh = c.post(f"/api/sos/{sid}/evidence", data={"kind": "photo"}, files={"file": ("page.html", html, "text/html")}, headers=ha)
    served = None
    for p in (ROOT / "data" / "evidence" / str(sid)).glob("*.html"):
        rs = c.get(f"/evidence-files/{sid}/{p.name}")
        served = {"status": rs.status_code, "content_type": rs.headers.get("content-type")}
    ih["evidence: .html file labelled photo, served back"] = {"upload": rh.status_code, "served": served}
    c.post(f"/api/sos/{sid}/cancel", headers=ha)
    ih["location push after cancel"] = sx(c.post(f"/api/sos/{sid}/location", json={"lat": 1, "lng": 1}, headers=ha))
    ih["track page after cancel (still readable)"] = sx(c.get(f"/api/track/{token}"))
    ih["track page exposes path points"] = len(c.get(f"/api/track/{token}").json()["path"])
    ih["ai/ask: empty body"] = sx(c.post("/api/ai/ask", json={}, headers=ha))
    res["input_handling"] = ih

    # ------------------------------------------------------------- evidence integrity
    ev_rows = c.get(f"/api/sos/{sid}/evidence", headers=ha).json()
    first = ev_rows[0]
    path = next((ROOT / "data" / "evidence" / str(sid)).glob(first["sha256"][:16] + ".*"))
    data = path.read_bytes()
    ok = hashlib.sha256(data).hexdigest() == first["sha256"]
    tampered = bytearray(data)
    tampered[len(tampered) // 2] ^= 0x01
    bad = hashlib.sha256(bytes(tampered)).hexdigest() == first["sha256"]
    t = time.perf_counter()
    for _ in range(20):
        hashlib.sha256(os.urandom(1_000_000)).hexdigest()
    hash_ms = (time.perf_counter() - t) / 20 * 1000
    res["evidence_integrity"] = {
        "stored_hash_matches_file": ok, "hash_matches_after_one_bit_flip": bad,
        "sha256_hex_length": len(first["sha256"]), "sha256_1MB_ms": round(hash_ms, 2),
        "verify_endpoint_exists": c.get(f"/api/sos/{sid}/evidence/{first['id']}/verify", headers=ha).status_code != 404,
    }
    import sys
    sys.path.insert(0, str(ROOT))
    from backend.app import config  # reads the same .env the server read
    res["jwt_secret_is_default_value"] = config.JWT_SECRET == "dev-secret-change-me"
    (OUT / "api_metrics.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
