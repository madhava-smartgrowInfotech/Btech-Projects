"""Complexity score (F5), parsing and clause splitting (F1), local vector store."""
import numpy as np
import pytest

from app.services import complexity, parsing, vectorstore

PLAIN = ("You pay us on time. We do the work well. Either of us can stop the deal with a month of notice. "
         "If something breaks we fix it. We keep your data safe. ") * 6
DENSE = ("Notwithstanding anything herein to the contrary, the party of the first part shall indemnify the party of the second part "
         "pursuant to Section 4.2 hereof, and the aforementioned covenant shall survive termination hereunder, without prejudice to "
         "the successors and assigns, whereas the arbitration shall be subject to the jurisdiction set out in Clause 9. ") * 6


def test_syllable_counter():
    assert complexity._count_syllables("contract") == 2
    assert complexity._count_syllables("a") == 1
    assert complexity._count_syllables("") == 0


def test_flesch_is_bounded_and_orders_plain_above_dense():
    assert 0 <= complexity.flesch_reading_ease(DENSE) <= 100
    assert complexity.flesch_reading_ease(PLAIN) > complexity.flesch_reading_ease(DENSE)
    assert complexity.flesch_reading_ease("") == 0.0


def test_legalese_density_counts_listed_terms():
    assert complexity.legalese_density("") == 0.0
    assert complexity.legalese_density("The parties agree hereto and herein.") > 0
    assert complexity.legalese_density(DENSE) > complexity.legalese_density(PLAIN)


def test_cross_references_counted():
    assert complexity.cross_reference_count("See Section 4.2 and Clause 9; as set out herein.") == 3
    assert complexity.cross_reference_count("Nothing to see.") == 0


def test_dense_contract_scores_harder_than_plain_one():
    easy = complexity.score_contract(PLAIN, 6)
    hard = complexity.score_contract(DENSE, 6)
    assert hard["complexity_score"] > easy["complexity_score"]
    assert easy["complexity_grade"] in "AB"
    assert hard["complexity_grade"] in "CDF"


@pytest.mark.parametrize("score,grade", [(0, "A"), (19.9, "A"), (20, "B"), (39.9, "B"), (40, "C"), (59.9, "C"), (60, "D"), (80, "F")])
def test_grade_boundaries(score, grade, monkeypatch):
    # Make all four difficulty components equal to `score`; the weights sum to 1, so the weighted score is `score`.
    monkeypatch.setattr(complexity, "flesch_reading_ease", lambda t: 100 - score)
    monkeypatch.setattr(complexity, "legalese_density", lambda t: score / 8)
    monkeypatch.setattr(complexity, "cross_reference_count", lambda t: score / 40)
    monkeypatch.setattr(complexity, "avg_sentence_length", lambda t: 15 + score / 3)
    out = complexity.score_contract("x", 1)
    assert out["complexity_score"] == pytest.approx(score, abs=0.11)
    assert out["complexity_grade"] == grade


TEXT = """1. Scope
The Consultant shall provide the services described in Schedule A to the Company.

2. Payment
The Company shall pay the monthly fee within thirty days of the invoice date.

3. Term
This Agreement runs for twelve months from the date of signature by both parties.
"""


def page(text, n=1):
    return parsing.ParsedPage(text=text, page_number=n)


def test_numbered_headings_split_into_clauses():
    out = parsing.split_into_clauses([page(TEXT)])
    assert len(out) == 3
    assert out[0]["text"].startswith("1. Scope")
    assert [c["index_in_doc"] for c in out] == [0, 1, 2]


def test_text_before_the_first_numbered_heading_is_dropped():
    preamble = "SERVICES AGREEMENT between Acme Pvt Ltd and the Consultant, made on 1 January 2026."
    out = parsing.split_into_clauses([page(preamble + chr(10) * 2 + TEXT)])
    assert len(out) == 3
    assert all("Acme" not in c["text"] for c in out)


def test_paragraph_fallback_merges_short_paragraphs():
    text = "\n\n".join(f"Short paragraph number {i} about something in the agreement." for i in range(6))
    out = parsing.split_into_clauses([page(text)])
    assert 1 <= len(out) < 6


def test_fragments_under_25_characters_are_dropped_and_empty_input_raises():
    assert parsing.split_into_clauses([page("1. A\n\n2. This clause is long enough to be kept as a clause.")])
    with pytest.raises(ValueError):
        parsing.split_into_clauses([page("   ")])
    with pytest.raises(ValueError):
        parsing.split_into_clauses([page("Hi")])


def test_page_numbers_are_kept():
    out = parsing.split_into_clauses([page(TEXT, 1), page(TEXT, 2)])
    assert {c["page_number"] for c in out} == {1, 2}
    assert len(out) == 6


def test_docx_and_pdf_extraction(tmp_path, docx_bytes):
    import fitz

    d = tmp_path / "c.docx"
    d.write_bytes(docx_bytes(TEXT))
    pages = parsing.extract_pages(str(d), "")
    assert len(pages) == 1 and "Payment" in pages[0].text

    pdf = tmp_path / "c.pdf"
    doc = fitz.open()
    for body in (TEXT, TEXT):
        doc.new_page().insert_text((50, 72), body, fontsize=10)
    doc.save(str(pdf))
    doc.close()
    pages = parsing.extract_pages(str(pdf), "application/pdf")
    assert [p.page_number for p in pages] == [1, 2]


def test_unsupported_file_type_rejected(tmp_path):
    f = tmp_path / "c.txt"
    f.write_text("hello")
    with pytest.raises(ValueError):
        parsing.extract_pages(str(f), "text/plain")


def test_vector_store_roundtrip_and_similarity():
    v = [0.5, -1.25, 3.0]
    assert vectorstore.from_blob(vectorstore.to_blob(v)).tolist() == v
    a, b = np.array([1.0, 0.0]), np.array([0.0, 1.0])
    assert vectorstore.cosine_similarity(a, a) == pytest.approx(1.0)
    assert vectorstore.cosine_similarity(a, b) == pytest.approx(0.0)
    assert vectorstore.cosine_similarity(a, np.zeros(2)) == 0.0
    top = vectorstore.top_k_similar(np.array([1.0, 0.1]), np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]), k=2)
    assert [i for i, _ in top] == [1, 2]
