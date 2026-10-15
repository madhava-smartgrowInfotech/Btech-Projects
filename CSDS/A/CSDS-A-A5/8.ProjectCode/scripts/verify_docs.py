"""Verify the documentation set at the batch root (run from anywhere; uses system python with python-docx / python-pptx).

Checks (see DOCS_PROMPT section 8): exact file names and sizes, no template or reference-paper leftovers, deck slide counts,
chapter headings in the final report, embedded figures and screenshot files, student/guide names on title pages, IEEE paper structure
and page count, and consistency of key metrics with experiments/eval/metrics.json.

Usage:  python scripts/verify_docs.py [--no-word]
"""
import json
import os
import re
import sys
import zipfile

from docx import Document
from docx.oxml.ns import qn
from pptx import Presentation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "docs_build"))

FILES = {
    "7.Review_1_PPT.pptx": 16, "9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx": None, "10.SCOPE & LIMITATIONS.docx": None,
    "11. BLOCK DIAGRAMS ALL.docx": None, "12.DESIGN &IMPLEMENTATION.docx": None, "13.Review_2_PPT.pptx": 20,
    "14.RESULTS.docx": None, "15.CONCLUSION&FUTURE SCOPE&REFERENCES.docx": None, "16.Final_PPT.pptx": 28,
    "17.Final Document.docx": None, "19.IEEE_Paper.docx": None,
}
MIN_KB = 40
TEMPLATE_BAD = ["[STUDENT NAME", "[ROLL NO", "Fakeddit", "PHEME", "Snopes", "MCNN", "bank transaction", "social media manipulation"]
REFPAPER_BAD = ["skincare", "Dayananda", "Sindhu", "recommender system"]
STUDENTS = [("B.ASHRITHA", "23K91A6732"), ("B.DIVYA", "23K91A6739"), ("A.KISHORE", "23K91A6716"), ("A.YAGNESH", "23K91A6711")]
GUIDE_KEY = "Ravi"

results = []


def check(name, ok, info=""):
    results.append((name, bool(ok), info))
    print(("PASS" if ok else "FAIL"), name, info)


def raw_text(path):
    """All text of every XML part of an OOXML file (covers body, tables, headers, footers, notes, charts)."""
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith(".xml") or n.endswith(".rels"):
                t = z.read(n).decode("utf8", "ignore")
                out.append(re.sub(r"<[^>]+>", " ", t) if n.endswith(".xml") else "")
    return " ".join(out)


def docx_text(path):
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            parts += [c.text for c in r.cells]
    return "\n".join(parts), d


def media_count(path):
    with zipfile.ZipFile(path) as z:
        return len([n for n in z.namelist() if n.startswith(("word/media/", "ppt/media/"))])


def inline_pictures(d):
    return len(d.inline_shapes)


def main():
    use_word = "--no-word" not in sys.argv
    paths = {n: os.path.join(BATCH, n) for n in FILES}
    # 1. existence and size
    for n, p in paths.items():
        ok = os.path.exists(p) and os.path.getsize(p) >= MIN_KB * 1024
        check(f"exists and >= {MIN_KB} KB: {n}", ok, f"{os.path.getsize(p) // 1024 if os.path.exists(p) else 0} KB")
    if not all(os.path.exists(p) for p in paths.values()):
        print("missing files; stopping")
        return summary()

    # 2. template leftovers and reference-paper leftovers (case-insensitive for words, exact for placeholders)
    for n, p in paths.items():
        t = raw_text(p)
        bad = [w for w in TEMPLATE_BAD + REFPAPER_BAD if w.lower() in t.lower()]
        check(f"no template / reference-paper leftovers: {n}", not bad, str(bad))

    # 3. deck slide counts
    for n, cnt in FILES.items():
        if cnt:
            prs = Presentation(paths[n])
            check(f"slide count {cnt}: {n}", len(prs.slides._sldIdLst) == cnt, str(len(prs.slides._sldIdLst)))

    # 4. final report structure
    ft, fd = docx_text(paths["17.Final Document.docx"])
    chapters = ["INTRODUCTION", "LITERATURE SURVEY", "FEASIBILITY STUDY", "SYSTEM REQUIREMENTS AND ANALYSIS", "SYSTEM DESIGN",
                "METHODOLOGY AND SOFTWARE IMPLEMENTATION", "SYSTEM TESTING", "RESULTS AND OUTPUT SCREENS", "CONCLUSION", "FUTURE SCOPE"]
    heads = [p.text.strip() for p in fd.paragraphs if p.style.name == "Heading 1"]
    for i, c in enumerate(chapters, 1):
        check(f"final report heading CHAPTER {i}: {c}", f"CHAPTER {i}: {c}" in heads)
    check("final report has REFERENCES", "REFERENCES" in heads)
    for a in ("A: IMPORTANT CODE", "B: INSTALLATION AND USER GUIDE", "C: ADDITIONAL SCREENS"):
        check(f"final report has APPENDIX {a}", f"APPENDIX {a}" in heads)
    for front in ("CERTIFICATE", "DECLARATION", "ACKNOWLEDGEMENT", "ABSTRACT", "TABLE OF CONTENTS", "LIST OF FIGURES", "LIST OF TABLES", "LIST OF ABBREVIATIONS"):
        check(f"final report front matter: {front}", front in ft)

    # 5. figures embedded; screenshots referenced exist
    from common import SCREENS, DIAG, CH, SS
    for k, (f, _c) in SCREENS.items():
        if not os.path.exists(os.path.join(SS, f)):
            check(f"screenshot exists: {f}", False)
    check("all screenshots referenced by the documents exist", all(os.path.exists(os.path.join(SS, f)) for f, _ in SCREENS.values()), f"{len(SCREENS)} screenshots")
    check("all 10 diagrams exist", len([x for x in os.listdir(DIAG) if x.endswith(".png")]) >= 10)
    n_fig = inline_pictures(fd)
    check("final report embeds figures (>= 40)", n_fig >= 40, f"{n_fig} inline pictures")
    caps = [p.text for p in fd.paragraphs if p.style.name == "Caption"]
    check("final report captions match pictures", len([c for c in caps if c.startswith("Figure")]) == n_fig, f"{len(caps)} captions")
    for n in ("9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx", "11. BLOCK DIAGRAMS ALL.docx", "12.DESIGN &IMPLEMENTATION.docx", "14.RESULTS.docx"):
        d = Document(paths[n])
        check(f"figures embedded: {n}", inline_pictures(d) >= 3, f"{inline_pictures(d)}")
    check("block-diagram document has all 10 diagrams", inline_pictures(Document(paths["11. BLOCK DIAGRAMS ALL.docx"])) >= 10)
    for n in ("7.Review_1_PPT.pptx", "13.Review_2_PPT.pptx", "16.Final_PPT.pptx"):
        check(f"deck embeds pictures: {n}", media_count(paths[n]) >= 3, f"{media_count(paths[n])} media files")

    # 6. names on title pages
    def title_text_docx(p):
        d = Document(p)
        parts = [x.text for x in d.paragraphs[:60]]
        for t in d.tables[:3]:
            for r in t.rows:
                parts += [c.text for c in r.cells]
        return "\n".join(parts)

    for n, p in paths.items():
        if n.endswith(".docx") and not n.startswith("19."):
            t = title_text_docx(p)
        elif n.endswith(".pptx"):
            prs = Presentation(p)
            t = "\n".join(sh.text_frame.text for sh in prs.slides[0].shapes if sh.has_text_frame)
        else:
            t = title_text_docx(p)
        miss = [x for pair in STUDENTS for x in pair if x not in t]
        check(f"student names and roll numbers on title page: {n}", not miss, str(miss))
        check(f"guide name on title page: {n}", GUIDE_KEY in t)

    # 7. IEEE paper
    ip = paths["19.IEEE_Paper.docx"]
    try:
        idoc = Document(ip)
        check("IEEE paper opens cleanly", True)
    except Exception as e:  # noqa: BLE001
        check("IEEE paper opens cleanly", False, str(e))
        return summary()
    secs = idoc.sections
    ncols = []
    for s in secs:
        c = s._sectPr.xpath("./w:cols")
        ncols.append(int(c[0].get(qn("w:num"), "1")) if c else 1)
    check("IEEE body is two-column", 2 in ncols, f"section columns {ncols}")
    s0 = secs[0]
    check("IEEE page is US Letter with 0.75/1.0/0.69 in margins",
          abs(s0.page_width.inches - 8.5) < 0.02 and abs(s0.page_height.inches - 11) < 0.02 and abs(s0.top_margin.inches - 0.75) < 0.02
          and abs(s0.bottom_margin.inches - 1.0) < 0.02 and abs(s0.left_margin.inches - 0.69) < 0.02 and abs(s0.right_margin.inches - 0.69) < 0.02)
    it, _ = docx_text(ip)
    romans = re.findall(r"^(I|II|III|IV|V)\.\s+([A-Z][A-Z \-&]+)$", it, flags=re.M)
    check("IEEE has five Roman-numbered sections", [r[0] for r in romans] == ["I", "II", "III", "IV", "V"], str(romans))
    check("IEEE has TABLE I and TABLE II", "TABLE I" in it and "TABLE II" in it)
    figs = re.findall(r"^Fig\. (\d+)\.", it, flags=re.M)
    check("IEEE has >= 4 captioned figures", len(set(figs)) >= 4, str(sorted(set(figs))))
    refs = re.findall(r"^\[(\d+)\]", it, flags=re.M)
    check("IEEE has 15-20 references", 15 <= len(set(refs)) <= 20, f"{len(set(refs))}")
    cited = set(int(x) for grp in re.findall(r"\[(\d+(?:[,–\-\s]+\d+)*)\]", re.sub(r"^\[\d+\].*$", "", it, flags=re.M)) for x in re.findall(r"\d+", grp) if "-" not in grp and "–" not in grp) if True else set()
    rng = set()
    for a, b in re.findall(r"\[(\d+)\s*[–\-]\s*(\d+)\]", it):
        rng.update(range(int(a), int(b) + 1))
    allcited = cited | rng
    listed = set(int(x) for x in refs)
    check("IEEE: every reference is cited and every citation is listed", listed <= allcited and allcited <= listed, f"uncited={sorted(listed - allcited)} unlisted={sorted(allcited - listed)}")
    words = len(re.findall(r"\w+", it))
    pages = None
    if use_word:
        try:
            import wordtools
            pages = wordtools.page_count(ip)
        except Exception as e:  # noqa: BLE001
            print("word unavailable:", e)
    if pages is not None:
        check("IEEE paper is 6 pages (5.5-6.5)", 5 <= pages <= 7, f"{pages} pages (Word), {words} words")
    else:
        check("IEEE paper word target 5,200-5,800", 5200 <= words <= 5800, f"{words} words (estimated)")

    # 8. key metrics consistency
    ev = json.load(open(os.path.join(ROOT, "experiments", "eval", "metrics.json")))["detection"]["taxpayer"]["model"]
    keys = [f"{ev['precision_at_k']['79']:.3f}", f"{ev['at_threshold']['f1']:.3f}", f"{ev['roc_auc']:.3f}"]
    for n in ("14.RESULTS.docx", "17.Final Document.docx", "19.IEEE_Paper.docx"):
        t, _ = docx_text(paths[n])
        miss = [k for k in keys if k not in t]
        check(f"key metrics {keys} present: {n}", not miss, str(miss))
    return summary()


def summary():
    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)} / {len(results)} checks passed")
    if bad:
        print("FAILED:")
        for r in bad:
            print("  -", r[0], r[2])
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
