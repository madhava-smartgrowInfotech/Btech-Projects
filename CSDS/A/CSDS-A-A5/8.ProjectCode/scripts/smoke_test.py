"""End-to-end smoke test against the running API (default http://127.0.0.1:8105).

Flow: health -> register + login -> generate a new ecosystem (small) and wait -> overview ->
risk ranking -> top taxpayer profile with evidence -> graph -> chains -> written explanation
(Gemini) -> metrics -> restore the default ecosystem (seed 42, 600 taxpayers).

Usage: python scripts/smoke_test.py [--base http://127.0.0.1:8105] [--skip-generate]
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8105"
TOKEN = None
results = []


def call(method, path, body=None, expect=200):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body else None)
    req.add_header("Content-Type", "application/json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            code, data = r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        code, data = e.code, json.loads(e.read() or b"null")
    if code != expect:
        raise AssertionError(f"{method} {path} -> {code} (expected {expect}): {data}")
    return data


def check(name, cond, info=""):
    results.append((name, bool(cond), info))
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {info}")
    if not cond:
        raise AssertionError(name)


def wait_run():
    for _ in range(300):
        st = call("GET", "/api/pipeline/status")
        if not st["running"]:
            return st
        time.sleep(1)
    raise AssertionError("pipeline run timed out")


def generate(seed, n):
    call("POST", "/api/pipeline/run", {"seed": seed, "taxpayers": n})
    st = wait_run()
    check(f"generate ecosystem seed={seed} n={n}", st["stage"] == "done" and st["current"]["seed"] == seed,
          st.get("error") or "")


def main():
    global BASE, TOKEN
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--skip-generate", action="store_true")
    a = ap.parse_args()
    BASE = a.base.rstrip("/")

    for _ in range(120):
        try:
            h = call("GET", "/api/health")
            if h["pipeline_ready"]:
                break
        except Exception:
            pass
        time.sleep(1)
    check("health + pipeline ready", h["pipeline_ready"])
    call("GET", "/api/overview", expect=401)
    check("protected routes need login", True)

    email = f"analyst{int(time.time())}@example.com"
    reg = call("POST", "/api/auth/register", {"name": "Smoke Analyst", "email": email, "password": "Sm0ke-test!"})
    TOKEN = reg["token"]
    check("register", bool(TOKEN))
    TOKEN = call("POST", "/api/auth/login", {"email": email, "password": "Sm0ke-test!"})["token"]
    check("login", call("GET", "/api/auth/me")["email"] == email)

    if not a.skip_generate:
        generate(7, 200)
        ov = call("GET", "/api/overview")
        check("overview reflects new ecosystem", ov["stats"]["taxpayers"] == 200 and ov["seed"] == 7,
              f"flagged={ov['stats']['flagged']}")
        generate(42, 600)

    ov = call("GET", "/api/overview")
    s = ov["stats"]
    check("overview counts", s["taxpayers"] > 0 and s["invoices"] > 0 and s["flagged"] > 0,
          f"taxpayers={s['taxpayers']} invoices={s['invoices']} flagged={s['flagged']} rings={s['rings']}")

    lst = call("GET", "/api/taxpayers?limit=10")
    risks = [t["risk"] for t in lst["items"]]
    check("risk ranking sorted", risks == sorted(risks, reverse=True), f"top risk={risks[0]}")
    ring_tp = call("GET", "/api/taxpayers?pattern=circular_trading&limit=5")["items"]
    check("circular-trading taxpayers found", len(ring_tp) > 0)

    top = lst["items"][0]
    prof = call("GET", f"/api/taxpayers/{top['gstin']}")
    check("top taxpayer profile has evidence", len(prof["evidence"]) > 0,
          f"{top['legal_name']}: {[e['title'] for e in prof['evidence'][:3]]}")
    check("monthly returns series", len(prof["monthly"]) == 12)

    rp = call("GET", f"/api/taxpayers/{ring_tp[0]['gstin']}")
    g = call("GET", f"/api/graph?focus={ring_tp[0]['gstin']}")
    check("graph shows circular-trading loop", any(l["ring"] for l in g["links"]) and len(rp["rings"]) > 0,
          f"nodes={len(g['nodes'])} links={len(g['links'])}")
    ov_graph = call("GET", "/api/graph")
    check("fraud network graph", len(ov_graph["nodes"]) > 0)
    st = call("GET", "/api/structures")
    check("rings and clusters listed", len(st["rings"]) > 0 and len(st["clusters"]) > 0,
          f"rings={len(st['rings'])} clusters={len(st['clusters'])}")
    ring_graph = call("GET", f"/api/graph?ring={st['rings'][0]['id']}")
    check("ring graph", all(l["ring"] for l in ring_graph["links"] if l["ring"]) and len(ring_graph["nodes"]) >= 2)

    chains = call("GET", "/api/chains")
    ch = call("GET", f"/api/chains/{chains[0]['id']}")
    check("invoice chain drill-down", len(ch["invoices"]) > 0, f"{ch['id']} score={ch['score']}")

    health = call("GET", "/api/health")
    if health["gemini_configured"]:
        ex = call("POST", f"/api/explanations/{top['gstin']}")
        q = ex["quality"]
        check("written explanation cites evidence", q["citations"] > 0 and q["invalid_citations"] == 0,
              f"model={ex['model']} citations={q['citations']} coverage={q['evidence_coverage']}")
        again = call("GET", f"/api/taxpayers/{top['gstin']}")
        check("explanation saved with case", again["explanation"] is not None)
    else:
        err = call("POST", f"/api/explanations/{top['gstin']}", expect=502)
        check("explanation reports missing GEMINI_API_KEY", "GEMINI_API_KEY" in err["detail"])
        print("       (set GEMINI_API_KEY in .env to test real explanations)")

    m = call("GET", "/api/metrics")
    ev = m["current"]["evaluation"]["taxpayer"]
    k = str(m["current"]["evaluation"]["n_fraud"])
    check("metrics vs rule baseline", "precision_at_k" in ev["model"] and "rule_baseline" in ev,
          f"P@{k} model={ev['model']['precision_at_k'][k]} baseline={ev['rule_baseline']['precision_at_k'][k]}")

    print(f"\nALL {len(results)} CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nSMOKE TEST FAILED: {e}")
        sys.exit(1)
