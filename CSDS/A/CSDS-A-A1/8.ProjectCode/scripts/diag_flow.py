"""DFD level 1 and 2 and the core-algorithm flowchart for PolicyLens."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def store(c, x, y, w, h, label, fc="#fff8e8"):
    """Open-ended rectangle: a data store (id | name)."""
    c.rect(x, y, w, h, fc=fc, ec="#44506b", lw=1.1)
    c.line((x + 5, y), (x + 5, y + h))
    parts = label.split(" ")
    c.text(x + 2.5, y + h / 2, parts[0], fs=7, bold=True)
    c.text(x + 5 + (w - 5) / 2, y + h / 2, " ".join(parts[1:]), fs=6.2)


def dfd1(out):
    c = Canvas(10.4, 7.6)
    c.box(6, 68, 62, 6, "Policyholder  (browser: credentials, policy PDF, questions, claim details, comparison and language choices)", fc=BLUE_L, fs=7.0, bold=True)
    c.box(78, 66, 24, 8.5, "Google Gemini API\n(external LLM)", fc=ROSE_L, fs=7.6, bold=True)
    cols = [18, 40, 62, 84]
    rowA, rowB = 56, 30
    pa = ["1.0\nAuthenticate\nuser", "2.0\nUpload, parse,\nsegment, index", "3.0\nExtract Policy\nCard + risks *", "4.0\nAnswer a\nquestion (RAG) *"]
    pb = ["5.0\nClaim\nCopilot *", "6.0\nCompare\nplans *", "7.0\nTranslate\n(en / hi / te) *", "8.0\nDashboard + model\nperformance"]
    for x, t in zip(cols, pa):
        c.ellipse(x, rowA, 19.5, 11.5, t, fc=INDIGO_L, ec=INDIGO, fs=6.9)
    for x, t in zip(cols, pb):
        c.ellipse(x, rowB, 19.5, 11.5, t, fc=INDIGO_L, ec=INDIGO, fs=6.9)
    for x in cols[:3]:
        c.arrow((x, 68), (x, 61.8), both=True)
    c.arrow((73.0, 56), (74.3, 56))
    for gx, ex in [(5.4, 8.3), (29.0, 30.3), (51.0, 52.3), (73.0, 74.3)]:
        c.path([(gx, 68), (gx, rowB), (ex, rowB)], head=True)
    c.text(52, 64.6, "requests and responses", fs=6.4, italic=True)
    c.arrow((70, 66), (64.5, 61.5), ls="--", both=True)
    c.arrow((86, 66), (86, 61.8), ls="--", both=True)
    sA = [("D1 users", 18), ("D2 documents, clauses, vector index", 40), ("D4 policy_cards + risk_flags", 62), ("D5 conversations, messages", 84)]
    for t, x in sA:
        store(c, x - 10, 38.5, 20, 5.6, t)
        c.arrow((x, 50.3), (x, 44.1), both=True, ls=":")
    sB = [("D6 claim_cases", 18), ("D7 comparisons", 40), ("D8 translations", 62), ("D9 evaluation runs", 84)]
    for t, x in sB:
        store(c, x - 10, 10, 20, 5.6, t)
        c.arrow((x, 24.2), (x, 15.6), both=True, ls=":")
    c.text(52, 5.2, "* also exchanges structured JSON with the Gemini API.   3.0, 5.0 and 6.0 read D2 and D4; 4.0 reads D2 and the vector index; 8.0 reads D5, D6 and D7.", fs=6.2, italic=True)
    c.text(52, 1.8, "DFD level 1 - eight processes, nine data stores.  Solid: external flows.  Dotted: reads and writes of data stores.  Dashed: external model.", fs=6.4, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(10.4, 6.6)
    c.box(1, 42, 11, 10, "Policyholder", fc=BLUE_L, fs=7.6, bold=True)
    xs = [24, 45, 66, 87]
    r1, r2 = 47, 24
    row1 = ["4.1\nDetect script,\ntranslate query", "4.2\nSearch BM25 +\ndense (30 each)", "4.3\nFuse (RRF) and\nre-rank (CE)", "4.4\nAbstention\ncheck"]
    row2 = ["4.5\nAdd rule/table\ncontext, call LLM", "4.6\nKeep only\nretrieved citations", "4.7\nScore faithful-\nness (NLI)", "4.8\nStore message,\nreturn answer"]
    for x, t in zip(xs, row1):
        c.ellipse(x, r1, 18, 11.5, t, fc=INDIGO_L, ec=INDIGO, fs=6.6)
    for x, t in zip(xs[::-1], row2):
        c.ellipse(x, r2, 18, 11.5, t, fc=INDIGO_L, ec=INDIGO, fs=6.6)
    c.arrow((12, 47), (15, 47))
    c.text(13.5, 51.2, "question,\nlanguage", fs=6)
    for a, b in zip(xs[:-1], xs[1:]):
        c.arrow((a + 9, r1), (b - 9, r1))
    c.text(55.5, r1 + 2.2, "top-30 lists", fs=6, italic=True)
    c.text(76.5, r1 + 2.2, "top-7", fs=6, italic=True)
    c.arrow((87, 41.2), (87, 29.8), label="no: clauses found", loff=(-0.5, 0), fs=6.2)
    for a, b in zip(xs[::-1][:-1], xs[::-1][1:]):
        c.arrow((a - 9, r2), (b + 9, r2))
    c.text(76, r2 - 3.0, "clauses + prompt", fs=6, italic=True)
    c.box(70, 60, 32, 6, "yes: \"Not covered in this policy\" without an LLM call\n(re-rank < 0.004 AND best BM25 < 9.0)", fc=AMBER_L, ec="#c9a45a", fs=6.4)
    c.arrow((92, 53), (92, 60), ls=":")
    c.path([(15, r2), (6.5, r2), (6.5, 41.8)], ls="--")
    c.text(11.5, 20.0, "answer,\ncitations,\nscore", fs=6)
    c.box(70, 3, 32, 7, "Gemini API (external)\nclauses + JSON schema  ->  answer JSON", fc=ROSE_L, ec="#c98a8a", fs=6.8)
    c.arrow((87, 18.2), (87, 10), ls="--", both=True)
    store(c, 31, 59, 18, 5, "D2 clauses")
    store(c, 51, 59, 18, 5, "D3 vector index")
    c.arrow((40, 59), (44, 53), ls=":")
    c.arrow((58, 59), (48, 53), ls=":")
    store(c, 4, 4, 22, 5, "D5 messages")
    c.arrow((24, 18.2), (15, 9.1), ls=":")
    c.save(out)


def flowchart(out):
    c = Canvas(10.4, 8.4)
    cx = 38
    c.terminal(cx, 80, 26, 4.4, "Start: question + answer language")
    c.box(cx - 17, 70, 34, 5.4, "Script is Hindi / Telugu?\nYes: translate to an English search query (Flash-Lite, cached)", fc=BLUE_L, fs=7)
    c.box(cx - 17, 60.5, 34, 5.4, "BM25 top 30  +  dense (MiniLM) top 30\nper query (original + translation + short follow-up)", fc=BLUE_L, fs=7)
    c.box(cx - 17, 51, 34, 5.4, "Reciprocal Rank Fusion  score = sum 1 / (60 + rank)\npool = fused top 20 + each retriever's top 8", fc=INDIGO_L, fs=7)
    c.box(cx - 17, 41.5, 34, 5.4, "Cross-encoder re-rank (ms-marco-MiniLM)\nkeep top 7 clauses", fc=INDIGO_L, fs=7)
    c.diamond(cx, 31.5, 36, 9.5, "re-rank < 0.004\nAND best BM25 < 9.0 ?", fs=7.2)
    c.box(66, 28, 34, 7, "Return \"Not covered in this policy\"\n(no LLM call, ~1 s)", fc=AMBER_L, ec="#c9a45a", fs=7)
    c.terminal(83, 21, 26, 4.4, "End (status not_in_policy)", fc=ROSE_L, fs=7)
    c.box(cx - 17, 17.5, 34, 6, "Add the rule a retrieved table belongs to (and the\ntables a rule governs), up to 4 extra clauses", fc=GREEN_L, fs=7)
    c.box(cx - 17, 8.5, 34, 6, "Gemini (JSON schema): status, answer, answer_en,\nclaims[] with clause tags, follow-ups", fc=GREEN_L, fs=7)
    c.box(66, 8.5, 34, 6, "Drop tags of clauses that were not retrieved;\nbuild citations (clause, page, quote, boxes)", fc=GREEN_L, fs=7)
    c.box(66, 0.8, 34, 6, "NLI entailment of each claim vs windows of its\ncited clauses; number check; mean -> score 0-100", fc=GREEN_L, fs=6.8)
    c.terminal(cx, 3.8, 26, 4.4, "Store message, return answer", fc=GREEN_L, fs=7.5)
    c.arrow((cx, 77.8), (cx, 75.4))
    c.arrow((cx, 70), (cx, 65.9))
    c.arrow((cx, 60.5), (cx, 56.4))
    c.arrow((cx, 51), (cx, 46.9))
    c.arrow((cx, 41.5), (cx, 36.3))
    c.arrow((cx + 18, 31.5), (66, 31.5), label="yes", loff=(0, 2))
    c.arrow((83, 28), (83, 23.2))
    c.arrow((cx, 26.7), (cx, 23.5), label="no", loff=(3, 0))
    c.arrow((cx, 17.5), (cx, 14.5))
    c.arrow((cx + 17, 11.5), (66, 11.5))
    c.arrow((83, 8.5), (83, 6.8))
    c.arrow((66, 3.8), (cx + 13, 3.8))
    c.text(2, 78, "Algorithm 1: answer_question()", fs=8.5, bold=True, ha="left")
    c.save(out)
