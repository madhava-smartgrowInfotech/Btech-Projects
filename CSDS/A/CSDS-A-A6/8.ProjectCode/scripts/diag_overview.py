"""System architecture, high-level workflow and DFD level 0 for ClauseGuard (drawn from the real code)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 7.6)
    c.text(52, 74.5, "ClauseGuard - system architecture", fs=11, bold=True)
    # browser
    c.zone(1.5, 26, 24, 44, "Browser (React 19 + Vite)")
    for i, t in enumerate(["Landing, Sign up,\nLog in", "Upload", "My contracts,\nContract report", "Clause detail,\nClause graph", "Evaluation"]):
        c.box(3, 58 - i * 7.0, 21, 6, t, fc=BLUE_L, fs=6.4)
    c.text(13.5, 28.0, "axios + TanStack Query,\nJWT in localStorage", fs=6.0, italic=True)
    # api
    c.zone(32, 12, 40, 58, "FastAPI backend (port 8106)")
    c.box(34, 56.5, 36, 8, "Routers /api: auth (register, login)\ncontracts (upload, list, report, clause, graph)\neval (metrics)   +   /api/health", fc=INDIGO_L, ec=INDIGO, fs=6.4)
    c.box(34, 49, 36, 5.5, "auth.py: bcrypt hash/verify, JWT HS256 (1,440 min),\nownership check on every contract route", fc=AMBER_L, ec="#c9a45a", fs=6.2)
    c.box(34, 14, 36, 33.5, "", fc="white", ec=INDIGO, ls="--", lw=1.0)
    c.text(52, 45.2, "services/ - pipeline.process_upload()", fs=6.6, bold=True)
    sv = [("parsing\nPyMuPDF, python-docx", 34, 36.5), ("classification\ncentroids + tie-break", 52.5, 36.5),
          ("rules\n8 regex rules", 34, 28), ("graph\n3 combinations (NetworkX)", 52.5, 28),
          ("complexity\nFlesch, jargon, refs", 34, 19.5), ("explain\nreason, wording, summary", 52.5, 19.5)]
    for t, x, y in sv:
        c.box(x + 0.5, y, 16.5, 7, t, fc=GREEN_L, fs=6.0)
    c.box(34.5, 15, 16.5, 3.2, "vectorstore (NumPy cosine)", fc=GREY_L, fs=5.8)
    c.box(53, 15, 16.5, 3.2, "gemini_client (retries)", fc=GREY_L, fs=5.8)
    # storage
    c.zone(78, 36, 22, 34, "Storage (local)")
    c.box(79.5, 57, 19, 8, "SQLite data/app.db\nusers, contracts,\nclauses (+ embedding BLOB), flags", fc="#fff8e8", fs=6.0)
    c.box(79.5, 47, 19, 8, "data/cuad_centroids.npz\n20 centroids x 3,072-d\n(cached)", fc="#fff8e8", fs=6.0)
    c.box(79.5, 37.5, 19, 7.5, "experiments/eval/metrics.json\ndata/sample/*.json (CUAD\nsplits, 40-clause test set)", fc="#fff8e8", fs=5.8)
    # external
    c.zone(78, 8, 22, 24, "External")
    c.box(79.5, 10, 19, 17, "Google Gemini API\n- gemini-embedding-001\n  (3,072-d vectors)\n- text model (default\n  gemini-flash-latest):\n  tie-break, reasons,\n  safer wording, summary", fc=ROSE_L, ec="#c98a8a", fs=5.9)
    # arrows
    c.arrow((25.5, 55), (32, 55), both=True, label="HTTPS /api\n(Vite proxy)", lpos=0.5, loff=(0, 4.2), fs=5.8)
    c.arrow((70, 60.5), (78.8, 60.5), both=True, ls=":")
    c.arrow((70, 36), (79.5, 51), both=True, ls=":")
    c.arrow((70, 20), (79.5, 20), both=True, ls="--", label="HTTPS", loff=(0, 2.2), fs=5.8)
    c.arrow((70, 28), (79.5, 41), ls=":")
    c.text(52, 5.3, "Solid: browser-API; dotted: local reads/writes; dashed: outbound calls to Gemini (the only network dependency).", fs=6.3, italic=True)
    c.text(52, 2.5, "No GPU, no vector database, no graph database: vectors live in SQLite BLOBs, the clause graph is rebuilt per request.", fs=6.3, italic=True)
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 5.2)
    c.text(52, 49, "High-level workflow: one contract, from upload to report", fs=11, bold=True)
    steps = [("1", "Upload\nPDF / DOCX\n(JWT user)", BLUE_L), ("2", "Parse\nPDF per page,\nDOCX as page 1", BLUE_L), ("3", "Segment\nnumbered headings,\nelse paragraphs", BLUE_L),
             ("4", "Classify\nGemini embedding,\nnearest of 20\nCUAD centroids", INDIGO_L), ("5", "Detect\n8 Indian-law\nregex rules", INDIGO_L),
             ("6", "Explain each flag\nGemini: reason,\nprovision, safer\nwording", ROSE_L), ("7", "Combine\n3 risky\ncombinations", INDIGO_L),
             ("8", "Score\ncomplexity\nA-F", INDIGO_L), ("9", "Summarise\nGemini: plain\nsummary,\nobligations", ROSE_L), ("10", "Store + show\nreport, clauses,\ngraph", GREEN_L)]
    w, h = 18.0, 14.5
    xs = [2 + i * 20.0 for i in range(5)]
    for i, (n, t, fc) in enumerate(steps):
        row = i // 5
        col = i % 5 if row == 0 else 4 - (i % 5)
        x, y = xs[col], 28 if row == 0 else 6
        c.box(x, y, w, h, t, fc=fc, fs=6.6)
        c.ellipse(x + 2.2, y + h - 1.6, 4.2, 4.2, n, fc="white", ec="#44506b", fs=6.3)
    for i in range(4):
        c.arrow((xs[i] + w, 35.2), (xs[i + 1], 35.2))
    c.path([(xs[4] + w / 2, 28), (xs[4] + w / 2, 24.5), (xs[4] + w / 2, 20.5)], head=True)
    for i in range(5, 9):
        col_a, col_b = 4 - (i % 5), 4 - ((i + 1) % 5)
        c.arrow((xs[col_a], 13.2), (xs[col_b] + w, 13.2))
    c.text(52, 1.8, "Pink steps call Gemini; every other step is local code. Each flag and each clause keeps its page number so the report can point back to the source.", fs=6.4, italic=True)
    c.save(out)


def dfd0(out):
    c = Canvas(10.4, 5.6)
    c.text(52, 53, "DFD level 0 - context diagram", fs=11, bold=True)
    c.ellipse(52, 28, 26, 19, "0\nClauseGuard\ncontract analysis\nsystem", fc=INDIGO_L, ec=INDIGO, fs=8)
    c.box(2, 36, 20, 11, "Signatory\n(freelancer, individual,\nsmall business)", fc=BLUE_L, fs=7.0, bold=True)
    c.box(82, 36, 18, 11, "Google Gemini\nAPI", fc=ROSE_L, ec="#c98a8a", fs=7.4, bold=True)
    c.box(2, 6, 20, 10, "Evaluator\n(runs ml/eval.py)", fc=GREEN_L, fs=7.0, bold=True)
    c.box(82, 6, 18, 10, "CUAD v1 corpus\n(CC BY 4.0, JSON)", fc=AMBER_L, ec="#c9a45a", fs=7.0, bold=True)
    c.arrow((22, 44), (39.5, 33), label="credentials, contract file\n(PDF / DOCX)", loff=(-1, 5.3), fs=6.2)
    c.arrow((40, 24.5), (22, 38), label="complexity grade, flagged clauses,\nreasons, safer wording, graph", loff=(-3, -6.5), fs=6.2)
    c.arrow((64.5, 33), (82, 43), label="clause text for embedding,\nexplanation, summary prompts", loff=(3.5, 5.3), fs=6.2)
    c.arrow((82, 38.5), (64.8, 28.5), label="vectors, JSON text", loff=(5.5, -3.5), fs=6.2)
    c.arrow((22, 11), (41, 22), label="run evaluation", loff=(0, 3.6), fs=6.2)
    c.arrow((82, 11), (63, 21), label="labelled clause spans\n(train / held-out)", loff=(0, 5.0), fs=6.2)
    c.arrow((42, 21), (22, 8), label="metrics.json (precision, recall, top-k)", loff=(5, -3.5), fs=6.0)
    c.text(52, 1.6, "Data stores are inside the single process: users, contracts, clauses, flags (SQLite), centroid cache and metrics file.", fs=6.3, italic=True)
    c.save(out)
