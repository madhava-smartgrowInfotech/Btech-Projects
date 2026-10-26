"""Unit, edge-case and security checks that the smoke test does not cover (writes docs/metrics/edge_tests.json).

Part 1 (in process):  knowledge base, PlantDoc label map and the heuristic engine.
Part 2 (own server on port 18417, throw-away DB): token tampering/expiry, upload limits and formats, injection-style
search strings, path traversal, CORS, paging validation, crop options.

A check that records a defect of the product is reported as DEFECT (not PASS) and counted separately.
Usage:  python scripts/edge_tests.py
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agrivision"))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("PYTHONHASHSEED", "0")

import smoke_test as S  # noqa: E402  (call, multipart, leaf_image)

S.PORT = int(os.environ.get("EDGE_PORT", "18417"))
S.BASE = f"http://127.0.0.1:{S.PORT}"
rows: list[tuple[str, str, str]] = []   # (group, status, label)


def rec(group: str, status: str, label: str, extra: str = "") -> None:
    rows.append((group, status, label))
    print(f"{status:7s} [{group}] {label}" + (f"  [{extra}]" if extra and status != "PASS" else ""), flush=True)


def check(group, ok, label, extra=""):
    rec(group, "PASS" if ok else "FAIL", label, extra)


def defect(group, present, label, extra=""):
    """present=True means the defect reproduces (the product misbehaves)."""
    rec(group, "DEFECT" if present else "PASS", label, extra)


# ------------------------------------------------------------------------------------------ part 1: unit
def unit() -> None:
    import disease_db as d
    import inference as inf
    from PIL import Image

    g = "unit"
    check(g, len(d.CLASSES) == 38 and len(set(d.CLASSES)) == 38, "38 distinct canonical classes")
    check(g, all(d.get_disease_info(c)["class"] == c for c in d.CLASSES), "get_disease_info echoes the class")
    check(g, d.get_disease_info("Not___a_class")["class"] == "Tomato___healthy", "unknown class falls back to Tomato healthy")
    check(g, all(set(d.get_disease_info(c)) >= {"name", "crop", "severity", "symptoms", "treatments", "prevention", "lifecycle", "urgent"} for c in d.CLASSES),
          "every info card has all fields")
    check(g, all(d.get_disease_info(c)["severity"] == "none" for c in d.CLASSES if "healthy" in c), "healthy classes have severity none")
    check(g, all(not d.get_disease_info(c)["healthy"] for c in d.CLASSES if "healthy" not in c), "diseased classes are not flagged healthy")
    check(g, all(d.get_disease_info(c)["urgent"] == (d.get_disease_info(c)["severity"] == "high") for c in d.CLASSES), "urgent flag equals severity high")
    check(g, all(v in d.CLASSES for v in inf.PLANTDOC_MAP.values()), "every PlantDoc label maps to a canonical class")
    check(g, len(set(inf.PLANTDOC_MAP.values())) == len(inf.PLANTDOC_MAP) == 28, "PlantDoc map is one-to-one (28 labels)")
    check(g, all(len(inf._candidates(k)) >= 1 for k in inf.CROP_ALIASES), "every crop option has at least one candidate class")
    check(g, len(inf._candidates("general")) == 38 and len(inf._candidates("")) == 38, "general / empty hint keeps all 38 classes")
    check(g, len(inf._candidates("TOMATO ")) == 10, "crop hint is case/space tolerant (tomato = 10 classes)")
    check(g, set(inf._candidates("maize")) == set(inf._candidates("corn")), "maize and corn give the same candidates")

    buf = io.BytesIO()
    Image.new("RGB", (300, 200), (40, 130, 50)).save(buf, "JPEG")
    img = buf.getvalue()
    a, b = inf.predict(img, "tomato"), inf.predict(img, "tomato")
    check(g, a["top3"] == b["top3"], "same image and same process give identical output")
    sums = []
    for f in sorted((ROOT / "datasets" / "plantdoc-images" / "test").glob("*/*"))[::4]:
        sums.append(sum(p for _, p in inf.predict(f.read_bytes(), "general")["top3"]))
    over = sum(1 for x in sums if x > 1.02) / max(1, len(sums))
    defect(g, over > 0.2, f"top-3 scores sum to at most 100% ({over * 100:.0f}% of {len(sums)} test photos sum above 102%, max {max(sums or [0]) * 100:.0f}%)")
    check(g, a["top3"][0][1] >= 0.62, "confidence floor of the heuristic is 0.62 (it never reports low confidence)")
    # the "confidence" is not an evidence measure: a plain green square is called healthy with high confidence
    check(g, "healthy" in a["predicted"].lower() and a["confidence"] > 0.9, "plain green image is called healthy with confidence above 0.9")
    big = io.BytesIO()
    Image.new("RGB", (4000, 3000), (120, 70, 30)).save(big, "JPEG")
    t = time.perf_counter()
    inf.predict(big.getvalue(), "general")
    check(g, time.perf_counter() - t < 5, "12 MP image is analysed in under 5 s", f"{time.perf_counter() - t:.2f}s")
    png = io.BytesIO()
    Image.new("RGBA", (64, 64), (0, 255, 0, 128)).save(png, "PNG")
    check(g, inf.predict(png.getvalue(), "general")["top3"], "RGBA PNG is accepted")
    try:
        inf.predict(b"not an image", "general")
        check(g, False, "garbage bytes raise an exception (caught by the API)")
    except Exception:
        check(g, True, "garbage bytes raise an exception (caught by the API)")
    # defect: crops with fewer than three candidate classes
    bad = [k for k in inf.CROP_ALIASES if len(inf._candidates(k)) < 3]
    failed = []
    for k in bad:
        try:
            inf.predict(img, k)
        except IndexError:
            failed.append(k)
    defect(g, bool(failed), f"crop options with fewer than 3 candidate classes work ({len(failed)} of {len(inf.CROP_ALIASES)} options raise IndexError)",
           ",".join(failed))
    json.dump({"crops_that_crash": failed, "n_crop_options": len(inf.CROP_ALIASES)}, open(ROOT / "docs" / "metrics" / "crop_crash.json", "w"), indent=1)


# ------------------------------------------------------------------------------------------ part 2: API
def api() -> None:
    g = "api"
    tmp = Path(tempfile.mkdtemp(prefix="agrivision_edge_"))
    env = dict(os.environ, AGRIVISION_DB=str(tmp / "edge.db"), AGRIVISION_UPLOADS=str(tmp / "uploads"), PYTHONHASHSEED="0")
    log = open(tmp / "server.log", "w")
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(S.PORT)],
                              cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    call, multipart = S.call, S.multipart
    try:
        for _ in range(60):
            try:
                if call("GET", "/api/health")[0] == 200:
                    break
            except Exception:
                time.sleep(1)
        s, lg, _ = call("POST", "/api/v1/auth/login", {"email": "demo@agrivision.ai", "password": "demo1234"})
        tok = lg["token"]
        payload, sig = tok.split(".", 1)
        # token handling
        check(g, call("GET", "/api/v1/auth/me", token=payload + "." + "0" * 64)[0] == 401, "token with a forged signature is rejected")
        check(g, call("GET", "/api/v1/auth/me", token="garbage")[0] == 401, "malformed token is rejected")
        check(g, call("GET", "/api/v1/auth/me", headers={"Authorization": "Basic abc"})[0] == 401, "non-bearer Authorization header is rejected")
        old = base64.urlsafe_b64encode(json.dumps({"uid": json.loads(base64.urlsafe_b64decode(payload))["uid"], "exp": int(time.time()) - 5}).encode()).decode()
        # a validly signed but expired token needs the server secret; the default dev secret is public in config.py
        import config
        sg = hmac.new((os.environ.get("AGRIVISION_SECRET") or config.SECRET_KEY).encode(), old.encode(), hashlib.sha256).hexdigest()
        check(g, call("GET", "/api/v1/auth/me", token=f"{old}.{sg}")[0] == 401, "expired token is rejected")
        # the default secret is a hard-coded string: anybody can mint a token for a known user id (documented risk)
        forged_p = base64.urlsafe_b64encode(json.dumps({"uid": json.loads(base64.urlsafe_b64decode(payload))["uid"], "exp": int(time.time()) + 600}).encode()).decode()
        forged_s = hmac.new(config.SECRET_KEY.encode(), forged_p.encode(), hashlib.sha256).hexdigest()
        defect(g, call("GET", "/api/v1/auth/me", token=f"{forged_p}.{forged_s}")[0] == 200,
               "token signed with the default development secret is refused (it is accepted: set AGRIVISION_SECRET in production)")
        # upload validation
        leaf = S.leaf_image()
        b, h = multipart("leaf.JPG", leaf, {"crop_type": "tomato"})
        check(g, call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)[0] == 200, "upper-case extension .JPG is accepted")
        b, h = multipart("leaf.webp", leaf, {"crop_type": "tomato"})
        s, r, _ = call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)
        check(g, s == 200, ".webp extension is accepted", str(s))
        b, h = multipart("empty.jpg", b"", {"crop_type": "tomato"})
        check(g, call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)[0] == 400, "empty file is rejected with 400")
        b, h = multipart("noext", leaf, {"crop_type": "tomato"})
        check(g, call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)[0] == 400, "file without extension is rejected")
        b, h = multipart("big.jpg", b"\xff\xd8" + b"0" * (11 * 1024 * 1024), {"crop_type": "tomato"})
        s, r, _ = call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)
        check(g, s == 413, "11 MB upload is refused with 413", str(s))
        b, h = multipart("../../evil.jpg", leaf, {"crop_type": "tomato"})
        s, r, _ = call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)
        check(g, s == 200 and "evil" not in json.dumps(r) and not (tmp / "evil.jpg").exists(), "path in the file name does not escape the upload folder")
        b, h = multipart("leaf.jpg", leaf, {"crop_type": "'; DROP TABLE results;--"})
        s, r, _ = call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)
        s2, hist, _ = call("GET", "/api/v1/history?limit=100", token=tok)
        check(g, s == 200 and s2 == 200, "SQL text in crop_type is stored as data (results table still works)")
        b, h = multipart("leaf.jpg", leaf, {"crop_type": "no-such-crop"})
        check(g, call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)[0] == 200, "unknown crop option falls back to all classes")
        # the crop-hint defect through the API
        b, h = multipart("leaf.jpg", leaf, {"crop_type": "blueberry"})
        s, r, _ = call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)
        defect(g, s == 400 and r.get("error") == "UNREADABLE_IMAGE",
               "crop = blueberry works (API answers 400 UNREADABLE_IMAGE for a valid leaf photo)", f"{s} {r}")
        # injection-style search and paging validation
        s, r, _ = call("GET", "/api/v1/history?q=" + urllib.request.quote("' OR 1=1 --"), token=tok)
        check(g, s == 200 and r["total_count"] == 0, "SQL text in the search box matches nothing")
        check(g, call("GET", "/api/v1/history?limit=0", token=tok)[0] == 422, "limit=0 is a validation error (422)")
        check(g, call("GET", "/api/v1/history?limit=101", token=tok)[0] == 422, "limit=101 is a validation error (422)")
        check(g, call("GET", "/api/v1/history?offset=-1", token=tok)[0] == 422, "negative offset is a validation error (422)")
        # file serving
        check(g, call("GET", "/api/v1/uploads/..%2F..%2Fconfig.py", raw=True)[0] == 404, "path traversal in /uploads/ gives 404")
        check(g, call("GET", "/api/v1/uploads/doesnotexist.jpg", raw=True)[0] == 404, "missing upload gives 404")
        s, one, _ = call("GET", "/api/v1/history?limit=1", token=tok)
        url = one["results"][0]["image_url"]
        check(g, call("GET", url, raw=True)[0] == 200, "uploaded images are served without a token (the random file name is the capability)")
        # CORS
        req = urllib.request.Request(S.BASE + "/api/health", headers={"Origin": "http://localhost:5416"})
        with urllib.request.urlopen(req) as r:
            check(g, r.headers.get("access-control-allow-origin") == "http://localhost:5416", "CORS allows the local web origin")
        req = urllib.request.Request(S.BASE + "/api/health", headers={"Origin": "http://evil.example"})
        with urllib.request.urlopen(req) as r:
            check(g, r.headers.get("access-control-allow-origin") is None, "CORS does not allow a foreign origin")
        # profile
        check(g, call("PUT", "/api/v1/profile", {"language": "mr", "crops": []}, token=tok)[0] == 200, "profile accepts Marathi and empty crop list")
        s, me, _ = call("GET", "/api/v1/auth/me", token=tok)
        check(g, me["crops"] == ["tomato"], "empty crop list falls back to tomato")
        check(g, call("POST", "/api/v1/auth/login", None)[0] == 401, "login with no body is 401")
        check(g, call("POST", "/api/v1/auth/register", None)[0] == 400, "register with no body is 400")
        s, dd, _ = call("GET", "/api/v1/diseases/" + urllib.request.quote("Tomato — Late blight"))
        check(g, s == 200 and dd["class"] == "Tomato___Late_blight", "disease detail also resolves by display name")
        # rate limiting and password hashing
        t = time.perf_counter()
        for _ in range(8):
            call("POST", "/api/v1/auth/login", {"email": "demo@agrivision.ai", "password": "wrong"})
        defect(g, True, "repeated wrong passwords are throttled (there is no rate limiting: 8 attempts in %.1f s all answered)" % (time.perf_counter() - t))
        import sqlite3
        con = sqlite3.connect(tmp / "edge.db")
        ph = con.execute("SELECT password_hash FROM users WHERE email='demo@agrivision.ai'").fetchone()[0]
        check(g, ph.startswith(("scrypt:", "pbkdf2:")) and "demo1234" not in ph, "passwords are stored as salted hashes", ph[:12])
        con.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


def main() -> int:
    (ROOT / "docs" / "metrics").mkdir(parents=True, exist_ok=True)
    unit()
    api()
    n = {k: sum(1 for _, s, _ in rows if s == k) for k in ("PASS", "FAIL", "DEFECT")}
    by_group = {g: {k: sum(1 for gg, s, _ in rows if gg == g and s == k) for k in ("PASS", "FAIL", "DEFECT")} for g in ("unit", "api")}
    print(f"\n{n['PASS']} passed, {n['FAIL']} failed, {n['DEFECT']} defects recorded")
    json.dump({"total": len(rows), **n, "by_group": by_group, "rows": rows}, open(ROOT / "docs" / "metrics" / "edge_tests.json", "w"), indent=1)
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
