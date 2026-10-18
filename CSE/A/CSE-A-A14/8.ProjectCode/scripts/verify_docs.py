"""Verify the eleven submission documents of batch A14.

    python scripts/verify_docs.py           # exit code 0 = all checks pass

Checks: files and names, sizes, template leftovers, deck slide counts, title pages (names, roll numbers, guide),
the ten chapters + references + three appendices of the full report, embedded figures and screenshots, headline numbers against
metrics.json, and the IEEE paper (two columns, five sections, two tables, captioned figures, 15-20 references with one-to-one
citations, page count, fonts).
"""
import glob
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

FILES = {
    "7.Review_1_PPT.pptx": 16, "13.Review_2_PPT.pptx": 20, "16.Final_PPT.pptx": 28,
    "9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx": None, "10.SCOPE & LIMITATIONS.docx": None, "11. BLOCK DIAGRAMS ALL.docx": None,
    "12.DESIGN &IMPLEMENTATION.docx": None, "14.RESULTS.docx": None, "15.CONCLUSION&FUTURE SCOPE&REFERENCES.docx": None,
    "17.Final Document.docx": None, "19.IEEE_Paper.docx": None,
}
STUDENTS = [("ANANTULA SAI NIKHILA SRAVANI", "23K91A0512"), ("AVULA ANUDEEP", "23K91A0518"), ("B SANDEEP", "24K915A0503"), ("DARAGANI VINOD KUMAR", "23K91A0558")]
GUIDE = "SRIKANTH"
LEFTOVERS = ["[STUDENT NAME", "[ROLL NO", "Fakeddit", "PHEME", "Snopes", "MCNN", "bank transaction", "social media manipulation", "Hidden Risk"]
PAPER_LEFTOVERS = ["skincare", "Dayananda", "Sindhu", "recommender system"]
CHAPTERS = ["CHAPTER 1:", "CHAPTER 2:", "CHAPTER 3:", "CHAPTER 4:", "CHAPTER 5:", "CHAPTER 6:", "CHAPTER 7:", "CHAPTER 8:", "CHAPTER 9:", "CHAPTER 10:"]

fails, passes = [], 0


def check(name, ok, detail=""):
    global passes
    if ok:
        passes += 1
        print(f"PASS  {name}")
    else:
        fails.append(name)
        print(f"FAIL  {name}  {detail}")


def xml_text(path):
    """All text of every XML part in an office file (document, headers, footers, notes, layouts, properties)."""
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith(".xml") or n.endswith(".rels"):
                out.append(z.read(n).decode("utf8", "ignore"))
    return "\n".join(out)


def plain_text(path):
    t = xml_text(path)
    t = re.sub(r"</w:p>|</a:p>", "\n", t)
    return re.sub(r"<[^>]+>", "", t)


def docx_paragraphs(path):
    from docx import Document

    return Document(path).paragraphs


M = json.load(open(os.path.join(ROOT, "experiments", "churn_synthetic", "metrics.json"), encoding="utf8"))

# ------------------------------------------------------------------ files, sizes, leftovers
for name, slides in FILES.items():
    p = os.path.join(BATCH, name)
    check(f"exists: {name}", os.path.exists(p))
    if not os.path.exists(p):
        continue
    kb = os.path.getsize(p) / 1024
    if name.endswith(".pptx"):
        check(f"size > 40 KB (deck): {name} ({kb:.0f} KB)", kb > 40)
    else:
        check(f"size >= 40 KB: {name} ({kb:.0f} KB)", kb >= 40)
    raw = xml_text(p)
    plain = plain_text(p)
    bad = [s for s in LEFTOVERS if s in raw or s in plain]
    check(f"no template leftovers: {name}", not bad, str(bad))
    if name.startswith("19."):
        bad = [s for s in PAPER_LEFTOVERS if s.lower() in plain.lower()]
        check("no reference-paper leftovers in the IEEE paper", not bad, str(bad))
    if name.endswith(".pptx"):
        from pptx import Presentation

        prs = Presentation(p)
        check(f"slide count {slides}: {name}", len(prs.slides) == slides, str(len(prs.slides)))
        first = " ".join(sh.text_frame.text for sh in prs.slides[0].shapes if sh.has_text_frame)
        check(f"title slide has names, roll numbers and guide: {name}",
              all(n.split()[0].lower() in first.lower() for n, _ in STUDENTS) and all(r in first for _, r in STUDENTS) and GUIDE in first.upper(), first[:120])
        pics = sum(1 for s in prs.slides for sh in s.shapes if sh.shape_type == 13)
        charts = sum(1 for s in prs.slides for sh in s.shapes if sh.has_chart)
        check(f"pictures / charts on slides: {name} ({pics} / {charts})", pics + charts >= (3 if slides == 16 else 12 if slides == 20 else 16))
        empty_notes = [i + 1 for i, s in enumerate(prs.slides) if not (s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())]
        check(f"speaker notes on every slide: {name}", not empty_notes, str(empty_notes))
    else:
        if not name.startswith("19."):
            head = " ".join(pp.text for pp in docx_paragraphs(p)[:80])
            tables = plain[:6000]
            ok = all(r in plain[:8000] for _, r in STUDENTS) and GUIDE in plain[:8000].upper()
            check(f"title page has names, roll numbers and guide: {name}", ok)

# ------------------------------------------------------------------ full report
rp = os.path.join(BATCH, "17.Final Document.docx")
if os.path.exists(rp):
    paras = docx_paragraphs(rp)
    heads = [p.text.strip() for p in paras if p.style.name.startswith("Heading")]
    for c in CHAPTERS:
        check(f"report heading: {c}", any(h.startswith(c) for h in heads))
    check("report has REFERENCES", "REFERENCES" in heads)
    for a in ("APPENDIX A", "APPENDIX B", "APPENDIX C"):
        check(f"report has {a}", any(h.startswith(a) for h in heads))
    for h in ("CERTIFICATE", "DECLARATION", "ACKNOWLEDGEMENT", "ABSTRACT", "TABLE OF CONTENTS", "LIST OF FIGURES", "LIST OF TABLES", "LIST OF ABBREVIATIONS"):
        check(f"report front matter: {h}", h in heads)
    from docx import Document

    d = Document(rp)
    imgs = len(d.inline_shapes)
    check(f"report embeds figures ({imgs})", imgs >= 40)
    caps_f = sum(1 for p in paras if p.text.startswith("Figure "))
    caps_t = sum(1 for p in paras if p.text.startswith("Table "))
    check(f"report has captioned figures ({caps_f}) and tables ({caps_t})", caps_f >= 40 and caps_t >= 30)
    body = "\n".join(p.text for p in paras)
    refs_start = body.index("\nREFERENCES\n") if "\nREFERENCES\n" in body else len(body)
    ref_nums = set(int(n) for n in re.findall(r"^\[(\d+)\]\s", body[refs_start:], re.M))
    cited = set(int(n) for n in re.findall(r"\[(\d+)\]", body[:refs_start]))
    # numbers cited inside tables
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                cited |= set(int(n) for n in re.findall(r"\[(\d+)\]", c.text))
    check(f"report references: all cited ({len(ref_nums)} listed)", ref_nums and ref_nums <= cited, f"uncited {sorted(ref_nums - cited)}")
    check("report citations all listed", cited <= ref_nums, f"unlisted {sorted(cited - ref_nums)}")

# ------------------------------------------------------------------ screenshots, diagrams, figures
shots = sorted(glob.glob(os.path.join(ROOT, "docs", "screenshots", "*.png")))
check(f"screenshots exist ({len(shots)})", len(shots) >= 16)
diags = glob.glob(os.path.join(ROOT, "docs", "diagrams", "*.png"))
check(f"diagrams exist ({len(diags)})", len(diags) >= 10)
for must in ("01_system_architecture", "02_high_level_workflow", "03_dfd_level0", "04_dfd_level1", "05_dfd_level2", "06_uml_class_diagram",
             "07_sequence_diagram", "08_use_case_diagram", "09_er_diagram", "10_core_algorithm_flowchart"):
    check(f"diagram: {must}", os.path.exists(os.path.join(ROOT, "docs", "diagrams", must + ".png")))
check("result figures exist", len(glob.glob(os.path.join(ROOT, "docs", "figures", "*.png"))) >= 12)

# ------------------------------------------------------------------ headline numbers
lr = M["app_default_split"]["class_weight"]["models"]["Logistic Regression"]
res = os.path.join(BATCH, "14.RESULTS.docx")
if os.path.exists(res):
    t = plain_text(res)
    for k in ("accuracy", "precision", "recall", "f1_score", "roc_auc"):
        check(f"results document quotes LR {k} {lr[k]:.4f}", f"{lr[k]:.4f}" in t)
    check("results document states the synthetic-data caveat", "synthetic" in t.lower())
    check("results document states the base-paper comparability caveat", "not comparable" in t.lower())

# ------------------------------------------------------------------ IEEE paper
pp = os.path.join(BATCH, "19.IEEE_Paper.docx")
if os.path.exists(pp):
    x = xml_text(pp)
    check("paper: two-column section (w:cols num=2)", re.search(r'<w:cols[^>]*w:num="2"', x) is not None)
    check("paper: column spacing 360", re.search(r'<w:cols[^>]*w:space="360"', x) is not None)
    m = re.search(r"<w:pgSz[^>]*>", x)
    check("paper: US Letter", m and 'w:w="12240"' in m.group(0) and 'w:h="15840"' in m.group(0))
    pt = plain_text(pp)
    romans = [r for r in ("I. INTRODUCTION", "II. LITERATURE SURVEY", "III. METHODOLOGY", "IV. RESULTS", "V. CONCLUSION") if r in pt]
    check(f"paper: five Roman sections ({len(romans)})", len(romans) == 5)
    check("paper: REFERENCES heading", "REFERENCES" in pt)
    check("paper: TABLE I and TABLE II", "TABLE I" in pt and "TABLE II" in pt)
    nfig = len(set(re.findall(r"Fig\. (\d+)\.", pt)))
    check(f"paper: >= 4 captioned figures ({nfig})", nfig >= 4)
    abstract = re.search(r"Abstract.{0,3}(.*?)Index Terms", pt, re.S)
    if abstract:
        wc = len(abstract.group(1).split())
        check(f"paper: abstract 120-200 words ({wc})", 120 <= wc <= 200)
        check("paper: abstract has no citations", not re.search(r"\[\d+\]", abstract.group(1)))
    body, _, refs = pt.partition("REFERENCES")
    refn = re.findall(r"^\s*\[(\d+)\]", refs, re.M)
    check(f"paper: 15-20 references ({len(refn)})", 15 <= len(refn) <= 20)
    cited = set()
    for grp in re.findall(r"\[([\d,\s–—\-]+)\]", body):
        for part in re.split(r",\s*", grp.strip()):
            r = re.split(r"[–—\-]", part)
            if len(r) == 2 and r[0].strip().isdigit() and r[1].strip().isdigit():
                cited |= set(range(int(r[0]), int(r[1]) + 1))
            elif part.strip().isdigit():
                cited.add(int(part))
    refset = set(int(n) for n in refn)
    check("paper: every reference cited", refset <= cited, f"uncited {sorted(refset - cited)}")
    check("paper: every citation listed", cited <= refset, f"unlisted {sorted(cited - refset)}")
    with zipfile.ZipFile(pp) as _z:
        fonts = set(re.findall(r'w:ascii="([^"]+)"', _z.read("word/document.xml").decode("utf8", "ignore")))
    check(f"paper: Times New Roman only ({sorted(fonts)})", fonts <= {"Times New Roman", "Symbol", "Cambria Math"} and "Times New Roman" in fonts)
    pdf = os.path.join(BATCH, "19.IEEE_Paper.pdf")
    if os.path.exists(pdf):
        import pymupdf

        n = len(pymupdf.open(pdf))
        last = pymupdf.open(pdf)[n - 1]
        words_last = len(last.get_text().split())
        eff = n if words_last > 600 else n - 1 + words_last / 700
        check(f"paper: 6 pages (5.5-6.5), PDF has {n} pages, effective {eff:.1f}", 5.5 <= eff <= 6.5)
    else:
        words = len(body.split())
        check(f"paper: no PDF, word target 5,200-5,800 ({words})", 5200 <= words <= 5800)

print(f"\n{passes} passed, {len(fails)} failed")
if fails:
    print("FAILED:", "; ".join(fails))
    sys.exit(1)
print("All documentation checks passed.")
