"""PeerScope smoke test: drives the running API (and web app) end to end through real HTTP calls.

Start run.bat first (API on 8408, web app on 5408), then:
    python scripts/smoke_test.py
Environment: PEERSCOPE_API, PEERSCOPE_WEB override the base URLs.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import requests

API = os.environ.get("PEERSCOPE_API", "http://127.0.0.1:8408").rstrip("/")
WEB = os.environ.get("PEERSCOPE_WEB", "http://127.0.0.1:5408").rstrip("/")
DEMO = Path(__file__).resolve().parent.parent / "data" / "demo" / "demo_paper.pdf"

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{' - ' + detail if detail and not ok else ''}")
    if not ok:
        failures.append(name)


def main() -> int:
    s = requests.Session()
    try:
        h = s.get(f"{API}/api/health", timeout=10)
    except requests.RequestException as exc:
        print(f"API not reachable at {API}: {exc}\nStart it with run.bat first.")
        return 2
    check("health 200 + product", h.status_code == 200 and h.json().get("product") == "PeerScope")

    m = s.get(f"{API}/api/model/metrics", timeout=10).json()
    check("model metrics present", "accuracy" in m or m.get("status") == "missing")
    if "accuracy" in m:
        check("metrics have confusion matrix", len(m.get("confusion_matrix", [])) == len(m.get("labels", [])) > 0)

    # reviewer CRUD
    before = s.get(f"{API}/api/reviewers", timeout=10).json()
    check("reviewers list", isinstance(before, list) and len(before) > 0)
    bad = s.post(f"{API}/api/reviewers", json={"display_name": ""}, timeout=10)
    check("empty reviewer name rejected (422)", bad.status_code == 422)
    new = s.post(f"{API}/api/reviewers", json={"display_name": "Smoke Test Reviewer", "affiliation": "QA Lab",
                                               "research_topics": "testing", "maximum_load": 3}, timeout=10)
    check("reviewer create 201", new.status_code == 201)
    rid = new.json().get("id")
    upd = s.put(f"{API}/api/reviewers/{rid}", json={"display_name": "Smoke Test Reviewer", "is_active": False}, timeout=10)
    check("reviewer deactivate", upd.status_code == 200 and upd.json()["is_active"] is False)
    csv = s.get(f"{API}/api/reviewers/export/csv", timeout=10)
    check("reviewer CSV export", csv.status_code == 200 and "display_name" in csv.text and "Smoke Test Reviewer" in csv.text)
    imp = s.post(f"{API}/api/reviewers/import", files={"file": ("r.csv", io.BytesIO(b"display_name,affiliation\nSmoke Imported,QA\n"), "text/csv")}, timeout=10)
    check("reviewer CSV import", imp.status_code == 200 and imp.json().get("imported") == 1)
    for r in s.get(f"{API}/api/reviewers", timeout=10).json():
        if r["display_name"].startswith("Smoke "):
            s.delete(f"{API}/api/reviewers/{r['id']}", timeout=10)
    after = s.get(f"{API}/api/reviewers", timeout=10).json()
    check("smoke reviewers cleaned up", len(after) == len(before))
    check("delete missing reviewer 404", s.delete(f"{API}/api/reviewers/999999", timeout=10).status_code == 404)

    # analyze
    nopdf = s.post(f"{API}/api/analyze", files={"file": ("a.txt", b"hello", "text/plain")}, timeout=30)
    check("non-PDF rejected (400)", nopdf.status_code == 400 and "PDF" in nopdf.json().get("detail", ""))
    fake = s.post(f"{API}/api/analyze", files={"file": ("a.pdf", b"not really a pdf", "application/pdf")}, timeout=30)
    check("fake PDF rejected (400)", fake.status_code == 400)
    if not DEMO.exists():
        check("demo PDF exists (python scripts/make_demo_pdf.py)", False)
    else:
        with DEMO.open("rb") as fh:
            r = s.post(f"{API}/api/analyze", files={"file": (DEMO.name, fh, "application/pdf")},
                       data={"active_only": "true", "min_score": "0", "topic": "", "method": ""}, timeout=600)
        check("analyze 200", r.status_code == 200, r.text[:200])
        if r.status_code == 200:
            a = r.json()
            aid = a.get("analysis_id")
            check("result has review + reviewers + literature", all(k in a for k in ("review", "reviewers", "literature", "features")))
            check("reviewers ranked with breakdown", bool(a["reviewers"]) and "breakdown" in a["reviewers"][0])
            check("disclaimer present", "human" in a.get("disclaimer", ""))
            lst = s.get(f"{API}/api/analyses", timeout=10).json()
            check("analysis appears in history", any(x["id"] == aid for x in lst))
            check("analysis fetch by id", s.get(f"{API}/api/analyses/{aid}", timeout=10).status_code == 200)
            j = s.get(f"{API}/api/analyses/{aid}/export?format=json", timeout=30)
            check("export JSON", j.status_code == 200 and "attachment" in j.headers.get("content-disposition", ""))
            p = s.get(f"{API}/api/analyses/{aid}/export?format=pdf", timeout=60)
            check("export PDF", p.status_code == 200 and p.content[:4] == b"%PDF")
    check("missing analysis 404", s.get(f"{API}/api/analyses/999999", timeout=10).status_code == 404)

    # web app
    try:
        w = s.get(WEB, timeout=10)
        check("web app serves index.html", w.status_code == 200 and '<div id="root">' in w.text)
        cors = s.options(f"{API}/api/health", headers={"Origin": WEB, "Access-Control-Request-Method": "GET"}, timeout=10)
        check("CORS allows the web origin", cors.headers.get("access-control-allow-origin") in ("*", WEB))
    except requests.RequestException:
        print(f"[SKIP] web app not reachable at {WEB}")

    print(f"\n{'ALL CHECKS PASSED' if not failures else 'FAILED: ' + ', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
