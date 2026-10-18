"""End-to-end smoke test for the Churn Intelligence API.

Start the backend first (run.bat, or `python -m uvicorn backend.main:app --port 8314`), then:
    python scripts/smoke_test.py [http://localhost:8314]
Exits 0 when every step passes. Uses only the standard library.
"""
import json
import sys
import urllib.error
import urllib.request
import uuid

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8314").rstrip("/")
TOKEN = None
FAILS = []


def call(method, path, body=None, files=None, expect=200):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    data = None
    if files:  # multipart: {"file": (name, bytes), **fields}
        boundary = uuid.uuid4().hex
        parts = []
        for k, v in files.items():
            if isinstance(v, tuple):
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{v[0]}"\r\n'
                             f'Content-Type: text/csv\r\n\r\n'.encode() + v[1] + b"\r\n")
            else:
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        data = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    text = raw.decode("utf-8", "replace")
    try:
        return status, json.loads(text)
    except ValueError:
        return status, text


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  -> {detail}" if not cond and detail else ""))
    if not cond:
        FAILS.append(name)


def step(name, method, path, expect=200, **kw):
    status, data = call(method, path, **kw)
    check(f"{name} [{status}]", status == expect, str(data)[:300])
    return data


def main():
    global TOKEN
    h = step("health", "GET", "/api/health")
    check("health ok", h.get("status") == "ok")

    status, _ = call("GET", "/api/state")
    check("protected route needs a token [401]", status == 401)
    status, _ = call("POST", "/api/auth/login", {"email": "demo@churniq.com", "password": "wrong"})
    check("bad password rejected [401]", status == 401)
    login = step("login", "POST", "/api/auth/login", body={"email": "demo@churniq.com", "password": "Demo@1234"})
    TOKEN = login["token"]
    step("me", "GET", "/api/auth/me")

    step("state", "GET", "/api/state")
    status, _ = call("GET", "/api/eda")
    check("eda before data is gated [409]", status == 409)

    sample = step("load sample", "POST", "/api/data/sample")
    check("sample detected target+id", sample["target_col"] == "Churn" and sample["id_col"] == "customerID")
    step("preview", "GET", "/api/data/preview")
    cfg = step("config", "GET", "/api/data/config")
    check("config has features", len(cfg["numeric_cols"]) + len(cfg["categorical_cols"]) == 19)
    q = step("quality", "GET", "/api/data/quality")
    check("dataset is training-ready", q["ready"] is True)
    prep = step("prepare", "POST", "/api/data/prepare")
    check("prepared rows", prep["rows_remaining"] == 1000)

    eda = step("eda", "GET", "/api/eda")
    check("eda kpis + charts", len(eda["kpis"]) == 7 and "Contract" in eda["by_category"] and eda["histogram"])
    f = json.dumps({"Contract": ["Two year"]})
    eda2 = step("eda filtered", "GET", "/api/eda?filters=" + urllib.parse.quote(f))
    check("filter narrows rows", eda2["filtered_rows"] < eda2["total_rows"])

    dash = step("dashboard (no model)", "GET", "/api/dashboard")
    check("dashboard stage", dash["stage"] in ("no_model", "ready"))

    status, _ = call("POST", "/api/models/train", {"models": []})
    check("train with no models rejected [422]", status == 422)
    tr = step("train", "POST", "/api/models/train", body={
        "test_size": 0.2, "imbalance_strategy": "class_weight",
        "models": ["Logistic Regression", "Decision Tree", "Random Forest"], "selection_metric": "f1_score"})
    check("3 models compared", len(tr["rows"]) == 3 and tr["recommended"])
    step("results", "GET", "/api/models/results")
    ev = step("evaluation", "GET", "/api/evaluation")
    check("curves + confusion", all(m["roc"] and m["pr"] and len(m["confusion"]) == 2 for m in ev["models"]))
    sv = step("save model", "POST", "/api/models/save", body={"name": tr["recommended"]})
    check("model active", sv["model"]["name"] == tr["recommended"])

    dash = step("dashboard", "GET", "/api/dashboard")
    check("dashboard ready with risk + drivers", dash["stage"] == "ready" and dash["risk"] and dash["at_risk"])
    rk = step("risk", "GET", "/api/risk?risk=High%20Risk,Critical%20Risk")
    check("risk summary", rk["summary"]["total"] == 1000)
    status, _ = call("PUT", "/api/risk/thresholds", {"low": 40, "medium": 42, "high": 90})
    check("bad thresholds rejected [422]", status == 422)
    step("thresholds", "PUT", "/api/risk/thresholds", body={"low": 25, "medium": 55, "high": 75})

    cust = step("customers", "GET", "/api/customers?limit=5")
    cid = cust["rows"][0]["id"]
    prof = step("customer 360", "GET", f"/api/customers/{cid}")
    check("profile complete", prof["groups"] and prof["recommendations"] and prof["risk"])
    status, _ = call("GET", "/api/customers/NOPE-0")
    check("unknown customer [404]", status == 404)
    step("xai global", "GET", "/api/xai/global")
    loc = step("xai local", "GET", f"/api/xai/local/{cid}")
    check("local explanation", loc["method"] in ("shap", "approximate"))

    sch = step("whatif schema", "GET", f"/api/whatif/schema?customer_id={cid}")
    check("schema fields", len(sch["fields"]) == 19 and sch["current"])
    wi = step("whatif", "POST", "/api/whatif", body={"customer_id": cid, "changes": {"Contract": "Two year", "tenure": 60}})
    check("whatif returns delta", wi["scenario"] != wi["original"] or wi["verdict"] == "none")

    rt = step("retention", "GET", "/api/retention?risk=High%20Risk,Critical%20Risk&limit=20")
    check("retention rows", rt["customers"] > 0 and rt["rows"])

    status, tpl = call("GET", "/api/batch/template")
    check("batch template csv", status == 200 and isinstance(tpl, str) and "tenure" in tpl.splitlines()[0])
    bp = step("batch predict", "POST", "/api/batch/predict", files={"file": ("batch.csv", tpl.encode()), "include_drivers": "true"})
    check("batch scored 25", bp["total"] == 25 and bp["rows"][0]["top_risk_factor_1"] != "")
    status, bad = call("POST", "/api/batch/predict", files={"file": ("bad.csv", b"a,b\n1,2\n"), "include_drivers": "false"})
    check("batch missing columns [422]", status == 422 and "Missing" in str(bad))

    mon = step("monitoring", "GET", "/api/monitoring")
    check("monitoring metadata", mon["name"] and mon["metrics"])
    dr = step("drift", "POST", "/api/monitoring/drift", files={"file": ("new.csv", tpl.encode())})
    check("drift report", dr["rows"] == 25 and dr["mean_comparison"])

    up = step("upload csv", "POST", "/api/data/upload", files={"file": ("mine.csv", sample_csv())})
    check("upload detected target", up["target_col"] == "Churn")
    status, _ = call("POST", "/api/data/upload", files={"file": ("notes.txt", b"hi")})
    check("non-csv rejected [422]", status == 422)
    step("re-sample", "POST", "/api/data/sample")
    step("re-prepare", "POST", "/api/data/prepare")

    print()
    if FAILS:
        print(f"{len(FAILS)} check(s) FAILED: {', '.join(FAILS)}")
        sys.exit(1)
    print("All smoke checks passed.")


def sample_csv() -> bytes:
    rows = ["customerID,tenure,Contract,MonthlyCharges,TotalCharges,Churn"]
    for i in range(80):
        rows.append(f"C{i},{i % 70},{'Month-to-month' if i % 3 else 'Two year'},{30 + i % 60},{(30 + i % 60) * (i % 70 + 1)},{'Yes' if i % 4 == 0 else 'No'}")
    return ("\n".join(rows) + "\n").encode()


if __name__ == "__main__":
    import urllib.parse  # noqa: F401  (used above via urllib.parse.quote)
    main()
