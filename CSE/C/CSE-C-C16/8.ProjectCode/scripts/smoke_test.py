"""End-to-end smoke test of the AgriVision API (register, login, detect, history, exports, analytics, delete).

It starts its own backend on a spare port with a throw-away database and upload folder, so your real data in
agrivision/agrivision.db is never touched.   Usage:  python scripts/smoke_test.py
Exit code 0 = every check passed.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("SMOKE_PORT", "18416"))
BASE = f"http://127.0.0.1:{PORT}"
results: list[tuple[bool, str]] = []


def check(ok: bool, label: str, extra: str = "") -> None:
    results.append((ok, label))
    print(("PASS " if ok else "FAIL ") + label + (f"  [{extra}]" if extra and not ok else ""))


def call(method: str, path: str, body=None, token: str | None = None, raw: bool = False, headers: dict | None = None):
    h = dict(headers or {})
    data = None
    if body is not None and not isinstance(body, bytes):
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    elif isinstance(body, bytes):
        data = body
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = r.read()
            return r.status, (payload if raw else json.loads(payload or b"null")), r.headers
    except urllib.error.HTTPError as e:
        payload = e.read()
        try:
            return e.code, (payload if raw else json.loads(payload or b"null")), e.headers
        except ValueError:
            return e.code, payload, e.headers


def multipart(filename: str, content: bytes, fields: dict[str, str]) -> tuple[bytes, dict]:
    boundary = uuid.uuid4().hex
    out = io.BytesIO()
    for k, v in fields.items():
        out.write(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    out.write(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode())
    out.write(b"Content-Type: application/octet-stream\r\n\r\n" + content + b"\r\n")
    out.write(f"--{boundary}--\r\n".encode())
    return out.getvalue(), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def leaf_image() -> bytes:
    """A real PlantDoc test leaf when the dataset is present, else a synthetic green leaf with brown blight spots."""
    d = ROOT / "datasets" / "plantdoc-images" / "test" / "Tomato_leaf_late_blight"
    if d.is_dir():
        for p in sorted(d.iterdir()):
            if p.suffix.lower() in (".jpg", ".jpeg", ".png") and p.stat().st_size < 5_000_000:
                return p.read_bytes()
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (256, 256), (40, 120, 50))
    draw = ImageDraw.Draw(img)
    for x, y in [(60, 70), (150, 100), (110, 170), (190, 190)]:
        draw.ellipse((x - 18, y - 14, x + 18, y + 14), fill=(120, 70, 30))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="agrivision_smoke_"))
    env = dict(os.environ, AGRIVISION_DB=str(tmp / "smoke.db"), AGRIVISION_UPLOADS=str(tmp / "uploads"), PYTHONHASHSEED="0")
    log = open(tmp / "server.log", "w")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(60):
            try:
                if call("GET", "/api/health")[0] == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            print("Backend did not start. Log:\n" + (tmp / "server.log").read_text()[-1500:])
            return 2

        s, h, _ = call("GET", "/api/health")
        check(s == 200 and h["status"] == "ok" and h["classes"] == 38, "health reports 38 classes", str(h))
        check(h["engine"] in ("heuristic",) or h["trained_model"], "health names the diagnosis engine", str(h))

        s, ds, _ = call("GET", "/api/v1/diseases")
        check(s == 200 and len(ds) == 38, "disease guide lists 38 entries")
        check(all(len(d["treatments"]) == 3 for d in ds), "every disease has chemical/organic/cultural treatments")
        s, d1, _ = call("GET", "/api/v1/diseases/" + urllib.request.quote("Tomato___Late_blight"))
        check(s == 200 and d1["severity"] == "high", "disease detail by class name")
        check(call("GET", "/api/v1/diseases/nope")[0] == 404, "unknown disease is 404")

        check(call("GET", "/api/v1/history")[0] == 401, "history needs sign-in (401)")
        check(call("POST", "/api/v1/auth/login", {"email": "demo@agrivision.ai", "password": "wrong"})[0] == 401, "wrong password is 401")
        s, lg, _ = call("POST", "/api/v1/auth/login", {"email": "demo@agrivision.ai", "password": "demo1234"})
        check(s == 200 and lg["token"] and lg["user"]["email"] == "demo@agrivision.ai", "demo login works")
        token = lg["token"]
        s, me, _ = call("GET", "/api/v1/auth/me", token=token)
        check(s == 200 and me["full_name"] == "Demo Farmer", "me returns the profile")

        email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
        s, rg, _ = call("POST", "/api/v1/auth/register", {"email": email, "password": "secret12", "full_name": "Smoke Tester", "crop": "potato"})
        check(s == 201 and rg["token"], "register creates an account and signs in")
        check(call("POST", "/api/v1/auth/register", {"email": email, "password": "secret12"})[0] == 409, "duplicate email is 409")
        check(call("POST", "/api/v1/auth/register", {"email": "bad", "password": "secret12"})[0] == 400, "invalid email is 400")
        check(call("POST", "/api/v1/auth/register", {"email": "x@y.zz", "password": "123"})[0] == 400, "short password is 400")
        other = rg["token"]

        s, up, _ = call("PUT", "/api/v1/profile", {"full_name": "Demo Farmer", "region": "Maharashtra", "language": "hi", "crops": ["tomato", "grape"]}, token=token)
        check(s == 200 and up["language"] == "hi" and up["crops"] == ["tomato", "grape"], "profile update saves language and crops")
        call("PUT", "/api/v1/profile", {"full_name": "Demo Farmer", "region": "Maharashtra", "language": "en", "crops": ["tomato", "potato"]}, token=token)
        check(call("PUT", "/api/v1/profile", {"language": "xx"}, token=token)[0] == 400, "unsupported language is 400")

        body, hd = multipart("leaf.jpg", leaf_image(), {"crop_type": "tomato"})
        check(call("POST", "/api/v1/detect/upload", body, headers=hd)[0] == 401, "detect needs sign-in")
        b2, h2 = multipart("notes.txt", b"hello", {"crop_type": "tomato"})
        check(call("POST", "/api/v1/detect/upload", b2, token=token, headers=h2)[0] == 400, "non-image extension is rejected")
        b3, h3 = multipart("broken.jpg", b"this is not an image", {"crop_type": "tomato"})
        check(call("POST", "/api/v1/detect/upload", b3, token=token, headers=h3)[0] == 400, "corrupt image is rejected cleanly")
        s, det, _ = call("POST", "/api/v1/detect/upload", body, token=token, headers=hd)
        check(s == 200 and det["result_id"] and len(det["top_3_predictions"]) == 3, "detect returns a result with top-3")
        check(0 < det["confidence"] <= 1 and det["severity"] in ("high", "medium", "low", "none"), "confidence and severity are valid")
        check(len(det["recommendations"]["treatments"]) == 3, "detect returns treatments")
        rid = det["result_id"]

        s, one, _ = call("GET", f"/api/v1/history/{rid}", token=token)
        check(s == 200 and one["result_id"] == rid and one["disease_details"]["treatments"], "result detail loads")
        check(len(one["top_3_predictions"]) == 3 and one["crop_type"] == "tomato", "result detail has top-3 and crop")
        s, img, _ = call("GET", one["image_url"], raw=True)
        check(s == 200 and len(img) > 100, "leaf image is served")
        check(call("GET", f"/api/v1/history/{rid}", token=other)[0] == 404, "another user cannot open the result")

        s, hist, _ = call("GET", "/api/v1/history?limit=10", token=token)
        check(s == 200 and any(r["result_id"] == rid for r in hist["results"]) and hist["total_count"] >= 1, "history lists the new scan")
        s, none, _ = call("GET", "/api/v1/history?q=zzzzzz", token=token)
        check(s == 200 and none["total_count"] == 0, "history search with no match is empty")
        name_part = det["predicted_disease"].split(" ")[0]
        s, hit, _ = call("GET", "/api/v1/history?q=" + urllib.request.quote(name_part), token=token)
        check(hit["total_count"] >= 1, "history search finds the scan")
        s, dis, _ = call("GET", "/api/v1/history?disease=healthy", token=token)
        s2, dis2, _ = call("GET", "/api/v1/history?disease=diseased", token=token)
        check(dis["total_count"] + dis2["total_count"] == hist["all_count"], "healthy + diseased filters add up to all scans")

        s, csv1, hdr = call("GET", f"/api/v1/history/{rid}/export?format=csv", token=token, raw=True)
        check(s == 200 and b"result_id" in csv1 and rid.encode() in csv1, "single-record CSV export")
        s, pdf, _ = call("GET", f"/api/v1/history/{rid}/export?format=pdf", token=token, raw=True)
        check(s == 200 and pdf[:4] == b"%PDF", "single-record PDF export")
        s, csv_all, _ = call("GET", "/api/v1/history/export", token=token, raw=True)
        check(s == 200 and rid.encode() in csv_all, "all-history CSV export")

        s, an, _ = call("GET", "/api/v1/analytics/dashboard", token=token)
        check(s == 200 and an["total_detections"] == hist["all_count"] and sum(an["severity"].values()) == an["total_detections"], "analytics totals match history")
        check(sum(t["count"] for t in an["timeline"]) == an["total_detections"], "timeline adds up")
        s, dash, _ = call("GET", "/api/v1/dashboard", token=token)
        check(s == 200 and dash["total"] == an["total_detections"] and len(dash["recent"]) >= 1, "dashboard stats and recent list")

        check(call("DELETE", f"/api/v1/history/{rid}", token=other)[0] == 404, "another user cannot delete the result")
        check(call("DELETE", f"/api/v1/history/{rid}", token=token)[0] == 200, "delete removes the record")
        check(call("GET", f"/api/v1/history/{rid}", token=token)[0] == 404, "deleted result is gone")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()

    failed = [label for ok, label in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED:", *failed, sep="\n  - ")
        print("Server log:", tmp / "server.log")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
