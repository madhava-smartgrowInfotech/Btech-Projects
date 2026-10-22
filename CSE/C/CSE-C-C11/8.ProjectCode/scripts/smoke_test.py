"""End-to-end API smoke test for FINJARVIS.

Starts its own backend on a spare port with a throw-away SQLite file (your finjarvis.db is never touched),
then walks the main flow: demo login, sign-up, add / edit / delete transactions, CSV import, budgets, goals,
investments, assistant, reports, notifications, and per-user data isolation.

Run from the project root with the project's interpreter:
    .venv\\Scripts\\python.exe scripts\\smoke_test.py
"""
from __future__ import annotations

import io
import os
import socket
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    checks.append((name, bool(condition), detail))
    print(("PASS  " if condition else "FAIL  ") + name + (f"   [{detail}]" if detail and not condition else ""), flush=True)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    port = free_port()
    tmp = tempfile.mkdtemp(prefix="finjarvis_smoke_")
    env = {**os.environ, "FINJARVIS_DB": os.path.join(tmp, "smoke.db"), "PYTHONIOENCODING": "utf-8"}
    log = open(os.path.join(tmp, "server.log"), "w")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}/api"
    try:
        for _ in range(90):
            try:
                if requests.get(f"{base}/health", timeout=1).ok:
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            print("Backend did not start; see", os.path.join(tmp, "server.log"))
            return 2

        s = requests.Session()
        today = date.today()

        # --- auth
        check("health endpoint", s.get(f"{base}/health").json()["status"] == "ok")
        check("protected route needs a token", s.get(f"{base}/dashboard").status_code == 401)
        r = s.post(f"{base}/auth/login", json={"identifier": "demo", "password": "Demo@1234"})
        check("demo account can log in", r.status_code == 200 and r.json()["user"]["username"] == "demo", r.text[:120])
        demo = {"Authorization": f"Bearer {r.json()['token']}"}
        check("wrong password rejected", s.post(f"{base}/auth/login", json={"identifier": "demo", "password": "nope"}).status_code == 401)
        check("weak password rejected on sign-up", s.post(f"{base}/auth/signup", json={
            "name": "A B", "email": "a@b.com", "username": "weakuser", "password": "abc", "confirm_password": "abc"}).status_code == 400)

        # --- demo data is real and current
        dash = s.get(f"{base}/dashboard", headers=demo).json()
        check("demo dashboard has current-month income", dash["metrics"]["monthly_income"] > 0, str(dash["metrics"]))
        check("health score is 0-100", 0 <= dash["health"]["score"] <= 100)
        check("six chart datasets returned", all(k in dash["charts"] for k in ("category_spend", "trend", "allocation", "budget_vs_actual", "goals")))
        show = s.get(f"{base}/public/showcase").json()
        check("public showcase works without login", show["metrics"]["net_worth"] != 0 and "answer" in show["assistant"])

        # --- new user, isolation
        u = {"name": "Smoke Tester", "email": "smoke@example.com", "username": "smoketest", "password": "Smoke@1234", "confirm_password": "Smoke@1234"}
        check("sign-up works", s.post(f"{base}/auth/signup", json=u).status_code == 201)
        check("duplicate sign-up rejected", s.post(f"{base}/auth/signup", json=u).status_code == 409)
        tok = s.post(f"{base}/auth/login", json={"identifier": "smoke@example.com", "password": u["password"]}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        check("new user starts empty", s.get(f"{base}/transactions", headers=h).json()["total"] == 0)

        # --- transactions
        r = s.post(f"{base}/transactions", headers=h, json={"date": today.isoformat(), "description": "Swiggy order", "amount": 450, "transaction_type": "expense"})
        check("auto-categorised expense", r.status_code == 201 and r.json()["category"] == "Food" and r.json()["auto_categorised"], r.text)
        txn_id = r.json()["id"]
        check("income added", s.post(f"{base}/transactions", headers=h, json={"date": today.isoformat(), "description": "Monthly salary", "amount": 65000,
                                                                              "transaction_type": "income", "category": "Salary"}).status_code == 201)
        check("zero amount rejected", s.post(f"{base}/transactions", headers=h, json={"date": today.isoformat(), "description": "x", "amount": 0, "transaction_type": "expense"}).status_code == 400)
        lst = s.get(f"{base}/transactions", headers=h, params={"q": "swiggy"}).json()
        check("search finds the expense", lst["total"] == 1 and lst["expense"] == 450)
        check("edit transaction", s.put(f"{base}/transactions/{txn_id}", headers=h, json={"amount": 500, "category": "Shopping"}).ok)
        check("edit persisted", s.get(f"{base}/transactions", headers=h).json()["items"][-1]["amount"] in (500, 65000))
        check("other user cannot touch it", s.put(f"{base}/transactions/{txn_id}", headers=demo, json={"amount": 1}).status_code == 404)
        check("other user cannot delete it", s.delete(f"{base}/transactions/{txn_id}", headers=demo).status_code == 404)
        check("delete transaction", s.delete(f"{base}/transactions/{txn_id}", headers=h).ok)
        check("deleted transaction is gone", s.delete(f"{base}/transactions/{txn_id}", headers=h).status_code == 404)

        # --- import
        csv = f"date,description,amount,category,type\n{today},Uber ride,220,,expense\n{today},Netflix subscription,649,Entertainment,expense\nbad,Broken,1,Food,expense\n"
        r = s.post(f"{base}/transactions/import/preview", headers=h, files={"file": ("t.csv", io.BytesIO(csv.encode()), "text/csv")})
        check("import preview: 2 valid, 1 skipped", r.ok and r.json()["valid"] == 2 and len(r.json()["warnings"]) == 1, r.text[:200])
        check("import fills a blank category", r.json()["rows"][0]["category"] == "Transport", str(r.json()["rows"][:1]))
        r = s.post(f"{base}/transactions/import/commit", headers=h, files={"file": ("t.csv", io.BytesIO(csv.encode()), "text/csv")})
        check("import commit", r.ok and r.json()["imported"] == 2)
        bad = s.post(f"{base}/transactions/import/preview", headers=h, files={"file": ("t.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")})
        check("import with missing columns gives a clear error", bad.status_code == 400 and "Missing required" in bad.text)

        # --- budgets, goals, investments
        r = s.post(f"{base}/budgets", headers=h, json={"category": "Transport", "budget_amount": 200, "month": today.month, "year": today.year})
        check("budget saved", r.status_code == 201)
        b = s.get(f"{base}/budgets", headers=h).json()["items"][0]
        check("budget shows overspend (220 of 200)", b["actual_spent"] == 220 and b["percent_used"] >= 100, str(b))
        check("alert notification raised", s.get(f"{base}/notifications", headers=h).json()["unread"] >= 1)
        check("mark all read", s.post(f"{base}/notifications/read-all", headers=h).ok and s.get(f"{base}/notifications", headers=h).json()["unread"] == 0)
        check("delete budget", s.delete(f"{base}/budgets/{b['id']}", headers=h).ok)

        r = s.post(f"{base}/goals", headers=h, json={"goal_name": "Laptop", "target_amount": 60000, "current_amount": 10000, "target_date": (today + timedelta(days=150)).isoformat()})
        gid = r.json()["id"]
        g = s.get(f"{base}/goals", headers=h).json()["items"][0]
        check("goal progress and monthly saving", round(g["percent_complete"]) == 17 and g["required_monthly_savings"] > 0, str(g))
        s.put(f"{base}/goals/{gid}", headers=h, json={"current_amount": 60000})
        check("goal completes at target", s.get(f"{base}/goals", headers=h).json()["items"][0]["status"] == "completed")
        check("delete goal", s.delete(f"{base}/goals/{gid}", headers=h).ok)

        r = s.post(f"{base}/investments", headers=h, json={"asset_name": "Test ETF", "symbol": "", "asset_type": "ETF", "quantity": 10, "purchase_price": 100,
                                                          "current_price": 120, "purchase_date": today.isoformat()})
        pf = s.get(f"{base}/investments", headers=h).json()
        check("portfolio P/L is 200 (20%)", pf["total_profit_loss"] == 200 and pf["total_return_percent"] == 20.0, str(pf)[:200])
        check("refresh without a symbol degrades gracefully", s.post(f"{base}/investments/{r.json()['id']}/refresh", headers=h).json()["success"] is False)
        check("delete investment", s.delete(f"{base}/investments/{r.json()['id']}", headers=h).ok)

        # --- analytics, assistant, reports, profile
        a = s.get(f"{base}/analytics", headers=demo).json()
        check("analytics for demo user has a prediction", a["prediction"]["available"] and a["prediction"]["predicted_next_month_expense"] > 0)
        a2 = s.get(f"{base}/analytics", headers=h).json()
        check("analytics for 1-month user refuses to predict", a2["prediction"]["available"] is False and "Need at least" in a2["prediction"]["message"])
        check("analytics bad range rejected", s.get(f"{base}/analytics", headers=h, params={"start": "2026-12-31", "end": "2026-01-01"}).status_code == 400)
        ans = s.post(f"{base}/assistant/ask", headers=demo, json={"question": "Where am I spending the most money?"}).json()
        check("assistant answers from the user's data", "biggest spending category" in ans["answer"] and ans["disclaimer"])
        check("insights returned", len(s.get(f"{base}/assistant/insights", headers=demo).json()["insights"]) >= 1)
        for kind, magic in (("pdf", b"%PDF"), ("excel", b"PK"), ("csv", b"id,date")):
            r = s.get(f"{base}/reports/{kind}", headers=demo)
            check(f"{kind} report downloads", r.ok and r.content[:len(magic)] == magic, f"{r.status_code} {r.content[:12]!r}")
        check("profile update", s.put(f"{base}/profile", headers=h, json={"name": "Smoke Renamed", "email": "smoke@example.com", "monthly_income": 50000,
                                                                          "currency": "USD", "risk_profile": "Aggressive", "savings_target": 1000}).json()["currency"] == "USD")
        check("profile with duplicate email rejected", s.put(f"{base}/profile", headers=h, json={"name": "x", "email": "demo@finjarvis.com", "monthly_income": 0,
                                                                                               "currency": "INR", "risk_profile": "Moderate", "savings_target": 0}).status_code == 409)
        check("demo data loader", s.post(f"{base}/profile/demo-data", headers=h).json()["transactions"] > 0)
        check("tampered token rejected", s.get(f"{base}/dashboard", headers={"Authorization": f"Bearer {tok[:-3]}abc"}).status_code == 401)
    finally:
        server.terminate()
        try:
            server.wait(10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()

    failed = [c for c in checks if not c[1]]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
