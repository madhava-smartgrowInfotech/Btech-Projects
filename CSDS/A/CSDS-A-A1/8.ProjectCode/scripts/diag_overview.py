"""System architecture, high-level workflow and DFD level 0 for PolicyLens (drawn from the real modules and routes)."""
from __future__ import annotations

import math

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 7.6)
    # users
    c.zone(2, 64, 100, 10.5, "User  (Chrome / Edge / phone browser)", fc="#f4f5fb")
    c.box(6, 65.5, 44, 5.6, "Policyholder - signs in, uploads a policy wording (PDF), asks questions,\nruns Claim Copilot, compares plans, switches English / Hindi / Telugu", fc="white", fs=7.2)
    c.box(54, 65.5, 44, 5.6, "Anyone - Model performance page (public evaluation figures, no login)", fc="white", fs=7.2)
    # frontend
    c.zone(2, 50, 100, 12.5, "Web app - React 18 + TypeScript + Vite   (port 5101, /api proxied to 8101)", fc="#eef4fe")
    fe = [("Pages and routing\nLanding, Dashboard, My policies,\nPolicy view, Ask, Claim Copilot,\nCompare, Performance, Settings", 6),
          ("Policy viewer and charts\nserver-rendered page images with\nhighlight boxes, Recharts", 37),
          ("Data layer\nTanStack Query + Axios,\nJWT bearer token, light/dark theme", 68)]
    for t, x in fe:
        c.box(x, 51.5, 30, 8, t, fc="white", fs=6.9)
    c.arrow((52, 64), (52, 62.5), both=True)
    # backend
    c.zone(2, 17, 100, 31, "Backend - FastAPI + Python 3.11   (port 8101)", fc="#eef8f2")
    c.box(6, 40.0, 92, 4.2, "REST API  /api:  auth - users - policies - conversations - claims - comparisons - dashboard - evaluation - health     (JWT, owner-only access, {detail, code} errors)",
          fc=INDIGO_L, ec=INDIGO, fs=7.0, bold=True)
    c.arrow((52, 50), (52, 44.2), label="HTTP / JSON", both=True, loff=(8, 0))
    svc = [("Ingestion\nworker\n(thread)", 6), ("PDF parser +\nsegmenter\nPyMuPDF", 18), ("Hybrid\nretriever\nBM25+dense\n+RRF+rerank", 30),
           ("Policy Card\nextractor +\nrisk engine", 42), ("Answerer\n(RAG)", 54), ("Claim Copilot\n+ eligibility\nrules", 66),
           ("Comparator\n+ Language\nservice", 78), ("Faithfulness\nscorer (NLI)", 90)]
    for t, x in svc:
        w = 11 if x < 90 else 8
        c.box(x, 27.5, w, 11.0, t, fc="white", fs=6.4)
        c.arrow((x + w / 2, 40.0), (x + w / 2, 38.5))
    c.box(6, 19, 74, 6.5, "Gemini client - JSON-schema output, model fallback chain, 10-minute cool-down for overloaded models,\nrequests-per-minute pacing, disk cache by content hash, per-call usage log", fc=AMBER_L, ec="#c9a45a", fs=7.0)
    for x in (11.5, 23.5, 35.5, 47.5, 59.5, 71.5, 83.5):
        c.line((x, 27.5), (x, 25.5), color="#9aa5ba", lw=0.8)
    c.box(84, 19, 14, 6.5, "Local CPU models\nMiniLM - cross-encoder\n- NLI DeBERTa", fc=GREEN_L, fs=6.6)
    c.arrow((94, 28), (92, 25.5))
    # storage + external
    c.zone(2, 1, 66, 14, "Storage  (data/)", fc="#fff8e8")
    c.box(5, 2.5, 20, 8.5, "SQLite app.db\n12 tables (SQLAlchemy 2)", fc="white", fs=6.8)
    c.box(27, 2.5, 18, 8.5, "ChromaDB\nclauses_minilm\n801 vectors, cosine", fc="white", fs=6.8)
    c.box(47, 2.5, 19, 8.5, "Files: uploaded PDFs,\npage images, AI response\ncache, models/hf", fc="white", fs=6.6)
    for x in (22, 36, 56):
        c.arrow((x, 17), (x, 11), both=True)
    c.box(72, 2.5, 28, 9, "Google Gemini API  (external)\nanswers, Policy Card, claim plan,\ncomparison, translation", fc=ROSE_L, ec="#c98a8a", fs=6.8)
    c.arrow((60, 19), (80, 11.5), label="HTTPS", loff=(0, 2))
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 5.8)
    steps = [("1  Upload", "policy wording PDF\n(or a sample policy)", BLUE_L),
             ("2  Parse", "lines, pages, columns;\nheaders removed;\nscans rejected", BLUE_L),
             ("3  Segment", "numbered clauses with\npage and highlight\nboxes", BLUE_L),
             ("4  Index", "BM25 + MiniLM\nvectors in ChromaDB", INDIGO_L),
             ("5  Policy Card", "one Gemini call; each\nvalue linked to its\nclause and verified", INDIGO_L)]
    steps2 = [("6  Risks", "rule + AI findings,\nde-duplicated, with\nseverity", GREEN_L),
              ("7  Ask", "hybrid retrieval, cited\nanswer, faithfulness\nscore", GREEN_L),
              ("8  Claim Copilot", "calculated pre-checks,\nverdict, checklist,\nsteps, estimate", AMBER_L),
              ("9  Compare", "two Policy Cards side\nby side, trade-offs", AMBER_L),
              ("10  Review", "dashboard, Model\nperformance, Hindi /\nTelugu answers", ROSE_L)]
    bw, bh, gap = 16.6, 14, 3.9
    xs = [3 + i * (bw + gap) for i in range(5)]
    row1 = [c.box(x, 33, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps)]
    row2 = [c.box(x, 10, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps2)]
    for b, (h, t, _) in zip(row1 + row2, steps + steps2):
        c.text(b["x"] + bw / 2, b["y"] + bh - 3.0, h, fs=8.2, bold=True)
        c.text(b["x"] + bw / 2, b["y"] + 5.4, t, fs=6.9)
    for r in (row1, row2):
        for a, b in zip(r[:-1], r[1:]):
            c.arrow(anchor(a, "r"), anchor(b, "l"))
    last, first = anchor(row1[-1], "b"), anchor(row2[0], "t")
    c.path([last, (last[0], 28.5), (first[0], 28.5), first])
    c.box(3, 51, 97.6, 4.6, "Steps 1-6 run once per policy in a background worker (status: queued, parsing, indexing, extracting, ready). Steps 7-10 run on demand.",
          fc=AMBER_L, ec="#c9a45a", fs=7.2, r=1.5)
    c.box(3, 2.2, 97.6, 4.6, "Answers come only from the uploaded wording. If the clauses do not cover the question, PolicyLens says \"Not covered in this policy\" instead of guessing.",
          fc=GREY_L, ec="#9aa5ba", fs=7.1, r=1.5)
    c.save(out)


CX, CY, A, B = 52, 29, 16, 20


def _edge_x(y, side):
    dx = A * math.sqrt(max(0.0, 1 - ((y - CY) / B) ** 2))
    return CX - dx if side == "l" else CX + dx


def dfd0(out):
    c = Canvas(10.4, 5.8)
    c.ellipse(CX, CY, 2 * A, 2 * B, "0\nPolicyLens\nhealth-insurance\nassistant", fc=INDIGO_L, ec=INDIGO, fs=9.5)
    c.box(1, 33, 17, 11, "Policyholder\n(user)", fc=BLUE_L, fs=8.5, bold=True)
    c.box(86, 33, 17, 11, "Google Gemini API\n(external LLM)", fc=ROSE_L, fs=8, bold=True)
    c.box(86, 8, 17, 9, "Insurer policy\nwording (PDF)", fc=AMBER_L, fs=8, bold=True)
    y1, y2 = 41, 36
    c.arrow((18, y1), (_edge_x(y1, "l"), y1))
    c.text(30, y1 + 4.2, "register, sign in, policy PDF,\nquestions, claim details,\ncomparison and language choice", fs=6.6)
    c.arrow((_edge_x(y2, "l"), y2), (18, y2), ls="--")
    c.text(30, y2 - 4.4, "Policy Card, risks, cited answers,\nfaithfulness scores, claim plan,\ncomparison, dashboard", fs=6.6)
    y1, y2 = 41, 36
    c.arrow((_edge_x(y1, "r"), y1), (86, y1))
    c.text(75, y1 + 4.2, "clauses + prompt\n(JSON schema)", fs=6.6)
    c.arrow((86, y2), (_edge_x(y2, "r"), y2), ls="--")
    c.text(75, y2 - 3.6, "structured JSON:\ncard, answer, plan", fs=6.6)
    c.arrow((86, 12.5), (_edge_x(12.5, "r"), 12.5))
    c.text(75, 17.2, "sample wordings\n(four insurers)", fs=6.6)
    c.text(52, 3.0, "Context diagram (level 0). Solid arrows: data in. Dashed arrows: data out.", fs=7.6, italic=True)
    c.save(out)
