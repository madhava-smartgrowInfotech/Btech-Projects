"""End-to-end smoke test: starts its own API on a spare port with a scratch database and scratch copies of the
model files, then drives the real API through the main flow (login -> graph -> scores -> botnets -> moderator
decisions -> retraining on those decisions). Your demo database and trained models are never touched.

    python scripts/smoke_test.py            # whole flow including retraining (about a minute)
    python scripts/smoke_test.py --no-retrain
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 13091
BASE = f"http://127.0.0.1:{PORT}"
PASSWORD = "Demo@1234"

passed = 0


def check(cond: bool, label: str, detail: str = "") -> None:
    global passed
    if not cond:
        print(f"  FAIL  {label} {detail}")
        raise SystemExit(f"smoke test failed: {label} {detail}")
    passed += 1
    print(f"  ok    {label}")


def call(method: str, path: str, token: str | None = None, body: dict | None = None, expect: int | None = 200):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status, data = r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        status, data = e.code, json.loads(e.read() or b"null")
    if expect is not None and status != expect:
        raise SystemExit(f"{method} {path} returned {status}, expected {expect}: {data}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-retrain", action="store_true")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="botgraph_smoke_"))
    shutil.copytree(ROOT / "models", tmp / "models")
    shutil.copytree(ROOT / "experiments", tmp / "experiments")
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{(tmp / 'smoke.db').as_posix()}",
        "BOTGRAPH_MODELS_DIR": str(tmp / "models"),
        "BOTGRAPH_EXPERIMENTS_DIR": str(tmp / "experiments"),
        "PYTHONWARNINGS": "ignore",
    }
    log = open(tmp / "server.log", "w")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(90):
            try:
                if call("GET", "/api/health", expect=None).get("status") == "ok":
                    break
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(1)
        else:
            raise SystemExit("API did not start; see " + str(tmp / "server.log"))

        print("health and login")
        h = call("GET", "/api/health")
        check(h["accounts"] > 4000 and h["edges"] > 50000, "health reports the graph size", str(h))
        call("GET", "/api/overview", expect=401)
        check(True, "protected routes reject anonymous requests")
        call("POST", "/api/auth/login", body={"email": "moderator@botgraph.app", "password": "wrong"}, expect=401)
        check(True, "wrong password is rejected")
        mod = call("POST", "/api/auth/login", body={"email": "moderator@botgraph.app", "password": PASSWORD})
        ana = call("POST", "/api/auth/login", body={"email": "analyst@botgraph.app", "password": PASSWORD})
        check(mod["user"]["role"] == "moderator" and ana["user"]["role"] == "analyst", "demo moderator and analyst can sign in")
        tm, ta = mod["token"], ana["token"]

        print("F1/F2 graph and features")
        g = call("GET", "/api/graph/summary", tm)
        check(g["nodes"] == g["real_nodes"] + g["injected_nodes"] and g["edges"] == g["real_edges"] + g["injected_edges"], "node and edge counts add up")
        check(g["n_features"] == len(g["features"]) >= 20, "feature summary lists every feature", str(g["n_features"]))
        check(0.05 < g["fake_share"] < 0.25, "labels are imbalanced", f"{g['fake_share']:.3f}")

        print("F3/F7 model comparison and scalability")
        m = call("GET", "/api/models", tm)
        by = {x["name"]: x for x in m["models"]}
        base = by["baseline"]["f1"]["mean"]
        for arch in ("gcn", "gat", "sage"):
            check(by[arch]["f1"]["mean"] > base, f"{by[arch]['label']} beats the no-graph baseline", f"{by[arch]['f1']['mean']:.3f} vs {base:.3f}")
        check(by[m["best"]]["is_best"], "best architecture is flagged")
        sc = call("GET", "/api/models/scalability", tm)
        check(len(sc["rows"]) >= 3 and sc["rows"][-1]["nodes"] > sc["rows"][0]["nodes"] * 4, "scalability sweep covers a growing graph")
        check(sc["rows"][-1]["models"]["gcn"]["train_seconds_per_epoch"] > sc["rows"][0]["models"]["gcn"]["train_seconds_per_epoch"], "training time grows with the graph")

        print("F4 account scoring")
        page = call("GET", "/api/accounts?page_size=10", tm)
        scores = [a["score"] for a in page["items"]]
        check(scores == sorted(scores, reverse=True) and scores[0] > 0.9, "accounts are ranked by fake-probability")
        top = page["items"][0]
        d = call("GET", f"/api/accounts/{top['id']}", tm)
        check(len(d["explanation"]["top"]) >= 5, "account detail lists its top contributing features")
        check(d["neighbourhood"]["degree"] > 0 and d["history"] == [], "account detail summarises the neighbourhood")
        nb = call("GET", f"/api/accounts/{top['id']}/neighbourhood", tm)
        check(len(nb["nodes"]) > 1 and len(nb["links"]) >= 1 and any(n["ego"] for n in nb["nodes"]), "neighbourhood graph has nodes and links")
        found = call("GET", f"/api/accounts?q={top['handle'][:6]}&page_size=5", tm)
        check(found["total"] >= 1, "search finds an account by handle")
        call("GET", "/api/accounts/99999999", tm, expect=404)
        check(True, "unknown account id returns 404")

        print("F5 botnet clusters")
        cl = call("GET", "/api/clusters", tm)["items"]
        coordinated = [c for c in cl if c["kind"] == "coordinated"]
        rec = m["cluster_recovery"]
        check(len(coordinated) >= 6, "coordinated botnets were found", f"{len(coordinated)}")
        check(rec["recovered"] >= 6, "injected botnets are recovered as single communities", f"{rec['recovered']}/{rec['botnets']}")
        cd = call("GET", f"/api/clusters/{coordinated[0]['id']}", tm)
        check(len(cd["members"]) == cd["size"] and len(cd["graph"]["links"]) > cd["size"], "cluster detail has members and an interactive graph")

        print("F6 moderator queue")
        q0 = call("GET", "/api/queue?kind=accounts", tm)["summary"]
        call("POST", "/api/queue/decisions", ta, {"target_type": "account", "target_id": str(top["id"]), "decision": "confirm"}, expect=403)
        check(True, "analyst cannot record decisions")
        r1 = call("POST", "/api/queue/decisions", tm, {"target_type": "account", "target_id": str(top["id"]), "decision": "confirm", "note": "smoke test"}, expect=201)
        second = page["items"][1]
        r2 = call("POST", "/api/queue/decisions", tm, {"target_type": "account", "target_id": str(second["id"]), "decision": "dismiss"}, expect=201)
        r3 = call("POST", "/api/queue/decisions", tm, {"target_type": "cluster", "target_id": coordinated[0]["id"], "decision": "confirm"}, expect=201)
        q1 = call("GET", "/api/queue?kind=accounts", tm)["summary"]
        check(q1["confirmed"] == q0["confirmed"] + 2 and q1["dismissed"] == q0["dismissed"] + 1, "decisions are counted")
        check(q1["pending_accounts"] < q0["pending_accounts"] - 2, "a cluster decision clears its member accounts from the queue")
        log_items = call("GET", "/api/decisions", tm)["items"]
        check(len(log_items) == 3 and log_items[0]["by"] == "Demo Moderator", "decisions are logged with who made them")
        check(call("GET", f"/api/accounts/{top['id']}", tm)["status"] == "confirmed", "account status reflects the decision")
        call("DELETE", f"/api/queue/decisions/{r2['id']}", tm)
        check(len(call("GET", "/api/decisions", tm)["items"]) == 2, "a decision can be undone before it is used in training")

        if args.no_retrain:
            print("(retraining skipped)")
        else:
            print("decisions feed the next training run")
            call("POST", "/api/models/retrain", ta, expect=403)
            check(True, "analyst cannot retrain")
            call("POST", "/api/models/retrain", tm, expect=202)
            t0 = time.time()
            while time.time() - t0 < 600:
                st = call("GET", "/api/models/retrain/status", tm)
                if st["state"] in ("done", "error"):
                    break
                time.sleep(3)
            check(st["state"] == "done", "retraining finished", str(st))
            m2 = call("GET", "/api/models", tm)
            run = m2["runs"][0]
            check(run["status"] == "done" and run["feedback_labels"] > 50, "run recorded with the number of labels used", str(run["feedback_labels"]))
            check(set(run["f1_after"]) == {"baseline", "gcn", "gat", "sage"}, "before and after F1 recorded for every model")
            check(m2["latest_retrain"] is not None and m2["meta"]["kind"] == "retrain", "retrained model is now served")
            used = call("GET", "/api/decisions", tm)["items"]
            check(all(i["used_in_run"] == run["id"] for i in used), "decisions are marked as used in that run")
            call("DELETE", f"/api/queue/decisions/{used[0]['id']}", tm, expect=409)
            check(True, "a used decision cannot be undone")
            check(call("GET", "/api/health", tm)["accounts"] == g["nodes"], "API still serves the full graph after retraining")

        print(f"\nsmoke test passed ({passed} checks)")
        return 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
