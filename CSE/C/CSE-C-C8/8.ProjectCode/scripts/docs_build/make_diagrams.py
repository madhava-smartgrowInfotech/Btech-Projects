"""Draw the PeerScope design diagrams (first half) into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: app/main.py (routes), app/models.py (tables), app/services/*.py (pipeline) and
scripts/prepare_dataset.py + scripts/train_model.py (decision model).
    python scripts/docs_build/make_diagrams.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------------------------------
def system_architecture():
    fig, ax = canvas(10, 8.4, 100, 84)
    panel(ax, 2, 66, 96, 17, "Presentation tier - React + Vite web app (port 5408)", PALE_BLUE, BLUE)
    box(ax, 16, 72, 25, 10, "Pages\nLanding - Dashboard - Analyze\nReviewers - Model - History\nAbout - Analysis detail", BLUE, fs=7.6)
    box(ax, 41.5, 72, 22, 10, "lib/api.js\nfetch wrapper over /api\n(dev server proxies to 8408)", BLUE, fs=7.6)
    box(ax, 65, 72, 22, 10, "UI kit\nRecharts - Framer Motion\nGSAP - three.js hero", BLUE, fs=7.6)
    box(ax, 87, 72, 19, 10, "Original static UI\nstatic/index.html\nserved by API at /", GREY, fs=7.6)

    panel(ax, 2, 46, 96, 18, "Application tier - FastAPI + Uvicorn (port 8408, routes in app/main.py)", PALE_TEAL, TEAL)
    box(ax, 15, 52, 24, 10.5, "Health and model\nGET /api/health\nGET /api/model/metrics", TEAL, fs=7.6)
    box(ax, 40.5, 52, 24, 10.5, "Reviewer directory\nGET POST /api/reviewers\nPUT DELETE /{id}\nCSV import and export", TEAL, fs=7.6)
    box(ax, 66, 52, 24, 10.5, "Analysis\nPOST /api/analyze\nGET /api/analyses[/{id}]\n/export?format=json|pdf", TEAL, fs=7.6)
    box(ax, 88, 52, 17, 10.5, "Guards\nPDF only, 20 MB\n%PDF header\nCORS, error handler", TEAL, fs=7.3)

    panel(ax, 2, 21, 78, 23, "Service tier - app/services (orchestrated by pipeline.run_analysis)", PALE_ORANGE, ORANGE)
    row1 = [("pipeline", "run_analysis()"), ("pdf_extract", "PyMuPDF text,\nsections, refs"), ("features", "structural\nsignals 0-100"),
            ("ml_predict", "TF-IDF + LogReg\ndecision signal"), ("review_synthesis", "deterministic\n+ 3-step LLM")]
    row2 = [("llm_service", "Qwen2.5 1.5B/0.5B\nlazy, CPU"), ("embeddings", "MiniLM or\nTF-IDF fallback"), ("matching", "auditable score,\nconflict check"),
            ("export_service", "JSON and\nPDF report"), ("literature", "OpenAlex works,\nranked")]
    for i, (n, d) in enumerate(row1):
        box(ax, 9.8 + i * 15.1, 35, 14, 9.5, f"{n}\n{d}", ORANGE, fs=6.9)
    for i, (n, d) in enumerate(row2):
        box(ax, 9.8 + i * 15.1, 26.4, 14, 8, f"{n}\n{d}", ORANGE, fs=6.9)

    box(ax, 90, 33, 15, 11, "OpenAlex\npublic API\n(timeout 8 s,\nno key)", WHITE, tc=INK, ec=NAVY, fs=7.6, bold=True)

    panel(ax, 2, 1.5, 96, 18, "Data tier - local files and SQLite (nothing leaves the machine except the OpenAlex query)", LIGHT, "#B7C3D3")
    store(ax, 14, 8, 21, 9, "SQLite data/peerscope.db\nreviewers - analyses", fs=7.2)
    store(ax, 37, 8, 22, 9, "models/\ndecision_model.joblib\ntfidf_vectorizer.joblib\nmetrics.json", fs=6.9)
    store(ax, 60, 8, 21, 9, "data/processed_dataset.csv\n1,400 labelled rows\n(synthetic fallback)", fs=7.0)
    store(ax, 83, 8, 22, 9, "models/hf_cache\nQwen weights (and MiniLM\nwhen downloaded)", fs=7.0)

    arrow(ax, (50, 66), (50, 64), "HTTP + JSON, multipart PDF upload", lo=(21, 0), fs=7.4, color=NAVY)
    arrow(ax, (50, 46), (50, 44), "Python calls", lo=(9, 0), fs=7.4, color=NAVY)
    arrow(ax, (50, 22), (50, 19.5), "read / write", lo=(7, 0), fs=7.4, color=NAVY)
    arrow(ax, (77, 28), (82.4, 31), "GET", lo=(1.5, -2.5), fs=7, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 5.8, 100, 58)
    ax.text(50, 55.3, "One analysis request, end to end (POST /api/analyze)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    top = [("Upload PDF", "drag and drop,\nfilters set", BLUE), ("Validate", ".pdf, type, size\n<= 20 MB, %PDF", BLUE), ("Extract", "page text, title,\nsections, refs", TEAL),
           ("Features", "structure, evidence,\nmethod, presentation", TEAL), ("Decision signal", "TF-IDF + LogReg\naccept/border/reject", TEAL)]
    xs = [10 + i * 20 for i in range(5)]
    for x, (t, d, c) in zip(xs, top):
        box(ax, x, 43, 16.5, 12, f"{t}\n{d}", c, fs=8)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.4, 43), (b - 8.4, 43), color=NAVY)
    bot = [("Review", "local Qwen 3-step,\nelse deterministic", PURPLE), ("Literature", "OpenAlex works,\nsemantic rank", PURPLE), ("Reviewer match", "score 0-100,\nconflict penalty", PURPLE),
           ("Assemble + store", "assessment, top 5,\nrow in analyses", NAVY), ("Show / export", "dashboard tabs,\nJSON or PDF", ORANGE)]
    bx = [90 - i * 20 for i in range(5)]
    for x, (t, d, c) in zip(bx, bot):
        box(ax, x, 15, 16.5, 12, f"{t}\n{d}", c, fs=8)
    for a, b in zip(bx[:-1], bx[1:]):
        arrow(ax, (a - 8.4, 15), (b + 8.4, 15), color=NAVY)
    arrow(ax, (xs[-1], 37), (bx[0], 21), color=NAVY)
    ax.text(50, 30, "same extracted document and features feed every later stage", ha="center", fontsize=8, color=GREY, style="italic")
    ax.text(26, 5.2, "Local model cannot load: UI shows 'Unavailable',\nthe deterministic review stays visible", ha="center", fontsize=7.6, color=ORANGE)
    ax.text(74, 5.2, "OpenAlex fails: literature_retrieval_status\n= unavailable, rest of the result unaffected", ha="center", fontsize=7.6, color=ORANGE)
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(9, 5.6, 100, 62)
    circle(ax, 50, 31, 13, "0\nPeerScope\nsystem", BLUE, fs=11)
    box(ax, 11, 44, 18, 9, "Editor /\nprogramme chair", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    box(ax, 11, 14, 18, 9, "Directory\nadministrator", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    box(ax, 90, 31, 17, 9, "OpenAlex\nAPI", WHITE, tc=INK, ec=NAVY, fs=10, bold=True)
    arrow(ax, (20, 46), (38.5, 38), "paper PDF,\nfilters", lo=(-2, 5.5), fs=8)
    arrow(ax, (38.8, 33.5), (20, 41.5), "assessment, reviewer ranking,\nhistory, JSON / PDF export", lo=(-5, -6.5), fs=7.8)
    arrow(ax, (20, 15), (38.8, 25), "reviewer profiles,\nCSV file", lo=(-2, 5.5), fs=8)
    arrow(ax, (38.5, 22), (20, 12.5), "directory, CSV export", lo=(3, -3.6), fs=7.8)
    arrow(ax, (63, 34), (81.4, 34), "title / keyword\nquery", lo=(0, 4.4), fs=8)
    arrow(ax, (81.4, 28), (63, 28), "related works", lo=(0, -2.6), fs=8)
    ax.text(50, 8.5, "model metrics and confusion matrix are served from local files (models/metrics.json)", ha="center", fontsize=8, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


# --------------------------------------------------------------------------------------------------
def er_diagram():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(50, 63.5, "Two SQLite tables (no foreign key) and four file-based stores", ha="center", fontsize=10, color=NAVY, fontweight="bold")

    def entity(x, ytop, w, title, rows, fc=NAVY, fs=6.6, lh=2.75):
        h = 4.4 + lh * len(rows) + 1.0
        ax.add_patch(Rectangle((x, ytop - h), w, h, fc=WHITE, ec=NAVY, lw=1.4, zorder=2))
        ax.add_patch(Rectangle((x, ytop - 4.4), w, 4.4, fc=fc, ec=NAVY, lw=1.4, zorder=3))
        ax.text(x + w / 2, ytop - 2.2, title, ha="center", va="center", color=WHITE, fontsize=9.2, fontweight="bold", zorder=4)
        for i, r in enumerate(rows):
            ax.text(x + 1.0, ytop - 4.4 - 1.9 - lh * i, r, ha="left", va="center", fontsize=fs, zorder=4, family="DejaVu Sans Mono")
        return h

    def fmt(pairs):
        return [(("PK " if i == 0 else "   ") + n).ljust(25) + t for i, (n, t) in enumerate(pairs)]

    entity(3, 58, 38, "reviewers", fmt([("id", "Integer (index)"), ("display_name", "String(200) NOT NULL"), ("affiliation", "String(300)"), ("expertise_description", "Text"),
                                        ("research_topics", "Text (comma list)"), ("methods", "Text (comma list)"), ("keywords", "Text (comma list)"), ("publication_titles", "Text"),
                                        ("current_load", "Integer = 0"), ("maximum_load", "Integer = 5"), ("is_active", "Boolean = true"), ("conflict_terms", "Text (comma list)")]), BLUE)
    entity(59, 58, 38, "analyses", fmt([("id", "Integer (index)"), ("filename", "String(300)"), ("created_at", "DateTime (UTC now)"), ("overall_assessment", "String(120)"),
                                        ("concern_count", "Integer"), ("recommendation_count", "Integer"), ("top_reviewer", "String(200)"), ("status", "String(60) = 'completed'"),
                                        ("result_json", "Text (whole result)")]), TEAL)
    arrow(ax, (41, 40), (59, 40), None, style="-", color=ORANGE, ls="--", lw=1.6)
    ax.text(50, 42.6, "no foreign key", ha="center", fontsize=8, color=ORANGE, fontweight="bold")
    ax.text(50, 38.0, "top_reviewer = copy\nof a display_name;\nresult_json holds the\nranked-reviewer snapshot", ha="center", fontsize=6.8, color=INK, va="top")

    store(ax, 14, 7, 25, 10, "data/processed_dataset.csv\ntitle, text, label, source\n1,400 rows", fs=7.0)
    store(ax, 40, 7, 25, 10, "models/decision_model.joblib\nLogisticRegression", fs=7.0)
    store(ax, 66, 7, 25, 10, "models/tfidf_vectorizer.joblib\nCombinedVectorizer\n(word + char TF-IDF)", fs=7.0)
    store(ax, 90, 7, 18, 10, "models/\nmetrics.json", fs=7.2)
    ax.text(50, 15.5, "File artefacts written by scripts/prepare_dataset.py and scripts/train_model.py, read by app/services/ml_predict.py", ha="center", fontsize=7.8, color=NAVY)
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------------------------------------------
def training_pipeline():
    fig, ax = canvas(10, 6.2, 100, 62)
    ax.text(50, 59, "Decision-model pipeline (scripts/prepare_dataset.py, scripts/train_model.py, app/services/ml_predict.py)", ha="center", fontsize=9, color=NAVY, fontweight="bold")
    r1 = [("prepare_dataset.py", "1,400 rows;\nsynthetic fallback\n(PeerRead probe, 6 s)", BLUE), ("processed_dataset.csv", "title, text,\nlabel, source", TEAL), ("Clean + encode", "drop empty rows,\nLabelEncoder:\naccept, borderline, reject", TEAL),
          ("Stratified split", "80 / 20, seed 42\n1,120 train\n280 test", TEAL)]
    xs = [13, 38, 63, 88]
    for x, (t, d, c) in zip(xs, r1):
        box(ax, x, 45, 21, 13, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 10.7, 45), (b - 10.7, 45), color=NAVY)
    r2 = [("Word TF-IDF", "1-2 grams, 8,000\nfeatures, English\nstop words", PURPLE), ("Char TF-IDF", "char_wb 3-5 grams\n4,000 features", PURPLE), ("hstack", "up to 12,000\nsparse columns", PURPLE),
          ("LogisticRegression", "class_weight=balanced\nC=1.0, max_iter=1000\nseed 42", NAVY)]
    x2 = [88, 63, 38, 13]
    for x, (t, d, c) in zip(x2, r2):
        box(ax, x, 24, 21, 13, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(x2[:-1], x2[1:]):
        arrow(ax, (a - 10.7, 24), (b + 10.7, 24), color=NAVY)
    ax.plot([88, 88], [38.5, 30.5], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (88, 31), (88, 30.5), color=NAVY)
    ax.text(90.5, 34.5, "fit on train only", fontsize=7.4, color=GREY, ha="left")
    box(ax, 13, 5.5, 21, 7, "Evaluate on test: accuracy, macro P/R/F1,\nROC-AUC (OvR), confusion matrix", ORANGE, fs=6.8)
    box(ax, 50, 5.5, 33, 7, "Write models/decision_model.joblib,\ntfidf_vectorizer.joblib, metrics.json", ORANGE, fs=7.2)
    box(ax, 85, 5.5, 25, 7, "Serve: /api/model/metrics and\nml_predict.predict_decision()", NAVY, fs=7.0)
    arrow(ax, (13, 17.5), (13, 9.2), color=NAVY)
    arrow(ax, (23.6, 5.5), (33.4, 5.5), color=NAVY)
    arrow(ax, (66.6, 5.5), (72.4, 5.5), color=NAVY)
    ax.text(50, 12.3, "at request time: title + summary + first 4,000 characters of the paper -> transform -> predict_proba", ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "11_ml_training_pipeline.png")


# --------------------------------------------------------------------------------------------------
def pdf_extraction_flow():
    fig, ax = canvas(10, 6.8, 100, 68)
    ax.text(50, 65.5, "PDF extraction and structural scoring (pdf_extract.py, features.py, review_synthesis._overall)", ha="center", fontsize=9, color=NAVY, fontweight="bold")
    r1 = [("Upload checks", ".pdf name, type,\nnon-empty, <= 20 MB,\n%PDF header", BLUE), ("PyMuPDF", "get_text('text')\nfor each page", TEAL), ("Normalise", "collapse spaces,\nkeep one blank line", TEAL),
          ("full_text", "pages joined;\nword and sentence\ncounts", TEAL)]
    xs = [13, 38, 63, 88]
    for x, (t, d, c) in zip(xs, r1):
        box(ax, x, 54, 21, 12, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 10.7, 54), (b - 10.7, 54), color=NAVY)
    r2 = [("Title", "first line of first 25\nwith 12-220 chars\nnot ending '.'", PURPLE), ("Sections", "heading lines <= 80 chars\nmatched to 9 patterns", PURPLE),
          ("References", "after 'References';\nsplit on [n] or 'n. A';\nmax 60", PURPLE), ("Summary", "summary / intro text\n(900 chars) or first\nlong paragraph", PURPLE)]
    x2 = [88, 63, 38, 13]
    for x, (t, d, c) in zip(x2, r2):
        box(ax, x, 34, 21, 12, f"{t}\n{d}", c, fs=7.4)
    for a, b in zip(x2[:-1], x2[1:]):
        arrow(ax, (a - 10.7, 34), (b + 10.7, 34), color=NAVY)
    ax.plot([88, 88], [48, 40], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (88, 40.5), (88, 40), color=NAVY)
    ax.text(86.5, 44, "detect from full_text", fontsize=7.2, color=GREY, ha="right")
    box(ax, 13, 13, 22, 11, "Four signals (0-100)\nstructure = 100 x found / 9\nevidence = 22 x refs per page\n(+10 if results)", ORANGE, fs=6.8)
    box(ax, 40, 13, 25, 11, "method clarity: 100 / 70 / 45 / 25\npresentation: 100 / 75 / 50\n(sentence length, short sections)", ORANGE, fs=6.8)
    box(ax, 70, 13, 26, 11, "overall = 0.35 structure + 0.25 evidence\n+ 0.25 method + 0.15 presentation", NAVY, fs=7.0)
    box(ax, 92, 13, 14, 11, ">= 75 strong\n>= 55 moderate\nelse early-stage", NAVY, fs=6.8)
    arrow(ax, (13, 28), (13, 18.6), color=NAVY)
    arrow(ax, (25.1, 13), (27.4, 13), color=NAVY)
    arrow(ax, (52.6, 13), (56.9, 13), color=NAVY)
    arrow(ax, (83.1, 13), (84.9, 13), color=NAVY)
    save(fig, OUT / "12_pdf_extraction_flow.png")


if __name__ == "__main__":
    from diagrams_more import all_more

    system_architecture()
    high_level_workflow()
    dfd0()
    er_diagram()
    training_pipeline()
    pdf_extraction_flow()
    all_more()
