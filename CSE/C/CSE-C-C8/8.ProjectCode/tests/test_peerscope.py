"""PeerScope tests: real logic, no placeholders."""
from __future__ import annotations


def test_pdf_extraction(tmp_path):
    from scripts.make_demo_pdf import main as make_demo  # noqa

    make_demo()
    from pathlib import Path

    from app.services import pdf_extract

    pdf = Path("data/demo/demo_paper.pdf")
    assert pdf.exists()
    doc = pdf_extract.extract_pdf(pdf)
    assert doc["page_count"] >= 1 and doc["word_count"] > 200
    assert "methodology" in doc["sections"] or "experiments" in doc["sections"]


def test_features():
    from app.services import features

    doc = {"title": "Test paper on learning", "paper_summary": "summary text here " * 20,
           "full_text": ("Introduction\nSome text about learning and evaluation. " * 40
                         + "\nMethodology\nWe train a neural model. " * 10
                         + "\nReferences\n[1] A. B. Something. " * 8),
           "sections": {"introduction": {"word_count": 200, "preview": "x"},
                        "methodology": {"word_count": 150, "preview": "x"},
                        "references": {"word_count": 60, "preview": "x"}},
           "page_count": 4, "reference_count": 8}
    f = features.extract_features(doc)
    assert f["has_methodology"] is True
    assert 0 <= f["overall_structural"] <= 100
    assert "learning" in f["keywords"] or f["word_count"] > 0


def test_matching_and_conflict():
    from types import SimpleNamespace

    from app.services import matching

    paper = matching.paper_profile("Retrieval grounded text classification", "transformer retrieval evaluation",
                                   ["retrieval", "classification"], ["transformer", "evaluation"], ["language"])
    r1 = SimpleNamespace(id=1, display_name="Reviewer Beta", affiliation="Harborview Language Lab",
                         expertise_description="NLP transformers retrieval", research_topics="language, nlp",
                         methods="transformer, evaluation", keywords="nlp, retrieval",
                         publication_titles="", current_load=0, maximum_load=5,
                         is_active=True, conflict_terms="nothing-xyz")
    r2 = SimpleNamespace(id=2, display_name="Reviewer Other", affiliation="Other Lab",
                         expertise_description="security networks", research_topics="security",
                         methods="clustering", keywords="security", publication_titles="",
                         current_load=0, maximum_load=5, is_active=True, conflict_terms="nothing-xyz")
    ranked = matching.match_reviewers(paper, [r1, r2], "some paper text")
    assert ranked[0]["display_name"] == "Reviewer Beta"
    assert ranked[0]["score"] >= ranked[1]["score"]
    assert "breakdown" in ranked[0] and "explanation" in ranked[0]
    # conflict
    r3 = SimpleNamespace(id=3, display_name="Reviewer Beta", affiliation="Harborview Language Lab",
                         expertise_description="NLP", research_topics="language", methods="transformer",
                         keywords="nlp", publication_titles="", current_load=0, maximum_load=5,
                         is_active=True, conflict_terms="retrieval")
    c = matching.detect_conflict("this paper uses retrieval methods", "title", r3)
    assert c["conflicted"] is True


def test_ml_predict_service():
    from app.services import ml_predict

    out = ml_predict.predict_decision("Efficient retrieval grounded classification", "transformer evaluation study")
    assert out["label"] in ("accept", "borderline", "reject", "unavailable")


def test_api_health():
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["product"] == "PeerScope"


def test_reviewer_crud():
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    created = c.post("/api/reviewers", json={"display_name": "Temp Reviewer", "expertise_description": "testing"})
    assert created.status_code == 201
    rid = created.json()["id"]
    upd = c.put(f"/api/reviewers/{rid}", json={"display_name": "Temp Reviewer", "expertise_description": "testing v2"})
    assert upd.status_code == 200
    assert c.delete(f"/api/reviewers/{rid}").status_code == 200


def test_pipeline_with_demo():
    from pathlib import Path

    from fastapi.testclient import TestClient

    from app.main import app

    pdf = Path("data/demo/demo_paper.pdf")
    assert pdf.exists()
    c = TestClient(app)
    with pdf.open("rb") as f:
        r = c.post("/api/analyze", files={"file": ("demo_paper.pdf", f, "application/pdf")})
    assert r.status_code == 200, r.text[:500]
    body = r.json()
    assert body["features"]["word_count"] > 100
    assert len(body["reviewers"]) >= 1
    assert body["review"]["strengths"]
