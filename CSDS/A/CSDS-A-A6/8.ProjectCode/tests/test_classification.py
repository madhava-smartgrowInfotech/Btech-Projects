"""F2 clause classification: nearest centroid, Gemini tie-break and the Unclassified floor (stubbed)."""
import numpy as np
import pytest

from app.services import classification, gemini_client

CATS = ["Alpha", "Beta", "Gamma"]


def unit_vec(*xs):
    v = np.array(xs, dtype="float32")
    return v / np.linalg.norm(v)


@pytest.fixture()
def centroids(monkeypatch):
    m = np.vstack([unit_vec(1, 0, 0), unit_vec(0, 1, 0), unit_vec(0, 0, 1)])
    monkeypatch.setattr(classification, "_CENTROIDS_CACHE", (CATS, m))
    return m


def test_confident_embedding_hit_needs_no_model_call(centroids, monkeypatch):
    monkeypatch.setattr(classification, "_tie_break", lambda *a, **k: pytest.fail("tie-break must not run"))
    out = classification.classify_clause("x", embedding=unit_vec(0.95, 0.2, 0.1))
    assert out["clause_type"] == "Alpha"
    assert out["method"] == "embedding"
    assert out["confidence"] > 0.9


def test_unclassified_below_floor(monkeypatch):
    m = np.eye(10, dtype="float32")[:3]
    monkeypatch.setattr(classification, "_CENTROIDS_CACHE", (CATS, m))
    emb = np.zeros(10, dtype="float32")
    emb[0], emb[5] = 0.3, 0.954  # cosine 0.3 with Alpha, 0 with the others: clear winner but under the 0.35 floor
    out = classification.classify_clause("x", embedding=emb)
    assert out["clause_type"] == classification.UNKNOWN_LABEL
    assert out["method"] == "embedding"


def test_close_top_two_with_low_confidence_triggers_tie_break(centroids, monkeypatch):
    calls = []

    def fake(text, candidates, fallback):
        calls.append(candidates)
        return "Beta", 0.8

    monkeypatch.setattr(classification, "_tie_break", fake)
    emb = unit_vec(1.0, 1.0, 0.2)  # Alpha and Beta equal, both ~0.70 -> gap 0 but top1 >= 0.60
    emb2 = unit_vec(1.0, 1.0, 1.0)  # three-way tie at 0.577 (< 0.60)
    classification.classify_clause("x", embedding=emb)
    assert calls == []  # top1 0.70 is not below 0.60
    out = classification.classify_clause("x", embedding=emb2)
    assert calls and len(calls[0]) == 3
    assert out["clause_type"] == "Beta" and out["method"] == "gemini_tiebreak" and out["confidence"] == 0.8


def test_tie_break_failure_falls_back_to_embedding(centroids, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("quota")

    monkeypatch.setattr(classification, "_tie_break", boom)
    out = classification.classify_clause("x", embedding=unit_vec(1.0, 1.0, 1.0))
    assert out["method"] == "embedding"
    assert out["clause_type"] in CATS


def test_tie_break_rejects_a_category_outside_the_candidates(monkeypatch):
    monkeypatch.setattr(gemini_client, "generate_json", lambda p: {"category": "Made Up", "confidence": 0.9})
    assert classification._tie_break("text", ["A", "B", "C"], 0.5) == ("A", 0.5)
    monkeypatch.setattr(gemini_client, "generate_json", lambda p: {"category": "B", "confidence": 0.9})
    assert classification._tie_break("text", ["A", "B", "C"], 0.5) == ("B", 0.9)


def test_below_035_is_other(centroids, monkeypatch):
    monkeypatch.setattr(classification, "_tie_break", lambda *a, **k: ("Alpha", 0.2))
    out = classification.classify_clause("x", embedding=unit_vec(1.0, 1.0, 1.0))
    assert out["clause_type"] == classification.UNKNOWN_LABEL
