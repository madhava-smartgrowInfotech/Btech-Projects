"""DFD level 1, DFD level 2 (review pipeline) and the flowchart of the core algorithm review_changes()."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas


def _store(c, x, y, w, h, text, fs=6.8):
    c.rect(x, y, w, h, fc="#fffdf2", ec="#44506b", lw=1.0)
    c.line((x + 4, y), (x + 4, y + h), lw=1.0)
    c.text(x + 4 + (w - 4) / 2, y + h / 2, text, fs=fs)


def dfd1(out):
    c = Canvas(10.4, 8.2)
    c.text(52, 80, "Level 1 - six processes and six data stores", fs=9, bold=True)
    c.box(2, 36, 15, 11, "Developer /\nreviewer", fc=GREY_L, fs=7.6, bold=True)
    c.box(82, 57, 18, 8, "GitHub\n(public API)", fc=GREY_L, fs=7.2, bold=True)
    c.box(82, 2, 18, 9, "Anthropic API\n(optional)", fc=GREY_L, fs=7.0, bold=True)
    P = {"1": (32, 70, "1.0\nAuthenticate"), "2": (32, 53, "2.0\nIngest change\nset"), "6": (32, 15, "6.0\nModel Lab"),
         "3": (58, 53, "3.0\nRun 7-agent\nreview"), "4": (58, 35, "4.0\nExport and\nhistory"), "5": (58, 15, "5.0\nCodebase\nassistant")}
    for k, (x, y, t) in P.items():
        c.ellipse(x, y, 17, 12, t, fc=INDIGO_L, ec=INDIGO, fs=6.9)
    _store(c, 72, 67, 26, 6, "D1  users (app.db)")
    _store(c, 72, 50.5, 26, 6, "D5  job table (memory)")
    _store(c, 72, 32, 26, 6, "D2  reviews (history.db)")
    _store(c, 72, 21, 26, 6, "D6  repository indexes (mem.)")
    _store(c, 20, 26.5, 24, 5.5, "D3  model artefacts")
    _store(c, 74, 40.5, 24, 5.5, "D4  rule knowledge base")
    c.arrow((13, 48), (23.5, 66), label="email, password", fs=6.2, loff=(-5, 4))
    c.arrow((40.5, 70), (72, 70), both=True, label="user record / new account", fs=6.2, loff=(0, 1.8))
    c.arrow((17, 43), (23.5, 51), label="diff / PR URL\n/ files", fs=6.2, loff=(-1, 5))
    c.arrow((82, 60), (40.5, 56.5), both=True, ls="--", label="PR URL, token  /  diff, repo zip", fs=6.2, loff=(6, 2.4))
    c.arrow((40.5, 53), (49.5, 53), label="changes", fs=6.2, loff=(0, 2))
    c.arrow((58, 47), (58, 41), label="review", fs=6.2, loff=(5, 0))
    c.arrow((66.5, 53), (72, 53.5), label="progress", fs=6.2, loff=(0, 3))
    c.arrow((66.5, 35), (72, 35), both=True, label="save / load", fs=6.2, loff=(-1, 2.5))
    c.arrow((49.5, 37), (17, 41), ls="--", label="verdict, findings,\nexports", fs=6.2, loff=(0, 4.5))
    c.arrow((17, 38), (24.5, 20), label="function code", fs=6.2, loff=(-6, -2))
    c.path([(9, 36), (9, 3.5), (58, 3.5), (58, 9)], label="repository source, question", fs=6.2, seg=1, loff=(0, 1.8))
    c.arrow((32, 21), (32, 26.5), both=True, label="load", fs=6.2, loff=(3, 0))
    c.arrow((66.5, 17), (72, 23.5), both=True, label="index", fs=6.2, loff=(-1, 3))
    c.arrow((64, 10), (82, 6), both=True, ls="--", label="text (if enabled)", fs=6.2, loff=(0, -2.6))
    c.arrow((74, 43), (60, 49), ls=":", head=True)
    c.text(36, 7.2, "3.0 also reads the model (D3) and the rules (D4)", fs=6.0, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(10.4, 6.6)
    c.text(52, 63.5, "Level 2 - process 3.0 'Run 7-agent review' expanded", fs=9, bold=True)
    c.box(1, 28, 14, 12, "From 2.0\nIngest:\nChangedFile list", fc=GREY_L, fs=7.2, bold=True)
    xs = [28, 44, 60, 76, 92]
    for x, n in zip(xs, ["3.1\nIngestion", "3.2\nStatic\nanalysis", "3.3\nML risk", "3.4\nSecurity\nreasoner", "3.5\nRemedi-\nation"]):
        c.ellipse(x, 34, 13, 11.5, n, fc=INDIGO_L, ec=INDIGO, fs=6.8)
    c.ellipse(44, 12, 13, 11.5, "3.6\nQuality\nreviewer", fc=INDIGO_L, ec=INDIGO, fs=6.8)
    c.ellipse(70, 12, 13, 11.5, "3.7\nJudge", fc=INDIGO_L, ec=INDIGO, fs=6.8)
    c.arrow((15, 34), (21.5, 34), label="files", fs=6.3, loff=(0, 2.2))
    for a, b, l in ((28, 44, "hunks,\nlines"), (44, 60, "findings,\nfunctions"), (60, 76, "p(vuln),\ntype"), (76, 92, "enriched\nfindings")):
        c.arrow((a + 6.5, 34), (b - 6.5, 34), label=l, fs=6.0, loff=(0, 5.4))
    c.rect(50, 51, 20, 5.5, fc="#fffdf2")
    c.text(60, 53.7, "D3 model artefacts", fs=6.6)
    c.arrow((60, 51), (60, 39.8), label="model", fs=6.2, loff=(-1, 0), lha="right")
    c.rect(72, 51, 27, 5.5, fc="#fffdf2")
    c.text(85.5, 53.7, "D4 rule knowledge base", fs=6.6)
    c.arrow((76, 51), (76, 39.8), label="CWE, OWASP,\nimpact text", fs=6.0, loff=(-8.5, 0))
    c.arrow((92, 51), (92, 39.8), label="fix templates", fs=6.0, loff=(-1, 0), lha="right")
    c.arrow((44, 28.2), (44, 17.8), label="quality\nissues", fs=6.0, loff=(6, 0))
    c.arrow((50.5, 12), (63.5, 12), label="quality list", fs=6.2, loff=(0, 2.4))
    c.path([(92, 28.2), (92, 12), (76.5, 12)], label="patched findings", fs=6.2, seg=0, loff=(-8.5, 0))
    c.box(84, 1.5, 17, 7.5, "To 4.0 Export and\nhistory: review\nrecord", fc=GREY_L, fs=6.6, bold=True)
    c.arrow((74.5, 8), (84, 5.2), label="score, verdict", fs=6.0, loff=(-1, -3))
    c.save(out)


def flowchart(out):
    c = Canvas(10.4, 8.6)
    L, M = 22, 62
    c.terminal(L, 82, 36, 5, "Start: review_changes(changed, options)", fs=6.8)
    c.arrow((L, 79.5), (L, 77))
    c.box(4, 70, 36, 7, "1. Ingestion Agent: count files, added / removed\nlines and languages", fc=BLUE_L, fs=6.8)
    c.arrow((L, 70), (L, 67))
    c.diamond(L, 62, 34, 10, "File has the full\nnew source?", fs=6.8)
    c.box(3, 44, 19, 8, "Analyse the whole\nfile; in_diff is set\nline by line", fc=BLUE_L, fs=6.3)
    c.box(24, 44, 19, 8, "Analyse each hunk,\npadded to its line\noffset", fc=BLUE_L, fs=6.3)
    c.path([(5, 62), (12.5, 62), (12.5, 52)], label="yes", fs=6.4, seg=0, loff=(0, 1.6))
    c.path([(39, 62), (33.5, 62), (33.5, 52)], label="no", fs=6.4, seg=0, loff=(0, 1.6))
    c.box(4, 31, 36, 8, "2. Static Analysis Agent: AST + taint rules (Python),\nregex rules (JS / PHP / Java), quality checks", fc=BLUE_L, fs=6.6)
    c.path([(12.5, 44), (12.5, 41.5), (18, 41.5), (18, 39)])
    c.path([(33.5, 44), (33.5, 41.5), (26, 41.5), (26, 39)])
    c.arrow((L, 31), (L, 28.5))
    c.diamond(L, 24, 30, 9, "ML agent enabled?", fs=6.8)
    c.box(4, 6, 36, 8, "3. ML Risk Agent: 14 metrics per function\n-> probability, type, top drivers", fc=INDIGO_L, fs=6.6)
    c.arrow((L, 19.5), (L, 14), label="yes", fs=6.4, loff=(3, 0))
    c.line((37, 24), (44, 24))
    c.text(41, 25.8, "no", fs=6.4)
    c.path([(40, 10), (44, 10), (44, 80), (46, 80)])
    c.box(46, 76.5, 32, 7, "4. Security Reasoner: CWE / OWASP text,\nsource -> sink, ML corroboration", fc=INDIGO_L, fs=6.4)
    c.arrow((M, 76.5), (M, 71))
    c.box(46, 64, 32, 7, "5. Remediation: apply the fix, re-scan, keep\nthe patch only if the finding is gone", fc=GREEN_L, fs=6.4)
    c.arrow((M, 64), (M, 59))
    c.box(46, 52, 32, 7, "6-7. Quality summary; Judge de-duplicates\nby file, line and CWE", fc=GREEN_L, fs=6.4)
    c.arrow((M, 52), (M, 47))
    c.box(46, 38, 32, 9, "score = round(100 x (1 - exp(-W / 18)))\nW = sum(severity x confidence weight);\noutside the diff counts 15 %", fc=AMBER_L, fs=6.3)
    c.arrow((M, 38), (M, 36))
    c.diamond(M, 31, 32, 10, "in-diff high/critical\nsecurity finding\nor score >= 70 ?", fs=6.1)
    c.diamond(M, 17, 32, 10, "in-diff medium+\nfinding or\nscore >= 30 ?", fs=6.2)
    c.arrow((M, 26), (M, 22), label="no", fs=6.4, loff=(3, 0))
    c.terminal(91, 31, 16, 4.6, "BLOCK", fc=ROSE_L, fs=7)
    c.terminal(91, 17, 16, 4.6, "REQUEST_CHANGES", fc=AMBER_L, fs=5.8)
    c.arrow((78, 31), (83, 31), label="yes", fs=6.4, loff=(0, 1.8))
    c.arrow((78, 17), (83, 17), label="yes", fs=6.4, loff=(0, 1.8))
    c.terminal(M, 5, 18, 4.6, "APPROVE", fc=GREEN_L, fs=7)
    c.arrow((M, 12), (M, 7.3), label="no", fs=6.4, loff=(3, 0))
    c.box(80, 1, 22, 8, "Build the review record,\nPR comment summary;\nstore.save() to history.db", fc=GREY_L, fs=6.2)
    c.arrow((71, 5), (80, 5))
    c.path([(99, 31), (101.5, 31), (101.5, 10.5), (95, 10.5), (95, 9)])
    c.line((99, 17), (101.5, 17))
    c.save(out)
