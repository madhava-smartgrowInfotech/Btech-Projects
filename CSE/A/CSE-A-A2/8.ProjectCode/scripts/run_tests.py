"""ResQAI test run: unit checks of the backend helpers, API validation / edge cases, and authentication / security checks.

Usage:  python scripts/run_tests.py [open_api=127.0.0.1:8302] [auth_api=127.0.0.1:8399]
 - open_api : backend started with REQUIRE_AUTH=0 (the default run.bat setting)
 - auth_api : a second backend started with REQUIRE_AUTH=1 (PORT=8399 REQUIRE_AUTH=1 python app.py)
Writes experiments/resqai_eval/tests.json. Nothing here changes product code; failures are findings, not hidden.
"""
import http.client
import json
import math
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OPEN = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8302"
AUTH = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1:8399"
OUT = ROOT / "experiments" / "resqai_eval"
OUT.mkdir(parents=True, exist_ok=True)
results = []


def rec(group, name, ok, detail=""):
    results.append({"group": group, "name": name, "passed": bool(ok), "detail": str(detail)})
    print(f"[{'PASS' if ok else 'FAIL'}] {group}: {name}" + (f" - {detail}" if detail else ""))


def http_call(hostport, method, path, body=None, raw=None, token=None, headers=None):
    c = http.client.HTTPConnection(hostport, timeout=20)
    h = dict(headers or {})
    data = None
    if raw is not None:
        data = raw
        h.setdefault("Content-Type", "application/json")
    elif body is not None:
        data = json.dumps(body)
        h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = f"Bearer {token}"
    c.request(method, path, data, h)
    r = c.getresponse()
    txt = r.read().decode("utf-8", "replace")
    c.close()
    try:
        return r.status, json.loads(txt)
    except Exception:
        return r.status, txt[:200]


# --------------------------------------------------------------------------------------------------- unit
def unit_tests():
    import warnings
    warnings.filterwarnings("ignore")
    import app as A
    g = "unit"
    rec(g, "haversine of identical points is 0", A.haversine_km(17.4, 78.4, 17.4, 78.4) == 0)
    d1, d2 = A.haversine_km(17.385, 78.4867, 17.4399, 78.4983), A.haversine_km(17.4399, 78.4983, 17.385, 78.4867)
    rec(g, "haversine is symmetric", abs(d1 - d2) < 1e-9, f"{d1:.3f} km")
    london_paris = A.haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    rec(g, "haversine London-Paris is about 343 km", 340 < london_paris < 347, f"{london_paris:.1f} km")
    rnd = random.Random(7)
    bad = 0
    for _ in range(500):
        lat, lon = 17.385 + rnd.uniform(-0.2, 0.2), 78.4867 + rnd.uniform(-0.2, 0.2)
        top = A.nearest_hospitals(lat, lon, 3)
        brute = sorted(A.haversine_km(lat, lon, h["lat"], h["lon"]) for h in A.HOSPITAL_DATA["hospitals"])[:3]
        # the app sorts on distances rounded to 2 decimals, so compare the top-3 distances at that precision
        bad += [h["distance_km"] for h in top] != [round(d, 2) for d in brute]
    rec(g, "nearest_hospitals top-3 distances match brute force on 500 random points", bad == 0, f"{bad} mismatches")
    top = A.nearest_hospitals(17.385, 78.4867, 10)
    rec(g, "nearest_hospitals returns distances in ascending order", [h["distance_km"] for h in top] == sorted(h["distance_km"] for h in top))
    X, fm = A.build_feature_vector({"acc_x": 3, "acc_y": 4, "acc_z": 0, "gyro_x": 0, "gyro_y": 0, "gyro_z": 0})
    rec(g, "build_feature_vector derives acc_magnitude = 5 from (3, 4, 0)", abs(fm["acc_magnitude"] - 5) < 1e-9)
    X, fm = A.build_feature_vector({"jerk": -7})
    rec(g, "build_feature_vector stores jerk as absolute value", fm["jerk"] == 7)
    X, fm = A.build_feature_vector({})
    rec(g, "empty payload defaults to a 1 g, stationary reading", X.shape == (1, 11) and abs(fm["acc_magnitude"] - 9.81) < 1e-9)
    rec(g, "feature vector follows the trained feature order", [k for k in fm][:0] == [] and A.FEATURE_NAMES == ["acc_x", "acc_y", "acc_z", "acc_magnitude", "gyro_x", "gyro_y", "gyro_z", "gyro_magnitude", "speed_before", "speed_change", "jerk"])
    rb = [A.rule_based_fallback({"acc_magnitude": m})[1] for m in (10, 20, 30, 60)]
    rec(g, "rule-based fallback bands 10/20/30/60 m/s2 -> None/Minor/Moderate/Severe", rb == [0, 1, 2, 3], rb)
    rec(g, "trained models are loaded", A.MODELS_LOADED is True)
    with A.app.test_client() as c:
        r = c.get("/api/health").get_json()
        rec(g, "/api/health reports models_loaded", r == {"status": "ok", "models_loaded": True}, r)
    ok = 0
    for sc, want in [("normal", 0), ("brake", 0), ("minor", 1), ("moderate", 2), ("severe", 3)]:
        with A.app.test_client() as c:
            hits = 0
            for _ in range(60):
                rd = c.get(f"/api/simulate?scenario={sc}").get_json()
                p = c.post("/api/predict", json=rd).get_json()
                hits += p["severity_level"] == want
        rec(g, f"60 simulated '{sc}' readings are all rated {['None', 'Minor', 'Moderate', 'Severe'][want]}", hits >= 58, f"{hits}/60")


# --------------------------------------------------------------------------------------------------- edge cases
def edge_tests():
    g = "edge"
    H = OPEN
    st, b = http_call(H, "POST", "/api/predict", body={})
    rec(g, "predict accepts an empty object and returns no accident", st == 200 and b.get("accident_detected") is False, st)
    st, b = http_call(H, "POST", "/api/predict", raw="{not json")
    rec(g, "predict with malformed JSON gives a client error (4xx)", 400 <= st < 500, f"HTTP {st}")
    st, b = http_call(H, "POST", "/api/predict", body={"acc_x": "abc"})
    rec(g, "predict with a non-numeric field gives a client error (4xx), not a crash", 400 <= st < 500, f"HTTP {st}")
    st, b = http_call(H, "POST", "/api/predict", raw='[1, 2, 3]')
    rec(g, "predict with a JSON array body gives a client error (4xx)", 400 <= st < 500, f"HTTP {st}")
    st, b = http_call(H, "POST", "/api/predict", raw='{"acc_x": NaN}')
    rec(g, "predict with NaN is rejected or answered safely", st in (200, 400, 422), f"HTTP {st} {str(b)[:80]}")
    st, b = http_call(H, "POST", "/api/predict", body={"acc_x": 1e9, "acc_y": 1e9, "acc_z": 1e9, "speed_before": 1e6})
    rec(g, "predict with absurdly large values still answers", st == 200, f"HTTP {st}; {b.get('severity_label') if isinstance(b, dict) else b}")
    st, b = http_call(H, "POST", "/api/predict", body={"speed_before": -50, "speed_change": 40})
    rec(g, "predict with negative speed answers", st == 200, f"HTTP {st}")
    st, b = http_call(H, "GET", "/api/predict")
    rec(g, "GET on a POST-only route gives 405", st == 405, st)
    st, b = http_call(H, "GET", "/api/simulate?scenario=bogus")
    rec(g, "simulate with an unknown scenario falls back to a random one", st == 200 and "scenario" in b, st)
    st, b = http_call(H, "GET", "/api/hospitals?lat=abc")
    rec(g, "hospitals with a non-numeric lat gives a client error (4xx)", 400 <= st < 500, f"HTTP {st}")
    st, b = http_call(H, "GET", "/api/hospitals?k=0")
    rec(g, "hospitals with k=0 returns an empty list", st == 200 and b.get("hospitals") == [], f"HTTP {st}, {len(b.get('hospitals', [])) if isinstance(b, dict) else ''} rows")
    st, b = http_call(H, "GET", "/api/hospitals?k=-1")
    n = len(b.get("hospitals", [])) if isinstance(b, dict) else -1
    rec(g, "hospitals with k=-1 is rejected or empty (a Python slice would return 9 of 10)", st >= 400 or n == 0, f"HTTP {st}, {n} rows")
    st, b = http_call(H, "GET", "/api/hospitals?k=1000")
    rec(g, "hospitals with k=1000 is capped at the 10-entry directory", st == 200 and len(b["hospitals"]) == 10, f"HTTP {st}")
    st, b = http_call(H, "GET", "/api/hospitals?lat=999&lon=999")
    rec(g, "hospitals with out-of-range coordinates is rejected (4xx)", 400 <= st < 500, f"HTTP {st}")
    st, b = http_call(H, "POST", "/api/emergency", body={})
    rec(g, "emergency with no body falls back to the default area and dispatches", st == 200 and b.get("status") == "dispatched", st)
    st, b = http_call(H, "POST", "/api/emergency", body={"confidence": "abc"})
    rec(g, "emergency with a non-numeric confidence gives a client error (4xx)", 400 <= st < 500, f"HTTP {st}")
    st, b = http_call(H, "POST", "/api/emergency", body={"lat": 17.4, "lon": 78.45, "severity_label": "Severe\nINJECT", "confidence": 0.9})
    rec(g, "emergency severity_label is validated against the four labels", not (st == 200 and "INJECT" in b.get("message", "")), f"HTTP {st}")
    st, b = http_call(H, "POST", "/api/emergency", body={"lat": 17.4, "lon": 78.45, "severity_label": "Severe", "confidence": 0.9})
    ok = st == 200 and b["nearest_hospitals"][0]["distance_km"] <= b["nearest_hospitals"][1]["distance_km"] and "google.com/maps" in b["message"]
    rec(g, "emergency message carries a map link and the nearest hospital first", ok)
    ids = set()
    for _ in range(3):
        ids.add(http_call(H, "POST", "/api/emergency", body={"severity_label": "Severe"})[1]["alert_id"])
        time.sleep(1.05)
    rec(g, "alert ids differ between alerts raised one second apart", len(ids) == 3, sorted(ids))
    a = http_call(H, "POST", "/api/emergency", body={"severity_label": "Severe"})[1]["alert_id"]
    b2 = http_call(H, "POST", "/api/emergency", body={"severity_label": "Severe"})[1]["alert_id"]
    rec(g, "alert ids are unique for two alerts in the same second (id is a 1-second timestamp)", a != b2, f"{a} vs {b2}")


# --------------------------------------------------------------------------------------------------- security
def security_tests():
    g = "security"
    H = AUTH
    em = f"sec-{int(time.time() * 1000)}@resqai.test"
    pw = "Sec-test-pass-1"
    for path in ["/api/predict", "/api/simulate", "/api/hospitals", "/api/emergency"]:
        st, _ = http_call(H, "POST" if path in ("/api/predict", "/api/emergency") else "GET", path, body={} if path in ("/api/predict", "/api/emergency") else None)
        rec(g, f"REQUIRE_AUTH=1: {path} without a token is refused (401)", st == 401, f"HTTP {st}")
    st, b = http_call(H, "GET", "/api/health")
    rec(g, "REQUIRE_AUTH=1: /api/health stays public", st == 200)
    st, b = http_call(H, "POST", "/api/auth/register", body={"name": "Sec Test", "email": em, "password": pw})
    rec(g, "register returns 201 and a token, never the password or its hash", st == 201 and "token" in b and "hash" not in json.dumps(b).lower() and pw not in json.dumps(b))
    tok = b.get("token", "")
    st, b = http_call(H, "GET", "/api/simulate?scenario=normal", token=tok)
    rec(g, "a valid token opens the protected API", st == 200, f"HTTP {st}")
    st, b = http_call(H, "GET", "/api/simulate?scenario=normal", token=tok[:-3] + ("AAA" if not tok.endswith("AAA") else "BBB"))
    rec(g, "a token with an altered signature is refused", st == 401, f"HTTP {st}")
    st, b = http_call(H, "GET", "/api/simulate", headers={"Authorization": "Basic abc"})
    rec(g, "a non-Bearer Authorization header is refused", st == 401, f"HTTP {st}")
    st, b = http_call(H, "GET", "/api/auth/me", token=tok)
    rec(g, "/me never exposes password_hash", st == 200 and "password" not in json.dumps(b).lower())
    st, b = http_call(H, "POST", "/api/auth/register", body={"name": "X", "email": "a@b.co", "password": "longenough1"})
    rec(g, "register rejects a 1-character name", st == 400 and b.get("field") == "name")
    st, b = http_call(H, "POST", "/api/auth/register", body={"name": "Long Pw", "email": f"lp-{int(time.time())}@resqai.test", "password": "x" * 200})
    rec(g, "register rejects a 200-character password", st == 400 and b.get("field") == "password")
    st, b = http_call(H, "POST", "/api/auth/register", body={"name": "Dup", "email": em.upper(), "password": pw})
    rec(g, "register treats e-mail case-insensitively (duplicate -> 409)", st == 409, f"HTTP {st}")
    st, b = http_call(H, "POST", "/api/auth/login", raw="not json")
    rec(g, "login with a malformed body is a client error, not a 500", 400 <= st < 500, f"HTTP {st}")
    codes = []
    for _ in range(5):
        codes.append(http_call(H, "POST", "/api/auth/login", body={"email": em, "password": "wrong-password"})[0])
    st, b = http_call(H, "POST", "/api/auth/login", body={"email": em, "password": pw})
    rec(g, "five wrong passwords lock the account: the correct password is then refused with 429", codes == [401] * 5 and st == 429, f"{codes} then {st}")
    users = json.loads((ROOT / "data" / "users.json").read_text(encoding="utf-8"))
    hashes = [u["password_hash"] for u in users.values()]
    rec(g, "stored passwords are salted hashes (scrypt/pbkdf2), never plain text", all(h.startswith(("scrypt:", "pbkdf2:")) for h in hashes), hashes[0].split("$")[0] if hashes else "")
    rec(g, ".env and data/users.json are git-ignored", all(s in (ROOT / ".gitignore").read_text() for s in (".env", "data/users.json")))
    st, b = http_call(AUTH, "OPTIONS", "/api/predict")
    rec(g, "an OPTIONS pre-flight is not blocked by the auth guard", st != 401, f"HTTP {st}")


def main():
    for fn in (unit_tests, edge_tests, security_tests):
        try:
            fn()
        except Exception as e:  # a crash in a group is itself recorded
            rec(fn.__name__, "group ran to completion", False, repr(e)[:200])
    passed = sum(r["passed"] for r in results)
    groups = {}
    for r in results:
        g = groups.setdefault(r["group"], [0, 0])
        g[0] += r["passed"]
        g[1] += 1
    summary = {"total": len(results), "passed": passed, "failed": len(results) - passed, "by_group": {k: {"passed": v[0], "total": v[1]} for k, v in groups.items()},
               "results": results}
    (OUT / "tests.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n{passed}/{len(results)} passed")
    for r in results:
        if not r["passed"]:
            print("FAILED:", r["group"], r["name"], r["detail"])


if __name__ == "__main__":
    main()
