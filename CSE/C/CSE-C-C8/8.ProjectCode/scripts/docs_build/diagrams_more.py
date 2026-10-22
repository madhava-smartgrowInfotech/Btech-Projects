"""Second half of the PeerScope diagram set (DFD 1/2, UML class, sequence, use case, matching flowchart)."""

from __future__ import annotations

from pathlib import Path

from dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def duo(ax, p1, p2, l1=None, l2=None, off=1.2, fs=7.0, side1=1, lo1=None, lo2=None):
    """Two parallel arrows between p1 and p2 (p1->p2 labelled l1, p2->p1 labelled l2)."""
    import math

    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * off, dx / n * off
    a1, b1 = (p1[0] + ox, p1[1] + oy), (p2[0] + ox, p2[1] + oy)
    a2, b2 = (p2[0] - ox, p2[1] - oy), (p1[0] - ox, p1[1] - oy)
    arrow(ax, a1, b1, l1, fs=fs, lo=lo1 if lo1 is not None else (ox * 4.5, oy * 4.5))
    arrow(ax, a2, b2, l2, fs=fs, color=BLUE, lo=lo2 if lo2 is not None else (-ox * 4.5, -oy * 4.5))


def dfd1():
    fig, ax = canvas(10, 10, 100, 100)
    R = 7.4
    box(ax, 8, 56, 14, 8, "Editor /\nchair", WHITE, tc=INK, ec=NAVY, fs=8.6, bold=True)
    box(ax, 93.5, 76, 12, 8, "OpenAlex\nAPI", WHITE, tc=INK, ec=NAVY, fs=8, bold=True)
    box(ax, 93.5, 18, 12, 8, "Directory\nadmin", WHITE, tc=INK, ec=NAVY, fs=7.8, bold=True)
    circle(ax, 28, 76, R, "1.0\nValidate and\nextract paper", BLUE, fs=7.0)
    circle(ax, 52, 76, R, "2.0\nAssess paper", BLUE, fs=7.8)
    circle(ax, 76, 76, R, "3.0\nRetrieve\nliterature", BLUE, fs=7.6)
    circle(ax, 28, 46, R, "6.0\nStore, show\nand export", BLUE, fs=7.4)
    circle(ax, 52, 46, R, "4.0\nMatch\nreviewers", BLUE, fs=7.6)
    circle(ax, 76, 18, R, "5.0\nManage\ndirectory", BLUE, fs=7.6)
    circle(ax, 8, 90, 6.8, "7.0\nReport model\nperformance", BLUE, fs=6.4)
    store(ax, 36, 94, 22, 6, "D3  Model files, metrics", fs=7.2)
    store(ax, 52, 18, 22, 6.4, "D1  reviewers table", fs=7.4)
    store(ax, 28, 18, 18, 6.4, "D2  analyses table", fs=7.4)

    duo(ax, (13, 60.5), (22.3, 70.5), None, None, off=1.0)
    ax.text(16.6, 57.6, "PDF, filters", fontsize=7.0, ha="left")
    ax.text(16.6, 55.4, "validation errors", fontsize=7.0, ha="left", color=BLUE)
    arrow(ax, (35.4, 76), (44.6, 76), "text, sections,\nreferences", lo=(0, 4.4), fs=7.0)
    arrow(ax, (59.4, 76), (68.6, 76), "title, keywords,\ntopics", lo=(0, 4.4), fs=7.0)
    duo(ax, (83.4, 76), (87.5, 76), "query", "works", off=1.1, fs=6.6, lo1=(0, 2.6), lo2=(0, -2.6))
    arrow(ax, (46, 91), (50, 83.4), "model,\nvectorizer", lo=(6.6, 0), fs=7.0)
    arrow(ax, (25, 94), (15, 91.5), "metrics, labels, CM", lo=(0, 3.6), fs=6.6)
    arrow(ax, (8, 83.2), (8, 60.2), None)
    ax.text(9.6, 72, "metrics,\nconfusion\nmatrix", fontsize=6.8, ha="left", va="center")
    arrow(ax, (52, 68.6), (52, 53.4), None)
    ax.text(53.5, 56, "keywords, methods,\ntopics, summary", fontsize=7.0, ha="left", va="center")
    arrow(ax, (46.5, 70.6), (33, 52), None)
    ax.text(29.5, 62.5, "assessment, review,\ndecision signal", fontsize=7.0, ha="center", va="center")
    arrow(ax, (72, 70), (34, 50.6), None)
    ax.text(66, 63.2, "related works", fontsize=7.0, ha="left", va="center")
    arrow(ax, (44.6, 46), (35.4, 46), "ranked reviewers", lo=(0, 2.4), fs=7.0)
    arrow(ax, (52, 21.5), (52, 38.6), "reviewer\nprofiles", lo=(6, 0), fs=7.0)
    duo(ax, (28, 38.6), (28, 21.4), None, None, off=1.2)
    ax.text(25.2, 30, "analysis\nrecord", fontsize=6.8, ha="right", va="center")
    ax.text(30.8, 30, "stored\nanalyses", fontsize=6.8, ha="left", va="center")
    duo(ax, (13.6, 52), (21.6, 41.6), None, None, off=1.0)
    ax.text(6.5, 45.5, "history /\nexport request", fontsize=6.6, ha="center", va="center")
    ax.text(10, 38.5, "results, history,\nexports", fontsize=6.6, ha="center", va="center", color=BLUE)
    duo(ax, (63, 18), (68.6, 18), "records", "records", off=1.1, fs=6.6, lo1=(0, 3.6), lo2=(0, -3.4))
    duo(ax, (83.4, 18), (87.5, 18), "data, CSV", "directory,\nCSV", off=1.1, fs=6.4, lo1=(0, 5.2), lo2=(0, -5.0))
    ax.text(50, 4.5, "Process 6.0 also serves history lookup (GET /api/analyses) and the JSON / PDF export", ha="center", fontsize=7.6, color=GREY, style="italic")
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 6.4, 100, 64)
    R = 6.2
    ax.text(50, 61.5, "Level 2 - expansion of processes 1.0 to 4.0 (pipeline.run_analysis)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    xs = [14, 38, 62, 86]
    top = ["1.1\nExtract\npage text", "1.2\nTitle, sections,\nreferences", "2.1\nStructural\nfeatures", "2.2\nDecision\nsignal"]
    for x, t in zip(xs, top):
        circle(ax, x, 48, R, t, BLUE, fs=6.9)
    flows = ["page text", "doc: title,\nsummary, text", "doc,\nfeatures"]
    for a, b, f in zip(xs[:-1], xs[1:], flows):
        arrow(ax, (a + R, 48), (b - R, 48), f, fs=6.9, lo=(0, 4.6))
    bot = ["4.2\nScore, rank\nreviewers", "4.1\nProfiles and\nembeddings", "3.1\nRetrieve\nliterature", "2.3\nDraft review"]
    bx = [14, 38, 62, 86]
    for x, t in zip(bx, bot):
        circle(ax, x, 22, R, t, BLUE, fs=6.9)
    arrow(ax, (86, 41.8), (86, 28.2), "doc, features,\nsignal", lo=(-8.3, 0), fs=6.9)
    arrow(ax, (86 - R, 22), (62 + R, 22), "review, title,\nkeywords", fs=6.9, lo=(0, 4.6))
    arrow(ax, (62 - R, 22), (38 + R, 22), "related works,\nprofile text", fs=6.9, lo=(0, 4.6))
    arrow(ax, (38 - R, 22), (14 + R, 22), "paper profile,\nvectors", fs=6.9, lo=(0, 4.6))

    store(ax, 86, 59, 20, 4.8, "D3  Model files", fs=7.2)
    arrow(ax, (86, 56.4), (86, 54.2), "weights", lo=(5.5, 0), fs=6.8)
    store(ax, 91, 5.5, 14, 6, "D4  Qwen\nweights", fs=7.0)
    arrow(ax, (89, 8.6), (88, 15.8), "prompts", lo=(-4.2, 0), fs=6.8)
    box(ax, 62, 5.5, 16, 6, "OpenAlex API", WHITE, tc=INK, ec=NAVY, fs=7.6, bold=True)
    arrow(ax, (60.6, 8.6), (60.6, 15.8), "query", lo=(-3.2, 0), fs=6.8)
    arrow(ax, (63.8, 15.8), (63.8, 8.6), "works", lo=(3.2, 0), fs=6.8)
    store(ax, 30, 5.5, 20, 6, "D1  reviewers table", fs=7.2)
    arrow(ax, (28, 8.8), (36, 15.9), "profiles", lo=(-3.6, 0), fs=6.8)
    arrow(ax, (24, 8.8), (17.5, 15.9), None)
    box(ax, 7, 5.5, 12, 6, "to 6.0\nresult dict", NAVY, fs=7.2)
    arrow(ax, (10, 8.8), (11, 15.8), "ranked", lo=(-3.2, 0), fs=6.8)
    ax.text(50, 36.2, "each stage adds its output to one result dictionary (assessment, signal, review, literature, ranking)", ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "05_dfd_level2.png")


def class_diagram():
    fig, ax = canvas(10, 11.8, 100, 118)
    W = 23.5
    cx = [1.5, 26.5, 51.5, 76.5]
    fs = 6.6

    def rel(p1, p2, label=None, ls="-", lo=(0, 1.2), style="-|>"):
        arrow(ax, p1, p2, label, color=NAVY, lw=1.2, style=style, ls=ls, fs=6.8, lo=lo)

    yA, yB, yC, yD = 112, 70, 46, 20
    a = uml_class(ax, cx[0], yA, W, "FastAPI app", [], ["health()", "model_metrics()", "list/create/update/delete_reviewer()", "import_reviewers()", "export_reviewers()", "analyze(file, filters)", "list_analyses()", "get_analysis(aid)", "export_analysis(aid, fmt)"], fs=fs, stereotype="main.py")
    b = uml_class(ax, cx[1], yA, W, "Reviewer", ["id: int  <<PK>>", "display_name: str", "affiliation: str", "expertise_description", "research_topics", "methods", "keywords", "publication_titles", "current_load: int", "maximum_load: int", "is_active: bool", "conflict_terms"], [], hdr=BLUE, fs=fs, stereotype="ORM table reviewers")
    c = uml_class(ax, cx[2], yA, W, "ReviewerIn", ["display_name  (1..200)", "affiliation  (<=300)", "expertise_description", "research_topics", "methods, keywords", "publication_titles", "current_load  (0..100)", "maximum_load  (1..100)", "is_active: bool", "conflict_terms"], [], hdr=GREY, fs=fs, stereotype="Pydantic schema")
    d = uml_class(ax, cx[3], yA, W, "Analysis", ["id: int  <<PK>>", "filename: str", "created_at: datetime", "overall_assessment: str", "concern_count: int", "recommendation_count: int", "top_reviewer: str", "status: str", "result_json: text"], [], hdr=TEAL, fs=fs, stereotype="ORM table analyses")

    e = uml_class(ax, cx[0], yB, W, "Pipeline", [], ["run_analysis(pdf, name, rev, opts)"], hdr=ORANGE, fs=fs, stereotype="pipeline.py")
    f = uml_class(ax, cx[1], yB, W, "PdfExtractor", ["SECTION_PATTERNS"], ["extract_pdf(path)", "_normalize(text)", "_detect_sections(text)", "_extract_references(text)", "_build_summary(text, secs)"], hdr=ORANGE, fs=fs, stereotype="pdf_extract.py")
    g = uml_class(ax, cx[2], yB, W, "FeatureExtractor", ["EXPECTED (9 sections)", "METHOD_TERMS", "TOPIC_HINTS", "STOP"], ["extract_features(doc)", "_tokens(text)"], hdr=ORANGE, fs=fs, stereotype="features.py")
    h = uml_class(ax, cx[3], yB, W, "MLPredictor", ["_model: LogisticRegression", "_vectorizer"], ["artifacts_exist()", "predict_decision(title, ...)", "load_metrics()"], hdr=ORANGE, fs=fs, stereotype="ml_predict.py")

    i = uml_class(ax, cx[0], yC, W, "ReviewSynthesis", [], ["deterministic_review(doc, f)", "llm_review(doc, feats)", "review_quality(review)", "_overall(feats)"], hdr=PURPLE, fs=fs, stereotype="review_synthesis.py")
    j = uml_class(ax, cx[1], yC, W, "LLMService", ["_pipe, _pipe_model", "_pipe_error", "PRIMARY: Qwen2.5-1.5B", "FALLBACK: Qwen2.5-0.5B"], ["ensure_llm()", "generate(prompt, n)", "llm_status()"], hdr=PURPLE, fs=fs, stereotype="llm_service.py")
    k = uml_class(ax, cx[2], yC, W, "LiteratureService", ["OPENALEX url"], ["retrieve_literature(...)", "score_literature(q, works)"], hdr=PURPLE, fs=fs, stereotype="literature.py")
    l = uml_class(ax, cx[3], yC, W, "MatchingService", ["MATCH_WEIGHTS (config)"], ["paper_profile(...)", "reviewer_profile(r)", "detect_conflict(text, r)", "match_reviewers(...)", "_overlap(a, b)", "_explain(...)"], hdr=PURPLE, fs=fs, stereotype="matching.py")

    m = uml_class(ax, cx[0], yD, W, "ExportService", [], ["analysis_to_json(result)", "analysis_to_pdf(result)"], hdr=GREY, fs=fs, stereotype="export_service.py")
    n = uml_class(ax, cx[1], yD, W, "SeedData", ["DEMO_REVIEWERS (6)"], ["seed_if_empty(db)"], hdr=GREY, fs=fs, stereotype="seed.py")
    o = uml_class(ax, cx[3], yD, W, "EmbeddingService", ["_model (MiniLM-L6-v2)", "_FALLBACK_VEC (TF-IDF 512)"], ["embed_texts(texts)", "cosine(a, b)", "embedding_status()"], hdr=PURPLE, fs=fs, stereotype="embeddings.py")

    mid0 = cx[0] + W / 2
    # FastAPI -> Pipeline, Reviewer, Analysis
    rel((mid0, yA - a[3]), (mid0, yB), "calls", lo=(3.2, 0))
    rel((cx[0] + W - 0.3, 108.3), (cx[1] + 0.3, 108.3), None)
    rel((cx[2] + 0.3, 108.3), (cx[1] + W - 0.3, 108.3), None)
    ax.plot([cx[0] + 17, cx[0] + 17, cx[3] + 12], [yA, 115, 115], color=NAVY, lw=1.2)
    rel((cx[3] + 12, 115), (cx[3] + 12, yA), None)
    ax.text(cx[2], 116.2, "stores each result in analyses", fontsize=6.8, ha="center", color=INK)
    # Pipeline bus 1 to the row-B services
    ax.plot([mid0, cx[3] + W / 2], [74.2, 74.2], color=NAVY, lw=1.2)
    for x in (cx[1], cx[2], cx[3]):
        rel((x + W / 2, 74.2), (x + W / 2, yB), None)
    ax.text(cx[1] + W / 2 + 1.2, 75.2, "uses", fontsize=6.8, color=INK)
    # Pipeline bus 2 to row C
    rel((mid0, yB - e[3]), (mid0, yC), "calls", lo=(3.2, 0))
    ax.plot([mid0, cx[3] + W / 2], [48.2, 48.2], color=NAVY, lw=1.2)
    for x in (cx[2], cx[3]):
        rel((x + W / 2, 48.2), (x + W / 2, yC), None)
    ax.text(cx[1] + W / 2 + 1.2, 49.2, "uses", fontsize=6.8, color=INK)
    # services
    rel((cx[0] + W, yC - 3.0), (cx[1], yC - 3.0), "optional", lo=(0, 1.3))
    rel((cx[3] + W / 2, yC - l[3]), (cx[3] + W / 2, yD), "embeds", lo=(3.5, 0), ls="--")
    rel((cx[2] + W / 2, yC - k[3]), (cx[3] + 2, yD - 3), "embeds", lo=(-4.2, 1.0), ls="--")
    ax.text(cx[2] + 0.5, 17.0, "FastAPI app -> Reviewer: CRUD;", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[2] + 0.5, 14.2, "ReviewerIn validates reviewer input;", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[2] + 0.5, 11.4, "FastAPI app also uses ExportService", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[2] + 0.5, 8.6, "and SeedData (start-up seeding).", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[2] + 0.5, 5.8, "Dashed: dependency on embeddings;", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[2] + 0.5, 3.0, "solid: calls or uses.", fontsize=6.8, color=GREY, ha="left")
    save(fig, OUT / "06_uml_class.png")


def sequence_diagram():
    fig, ax = canvas(10, 11.8, 100, 118)
    names = ["Browser\n(React)", "FastAPI\nmain.py", "pipeline", "pdf_extract\n+ features", "ml_predict", "review_\nsynthesis\n+ llm", "literature\n(OpenAlex)", "matching\n+ embeddings", "SQLite"]
    xs = [5.5, 17.5, 29.5, 41.5, 53.5, 65.5, 76.5, 87.5, 96]
    top = 114
    for x, n in zip(xs, names):
        box(ax, x, top, 10.2 if x < 95 else 8, 6.8, n, NAVY, fs=6.8, bold=True)
        ax.plot([x, x], [top - 3.4, 1], color="#9AA7B8", lw=1.0, ls="--", zorder=1)
    y = [top - 9]

    def msg(i, j, text, ret=False, gap=4.5, left=None):
        arrow(ax, (xs[i], y[0]), (xs[j], y[0]), None, color=(GREY if ret else BLUE), ls="--" if ret else "-", lw=1.3)
        lo, hi = sorted((xs[i], xs[j]))
        ax.text(left if left is not None else (lo + hi) / 2, y[0] + 1.0, text, ha="left" if left is not None else "center", fontsize=6.9, va="bottom", color=INK,
                bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.9))
        y[0] -= gap

    def self_call(i, text, gap=5.6):
        yy = y[0]
        sgn = -1 if xs[i] > 50 else 1
        ax.plot([xs[i], xs[i] + sgn * 2.6, xs[i] + sgn * 2.6, xs[i]], [yy + 0.8, yy + 0.8, yy - 2.0, yy - 2.0], color=BLUE, lw=1.2, zorder=4)
        arrow(ax, (xs[i] + sgn * 2.6, yy - 2.0), (xs[i], yy - 2.0), None, color=BLUE, lw=1.2)
        ax.text(xs[i] + sgn * 3.6, yy - 0.6, text, fontsize=6.9, ha="left" if sgn > 0 else "right", va="center", color=INK, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.9))
        y[0] -= gap

    msg(0, 1, "1  POST /api/analyze  (PDF, active_only, min_score, topic, method)", gap=5.0, left=1.0)
    self_call(1, "2  check .pdf, content type, non-empty, <= 20 MB, %PDF header; write temp file")
    msg(1, 8, "3  SELECT reviewers (400 if the directory is empty)")
    msg(8, 1, "4  reviewer rows", ret=True)
    msg(1, 2, "5  run_analysis(tmp.pdf, filename, reviewers, options)")
    msg(2, 3, "6  extract_pdf(); extract_features(doc)")
    msg(3, 2, "7  doc (title, sections, refs), feature signals", ret=True)
    msg(2, 4, "8  predict_decision(title, summary, text[:4000])")
    msg(4, 2, "9  label, confidence, probabilities", ret=True)
    msg(2, 5, "10  llm_review(doc, feats)")
    self_call(5, "11  deterministic_review(); if Qwen loads: analyze, critique, synthesize")
    msg(5, 2, "12  review + llm_status", ret=True)
    msg(2, 6, "13  retrieve_literature(title, keywords)")
    self_call(6, "14  GET api.openalex.org/works (timeout 8 s); rank by similarity")
    msg(6, 2, "15  works, or status 'unavailable'", ret=True)
    msg(2, 7, "16  match_reviewers(profile, reviewers, text[:4000])")
    self_call(7, "17  embed, cosine, overlaps, availability, conflict check, score 0-100")
    msg(7, 2, "18  ranked list with breakdown and explanation", ret=True)
    self_call(2, "19  apply filters; keep top 5; build result dict", gap=6.0)
    msg(2, 1, "20  result dict", ret=True)
    msg(1, 8, "21  INSERT analyses (result_json); delete temp file")
    msg(1, 0, "22  JSON result + analysis_id (warning if < 50 words)", ret=True, gap=5.0, left=7.0)
    save(fig, OUT / "07_sequence_analyze.png")


def use_case():
    fig, ax = canvas(10, 7.6, 100, 76)
    ax.add_patch(Rectangle((26, 0.2), 48, 74.6, fc="#FAFBFD", ec=NAVY, lw=1.6, zorder=0))
    ax.text(50, 72.6, "PeerScope web application", ha="center", fontsize=11, color=NAVY, fontweight="bold")
    names = ["UC1  Upload paper PDF\nand set filters", "UC2  View preliminary assessment\n(structure, decision signal)", "UC3  Read review\n(AI or deterministic)", "UC4  See related literature",
             "UC5  Get ranked reviewers\nwith audit breakdown", "UC6  Detect conflicts of interest", "UC7  Export analysis\n(JSON or PDF)", "UC8  Browse analysis history",
             "UC9  Manage reviewer directory", "UC10  Import / export reviewers (CSV)", "UC11  View model performance"]
    ys = [66, 60, 54, 48, 42, 36, 30, 24, 18, 12, 6]
    for t, y in zip(names, ys):
        ellipse(ax, 50, y, 40, 5.2, t, fs=7.2)

    def actor(x, y, name):
        ax.add_patch(Circle((x, y + 6.5), 1.6, fc="white", ec=NAVY, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 4.9, y + 1.0], color=NAVY, lw=1.6)
        ax.plot([x - 3, x + 3], [y + 3.8, y + 3.8], color=NAVY, lw=1.6)
        ax.plot([x, x - 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.plot([x, x + 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.text(x, y - 5.0, name, ha="center", fontsize=8.6, fontweight="bold", color=INK)

    actor(10, 44, "Editor /\nprogramme chair")
    actor(10, 9, "Directory\nadministrator")
    ax.add_patch(Rectangle((84, 38), 14, 8, fc=WHITE, ec=NAVY, lw=1.4, zorder=2))
    ax.text(91, 42, "OpenAlex API\n<<system>>", ha="center", va="center", fontsize=7.6, fontweight="bold", zorder=3)
    ax.add_patch(Rectangle((84, 52), 14, 8, fc=WHITE, ec=NAVY, lw=1.4, zorder=2))
    ax.text(91, 56, "Local Qwen model\n<<system>>", ha="center", va="center", fontsize=7.2, fontweight="bold", zorder=3)

    for idx in (0, 1, 2, 3, 4, 6, 7, 10):
        arrow(ax, (15, 50), (30, ys[idx]), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    for idx in (8, 9):
        arrow(ax, (15, 15), (30, ys[idx]), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (84, 42), (69, 48), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (84, 56), (69, 54), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (50, 39.4), (50, 38.6), None, color=GREY, lw=1.2, ls="--")
    ax.text(71.5, 39, "<<include>>", fontsize=6.8, color=GREY, style="italic")
    ax.text(50, 1.4, "UC2 to UC5 are results of UC1; UC5 includes UC6", ha="center", fontsize=7, color=GREY)
    save(fig, OUT / "08_use_case.png")


def flowchart():
    fig, ax = canvas(10, 11.0, 100, 110)
    cx, w, hh = 38, 60, 6.6
    ax.text(50, 107, "Reviewer-matching algorithm (matching.match_reviewers)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    steps = [
        (98, "paper_profile(): title + summary + keywords\n+ methodology terms + topics", BLUE),
        (89, "embed paper and every reviewer profile\n(all-MiniLM-L6-v2, else TF-IDF fallback; text cut to 2,000 chars)", BLUE),
        (80, "sim = max(0, cosine(paper vector, reviewer vector))", TEAL),
        (71, "keyword score = overlap(paper keywords,\nreviewer keywords + topics)  (exact + substring hits)", TEAL),
        (62, "method score = overlap(paper methods + topics,\nreviewer methods + topics)", TEAL),
        (53, "availability = clip(1 - current_load / maximum_load, 0, 1)", TEAL),
    ]
    for y, t, c in steps:
        box(ax, cx, y, w, hh, t, c, fs=7.4)
    for (y1, _, _), (y2, _, _) in zip(steps[:-1], steps[1:]):
        arrow(ax, (cx, y1 - hh / 2), (cx, y2 + hh / 2), color=NAVY)
    diamond(ax, cx, 42, 36, 10, "conflict of interest?", fs=8)
    arrow(ax, (cx, 53 - hh / 2), (cx, 47), color=NAVY)
    ax.text(77, 42, "tests (first 3,000 characters of text):\n- a reviewer conflict term appears\n- reviewer's full name appears\n- reviewer's affiliation appears", fontsize=6.8, ha="left", va="center", color=INK)
    box(ax, 12, 32.5, 17, 5, "no: penalty = 0", PALE_TEAL, tc=INK, ec=TEAL, fs=7.2)
    box(ax, 64, 32.5, 20, 5, "yes: penalty = 0.60", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.2)
    arrow(ax, (cx - 18, 42), (12, 35.2), None, color=NAVY)
    arrow(ax, (cx + 18, 42), (64, 35.2), None, color=NAVY)
    box(ax, cx, 24, w, hh, "final = 0.55 sim + 0.20 keyword + 0.15 method + 0.10 availability - penalty", NAVY, fs=7.4)
    arrow(ax, (12, 30), (22, 27.3), None, color=NAVY)
    arrow(ax, (64, 30), (54, 27.3), None, color=NAVY)
    box(ax, cx, 15, w, hh, "score = clip(100 x final, 0, 100); Strong >= 65, Good >= 45, Possible >= 25, else Weak\nexplanation text from the same terms", ORANGE, fs=7.2)
    arrow(ax, (cx, 24 - hh / 2), (cx, 15 + hh / 2), color=NAVY)
    box(ax, cx, 5.5, w, hh, "sort by score, assign rank; pipeline applies filters\n(active only, min score, topic, method); return top 5", NAVY, fs=7.4)
    arrow(ax, (cx, 15 - hh / 2), (cx, 5.5 + hh / 2), color=NAVY)
    ax.add_patch(Rectangle((4, 12), 68, 72.5, fc="none", ec=ORANGE, lw=1.3, ls="--", zorder=1))
    ax.text(73.5, 80, "loop: every reviewer\nin the directory", fontsize=7.4, color=ORANGE, fontweight="bold", va="center")
    ax.text(77, 24, "weights: config.MATCH_WEIGHTS\n(env-overridable, shown in\nevery audit table)", fontsize=6.8, ha="left", va="center", color=GREY)
    save(fig, OUT / "10_flowchart_matching.png")


def all_more():
    dfd1()
    dfd2()
    class_diagram()
    sequence_diagram()
    use_case()
    flowchart()
