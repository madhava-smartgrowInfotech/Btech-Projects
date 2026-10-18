"""
End-to-end smoke test for the FastAPI layer (standard library only).

Start the stack first (run.bat), then:

    python scripts/smoke_test.py            # backend on 8312
    python scripts/smoke_test.py --base http://localhost:5312   # through the Vite proxy
"""

import argparse
import http.cookiejar
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "dataset_sample")
DEMO = {"email": "demo@pneumodetect.ai", "password": "Pneumo@123"}

failures = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


class Client:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, method, path, body=None, headers=None, raw=False):
        req = urllib.request.Request(self.base + path, data=body, method=method, headers=headers or {})
        try:
            with self.opener.open(req, timeout=120) as r:
                data = r.read()
                return r.status, (data if raw else json.loads(data or b"null"))
        except urllib.error.HTTPError as e:
            data = e.read()
            try:
                return e.code, json.loads(data)
            except ValueError:
                return e.code, data

    def json(self, method, path, obj=None):
        body = json.dumps(obj).encode() if obj is not None else None
        return self.call(method, path, body, {"Content-Type": "application/json"} if body else None)

    def upload(self, filename, content):
        boundary = uuid.uuid4().hex
        ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"xray_image\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        return self.call("POST", "/api/predict", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8312")
    c = Client(ap.parse_args().base)

    s, h = c.json("GET", "/api/health")
    check("health is public and ok", s == 200 and h["status"] == "ok" and len(h["classes"]) == 3)

    s, who = c.json("GET", "/api/auth/me")
    check("me is null when signed out", s == 200 and who is None)
    s, _ = c.json("GET", "/api/predictions")
    check("history requires login (401)", s == 401)
    s, _ = c.json("POST", "/api/auth/login", {"email": DEMO["email"], "password": "wrong"})
    check("wrong password rejected (401)", s == 401)
    s, me = c.json("POST", "/api/auth/login", DEMO)
    check("demo login works", s == 200 and me["email"] == DEMO["email"])
    s, who = c.json("GET", "/api/auth/me")
    check("session cookie is accepted", s == 200 and who and who["email"] == DEMO["email"])

    s, before = c.json("GET", "/api/stats")
    check("stats readable", s == 200 and "by_class" in before)

    s, e = c.upload("notes.txt", b"hello")
    check("unsupported type rejected (400)", s == 400 and "Unsupported" in e["detail"], str(e))
    s, e = c.upload("broken.png", b"this is not an image")
    check("unreadable image rejected (400)", s == 400, str(e))
    s, e = c.upload("huge.png", b"\0" * (8 * 1024 * 1024 + 10))
    check("oversize upload rejected (413)", s == 413, str(e))

    samples = sorted(f for f in os.listdir(SAMPLES) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    check("sample X-rays present", len(samples) > 0, SAMPLES)
    first = None
    for name in samples:
        with open(os.path.join(SAMPLES, name), "rb") as f:
            s, rec = c.upload(name, f.read())
        probs = rec.get("probabilities", {}) if s == 201 else {}
        ok = s == 201 and abs(sum(probs.values()) - 1) < 1e-3 and rec["prediction"] in probs
        check(f"predict {name}", ok, str(rec)[:200])
        first = first or rec
        if s == 201:
            si, img = c.call("GET", rec["original_url"], raw=True)
            sh, heat = c.call("GET", rec["heatmap_url"], raw=True)
            check(f"images served for #{rec['id']}", si == 200 and sh == 200 and len(img) > 0 and len(heat) > 0)

    s, rows = c.json("GET", "/api/predictions")
    check("history lists new scans", s == 200 and len(rows) >= len(samples))
    if first:
        s, one = c.json("GET", f"/api/predictions/{first['id']}")
        check("single prediction fetch", s == 200 and one["id"] == first["id"])
    s, _ = c.json("GET", "/api/predictions/99999999")
    check("unknown id is 404", s == 404)

    s, after = c.json("GET", "/api/stats")
    check("stats total grew", s == 200 and after["total"] >= before["total"] + len(samples))

    s, rec = c.upload("tmp-delete.png", open(os.path.join(SAMPLES, samples[0]), "rb").read())
    s2, _ = c.json("DELETE", f"/api/predictions/{rec['id']}")
    s3, _ = c.json("GET", f"/api/predictions/{rec['id']}")
    check("delete removes a scan", s == 201 and s2 == 200 and s3 == 404)

    c.json("POST", "/api/auth/logout")
    s, _ = c.json("GET", "/api/predictions")
    check("logout ends the session", s == 401)

    print(f"\n{'ALL PASSED' if not failures else str(len(failures)) + ' FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
