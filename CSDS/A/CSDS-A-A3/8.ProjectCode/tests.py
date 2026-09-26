"""End-to-end smoke tests.  Run:  python tests.py   (after `python run.py train`)"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phishguard import config  # noqa: E402

# isolate the threat-intel database so tests never touch real data
config.TI_DATABASE = Path(tempfile.gettempdir()) / "phishguard_test.db"
config.AUTO_RETRAIN_EVERY = 10 ** 9
if config.TI_DATABASE.exists():
    os.remove(config.TI_DATABASE)

from phishguard.features import FEATURE_NAMES, extract_features, normalize_url  # noqa: E402
from phishguard.threat_intel import ThreatIntel  # noqa: E402
from phishguard.webapp import create_app  # noqa: E402


def test_features():
    f = extract_features("http://paypal.com.verify-login.tk/signin?user=a&pwd=b")
    assert set(f) == set(FEATURE_NAMES)
    assert f["is_suspicious_tld"] == 1 and f["brand_outside_domain"] == 1
    assert f["num_query_params"] == 2 and f["num_subdomains"] == 2
    assert extract_features("http://10.0.0.1/x")["is_ip_host"] == 1
    assert normalize_url("WWW.Example.com/A") == "http://example.com/A"
    assert normalize_url("http://foo.com: /x")  # malformed port doesn't crash
    print("features ............ ok")


def test_threat_intel():
    ti = ThreatIntel()
    url = "http://zero-day-phish.example/login"
    assert ti.report(url, "phishing", "a")["status"] == "pending"
    assert ti.report(url, "phishing", "b")["status"] == "confirmed_phishing"
    assert ti.report(url, "safe", "c")["status"] == "pending"
    assert ti.lookup_host("http://zero-day-phish.example/other") is None
    ti.report(url, "phishing", "d")
    assert ti.lookup_host("http://zero-day-phish.example/other")["status"] == "confirmed_phishing"
    assert ti.training_examples() == [(normalize_url(url), 1)]
    assert ti.stats()["reports"] == 4
    print("threat intel ........ ok")


def test_webapp():
    app = create_app(ThreatIntel())
    c = app.test_client()
    for path in ("/", "/report", "/community", "/models"):
        assert c.get(path).status_code == 200
    j = c.get("/api/check?url=http://192.168.1.5/wp-admin/bank/update.php").get_json()
    assert j["verdict"] == "phishing" and j["decided_by"] == "ml"
    safe = "https://github.com/anthropics"
    assert c.get(f"/api/check?url={safe}").get_json()["verdict"] == "safe"
    for who in ("alice", "bob"):
        c.post("/api/report", json={"url": safe, "verdict": "phishing", "reporter": who})
    j = c.get(f"/api/check?url={safe}").get_json()
    assert j["verdict"] == "phishing" and j["decided_by"] == "community"
    assert c.get("/api/check?url=").status_code == 400
    print("web app + api ....... ok")


if __name__ == "__main__":
    test_features()
    test_threat_intel()
    test_webapp()
    print("all tests passed")
