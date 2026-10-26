"""
Draws every design diagram used in the LabLens project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does:
  backend/main.py (FastAPI routes + HMAC bearer token), report_processor.py (orchestrator),
  ocr_processor.py, ner_processor.py, result_analyzer.py, ai_insights.py, database.py / models.py (SQLite),
  and the React routes in frontend/src/App.jsx.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)

NAVY, INK, SLATE = "#1B2A41", "#0F172A", "#475569"
ORANGE, BLUE, GREEN, PURPLE, GOLD = "#EB6834", "#2A78D6", "#1BAF7A", "#6B52D6", "#E8A317"
PAPER, LINE, GREY = "#F6F8FB", "#9AA8BD", "#8A94A6"
plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(w, h, title=None, ty=99):
    """Work in a 100 x ty space; the figure is cropped to its content when saved."""
    top = ty + 2
    fig, ax = plt.subplots(figsize=(w, w * top / 100))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, top)
    ax.axis("off")
    ax.set_aspect("equal")
    if title:
        ax.text(1, ty, title, fontsize=13, fontweight="bold", color=NAVY, va="top")
    return fig, ax


def box(ax, x, y, w, h, text, fc=PAPER, ec=LINE, tc=INK, fs=9.5, bold=False, lw=1.3, rounding=1.2, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounding}", fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p, q, label=None, color=SLATE, lw=1.4, ls="-", fs=8, off=(0, 1.2), rad=0.0, head="-|>", lab_ha="center", lp=None):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=head, color=color, lw=lw, ls=ls,
                                                    connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if label:
        lx, ly = lp if lp else ((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1])
        ax.text(lx, ly, label, fontsize=fs, color=color, ha=lab_ha, va="center",
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(12, 8, "System architecture of LabLens", ty=80)
    tiers = ((1, 20, "Presentation tier"), (23, 23, "Application tier"), (49, 25, "Pipeline modules"), (77, 22, "Data tier"))
    for x, w, label in tiers:
        ax.add_patch(Rectangle((x, 12), w, 62, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 71.4, label, ha="center", fontsize=9.5, color=SLATE, fontweight="bold")
    box(ax, 3, 44, 16, 22, "React 18 SPA\nVite dev server\nport 5308\n\nLanding, Sign in,\nDashboard, Upload,\nAnalysis, Reports,\nTrends, Compare,\nInsights, About", fc="#E8F0FC", ec=BLUE, fs=7.6)
    box(ax, 3, 18, 16, 20, "Original Streamlit\napp (app.py)\nport 8501\n\nsame modules,\nsame SQLite file", fc="#FFF1EA", ec=ORANGE, fs=7.8)
    box(ax, 25, 44, 19, 22, "FastAPI service\nbackend/main.py\nport 8308\n\nHMAC bearer token\nCORS: port 5308 only\n15 MB upload limit\n14 JSON routes\nserves frontend/dist", fc="#E6F6EF", ec=GREEN, fs=7.8)
    box(ax, 25, 18, 19, 20, "report_processor.py\nprocess_uploaded_report()\n\norchestrates the six\nstages and records a\nstatus + error message\nfor each report", fc="#EFEBFC", ec=PURPLE, fs=7.8)
    box(ax, 51, 53, 21, 9.5, "ocr_processor.py\nvalidate, PDF text layer,\nOpenCV + Tesseract", fc=PAPER, ec=NAVY, fs=7.6)
    box(ax, 51, 41, 21, 9.5, "ner_processor.py\nregex row parser,\nTF-IDF name matcher", fc=PAPER, ec=NAVY, fs=7.6)
    box(ax, 51, 29, 21, 9.5, "result_analyzer.py\nLOW / NORMAL / HIGH /\nUNKNOWN", fc=PAPER, ec=NAVY, fs=7.6)
    box(ax, 51, 17, 21, 9.5, "ai_insights.py\nrule knowledge base,\noptional LLM rewrite", fc=PAPER, ec=NAVY, fs=7.6)
    box(ax, 79, 57, 18, 13, "database.py\nSQLAlchemy 2.0\nsession helpers,\ndashboard stats", fc=PAPER, ec=NAVY, fs=7.8)
    box(ax, 79, 35, 18, 15, "SQLite file\ndata/medical_lab.db\nreports\ntest_results\nhealth_insights", fc="#FFF8E5", ec=GOLD, fs=7.8)
    box(ax, 79, 16, 18, 13, "Tesseract OCR\n(external engine,\nscanned pages and\nimages only)", fc="white", ec=GREY, fs=7.4, ls="--")
    box(ax, 51, 3, 21, 7.5, "Anthropic API (optional)\nneeds ANTHROPIC_API_KEY", fc="white", ec=GREY, fs=7.4, ls="--")
    arrow(ax, (19, 55), (25, 55), "JSON,\nmultipart", color=BLUE, off=(0, 4.6), fs=7.2)
    arrow(ax, (19, 28), (25, 28), "direct\ncalls", color=ORANGE, off=(0, 4.0), fs=7.2)
    arrow(ax, (34.5, 44), (34.5, 38), "upload", off=(4.2, 0), fs=7.2, color=GREEN)
    for y0, y1 in ((36, 57.7), (31, 45.7), (26, 33.7), (21, 21.7)):
        arrow(ax, (44, y0), (51, y1), None, color=PURPLE, lw=1.2)
    arrow(ax, (44, 65), (79, 65), None, color=GREEN)
    ax.text(61.5, 67, "reads for GET routes", fontsize=7.2, color=GREEN, ha="center")
    ax.plot([34.5, 34.5, 75.5, 75.5], [18, 14.5, 14.5, 59], color=PURPLE, lw=1.4)
    arrow(ax, (75.5, 59), (79, 59), None, color=PURPLE)
    ax.text(35.5, 15.8, "create / save / update via database.py", fontsize=7.2, color=PURPLE, ha="left")
    arrow(ax, (88, 57), (88, 50), None)
    arrow(ax, (72, 56), (79, 27), None, color=GREY, ls="--", lw=1.1)
    ax.text(76.2, 36, "OCR", fontsize=7, color=GREY, ha="center")
    arrow(ax, (61.5, 17), (61.5, 10.5), "if use_llm", off=(5.5, 0), fs=7.2, color=GREY, ls="--")
    ax.text(1.5, 8.8, "Solid = implemented and exercised.  Dashed = optional, not\nexercised on the test machine (no Tesseract, no API key).",
            fontsize=7.8, color=SLATE, style="italic", va="center", linespacing=1.4)
    ax.text(1.5, 3.4, "Proposed in the abstract, not built: PP-OCR, CRF tagger,\nRAG retrieval, Supabase, serverless functions.",
            fontsize=7.6, color=GREY, va="center", linespacing=1.4, bbox=dict(fc="#F1F3F6", ec=GREY, pad=2.5, ls="--"))
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11.5, 5.8, "High-level workflow of one uploaded report", ty=58)
    steps = [
        ("1  Sign in", "demo account,\nbearer token\n(12 h)", NAVY),
        ("2  Upload", "PDF / JPG / PNG,\nup to 15 MB", BLUE),
        ("3  Extract text", "PDF text layer, or\nOpenCV + Tesseract\nfor scans", ORANGE),
        ("4  Parse rows", "name, value, unit,\nreference range,\nconfidence", PURPLE),
        ("5  Classify", "LOW / NORMAL /\nHIGH / UNKNOWN", GREEN),
        ("6  Explain", "rule-based text for\nLOW / HIGH rows,\noptional LLM rewrite", GOLD),
        ("7  Store", "reports, test_results,\nhealth_insights\n(SQLite)", NAVY),
        ("8  Review", "dashboard, analysis,\ntrends, compare,\ninsights", BLUE),
    ]
    bw, gap = 20.5, 5.0
    xs = [1.5 + (i % 4) * (bw + gap) for i in range(8)]
    for i, (t, s, c) in enumerate(steps):
        y = 34 if i < 4 else 14
        x = xs[i]
        box(ax, x, y, bw, 17, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((x, y + 12.2), bw, 4.8, fc=c, ec=c))
        ax.text(x + bw / 2, y + 14.6, t, ha="center", va="center", color="white", fontsize=9.8, fontweight="bold")
        ax.text(x + bw / 2, y + 5.8, s, ha="center", va="center", color=INK, fontsize=8.4, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (x + bw, y + 8), (x + bw + gap, y + 8))
    x4 = xs[3] + bw / 2
    ax.plot([x4, x4], [34, 29.5], color=SLATE, lw=1.4)
    ax.plot([x4, xs[4] + bw / 2], [29.5, 29.5], color=SLATE, lw=1.4)
    arrow(ax, (xs[4] + bw / 2, 29.5), (xs[4] + bw / 2, 31), None)
    ax.annotate("", xy=(xs[4] + bw / 2, 31.0), xytext=(xs[4] + bw / 2, 29.5), arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=1.4))
    ax.text(50, 8.4, "Stages 3 to 7 run inside one call: report_processor.process_uploaded_report().", ha="center", fontsize=8.2, color=SLATE, style="italic")
    ax.text(50, 4.2, "A failure at stage 3, 4, 5 or 7 marks the report Failed with a readable message; a failure at stage 6 keeps it Completed.",
            ha="center", fontsize=8.2, color=SLATE, style="italic")
    save(fig, "02_high_level_workflow.png")


# ---------------------------------------------------------------- DFD helpers
def process(ax, cx, cy, r, text, num, fs=8):
    ax.add_patch(Circle((cx, cy), r, fc="#E8F0FC", ec=BLUE, lw=1.6))
    ax.text(cx, cy + r * 0.52, num, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
    ax.text(cx, cy - r * 0.12, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)
    return (cx, cy, r)


def entity(ax, x, y, w, h, text, dashed=False):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF1EA", ec=ORANGE if not dashed else GREY, lw=1.8, ls="--" if dashed else "-"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, fontweight="bold", linespacing=1.2)
    return (x, y, w, h)


def store(ax, x, y, w, h, text, tag):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF8E5", ec="none"))
    ax.plot([x, x + w], [y + h, y + h], color=GOLD, lw=1.8)
    ax.plot([x, x + w], [y, y], color=GOLD, lw=1.8)
    ax.plot([x, x], [y, y + h], color=GOLD, lw=1.8)
    ax.text(x + 1.3, y + h / 2, tag, ha="left", va="center", fontsize=8.5, fontweight="bold", color=GOLD)
    ax.text(x + w / 2 + 2.5, y + h / 2, text, ha="center", va="center", fontsize=8.2, color=INK, linespacing=1.2)
    return (x, y, w, h)


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(11, 5.8, "Data flow diagram, level 0 (context)", ty=60)
    entity(ax, 2, 26, 17, 14, "User\n(signed-in\npatient)")
    process(ax, 50, 33, 15, "LabLens\nlab report\nanalysis", "0", fs=9.5)
    store(ax, 74, 38, 24, 9, "reports, test results,\ninsights (SQLite)", "D1")
    entity(ax, 76, 6, 22, 14, "Anthropic API\n(optional LLM)", dashed=True)
    arrow(ax, (19, 37), (35.3, 37), "credentials, lab report\n(PDF / JPG / PNG),\nview and delete requests", off=(0, 5.6), fs=7.6)
    arrow(ax, (35.3, 29), (19, 29), "extracted results, flags,\nexplanations, trends,\ncomparison, statistics", off=(0, -5.6), fs=7.6)
    arrow(ax, (63.5, 38.5), (74, 43), "rows to store", lp=(66.8, 45.4), fs=7.6)
    arrow(ax, (74, 41), (64.8, 35.6), "stored rows", lp=(72.6, 36.2), fs=7.6)
    arrow(ax, (57, 19.7), (76, 12), "test name + status\n(only if requested)", lp=(63, 10.2), fs=7.4, ls="--", color=GREY)
    arrow(ax, (84, 20), (62.5, 24.7), "reworded text", lp=(76.5, 24.6), fs=7.4, ls="--", color=GREY)
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11.5, 7.4, "Data flow diagram, level 1", ty=88)
    entity(ax, 1, 18, 12, 58, "User")
    procs = [(74, "1.0", "Authenticate"), (56, "2.0", "Process\nuploaded\nreport"), (38, "3.0", "Present results,\ntrends and\nstatistics"), (20, "4.0", "Delete report /\nload sample\nreports")]
    for y, n, t in procs:
        process(ax, 36, y, 7.8, t, n, fs=7.0)
    store(ax, 66, 14, 33, 52, "SQLite database\nreports\ntest_results\nhealth_insights", "D1")
    entity(ax, 70, 72, 28, 10, "Anthropic API (optional)", dashed=True)
    pairs = [
        (74, "email, password", "signed token (12 h)"),
        (56, "lab report file", "results + stage log"),
        (38, "view requests", "JSON results"),
        (20, "delete, load sample", "confirmation"),
    ]
    for y, a, b in pairs:
        arrow(ax, (13, y + 1.7), (28.2, y + 1.7), a, lp=(20.6, y + 4.4), fs=7.0)
        arrow(ax, (28.2, y - 1.7), (13, y - 1.7), b, lp=(20.6, y - 4.4), fs=7.0)
    arrow(ax, (43.8, 58), (66, 58), "report row, test rows,\ninsight rows, status", lp=(54.8, 53.4), fs=7.0)
    arrow(ax, (66, 38), (43.8, 38), "stored rows", lp=(54.8, 40.6), fs=7.0)
    arrow(ax, (43.8, 22), (66, 22), "cascade delete,\nsample rows", lp=(54.8, 26), fs=7.0)
    arrow(ax, (43.2, 59.8), (70, 74), "test name + status", lp=(52, 69.4), fs=7.0, ls="--", color=GREY)
    arrow(ax, (84, 72), (43.6, 55.2), "reworded text", lp=(61.5, 66.4), fs=7.0, ls="--", color=GREY, rad=0.0)
    ax.text(50, 3, "Authentication is stateless (HMAC-signed token), so 1.0 touches no data store.  Every process except 1.0 needs a valid token (HTTP 401 otherwise).",
            ha="center", fontsize=7.4, color=SLATE, style="italic")
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(11.5, 7.4, "Data flow diagram, level 2: process 2.0 expanded", ty=84)
    entity(ax, 1, 62, 12, 10, "User")
    store(ax, 1, 8, 10, 40, "reports", "D1")
    process(ax, 29, 62, 8.4, "Validate\nfile", "2.1", fs=7.8)
    process(ax, 55, 62, 8.4, "Extract\ntext", "2.2", fs=7.8)
    process(ax, 81, 62, 8.4, "Parse\ntest rows", "2.3", fs=7.8)
    process(ax, 81, 34, 8.4, "Classify\nvs. range", "2.4", fs=7.8)
    process(ax, 55, 34, 8.4, "Store\nresults", "2.5", fs=7.8)
    process(ax, 29, 34, 8.4, "Generate\ninsights,\nset status", "2.6", fs=7.2)
    store(ax, 40, 6, 28, 9, "test_results", "D2")
    store(ax, 72, 6, 27, 9, "health_insights", "D3")
    box(ax, 44, 74, 22, 7, "Tesseract (scans only)", fc="white", ec=GREY, fs=7.4, ls="--")
    arrow(ax, (13, 67), (20.8, 65), "file", lp=(16.6, 70.0), fs=7.4)
    arrow(ax, (37.4, 62), (46.6, 62), "valid bytes", lp=(42, 65.2), fs=7.4)
    arrow(ax, (63.4, 62), (72.6, 62), "raw text", lp=(68, 65.2), fs=7.4)
    arrow(ax, (81, 53.6), (81, 42.4), "name, value, unit,\nrange, confidence", lp=(91.2, 48), fs=7.2)
    arrow(ax, (72.6, 34), (63.4, 34), "status added", lp=(68, 37.4), fs=7.4)
    arrow(ax, (46.6, 34), (37.4, 34), "row ids", lp=(42, 37.4), fs=7.4)
    arrow(ax, (55, 53.6), (55, 66.0), None, color=GREY, ls="--", lw=1.1, head="<|-|>")
    ax.annotate("", xy=(55, 74), xytext=(55, 70.4), arrowprops=dict(arrowstyle="<|-|>", color=GREY, lw=1.1, ls="--"))
    ax.text(60.5, 72.0, "page images /\ntext", fontsize=6.8, color=GREY, va="center")
    arrow(ax, (55, 25.6), (55, 15), "result rows", lp=(60.2, 20.4), fs=7.2)
    arrow(ax, (33, 26.4), (72, 14.8), "insight rows", lp=(42.5, 26.8), fs=7.2, rad=0.0)
    arrow(ax, (20.6, 34), (11, 34), "status\nCompleted", lp=(15.8, 38.2), fs=7.0, color=SLATE)
    arrow(ax, (22, 55.4), (9, 48), "rejected / unreadable:\nFailed + message", lp=(21.5, 47.2), fs=7.0, color=ORANGE)
    ax.text(50, 0.4, "2.1: extension, non-empty, <= 15 MB.   2.2: PDF text layer (>= 30 characters per page) or 300 dpi render + OpenCV + Tesseract.   "
                     "2.3: regex + TF-IDF name match.   2.6: LOW / HIGH rows only; optional LLM rewrite.",
            ha="center", fontsize=6.6, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML class
def uml_class(ax, x, y, w, name, attrs, methods, stereo=None, color=BLUE, fs=7.0):
    lh = 2.05
    h = 4.8 + lh * (len(attrs) + len(methods)) + (1.2 if attrs and methods else 0.4)
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.6))
    ax.add_patch(Rectangle((x, y - 4.8), w, 4.8, fc=color, ec=color))
    if stereo:
        ax.text(x + w / 2, y - 1.2, f"<<{stereo}>>", ha="center", va="center", color="white", fontsize=6.4)
        ax.text(x + w / 2, y - 3.3, name, ha="center", va="center", color="white", fontsize=8.2, fontweight="bold")
    else:
        ax.text(x + w / 2, y - 2.4, name, ha="center", va="center", color="white", fontsize=8.2, fontweight="bold")
    cy = y - 4.8 - 1.2
    for a in attrs:
        ax.text(x + 0.8, cy, a, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    if attrs and methods:
        ax.plot([x, x + w], [cy + 0.3, cy + 0.3], color=color, lw=0.8)
        cy -= 0.9
    for m in methods:
        ax.text(x + 0.8, cy, m, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    return (x, y - h, w, h)


def class_diagram():
    fig, ax = canvas(12.6, 9.4, "UML class diagram (modules drawn as classes; the pipeline code is function-oriented)", ty=116)
    W = 22.5
    X = [1, 26.5, 52, 77.5]
    top = 110
    api = uml_class(ax, X[0], top, W, "FastAPI app", ["-SECRET : bytes", "-TOKEN_TTL = 12 h", "-MAX_UPLOAD_MB = 15"],
                    ["+login(LoginBody)", "+upload_report(file, use_llm)", "+report_detail(id)", "+delete_report(id)", "+trends(test) / compare(a, b)",
                     "+insights() / dashboard()", "+seed_demo()", "+require_user(Authorization)"], "module backend.main", GREEN)
    rp = uml_class(ax, X[1], top, W, "report_processor", [], ["+process_uploaded_report(", "   filename, bytes, use_llm)"], "module", PURPLE)
    pr = uml_class(ax, X[1], rp[1] - 5, W, "ProcessingResult", ["+report_id : int", "+raw_text : str", "+classified_results", "+stages_completed : list", "+error, status : str"], [],
                   "class", PURPLE)
    ocr = uml_class(ax, X[2], top, W, "ocr_processor", ["+MIN_TEXT_LAYER_CHARS = 30"],
                    ["+validate_file(name, bytes)", "+extract_text(name, bytes)", "+preprocess_image_for_ocr()", "+_deskew(image)"], "module", NAVY)
    ner = uml_class(ax, X[2], ocr[1] - 5, W, "ner_processor", ["+FUZZY_MATCH_THRESHOLD = 0.55"],
                    ["+extract_structured_tests(text)", "+normalize_test_name(raw)", "+extract_test_date(text)", "+_deduplicate(rows)"], "module", NAVY)
    ana = uml_class(ax, X[2], ner[1] - 5, W, "result_analyzer", [], ["+classify_result(v, low, high)", "+analyze_results(rows)", "+summarize_statuses(rows)"], "module", NAVY)
    ai = uml_class(ax, X[2], ana[1] - 5, W, "ai_insights", ["+TEST_KNOWLEDGE : dict[17]"],
                   ["+generate_insight(name,", "    status, use_llm)", "+generate_rule_based_insight()", "-_call_llm_for_insight()"], "module", NAVY)
    oe = uml_class(ax, X[3], top, W, "OCRError", [], [], "exception", SLATE)
    cr = uml_class(ax, X[3], ner[1] - 5, W, "ClassifiedResult", ["+test_name : str", "+result_value : float", "+status : str", "+confidence_score : float"], ["+as_dict()"], "dataclass", GREEN)
    it = uml_class(ax, X[3], cr[1] - 3, W, "InsightText", ["+explanation : str", "+possible_causes : str", "+recommendations : str", "+disclaimer : str"], [],
                   "dataclass HealthInsight", GREEN)
    db = uml_class(ax, X[0], api[1] - 5, W, "database", ["+engine, SessionLocal"],
                   ["+init_db() / get_session()", "+create_report()", "+update_report_status()", "+save_test_results()", "+save_health_insight()", "+get_results_for_report()", "+get_dashboard_stats()", "+delete_report(id)"],
                   "module", NAVY)
    base = min(db[1], ai[1], cr[1], pr[1], it[1]) - 9
    rep = uml_class(ax, X[0], base, W, "Report", ["+id : int  (PK)", "+file_name, file_type", "+upload_date : DateTime", "+processing_status", "+error_message, raw_text"], [], "ORM table reports", GOLD)
    tr = uml_class(ax, 32, base, 29, "TestResult", ["+id : int  (PK)", "+report_id : int  (FK)", "+test_name : str", "+result_value : float", "+unit : str", "+reference_low / high : float", "+status : str", "+test_date, confidence_score"], [],
                   "ORM table test_results", GOLD)
    hi = uml_class(ax, 68, base, 31, "HealthInsight (ORM)", ["+id : int  (PK)", "+test_result_id : int  (FK)", "+explanation : Text", "+possible_causes : Text", "+recommendations : Text", "+created_at : DateTime"], [],
                   "ORM table health_insights", GOLD)

    def link(p, q, label=None, ls="-", lp=None, color=SLATE, fs=6.8):
        arrow(ax, p, q, label, color=color, lw=1.1, ls=ls, fs=fs, lp=lp)

    link((X[0] + W, top - 6), (X[1], top - 6), "calls", lp=(25, top - 3.4))
    bus_x = 50.6
    ax.plot([X[1] + W, bus_x, bus_x], [top - 6, top - 6, ai[1] + ai[3] - 6.5], color=PURPLE, lw=1.2)
    for b, n in ((ocr, "1"), (ner, "2"), (ana, "3"), (ai, "5")):
        y = b[1] + b[3] - 6.5
        link((bus_x, y), (X[2], y), None, color=PURPLE)
        ax.text(bus_x - 1.6, y + 1.4, n, fontsize=7, color=PURPLE, fontweight="bold")
    link((X[1] + W / 2, rp[1]), (X[1] + W / 2, pr[1] + pr[3]), "returns", ls="--", lp=(X[1] + W / 2 + 4.2, rp[1] - 2.5))
    link((X[2] + W, top - 2.6), (X[3], top - 2.6), "raises", ls="--", lp=(75.2, top + 1.6))
    link((X[2] + W, ana[1] + ana[3] - 6.5), (X[3], ana[1] + ana[3] - 6.5), "returns", ls="--", lp=(75.2, ana[1] + ana[3] - 4.6))
    link((X[2] + W, it[1] + it[3] - 6.0), (X[3], it[1] + it[3] - 6.0), "returns", ls="--", lp=(75.2, it[1] + it[3] - 4.1))
    link((X[0] + W / 2, api[1]), (X[0] + W / 2, db[1] + db[3]), "reads", lp=(X[0] + W / 2 + 4, api[1] - 2.5))
    link((X[1], top - 8.0), (X[0] + W, db[1] + db[3] - 6.5), None, color=PURPLE)
    ax.text(24.2, 78, "4", fontsize=7, color=PURPLE, fontweight="bold", ha="center")
    link((X[0] + W / 2, db[1]), (X[0] + W / 2, rep[1] + rep[3]), "ORM", lp=(X[0] + W / 2 + 2.6, db[1] - 3.6))
    yy = rep[1] + rep[3] - 9
    link((X[0] + W, yy), (32, yy), None, color=NAVY)
    ax.text(X[0] + W + 0.4, yy + 1.5, "1", fontsize=8, color=NAVY, fontweight="bold")
    ax.text(30.6, yy + 1.5, "*", fontsize=9, color=NAVY, fontweight="bold")
    yy2 = tr[1] + tr[3] - 9
    link((61, yy2), (68, yy2), None, color=NAVY)
    ax.text(61.3, yy2 + 1.5, "1", fontsize=8, color=NAVY, fontweight="bold")
    ax.text(66.4, yy2 + 1.5, "*", fontsize=9, color=NAVY, fontweight="bold")
    ax.text(1, base - max(rep[3], tr[3], hi[3]) - 4,
            "Solid arrows: calls (numbers = stage order in process_uploaded_report).  Dashed: returned data objects.  1 --- * : one-to-many with cascade delete\n"
            "(reports -> test_results -> health_insights).  ProcessingResult is what the API serialises; the ORM rows are what is stored.",
            fontsize=7.0, color=SLATE, style="italic", va="top", linespacing=1.4)
    save(fig, "06_uml_class_diagram.png")


# ---------------------------------------------------------------- 07 sequence
def sequence():
    fig, ax = canvas(12, 8.8, "Sequence diagram: uploading and analysing one lab report", ty=92)
    actors = [("User", 7), ("React SPA", 21.5), ("FastAPI\nmain.py", 36), ("report_\nprocessor", 50.5), ("ocr / ner /\nanalyzer", 65), ("ai_insights", 79.5), ("SQLite\n(database.py)", 93)]
    top = 82
    for n, x in actors:
        box(ax, x - 6.4, top, 12.8, 7, n, fc=NAVY, ec=NAVY, tc="white", fs=7.8, bold=True)
        ax.plot([x, x], [top, 18.5], color=LINE, lw=1, ls=(0, (4, 3)))
    X = {a[0]: a[1] for a in actors}
    names = [a[0] for a in actors]
    U, S, F, R, P, A, D = names
    seq = [
        (U, S, "choose file, press Upload", 78, False),
        (S, F, "POST /api/reports (file, use_llm) + Bearer token", 74.2, False),
        (F, F, "require_user: verify HMAC signature + expiry", 70.2, "self"),
        (F, R, "process_uploaded_report(name, bytes, use_llm)", 65.6, False),
        (R, D, "create_report(), status = Processing", 62, False),
        (R, P, "extract_text() then extract_structured_tests()", 58.4, False),
        (P, R, "raw text, then rows (name, value, unit, range)", 54.8, True),
        (R, P, "analyze_results(rows)", 51.2, False),
        (P, R, "ClassifiedResult list (LOW / NORMAL / HIGH / UNKNOWN)", 47.6, True),
        (R, D, "save_test_results() -> row ids", 44.0, False),
        (R, A, "generate_insight(name, status)  for each LOW / HIGH row", 40.4, False),
        (A, R, "rule text (optional LLM rewrite, falls back on error)", 36.8, True),
        (R, D, "save_health_insight(); status = Completed", 33.2, False),
        (R, F, "ProcessingResult (status, stages, rows)", 29.6, True),
        (F, S, "200 JSON: results + insights + stage log", 26.0, True),
        (S, U, "results table, flags, insight cards", 22.4, True),
    ]
    for a, b, label, y, ret in seq:
        xa, xb = X[a], X[b]
        if ret == "self":
            ax.add_patch(Rectangle((xa, y - 1.2), 2.6, 3.6, fc="#E8F0FC", ec=BLUE, lw=1))
            ax.text(xa + 3.8, y + 0.6, label, fontsize=7.2, va="center", color=INK)
            continue
        arrow(ax, (xa, y), (xb, y), None, color=GREEN if ret else BLUE, ls="--" if ret else "-", lw=1.3)
        ax.text((xa + xb) / 2, y + 1.55, label, fontsize=7.0, ha="center", color=INK, bbox=dict(fc="white", ec="none", pad=0.35, alpha=0.9))
    ax.add_patch(Rectangle((2, 3), 96, 12.6, fc="#FFF1EA", ec=ORANGE, lw=1, ls="--"))
    ax.text(4, 13.2, "alt  any stage fails (bad file, no text, no rows, DB error)", fontsize=7.6, color=ORANGE, fontweight="bold", va="center")
    ax.text(4, 7.6, "report_processor sets status = Failed with the message, keeps the raw text and returns it; FastAPI answers 200 with status 'Failed' and the error.\n"
                    "Missing or expired token -> 401 before any processing.   Insight failure -> the report is still Completed (partial).",
            fontsize=7.0, color=INK, va="center", linespacing=1.5)
    save(fig, "07_sequence_diagram.png")


# ---------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(11.5, 7.8, "Use-case diagram", ty=82)
    ax.add_patch(Rectangle((24, 3), 50, 76, fc="#FBFCFE", ec="#D5DCE6", lw=1.4))
    ax.text(49, 75.6, "LabLens", ha="center", fontsize=10.5, fontweight="bold", color=NAVY)
    cases = [
        ("Sign in (demo account)", 69.5), ("Upload lab report\n(PDF, JPG, PNG)", 62), ("View extracted results\nand LOW / NORMAL / HIGH flags", 54),
        ("Read plain-language\ninsights", 46), ("Track one test across\nreports (trend chart)", 38.5), ("Compare two reports", 31),
        ("Browse, open, delete reports", 23.5), ("View dashboard totals\nand critical alerts", 16), ("Load sample reports", 8.5),
    ]
    for t, y in cases:
        ax.add_patch(Ellipse((47, y), 38, 5.8, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(47, y, t, ha="center", va="center", fontsize=7.6, color=INK, linespacing=1.1)

    def actor(x, y, label, color):
        ax.add_patch(Circle((x, y + 8), 2.2, fc="white", ec=color, lw=1.8))
        ax.plot([x, x], [y + 5.8, y + 1.2], color=color, lw=1.8)
        ax.plot([x - 3, x + 3], [y + 4.2, y + 4.2], color=color, lw=1.8)
        ax.plot([x, x - 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.plot([x, x + 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.text(x, y - 5.2, label, ha="center", fontsize=8.4, fontweight="bold", color=INK, linespacing=1.15)

    actor(10, 38, "User\n(signed-in patient)", ORANGE)
    for t, y in cases:
        ax.plot([13.2, 28.5], [44, y], color=LINE, lw=0.9)
    box(ax, 80, 64, 19, 11, "Tesseract OCR\n(external, optional)\nscanned pages, images", fc="white", ec=GREY, fs=7.2, ls="--")
    box(ax, 80, 44, 19, 11, "Anthropic API\n(external, optional)\nrewrites insight text", fc="white", ec=GREY, fs=7.2, ls="--")
    ax.plot([66, 80], [62.5, 67.5], color=GREY, lw=1, ls="--")
    ax.plot([66, 80], [61.2, 50.5], color=GREY, lw=1, ls="--")
    ax.text(73, 69.8 - 1.2, "", fontsize=7)
    ax.text(49, -1.2, "Every case except 'Sign in' needs a valid bearer token. There is one account; no roles. Dashed links: used only when the scan needs OCR / the LLM switch is on.",
            ha="center", fontsize=7.4, color=SLATE, style="italic")
    save(fig, "08_use_case_diagram.png")


# ---------------------------------------------------------------- 09 ER
def er_table(ax, x, y, w, title, cols, color):
    lh = 3.2
    h = 5 + lh * len(cols)
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.8))
    ax.add_patch(Rectangle((x, y - 5), w, 5, fc=color, ec=color))
    ax.text(x + w / 2, y - 2.5, title, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    pos = {}
    for i, (key, n, t, c) in enumerate(cols):
        yy = y - 5 - lh * (i + 0.5)
        pos[n] = yy
        ax.text(x + 1, yy, key, fontsize=7.6, va="center", family="monospace", color=ORANGE if key == "FK" else NAVY, fontweight="bold")
        ax.text(x + 4.6, yy, n, fontsize=7.8, va="center", family="monospace", color=INK, fontweight="bold" if key == "PK" else "normal")
        ax.text(x + w - 1, yy, t, fontsize=7.2, va="center", ha="right", family="monospace", color=BLUE)
    return (x, y - h, w, h), pos


def er():
    fig, ax = canvas(12, 5.8, "Entity-relationship diagram of the SQLite database", ty=58)
    r_box, r_pos = er_table(ax, 1, 53, 27, "reports", [
        ("PK", "id", "INTEGER", ""), ("", "file_name", "VARCHAR(255)", ""), ("", "file_type", "VARCHAR(10)", ""), ("", "upload_date", "DATETIME", ""),
        ("", "processing_status", "VARCHAR(50)", ""), ("", "error_message", "TEXT", ""), ("", "raw_text", "TEXT", "")], NAVY)
    t_box, t_pos = er_table(ax, 37, 53, 30, "test_results", [
        ("PK", "id", "INTEGER", ""), ("FK", "report_id", "INTEGER", ""), ("", "test_name", "VARCHAR(255)", ""), ("", "result_value", "FLOAT", ""),
        ("", "unit", "VARCHAR(50)", ""), ("", "reference_low", "FLOAT", ""), ("", "reference_high", "FLOAT", ""), ("", "status", "VARCHAR(20)", ""),
        ("", "test_date", "DATETIME", ""), ("", "confidence_score", "FLOAT", "")], GREEN)
    h_box, h_pos = er_table(ax, 76, 53, 23, "health_insights", [
        ("PK", "id", "INTEGER", ""), ("FK", "test_result_id", "INTEGER", ""), ("", "explanation", "TEXT", ""), ("", "possible_causes", "TEXT", ""),
        ("", "recommendations", "TEXT", ""), ("", "created_at", "DATETIME", "")], PURPLE)
    for (x0, y0), (x1, y1), xm in (((28, r_pos["id"]), (37, t_pos["report_id"]), 32.5), ((67, t_pos["id"]), (76, h_pos["test_result_id"]), 71.5)):
        ax.plot([x0, xm, xm], [y0, y0, y1], color=SLATE, lw=1.4)
        arrow(ax, (xm, y1), (x1, y1), None, head="-", lw=1.4)
        ax.text(x0 + 0.5, y0 + 1.6, "1", fontsize=9, color=NAVY, fontweight="bold")
        ax.text(x1 - 2.2, y1 + 1.6, "N", fontsize=9, color=NAVY, fontweight="bold")
    ax.text(32.5, 41, "has\n(cascade\ndelete)", fontsize=7.2, color=SLATE, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.4))
    ax.text(71.5, 41, "has\n(cascade\ndelete)", fontsize=7.2, color=SLATE, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.4))
    ax.text(1, 4.2, "status (test_results): LOW | NORMAL | HIGH | UNKNOWN.   processing_status (reports): Pending -> Processing -> Completed | Failed.\n"
                    "health_insights rows exist only for LOW and HIGH results. Deleting a report removes its results and insights (delete-orphan cascade).\n"
                    "The signed-in user is not stored: the demo account comes from .env and is carried only in the signed token.",
            fontsize=7.4, color=SLATE, style="italic", linespacing=1.5, va="center")
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 flowchart
def diamond(ax, cx, cy, w, h, text, fc="#FFF8E5", ec=GOLD, fs=7.2):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fc, ec=ec, lw=1.4))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.1)


def flowchart():
    fig, ax = canvas(12.6, 9.6, "Flowchart of the core algorithm: row parser, name matcher and classifier", ty=128)
    o = 24  # A and B sit above the classifier strip

    def term(cx, y, t, w=26, h=4.4):
        box(ax, cx - w / 2, y - h / 2, w, h, t, fc=NAVY, ec=NAVY, tc="white", fs=7.4, bold=True, rounding=2.2)

    def step(cx, y, t, c=BLUE, w=28, h=5.6, fs=7.0):
        box(ax, cx - w / 2, y - h / 2, w, h, t, fc="#F4F8FE", ec=c, fs=fs)

    def down(x, a, b):
        arrow(ax, (x, a), (x, b), None, lw=1.2)

    # ---- A. row parser
    c1 = 16
    ax.text(1, 100.2 + o, "A. Row parser  (ner_processor)", fontsize=8.8, fontweight="bold", color=NAVY, va="center")
    term(c1, 94.5 + o, "text from extract_text()", 27)
    step(c1, 87.2 + o, "test_date = first date in text\nfor each line: strip")
    diamond(ax, c1, 78.4 + o, 27, 8, "blank, < 3 chars or\nheader-only line?")
    diamond(ax, c1, 69 + o, 27, 8, "contains a digit?")
    diamond(ax, c1, 59.6 + o, 27, 8, "name + value regex\nmatches line start?")
    step(c1, 49.6 + o, "value = float;  unit = optional unit;\nrange = a-b / a to b (two-sided),\nelse <x or >x;  no unit: trailing unit", w=29, h=8.4, fs=6.8)
    diamond(ax, c1, 38.6 + o, 27, 8, "no range and\nno unit?")
    step(c1, 28.4 + o, "confidence = 0.9 (both bounds)\nelse 0.6;  minus 0.1 if no unit", PURPLE, w=28)
    for a, b in ((92.3, 90.0), (84.4, 82.4), (74.4, 73.0), (65.0, 63.6), (55.6, 53.8), (45.4, 42.6), (34.6, 31.2)):
        down(c1, a + o, b + o)
    for y, lab in ((78.4, "no"), (69, "yes"), (59.6, "yes"), (38.6, "no")):
        ax.text(c1 + 1.0, y + o - 5.0, lab, fontsize=6.8, color=GREEN)
    for y, lab in ((78.4, "yes"), (69, "no"), (59.6, "no"), (38.6, "yes")):
        arrow(ax, (c1 + 13.5, y + o), (c1 + 18.5, y + o), None, color=ORANGE, lw=1.2)
        ax.text(c1 + 14.3, y + o + 1.6, lab, fontsize=6.8, color=ORANGE)
        ax.text(c1 + 19.0, y + o, "skip line", fontsize=7.0, color=ORANGE, va="center")

    # ---- B. name matcher
    c2 = 71
    ax.text(48, 100.2 + o, "B. Name matcher  (normalize_test_name)", fontsize=8.8, fontweight="bold", color=NAVY, va="center")
    arrow(ax, (c1 + 14, 28.4 + o), (49.0, 94.5 + o), None, color=PURPLE, lw=1.2, rad=-0.28)
    ax.text(45.5, 62 + o, "raw name", fontsize=6.8, color=PURPLE, rotation=90, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.3))
    step(c2 + 2, 94.5 + o, "clean: keep letters, digits, / ( ) %;  collapse spaces;  trim : . -", PURPLE, w=44, h=5.0)
    step(c2 + 2, 86.0 + o, "TF-IDF vector (char n-grams 2-4), cosine similarity to the 55 known names", PURPLE, w=44, h=5.0)
    diamond(ax, c2 + 2, 75.5 + o, 24, 8.8, "best similarity\n>= 0.55 ?")
    step(c2 - 10, 62.5 + o, "snap to canonical name\n(Haemogl0bin -> Hemoglobin)", GREEN, w=21, h=6.6, fs=6.6)
    step(c2 + 14, 62.5 + o, "keep cleaned name\n(title-case if all\nupper / lower)", ORANGE, w=21, h=6.6, fs=6.6)
    step(c2 + 2, 51.5 + o, "append row {name, value, unit, low, high, date, confidence}", BLUE, w=44, h=5.0)
    step(c2 + 2, 43.5 + o, "drop duplicates on (name, value, unit)", BLUE, w=44, h=5.0)
    down(c2 + 2, 92.0 + o, 88.5 + o)
    down(c2 + 2, 83.5 + o, 79.9 + o)
    arrow(ax, (c2 - 4, 73.6 + o), (c2 - 10, 65.8 + o), None, lw=1.2)
    arrow(ax, (c2 + 8, 73.6 + o), (c2 + 14, 65.8 + o), None, lw=1.2)
    ax.text(c2 - 9, 70.6 + o, "yes", fontsize=6.8, color=GREEN)
    ax.text(c2 + 10.6, 70.6 + o, "no", fontsize=6.8, color=ORANGE)
    ax.plot([c2 - 10, c2 - 10, c2 + 2], [59.2 + o, 55.6 + o, 55.6 + o], color=SLATE, lw=1.2)
    ax.plot([c2 + 14, c2 + 14, c2 + 2], [59.2 + o, 55.6 + o, 55.6 + o], color=SLATE, lw=1.2)
    arrow(ax, (c2 + 2, 55.6 + o), (c2 + 2, 54.0 + o), None, lw=1.2)
    down(c2 + 2, 49.0 + o, 46.0 + o)
    down(c2 + 2, 41.0 + o, 39.7 + o)
    term(c2 + 2, 37.5 + o, "list of structured rows  ->  analyze_results()", 40)

    # ---- C. classifier strip (horizontal)
    ax.plot([c2 + 2, c2 + 2, 7], [35.3 + o, 33.0, 33.0], color=SLATE, lw=1.2)
    arrow(ax, (7, 33.0), (7, 28.8), None, lw=1.2)
    ax.text(1, 36.2, "C. Classifier  (result_analyzer.classify_result, applied to every row)", fontsize=8.8, fontweight="bold", color=NAVY, va="center")
    term(7, 26.2, "value,\nlow, high", 11.5, 5.0)
    xs = [25, 42, 59, 76]
    qs = ["value is\nNone?", "low and high\nboth known?", "only high\nknown?", "only low\nknown?"]
    for x, q in zip(xs, qs):
        diamond(ax, x, 26.2, 14.5, 8.6, q, fs=6.8)
    arrow(ax, (12.8, 26.2), (17.75, 26.2), None, lw=1.2)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.25, 26.2), (b - 7.25, 26.2), None, lw=1.2)
        ax.text((a + b) / 2, 27.9, "no", fontsize=6.8, color=GREEN, ha="center")
    outs = ["UNKNOWN", "v < low:  LOW\nv > high:  HIGH\nelse NORMAL", "v > high:  HIGH\nelse NORMAL", "v < low:  LOW\nelse NORMAL"]
    for x, t in zip(xs, outs):
        unk = t == "UNKNOWN"
        arrow(ax, (x, 21.9), (x, 16.8), None, color=ORANGE if unk else GREEN, lw=1.2)
        ax.text(x + 1.0, 19.4, "yes", fontsize=6.8, color=GREEN)
        box(ax, x - 7.8, 9.0, 15.6, 7.8, t, fc="#F1F3F6" if unk else "#F4F8FE", ec=GREY if unk else GREEN, fs=6.8, bold=unk)
    arrow(ax, (xs[-1] + 7.25, 26.2), (87.0, 26.2), None, lw=1.2)
    ax.text(83.5, 27.9, "no", fontsize=6.8, color=GREEN, ha="center")
    box(ax, 87.0, 22.2, 12.0, 8.0, "UNKNOWN", fc="#F1F3F6", ec=GREY, fs=6.8, bold=True)
    ax.text(50, 3.4, "Boundaries are inclusive: a value equal to either limit is NORMAL.  Skipped lines produce no row; unmatched names are kept, not dropped.",
            ha="center", fontsize=7.2, color=SLATE, style="italic")
    save(fig, "10_core_algorithm_flowchart.png")


def main():
    for fn in (architecture, workflow, dfd0, dfd1, dfd2, class_diagram, sequence, use_case, er, flowchart):
        fn()


if __name__ == "__main__":
    main()
