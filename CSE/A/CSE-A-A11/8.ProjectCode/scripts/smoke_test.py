"""End-to-end API smoke test. Start the backend first (run.bat, or `python -m backend`), then:  python scripts/smoke_test.py"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8311
for line in (ROOT / ".env").read_text().splitlines() if (ROOT / ".env").exists() else []:
    if line.startswith("BACKEND_PORT="):
        PORT = int(line.split("=", 1)[1])
BASE = f"http://127.0.0.1:{PORT}/api"
TOKEN = None
passed = failed = 0


def call(method, path, body=None, raw=False, expect=200):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            payload = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        payload, status = e.read(), e.code
    if status != expect:
        raise AssertionError(f"{method} {path} -> {status}, expected {expect}: {payload[:200]!r}")
    return payload if raw else json.loads(payload or b"null")


def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"PASS  {name}")
    except Exception as e:  # noqa: BLE001
        failed += 1
        print(f"FAIL  {name}: {e}")


def wait_job(job_id, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        j = call("GET", f"/jobs/{job_id}")
        if j["status"] != "running":
            return j
        time.sleep(0.4)
    raise AssertionError("job timed out")


state = {}


def t_health():
    assert call("GET", "/health")["status"] == "ok"


def t_public_stats():
    s = call("GET", "/public/stats")
    assert s["functions"] > 0 and 0 < s["f1"] <= 1


def t_public_landing_data():
    ex = call("GET", "/public/example")
    assert ex["finding"]["title"] and ex["verdict"] == "BLOCK"
    assert "SQL injection" in call("GET", "/public/rules")["rules"]


def t_auth_required():
    call("GET", "/reviews", expect=401)


def t_bad_login():
    call("POST", "/auth/login", {"email": "demo@autosecai.dev", "password": "wrong"}, expect=401)


def t_login():
    global TOKEN
    d = call("GET", "/auth/demo")
    r = call("POST", "/auth/login", d)
    TOKEN = r["token"]
    assert call("GET", "/auth/me")["email"] == d["email"]


def t_register():
    email = f"smoke{int(time.time())}@example.com"
    r = call("POST", "/auth/register", {"name": "Smoke Test", "email": email, "password": "Passw0rd!x"}, expect=201)
    assert r["user"]["email"] == email
    call("POST", "/auth/register", {"name": "Smoke Test", "email": email, "password": "Passw0rd!x"}, expect=409)


def t_meta():
    m = call("GET", "/meta")
    assert len(m["pipeline"]) == 7 and len(m["metrics"]) == 14
    s = call("GET", "/samples")
    assert "diff --git" in s["demo_diff"]


def t_demo_review():
    j = wait_job(call("POST", "/reviews", {"kind": "demo-diff"}, expect=202)["job_id"])
    assert j["status"] == "done", j
    assert len(j["messages"]) >= 5
    state["review"] = j["result"]["review_id"]
    r = call("GET", f"/reviews/{state['review']}")
    assert r["verdict"] == "BLOCK" and r["findings"] and len(r["trace"]) == 7


def t_versions_review():
    j = wait_job(call("POST", "/reviews", {"kind": "versions", "filename": "a.py", "old": "",
                                           "new": "def f(n):\n    cur.execute(f\"SELECT * FROM t WHERE a='{n}'\")\n"},
                      expect=202)["job_id"])
    assert j["status"] == "done"


def t_diff_review_and_validation():
    call("POST", "/reviews", {"kind": "diff", "diff": "   "}, expect=422)
    call("POST", "/reviews", {"kind": "diff", "diff": "not a diff"}, expect=422)
    call("POST", "/reviews", {"kind": "folder", "folder": "Z:/nope"}, expect=422)


def t_github_bad_url():
    j = wait_job(call("POST", "/reviews", {"kind": "github", "url": "https://example.com/x"}, expect=202)["job_id"])
    assert j["status"] == "error" and "GitHub" in j["error"]


def t_history_and_exports():
    rid = state["review"]
    assert any(r["id"] == rid for r in call("GET", "/reviews"))
    for fmt, needle in (("md", b"AutoSecAI review"), ("sarif", b"2.1.0"), ("json", b'"verdict"'), ("csv", b"severity")):
        assert needle in call("GET", f"/reviews/{rid}/export/{fmt}", raw=True), fmt
    call("GET", f"/reviews/{rid}/export/pdf", expect=404)
    r = call("GET", f"/reviews/{rid}")
    if r["patched"]:
        path = next(iter(r["patched"]))
        call("GET", f"/reviews/{rid}/patched?path={urllib.request.quote(path)}", raw=True)


def t_delete_review():
    j = wait_job(call("POST", "/reviews", {"kind": "demo-versions"}, expect=202)["job_id"])
    rid = j["result"]["review_id"]
    call("DELETE", f"/reviews/{rid}")
    call("GET", f"/reviews/{rid}", expect=404)


def t_codebase():
    ix = call("POST", "/codebase/index", {"source": "demo"})
    assert ix["files"] > 3 and ix["overview"]["routes"] is not None and ix["graph"]["nodes"]
    a = call("POST", f"/codebase/{ix['index_id']}/ask", {"question": "Where is the authentication mechanism implemented?"})
    assert a["hits"] and a["answer"]
    call("POST", f"/codebase/{ix['index_id']}/ask", {"question": "  "}, expect=422)
    call("GET", "/codebase/missing", expect=404)
    me = call("POST", "/codebase/index", {"source": "self"})
    assert not any(c["files"] and any(f.startswith("frontend/") or f == ".env" for f in c["files"]) for c in me["overview"]["by_concept"])


def t_lab():
    R = call("GET", "/lab/report")
    assert R["best"] in R["results"]
    out = call("POST", "/lab/analyze", {"code": "def get_user(name):\n    q = f\"SELECT * FROM users WHERE name = '{name}'\"\n    cur.execute(q)\n    return cur.fetchall()\n"})
    assert 0 <= out["functions"][0]["probability"] <= 1 and any(f["rule_id"] == "SQLI" for f in out["findings"])
    call("POST", "/lab/analyze", {"code": "def ("}, expect=422)


for name, fn in [("health", t_health), ("public stats", t_public_stats), ("landing example + rules", t_public_landing_data), ("auth required", t_auth_required),
                 ("bad login rejected", t_bad_login), ("demo login + /me", t_login), ("register + duplicate", t_register),
                 ("meta + samples", t_meta), ("demo diff review (job)", t_demo_review),
                 ("compare-versions review", t_versions_review), ("review input validation", t_diff_review_and_validation),
                 ("github bad url -> readable error", t_github_bad_url), ("history + exports", t_history_and_exports),
                 ("delete review", t_delete_review), ("codebase index + ask", t_codebase), ("model lab", t_lab)]:
    check(name, fn)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
