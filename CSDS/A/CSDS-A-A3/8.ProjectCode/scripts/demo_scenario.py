"""Put realistic usage into a running PhishGuard so its screens show real data (used for the report screenshots).

    python scripts/demo_scenario.py [http://127.0.0.1:8103]

Everything goes through the public API: URL checks fill the activity log, then community reports are filed
the way real users would file them. Three groups of URLs are used:
  * zero-day  - lookalike URLs the model scores as safe; two reports make the community verdict override it
  * corrected - legitimate URLs the model flags; two "safe" reports clear them
  * pending   - a single report, or reports that disagree, so no verdict is confirmed
The before / after verdicts are saved to docs/experiments/demo_scenario.json.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8103").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "experiments" / "demo_scenario.json"


def get(path: str, **params):
    q = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{BASE}{path}?{q}", timeout=60) as r:
        return json.load(r)


def post(path: str, body: dict):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def check(url: str) -> dict:
    r = get("/api/check", url=url)
    return {"url": url, "verdict": r["verdict"], "probability": r["probability"], "decided_by": r["decided_by"]}


ZERO_DAY = [
    ("https://docs-share.cloudhost-files.com/drive/view?id=44", ["volunteer-12", "soc-analyst"], "fake document-share page"),
    ("http://sbi-netbanking-kyc-update.top/login.php", ["helpdesk-01", "mail-gateway"], "bank KYC lure"),
    ("http://amazon-gift-claim.winner-prize.xyz/claim", ["soc-analyst", "volunteer-07"], "prize scam"),
    ("http://microsoft-office365.sharepoint-docs.work/invoice.html", ["mail-gateway", "volunteer-03"], "invoice lure with Office 365 login"),
    ("http://hdfc-rewards-points-redeem.info/redeem?id=88213", ["helpdesk-01", "volunteer-07", "soc-analyst"], "reward-points lure"),
]
CORRECTED = [
    ("https://docs.python.org/3/library/urllib.html", ["volunteer-03", "volunteer-12"], "official documentation"),
    ("https://www.amazon.in/gp/cart/view.html", ["helpdesk-01", "volunteer-07"], "real shopping-cart page"),
]
PENDING = [
    ("http://track-parcel-update.web.app/", [("phishing", "volunteer-03")], "parcel-tracking lure, one report so far"),
    ("https://myaccount-recover.pages.dev/index.html", [("phishing", "soc-analyst"), ("safe", "volunteer-12")], "reports disagree"),
    ("https://wetransfer.com/downloads/8a1b2c3d4e", [("phishing", "volunteer-07")], "unverified, one report"),
]
EXTRA_CHECKS = [
    "https://github.com/anthropics", "https://www.wikipedia.org/wiki/Phishing", "https://stackoverflow.com/questions/11227809",
    "http://192.168.1.5/wp-admin/bank/update.php", "http://paypal.com.verify-login.tk/signin?user=a&pwd=b",
    "http://apple-id-locked.support-center.xyz/unlock/account.html", "http://free-prize-winner-lucky.top/claim.exe",
    "https://www.irctc.co.in/nget/train-search", "http://bit.ly/3xYz9Ab", "http://netflix-billing-update.com/payment/verify",
]


def main():
    log: dict = {"base": BASE, "before": [], "after": [], "reports": []}
    for url, _, _ in ZERO_DAY + CORRECTED + [(u, 0, 0) for u, _, _ in PENDING]:
        log["before"].append(check(url))
    for url in EXTRA_CHECKS:
        log["before"].append(check(url))
    for url, who, note in ZERO_DAY:
        for w in who:
            e = post("/api/report", {"url": url, "verdict": "phishing", "reporter": w, "note": note})
            log["reports"].append({"url": url, "verdict": "phishing", "reporter": w, "status": e["status"]})
    for url, who, note in CORRECTED:
        for w in who:
            e = post("/api/report", {"url": url, "verdict": "safe", "reporter": w, "note": note})
            log["reports"].append({"url": url, "verdict": "safe", "reporter": w, "status": e["status"]})
    for url, votes, note in PENDING:
        for verdict, w in votes:
            e = post("/api/report", {"url": url, "verdict": verdict, "reporter": w, "note": note})
            log["reports"].append({"url": url, "verdict": verdict, "reporter": w, "status": e["status"]})
    for url, _, _ in ZERO_DAY + CORRECTED + [(u, 0, 0) for u, _, _ in PENDING]:
        log["after"].append(check(url))
    log["stats"] = get("/api/stats")["threat_intel"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(log, indent=2), encoding="utf-8")
    for b, a in zip(log["before"][:10], log["after"]):
        print(f"{b['verdict']:<10}{(b['probability'] or 0):<8}-> {a['verdict']:<10}{a['decided_by']:<10}{a['url']}")
    print(log["stats"])


if __name__ == "__main__":
    main()
