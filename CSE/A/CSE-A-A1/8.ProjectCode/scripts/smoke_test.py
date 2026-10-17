"""
End-to-end smoke test for the JSON API (backend on port 8301 must be running).

    venv\\Scripts\\python.exe scripts\\smoke_test.py

Covers: health, register, login, me, upload, documents, ask, history, quiz generate/submit,
roadmap, dashboard, delete, logout. Uses only the standard library.
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8301")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "sample_data", "sample_notes_data_structures.txt")

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
failures = []


def call(method, path, body=None, raw=None, headers=None):
    data = raw
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=hdrs)
    try:
        with opener.open(req) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        payload = e.read()
        try:
            return e.code, json.loads(payload)
        except ValueError:
            return e.code, payload.decode(errors="replace")


def multipart(fields, file_field, filename, content):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n".encode() + content + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def main():
    user = f"smoke_{int(time.time())}"
    pwd = "smoke-pass-1"

    s, r = call("GET", "/api/health")
    check("health", s == 200 and r.get("status") == "ok", r)

    s, r = call("GET", "/api/dashboard")
    check("protected route rejects anonymous (401)", s == 401, (s, r))

    s, r = call("POST", "/api/auth/register", {"username": "", "password": ""})
    check("register rejects empty fields (400)", s == 400, (s, r))
    s, r = call("POST", "/api/auth/register", {"username": user, "password": pwd, "interests": "Data Structures"})
    check("register", s == 201, (s, r))
    s, r = call("POST", "/api/auth/register", {"username": user, "password": pwd})
    check("register duplicate (409)", s == 409, (s, r))
    s, r = call("POST", "/api/auth/login", {"username": user, "password": "wrong"})
    check("login wrong password (401)", s == 401, (s, r))
    s, r = call("POST", "/api/auth/login", {"username": user, "password": pwd})
    check("login", s == 200 and r.get("username") == user, (s, r))
    s, r = call("GET", "/api/auth/me")
    check("me", s == 200 and r.get("username") == user, (s, r))

    s, r = call("GET", "/api/dashboard")
    check("dashboard empty", s == 200 and r["doc_count"] == 0 and r["performance"] == [], (s, r))

    with open(SAMPLE, "rb") as f:
        content = f.read()
    raw, hdr = multipart({"subject": "Data Structures"}, "document", "sample_notes.txt", content)
    s, r = call("POST", "/api/documents", raw=raw, headers=hdr)
    check("upload txt", s == 201 and r["chunks_count"] > 0 and r["topics_count"] > 0, (s, r))
    doc_id = r["document"]["id"] if s == 201 else None

    raw, hdr = multipart({}, "document", "bad.exe", b"MZ")
    s, r = call("POST", "/api/documents", raw=raw, headers=hdr)
    check("upload rejects unsupported type (400)", s == 400, (s, r))

    s, r = call("GET", "/api/documents")
    check("documents list", s == 200 and len(r) == 1 and r[0]["topics"], (s, r))

    s, r = call("POST", "/api/ask", {"question": ""})
    check("ask rejects empty question (400)", s == 400, (s, r))
    s, r = call("POST", "/api/ask", {"question": "What is the LIFO principle?"})
    check("ask returns answer + sources", s == 200 and r["answer"] and r["sources"], (s, r))
    s, r = call("GET", "/api/ask/history")
    check("ask history", s == 200 and len(r) == 1, (s, r))

    s, r = call("POST", "/api/quiz/submit", {"answers": []})
    check("submit without quiz (409)", s == 409, (s, r))
    s, r = call("POST", "/api/quiz/generate", {"doc_id": 999999})
    check("quiz on unknown document (404)", s == 404, (s, r))
    s, r = call("POST", "/api/quiz/generate", {"doc_id": doc_id})
    check("quiz generate (answers hidden)", s == 200 and r["questions"] and "answer_index" not in r["questions"][0], (s, r))
    n = len(r["questions"]) if s == 200 else 0
    s, r = call("POST", "/api/quiz/submit", {"answers": [0] * n})
    check("quiz submit", s == 200 and r["total"] == n and 0 <= r["score_pct"] <= 100, (s, r))

    s, r = call("GET", "/api/roadmap")
    check("roadmap", s == 200 and len(r) > 0 and r[0]["priority"] in ("High", "Medium", "Low"), (s, r))
    s, r = call("GET", "/api/dashboard")
    check("dashboard has data", s == 200 and r["doc_count"] == 1 and r["query_count"] == 1 and r["quiz_attempts"] == n, (s, r))

    s, r = call("DELETE", f"/api/documents/{doc_id}")
    check("delete document", s == 200, (s, r))
    s, r = call("DELETE", f"/api/documents/{doc_id}")
    check("delete again (404)", s == 404, (s, r))

    s, r = call("POST", "/api/auth/logout")
    check("logout", s == 200, (s, r))
    s, r = call("GET", "/api/auth/me")
    check("session cleared (me is null)", s == 200 and r is None, (s, r))

    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        sys.exit(1)
    print("All smoke checks passed.")


if __name__ == "__main__":
    main()
