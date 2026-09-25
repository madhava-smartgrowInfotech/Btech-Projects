"""Drives the running ClauseGuard API through the full end-to-end flow:
register -> login -> upload a sample contract -> report -> clause detail ->
graph -> eval metrics. Exits non-zero on any failure.

Usage (backend must already be running on BACKEND_PORT, default 8106):
    backend\\venv\\Scripts\\python.exe scripts\\smoke_test.py
"""
import io
import sys
import time
import uuid
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "backend"))
from app.config import BACKEND_PORT, gemini_configured  # noqa: E402

BASE_URL = f"http://127.0.0.1:{BACKEND_PORT}"

SAMPLE_CONTRACT_TEXT = """FREELANCE SERVICES AGREEMENT

1. Scope of Services
The Consultant shall provide software development services to the Company as described in Schedule A.

2. Term and Termination
The Company may terminate this Agreement at any time, without cause or notice, at its sole discretion, and the Consultant shall have no right to object or claim compensation for unfinished work.

3. Fees and Refunds
The Company shall pay the Consultant a monthly fee of Rs. 60,000. All payments made under this Agreement are non-refundable under any circumstances, including early termination by the Company.

4. Penalty for Delay
If the Consultant delays delivery of any milestone, the Consultant shall pay a penalty of Rs. 25,000 per day of delay, irrespective of the actual loss suffered by the Company.

5. Non-Compete
During the term of this Agreement and for a period of two years thereafter, the Consultant shall not, directly or indirectly, engage in any competing business or provide services to any competitor of the Company within India.

6. Liability
The Consultant shall be fully liable for any and all losses, damages, claims and expenses arising in connection with this Agreement, with no limitation on liability whatsoever.

7. Intellectual Property
All intellectual property created by the Consultant, whether related to this engagement or otherwise, including prior and pre-existing works, shall be assigned to the Company irrevocably and worldwide.

8. Governing Law
This Agreement shall be governed by and construed in accordance with the laws of India, and the courts at Bengaluru shall have exclusive jurisdiction.

9. Confidentiality
Each party shall maintain the confidentiality of the other party's proprietary information disclosed under this Agreement.
"""


def fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    print(f"Smoke test against {BASE_URL}")

    if not gemini_configured():
        print("SKIP: GEMINI_API_KEY is not set in .env. The smoke test needs a real key to drive")
        print("the upload/classification/explanation pipeline end-to-end.")
        print("Add your key to .env (see .env.example), restart the backend, and re-run this script.")
        sys.exit(0)

    health = requests.get(f"{BASE_URL}/api/health", timeout=10)
    if health.status_code != 200:
        fail(f"health check returned {health.status_code}")
    print("OK  health check")

    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    password = "smoke-test-pw-123"
    reg = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": password}, timeout=10)
    if reg.status_code != 200:
        fail(f"register failed: {reg.status_code} {reg.text}")
    token = reg.json()["token"]
    print("OK  register")

    login = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=10)
    if login.status_code != 200:
        fail(f"login failed: {login.status_code} {login.text}")
    print("OK  login")

    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("sample_freelance_contract.docx", _build_docx_bytes(SAMPLE_CONTRACT_TEXT),
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    start = time.time()
    upload = requests.post(f"{BASE_URL}/api/contracts/upload", headers=headers, files=files, timeout=180)
    if upload.status_code != 200:
        fail(f"upload failed: {upload.status_code} {upload.text}")
    report = upload.json()
    print(f"OK  upload + full pipeline ({time.time() - start:.1f}s) -> grade {report['complexity_grade']}, "
          f"{len(report['clauses'])} clauses")

    if not report["clauses"]:
        fail("no clauses were extracted")

    flagged = [c for c in report["clauses"] if c["flag_count"] > 0]
    if not flagged:
        fail("expected at least one flagged clause in the sample contract")
    print(f"OK  {len(flagged)} clauses flagged")

    contract_id = report["id"]
    clause_id = flagged[0]["id"]
    detail = requests.get(f"{BASE_URL}/api/contracts/{contract_id}/clauses/{clause_id}", headers=headers, timeout=30)
    if detail.status_code != 200:
        fail(f"clause detail failed: {detail.status_code} {detail.text}")
    clause_detail = detail.json()
    if not clause_detail["flags"]:
        fail("clause detail returned no flags")
    if not clause_detail["flags"][0]["reason"] or not clause_detail["flags"][0]["safer_wording"]:
        fail("flag missing reason/safer_wording")
    print("OK  clause detail (explanation + safer wording present)")

    graph = requests.get(f"{BASE_URL}/api/contracts/{contract_id}/graph", headers=headers, timeout=30)
    if graph.status_code != 200:
        fail(f"graph failed: {graph.status_code} {graph.text}")
    graph_data = graph.json()
    if not graph_data.get("risky_combinations"):
        fail("expected at least one risky combination for the sample contract")
    print(f"OK  graph shows {len(graph_data['risky_combinations'])} risky combination(s)")

    listing = requests.get(f"{BASE_URL}/api/contracts", headers=headers, timeout=15)
    if listing.status_code != 200 or not listing.json():
        fail("contract listing failed or empty")
    print("OK  contract listing")

    metrics = requests.get(f"{BASE_URL}/api/eval/metrics", timeout=15)
    if metrics.status_code != 200:
        fail(f"eval metrics failed: {metrics.status_code}")
    print("OK  eval metrics endpoint")

    print("\nSMOKE TEST PASSED")


def _build_docx_bytes(text: str) -> bytes:
    from docx import Document
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    main()
