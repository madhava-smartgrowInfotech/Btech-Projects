from utils.rag_engine import RAGEngine
from utils.text_extraction import chunk_text, clean_text


def build(texts):
    e = RAGEngine()
    e.build_index([{"text": t, "doc_id": 1, "doc_name": "n.txt", "chunk_index": i} for i, t in enumerate(texts)])
    return e


def sample_engine():
    raw = open("sample_data/sample_notes_data_structures.txt", encoding="utf-8").read()
    return build(chunk_text(clean_text(raw)))


def test_empty_index_returns_nothing():
    e = RAGEngine()
    e.build_index([])
    assert e.retrieve("anything") == []
    answer, src = e.generate_answer("anything")
    assert src == [] and answer.startswith("No relevant content")


def test_retrieves_the_right_chunk():
    e = build(["Stacks follow the LIFO principle with push and pop.", "Photosynthesis happens in chloroplasts.",
               "Binary search halves the interval each step."])
    top = e.retrieve("What is the LIFO principle?", top_k=3)[0]
    assert "LIFO" in top["text"] and top["doc_name"] == "n.txt" and 0 < top["score"] <= 1


def test_scores_are_sorted_descending():
    e = sample_engine()
    scores = [r["score"] for r in e.retrieve("sorting algorithms time complexity", top_k=4)]
    assert scores == sorted(scores, reverse=True)


def test_query_without_shared_terms_has_no_results():
    e = build(["Stacks follow the LIFO principle."])
    assert e.retrieve("zebra giraffe", top_k=4) == []
    assert e.generate_answer("zebra giraffe")[0].startswith("No relevant content")


def test_top_k_is_respected():
    e = build(["alpha beta %d" % i for i in range(10)])
    assert len(e.retrieve("alpha beta", top_k=2)) == 2


def test_extractive_answer_is_taken_from_retrieved_text():
    e = sample_engine()
    answer, src = e.generate_answer("What is the LIFO principle?")
    assert "LIFO" in answer
    ctx = " ".join(r["text"] for r in src)
    assert set(answer.lower().split()) <= set(ctx.lower().split())      # extractive: no new words


def test_llm_failure_falls_back_to_extractive(monkeypatch):
    e = sample_engine()

    def boom(*a, **k):
        raise RuntimeError("no network")

    monkeypatch.setattr(e, "_llm_answer", boom)
    answer, src = e.generate_answer("What is a queue?", api_key="fake-key")
    assert "queue" in answer.lower() and src


def test_llm_answer_used_when_available(monkeypatch):
    e = sample_engine()
    monkeypatch.setattr(e, "_llm_answer", lambda q, r, k: "LLM says hello")
    assert e.generate_answer("What is a queue?", api_key="k")[0] == "LLM says hello"


def test_sources_carry_document_names():
    e = sample_engine()
    for r in e.retrieve("binary search tree", top_k=3):
        assert r["doc_name"] == "n.txt" and isinstance(r["chunk_index"], int)
