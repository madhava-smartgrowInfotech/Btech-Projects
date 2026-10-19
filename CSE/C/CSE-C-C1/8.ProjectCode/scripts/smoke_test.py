"""End-to-end smoke test for AegisBallot: API contract + the main voting flow + the web proxy.

Needs both servers running (run.bat). Uses only the standard library.
    python scripts/smoke_test.py

It creates one "Smoke Test <time>" election (closed at the end) and casts one ballot with voter1..voter20,
choosing a voter that has not voted in it. Seeded elections and the ledger's validity are left untouched.
"""
import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_env():
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = read_env()
API = f"http://127.0.0.1:{ENV.get('BACKEND_PORT', '8401')}"
WEB = f"http://localhost:{ENV.get('FRONTEND_PORT', '5401')}"


class Client:
    """Tiny cookie-keeping JSON client."""

    def __init__(self, base=API):
        self.base = base
        self.csrf = None
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, method, path, body=None, csrf=True):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if csrf and self.csrf and method != "GET":
            req.add_header("X-CSRF-Token", self.csrf)
        try:
            with self.opener.open(req, timeout=30) as r:
                raw = r.read().decode()
                return r.status, (json.loads(raw) if raw and r.headers.get_content_type() == "application/json" else raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, raw

    def login(self, user, password):
        status, body = self.call("POST", "/api/auth/login", {"username": user, "password": password})
        if status == 200:
            self.csrf = body["csrf"]
        return status, body


results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail and not cond else ""))


def main():
    anon = Client()
    s, b = anon.call("GET", "/api/health")
    check("backend health", s == 200 and b.get("status") == "ok" and b.get("chain_valid") is True, b)
    s, b = anon.call("GET", "/api/public/overview")
    check("public overview lists elections and ledger", s == 200 and "elections" in b and b["ledger"]["height"] >= 1, b)
    s, b = anon.call("GET", "/api/auth/me")
    check("auth/me is 200 with user=null when signed out", s == 200 and b["user"] is None, b)
    s, _ = anon.call("GET", "/api/admin/overview")
    check("admin endpoint rejects anonymous (401)", s == 401)
    s, _ = anon.login("admin", "wrong-password")
    check("bad password rejected (401)", s == 401)

    admin = Client()
    s, b = admin.login("admin", "Admin@123")
    check("admin login", s == 200 and b["user"]["role"] == "ADMIN", b)
    s, b = admin.call("POST", "/api/admin/elections/1/status", {"status": "OPEN"}, csrf=False)
    check("mutation without CSRF token rejected (403)", s == 403, b)
    s, b = admin.call("GET", "/api/admin/overview")
    check("admin overview has stats", s == 200 and b["total_voters"] >= 1 and b["chain"]["valid"], b if s != 200 else "")

    now = datetime.utcnow()
    title = f"Smoke Test {now.strftime('%Y-%m-%d %H:%M:%S')}"
    s, b = admin.call("POST", "/api/admin/elections", {"title": title, "description": "smoke", "start_time": now.isoformat(timespec="seconds"), "end_time": (now + timedelta(days=1)).isoformat(timespec="seconds")})
    check("create election", s == 201, b)
    eid = b.get("id")
    s, b2 = admin.call("POST", "/api/admin/elections", {"title": "x", "description": "", "start_time": "2030-01-02T00:00:00", "end_time": "2030-01-01T00:00:00"})
    check("end before start rejected (400)", s == 400, b2)
    cand_ids = []
    for name in ("Smoke Alpha", "Smoke Beta"):
        s, c = admin.call("POST", f"/api/admin/elections/{eid}/candidates", {"name": name, "party": "Smoke Party", "description": "", "manifesto": ""})
        check(f"add candidate {name}", s == 201, c)
        cand_ids.append(c.get("id"))
    s, c = admin.call("POST", f"/api/admin/candidates/{cand_ids[1]}/toggle")
    check("toggle candidate off", s == 200 and c["is_active"] is False, c)
    s, c = admin.call("POST", f"/api/admin/candidates/{cand_ids[1]}/toggle")
    check("toggle candidate on", s == 200 and c["is_active"] is True, c)
    s, b = admin.call("POST", f"/api/admin/elections/{eid}/status", {"status": "BOGUS"})
    check("invalid status rejected (400)", s == 400, b)
    s, b = admin.call("POST", f"/api/admin/elections/{eid}/status", {"status": "OPEN"})
    check("open election", s == 200 and b["status"] == "OPEN", b)
    s, b = admin.call("GET", f"/api/admin/elections/{eid}")
    check("election detail", s == 200 and len(b["candidates"]) == 2 and b["eligible"] >= 1 and b["results"] is None, b if s != 200 else "")

    identities = json.loads((ROOT / "data" / "synthetic_identities.json").read_text(encoding="utf-8"))
    me, other = identities[0], identities[1]
    voter = Client()
    s, b = voter.login(me["username"], me["password"])
    check("voter login", s == 200 and b["user"]["role"] == "VOTER", b)
    s, _ = voter.call("GET", "/api/admin/overview")
    check("voter blocked from admin API (403)", s == 403)
    s, b = voter.call("GET", "/api/voter/elections")
    check("voter sees the open election", s == 200 and any(e["id"] == eid and not e["voted"] for e in b["elections"]), "")
    s, b = voter.call("GET", f"/api/voter/elections/{eid}")
    check("voter election shows masked Aadhaar", s == 200 and b["masked_aadhaar"] == me["masked"], b)
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": "123"})
    check("short Aadhaar rejected (400)", s == 400, b)
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": "123456789012"})
    check("bad checksum / unknown Aadhaar rejected (400)", s == 400, b)
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": other["aadhaar"]})
    check("another voter's Aadhaar rejected (403)", s == 403, b)
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": me["aadhaar"]})
    check("correct Aadhaar issues a one-time token", s == 200 and b["auth_token"] and len(b["candidates"]) == 2 and b["expires_in"] == 600, b)
    token = b.get("auth_token", "")
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": cand_ids[0], "auth_token": "wrong-token"})
    check("wrong token rejected (400)", s == 400, b)
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": cand_ids[0], "auth_token": token})
    receipt = b.get("receipt", {})
    check("cast vote returns a receipt", s == 200 and receipt.get("tx_hash") and receipt.get("block_index", 0) >= 1, b)
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/cast", {"candidate_id": cand_ids[0], "auth_token": token})
    check("replayed token / duplicate vote rejected (400)", s == 400, b)
    s, b = voter.call("POST", f"/api/voter/elections/{eid}/verify", {"aadhaar": me["aadhaar"]})
    check("verify after voting says already voted (400)", s == 400 and "already voted" in str(b), b)
    s, b = voter.call("GET", f"/api/voter/elections/{eid}")
    check("voter election now voted with ballot id", s == 200 and b["voted"] and b["ballot_id"] == receipt.get("ballot_id"), b)
    s, _ = voter.call("GET", f"/api/elections/{eid}/results")
    check("voter cannot see results before close (404)", s == 404)

    s, b = admin.call("GET", f"/api/elections/{eid}/results")
    check("admin sees provisional tally", s == 200 and b["total_votes"] == 1, b)
    s, b = admin.call("POST", f"/api/admin/elections/{eid}/status", {"status": "CLOSED"})
    check("close election", s == 200 and b["status"] == "CLOSED", b)
    s, b = voter.call("GET", f"/api/elections/{eid}/results")
    top = b["results"][0] if s == 200 else {}
    check("voter sees results after close", s == 200 and b["total_votes"] == 1 and top.get("votes") == 1 and top.get("candidate_id") == cand_ids[0], b)
    s, b = admin.call("GET", "/api/admin/benchmarks")
    check("benchmarks endpoint", s == 200 and "runs" in b, b)

    auditor = Client()
    s, b = auditor.login("auditor", "Audit@123")
    check("auditor login", s == 200 and b["user"]["role"] == "AUDITOR", b)
    s, b = auditor.call("GET", "/api/auditor/overview")
    check("auditor overview", s == 200 and b["chain"]["valid"] and len(b["validators"]) == 3 and b["blocks"], b if s != 200 else "")
    s, b = auditor.call("POST", "/api/auditor/verify")
    check("verify ledger integrity", s == 200 and b["valid"] is True, b)
    s, b = auditor.call("POST", "/api/auditor/tamper-test")
    check("tamper demo detects tampering", s == 200 and b.get("detected") is True, b)
    s, b = auditor.call("GET", f"/api/auditor/blocks/{receipt.get('block_index', 1)}")
    check("block detail contains the voter's transaction", s == 200 and any(t["tx_hash"] == receipt.get("tx_hash") for t in b["transactions"]) and len(b["signatures"]) >= 2, b if s != 200 else "")
    s, _ = auditor.call("GET", "/api/auditor/blocks/999999")
    check("unknown block is 404", s == 404)
    s, b = auditor.call("GET", "/api/health")
    check("ledger still valid after the run", s == 200 and b["chain_valid"] is True, b)

    web = Client(WEB)
    s, b = web.call("GET", "/")
    check("web app serves the SPA", s == 200 and "AegisBallot" in str(b))
    s, b = web.call("GET", "/api/health")
    check("web app proxies /api to the backend", s == 200 and b.get("status") == "ok", b)

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    time.sleep(0)
    main()
