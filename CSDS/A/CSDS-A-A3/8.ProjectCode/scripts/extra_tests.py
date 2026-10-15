"""Wider test run than tests.py: functional, validation, edge-case and security checks.

    python scripts/extra_tests.py

Uses a throwaway threat-intel database and never retrains, so shipped data and models are untouched.
Writes docs/experiments/test_results.json (counts per category) for the report.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from phishguard import config  # noqa: E402

config.TI_DATABASE = Path(tempfile.gettempdir()) / "phishguard_extra.db"
config.AUTO_RETRAIN_EVERY = 10 ** 9
if config.TI_DATABASE.exists():
    os.remove(config.TI_DATABASE)

from backend.server import build_app  # noqa: E402
from phishguard.detector import Detector  # noqa: E402
from phishguard.features import (FEATURE_NAMES, explain_features, extract_features,  # noqa: E402
                                 normalize_url, shannon_entropy, split_host)
from phishguard.threat_intel import ThreatIntel  # noqa: E402

RESULTS: list[tuple[str, str, bool, str]] = []


def check(category: str, name: str, cond: bool, detail: str = ""):
    RESULTS.append((category, name, bool(cond), detail))
    print(f"{'ok  ' if cond else 'FAIL'}  [{category}] {name}{('  ' + detail) if detail else ''}")


def raises(fn, exc=Exception) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:  # noqa: BLE001
        return False
    return False


def main():
    ti = ThreatIntel()
    det = Detector(ti)
    app = build_app(ti, det)
    c = app.test_client()

    # ---------------------------------------------------------------- unit: features
    U = "unit"
    f = extract_features("http://paypal.com.verify-login.tk/signin?user=a&pwd=b")
    check(U, "47 features returned in a fixed order", list(f) == FEATURE_NAMES and len(f) == 47)
    check(U, "suspicious TLD detected", f["is_suspicious_tld"] == 1)
    check(U, "brand outside the registered domain detected", f["brand_outside_domain"] == 1)
    check(U, "query parameters counted", f["num_query_params"] == 2)
    check(U, "IP host detected", extract_features("http://10.0.0.1/x")["is_ip_host"] == 1)
    check(U, "hex / decimal IP host detected", extract_features("http://0x7f000001/a")["is_ip_host"] == 1)
    check(U, "'@' symbol detected", extract_features("http://good.com@evil.tk/a")["has_at_symbol"] == 1)
    check(U, "URL shortener detected", extract_features("http://bit.ly/abc123")["is_url_shortener"] == 1)
    check(U, "executable extension detected", extract_features("http://x.tk/a/setup.exe")["has_executable_extension"] == 1)
    check(U, "popular domain flagged", extract_features("https://www.wikipedia.org/wiki/X")["is_popular_domain"] == 1)
    check(U, "two-level suffix split (co.uk)", split_host("shop.example.co.uk") == ("shop", "example", "co.uk"))
    check(U, "plain host split", split_host("a.b.example.com") == ("a.b", "example", "com"))
    check(U, "entropy of a constant string is 0", shannon_entropy("aaaa") == 0.0)
    check(U, "entropy of 'ab' is 1 bit", abs(shannon_entropy("ab") - 1.0) < 1e-9)
    check(U, "normalise adds scheme and strips www", normalize_url("WWW.Example.com/A") == "http://example.com/A")
    check(U, "normalise keeps https", normalize_url("https://Example.com/x").startswith("https://example.com"))
    check(U, "red flags listed for a bad URL", len(explain_features(f)) >= 3)
    check(U, "no red flags for a plain reputable URL",
          explain_features(extract_features("https://www.wikipedia.org/wiki/Phishing")) == [])

    # ---------------------------------------------------------------- unit: consensus
    url = "http://zero-day.example.net/login"
    check(U, "first report stays pending", ti.report(url, "phishing", "a")["status"] == "pending")
    check(U, "second report confirms phishing", ti.report(url, "phishing", "b")["status"] == "confirmed_phishing")
    check(U, "opposing vote drops back to pending", ti.report(url, "safe", "c")["status"] == "pending")
    check(U, "trusted feed confirms immediately",
          ti.report("http://feed-only.example/x", "phishing", "feed:test", source="test", trusted=True)["status"]
          == "confirmed_phishing")
    for who in ("d", "e"):
        ti.report("http://false-alarm.example/", "safe", who)
    check(U, "two safe votes confirm legitimate", ti.lookup("http://false-alarm.example/")["status"] == "confirmed_safe")

    # ---------------------------------------------------------------- integration: detector
    I = "integration"
    r = det.check("http://secure-paypal-login.account-verify.tk/signin?user=a", log=False)
    check(I, "obvious phishing URL decided by the model", r["verdict"] == "phishing" and r["decided_by"] == "ml",
          f"p={r['probability']}")
    r = det.check("https://github.com/anthropics", log=False)
    check(I, "reputable URL is safe", r["verdict"] == "safe", f"p={r['probability']}")
    victim = "https://www.wikipedia.org/wiki/Phishing"
    before = det.check(victim, log=False)["verdict"]
    ti.report(victim, "phishing", "u1")
    ti.report(victim, "phishing", "u2")
    after = det.check(victim, log=False)
    check(I, "confirmed community verdict overrides the model",
          before == "safe" and after["verdict"] == "phishing" and after["decided_by"] == "community")
    ti.report("http://192.168.0.9/wp-admin/bank/update.php", "safe", "s1")
    ti.report("http://192.168.0.9/wp-admin/bank/update.php", "safe", "s2")
    r = det.check("http://192.168.0.9/wp-admin/bank/update.php", log=False)
    check(I, "confirmed-safe report corrects a model false alarm", r["verdict"] == "safe" and r["decided_by"] == "community")
    host_url = "http://phish-host.example/a"
    ti.report(host_url, "phishing", "h1")
    ti.report(host_url, "phishing", "h2")
    r = det.check("http://phish-host.example/completely/other/page", log=False)
    check(I, "confirmed host covers its other pages", r["verdict"] == "phishing" and r["decided_by"] == "community")
    pending = "http://pending-vote.test-site.top/a"
    base = det.check(pending, log=False)["probability"]
    ti.report(pending, "phishing", "p1")
    nudged = det.check(pending, log=False)["probability"]
    check(I, "one pending phishing report raises the score", nudged >= base, f"{base} -> {nudged}")
    check(I, "training examples reflect confirmed URLs",
          len(ti.training_examples()) >= 4 and all(lbl in (0, 1) for _, lbl in ti.training_examples()))
    check(I, "mark_trained clears the awaiting-training count",
          ti.pending_training_count() > 0 and ti.mark_trained() > 0 and ti.pending_training_count() == 0)

    # ---------------------------------------------------------------- functional: API
    F = "functional"
    h = c.get("/api/health").get_json()
    check(F, "GET /api/health reports a ready model", h["ok"] and h["model_ready"])
    j = c.get("/api/check", query_string={"url": "http://login-verify-account.xyz/secure"}).get_json()
    check(F, "GET /api/check returns the documented fields",
          all(k in j for k in ("verdict", "probability", "decided_by", "reason", "red_flags", "features", "model")))
    check(F, "feature dictionary has 47 entries", len(j["features"]) == 47)
    e = c.post("/api/report", json={"url": "http://api-report.example/x", "verdict": "phishing", "reporter": "t1"}).get_json()
    check(F, "POST /api/report returns the vote counts", e["phishing_votes"] == 1 and e["status"] == "pending")
    check(F, "GET /api/stats has threat-intel counters and metrics",
          {"threat_intel", "metrics", "retraining"} <= set(c.get("/api/stats").get_json()))
    check(F, "GET /api/config exposes the thresholds",
          c.get("/api/config").get_json()["phishing_threshold"] == config.PHISHING_THRESHOLD)
    check(F, "GET /api/checks lists the log", isinstance(c.get("/api/checks?limit=5").get_json(), list))
    check(F, "GET /api/intel filters by status",
          all(x["status"] == "confirmed_phishing" for x in c.get("/api/intel?status=confirmed_phishing").get_json()))
    check(F, "GET /api/intel/lookup returns the report history",
          len(c.get("/api/intel/lookup", query_string={"url": victim}).get_json()["entry"]["reports"]) == 2)
    for p in ("/", "/report", "/community", "/models"):
        check(F, f"original page {p} renders", c.get(p).status_code == 200)
    r = c.post("/", data={"url": "http://form-check.example/login"})
    check(F, "form POST on / shows a verdict", r.status_code == 200 and b"verdict" in r.data)

    # ---------------------------------------------------------------- validation and edge cases
    V = "validation"
    check(V, "empty URL rejected with 400", c.get("/api/check?url=").status_code == 400)
    check(V, "missing url parameter rejected", c.get("/api/check").status_code == 400)
    check(V, "whitespace-only URL rejected", c.get("/api/check", query_string={"url": "   "}).status_code == 400)
    check(V, "report with unknown verdict rejected",
          c.post("/api/report", json={"url": "http://a.b", "verdict": "maybe"}).status_code == 400)
    check(V, "report with empty URL rejected",
          c.post("/api/report", json={"url": "", "verdict": "phishing"}).status_code == 400)
    check(V, "unknown intel status rejected", c.get("/api/intel?status=bogus").status_code == 400)
    check(V, "non-numeric limit falls back to the default", c.get("/api/checks?limit=abc").status_code == 200)
    check(V, "lookup without url rejected", c.get("/api/intel/lookup").status_code == 400)
    for label, u in (("bare domain", "example.com"), ("no scheme with path", "example.com/a/b?c=d"),
                     ("malformed port", "http://foo.com:abc/x"), ("unmatched bracket", "http://[::1/x"),
                     ("very long URL", "http://a.com/" + "x" * 5000),
                     ("unicode host", "http://bücher.example/straße"),
                     ("percent-encoded path", "http://a.com/%2e%2e/%2e%2e/etc/passwd"),
                     ("javascript scheme", "javascript:alert(1)"), ("data scheme", "data:text/html,<b>x</b>")):
        resp = c.get("/api/check", query_string={"url": u})
        check(V, f"edge case handled: {label}", resp.status_code in (200, 400), f"HTTP {resp.status_code}")

    # ---------------------------------------------------------------- security
    S = "security"
    sqli = "http://x.com/'; DROP TABLE reports; --"
    resp = c.post("/api/report", json={"url": sqli, "verdict": "phishing", "reporter": "x'); DROP TABLE intel;--"})
    check(S, "SQL-injection string is stored as data", resp.status_code == 200 and ti.stats()["reports"] > 0)
    check(S, "tables survive the injection attempt", ti.stats()["urls_tracked"] > 0)
    xss = "http://x.com/<script>alert(1)</script>"
    c.post("/api/report", json={"url": xss, "verdict": "phishing", "reporter": "<b>x</b>", "note": "<img src=x onerror=alert(1)>"})
    page = c.get("/community").data
    check(S, "script tag in a reported URL is HTML-escaped on /community", b"<script>alert(1)</script>" not in page)
    page = c.post("/", data={"url": xss}).data
    check(S, "script tag in a checked URL is HTML-escaped on /", b"<script>alert(1)</script>" not in page)
    check(S, "reporter name with markup is escaped", b"<b>x</b>" not in c.get("/community").data)
    check(S, "CORS header present on API responses", c.get("/api/health").headers.get("Access-Control-Allow-Origin") == "*")
    check(S, "API accepts no cookies / credentials (no session state)", "Set-Cookie" not in c.get("/api/health").headers)
    big = c.post("/api/report", json={"url": "http://big-note.example/", "verdict": "phishing", "note": "n" * 100000})
    check(S, "very large note does not crash the server", big.status_code in (200, 400, 413))

    # ---------------------------------------------------------------- performance
    P = "performance"
    t = time.perf_counter()
    for _ in range(100):
        c.get("/api/check", query_string={"url": "http://login-verify-account.xyz/secure"})
    per = (time.perf_counter() - t) / 100 * 1000
    check(P, "mean /api/check latency under 50 ms", per < 50, f"{per:.1f} ms")
    t = time.perf_counter()
    for _ in range(2000):
        extract_features("http://login-verify-account.xyz/secure?id=1")
    per = (time.perf_counter() - t) / 2000 * 1000
    check(P, "feature extraction under 1 ms per URL", per < 1, f"{per:.3f} ms")

    # ---------------------------------------------------------------- summary
    cats: dict[str, dict] = {}
    for cat, _, ok, _ in RESULTS:
        d = cats.setdefault(cat, {"total": 0, "passed": 0})
        d["total"] += 1
        d["passed"] += int(ok)
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r[2])
    out = {"total": total, "passed": passed, "failed": total - passed, "by_category": cats,
           "failures": [f"[{a}] {b} {d}" for a, b, ok, d in RESULTS if not ok],
           "cases": [{"category": a, "name": b, "passed": ok, "detail": d} for a, b, ok, d in RESULTS]}
    dest = ROOT / "docs" / "experiments"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "test_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n{passed}/{total} checks passed", json.dumps(cats))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
