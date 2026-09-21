"""End-to-end API flow on a generated policy: upload -> parse -> index -> search -> chat -> claim -> delete.

Gemini is not called: the AI steps are replaced with deterministic stand-ins that respect the
same schemas, so the rest of the pipeline (retrieval, citation checks, faithfulness scoring,
persistence) runs for real.
"""

import time

import pytest

from app.services import answerer, claim_copilot


def _wait_ready(client, headers, policy_id, timeout=240):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"/api/policies/{policy_id}/status", headers=headers).json()
        if status["status"] in ("ready", "failed"):
            return status
        time.sleep(0.5)
    raise AssertionError("policy did not finish processing")


@pytest.fixture()
def uploaded(client, auth_headers, policy_pdf):
    with policy_pdf.open("rb") as fh:
        res = client.post("/api/policies", headers=auth_headers,
                          files={"file": ("sample-policy-wording.pdf", fh, "application/pdf")},
                          data={"display_name": "Test Policy"})
    assert res.status_code == 201, res.text
    policy = res.json()
    status = _wait_ready(client, auth_headers, policy["id"])
    assert status["status"] == "ready", status
    return policy


def test_upload_rejects_non_pdf(client, auth_headers):
    res = client.post("/api/policies", headers=auth_headers, files={"file": ("notes.txt", b"hello", "text/plain")})
    assert res.status_code == 400
    assert res.json()["code"] == "not_pdf"


def test_policy_pipeline_and_search(client, auth_headers, uploaded):
    pid = uploaded["id"]
    status = client.get(f"/api/policies/{pid}/status", headers=auth_headers).json()
    assert "Gemini" in (status["extraction_error"] or "")  # no key in tests -> card not built, policy still usable

    clauses = client.get(f"/api/policies/{pid}/clauses", headers=auth_headers).json()
    assert any(c["clause_ref"] == "Excl02" for c in clauses)

    res = client.post(f"/api/policies/{pid}/search", headers=auth_headers,
                      json={"query": "after how long is cataract covered", "mode": "hybrid_rerank", "k": 3})
    assert res.status_code == 200
    top = res.json()["items"][0]["clause"]
    assert "cataract" in top["text"].lower()

    for mode in ("bm25", "dense", "hybrid"):
        assert client.post(f"/api/policies/{pid}/search", headers=auth_headers,
                           json={"query": "cosmetic surgery", "mode": mode}).status_code == 200

    page = client.get(f"/api/policies/{pid}/pages/2?scale=1", headers=auth_headers)
    assert page.status_code == 200 and page.headers["content-type"] == "image/png"
    assert client.get(f"/api/policies/{pid}/file", headers=auth_headers).status_code == 200
    card = client.get(f"/api/policies/{pid}/card", headers=auth_headers)
    assert card.status_code == 404


def test_other_users_cannot_see_policy(client, auth_headers, uploaded):
    other = client.post("/api/auth/register", json={"full_name": "Other", "email": "other-user@example.com",
                                                    "password": "Secret123"})
    headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert client.get(f"/api/policies/{uploaded['id']}", headers=headers).status_code == 404


def test_chat_answer_citations_and_faithfulness(client, auth_headers, uploaded, monkeypatch):
    def fake_generate(*, prompt, schema, **kwargs):
        # Cite the retrieved clause block that mentions cataract, as a grounded model would.
        blocks = [b for b in prompt.split("\n\n") if b.startswith("[C")]
        block = next((b for b in blocks if "cataract" in b.lower()), blocks[0])
        tag = block.split("]", 1)[0].strip("[")
        out = schema(
            status="answered",
            answer=f"Cataract is covered after 24 months of continuous coverage [{tag}] [C999].",
            answer_en=f"Cataract is covered after 24 months of continuous coverage [{tag}] [C999].",
            claims=[{"text_en": "Treatment of cataract is excluded until the expiry of 24 months of continuous coverage.",
                     "clauses": [tag, "C999"]}],
            follow_up_questions=["Is joint replacement also on the list?"],
        )
        from app.services.gemini_client import CallMeta

        return out, CallMeta(model="test-model", latency_ms=5)

    monkeypatch.setattr(answerer, "generate_json", fake_generate)
    conv = client.post("/api/conversations", headers=auth_headers, json={"policy_id": uploaded["id"]}).json()
    res = client.post(f"/api/conversations/{conv['id']}/messages", headers=auth_headers,
                      json={"question": "Is cataract surgery covered and after how long?", "language": "en"})
    assert res.status_code == 200, res.text
    answer = res.json()["answer"]
    assert "[C999]" not in answer["content"]  # citation to a clause that was not retrieved is removed
    assert answer["citations"] and answer["citations"][0]["page"] == 2
    assert answer["faithfulness"] is not None and answer["faithfulness"] >= 50
    detail = client.get(f"/api/conversations/{conv['id']}", headers=auth_headers).json()
    assert len(detail["messages"]) == 2


def test_out_of_scope_question_abstains(client, auth_headers, uploaded, monkeypatch):
    def fake_generate(*, prompt, schema, **kwargs):
        from app.services.gemini_client import CallMeta

        return schema(status="not_in_policy", answer="This isn't covered in this policy.",
                      answer_en="This isn't covered in this policy.", claims=[], follow_up_questions=[]), \
            CallMeta(model="test-model", latency_ms=5)

    monkeypatch.setattr(answerer, "generate_json", fake_generate)
    conv = client.post("/api/conversations", headers=auth_headers, json={"policy_id": uploaded["id"]}).json()
    res = client.post(f"/api/conversations/{conv['id']}/messages", headers=auth_headers,
                      json={"question": "Does this policy insure my car against theft?"})
    assert res.json()["answer"]["status"] == "not_in_policy"


def test_claim_copilot_flow(client, auth_headers, uploaded, monkeypatch):
    def fake_generate(*, prompt, schema, **kwargs):
        from app.services.gemini_client import CallMeta

        tag = "C" + prompt.split("[C", 1)[1].split("]", 1)[0]
        plan = schema(
            verdict="covered", verdict_summary="Covered after the waiting period.",
            verdict_summary_en="Covered after the waiting period.",
            reasons=[{"text": f"Cataract has a 24 month wait [{tag}]", "text_en": "Cataract has a 24 month wait",
                      "policy_fact_en": "Treatment of cataract is excluded until the expiry of 24 months of "
                                        "continuous coverage.", "clauses": [tag]}],
            prechecks=[], documents=[{"item": "Discharge summary", "why": "Required for every claim", "clauses": []}],
            steps=[{"title": "Inform the insurer", "detail": "Within 24 hours of emergency admission",
                    "timeline": "24 hours", "clauses": [tag]}],
            cost_notes=["Room rent is capped"],
        )
        return plan, CallMeta(model="test-model", latency_ms=5)

    monkeypatch.setattr(claim_copilot, "generate_json", fake_generate)
    res = client.post("/api/claims", headers=auth_headers, json={
        "policy_id": uploaded["id"], "treatment": "Cataract surgery", "claim_mode": "cashless",
        "policy_start_date": "2025-12-01", "estimated_cost": 50000})
    assert res.status_code == 201, res.text
    case = res.json()
    assert case["verdict"] in {"covered", "not_covered"}
    item = case["result"]["documents"][0]["id"]
    upd = client.patch(f"/api/claims/{case['id']}/checklist", headers=auth_headers, json={"item_id": item, "done": True})
    assert upd.json()["checklist_state"][item] is True
    assert client.get("/api/dashboard/summary", headers=auth_headers).json()["kpis"]["claim_checks"] >= 1


def test_delete_policy(client, auth_headers, uploaded):
    pid = uploaded["id"]
    assert client.delete(f"/api/policies/{pid}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/policies/{pid}", headers=auth_headers).status_code == 404
