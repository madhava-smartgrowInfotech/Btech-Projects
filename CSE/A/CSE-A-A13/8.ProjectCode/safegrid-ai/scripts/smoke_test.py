"""End-to-end smoke test of the main flow against a running SafeGrid-AI backend (and the frontend proxy if it is up).

Usage:  python scripts/smoke_test.py [backend_url] [frontend_url]
Defaults: http://127.0.0.1:8313  http://127.0.0.1:5313   (standard library only)
"""
import json
import sys
import urllib.error
import urllib.request

API = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8313").rstrip("/")
WEB = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5313").rstrip("/")
failures = []


def call(method, path, body=None, base=API):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw[:1] in "[{" else raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


s, h = call("GET", "/api/health")
check("health is ok", s == 200 and h.get("status") == "ok", h)

s, sc = call("GET", "/api/scenarios")
check("seven scenarios listed", s == 200 and len(sc) == 7, sc)

s, top = call("GET", "/api/grid/topology")
check("topology has nodes and edges", s == 200 and top.get("nodes") and top.get("edges"))

s, st = call("POST", "/api/simulation/reset", {"scenario_id": "unsafe_ai_action", "provider": "mock", "seed": 42, "step_delay_s": 0})
check("reset loads the unsafe-action scenario", s == 200 and st["step"] == 0 and st["scenario_id"] == "unsafe_ai_action", st)

for i in range(3):
    s, r = call("POST", "/api/simulation/step")
    check(f"step {i + 1} advances", s == 200 and r["status"]["step"] == i + 1, r)

s, g = call("GET", "/api/grid/state")
check("grid state has power-flow totals", s == 200 and "totals" in g and g["converged"], g if s != 200 else "")

s, ag = call("GET", "/api/agents")
check("three agents with a latest decision", s == 200 and len(ag) == 3 and all(a.get("latest") for a in ag))

aid = ag[0]["agent_id"]
s, d = call("GET", f"/api/agents/{aid}")
check("agent history is returned", s == 200 and d["history"] and d["latest"]["explanation"])

action = {"agent_id": "renewable_01", "action_type": "export_power", "power_kw": 1000, "duration_minutes": 15, "target_node": None, "reason_codes": ["OPERATOR_TEST"], "confidence": 1}
s, dr = call("POST", "/api/agents/renewable_01/decision", {"action": action})
check("dry run of an absurd export is not approved", s == 200 and dr["shield"]["status"] in ("rejected", "projected"), dr)

s, m = call("GET", "/api/metrics")
check("metrics carry a summary and series", s == 200 and m["series"] and m["summary"]["proposals"] > 0)

s, se = call("GET", "/api/safety/events")
check("safety log chain is valid", s == 200 and se["chain_valid"] is True, se if s != 200 else "")

s, c = call("GET", "/api/safety/constraints")
check("constraints expose voltage limits", s == 200 and c.get("v_min") == 0.95 and c.get("node_limits"))

s, r = call("POST", "/api/scenarios/high_solar/run", {"seed": 42, "provider": "mock", "step_delay_s": 0})
check("a scenario runs to completion", s == 200 and r["summary"]["proposals"] > 0, r if s != 200 else "")
check("no violations are caused by executed actions", s == 200 and r["summary"]["violations_caused_by_actions"] == 0)

s, ev = call("GET", "/api/events")
check("event log is readable", s == 200 and "events" in ev)

s, rs = call("GET", "/api/runs")
check("stored runs are listed", s == 200 and isinstance(rs, list))

s, _ = call("GET", "/api/agents/nobody")
check("unknown agent gives 404", s == 404)

try:
    s, h2 = call("GET", "/api/health", base=WEB)
    check("frontend proxy reaches the API", s == 200 and h2.get("status") == "ok")
except Exception:
    print("SKIP frontend proxy check (frontend not running)")

print("\n%s" % ("ALL CHECKS PASSED" if not failures else f"{len(failures)} CHECK(S) FAILED: {failures}"))
sys.exit(1 if failures else 0)
