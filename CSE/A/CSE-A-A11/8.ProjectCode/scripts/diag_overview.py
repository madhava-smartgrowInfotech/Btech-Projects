"""System architecture, high-level workflow and DFD level 0 for AutoSecAI (drawn from the real modules and routes)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 7.8)
    c.zone(2, 65, 100, 12, "Users  (any modern browser)", fc="#f4f5fb")
    c.box(6, 66.3, 44, 5.4, "Developer / reviewer - signs in (or uses the demo account), starts a PR review, reads\nfindings, exports reports, asks questions about a repository, tries the Model Lab", fc="white", fs=7.0)
    c.box(54, 66.3, 44, 5.4, "Visitor - landing page: real model statistics and one live example finding\n(no sign-in needed)", fc="white", fs=7.0)

    c.zone(2, 51.5, 100, 12.5, "Web app - React 19 + TypeScript + Vite 8 + Tailwind 4   (port 5311, /api proxied to 8311)", fc="#eef4fe")
    for t, x in [("Pages (lazy routes)\nLanding, Login, Overview, New review,\nReview result, Codebase, Model Lab,\nHistory, Settings, About", 5),
                 ("Data layer\nTanStack Query + axios, JWT in\nlocal storage, job polling hook,\nsettings kept in the browser", 37),
                 ("Interface kit (Aurora Glass)\ndark mode, reduced motion, charts\n(recharts), Markdown, code blocks", 69)]:
        c.box(x, 52.8, 30, 8.2, t, fc="white", fs=6.8)
    c.arrow((52, 65), (52, 64), both=True)

    c.zone(2, 17, 100, 33, "Backend - FastAPI + Python 3.11   (port 8311)", fc="#eef8f2")
    c.box(5, 41.5, 52, 4.4, "REST API /api : auth - meta - samples - reviews - jobs - exports - codebase - lab", fc=INDIGO_L, ec=INDIGO, fs=7.0, bold=True)
    c.box(60, 41.5, 19, 4.4, "auth.py  bcrypt + JWT\nusers in SQLite", fc="white", fs=6.6)
    c.box(81, 41.5, 19, 4.4, "Job runner (threads)\nlive agent messages", fc="white", fs=6.6)
    c.arrow((31, 51.5), (31, 45.9), both=True, label="HTTP / JSON", loff=(7, 0))
    svc = [("diffutil.py\ndiff / zip /\nGitHub input", 5), ("rules.py\nAST + taint\nengine, 30\nsecurity rules", 18),
           ("metrics.py\nmlmodel.py\n14 metrics,\nXGBoost model", 31), ("agents.py\n7 agents:\nreasoner,\nremediation,\njudge", 44),
           ("knowledge.py\n43 rule\nentries: CWE,\nOWASP, fixes", 57), ("codeintel.py\nTF-IDF + concept\n+ call graph\nretrieval", 70),
           ("report.py\nstore.py\nMD, SARIF,\nJSON, CSV", 83)]
    for t, x in svc:
        c.box(x, 27.5, 12.5, 11.5, t, fc="white", fs=6.2)
        c.arrow((x + 6.25, 41.5), (x + 6.25, 39))
    c.box(5, 19.5, 70, 5.5, "Optional LLM layer (llm.py): rewrites explanations and repository answers when an Anthropic key is supplied; off by default,\nnothing leaves the machine otherwise", fc=AMBER_L, ec="#c9a45a", fs=6.6)
    c.box(78, 19.5, 22, 5.5, "scikit-learn / XGBoost\nSMOTE-Tomek, 9 models", fc=GREEN_L, fs=6.6)
    for x in (11, 24, 37, 50, 63, 76, 89):
        c.line((x, 27.5), (x, 25), color="#9aa5ba", lw=0.8)

    c.zone(2, 1, 64, 15, "Storage (data/ and autosecai/artifacts/)", fc="#fff8e8")
    c.box(5, 2.5, 18, 9, "app.db (SQLite)\ntable users", fc="white", fs=6.8)
    c.box(25, 2.5, 19, 9, "history.db (SQLite)\ntable reviews\n(JSON payload)", fc="white", fs=6.8)
    c.box(46, 2.5, 17, 9, "bundle.joblib,\nreport.json,\ndataset csv", fc="white", fs=6.6)
    for x in (14, 34, 54):
        c.arrow((x, 17), (x, 11.5), both=True)
    c.box(69, 2.5, 30, 10.5, "External services (optional)\nGitHub REST: PR diff, repo zip\nAnthropic API: explanation text", fc=ROSE_L, ec="#c98a8a", fs=6.8)
    c.arrow((72, 19.5), (78, 13.2), label="HTTPS", loff=(5, 0))
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 5.4)
    row1 = [("1  Sign in", "JWT session or\nthe demo account", BLUE_L), ("2  Choose input", "demo, pasted diff, two\nversions, GitHub PR,\nfiles / zip / folder", BLUE_L),
            ("3  Ingestion Agent", "files, hunks, changed\nlines, languages", INDIGO_L), ("4  Static Analysis", "AST + taint rules,\nquality checks", INDIGO_L),
            ("5  ML Risk Agent", "14 metrics per function\n-> probability, type", INDIGO_L)]
    row2 = [("6  Security Reasoner", "CWE / OWASP, impact,\nsource -> sink flow", GREEN_L), ("7  Remediation", "safe patch, re-scanned\nto verify the fix", GREEN_L),
            ("8  Quality Reviewer", "complexity, nesting,\nsize, dead imports", GREEN_L), ("9  Judge Agent", "de-duplicate, risk\nscore, verdict", AMBER_L),
            ("10  Review", "findings, charts, exports,\nhistory, delete", AMBER_L)]
    w, h, gap = 16.6, 13, 3.4
    xs = [3 + i * (w + gap) for i in range(5)]
    for r, (row, y) in enumerate(((row1, 33), (row2, 12))):
        for i, (t, s, col) in enumerate(row):
            c.box(xs[i], y, w, h, "", fc=col)
            c.text(xs[i] + w / 2, y + h - 3.2, t, fs=8, bold=True)
            c.text(xs[i] + w / 2, y + 4.6, s, fs=7)
        for i in range(4):
            c.arrow((xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2))
    c.path([(xs[4] + w / 2, 33), (xs[4] + w / 2, 28), (xs[0] + w / 2, 28), (xs[0] + w / 2, 25)], label="agents run in a background job; the UI polls and shows each agent's message", fs=7, seg=1, loff=(0, 2.2))
    c.box(3, 1.2, 98, 6.2, "Side path - Codebase assistant: index a repository (demo shop, this project, zip, folder, GitHub) -> TF-IDF + concept + call-graph retrieval -> cited answer,\nrepository map and onboarding guide.   Side path - Model Lab: the base-paper pipeline, charts and a 'try it' scorer.", fc=GREY_L, fs=7)
    c.text(52, 49.5, "Every finding is explained and, where possible, patched and verified; nothing is merged or posted automatically.", fs=8, italic=True)
    c.save(out)


def dfd0(out):
    c = Canvas(10.4, 5.6)
    c.text(52, 53, "Context diagram - the system boundary", fs=9, bold=True)
    c.ellipse(52, 27, 34, 22, "0.0\nAutoSecAI\nPR analysis and\ncodebase intelligence", fc=INDIGO_L, ec=INDIGO, fs=9)
    c.box(2, 31, 18, 10, "Developer /\nreviewer", fc=GREY_L, fs=7.6, bold=True)
    c.box(2, 3, 18, 10, "Local files\n(diff, zip, folder)", fc=GREY_L, fs=7.2, bold=True)
    c.box(84, 38, 18, 10, "GitHub\n(public API)", fc=GREY_L, fs=7.6, bold=True)
    c.box(84, 4, 18, 10, "Anthropic API\n(optional)", fc=GREY_L, fs=7.2, bold=True)
    c.arrow((20, 38), (35.5, 32), label="credentials, PR URL, diff,\nquestions, settings", fs=6.2, loff=(-2, 4.5))
    c.arrow((36, 25), (20, 33), label="verdict, findings, patches,\ncharts, exports, answers", fs=6.2, loff=(2, -5.5))
    c.arrow((20, 8), (40, 20), label="source files", fs=6.2, loff=(-3, -3))
    c.arrow((66, 36), (84, 45), label="PR URL, token", fs=6.2, loff=(-6, 3.5))
    c.arrow((88, 38), (70, 29.5), label="diff, repo zip", fs=6.2, loff=(7, -1))
    c.arrow((68, 20), (84, 11), label="findings / code\n(only if enabled)", fs=6.2, loff=(-2, 4.5))
    c.arrow((88, 4), (66, 15), label="explanation text", fs=6.2, loff=(6, -3))
    c.save(out)
