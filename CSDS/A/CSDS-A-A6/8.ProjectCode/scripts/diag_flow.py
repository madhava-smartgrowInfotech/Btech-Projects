"""DFD level 1 and 2 and the core-algorithm flowcharts for ClauseGuard."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas


def store(c, x, y, w, h, label, fc="#fff8e8", fs=6.2):
    """Open-ended rectangle: a data store (id | name)."""
    c.rect(x, y, w, h, fc=fc, ec="#44506b", lw=1.1)
    c.line((x + 5, y), (x + 5, y + h))
    a, b = label.split(" ", 1)
    c.text(x + 2.5, y + h / 2, a, fs=7, bold=True)
    c.text(x + 5 + (w - 5) / 2, y + h / 2, b, fs=fs)


def dfd1(out):
    c = Canvas(10.4, 7.2)
    c.text(52, 69.5, "DFD level 1", fs=11, bold=True)
    c.box(2, 56, 26, 8, "Signatory", fc=BLUE_L, fs=7.4, bold=True)
    c.box(52, 56, 36, 8, "Google Gemini API", fc=ROSE_L, ec="#c98a8a", fs=7.4, bold=True)
    xs = [8, 22.5, 37, 51.5, 66, 80.5, 95]
    names = ["1.0\nAuthen-\nticate", "2.0\nParse and\nsegment", "3.0\nClassify\nclauses", "4.0\nDetect\npredatory\nclauses",
             "5.0\nCombine\nrisks, score\ncomplexity", "6.0\nExplain and\nsummarise", "7.0\nReport\nand browse"]
    for x, t in zip(xs, names):
        c.ellipse(x, 38, 13.4, 13.5, t, fc=INDIGO_L, ec=INDIGO, fs=5.9)
    # external flows
    c.arrow((7, 56), (7, 44.8), both=True, label="email, password,\nJWT", lpos=0.5, loff=(-0.8, 0), lha="right", fs=5.6)
    c.arrow((22.5, 56), (22.5, 44.8), label="contract file", loff=(1, 0), lha="left", fs=5.6)
    c.path([(52, 60), (37, 60), (37, 44.8)], label="clause vectors,\ntie-break answers", seg=1, loff=(-1, 0), lha="right", fs=5.6, ls="--")
    c.arrow((80.5, 56), (80.5, 44.8), both=True, label="prompts / text", loff=(1, 0), lha="left", fs=5.6, ls="--")
    c.path([(95, 44.8), (95, 67), (15, 67), (15, 64)], label="grade, flags, reasons, safer wording, graph", seg=1, loff=(20, 1.6), fs=5.6)
    labs = ["authorised\nuser", "clauses", "clauses +\ntypes", "rule ids\nper clause", "flags, combos,\nscores", "explanations,\nsummary"]
    for i, t in enumerate(labs):
        c.arrow((xs[i] + 6.8, 38), (xs[i + 1] - 6.8, 38), label=t, loff=(0, 5.6), fs=5.2)
    st = [("D1 users", 8), ("D2 contracts", 22.5), ("D3 clauses", 37), ("D4 flags", 51.5), ("D2 contracts", 66), ("D4 flags", 80.5), ("D2-D4 (read)", 95)]
    for t, x in st:
        store(c, x - 7, 14, 14, 5.6, t, fs=5.4)
        c.arrow((x, 31.2), (x, 19.6), both=(x != 95), ls=":", head=True)
    store(c, 24, 4.5, 26, 5.2, "D5 centroid cache (npz) - read by 3.0", fs=5.4)
    c.arrow((35, 14), (35, 9.7), ls=":")
    c.text(75, 7.0, "D1-D4: SQLite tables users, contracts, clauses, flags. Evaluation (ml/eval.py)", fs=5.6, italic=True)
    c.text(75, 4.0, "runs offline and is shown in DFD level 0, not here.", fs=5.6, italic=True)
    c.text(52, 0.9, "1.0 issues the JWT; every other process checks it and the owner of the contract. Solid: external and process flows; dotted: store access; dashed: Gemini calls.", fs=5.6, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(10.4, 6.6)
    c.text(52, 63, "DFD level 2 - process 3.0 Classify clauses", fs=11, bold=True)
    c.box(1, 38, 14, 10, "2.0 Parse and\nsegment\n(clause text)", fc=GREY_L, fs=6.4, bold=True)
    xs = [27, 47, 67, 87]
    top = ["3.1\nLoad or build\n20 category\ncentroids", "3.2\nEmbed clause\n(gemini-embedding-001,\nRETRIEVAL_QUERY)", "3.3\nCosine similarity to\n20 centroids; rank", "3.4\nMargin test:\ntop1 - top2 < 0.03\nand top1 < 0.60 ?"]
    for x, t in zip(xs, top):
        c.ellipse(x, 43, 18, 14, t, fc=INDIGO_L, ec=INDIGO, fs=6.1)
    c.ellipse(87, 18, 18, 14, "3.5\nGemini tie-break\namong top 3", fc=ROSE_L, ec="#c98a8a", fs=6.2)
    c.ellipse(63, 18, 18, 14, "3.6\nFloor test:\nconfidence < 0.35\n-> Unclassified", fc=INDIGO_L, ec=INDIGO, fs=6.1)
    c.ellipse(39, 18, 18, 14, "3.7\nWrite clause_type,\nconfidence, method,\nembedding BLOB", fc=INDIGO_L, ec=INDIGO, fs=6.1)
    c.arrow((15, 43), (18, 43))
    c.arrow((54.5, 43), (57.5, 43), head=False)
    c.arrow((36, 43), (38, 43))
    c.arrow((56, 43), (58, 43))
    c.arrow((76, 43), (78, 43))
    c.arrow((87, 36), (87, 25), label="yes (not seen on\nCUAD spans)", loff=(9, 0), fs=5.8)
    c.arrow((78, 18), (72, 18))
    c.arrow((79.5, 38.2), (67.5, 24.8), label="no", loff=(-3.5, 1.5), fs=5.8)
    c.arrow((54, 18), (48, 18))
    c.box(2, 10, 16, 8, "D5 centroid cache\n(npz) / CUAD\ntraining spans", fc="#fff8e8", ec="#44506b", fs=5.8)
    c.arrow((18, 14), (27, 36), ls=":")
    c.box(2, 22, 16, 7, "D3 clauses\n(table)", fc="#fff8e8", ec="#44506b", fs=6.0)
    c.arrow((30, 18), (18, 25.5), ls=":")
    c.box(40, 53, 28, 6, "Google Gemini API (embedding, generate)", fc=ROSE_L, ec="#c98a8a", fs=6.2, bold=True)
    c.arrow((47, 49.8), (47, 53), both=True, ls="--")
    c.path([(87, 25), (95, 25), (95, 55.5), (68, 55.5)], ls="--", head=False)
    c.text(52, 3.5, "Measured on 240 held-out CUAD spans: top-1 cosine ranges 0.657-0.849, so the 0.60 and 0.35 tests never fire; every clause receives one of the 20 labels.", fs=6.1, italic=True)
    c.save(out)


def flowchart(out):
    c = Canvas(10.4, 9.0)
    cx, rx = 24, 79
    c.text(2, 87.5, "Algorithm 1: process_upload()  (POST /api/contracts/upload)", fs=7.4, bold=True, ha="left")
    c.text(58, 87.5, "Algorithm 2: classify_clause()", fs=7.4, bold=True, ha="left")
    c.terminal(cx, 83, 34, 4.2, "Start: PDF / DOCX from a signed-in user", fs=6.6)
    c.diamond(cx, 75.5, 32, 7.5, "extension .pdf\nor .docx ?", fs=6.4)
    c.box(cx - 17, 63.5, 34, 5.8, "extract pages (PDF per page, DOCX = page 1);\nsplit each page into clauses (headings / paragraphs)", fc=BLUE_L, fs=6.2)
    c.diamond(cx, 54.5, 32, 7.5, "any clause of\n>= 25 characters ?", fs=6.4)
    c.box(cx - 17, 42, 34, 6, "for each clause: classify (Algorithm 2);\ndetect_flags(): 8 regex rules; Gemini explains each hit", fc=INDIGO_L, fs=6.1)
    c.box(cx - 17, 32.5, 34, 5.6, "detect_risky_combinations() on all rule ids;\nscore_contract(): complexity 0-100 -> A-F", fc=INDIGO_L, fs=6.1)
    c.box(cx - 17, 23.5, 34, 5.6, "Gemini summary of the first 40 clauses and\nthe flag list -> plain_summary, key_obligations", fc=ROSE_L, ec="#c98a8a", fs=6.1)
    c.box(cx - 17, 14.5, 34, 5.6, "commit contract, clauses, flags (one transaction);\ndelete the uploaded file", fc=GREEN_L, fs=6.2)
    c.terminal(cx, 6, 26, 4.2, "End: report returned", fs=6.6)
    c.arrow((cx, 80.9), (cx, 79.25))
    c.arrow((cx, 71.75), (cx, 69.3), label="yes", loff=(2.5, 0), fs=5.8)
    c.arrow((cx, 63.5), (cx, 58.25))
    c.arrow((cx, 50.75), (cx, 48), label="yes", loff=(2.5, 0), fs=5.8)
    c.arrow((cx, 42), (cx, 38.1))
    c.arrow((cx, 32.5), (cx, 29.1))
    c.arrow((cx, 23.5), (cx, 20.1))
    c.arrow((cx, 14.5), (cx, 8.1))
    c.box(45.5, 72.5, 9.5, 6, "HTTP 400", fc=ROSE_L, ec="#c98a8a", fs=6.2)
    c.arrow((cx + 16, 75.5), (45.5, 75.5), label="no", loff=(0, 1.6), fs=5.8)
    c.box(45.5, 51.5, 9.5, 6, "HTTP 400\nno clauses", fc=ROSE_L, ec="#c98a8a", fs=5.8)
    c.arrow((cx + 16, 54.5), (45.5, 54.5), label="no", loff=(0, 1.6), fs=5.8)
    c.box(45.5, 40.5, 9.5, 9, "Gemini failure\n(3 retries):\nHTTP 502,\nrollback", fc=ROSE_L, ec="#c98a8a", fs=5.6)
    c.arrow((cx + 17, 45), (45.5, 45), ls="--")
    # algorithm 2
    c.terminal(rx, 83, 36, 4.2, "Start: clause text", fs=6.6)
    c.box(rx - 18, 73.5, 36, 6, "embed (gemini-embedding-001, RETRIEVAL_QUERY);\ncosine to the 20 centroids; sort", fc=BLUE_L, fs=6.1)
    c.diamond(rx, 63, 36, 9, "top1 - top2 < 0.03\nand top1 < 0.60 ?", fs=6.3)
    c.box(rx - 18, 47.5, 36, 6, "ask Gemini to pick one of the top 3\n(JSON: category, confidence)", fc=ROSE_L, ec="#c98a8a", fs=6.1)
    c.diamond(rx, 37, 36, 8.5, "category in the\ncandidates ?", fs=6.3)
    c.diamond(rx, 25.5, 36, 8.5, "confidence < 0.35 ?", fs=6.3)
    c.box(rx - 18, 12.5, 36, 5.6, "label = 'Other / Unclassified'", fc=AMBER_L, ec="#c9a45a", fs=6.2)
    c.terminal(rx, 4.5, 36, 4.2, "Return type, confidence, method, vector", fs=6.4)
    c.arrow((rx, 80.9), (rx, 79.5))
    c.arrow((rx, 73.5), (rx, 67.5))
    c.arrow((rx, 58.5), (rx, 53.5), label="yes", loff=(2.5, 0), fs=5.8)
    c.arrow((rx, 47.5), (rx, 41.25))
    c.arrow((rx, 32.75), (rx, 29.75), label="yes", loff=(2.5, 0), fs=5.8)
    c.arrow((rx, 21.25), (rx, 18.1), label="yes", loff=(2.5, 0), fs=5.8)
    c.arrow((rx, 12.5), (rx, 6.6))
    c.path([(rx + 18, 63), (98.5, 63), (98.5, 25.5), (rx + 18, 25.5)], label="no: keep top-1", seg=1, loff=(-5.0, 20), fs=5.8, lha="center")
    c.path([(rx - 18, 37), (60, 37), (60, 25.5), (rx - 18, 25.5)], label="no: first candidate", seg=0, loff=(-1, 2.0), fs=5.8, lha="right")
    c.path([(rx + 6, 21.0), (rx + 24, 21.0), (rx + 24, 4.5), (rx + 18, 4.5)], label="no: label unchanged", seg=1, loff=(-6.5, 0), fs=5.8, lha="center")
    c.save(out)
