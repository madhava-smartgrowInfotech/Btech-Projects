import pymupdf
import pytest

from app.services.pdf_parser import Line, ParsedPdf, ScannedPdfError, parse_pdf
from app.services.segmenter import find_uin, segment


def test_parse_and_segment(policy_pdf):
    parsed = parse_pdf(policy_pdf)
    assert parsed.page_count == 2
    text = " ".join(line.text for line in parsed.lines)
    assert "Test Health Insurance Ltd | Policy Wording" not in text  # running header removed
    chunks = segment(parsed)
    refs = {c.clause_ref for c in chunks}
    assert {"2.1", "3.1", "Excl01", "Excl02"} <= refs
    excl02 = next(c for c in chunks if c.clause_ref == "Excl02")
    assert excl02.page_start == 2
    assert "cataract" in excl02.text.lower()
    assert excl02.bboxes and excl02.bboxes[0]["page"] == 2
    assert "4" in excl02.section_path  # nested under "4 Exclusions"
    assert find_uin(parsed) == "TESTHLIP26001V012526"


def _lines(rows: list[tuple[str, bool]]) -> ParsedPdf:
    lines = [Line(page=1, text=t, x0=50, y0=100 + 14 * i, x1=500, y1=112 + 14 * i, size=10, bold=b,
                  bold_lead=t.split(":")[0] if b else "") for i, (t, b) in enumerate(rows)]
    return ParsedPdf(page_count=1, page_sizes=[(595, 842)], lines=lines, two_column=False, body_size=10,
                     text_pages=1, removed_furniture=0)


def test_lettered_exclusion_items_become_clauses():
    """Codes that open an item, close it, or wrap onto the next line each give the item its own clause;
    a code mentioned in prose does not."""
    parsed = _lines([
        ("2. Standard Exclusions", True),
        ("a. Investigation & Evaluation: Code Excl04", True),
        ("i. Expenses related to any admission primarily for diagnostics and evaluation purposes are excluded.", False),
        ("b. Treatment for Alcoholism, drug or substance abuse or any addictive condition and consequences", False),
        ("thereof. Code – Excl12", True),
        ("c. Maternity: Code – Excl18:", True),
        ("i. Medical treatment expenses traceable to childbirth except ectopic pregnancy;", False),
        ("ii. Exclusion no. 3 (Code Excl 03) as stated under this policy shall not apply for the new born baby.", False),
        ("22. Intentional self-injury - Code Excl 22", False),
        ("23. Injury or disease caused by or contributed to by nuclear weapons or materials - Code", False),
        ("Excl 25", True),
    ])
    chunks = segment(parsed)
    by_ref = {c.clause_ref: c for c in chunks}
    assert [c.clause_ref for c in chunks] == ["Excl04", "Excl12", "Excl18", "Excl22", "Excl25"]
    assert by_ref["Excl04"].heading == "Investigation & Evaluation"
    assert by_ref["Excl12"].text.endswith("thereof. Code – Excl12")
    assert by_ref["Excl18"].heading == "Maternity" and "Exclusion no. 3" in by_ref["Excl18"].text
    assert by_ref["Excl22"].heading == "Intentional self-injury"
    assert by_ref["Excl25"].text.endswith("Excl 25")


def test_scanned_pdf_is_rejected(tmp_path):
    path = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.draw_rect(pymupdf.Rect(50, 50, 300, 300), color=(0, 0, 0), fill=(0.8, 0.8, 0.8))
    doc.save(str(path))
    doc.close()
    with pytest.raises(ScannedPdfError):
        parse_pdf(path)
