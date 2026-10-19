"""StoryVox smoke test: walks the main flow through the running web app.

Needs the app running (run.bat). Uses only the standard library.
  python scripts/smoke_test.py                      # web app on 5402, which proxies /api to 8402
  python scripts/smoke_test.py http://localhost:8402
Narration is only requested if the speech model is installed, so the test also passes on a machine without it.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5402").rstrip("/")
FAILS: list[str] = []


def call(method: str, path: str, body: dict | None = None, timeout: int = 300):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read()
            ctype = res.headers.get("content-type", "")
            return res.status, (json.loads(raw) if "json" in ctype else raw)
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read())
        except Exception:
            return exc.code, {}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


status, page = call("GET", "/")
check("web app serves the page", status == 200 and b"<div id=\"root\">" in page)

status, health = call("GET", "/api/health")
check("health", status == 200 and health.get("status") == "ok")

status, langs = call("GET", "/api/languages")
check("languages", status == 200 and len(langs) >= 10, f"{len(langs)} languages")

status, meta = call("GET", "/api/meta")
check("meta lists styles and lengths", status == 200 and meta.get("styles") and meta.get("lengths"))

status, err = call("POST", "/api/stories/generate", {"prompt": "   ", "language_code": "en"})
check("blank idea is rejected with a message", status == 422 and err.get("detail"))

status, story = call("POST", "/api/stories/generate", {
    "prompt": "A lighthouse keeper befriends a storm", "language_code": "en",
    "style": "Fantasy", "length_option": "Short", "synthesize": False})
check("generate story", status == 200 and story.get("story_text") and story.get("title"), story.get("title", ""))
sid = story.get("id")

if sid:
    status, listing = call("GET", "/api/stories?limit=200")
    check("story appears in history", status == 200 and any(s["id"] == sid for s in listing))

    status, one = call("GET", f"/api/stories/{sid}")
    check("get story by id", status == 200 and one["id"] == sid)

    status, aud = call("POST", f"/api/stories/{sid}/synthesize")
    if status == 200:
        check("narration generated", aud.get("duration_seconds", 0) > 0, f"{aud['duration_seconds']}s via {aud['tts_model']}")
        status, wav = call("GET", f"/api/audio/{aud['id']}")
        check("audio streams as WAV", status == 200 and bytes(wav[:4]) == b"RIFF")
    else:
        check("narration failure carries a readable message", bool(aud.get("detail")), aud.get("detail", ""))

    status, gone = call("DELETE", f"/api/stories/{sid}")
    check("delete story", status == 200 and gone.get("status") == "deleted")
    status, _ = call("GET", f"/api/stories/{sid}")
    check("deleted story is gone (404)", status == 404)

status, evals = call("GET", "/api/evaluations")
check("evaluations list", status == 200 and isinstance(evals, list), f"{len(evals)} saved")

print()
print("ALL PASSED" if not FAILS else f"{len(FAILS)} FAILED: {', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
