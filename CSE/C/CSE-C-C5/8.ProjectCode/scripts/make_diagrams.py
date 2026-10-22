"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi) -> docs/diagrams/*.png

Each diagram mirrors what the code does: app.py + templates/ (Flask), backend/main.py (FastAPI, 9 routes),
src/ (generate_dataset, preprocess, hybrid_model, recommend) and frontend/ (React). There is no SQL database:
data lives in data/*.csv and models/*.pkl, so the ER diagram is the logical data model of those files.

    python scripts/make_diagrams.py
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
PAPER, LINE = "#F6F8FB", "#9AA8BD"
plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(w, title=None, ty=99, top=None):
    top = top or ty + 2
    fig, ax = plt.subplots(figsize=(w, w * top / 100))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, top)
    ax.axis("off")
    ax.set_aspect("equal")
    if title:
        ax.text(1, ty, title, fontsize=13, fontweight="bold", color=NAVY, va="top")
    return fig, ax


def box(ax, x, y, w, h, text, fc=PAPER, ec=LINE, tc=INK, fs=9.5, bold=False, lw=1.3, rounding=1.2, ls="-", ha="center"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounding}", fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    tx = x + w / 2 if ha == "center" else x + 1.2
    ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p, q, label=None, color=SLATE, lw=1.4, ls="-", fs=8, off=(0, 1.2), rad=0.0, head="-|>", lp=None):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=head, color=color, lw=lw, ls=ls,
                                                    connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if label:
        lx, ly = lp if lp else ((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1])
        ax.text(lx, ly, label, fontsize=fs, color=color, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.88))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


def process(ax, cx, cy, r, text, num, fs=8):
    ax.add_patch(Circle((cx, cy), r, fc="#E8F0FC", ec=BLUE, lw=1.6))
    ax.text(cx, cy + r * 0.52, num, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
    ax.text(cx, cy - r * 0.12, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)
    return (cx, cy, r)


def entity(ax, x, y, w, h, text):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF1EA", ec=ORANGE, lw=1.8))
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


def mid(b, side):
    x, y, w, h = b
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]


def cpt(c, ang_deg):
    import math
    cx, cy, r = c
    return (cx + r * math.cos(math.radians(ang_deg)), cy + r * math.sin(math.radians(ang_deg)))



# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11.5, "System architecture", ty=82)
    cols = ((1, 20, "Presentation"), (24, 24, "Application (FastAPI)"), (51, 29, "Core (src/, Python)"), (83, 16, "Data and models"))
    for x, w, label in cols:
        ax.add_patch(Rectangle((x, 6), w, 70, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 73.5, label, ha="center", fontsize=9.5, color=SLATE, fontweight="bold")
    box(ax, 2.5, 40, 17, 26, "React 19 SPA\n(Vite, Tailwind 4)\nport 5405\n/api proxy\n\nLanding, Eligibility,\nRecommendations,\nOfficer dashboard,\nRecruiter, Companies,\ncommand palette,\nactivity log", fc="#E8F0FC", ec=BLUE, fs=7.2)
    box(ax, 2.5, 14, 17, 18, "Original Flask UI\napp.py + templates/\n5 pages, port 5000\n(imports the same\nsrc/ core)", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    box(ax, 25.5, 52, 21, 15, "backend/main.py\n9 route handlers\nport 8405, /docs\nPydantic validation\nerrors 404 / 422 / 503", fc="#E6F6EF", ec=GREEN, fs=7.8)
    box(ax, 25.5, 36, 21, 12, "CORS middleware\nallows only the\nfrontend origin (5405)", fc="#E6F6EF", ec=GREEN, fs=7.6)
    box(ax, 25.5, 20, 21, 12, "helpers: _tips(),\n_company_row(),\n_records(), _dataset()", fc="#E6F6EF", ec=GREEN, fs=7.6)
    box(ax, 52.5, 56, 26, 11, "recommend.py\npredict_for(), recommend(),\ndelta_max_cgpa()", fc="#EFE9FB", ec=PURPLE, fs=7.8)
    box(ax, 52.5, 46, 26, 6.5, "preprocess.py  (24 features)", fc=PAPER, ec=NAVY, fs=7.8)
    box(ax, 52.5, 37, 26, 6.5, "hybrid_model.py  (training)", fc=PAPER, ec=NAVY, fs=7.8)
    box(ax, 52.5, 28, 26, 6.5, "generate_dataset.py", fc=PAPER, ec=NAVY, fs=7.8)
    ax.text(65.5, 18, "XGBoost 3 + Platt scaling,\nkNN / SVM residual models,\nscikit-learn, pandas, SHAP", ha="center", va="center", fontsize=7.4, color=SLATE, style="italic")
    box(ax, 84.5, 56, 13, 12, "models/\npreprocess.pkl\nxgb_calibrated.pkl\nknn_residual.pkl\nsvm_residual.pkl", fc="#FFF8E5", ec=GOLD, fs=6.6)
    box(ax, 84.5, 42, 13, 10, "data/\ncompanies.csv\n(30 rows)", fc="#FFF8E5", ec=GOLD, fs=7.4)
    box(ax, 84.5, 28, 13, 10, "data/\nplacement_\ndataset.csv", fc="#FFF8E5", ec=GOLD, fs=7.2)
    box(ax, 84.5, 12, 13, 12, "metrics.json\nstatic/\nshap, pca,\nprob_hist .png", fc="#FFF8E5", ec=GOLD, fs=6.8)
    arrow(ax, (19.5, 58), (25.5, 58), "JSON", color=BLUE, off=(0, 2.6), fs=7)
    ax.plot([11, 11, 51.2], [14, 8.5, 8.5], color=ORANGE, lw=1.4, ls="--")
    ax.plot([51.2, 51.2], [8.5, 61.5], color=ORANGE, lw=1.4, ls="--")
    arrow(ax, (51.2, 61.5), (52.5, 61.5), None, color=ORANGE, ls="--")
    ax.text(32, 5.2, "Flask imports the same src/ modules directly", fontsize=7.2, color=ORANGE, ha="center")
    arrow(ax, (36, 52), (36, 48), None)
    arrow(ax, (36, 36), (36, 32), None)
    arrow(ax, (46.5, 62), (52.5, 62), "calls", off=(-0.8, 2.4), fs=7.4, color=GREEN)
    arrow(ax, (78.5, 62), (84.5, 62), "load", off=(0, 2.4), fs=7)
    arrow(ax, (78.5, 49), (84.5, 47), None)
    arrow(ax, (78.5, 40), (84.5, 33), "read /\nwrite", off=(0.3, 4.6), fs=6.6)
    arrow(ax, (78.5, 31), (84.5, 18), None, ls="--")
    ax.text(50, 1.4, "No SQL database: data is read from CSV files and trained models are loaded from pickle files on each request.", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(11.5, "Data flow diagram, level 0 (context)", ty=60)
    entity(ax, 2, 40, 17, 12, "Student")
    entity(ax, 2, 22, 17, 12, "Placement officer")
    entity(ax, 2, 4, 17, 12, "Recruiter")
    P = process(ax, 53, 30, 14, "Smart Campus\nPlacement\nSystem", "0", fs=9)
    store(ax, 74, 44, 25, 8, "student records (CSV)", "D1")
    store(ax, 74, 30, 25, 8, "company table (CSV)", "D2")
    store(ax, 74, 16, 25, 8, "trained models (pkl)", "D3")
    store(ax, 74, 2, 25, 8, "metrics + plots", "D4")
    arrow(ax, (19, 49), (41, 36), "student profile,\ntarget company, role", fs=7.4, lp=(28.5, 47.2))
    arrow(ax, (41.5, 33), (19, 43.5), "probability, label,\nskill-gap tips,\ntop-5 alternatives", fs=7.2, color=GREEN, lp=(29.8, 34.7))
    arrow(ax, (19, 29), (39.2, 29.5), "dashboard request", fs=7.4, off=(0, 1.8))
    arrow(ax, (39.2, 26.5), (19, 25), "metrics, plots,\nplacement stats", fs=7.2, color=GREEN, lp=(29.2, 22.2))
    arrow(ax, (19, 9), (43, 21), "shortlist filters\n(CGPA, aptitude, branch)", fs=7.4, lp=(28, 16.2))
    arrow(ax, (47.5, 18.5), (19, 6), "matching students", fs=7.2, color=GREEN, lp=(36, 8.8))
    arrow(ax, (63, 40), (74, 47), "read", off=(-0.2, 2.0), fs=7)
    arrow(ax, (67, 33), (74, 34), "read", off=(0, 2.0), fs=7)
    arrow(ax, (66, 24), (74, 20), "load", off=(0, -2.0), fs=7)
    arrow(ax, (60, 18), (74, 6), "read", off=(0, -2.2), fs=7)
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11.5, "Data flow diagram, level 1", ty=100)
    R = 6.6
    entity(ax, 1, 40, 12, 12, "Student")
    entity(ax, 1, 16, 12, 12, "Placement\nofficer")
    entity(ax, 1, 1.5, 12, 10, "Recruiter")
    ys = {1: 90, 2: 74, 3: 56, 4: 38, 5: 22, 6: 7}
    names = {1: "Prepare\ndata and\nfeatures", 2: "Train and\nevaluate\nmodels", 3: "Predict\nplacement\nprobability",
             4: "Recommend\ncompany-\nrole pairs", 5: "Officer\nanalytics", 6: "Recruiter\nshortlist"}
    P = {k: process(ax, 42, y, R, names[k], str(k), fs=6.8) for k, y in ys.items()}
    sx, sw, sh = 76, 23, 6.2

    def st(y, text, tag):
        store(ax, sx, y - sh / 2, sw, sh, text, tag)
        return y

    st(90, "student records (CSV)", "D1")
    st(77, "trained models (pkl)", "D3")
    st(68, "metrics.json + plots", "D4")
    st(59, "trained models (pkl)", "D3")
    st(51, "company table (CSV)", "D2")
    st(41, "company table (CSV)", "D2")
    st(33, "trained models (pkl)", "D3")
    st(22, "metrics.json + plots", "D4")
    st(7, "student records (CSV)", "D1")
    # student <-> 3 / 4
    arrow(ax, (13, 49), (36.2, 55), "profile, company, role", fs=6.8, lp=(21.5, 54.2))
    arrow(ax, (36.4, 52.8), (13, 46.5), "probability, label, tips", fs=6.8, color=GREEN, lp=(22.5, 47.2))
    arrow(ax, (13, 43.5), (36.4, 38.8), "profile, target", fs=6.8, lp=(20.0, 37.4))
    arrow(ax, (36.4, 36.2), (13, 41.0), "top-5, gain, match rate", fs=6.8, color=GREEN, lp=(23.8, 34.2))
    # officer <-> 5, recruiter <-> 6
    arrow(ax, (13, 25), (35.4, 23.2), "dashboard request", fs=6.8, lp=(23, 26.6))
    arrow(ax, (35.4, 20.4), (13, 20.0), "metrics, plots, stats", fs=6.8, color=GREEN, lp=(23.5, 17.4))
    arrow(ax, (13, 9), (35.4, 8.0), "filters", fs=6.8, lp=(23, 10.6))
    arrow(ax, (35.4, 5.4), (13, 4.5), "students", fs=6.8, color=GREEN, lp=(23, 2.3))
    # internal
    arrow(ax, (42, 83.4), (42, 80.6), "features,\nlabels", fs=6.4, lp=(49.5, 82.0))
    arrow(ax, (42, 67.4), (42, 62.6), None)
    arrow(ax, (42, 49.4), (42, 44.6), None)
    # stores
    arrow(ax, (48.6, 90), (76, 90), "read", fs=6.8, off=(0, 1.5))
    arrow(ax, (47.6, 77.5), (76, 77), "save models", fs=6.8, color=ORANGE, off=(0, 1.6))
    arrow(ax, (46.6, 70.5), (76, 68.5), "save metrics, plots", fs=6.8, color=ORANGE, off=(0, -1.8))
    arrow(ax, (76, 59), (48.6, 56.6), "load", fs=6.8, off=(0, 1.6))
    arrow(ax, (76, 51), (46.2, 53.0), "cutoffs", fs=6.8, off=(1, -1.7))
    arrow(ax, (76, 41), (48.6, 39.0), "cutoffs", fs=6.8, off=(0, 1.6))
    arrow(ax, (76, 33), (47.0, 35.4), "load", fs=6.8, off=(0, -1.7))
    arrow(ax, (76, 22), (48.6, 22), "read", fs=6.8, off=(0, 1.5))
    arrow(ax, (76, 7), (48.6, 7), "read", fs=6.8, off=(0, 1.5))
    ax.text(88, 96.2, "Stores shown more than once are the same store, repeated to keep the lines short.", ha="center", fontsize=6.4, color=SLATE, style="italic", va="center", wrap=True)
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2 (process 4)
def dfd2():
    fig, ax = canvas(11.5, "Data flow diagram, level 2 - process 4 (Recommend company-role pairs)", ty=60)
    entity(ax, 1, 16, 13, 12, "Student")
    store(ax, 18, 50, 28, 7, "trained models (xgb + kNN)", "D3")
    store(ax, 49, 50, 20, 7, "company table", "D2")
    store(ax, 72, 50, 27, 7, "trained models (xgb + kNN)", "D3")
    P41 = process(ax, 32, 34, 8.5, "Score the\noriginal\ntarget", "4.1", fs=7)
    P42 = process(ax, 56, 34, 8.5, "Apply\nfeasibility\nfilters", "4.2", fs=7)
    P43 = process(ax, 80, 34, 8.5, "Score every\ncompany x\nrole pair", "4.3", fs=7)
    P44 = process(ax, 80, 10, 8.5, "Rank and\nbuild 3 lists", "4.4", fs=7)
    P45 = process(ax, 50, 10, 8.5, "Compute gain\nand match\nrate", "4.5", fs=7)
    arrow(ax, (32, 50), (32, 42.5), "load", fs=7, off=(2.6, 0))
    arrow(ax, (59, 50), (59, 42.5), "cutoffs, tier,\npackage, location", fs=6.6, lp=(66.2, 46.2))
    arrow(ax, (82, 50), (82, 42.5), "load", fs=7, off=(2.6, 0))
    arrow(ax, (14, 26), (24, 31), "profile,\ntarget", fs=7, lp=(12.5, 31.6))
    arrow(ax, (40.5, 34), (47.5, 34), "p0", fs=7, off=(0, 2))
    arrow(ax, (64.5, 34), (71.5, 34), "feasible\ncompanies", fs=6.8, off=(0, 3.6))
    arrow(ax, (80, 25.5), (80, 18.5), "scored\ncandidates", fs=6.8, lp=(87.2, 22.0))
    arrow(ax, (71.5, 10), (58.5, 10), "top-5", fs=7, off=(0, 2))
    arrow(ax, (41.5, 10), (14, 19.5), "base probability, gain,\nmatch rate, 3 lists", fs=7, color=GREEN, lp=(27.5, 10.8))
    ax.text(50, 0.8, "Feasibility rules: |CGPA - cutoff| <= delta_max(tier); aptitude >= cutoff - 15; no Tier-1 company when backlogs > 2; optional minimum package", ha="center", fontsize=7.2, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 class diagram
def uml_class(ax, x, y, w, name, attrs, ops, stereotype=None, fc="#FFFFFF", ec=NAVY):
    lh = 2.45
    h = 4.6 + lh * (len(attrs) + len(ops)) + 2.2
    ax.add_patch(Rectangle((x, y - h), w, h, fc=fc, ec=ec, lw=1.4))
    ax.add_patch(Rectangle((x, y - 4.6), w, 4.6, fc="#E8EEF7", ec=ec, lw=1.4))
    if stereotype:
        ax.text(x + w / 2, y - 1.3, "<<%s>>" % stereotype, ha="center", va="center", fontsize=6.4, color=SLATE)
        ax.text(x + w / 2, y - 3.3, name, ha="center", va="center", fontsize=8.2, fontweight="bold", color=INK)
    else:
        ax.text(x + w / 2, y - 2.3, name, ha="center", va="center", fontsize=8.2, fontweight="bold", color=INK)
    yy = y - 4.6
    for a in attrs:
        yy -= lh
        ax.text(x + 0.9, yy + lh / 2, a, ha="left", va="center", fontsize=6.5, color=INK, family="DejaVu Sans Mono")
    yy -= 1.0
    ax.plot([x, x + w], [yy + 0.3, yy + 0.3], color=ec, lw=0.9)
    for o in ops:
        yy -= lh
        ax.text(x + 0.9, yy + lh / 2, o, ha="left", va="center", fontsize=6.5, color=INK, family="DejaVu Sans Mono")
    return (x, y - h, w, h)


def class_diagram():
    fig, ax = canvas(12, "UML class diagram", ty=98, top=100)
    gap = 4
    # column 1: request models
    c1 = []
    y = 94
    for name, attrs in (
        ("Profile", ["cgpa: float [0,10]", "tenth, twelfth: float", "aptitude, technical: float", "communication, dsa: float", "projects, internships: int", "certifications, backlogs: int", "branch: str", "degree: str"]),
        ("PredictIn", ["target_company: str", "target_role: str = 'SDE'"]),
        ("RecommendIn", ["cgpa, aptitude, technical: float", "communication, dsa: float", "projects, internships: int", "certifications, backlogs: int", "branch: str", "target_company: str | None", "target_role: str", "location: str | None"]),
        ("ShortlistIn", ["min_cgpa: float", "min_apt: float", "branch: str = 'ALL'"]),
    ):
        b = uml_class(ax, 1, y, 26, name, attrs, [], "pydantic")
        c1.append(b)
        y = b[1] - gap
    # column 2
    api = uml_class(ax, 36, 94, 29, "FastAPI app (backend/main.py)", [], ["health()", "meta()", "companies()", "metrics()", "stats()", "plot(name)", "predict(body: PredictIn)", "recommend_endpoint(body)", "shortlist(body)", "_tips(profile, row)"], "module")
    rec = uml_class(ax, 36, api[1] - 6, 29, "recommend.py", ["MODEL_DIR: str"], ["delta_max_cgpa(tier)", "load_artifacts()", "predict_for(profile, row, role)", "recommend(profile, top_k,", "    min_package, location)"], "module")
    pre = uml_class(ax, 36, rec[1] - 6, 29, "preprocess.py", ["FREQ_COLS (5)", "NUM_COLS (13)", "EXTRA_NUM (6)"], ["load_raw()", "build_features(df, comp,", "  freq_maps, scaler_stats, fit)", "save_artifacts(...)"], "module")
    # column 3
    hyb = uml_class(ax, 72, 94, 27, "hybrid_model.py", ["SEED = 42"], ["metrics(y, pred, prob)", "main(): 70/15/15 split,", "  6 baselines, 9-fold CV,", "  Platt calibration,", "  residual hybrid (kNN, SVM),", "  SHAP, PCA, histogram"], "module")
    art = uml_class(ax, 72, hyb[1] - 4, 27, "Trained artefacts (models/)", ["preprocess.pkl", "xgb_calibrated.pkl", "knn_residual.pkl", "svm_residual.pkl", "companies.pkl, metrics.json"], [], "files")
    lib = uml_class(ax, 72, art[1] - 4, 27, "scikit-learn / xgboost", ["CalibratedClassifierCV(", "  XGBClassifier, sigmoid,cv=3)", "KNeighborsClassifier(k=9)", "SVC(kernel='rbf')"], [], "library")
    gen = uml_class(ax, 72, lib[1] - 4, 27, "generate_dataset.py", ["COMPANIES: 30 tuples", "N = 3000, SEED = 42"], ["logit label model", "writes data/*.csv"], "script")

    def top(b, f=0.5):
        return (b[0] + b[2] * f, b[1] + b[3])

    def bot(b, f=0.5):
        return (b[0] + b[2] * f, b[1])

    # PredictIn -> Profile (inheritance)
    arrow(ax, top(c1[1], 0.3), bot(c1[0], 0.3), None, color=NAVY, head="-|>")
    ax.text(top(c1[1], 0.3)[0] + 1.5, (top(c1[1])[1] + bot(c1[0])[1]) / 2, "extends", fontsize=6.4, color=SLATE, va="center")
    # main.py uses request models
    arrow(ax, (36, 84), (27, 84), "uses", fs=6.8, off=(0, 1.6), color=BLUE)
    # main.py -> recommend.py -> preprocess.py
    arrow(ax, bot(api, 0.5), top(rec, 0.5), "calls", fs=6.8, lp=(bot(api)[0] + 4.5, (bot(api)[1] + top(rec)[1]) / 2), color=GREEN)
    arrow(ax, bot(rec, 0.5), top(pre, 0.5), "imports", fs=6.8, lp=(bot(rec)[0] + 4.5, (bot(rec)[1] + top(pre)[1]) / 2), color=GREEN)
    # recommend.py -> artefacts (loads)
    ry = rec[1] + rec[3] * 0.6
    ax.plot([65, 68.5], [ry, ry], color=PURPLE, lw=1.3)
    ax.plot([68.5, 68.5], [ry, art[1] + art[3] * 0.5], color=PURPLE, lw=1.3)
    arrow(ax, (68.5, art[1] + art[3] * 0.5), (72, art[1] + art[3] * 0.5), "loads", fs=6.8, lp=(68.5, ry + 1.8), color=PURPLE)
    # hybrid_model -> artefacts (saves), artefacts wraps library
    arrow(ax, bot(hyb, 0.5), top(art, 0.5), "saves", fs=6.8, lp=(bot(hyb)[0] + 3.5, (bot(hyb)[1] + top(art)[1]) / 2), color=ORANGE)
    arrow(ax, bot(art, 0.5), top(lib, 0.5), "pickles", fs=6.8, lp=(bot(art)[0] + 3.5, (bot(art)[1] + top(lib)[1]) / 2))
    # preprocess <- hybrid_model (build_features)
    py = pre[1] + pre[3] * 0.5
    ax.plot([72, 68.5], [hyb[1] + hyb[3] * 0.25, hyb[1] + hyb[3] * 0.25], color=SLATE, lw=1.1, ls="--")
    ax.plot([68.5, 68.5], [hyb[1] + hyb[3] * 0.25, py], color=SLATE, lw=1.1, ls="--")
    arrow(ax, (68.5, py), (65, py), "build_features", fs=6.4, lp=(68.2, py + 2.4), color=SLATE, ls="--")
    ax.text(50, 0.8, "PredictIn extends Profile. The core (src/) is written as modules of functions, so the UML shows each module as a class box.", ha="center", fontsize=7.2, color=SLATE, style="italic")
    save(fig, "06_class_diagram.png")


# ---------------------------------------------------------------- 09 ER
def er_table(ax, x, y, w, title, rows, ec=NAVY):
    lh = 2.45
    h = 4.2 + lh * len(rows)
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=ec, lw=1.5))
    ax.add_patch(Rectangle((x, y - 4.2), w, 4.2, fc=ec, ec=ec))
    ax.text(x + w / 2, y - 2.1, title, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    for i, r in enumerate(rows):
        ax.text(x + 1, y - 4.2 - lh * (i + 0.55), r, ha="left", va="center", fontsize=6.8, family="DejaVu Sans Mono", color=INK)
    return (x, y - h, w, h)


def er_diagram():
    fig, ax = canvas(12, "Entity-relationship diagram (logical data model: CSV + pickle files)", ty=88, top=90)
    stu = er_table(ax, 1, 84, 34, "STUDENT_RECORD (placement_dataset.csv)", [
        "PK row id (implicit)", "CGPA, Tenth_Percent, Twelfth_Percent", "Aptitude_Score, Technical_Score",
        "Communication_Score, DSA_Score", "Projects, Internships, Certifications", "Backlogs", "Branch, Degree_Type, Student_Type",
        "Placement_Year", "FK Target_Company", "FK Target_Role", "Target_Tier", "Placed (0/1)  <- label"])
    com = er_table(ax, 46, 84, 30, "COMPANY (companies.csv)", [
        "PK Company", "Tier (1/2/3)", "CGPA_Cutoff", "Apt_Cutoff", "Tech_Cutoff", "Package_LPA", "Location", "Company_Type", "Hiring_Rate"], ec=ORANGE)
    role = er_table(ax, 46, 54, 30, "ROLE (8 values, enumerated)", ["SDE, Data Analyst, ML Engineer,", "QA Engineer, DevOps,", "Support Engineer,", "Embedded Engineer,", "Design Engineer"], ec=GREEN)
    mod = er_table(ax, 1, 31, 34, "MODEL_ARTIFACT (models/*.pkl)", ["preprocess.pkl (freq maps, scaler)", "xgb_calibrated.pkl", "knn_residual.pkl", "svm_residual.pkl", "companies.pkl"], ec=PURPLE)
    met = er_table(ax, 46, 31, 30, "METRICS (metrics.json)", ["9 models x 5 metrics", "cv_xgb_9fold", "brier_platt", "residual_rate", "test_size"], ec=GOLD)
    plot = er_table(ax, 81, 31, 18, "PLOT_FILE", ["static/", " prob_hist.png", " pca.png", " shap.png"], ec=SLATE)
    ax.plot([35, 46], [60, 74], color=SLATE, lw=1.6)
    ax.text(36.2, 63.6, "N", fontsize=9, color=ORANGE, fontweight="bold")
    ax.text(43.6, 74.8, "1", fontsize=9, color=ORANGE, fontweight="bold")
    ax.text(38.6, 66.6, "targets", fontsize=7.4, color=SLATE, rotation=50)
    ax.plot([35, 46], [52, 52], color=SLATE, lw=1.6)
    ax.text(36, 53.4, "N", fontsize=9, color=GREEN, fontweight="bold")
    ax.text(43.6, 53.4, "1", fontsize=9, color=GREEN, fontweight="bold")
    ax.text(40.5, 49.6, "applies for", fontsize=7.4, color=SLATE, ha="center")
    arrow(ax, (18, 51.6), (18, 31.0), None, color=PURPLE, ls="--")
    ax.text(19.5, 41, "trained on (2,100 of the 3,000 rows)", fontsize=7.2, color=PURPLE, va="center")
    arrow(ax, (35, 22), (46, 22), None, head="-", color=SLATE)
    ax.text(40.5, 23.6, "evaluated as", fontsize=7, color=SLATE, ha="center")
    arrow(ax, (76, 22), (81, 22), None, head="-", color=SLATE)
    ax.text(78.5, 23.6, "plots", fontsize=7, color=SLATE, ha="center")
    ax.text(50, 6, "There is no SQL database. Entities are CSV tables and pickled model files; relationships hold by value\n(Target_Company must exist in companies.csv, otherwise the API answers 404).", ha="center", fontsize=7.6, color=SLATE, style="italic")
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11.5, "High-level workflow of the placement system", ty=46)
    steps = [
        ("1  Generate data", "3,000 students,\n30 companies, seed 42", NAVY),
        ("2  Encode + scale", "frequency encoding,\nz-score, 6 engineered\nfeatures (24 total)", BLUE),
        ("3  Train + compare", "70/15/15 split; LogReg,\nTree, RF, SVM, kNN, XGB", ORANGE),
        ("4  Calibrate + hybrid", "Platt scaling; kNN/SVM on\nresidual (borderline) cases", PURPLE),
        ("5  Serve predictions", "FastAPI: probability,\nlabel, skill-gap tips", GREEN),
        ("6  Recommend", "feasibility filters, top-5\ncompany-role pairs", GOLD),
        ("7  Officer analytics", "metrics, SHAP, PCA,\nplacement rates", NAVY),
        ("8  Recruiter shortlist", "filter by CGPA, aptitude,\nbranch (top 50)", BLUE),
    ]
    w = 21.5
    for i, (t, s, c) in enumerate(steps):
        row_y = 24 if i < 4 else 4
        xx = 1.5 + (i % 4) * (w + 3.6)
        box(ax, xx, row_y, w, 14, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 9.6), w, 4.4, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 11.8, t, ha="center", va="center", color="white", fontsize=9.2, fontweight="bold")
        ax.text(xx + w / 2, row_y + 4.6, s, ha="center", va="center", color=INK, fontsize=8.0, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 6), (xx + w + 3.6, row_y + 6))
    x4 = 1.5 + 3 * (w + 3.6) + w / 2
    ax.plot([x4, x4], [24, 21], color=SLATE, lw=1.4)
    ax.plot([x4, 1.5 + w / 2], [21, 21], color=SLATE, lw=1.4)
    arrow(ax, (1.5 + w / 2, 21), (1.5 + w / 2, 18.2))
    ax.text(50, 41.2, "Steps 1-4 run offline (run.bat trains only when models/ is empty); steps 5-8 run per request against the saved models.",
            ha="center", fontsize=8.3, color=SLATE, style="italic")
    save(fig, "02_high_level_workflow.png")




# ---------------------------------------------------------------- 07 sequence
def sequence():
    fig, ax = canvas(11.5, "Sequence diagram - placement prediction (POST /api/predict)", ty=70)
    actors = ["Student", "React page\n/predict", "FastAPI\nbackend/main.py", "recommend.py\npredict_for()", "preprocess.py\nbuild_features()", "models/*.pkl"]
    xs = [8, 24, 42, 60, 77, 92]
    for x, a in zip(xs, actors):
        box(ax, x - 7.5, 62, 15, 6, a, fc="#E8EEF7", ec=NAVY, fs=7.4, bold=True)
        ax.plot([x, x], [3, 62], color="#9AA8BD", lw=1, ls=(0, (4, 3)))

    def msg(i, j, y, text, ret=False, fs=7.2):
        arrow(ax, (xs[i], y), (xs[j], y), None, color=GREEN if ret else SLATE, ls="--" if ret else "-", lw=1.3)
        ax.text((xs[i] + xs[j]) / 2, y + 1.2, text, ha="center", va="bottom", fontsize=fs, color=INK)

    msg(0, 1, 58, "enter profile, pick company + role")
    msg(1, 2, 53, "POST /api/predict (JSON)")
    ax.text(42, 49.5, "validate with Pydantic (422 on bad range)", fontsize=6.8, ha="left", color=ORANGE, style="italic")
    ax.text(42, 46.2, "_company_row(): 404 if unknown", fontsize=6.8, ha="left", color=ORANGE, style="italic")
    msg(2, 3, 42, "predict_for(profile, row, role)")
    msg(3, 5, 37, "load_artifacts(): pickles")
    msg(5, 3, 34, "preprocess, xgb, knn, companies", ret=True, fs=6.8)
    msg(3, 4, 30, "build_features(1 row)")
    msg(4, 3, 27, "X (1 x 24)", ret=True)
    ax.text(60, 23.7, "p = xgb.predict_proba(X)", fontsize=6.8, ha="left", color=PURPLE)
    ax.text(60, 20.7, "if 0.4 <= p <= 0.6: p = 0.5 p + 0.5 kNN(X)", fontsize=6.8, ha="left", color=PURPLE)
    msg(3, 2, 16.5, "probability p", ret=True)
    ax.text(42, 13.0, "label = READY if p >= 0.5; _tips()", fontsize=6.8, ha="left", color=ORANGE, style="italic")
    msg(2, 1, 9.5, "JSON: probability, label, tips, company", ret=True)
    msg(1, 0, 5, "result card + toast", ret=True)
    save(fig, "07_sequence_prediction.png")


# ---------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(11.5, "Use-case diagram", ty=70)
    ax.add_patch(Rectangle((24, 3), 52, 63, fc="#FBFCFE", ec="#D5DCE6", lw=1.2))
    ax.text(50, 63.2, "Smart Campus Placement System", ha="center", fontsize=9.5, fontweight="bold", color=SLATE)
    acts = {"Student": (9, 50), "Placement officer": (9, 28), "Recruiter": (91, 22), "Developer\n(offline)": (91, 52)}
    for n, (x, y) in acts.items():
        ax.add_patch(Circle((x, y + 5.5), 1.8, fc="white", ec=NAVY, lw=1.5))
        ax.plot([x, x], [y + 3.7, y - 1], color=NAVY, lw=1.5)
        ax.plot([x - 3, x + 3], [y + 1.8, y + 1.8], color=NAVY, lw=1.5)
        ax.plot([x, x - 2.6], [y - 1, y - 6], color=NAVY, lw=1.5)
        ax.plot([x, x + 2.6], [y - 1, y - 6], color=NAVY, lw=1.5)
        ax.text(x, y - 9.6, n, ha="center", va="center", fontsize=8.6, color=INK, fontweight="bold")
    cases = {
        "uc1": (50, 56, "Check placement eligibility"),
        "uc2": (50, 49, "View skill-gap tips"),
        "uc3": (50, 42, "Get company-role recommendations"),
        "uc4": (36, 34, "Browse companies and cutoffs"),
        "uc5": (50, 28, "View model metrics and plots"),
        "uc6": (50, 21, "View placement statistics"),
        "uc7": (64, 14, "Shortlist students"),
        "uc8": (36, 14, "Toggle theme / command palette"),
        "uc9": (64, 36, "Retrain models (CLI scripts)"),
    }
    for k, (x, y, t) in cases.items():
        ax.add_patch(Ellipse((x, y), 24, 5.6, fc="#E8F0FC", ec=BLUE, lw=1.4))
        ax.text(x, y, t, ha="center", va="center", fontsize=7.3, color=INK)

    def link(a, c, side="r"):
        ax_, ay_ = acts[a][0], acts[a][1] + 1.8
        cx, cy, _ = cases[c][0], cases[c][1], 0
        ex = cx - 12 if ax_ < 50 else cx + 12
        ax.plot([ax_ + (3 if ax_ < 50 else -3), ex], [ay_, cy], color=SLATE, lw=1.0)

    for c in ("uc1", "uc2", "uc3", "uc4"):
        link("Student", c)
    for c in ("uc4", "uc5", "uc6", "uc3"):
        link("Placement officer", c)
    for c in ("uc7", "uc4", "uc6"):
        link("Recruiter", c)
    link("Developer\n(offline)", "uc9")
    arrow(ax, (50, 53.2), (50, 51.8), None, ls="--", color=ORANGE, head="->")
    ax.text(58.2, 52.8, "<<include>>", fontsize=6.6, color=ORANGE)
    arrow(ax, (50, 44.9), (50, 52.2), None, ls="--", color=ORANGE, head="-")
    ax.text(30.5, 24, "Shortlist, metrics and statistics are\nread from CSV/JSON; no login exists.", fontsize=7, color=SLATE, style="italic")
    save(fig, "08_use_case.png")




# ---------------------------------------------------------------- flowcharts
def decision(ax, cx, cy, w, h, text, fs=7.6, fc="#FFF8E5", ec=GOLD):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)


def terminal(ax, cx, cy, w, h, text, fc="#E6F6EF", ec=GREEN):
    box(ax, cx - w / 2, cy - h / 2, w, h, text, fc=fc, ec=ec, fs=8, rounding=h / 2, bold=True)


def flow_core():
    fig, ax = canvas(9, "Core algorithm - hybrid placement probability (serving time)", ty=102)
    terminal(ax, 50, 96, 44, 5, "Start: student profile, company, role")
    box(ax, 22, 84, 56, 7, "Build one feature row (24 features): frequency encoding of Branch, Company,\nRole, Degree, Student type; z-score of 19 numeric; gap features vs company cutoffs", fs=7.2)
    box(ax, 22, 72, 56, 7, "p = calibrated XGBoost probability (Platt / sigmoid, 3-fold)", fs=8)
    decision(ax, 50, 59, 50, 12, "borderline?\n0.4 <= p <= 0.6", fs=8)
    box(ax, 7, 41, 36, 8, "p_knn = kNN (k = 9) probability\nfrom 9 nearest training students\np = 0.5 p + 0.5 p_knn", fc="#EFE9FB", ec=PURPLE, fs=7.4)
    box(ax, 58, 41, 35, 8, "keep p (confident XGBoost\nprediction)", fs=7.6)
    decision(ax, 50, 27, 40, 11, "p >= 0.5 ?", fs=8)
    box(ax, 6, 8, 34, 8, "PLACEMENT READY\n(show probability)", fc="#E6F6EF", ec=GREEN, fs=8)
    box(ax, 60, 8, 34, 8, "NEEDS IMPROVEMENT\n+ skill-gap tips (cutoff rules)", fc="#FDECEA", ec="#C0504D", fs=8)
    terminal(ax, 50, 1.2, 14, 4, "End", fc="#EEF1F6", ec=SLATE)
    arrow(ax, (50, 93.5), (50, 91)); arrow(ax, (50, 84), (50, 79)); arrow(ax, (50, 72), (50, 65))
    arrow(ax, (25, 59), (25, 49), "yes", fs=8, lp=(22.5, 54), color=GREEN)
    arrow(ax, (75, 59), (75, 49), "no", fs=8, lp=(77.5, 54), color=ORANGE)
    arrow(ax, (25, 41), (40, 32.5)); arrow(ax, (75, 41), (60, 32.5))
    arrow(ax, (38, 27), (23, 16), "yes", fs=8, lp=(26, 23), color=GREEN); arrow(ax, (62, 27), (77, 16), "no", fs=8, lp=(74, 23), color=ORANGE)
    arrow(ax, (23, 8), (45, 3.3)); arrow(ax, (77, 8), (55, 3.3))
    save(fig, "10_core_algorithm_flowchart.png")


def flow_training():
    fig, ax = canvas(11.5, "Training pipeline (src/generate_dataset.py, preprocess.py, hybrid_model.py)", ty=50)
    steps = [("Synthetic data", "3,000 students\n30 companies\nlogit label model", NAVY),
             ("Stratified split", "70 / 15 / 15\n2,100 / 450 / 450\nseed 42", BLUE),
             ("Features", "fit freq maps + z-score\non train only\n24 features", ORANGE),
             ("6 baselines", "LogReg, Tree, RF,\nSVM, kNN, XGBoost\n9-fold CV (XGB)", PURPLE),
             ("Platt calibration", "CalibratedClassifierCV\nsigmoid, cv = 3\nBrier score", GREEN),
             ("Residual set R", "misclassified OR\n0.4 <= p <= 0.6\n(paper Eq. 1)", GOLD),
             ("Local models", "kNN (k=9), SVC rbf\nfit on all training\nrows", NAVY),
             ("Save + plots", "5 pickles, metrics.json\nSHAP, PCA,\nprobability histogram", BLUE)]
    w = 21.5
    for i, (t, s, c) in enumerate(steps):
        row_y = 26 if i < 4 else 4
        xx = 1.5 + (i % 4) * (w + 3.6)
        box(ax, xx, row_y, w, 15, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 10.6), w, 4.4, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 12.8, "%d  %s" % (i + 1, t), ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        ax.text(xx + w / 2, row_y + 5.0, s, ha="center", va="center", color=INK, fontsize=8, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 6), (xx + w + 3.6, row_y + 6))
    x4 = 1.5 + 3 * (w + 3.6) + w / 2
    ax.plot([x4, x4], [26, 23], color=SLATE, lw=1.4)
    ax.plot([x4, 1.5 + w / 2], [23, 23], color=SLATE, lw=1.4)
    arrow(ax, (1.5 + w / 2, 23), (1.5 + w / 2, 19.2))
    ax.text(50, 46.5, "Paper Eq. 1 selects the residual set with the TRUE test labels; the served model can only use the borderline rule (see Results).", ha="center", fontsize=8, color=ORANGE, style="italic")
    save(fig, "11_training_pipeline.png")


def flow_reco():
    fig, ax = canvas(9, "Recommendation algorithm (src/recommend.py)", ty=108)
    terminal(ax, 50, 103, 46, 4.6, "Start: profile, target company, role")
    box(ax, 18, 92, 64, 6, "base_p = predict_for(profile, target company, target role)  (0 if no target)", fs=7.6)
    box(ax, 18, 82, 64, 6, "for each of the 30 companies", fs=8, fc="#EEF1F6", ec=SLATE)
    decision(ax, 50, 70, 64, 11, "|CGPA - cutoff| <= delta_max(tier)  and\naptitude >= cutoff - 15  and  not (backlogs > 2 and Tier 1)\nand package >= minimum (if given)?", fs=6.8)
    box(ax, 70, 58, 28, 6, "skip company", fs=7.6, fc="#FDECEA", ec="#C0504D")
    box(ax, 4, 56, 56, 8, "proximity = max(0, 1 - gap / delta_max)\nfor role in {target role, SDE, Data Analyst, QA Engineer}:\n   p = predict_for(...)   score = p + 0.05 prox + 0.02 (location match)", fs=7, fc="#EFE9FB", ec=PURPLE)
    box(ax, 18, 42, 64, 7, "sort all candidates by score (descending)", fs=8)
    box(ax, 4, 28, 28, 9, "Company-only:\nbest role per company\n(top 5)", fs=7.4)
    box(ax, 36, 28, 28, 9, "Role-only:\ntarget company with\ndifferent roles (top 5)", fs=7.4)
    box(ax, 68, 28, 28, 9, "Hybrid:\nbest 5 company-role\npairs overall", fs=7.4, fc="#E6F6EF", ec=GREEN)
    box(ax, 12, 12, 76, 10, "improved = hybrid items with p > base_p\navg_gain = mean(p - base_p) over improved;  match_rate = |improved| / |hybrid|", fs=7.6)
    terminal(ax, 50, 4, 24, 4.6, "Return JSON", fc="#EEF1F6", ec=SLATE)
    arrow(ax, (50, 100.7), (50, 98)); arrow(ax, (50, 92), (50, 88)); arrow(ax, (50, 82), (50, 75.5))
    arrow(ax, (82, 70), (84, 64), "no", fs=8, color=ORANGE, lp=(86.5, 68))
    arrow(ax, (30, 64.5), (30, 64.0), None)
    arrow(ax, (30, 70), (30, 64), "yes", fs=8, color=GREEN, lp=(26, 66))
    arrow(ax, (32, 56), (45, 49), None); arrow(ax, (84, 58), (70, 49), None)
    arrow(ax, (50, 42), (18, 37), None); arrow(ax, (50, 42), (50, 37), None); arrow(ax, (50, 42), (82, 37), None)
    arrow(ax, (82, 28), (70, 22), None); arrow(ax, (50, 28), (50, 22), None); arrow(ax, (18, 28), (30, 22), None)
    arrow(ax, (50, 12), (50, 6.5))
    save(fig, "12_recommendation_flowchart.png")




if __name__ == "__main__":
    architecture(); workflow(); dfd0(); dfd1(); dfd2(); class_diagram(); sequence(); use_case(); er_diagram()
    flow_core(); flow_training(); flow_reco()
