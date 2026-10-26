"""Verify the ten submission documents at the batch root.

    python scripts/verify_docs.py

Checks: (1) all ten files exist with the exact names and are not under 40 KB (decks excepted when legitimately smaller);
(2) no template leftovers; (3) deck slide counts 16 / 20 / 28; (4) the full report has all ten chapter headings, the
references and three appendices; (5) figures are embedded and every screenshot/diagram referenced exists;
(6) student names, roll numbers and the guide name from 1.*_BATCH_DETAILS.docx appear on the title pages.
Needs python-docx and python-pptx. Exit code 0 only when every check passes.
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_common import BATCH, DIAG, SHOTS, CHARTS  # noqa: E402
from rc_results import SCREENS  # noqa: E402

FILES = ["7.Review_1_PPT.pptx", "9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx", "10.SCOPE & LIMITATIONS.docx", "11. BLOCK DIAGRAMS ALL.docx",
         "12.DESIGN &IMPLEMENTATION.docx", "13.Review_2_PPT.pptx", "14.RESULTS.docx", "15.CONCLUSION&FUTURE SCOPE&REFERENCES.docx",
         "16.Final_PPT.pptx", "17.Final Document.docx"]
DECKS = {"7.Review_1_PPT.pptx": 16, "13.Review_2_PPT.pptx": 20, "16.Final_PPT.pptx": 28}
MIN_KB = 40
EXACT = ["[STUDENT NAME", "[ROLL NO"]
PHRASES = ["Fakeddit", "PHEME", "Snopes", "MCNN", "bank transaction", "social media manipulation", "Hidden Risk of Social Media", "FraudShield",
           "Kafka", "Batch B17", "Batch D1", "Royyala", "GenImage", "ResNet50", "Kaliyar", "Sarwosri", "Chandrakala",
           "SeatWise", "PolicyLens", "TrendCast", "CropSight", "Khaliq", "health insurance", "seating arrangement", "Batch A1 ", "Batch A13", "Batch A17", "OR-Tools"]
PAPER = "19.IEEE_Paper.docx"
PAPER_PHRASES = PHRASES + ["skincare", "Dayananda", "Sindhu", "recommender system"]
CHAPTERS = ["INTRODUCTION", "LITERATURE SURVEY", "FEASIBILITY STUDY", "SYSTEM REQUIREMENTS AND ANALYSIS", "SYSTEM DESIGN",
            "METHODOLOGY AND SOFTWARE IMPLEMENTATION", "SYSTEM TESTING", "RESULTS AND OUTPUT SCREENS", "CONCLUSION", "FUTURE SCOPE"]

failures: list[str] = []


def check(ok: bool, what: str) -> None:
    print(("PASS  " if ok else "FAIL  ") + what)
    if not ok:
        failures.append(what)


def zip_texts(path: Path) -> dict[str, str]:
    """All XML text of a docx/pptx package (including headers, notes, layouts, charts and embedded workbooks)."""
    out: dict[str, str] = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            data = z.read(name)
            if name.endswith((".xml", ".rels")):
                out[name] = re.sub(r"<[^>]+>", " ", data.decode("utf-8", "ignore"))
            elif name.endswith(".xlsx"):
                with zipfile.ZipFile(io.BytesIO(data)) as inner:
                    for n2 in inner.namelist():
                        if n2.endswith(".xml"):
                            out[f"{name}!{n2}"] = re.sub(r"<[^>]+>", " ", inner.read(n2).decode("utf-8", "ignore"))
    return out


def batch_details():
    """Student names, roll numbers and the guide name from 1.*_BATCH_DETAILS.docx (placeholders included as written)."""
    path = next(BATCH.glob("1.*_BATCH_DETAILS.docx"))
    doc = Document(path)
    tokens: list[str] = []
    for t in doc.tables:
        header = [c.text.strip().lower() for c in t.rows[0].cells]
        if any("student" in h for h in header) and any("hall" in h or "roll" in h for h in header):
            for row in t.rows[1:]:
                tokens += [c.text.strip() for c in row.cells[1:] if c.text.strip() and c.text.strip().upper() not in ("STUDENT NAME", "GUIDE NAME")]
    guide = ""
    for p in doc.paragraphs:
        if "guidance" in p.text.lower() and ":" in p.text:
            guide = p.text.split(":", 1)[1].strip()
    return tokens, guide


def docx_first_text(path: Path) -> str:
    doc = Document(path)
    chunks = [p.text for p in doc.paragraphs[:40]]
    for t in doc.tables[:3]:
        for row in t.rows:
            chunks += [c.text for c in row.cells]
    return "\n".join(chunks)


def check_paper() -> None:
    """Checks 7 and 8: the IEEE paper's structure, length, citations and absence of reference-paper leftovers."""
    print("== 7. IEEE paper")
    path = BATCH / PAPER
    check(path.exists(), f"exists: {PAPER}")
    if not path.exists():
        return
    doc = Document(path)
    check(path.stat().st_size / 1024 >= 40, f"size {path.stat().st_size / 1024:,.0f} KB")
    cols = [int(c.get(qn("w:num"), "1")) for c in doc.element.body.iter(qn("w:cols"))]
    check(2 in cols, f"two-column body section (w:cols num values: {cols})")
    paras = [p.text.strip() for p in doc.paragraphs]
    heads = [t for t in paras if re.match(r"^(I|II|III|IV|V)\. [A-Z ]+$", t)]
    check(len(heads) == 5, f"five Roman-numbered sections: {heads}")
    check(any(t.startswith("REFERENCES") for t in paras), "REFERENCES heading")
    text = "\n".join(paras)
    tables = [t for t in paras if re.match(r"^TABLE (I|II)$", t) or t.startswith("TABLE I")]
    check(any(t.startswith("TABLE I") and not t.startswith("TABLE II") for t in paras) and any(t.startswith("TABLE II") for t in paras), "TABLE I and TABLE II present")
    figs = [t for t in paras if re.match(r"^Fig\. \d+\.", t)]
    check(len(figs) >= 4, f"{len(figs)} captioned figures")
    refs = [t for t in paras if re.match(r"^\[\d+\]\t", t)]
    check(15 <= len(refs) <= 20, f"{len(refs)} references (15-20)")
    body = "\n".join(t for t in paras if not re.match(r"^\[\d+\]\t", t))
    cited = set()
    for m in re.finditer(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", body):
        for part in re.split(r"\s*,\s*", m.group(1)):
            if re.search(r"[–-]", part):
                a, b = (int(x) for x in re.split(r"[–-]", part))
                cited.update(range(a, b + 1))
            else:
                cited.add(int(part))
    listed = set(range(1, len(refs) + 1))
    check(cited == listed, f"every reference cited and every citation listed (cited-not-listed {sorted(cited - listed)}, listed-not-cited {sorted(listed - cited)})")
    abstract = next((t for t in paras if t.startswith("Abstract")), "")
    words = len(abstract.split()) - 1
    check(120 <= words <= 200 and not re.search(r"\[\d+\]", abstract), f"abstract {words} words, no citations")
    pdf = BATCH / "19.IEEE_Paper.pdf"
    if pdf.exists():
        import pymupdf
        pages = len(pymupdf.open(pdf))
        check(pages == 6, f"PDF has {pages} pages (target 6)")
    else:
        check(False, "19.IEEE_Paper.pdf missing (run scripts/paper_finish.py)")
    print("== 8. no leftovers from the reference paper or other batches in the paper")
    hits = []
    for name, txt in zip_texts(path).items():
        low = txt.lower()
        for ph in PAPER_PHRASES:
            if ph.lower() in low:
                hits.append((name, ph))
        for tok in EXACT:
            if tok in txt:
                hits.append((name, tok))
    check(not hits, "no leftovers" + (f" -> {hits[:4]}" if hits else ""))
    tokens, guide = batch_details()
    first = "\n".join(c.text for t in doc.tables[:1] for r in t.rows for c in r.cells)
    missing = [t for t in tokens if t not in first]
    check(not missing, "authors and roll numbers in the author block" + (f" -> missing {missing}" if missing else ""))


def main() -> int:
    paths = {f: BATCH / f for f in FILES}
    print("== 1. files")
    for f, p in paths.items():
        check(p.exists(), f"exists: {f}")
        if p.exists():
            kb = p.stat().st_size / 1024
            check(kb >= MIN_KB or f in DECKS and kb >= 20, f"size {kb:,.0f} KB: {f}")
    if failures:
        return 1

    print("== 2. template leftovers")
    for f, p in paths.items():
        texts = zip_texts(p)
        hits = []
        for name, txt in texts.items():
            for tok in EXACT:
                if tok in txt:
                    hits.append((name, tok))
            low = txt.lower()
            for ph in PHRASES:
                if ph.lower() in low:
                    hits.append((name, ph))
        check(not hits, f"no template leftovers in {f}" + (f"  -> {hits[:4]}" if hits else ""))

    print("== 3. deck slide counts")
    for f, n in DECKS.items():
        prs = Presentation(paths[f])
        check(len(prs.slides) == n, f"{f}: {len(prs.slides)} slides (expected {n})")

    print("== 4. full report structure")
    doc = Document(paths["17.Final Document.docx"])
    heads = [p.text.upper().replace("\n", " ").replace("\x0b", " ") for p in doc.paragraphs if p.style.name.startswith("Heading 1")]
    for i, ch in enumerate(CHAPTERS, 1):
        check(any(h.startswith(f"CHAPTER {i}") and ch in h for h in heads), f"chapter {i} heading: {ch}")
    check(any(h.strip() == "REFERENCES" for h in heads), "references section")
    for letter in "ABC":
        check(any(h.startswith(f"APPENDIX {letter}") for h in heads), f"appendix {letter}")
    for front in ("CERTIFICATE", "DECLARATION", "ACKNOWLEDGEMENT", "ABSTRACT", "TABLE OF CONTENTS", "LIST OF FIGURES", "LIST OF TABLES", "LIST OF ABBREVIATIONS"):
        check(any(p.text.strip().upper() == front for p in doc.paragraphs), f"front matter: {front}")

    print("== 5. figures and screenshots")
    for f in FILES:
        if f.endswith(".docx"):
            with zipfile.ZipFile(paths[f]) as z:
                n = len([m for m in z.namelist() if m.startswith("word/media/")])
            need = 3 if "17." in f or "11." in f or "14." in f else 1
            check(n >= need, f"{f}: {n} embedded images")
        else:
            with zipfile.ZipFile(paths[f]) as z:
                n = len([m for m in z.namelist() if m.startswith("ppt/media/")])
            check(n >= 5, f"{f}: {n} media files")
    check(len(doc.inline_shapes) >= 40, f"full report: {len(doc.inline_shapes)} inline figures (need at least 40)")
    missing = [s[0] for s in SCREENS if not (SHOTS / s[0]).exists()]
    check(not missing, f"every screenshot referenced exists ({len(SCREENS)} listed)" + (f"  -> missing {missing}" if missing else ""))
    diag_files = sorted(DIAG.glob("*.png"))
    check(len(diag_files) >= 10, f"{len(diag_files)} diagram files in docs/diagrams")

    print("== 6. names, roll numbers and guide on the title pages")
    tokens, guide = batch_details()
    for f in FILES:
        p = paths[f]
        if f.endswith(".pptx"):
            prs = Presentation(p)
            text = "\n".join(sh.text_frame.text for sh in prs.slides[0].shapes if sh.has_text_frame)
        else:
            text = docx_first_text(p)
        missing = [t for t in tokens if t not in text]
        check(not missing, f"{f}: students/rolls on title page" + (f"  -> missing {missing}" if missing else ""))
        check(guide != "" and guide.lower().strip("[]") in text.lower(), f"{f}: guide name ({guide})")

    check_paper()

    print()
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
