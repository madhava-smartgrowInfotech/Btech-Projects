import pymupdf
import pytest

from app.services.pdf_parser import ScannedPdfError, parse_pdf
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


def test_scanned_pdf_is_rejected(tmp_path):
    path = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.draw_rect(pymupdf.Rect(50, 50, 300, 300), color=(0, 0, 0), fill=(0.8, 0.8, 0.8))
    doc.save(str(path))
    doc.close()
    with pytest.raises(ScannedPdfError):
        parse_pdf(path)
