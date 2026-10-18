"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does: app.py + pages/ (Streamlit), backend/ (FastAPI: main.py, auth.py,
state.py, helpers.py, config.py), src/ (pure-Python core) and frontend/ (React). There is no database,
so the ER diagram is the logical data model of the entities the code handles.
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
    """Work in a 100-wide coordinate space; the figure is cropped to its content when saved."""
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


# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11.5, "System architecture", ty=82)
    cols = ((1, 20, "Presentation"), (24, 24, "Application (FastAPI)"), (51, 29, "Core (src/, pure Python)"), (83, 16, "Data and state"))
    for x, w, label in cols:
        ax.add_patch(Rectangle((x, 6), w, 70, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 73.5, label, ha="center", fontsize=9.5, color=SLATE, fontweight="bold")
    box(ax, 2.5, 46, 17, 20, "React 19 SPA\n\"ChurnIQ\"\nVite, port 5314\n/api proxy\n\nDashboard, Data,\nExplore, Train,\nEvaluate, Risk, 360,\nExplain, What-if,\nRetention, Batch,\nMonitoring", fc="#E8F0FC", ec=BLUE, fs=7.2)
    box(ax, 2.5, 14, 17, 14, "Original Streamlit UI\napp.py + 13 pages/\nport 8501\n(same src/ core)", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    box(ax, 25.5, 51, 21, 15, "backend/main.py\n31 route handlers\nport 8314, /docs\nerrors 401/404/409/422", fc="#E6F6EF", ec=GREEN, fs=8)
    box(ax, 25.5, 37, 21, 11, "backend/auth.py\nHMAC-SHA256 bearer token\n12 h expiry, demo login", fc="#E6F6EF", ec=GREEN, fs=7.6)
    box(ax, 25.5, 23, 21, 11, "backend/state.py\nAppState (in memory)\ndataset, trial, active model", fc="#E6F6EF", ec=GREEN, fs=7.6)
    box(ax, 25.5, 10, 21, 10, "backend/helpers.py, config.py\nJSON conversion, .env", fc="#E6F6EF", ec=GREEN, fs=7.6)
    names = [("data_loader, eda", 63), ("preprocessing, train_models", 56), ("evaluation, explainability", 49),
             ("risk_segmentation, prediction", 42), ("retention_engine", 35), ("persistence, utils, sample_data", 28)]
    for t, y in names:
        box(ax, 52.5, y - 2.8, 26, 5.8, t, fc=PAPER, ec=NAVY, fs=7.8)
    ax.text(65.5, 12.5, "scikit-learn 1.9, pandas 3, numpy,\nimbalanced-learn (SMOTE), joblib;\nSHAP optional (not installed)", ha="center", va="center", fontsize=7.4, color=SLATE, style="italic")
    box(ax, 84.5, 56, 13, 12, "data/\ncustomer_\nchurn.csv\n(+ uploads)", fc="#FFF8E5", ec=GOLD, fs=7.6)
    box(ax, 84.5, 38, 13, 14, "models/\nmodel.pkl\npreprocessor.pkl\nmodel_\nmetadata.pkl", fc="#FFF8E5", ec=GOLD, fs=7.4)
    box(ax, 84.5, 20, 13, 14, "in-memory\nAppState\n(session only)\n+ .env demo\ncredentials", fc="#FFF8E5", ec=GOLD, fs=7.4)
    arrow(ax, (19.5, 58), (25.5, 58), "JSON\n(Bearer)", color=BLUE, off=(0, 3.4), fs=7)
    ax.plot([11, 11, 54.5], [14, 7.6, 7.6], color=ORANGE, lw=1.4, ls="--")
    arrow(ax, (54.5, 7.6), (54.5, 25.2), None, color=ORANGE, ls="--")
    ax.text(33, 4.6, "imports the same src/ modules directly", fontsize=7.2, color=ORANGE, ha="center")
    arrow(ax, (36, 51), (36, 48), None)
    arrow(ax, (36, 37), (36, 34), None)
    arrow(ax, (46.5, 58), (52.5, 49), "calls", off=(0, 3), fs=7.4, color=GREEN)
    arrow(ax, (78.5, 63), (84.5, 62), "read CSV", off=(0, 2.4), fs=7)
    arrow(ax, (78.5, 31), (84.5, 44), "joblib\nsave/load", off=(0.5, 3.8), fs=7)
    arrow(ax, (46.5, 24), (84.5, 24), "holds session state", lp=(70, 22.2), fs=7.2, ls="--")
    ax.text(50, 1.2, "State lives in memory; only the active model (models/*.pkl) survives a restart. No SQL database is used.", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11.5, "High-level workflow of a retention analysis", ty=46)
    steps = [
        ("1  Sign in", "demo account\nbearer token", NAVY),
        ("2  Load data", "sample (1,000 rows)\nor upload CSV", BLUE),
        ("3  Profile + prepare", "target / ID detection,\nduplicates, missing", ORANGE),
        ("4  Train + compare", "LR, DT, RF (+GB, HGB)\nclass weights / SMOTE", PURPLE),
        ("5  Evaluate + save", "acc, prec, recall, F1,\nROC-AUC; best on F1", GREEN),
        ("6  Score + segment", "probability %, risk bands\nLow / Med / High / Critical", GOLD),
        ("7  Explain + act", "drivers, what-if,\nretention rules", NAVY),
        ("8  Batch + monitor", "score a CSV, drift\ncheck, export", BLUE),
    ]
    w = 21.5
    for i, (t, s, c) in enumerate(steps):
        row_y = 24 if i < 4 else 4
        xx = 1.5 + (i % 4) * (w + 3.6)
        box(ax, xx, row_y, w, 14, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 9.6), w, 4.4, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 11.8, t, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        ax.text(xx + w / 2, row_y + 4.6, s, ha="center", va="center", color=INK, fontsize=8.6, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 6), (xx + w + 3.6, row_y + 6))
    x4 = 1.5 + 3 * (w + 3.6) + w / 2
    ax.plot([x4, x4], [24, 21], color=SLATE, lw=1.4)
    ax.plot([x4, 1.5 + w / 2], [21, 21], color=SLATE, lw=1.4)
    arrow(ax, (1.5 + w / 2, 21), (1.5 + w / 2, 18.2))
    ax.text(50, 41.2, "Steps 3 to 5 are re-run whenever new data or settings are chosen; the saved model (step 5) is restored automatically after a restart.",
            ha="center", fontsize=8.3, color=SLATE, style="italic")
    save(fig, "02_high_level_workflow.png")


# ---------------------------------------------------------------- DFD helpers
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


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(11.5, "Data flow diagram, level 0 (context)", ty=56)
    entity(ax, 2, 28, 17, 14, "Retention analyst\n(demo user)")
    entity(ax, 2, 6, 17, 10, "Customer data\nsource (CSV)")
    process(ax, 48, 35, 15, "ChurnIQ\nChurn Prediction\nSystem", "0", fs=9)
    store(ax, 70, 42, 28, 8, "working dataset (memory)", "D1")
    store(ax, 70, 26, 28, 8, "model files (models/*.pkl)", "D2")
    store(ax, 70, 10, 28, 8, "session state (memory)", "D3")
    arrow(ax, (19, 38.5), (33.3, 38.5), "credentials, settings, thresholds,\nwhat-if edits, batch CSV", off=(0, 5.0), fs=7.6)
    arrow(ax, (33.3, 31), (19, 31), "risk lists, metrics, explanations,\nretention actions, scored CSV", off=(0, -5.2), fs=7.6)
    arrow(ax, (19, 12), (37, 25), "customer CSV / sample", off=(-1, -3.2), fs=7.6)
    arrow(ax, (61, 42), (70, 45.5), "rows", off=(0, 2.4), fs=7.6)
    arrow(ax, (63, 34), (70, 30), "save / load model", off=(-0.5, 3.2), fs=7.4)
    arrow(ax, (58, 24.6), (70, 14), "config, trial, scores", off=(0.5, -3.2), fs=7.4)
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11.5, "Data flow diagram, level 1", ty=92)
    entity(ax, 1.5, 42, 12.5, 14, "Analyst")
    entity(ax, 1.5, 9, 12.5, 14, "Analyst*\n(same user)")
    entity(ax, 86, 6, 13, 12, "CSV\nsource")
    process(ax, 29, 82, 8, "Authenticate", "1.0")
    process(ax, 29, 49, 7.8, "Load, profile\nand prepare", "2.0", fs=7.6)
    process(ax, 52, 49, 8.2, "Train, evaluate\nand select", "3.0", fs=7.6)
    process(ax, 75, 49, 7.8, "Score and\nsegment risk", "4.0", fs=7.6)
    process(ax, 42, 15, 8.4, "Explain, what-if\nand retention", "5.0", fs=7.2)
    process(ax, 68, 15, 8.0, "Batch scoring\nand monitor", "6.0", fs=7.4)
    store(ax, 56, 76, 30, 8, "bearer token (client)", "D0")
    store(ax, 18, 64, 25, 8, "working dataset", "D1")
    store(ax, 47, 64, 26, 8, "trial results", "D3")
    store(ax, 70, 29, 28, 7, "model artefacts", "D2")
    arrow(ax, (8, 56), (22.5, 78), "login", lp=(11.5, 67), fs=7.4)
    arrow(ax, (37, 82), (56, 80.4), "signed token", off=(0, 2.4), fs=7.4)
    arrow(ax, (14, 49), (21.2, 49), "choice", off=(0, 2.4), fs=7.2)
    arrow(ax, (14, 17), (26, 43), "CSV file", lp=(11, 30), fs=7.4, rad=0.0, color=ORANGE)
    arrow(ax, (29, 56.8), (29, 64), "rows", off=(3, 0), fs=7.2)
    arrow(ax, (36.8, 49), (43.8, 49), "clean\nX, y", off=(0, 3.4), fs=7.0)
    arrow(ax, (52, 57.2), (52, 64), "metrics", off=(4.6, 0), fs=7.2)
    arrow(ax, (60.2, 49), (67.2, 49), "best\nmodel", off=(0, 3.4), fs=7.0)
    arrow(ax, (80, 41.5), (84, 36), "save /\nload", lp=(91, 40), fs=7.2)
    arrow(ax, (72, 41.2), (46, 22.6), "scores, model", lp=(63.5, 33.5), fs=7.2)
    arrow(ax, (14, 19), (33.6, 17), "customer id, thresholds,\nwhat-if edits", off=(-0.5, 4.6), fs=7.2)
    arrow(ax, (33.6, 11.5), (14, 13), "risk lists, explanations,\nactions", off=(0, -4.4), fs=7.2)
    arrow(ax, (86, 12), (76, 13.6), "batch CSV", off=(0, 2.4), fs=7.2, color=ORANGE)
    arrow(ax, (86, 33), (72, 22), "load model", lp=(86, 25), fs=7.2)
    arrow(ax, (68, 6.9), (8, 8.8), "scored CSV, drift report", lp=(38, 3.6), fs=7.2, rad=-0.1)
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(11.5, "Data flow diagram, level 2: process 3.0 (train, evaluate and select) expanded", ty=84)
    store(ax, 2, 70, 22, 8, "prepared dataset", "D1")
    xs = [10, 28.5, 47, 65.5]
    items = [("3.1", "Stratified\nsplit 80 / 20\nseed 42"), ("3.2", "Fit impute +\nscale + one-hot\non train only"), ("3.3", "Imbalance:\nclass weight /\nSMOTE / none"), ("3.4", "Fit selected\nmodels")]
    for (n, t), x in zip(items, xs):
        process(ax, x, 52, 7.4, t, n, fs=6.7)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.4, 52), (b - 7.4, 52), None)
    arrow(ax, (10, 70), (10, 59.4), "X, y", off=(3.4, 0), fs=7.4)
    process(ax, 84, 52, 7.4, "Evaluate\non test split", "3.5", fs=6.7)
    arrow(ax, (72.9, 52), (76.6, 52), None)
    process(ax, 84, 26, 7.4, "Select best\nby chosen\nmetric (F1)", "3.6", fs=6.7)
    arrow(ax, (84, 44.6), (84, 33.4), "metrics,\nCM, ROC, PR", off=(-8.6, 0), fs=7.2)
    process(ax, 64, 26, 7.4, "Save\nartefacts", "3.7", fs=7.0)
    arrow(ax, (76.6, 26), (71.4, 26), "name", off=(0, 2.4), fs=7.0)
    store(ax, 14, 28, 30, 8, "models/*.pkl", "D2")
    store(ax, 14, 6, 30, 8, "trial results (memory)", "D3")
    arrow(ax, (28.5, 44.6), (28.5, 36), "fitted\npreprocessor", off=(-7, 0), fs=7.0)
    arrow(ax, (56.6, 27.5), (44, 32), None)
    arrow(ax, (78, 20.6), (44, 10), "results table", lp=(64, 13.8), fs=7.2)
    ax.text(50, 1.5, "SMOTE is applied to the transformed training split only; the test split is never resampled.", ha="center", fontsize=8.2, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML class diagram
LH = 1.75


def uml_h(attrs, ops):
    return 6.4 + max(2.8, len(attrs) * LH + 1.4) + max(2.8, len(ops) * LH + 1.4)


def uml_class(ax, x, y, w, title, attrs, ops, stereo, hdr=BLUE, fs=6.9):
    h_title = 6.4
    h_attr = max(2.8, len(attrs) * LH + 1.4)
    h_ops = max(2.8, len(ops) * LH + 1.4)
    h = h_title + h_attr + h_ops
    ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=hdr, lw=1.5))
    ax.add_patch(Rectangle((x, y + h - h_title), w, h_title, fc=hdr, ec=hdr))
    ax.text(x + w / 2, y + h - 1.6, f"<<{stereo}>>", ha="center", va="center", color="white", fontsize=6.4)
    ax.text(x + w / 2, y + h - 4.4, title, ha="center", va="center", color="white", fontsize=8.2, fontweight="bold")
    ax.plot([x, x + w], [y + h_ops, y + h_ops], color=hdr, lw=1)
    for i, a in enumerate(attrs):
        ax.text(x + 1, y + h - h_title - 1.4 - i * LH, a, fontsize=fs, va="center", color=INK, family="DejaVu Sans Mono")
    for i, o in enumerate(ops):
        ax.text(x + 1, y + h_ops - 1.4 - i * LH, o, fontsize=fs, va="center", color=INK, family="DejaVu Sans Mono")
    return (x, y, w, h)


def uml():
    GAP = 4.5
    specs = {
        1: [("FastAPI routes", ["31 handlers under /api/*"], ["login, auth/me, state", "data: sample, upload, config,", "  quality, prepare, eda", "models: train, results, save", "evaluation, risk, customers", "xai, whatif, retention", "batch, monitoring, dashboard"], "backend/main.py", GREEN),
            ("AppState", ["dataset_name, raw_df, working_df", "target_col, id_col, feature_cols", "trial: dict", "model, preprocessor, explainer", "metadata, X_test_t, y_test", "risk_thresholds: dict"], ["restore_from_disk()", "has_model: bool", "model_features: list"], "dataclass, backend/state.py", GREEN),
            ("Auth", ["AUTH_SECRET, TOKEN_TTL = 12 h", "DEMO_EMAIL, DEMO_PASSWORD"], ["check_credentials(email, pw)", "make_token(email)", "read_token(token)", "require_user(Authorization)"], "module, backend/auth.py", GREEN)],
        2: [("DataLoader", ["DatasetProfile: n_rows, n_cols,", "  target_col, id_col, warnings"], ["load_csv(file)", "detect_target_column(df)", "profile_dataset(df)", "normalize_target(df, col)"], "module, data_loader.py", BLUE),
            ("Preprocessing", ["numeric: median + StandardScaler", "categorical: mode + OneHot"], ["clean_missing_and_duplicates(df)", "build_preprocessor(num, cat)", "train_test_split_data(X, y)", "apply_smote(X_t, y_t)"], "module", PURPLE),
            ("TrainModels", ["MODEL_REGISTRY: LR, DT, RF,", "  GB, HGB"], ["train_selected_models(X, y,", "  names, imbalance_strategy)", "select_best_model(res, metric)"], "module", PURPLE),
            ("Evaluation", ["accuracy, precision, recall,", "f1_score, roc_auc, cm, ROC, PR"], ["evaluate_model(model, X, y)", "results_to_table(results)"], "module", PURPLE),
            ("Persistence", ["models/model.pkl, preprocessor.pkl,", "  model_metadata.pkl"], ["save_artifacts(m, p, meta)", "load_artifacts()", "artifacts_exist()"], "module", PURPLE)],
        3: [("Prediction + Risk", ["thresholds 30 / 60 / 80"], ["score_customers(df, pre, model)", "build_batch_predictions(...)", "assign_risk_category(p, th)", "build_risk_table(...)"], "modules", ORANGE),
            ("Explainability", ["SHAP optional (not installed)"], ["global_importance(model, X, ...)", "local_explanation(expl, model, x)", "clean_feature_label(raw)"], "module", ORANGE),
            ("RetentionEngine", ["10 IF/THEN rules + 2 fallbacks"], ["generate_recommendations(", "  row, probability, band)", "recommendations_dataframe(...)"], "module", ORANGE)],
    }
    xs = {1: (1, 30), 2: (36, 29), 3: (70, 29)}
    heights = {c: sum(uml_h(s[1], s[2]) for s in v) + GAP * (len(v) - 1) for c, v in specs.items()}
    H = max(heights.values()) + 10
    fig, ax = canvas(12.5, "UML class diagram (modules of src/ and backend/ drawn as classes)", ty=H + 6, top=H + 8)
    boxes = {}
    for c, v in specs.items():
        y = H - 2
        for (title, at, op, st, col) in v:
            h = uml_h(at, op)
            y -= h
            boxes[title] = uml_class(ax, xs[c][0], y, xs[c][1], title, at, op, st, col)
            y -= GAP
    def edge(a, side, b, side_b, label=None, **kw):
        ba, bb = boxes[a], boxes[b]
        pa = mid(ba, side); pb = mid(bb, side_b)
        arrow(ax, pa, pb, label, **kw)
    edge("FastAPI routes", "b", "AppState", "t", "owns", off=(3.5, 0), fs=7)
    edge("AppState", "b", "Auth", "t", None)
    edge("FastAPI routes", "r", "DataLoader", "l", "calls", color=GREEN, off=(0, 1.5), fs=7)
    edge("AppState", "r", "Preprocessing", "l", "holds fitted\npreprocessor", off=(0, 2.6), fs=6.8)
    edge("Preprocessing", "b", "TrainModels", "t", "X, y", off=(3, 0), fs=7)
    edge("TrainModels", "b", "Evaluation", "t", "models", off=(3.6, 0), fs=7)
    edge("Evaluation", "b", "Persistence", "t", "best model", off=(4.4, 0), fs=7, ls="--")
    edge("Preprocessing", "r", "Prediction + Risk", "l", "scores with the\nfitted preprocessor", off=(-1, 3), fs=6.8, ls="--", rad=-0.05)
    edge("Prediction + Risk", "b", "Explainability", "t", None)
    edge("Explainability", "b", "RetentionEngine", "t", "drivers,\nband", off=(4.6, 0), fs=7)
    ax.text(1, 1.5, "Solid arrow = uses / owns; dashed = data flow. The code is function-oriented, so modules are drawn as classes (<<module>>).", fontsize=7.6, color=SLATE, style="italic")
    save(fig, "06_uml_class_diagram.png")


# ---------------------------------------------------------------- 07 sequence diagram
def sequence():
    fig, ax = canvas(11.5, "Sequence diagram: train, save and explain a customer", ty=94, top=96)
    names = ["Analyst", "React SPA", "FastAPI\nmain.py", "AppState", "src/ core", "models/\n*.pkl"]
    xs = [8, 24, 42, 58, 75, 92]
    cols = [ORANGE, BLUE, GREEN, GREEN, PURPLE, GOLD]
    for x, n, c in zip(xs, names, cols):
        box(ax, x - 7, 83, 14, 6, n, fc="white", ec=c, lw=1.8, fs=8.2, bold=True)
        ax.plot([x, x], [83, 4], color="#CBD5E1", lw=1, ls="--")
    msgs = [
        (0, 1, 80, "sign in (demo email, password)", False),
        (1, 2, 76.5, "POST /api/auth/login", False),
        (2, 1, 73, "bearer token (HMAC, 12 h)", True),
        (1, 2, 69.5, "POST /api/data/sample, /api/data/prepare", False),
        (2, 4, 66, "generate_sample / clean / detect types", False),
        (2, 3, 62.5, "store working_df, feature columns", False),
        (1, 2, 59, "POST /api/models/train (models, strategy)", False),
        (2, 4, 55.5, "split, fit preprocessor, train, evaluate", False),
        (4, 2, 52, "metrics + best model name", True),
        (2, 3, 48.5, "keep trial results", False),
        (1, 2, 45, "POST /api/models/save {name}", False),
        (2, 5, 41.5, "save_artifacts (joblib)", False),
        (2, 1, 38, "saved + metadata", True),
        (0, 1, 34.5, "open Customer 360 for an id", False),
        (1, 2, 31, "GET /api/customers/{id}", False),
        (2, 3, 27.5, "read active model, thresholds", False),
        (2, 4, 24, "score, risk band, local explanation, rules", False),
        (4, 2, 20.5, "probability, drivers, actions", True),
        (2, 1, 17, "JSON: risk, drivers, retention actions", True),
        (1, 0, 13.5, "profile card, drivers, retention steps", True),
    ]
    for a, b, y, t, ret in msgs:
        arrow(ax, (xs[a], y), (xs[b], y), None, color=SLATE, ls="--" if ret else "-", lw=1.2)
        ax.text((xs[a] + xs[b]) / 2, y + 0.9, t, ha="center", va="bottom", fontsize=7.2, color=INK)
    ax.text(50, 7.2, "Errors: missing / expired token -> 401; nothing prepared or no model -> 409; invalid settings -> 422; unknown customer -> 404.", ha="center", fontsize=7.8, color=SLATE, style="italic")
    save(fig, "07_sequence_diagram.png")


# ---------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(11.5, "Use-case diagram", ty=70, top=72)
    ax.add_patch(Rectangle((19, 3), 62, 62, fc="#FBFCFE", ec=LINE, lw=1.4))
    ax.text(50, 62.4, "ChurnIQ (system boundary)", ha="center", fontsize=10, fontweight="bold", color=SLATE)
    left = ["Sign in (demo account)", "Review data quality", "Train and compare models", "View portfolio dashboard", "List customers by risk", "Explain drivers (global / local)", "Get retention actions", "Monitor model and data drift"]
    right = ["Load sample data or upload CSV", "Explore churn patterns (EDA)", "Evaluate and save best model", "Edit risk thresholds", "Open Customer 360", "Run what-if scenario", "Batch-score a CSV"]

    def actor(cx, label):
        ax.add_patch(Circle((cx, 40), 2.2, fc="white", ec=ORANGE, lw=1.8))
        ax.plot([cx, cx], [37.8, 31], color=ORANGE, lw=1.8)
        ax.plot([cx - 3.6, cx + 3.6], [35, 35], color=ORANGE, lw=1.8)
        ax.plot([cx, cx - 3.6], [31, 25.5], color=ORANGE, lw=1.8)
        ax.plot([cx, cx + 3.6], [31, 25.5], color=ORANGE, lw=1.8)
        ax.text(cx, 23, label, ha="center", va="top", fontsize=7.6, fontweight="bold", color=INK)

    actor(9, "Retention analyst /\ndata scientist\n(shared demo account)")
    actor(91, "Same user\n(drawn again\nfor clarity)")
    for i, t in enumerate(left):
        cy = 55 - i * 6.6
        ax.add_patch(Ellipse((35, cy), 24, 5.6, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(35, cy, t, ha="center", va="center", fontsize=7.3, color=INK)
        ax.plot([13, 23], [34, cy], color="#94A3B8", lw=0.8)
    for i, t in enumerate(right):
        cy = 55 - i * 6.6
        ax.add_patch(Ellipse((65, cy), 24, 5.6, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(65, cy, t, ha="center", va="center", fontsize=7.3, color=INK)
        ax.plot([87, 77], [34, cy], color="#94A3B8", lw=0.8)
    ax.text(50, 0.8, "Sign in precedes every other use case; training precedes save, risk, explain, what-if and retention.", ha="center", fontsize=7.4, color=SLATE, style="italic")
    save(fig, "08_use_case_diagram.png")


# ---------------------------------------------------------------- 09 ER (logical)
def er():
    fig, ax = canvas(11.5, "Entity-relationship diagram (logical data model: CSV + joblib + in-memory state)", ty=94, top=96)

    def ent(x, y, w, name, attrs, color=BLUE):
        lh = 3.0
        h = 5 + len(attrs) * lh
        ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=color, lw=1.6))
        ax.add_patch(Rectangle((x, y + h - 5), w, 5, fc=color, ec=color))
        ax.text(x + w / 2, y + h - 2.5, name, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        for i, a in enumerate(attrs):
            ax.text(x + 1.2, y + h - 5 - 1.8 - i * lh, a, fontsize=7.2, va="center", color=INK, family="DejaVu Sans Mono")
        return (x, y, w, h)

    ent(2, 66, 27, "DATASET", ["PK dataset_name", "   n_rows, n_cols", "   target_col (Churn)", "   id_col (customerID)", "   numeric_cols[4]", "   categorical_cols[15]"], BLUE)
    ent(37, 66, 26, "TRIAL_RUN", ["PK model_name", "   strategy, test_size", "   accuracy, precision", "   recall, f1_score", "   roc_auc, cm, fit_secs"], PURPLE)
    ent(72, 66, 26, "MODEL_ARTEFACT", ["PK model_name", "   model.pkl", "   preprocessor.pkl", "   model_metadata.pkl", "   feature_cols, metrics"], GOLD)
    ent(2, 24, 27, "CUSTOMER", ["PK customerID", "   gender, SeniorCitizen", "   Partner, Dependents", "   tenure, Contract", "   InternetService, add-ons", "   MonthlyCharges", "   TotalCharges, PaymentMethod", "   Churn (Yes/No)"], BLUE)
    ent(37, 32, 26, "RISK_RECORD", ["PK,FK customerID", "FK model_name", "   probability (0-100)", "   risk_band", "   top drivers (5+ / 5-)"], ORANGE)
    ent(72, 35, 26, "RISK_THRESHOLDS", ["PK scope (session)", "   low = 30", "   medium = 60", "   high = 80"], GREEN)
    ent(37, 8, 26, "RECOMMENDATION", ["PK,FK customerID", "PK rule_id", "   action, priority", "   rationale"], GREEN)
    arrow(ax, (29, 77), (37, 77), None, head="-")
    ax.text(33, 79.6, "1 : N", fontsize=7.2, color=SLATE, ha="center")
    ax.text(33, 74.2, "trained on", fontsize=6.8, color=SLATE, ha="center")
    arrow(ax, (63, 77), (72, 77), None, head="-")
    ax.text(67.5, 79.6, "1 : 0..1", fontsize=7.2, color=SLATE, ha="center")
    ax.text(67.5, 74.2, "select + save", fontsize=6.8, color=SLATE, ha="center")
    arrow(ax, (15.5, 66), (15.5, 53), None, head="-")
    ax.text(17, 59.5, "1 : N  contains", fontsize=7.2, color=SLATE)
    arrow(ax, (29, 42), (37, 42), None, head="-")
    ax.text(33, 44.5, "1 : 1", fontsize=7.2, color=SLATE, ha="center")
    ax.text(33, 39.4, "is scored", fontsize=6.8, color=SLATE, ha="center")
    arrow(ax, (72, 42), (63, 42), None, head="-")
    ax.text(67.5, 44.8, "N : 1", fontsize=7.2, color=SLATE, ha="center")
    ax.text(67.5, 39.4, "band from", fontsize=6.8, color=SLATE, ha="center")
    arrow(ax, (85, 66), (60, 52), None, head="-")
    ax.text(77.5, 58.6, "1 : N  scores", fontsize=7.2, color=SLATE)
    arrow(ax, (50, 32), (50, 25), None, head="-")
    ax.text(52, 28.5, "1 : N  has actions", fontsize=7.2, color=SLATE, va="center")
    ax.text(50, 2.5, "There is no SQL database: DATASET and CUSTOMER are CSV / DataFrame, TRIAL_RUN and RISK_RECORD are in memory, MODEL_ARTEFACT is on disk (joblib).",
            ha="center", fontsize=7.4, color=SLATE, style="italic")
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 core algorithm flowchart
def diamond(ax, cx, cy, w, h, text, fc="#FFF8E5", ec=GOLD, fs=8):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)


def terminator(ax, cx, cy, w, h, text):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=NAVY, ec=NAVY))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")


def flowchart():
    fig, ax = canvas(8.4, "Core algorithm: train, select, score and recommend", ty=137, top=139)
    cx, d = 46, 10

    def Y(v):
        return v + d

    terminator(ax, cx, Y(122), 22, 5, "Start")
    box(ax, cx - 17, Y(110), 34, 7, "Load CSV or sample; detect Churn\nand ID columns; drop duplicates", fs=7.8)
    diamond(ax, cx, Y(98), 36, 11, "Validation passes?\n(2 classes, rows,\ntarget present)", fs=7.4)
    box(ax, cx - 17, Y(82), 34, 7, "Stratified split 80/20 (seed 42);\nfit imputer + scaler + one-hot on train", fs=7.6)
    diamond(ax, cx, Y(70), 36, 11, "Imbalance strategy?", fs=7.8)
    box(ax, 69, Y(64), 28, 12, "class_weight='balanced'\n(LR, DT, RF) or SMOTE\non train only or none", fs=7.2)
    box(ax, cx - 17, Y(53), 34, 7, "Fit each selected model;\npredict test split", fs=7.8)
    box(ax, cx - 17, Y(41), 34, 7, "Accuracy, precision, recall, F1,\nROC-AUC, confusion matrix", fs=7.8)
    box(ax, cx - 17, Y(29), 34, 7, "Select best model by chosen\nmetric (default F1); save .pkl", fs=7.8)
    box(ax, cx - 17, Y(17), 34, 7, "Score: P(churn) = predict_proba x 100;\nrisk band from 30 / 60 / 80", fs=7.6)
    diamond(ax, cx, Y(6), 34, 9, "P >= 60 or Critical?", fs=7.6)
    box(ax, 68, Y(0.5), 30, 11, "Apply rules (contract, tech support,\nsecurity, charges, e-check,\ntenure, fibre ...) -> actions", fs=6.9)
    terminator(ax, cx, Y(-6), 22, 5, "End")
    box(ax, 1, Y(92), 20, 10, "Show errors;\nstop (HTTP 422)", fc="#FFF1EA", ec=ORANGE, fs=7.4)
    for y0, y1 in ((119.5, 117), (110, 103.5), (92.5, 89), (82, 75.5), (64.5, 60), (53, 48), (41, 36), (29, 24), (17, 10.5)):
        arrow(ax, (cx, Y(y0)), (cx, Y(y1)), None)
    ax.text(cx + 2, Y(90.8), "yes", fontsize=7.4, color=GREEN)
    arrow(ax, (cx - 18, Y(98)), (21, Y(97)), "no", off=(0, 1.8), fs=7.4, color=ORANGE)
    arrow(ax, (cx + 18, Y(70)), (69, Y(70)), "any", off=(0, 1.8), fs=7.2)
    arrow(ax, (83, Y(64)), (cx + 17, Y(56.5)), None, rad=-0.2)
    arrow(ax, (cx + 17, Y(6)), (68, Y(6)), "yes", off=(0, 1.8), fs=7.4, color=GREEN)
    arrow(ax, (83, Y(0.5)), (cx + 11, Y(-6)), None, rad=0.25)
    arrow(ax, (cx, Y(1.5)), (cx, Y(-3.5)), "no: generic message", off=(-13, 0.4), fs=7.0)
    save(fig, "10_core_algorithm_flowchart.png")


if __name__ == "__main__":
    architecture()
    workflow()
    dfd0()
    dfd1()
    dfd2()
    uml()
    sequence()
    use_case()
    er()
    flowchart()
