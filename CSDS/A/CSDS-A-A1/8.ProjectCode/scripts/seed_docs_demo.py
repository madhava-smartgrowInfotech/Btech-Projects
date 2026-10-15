"""Put real activity into the running PolicyLens demo account so the screenshots are not empty.

Calls the running API (port 8101) exactly as the web app does - live Gemini answers, a Claim Copilot check
and a plan comparison - and writes the ids to docs/screenshots/_seed.json for capture_screenshots.py.

    python scripts/seed_docs_demo.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8101/api"
DEMO = {"email": "demo@policylens.app", "password": "Demo@12345"}


def call(path, token=None, method="GET", body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def main() -> int:
    token = call("/auth/login", method="POST", body=DEMO)["access_token"]
    policies = {p["document"]["file_name"]: p for p in call("/policies", token)}
    star = policies["star-health-family-health-optima.pdf"]
    hdfc = policies["hdfc-ergo-optima-secure.pdf"]
    out: dict = {"star": star["id"], "hdfc": hdfc["id"], "niva": policies["niva-bupa-reassure-2.pdf"]["id"],
                 "care": policies["care-health-care-supreme.pdf"]["id"]}

    # 1. English conversations on the Star Health policy - one per question so each screen is clean
    for key, q in [("conversation", "Is cataract surgery covered and after how long?"),
                   ("conversation_copay", "Is there a co-payment in this policy?"),
                   ("conversation_fire", "Does this policy insure my house against fire?")]:
        conv = call("/conversations", token, "POST", {"policy_id": star["id"]})
        out[key] = conv["id"]
        r = call(f"/conversations/{conv['id']}/messages", token, "POST", {"question": q, "language": "en"})
        a = r["answer"]
        print(f"{a['status']:<14} faith={a.get('faithfulness')} ms={a.get('total_ms')} :: {q}")

    # 2. Hindi conversation
    conv2 = call("/conversations", token, "POST", {"policy_id": hdfc["id"]})
    out["conversation_hi"] = conv2["id"]
    r = call(f"/conversations/{conv2['id']}/messages", token, "POST",
             {"question": "क्या इस पॉलिसी में कमरे के किराए की सीमा है?", "language": "hi"})
    print("hindi", r["answer"]["status"], r["answer"].get("faithfulness"))

    # 3. Claim Copilot - knee replacement, the documented demo scenario
    claim = call("/claims", token, "POST", {
        "policy_id": star["id"], "treatment": "Knee replacement", "hospitalization_type": "planned",
        "claim_mode": "cashless", "policy_start_date": "2023-10-01", "insured_age": 64, "pre_existing": "no",
        "estimated_cost": 350000, "room_type": "not_sure", "language": "en"})
    out["claim"] = claim["id"]
    print("claim", claim["verdict"], claim.get("faithfulness"), claim.get("total_ms"))

    claim2 = call("/claims", token, "POST", {
        "policy_id": star["id"], "treatment": "Knee replacement", "hospitalization_type": "planned",
        "claim_mode": "cashless", "policy_start_date": "2026-04-01", "insured_age": 45, "pre_existing": "no",
        "estimated_cost": 300000, "room_type": "not_sure", "language": "en"})
    out["claim_failing"] = claim2["id"]
    print("claim (new policy)", claim2["verdict"])

    # 4. Plan comparison
    cmp_ = call("/comparisons", token, "POST", {"policy_a_id": star["id"], "policy_b_id": hdfc["id"], "language": "en"})
    out["comparison"] = cmp_["id"]
    print("comparison", cmp_["id"], len(cmp_["result"]["rows"]), "rows")

    dest = ROOT / "docs" / "screenshots"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "_seed.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("saved", dest / "_seed.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
