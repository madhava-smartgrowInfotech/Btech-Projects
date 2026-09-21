"""Deterministic generator for a small, synthetic policy wording PDF used by the tests.

The wording is invented for testing (clearly not a real product) but follows the structure of
Indian policy wordings: numbered sections, definitions, exclusion codes, running headers and
two pages, so the parser, segmenter, retrieval and API can be exercised end-to-end offline.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

HEADER = "Test Health Insurance Ltd | Policy Wording | UIN: TESTHLIP26001V012526"

PAGES = [
    [
        ("h", "1. Preamble"),
        ("p", "This policy is a contract between the insured person and the company. The proposal and declaration form "
              "the basis of this contract."),
        ("h", "2. Definitions"),
        ("p", "2.1. Accident means a sudden, unforeseen and involuntary event caused by external, visible and violent "
              "means."),
        ("p", "2.2. Room Rent means the amount charged by a hospital towards room and boarding expenses."),
        ("h", "3. Coverage"),
        ("p", "3.1. Hospitalization Expenses: We will pay medical expenses for in-patient care up to the sum insured of "
              "Rs. 5,00,000. Room rent is covered up to Rs. 5,000 per day."),
        ("p", "3.2. Pre-hospitalization Expenses: Medical expenses incurred up to 30 days before admission are covered."),
    ],
    [
        ("h", "4. Exclusions"),
        ("p", "4.1. Pre-Existing Diseases - Code Excl01: Expenses related to the treatment of a pre-existing disease "
              "shall be excluded until the expiry of 36 months of continuous coverage."),
        ("p", "4.2. Specified disease waiting period - Code Excl02: Treatment of cataract and joint replacement shall be "
              "excluded until the expiry of 24 months of continuous coverage."),
        ("p", "4.3. Cosmetic or plastic surgery - Code Excl08: Expenses for cosmetic surgery are excluded unless for "
              "reconstruction following an accident, burns or cancer."),
        ("h", "5. Claims"),
        ("p", "5.1. Claim Intimation: In an emergency the company must be informed within 24 hours of hospitalization. "
              "Reimbursement documents must be submitted within 30 days of discharge."),
    ],
]


def make_policy_pdf(path: Path) -> Path:
    doc = pymupdf.open()
    for page_no, blocks in enumerate(PAGES, start=1):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 40), HEADER, fontsize=8, fontname="helv")
        page.insert_text((520, 820), f"{page_no}", fontsize=8, fontname="helv")
        y = 90.0
        for kind, text in blocks:
            if kind == "h":
                page.insert_text((50, y), text, fontsize=13, fontname="hebo")
                y += 26
                continue
            rect = pymupdf.Rect(50, y, 545, y + 200)
            leftover = page.insert_textbox(rect, text, fontsize=10.5, fontname="helv")
            used = 200 - leftover if leftover >= 0 else 200
            y += used + 14
    doc.save(str(path))
    doc.close()
    return path


if __name__ == "__main__":
    out = make_policy_pdf(Path("sample-policy-wording.pdf"))
    print(f"wrote {out}")
