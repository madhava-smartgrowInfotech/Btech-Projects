"""End-to-end smoke test of the main flow through the frontend dev server (which proxies /api to the backend).

Run with the app up (run.bat):  python scripts/smoke_test.py
Standard library only. Exits non-zero on the first failure.
"""
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from http.cookiejar import CookieJar

WEB = os.getenv("CARELENS_WEB", "http://localhost:5412")
API = os.getenv("CARELENS_API", "http://127.0.0.1:8412")
results = []


def client():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def call(op, base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"} if data else {})
    try:
        with op.open(req, timeout=180) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw and raw.lstrip()[:1] in "[{" else raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def check(name, cond, detail=""):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail and not cond else ""))


def main():
    op = client()
    s, d = call(op, API, "GET", "/api/health")
    check("backend health on 8412", s == 200 and d.get("status") == "ok", d)
    s, html = call(op, WEB, "GET", "/")
    check("frontend serves the app on 5412", s == 200 and "<div id=\"root\">" in html)
    s, d = call(op, WEB, "GET", "/api/health")
    check("frontend proxy reaches the API", s == 200 and d.get("status") == "ok", d)

    s, d = call(op, WEB, "GET", "/api/history")
    check("history requires sign-in (401)", s == 401, s)
    s, d = call(op, WEB, "POST", "/api/auth/login", {"email": "demo@carelens.ai", "password": "wrong-pass"})
    check("bad password rejected (401)", s == 401 and "Invalid" in d.get("detail", ""), d)

    s, d = call(op, WEB, "POST", "/api/auth/login", {"email": "demo@carelens.ai", "password": "Demo@1234"})
    check("demo login works", s == 200 and d.get("email") == "demo@carelens.ai", d)
    s, d = call(op, WEB, "GET", "/api/auth/me")
    check("session cookie -> /me", s == 200 and d.get("email") == "demo@carelens.ai", d)

    s, d = call(op, WEB, "POST", "/api/chat", {"query": "I have high fever, headache and body pain"})
    ok = s == 200 and d.get("answer") and len(d.get("evidence", [])) >= 1 and d.get("safety_flag") in ("routine", "caution", "emergency")
    check("chat returns answer + evidence", ok, d)
    cid = d.get("consultation_id") if isinstance(d, dict) else None
    if ok:
        e = d["evidence"][0]
        check("evidence has card fields", all(k in e for k in ("disease", "symptoms", "description", "guidance", "severity", "relevance")), e)
    s, d = call(op, WEB, "POST", "/api/chat", {"query": "severe chest pain and difficulty breathing"})
    check("emergency wording escalates", s == 200 and d.get("safety_flag") == "emergency", d.get("safety_flag") if isinstance(d, dict) else d)
    eid = d.get("consultation_id") if isinstance(d, dict) else None
    s, d = call(op, WEB, "POST", "/api/chat", {"query": "x"})
    check("too-short query rejected (422)", s == 422, s)

    s, d = call(op, WEB, "GET", "/api/history")
    check("history lists consultations", s == 200 and isinstance(d, list) and any(c["id"] == cid for c in d))
    s, d = call(op, WEB, "GET", "/api/history?search=fever")
    check("history search filters", s == 200 and d and all("fever" in (c["symptom_query"] + c["top_condition"]).lower() for c in d))
    s, d = call(op, WEB, "GET", f"/api/history/{cid}")
    check("history detail", s == 200 and d.get("id") == cid and d.get("retrieved_evidence"))
    for i in (cid, eid):
        if i:
            s, d = call(op, WEB, "DELETE", f"/api/history/{i}")
            check(f"delete consultation {i}", s == 200 and d.get("ok") is True, d)
    s, d = call(op, WEB, "GET", f"/api/history/{cid}")
    check("deleted consultation is 404", s == 404, s)

    s, d = call(op, WEB, "GET", "/api/about/metrics")
    check("about metrics endpoint", s == 200 and "top1_accuracy" in d and d.get("kb_records", 0) > 0, d)

    # registration + isolation, on a throwaway user
    op2 = client()
    mail = f"smoke{uuid.uuid4().hex[:8]}@example.com"
    s, d = call(op2, WEB, "POST", "/api/auth/register", {"email": mail, "password": "Smoke123"})
    check("register new account", s == 200 and d.get("email") == mail, d)
    s, d = call(op2, WEB, "POST", "/api/auth/register", {"email": mail, "password": "Smoke123"})
    check("duplicate email rejected (400)", s == 400, d)
    s, d = call(op2, WEB, "GET", "/api/history")
    check("new account has empty, private history", s == 200 and d == [], d)
    s, d = call(op2, WEB, "POST", "/api/auth/logout")
    s, d = call(op2, WEB, "GET", "/api/auth/me")
    check("logout clears the session", s == 401, s)

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
