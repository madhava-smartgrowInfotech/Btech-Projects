"""Edge-case and security checks against the running API (http://127.0.0.1:8105). Writes experiments/edge_tests.json.

Run from 8.ProjectCode:  venv\\Scripts\\python scripts\\docs_build\\edge_tests.py
These are black-box HTTP checks; each row records the request, the expected status and the observed status.
"""
import json
import os
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = "http://127.0.0.1:8105"
rows = []


def call(method, path, body=None, token=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r = urllib.request.Request(B + path, method=method, data=data)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            code, txt = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        code, txt = e.code, e.read()
    ms = round((time.perf_counter() - t0) * 1000, 1)
    try:
        js = json.loads(txt or b"null")
    except Exception:
        js = None
    return code, js, ms


def check(area, name, expected, got, note=""):
    ok = got == expected
    rows.append(dict(area=area, case=name, expected=expected, observed=got, passed=ok, note=note))
    print(("PASS" if ok else "FAIL"), area, "|", name, "| expected", expected, "got", got, note)


def main():
    stamp = int(time.time())
    code, js, _ = call("POST", "/api/auth/login", {"email": "demo@taxsentinel.app", "password": "Demo@1234"})
    check("Authentication", "demo login with correct password", 200, code)
    tok = js["token"]
    code, js, _ = call("POST", "/api/auth/login", {"email": "demo@taxsentinel.app", "password": "wrong-password"})
    check("Authentication", "wrong password", 401, code, str(js))
    code, _, _ = call("POST", "/api/auth/login", {"email": "nobody@example.com", "password": "Whatever1!"})
    check("Authentication", "unknown e-mail", 401, code)
    code, _, _ = call("POST", "/api/auth/login", {"email": "DEMO@TaxSentinel.APP ", "password": "Demo@1234"})
    check("Authentication", "e-mail is case-insensitive and trimmed", 200, code)
    code, _, _ = call("POST", "/api/auth/register", {"name": "Edge", "email": f"edge{stamp}@example.com", "password": "short"})
    check("Validation", "password shorter than 8 characters", 422, code)
    code, _, _ = call("POST", "/api/auth/register", {"name": "Edge", "email": "not-an-email", "password": "LongEnough1!"})
    check("Validation", "malformed e-mail", 422, code)
    code, _, _ = call("POST", "/api/auth/register", {"name": "", "email": f"edge{stamp}@example.com", "password": "LongEnough1!"})
    check("Validation", "empty name", 422, code)
    code, _, _ = call("POST", "/api/auth/register", {"name": "Edge", "email": "demo@taxsentinel.app", "password": "LongEnough1!"})
    check("Validation", "duplicate registration", 409, code)
    code, _, _ = call("POST", "/api/auth/register", {"name": "Edge", "email": f"edge{stamp}@example.com", "password": "LongEnough1!"})
    check("Authentication", "valid registration", 200, code)
    code, _, _ = call("POST", "/api/auth/login", raw=b"{not json")
    check("Validation", "malformed JSON body", 422, code)

    code, _, _ = call("GET", "/api/overview")
    check("Authorisation", "no token", 401, code)
    code, _, _ = call("GET", "/api/overview", token="abc.def.ghi")
    check("Authorisation", "garbage token", 401, code)
    parts = tok.split(".")
    tampered = ".".join([parts[0], parts[1], parts[2][:-4] + ("AAAA" if not parts[2].endswith("AAAA") else "BBBB")])
    code, _, _ = call("GET", "/api/overview", token=tampered)
    check("Authorisation", "token with altered signature", 401, code)
    for p in ("/api/taxpayers", "/api/chains", "/api/structures", "/api/graph", "/api/metrics", "/api/pipeline/status", "/api/pipeline/runs"):
        code, _, _ = call("GET", p)
        check("Authorisation", f"GET {p} without token", 401, code)
    code, _, _ = call("POST", "/api/pipeline/run", {"seed": 1, "taxpayers": 200})
    check("Authorisation", "POST /api/pipeline/run without token", 401, code)
    code, _, _ = call("POST", "/api/explanations/ABC")
    check("Authorisation", "POST /api/explanations without token", 401, code)
    code, js, _ = call("GET", "/api/health")
    check("Availability", "health is public", 200, code)

    code, _, _ = call("GET", "/api/taxpayers/NOT-A-GSTIN", token=tok)
    check("Edge case", "unknown GSTIN profile", 404, code)
    code, _, _ = call("POST", "/api/explanations/NOT-A-GSTIN", token=tok)
    check("Edge case", "explanation for unknown GSTIN", 404, code)
    code, _, _ = call("GET", "/api/chains/CH-DOES-NOT-EXIST", token=tok)
    check("Edge case", "unknown chain id", 404, code)
    code, js, _ = call("GET", "/api/taxpayers?limit=0", token=tok)
    check("Validation", "limit=0 rejected", 422, code)
    code, js, _ = call("GET", "/api/taxpayers?limit=501", token=tok)
    check("Validation", "limit above 500 rejected", 422, code)
    code, js, _ = call("GET", "/api/taxpayers?offset=-1", token=tok)
    check("Validation", "negative offset rejected", 422, code)
    code, js, _ = call("GET", "/api/taxpayers?q=zzzz-no-such-name", token=tok)
    check("Edge case", "search with no match returns an empty page", 200, code, f"items={len(js['items'])}")
    code, js, _ = call("GET", "/api/taxpayers?q=%27%3B%20DROP%20TABLE%20users%3B--", token=tok)
    check("Security", "SQL-injection-style search text is inert", 200, code, f"items={len(js['items'])}")
    code, js, _ = call("GET", "/api/taxpayers?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E", token=tok)
    check("Security", "script tag in search text is inert", 200, code, f"items={len(js['items'])}")
    code, _, _ = call("POST", "/api/pipeline/run", {"seed": 1, "taxpayers": 100}, token=tok)
    check("Validation", "taxpayers below 150 rejected", 422, code)
    code, _, _ = call("POST", "/api/pipeline/run", {"seed": 1, "taxpayers": 5000}, token=tok)
    check("Validation", "taxpayers above 1500 rejected", 422, code)
    code, _, _ = call("POST", "/api/pipeline/run", {"seed": -5, "taxpayers": 200}, token=tok)
    check("Validation", "negative seed rejected", 422, code)
    code, _, _ = call("POST", "/api/pipeline/run", {"seed": "abc", "taxpayers": 200}, token=tok)
    check("Validation", "non-numeric seed rejected", 422, code)

    # one run at a time: start a small run, immediately try a second
    code, js, _ = call("POST", "/api/pipeline/run", {"seed": 5, "taxpayers": 150}, token=tok)
    check("Concurrency", "first run accepted", 200, code)
    code, js2, _ = call("POST", "/api/pipeline/run", {"seed": 6, "taxpayers": 150}, token=tok)
    check("Concurrency", "second run while one is running", 409, code, str((js2 or {}).get("detail")))
    for _ in range(300):
        code, st, _ = call("GET", "/api/pipeline/status", token=tok)
        if not st["running"]:
            break
        time.sleep(1)
    check("Concurrency", "small run (seed 5, 150 taxpayers) completes", "done", st["stage"])
    # restore the bundled ecosystem (seed 42, 600)
    code, js, _ = call("POST", "/api/pipeline/run", {"seed": 42, "taxpayers": 600}, token=tok)
    for _ in range(400):
        code, st, _ = call("GET", "/api/pipeline/status", token=tok)
        if not st["running"]:
            break
        time.sleep(1)
    check("Concurrency", "bundled ecosystem restored (seed 42, 600)", "done", st["stage"])
    code, ov, _ = call("GET", "/api/overview", token=tok)
    check("Consistency", "restored ecosystem flags 78 taxpayers", 78, ov["stats"]["flagged"])

    out = dict(base=B, total=len(rows), passed=sum(r["passed"] for r in rows), rows=rows)
    with open(os.path.join(ROOT, "experiments", "edge_tests.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n{out['passed']} / {out['total']} passed")


if __name__ == "__main__":
    main()
