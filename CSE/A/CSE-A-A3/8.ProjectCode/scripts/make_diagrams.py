"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does: generate_data.py (synthetic CSVs) -> train_models.py (4 models x 4 diseases,
best by F1, saved to models/) -> app.py (model bundles, field metadata, report) -> backend/main.py (FastAPI, 7 routes,
port 8303) -> frontend/ (React + Vite, port 5303).  There is no database, no authentication and no stored patient
data, so the ER diagram is the logical data model of the files and transient objects the code handles.
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


def mid(b, side):
    x, y, w, h = b
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]


# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11.5, "System architecture", ty=82)
    # offline band
    ax.add_patch(Rectangle((0.5, 54), 99, 24, fc="#FFFDF5", ec="#E8D9A8", lw=1, ls="--"))
    ax.text(2, 76, "Offline pipeline (run once by a developer)", fontsize=9, color=SLATE, fontweight="bold", va="center")
    gen = box(ax, 2, 57, 21, 14, "generate_data.py\n4 synthetic CSVs\nN = 2,000, seed 42\n8 % label noise", fc="#FFF1EA", ec=ORANGE, fs=8)
    csv = box(ax, 28, 57, 20, 14, "data/\ndiabetes.csv, heart.csv,\nliver.csv, kidney.csv\n(2,000 rows each)", fc="#FFF8E5", ec=GOLD, fs=8)
    trn = box(ax, 53, 57, 22, 14, "train_models.py\n4 models x 4 diseases\nStandardScaler, 80/20 split\nbest by F1", fc="#EFEAFB", ec=PURPLE, fs=8)
    mdl = box(ax, 79, 57, 20, 14, "models/\n12 x *.pkl (model,\nscaler, features) +\ntraining_report.json", fc="#FFF8E5", ec=GOLD, fs=8)
    arrow(ax, (23, 64), (28, 64))
    arrow(ax, (48, 64), (53, 64), "read")
    arrow(ax, (75, 64), (79, 64), "save")
    # online row
    ax.add_patch(Rectangle((0.5, 4), 99, 46, fc="#FBFCFE", ec="#D5DCE6", lw=1))
    ax.text(2, 47.5, "Online application (run.bat: API on 8303, web app on 5303)", fontsize=9, color=SLATE, fontweight="bold", va="center")
    rea = box(ax, 2, 24, 21, 18, "React 19 SPA (Vite)\nport 5303\nLanding, Overview,\nPredict (x4), Models,\nDatasets, About, 404", fc="#E8F0FC", ec=BLUE, fs=8)
    fla = box(ax, 2, 7, 21, 11, "Original Flask pages\nport 5000 (index.html,\npredict.html)", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    api = box(ax, 28, 24, 21, 18, "backend/main.py\nFastAPI, port 8303\n7 routes /api/*\nCORS: localhost:5303\nPredictBody validation", fc="#E6F6EF", ec=GREEN, fs=8)
    app = box(ax, 53, 24, 22, 18, "app.py (imported,\nnot modified)\nBUNDLES, FIELD_META,\nDISEASE_TITLES,\nTRAINING_REPORT", fc="#E6F6EF", ec=GREEN, fs=8)
    skl = box(ax, 79, 24, 20, 18, "scikit-learn 1.8.0\nStandardScaler.transform\nmodel.predict /\npredict_proba", fc=PAPER, ec=NAVY, fs=8)
    arrow(ax, (23, 33), (28, 33), "JSON /\nHTTP", off=(0, 3.2), fs=7.4, color=BLUE)
    arrow(ax, (49, 33), (53, 33), "import", off=(0, 2.2), fs=7.4, color=GREEN)
    arrow(ax, (75, 33), (79, 33), "call", off=(0, 2.2), fs=7.4, color=GREEN)
    arrow(ax, (23, 12.5), (58, 24), "same bundles, same maths", lp=(40, 14), fs=7.4, color=ORANGE, ls="--")
    arrow(ax, (38.5, 42), (38.5, 57), "samples,\ndataset counts", lp=(38.5, 52.2), fs=7.2)
    arrow(ax, (66, 42), (84, 57), "load pickles\nat start-up", lp=(79, 52.4), fs=7.2)
    ax.text(50, 1.2, "No SQL database, no authentication, no stored patient data: a prediction is computed from the request and returned.",
            ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11.5, "High-level workflow of the Multi-Disease Prediction system", ty=46)
    steps = [
        ("1  Generate data", "generate_data.py:\n4 CSVs, 2,000 rows each", ORANGE),
        ("2  Train + compare", "LR, DT, RF, SVM per\ndisease, 80/20 split", PURPLE),
        ("3  Select + save", "best F1 per disease;\nmodels/*.pkl + report", GOLD),
        ("4  Start the API", "load 4 bundles, field\nmetadata, report (8303)", GREEN),
        ("5  Choose disease", "diabetes, heart, liver\nor kidney form (5303)", BLUE),
        ("6  Enter values", "or load a real CSV row\n(positive / negative)", BLUE),
        ("7  Predict", "validate, scale, model\npredict + confidence", GREEN),
        ("8  Show result", "class, confidence, model,\nhold-out accuracy", NAVY),
    ]
    w = 21.5
    for i, (t, s, c) in enumerate(steps):
        row_y = 24 if i < 4 else 4
        xx = 1.5 + (i % 4) * (w + 3.6)
        box(ax, xx, row_y, w, 14, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 9.6), w, 4.4, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 11.8, t, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        ax.text(xx + w / 2, row_y + 4.6, s, ha="center", va="center", color=INK, fontsize=8.4, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 6), (xx + w + 3.6, row_y + 6))
    x4 = 1.5 + 3 * (w + 3.6) + w / 2
    ax.plot([x4, x4], [24, 21], color=SLATE, lw=1.4)
    ax.plot([x4, 1.5 + w / 2], [21, 21], color=SLATE, lw=1.4)
    arrow(ax, (1.5 + w / 2, 21), (1.5 + w / 2, 18.2))
    ax.text(50, 41.2, "Steps 1 to 3 are offline and are re-run only to regenerate data or retrain; steps 4 to 8 repeat for every prediction request.",
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


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(11.5, "Data flow diagram, level 0 (context)", ty=56)
    entity(ax, 2, 34, 17, 14, "User\n(patient or\nclinician)")
    entity(ax, 2, 6, 17, 12, "Developer /\ntrainer")
    process(ax, 48, 35, 15, "Multi-Disease\nPrediction\nSystem", "0", fs=9)
    store(ax, 70, 42, 28, 8, "data/*.csv (4 datasets)", "D1")
    store(ax, 70, 24, 28, 9, "models/*.pkl +\ntraining_report.json", "D2")
    arrow(ax, (19, 44), (34, 40), "disease choice, patient\nvalues, sample request", lp=(24, 49.5), fs=7.6)
    arrow(ax, (33.5, 33), (19, 37.5), "risk class, confidence,\nmodel, accuracy,\nmetrics, dataset facts", lp=(25, 29.3), fs=7.6)
    arrow(ax, (19, 14), (38, 26), "run generate_data.py,\ntrain_models.py", lp=(21, 24.6), fs=7.6, color=ORANGE)
    arrow(ax, (38, 23.5), (19, 10), "training report\n(console + JSON)", lp=(33, 11), fs=7.6, color=ORANGE)
    arrow(ax, (63, 42), (70, 45.5), "rows", off=(-0.5, 2.4), fs=7.6)
    arrow(ax, (63, 32), (70, 29), "load / save\nmodels", off=(0, 3.4), fs=7.4)
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11.5, "Data flow diagram, level 1", ty=88, top=90)
    entity(ax, 1.5, 61, 13, 13, "Developer")
    entity(ax, 1.5, 10, 13, 40, "User")
    process(ax, 42, 66, 8.2, "Generate\ndatasets", "1.0", fs=7.8)
    store(ax, 57, 62, 22, 8, "data/*.csv", "D1")
    process(ax, 91, 66, 8.2, "Train and\nselect models", "2.0", fs=7.4)
    store(ax, 66, 41, 32, 8, "models/*.pkl, report", "D2")
    process(ax, 42, 44, 8.2, "Serve metadata\nand samples", "3.0", fs=7.2)
    process(ax, 42, 16, 8.2, "Predict\nrisk", "4.0", fs=8.4)
    arrow(ax, (14.5, 67.5), (33.8, 67.5), "run generate_data.py,\ntrain_models.py", lp=(24, 71.8), fs=7.2, color=ORANGE)
    arrow(ax, (50.2, 66), (57, 66), None)
    arrow(ax, (79, 66), (82.8, 66), None)
    ax.text(81, 69.4, "X, y", fontsize=7.4, color=SLATE, ha="center")
    arrow(ax, (91, 57.8), (91, 49), "pickles,\nreport", lp=(95.5, 53.4), fs=7.2)
    arrow(ax, (91, 74.2), (8, 74.2), "training report (console + JSON)", lp=(50, 83.5), fs=7.6, color=ORANGE, rad=0.2)
    arrow(ax, (14.5, 46.5), (34.2, 47.5), "choose disease,\nsample request", lp=(24, 52), fs=7.2)
    arrow(ax, (34.2, 40.5), (14.5, 40), "form fields,\nmetrics, samples", lp=(24, 35.5), fs=7.2)
    arrow(ax, (14.5, 19), (33.8, 19), "disease +\npatient values", lp=(24, 23.6), fs=7.2, color=BLUE)
    arrow(ax, (33.8, 13), (14.5, 13), "risk class, confidence,\nmodel, accuracy", lp=(24, 8.2), fs=7.2, color=BLUE)
    arrow(ax, (47, 51.5), (62, 61.8), "read rows", lp=(50, 57.6), fs=7.4)
    arrow(ax, (50.2, 44.5), (66, 45), "report, bundles", lp=(58.5, 47.4), fs=7.4)
    arrow(ax, (49, 20), (73, 40.8), "model, scaler", lp=(63, 27.5), fs=7.4)
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(11.5, "Data flow diagram, level 2: process 4.0 (predict risk) expanded", ty=70, top=72)
    entity(ax, 1.5, 33, 12, 12, "User")
    xs = [27, 46, 65, 84]
    items = [("4.1", "Validate\ndisease key"), ("4.2", "Convert\nvalues to\nnumbers"), ("4.3", "Scale with\nsaved\nStandardScaler"), ("4.4", "Predict class\n+ confidence")]
    for (n, t), x in zip(items, xs):
        process(ax, x, 39, 7.8, t, n, fs=6.9)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.8, 39), (b - 7.8, 39), None)
    arrow(ax, (13.5, 39), (19.2, 39), None)
    ax.text(14.2, 35.6, "disease +\nvalues", fontsize=7.2, color=SLATE, ha="left", va="center")
    process(ax, 84, 18, 7.8, "Format\nresult", "4.5", fs=7.2)
    arrow(ax, (84, 31.2), (84, 25.8), None)
    ax.text(85.6, 28.6, "class,\nprobabilities", fontsize=7.2, color=SLATE, ha="left", va="center")
    store(ax, 20, 8, 52, 8, "model, scaler, features (from the saved bundle)", "D2")
    arrow(ax, (46, 16), (46, 31.2), "feature order", lp=(46, 23.5), fs=7.2)
    arrow(ax, (65, 16), (65, 31.2), "scaler", lp=(65, 23.5), fs=7.2)
    arrow(ax, (70, 16), (79.4, 32.2), "model", lp=(70.2, 25.5), fs=7.2)
    ax.plot([84, 84, 7.5], [10.2, 4.6, 4.6], color=BLUE, lw=1.4)
    arrow(ax, (7.5, 4.6), (7.5, 33), None, color=BLUE)
    ax.text(45, 4.6, "JSON: result, probability, model, accuracy", fontsize=7.4, color=BLUE, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.6))
    arrow(ax, (27, 46.8), (10, 45), "404 unknown disease", lp=(13, 55.5), fs=7.4, color=ORANGE, rad=0.3)
    arrow(ax, (46, 46.8), (4.5, 45), "422 missing / non-finite value", lp=(34, 59.5), fs=7.4, color=ORANGE, rad=0.3)
    ax.text(50, 0.2, "Validation happens twice: the React form checks required / numeric fields, and the API checks the disease key and every value.", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML class diagram
LH = 1.85


def uml_h(attrs, ops):
    return 6.4 + max(2.8, len(attrs) * LH + 1.4) + max(2.8, len(ops) * LH + 1.4)


def uml_class(ax, x, y, w, title, attrs, ops, stereo, hdr=BLUE, fs=6.9):
    h_title = 6.4
    h_attr = max(2.8, len(attrs) * LH + 1.4)
    h_ops = max(2.8, len(ops) * LH + 1.4)
    h = h_title + h_attr + h_ops
    ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=hdr, lw=1.5))
    ax.add_patch(Rectangle((x, y + h - h_title), w, h_title, fc=hdr, ec=hdr))
    ax.text(x + w / 2, y + h - 1.6, f"<<{stereo}>>", ha="center", va="center", color="white", fontsize=6.6)
    ax.text(x + w / 2, y + h - 4.4, title, ha="center", va="center", color="white", fontsize=8.2, fontweight="bold")
    ax.plot([x, x + w], [y + h_ops, y + h_ops], color=hdr, lw=1)
    for i, a in enumerate(attrs):
        ax.text(x + 1, y + h - h_title - 1.4 - i * LH, a, fontsize=fs, va="center", color=INK, family="DejaVu Sans Mono")
    for i, o in enumerate(ops):
        ax.text(x + 1, y + h_ops - 1.4 - i * LH, o, fontsize=fs, va="center", color=INK, family="DejaVu Sans Mono")
    return (x, y, w, h)


def uml():
    GAP = 6
    specs = {
        1: [("FastAPI routes", ["BUNDLES, FIELD_META, TITLES,", "REPORT   (taken from app.py)", "DATA: {disease: DataFrame}", "TARGETS: {disease: column}"],
             ["health()", "diseases()", "disease(d)", "sample(d, outcome)", "predict(d, body)", "report()", "datasets()", "_check(d)  -> 404", "_fields(d), _summary(d)"], "module, backend/main.py", GREEN),
            ("PredictBody", ["values: dict[str, float|int|", "         str|None]"], ["(pydantic validation of", " the JSON body)"], "pydantic BaseModel", GREEN)],
        2: [("app.py", ["TRAINING_REPORT: dict", "BUNDLES: {disease: ModelBundle}", "FIELD_META: {disease: {feature:", "   (label, placeholder, kind)}}", "DISEASE_TITLES: dict"],
             ["load_bundle(disease)", "handle_prediction(disease)", "home(), diabetes(), heart(),", "  liver(), kidney()   (Flask)"], "module (Flask app)", BLUE),
            ("ModelBundle", ["model: fitted estimator", "scaler: StandardScaler", "features: list[str]"], ["(a 3-tuple read from", " models/<d>_*.pkl)"], "tuple, one per disease", GOLD)],
        3: [("Estimators", ["LogisticRegression(max_iter=1000)", "DecisionTreeClassifier(max_depth=6)", "RandomForestClassifier(200, depth 8)", "SVC(kernel='rbf', C=1,", "    probability=True)"],
             ["fit(X, y)", "predict(X)", "predict_proba(X)"], "scikit-learn", PURPLE),
            ("train_models.py", ["DISEASES: csv, target, features", "MODEL_BUILDERS: 4 factories", "RANDOM_STATE = 42"],
             ["(script) per disease: split,", " scale, fit 4 models, score,", " pick max F1, joblib.dump,", " write training_report.json"], "script", PURPLE),
            ("generate_data.py", ["N = 2000, seed 42"], ["generate_diabetes() ...", "generate_heart() ...", "generate_liver() ...", "generate_kidney() ...", "add_noise_labels(risk, 0.08)"], "script", ORANGE)],
    }
    xs = {1: (1, 28), 2: (37, 28), 3: (71, 29)}
    heights = {c: sum(uml_h(s[1], s[2]) for s in v) + GAP * (len(v) - 1) for c, v in specs.items()}
    H = max(heights.values()) + 8
    fig, ax = canvas(12.5, "UML class diagram (modules, tuples and scikit-learn classes of the project)", ty=H + 6, top=H + 8)
    boxes = {}
    for c, v in specs.items():
        y = H - 2
        for (title, at, op, st, col) in v:
            h = uml_h(at, op)
            y -= h
            boxes[title] = uml_class(ax, xs[c][0], y, xs[c][1], title, at, op, st, col, fs=6.7)
            y -= GAP

    def pt(name, side, dy=0.0):
        x, y, w, h = boxes[name]
        px, py = mid(boxes[name], side)
        return (px, py + dy)

    arrow(ax, pt("FastAPI routes", "r", 6), pt("app.py", "l", 6), "imports", color=GREEN, off=(0, 2.2), fs=7)
    arrow(ax, pt("FastAPI routes", "b"), pt("PredictBody", "t"), "uses", off=(3, 0), fs=7)
    arrow(ax, pt("app.py", "b"), pt("ModelBundle", "t"), "BUNDLES holds 4", off=(7.5, 0), fs=7)
    arrow(ax, (boxes["ModelBundle"][0] + boxes["ModelBundle"][2], boxes["ModelBundle"][1] + boxes["ModelBundle"][3] - 3),
          (boxes["Estimators"][0], boxes["Estimators"][1] + 4), "contains one", lp=(66.5, 66), fs=7, color=GOLD)
    arrow(ax, pt("train_models.py", "l", -2), (boxes["ModelBundle"][0] + boxes["ModelBundle"][2], boxes["ModelBundle"][1] + 4),
          "writes pickles", lp=(66.5, 48), fs=7, ls="--", color=PURPLE)
    arrow(ax, pt("train_models.py", "t"), pt("Estimators", "b"), "builds 4", off=(4, 0), fs=7, color=PURPLE)
    arrow(ax, pt("generate_data.py", "t"), pt("train_models.py", "b"), "CSV files", off=(4, 0), fs=7, color=ORANGE)
    ax.text(1, 1.5, "The code is function-oriented, so modules, tuples and dictionaries are drawn as classes (stereotype in << >>). "
            "Solid arrow = uses / contains; dashed = writes files.", fontsize=7.6, color=SLATE, style="italic")
    save(fig, "06_uml_class_diagram.png")


# ---------------------------------------------------------------- 07 sequence diagram
def sequence():
    fig, ax = canvas(11.5, "Sequence diagram: predict the risk of one patient record", ty=96, top=98)
    names = ["User", "React SPA\nPredict.jsx", "FastAPI\nmain.py", "app.py\nBUNDLES", "scikit-learn\nscaler + model"]
    xs = [8, 28, 49, 70, 90]
    cols = [ORANGE, BLUE, GREEN, GREEN, PURPLE]
    rows = [
        ("m", 0, 1, "open /app/predict/heart", False),
        ("m", 1, 2, "GET /api/diseases/heart", False),
        ("m", 2, 1, "fields, ranges, metrics, algorithms", True),
        ("m", 0, 1, "click 'Positive sample' (optional)", False),
        ("m", 1, 2, "GET /api/diseases/heart/sample?outcome=1", False),
        ("m", 2, 1, "one real CSV row (values, label)", True),
        ("m", 0, 1, "click 'Predict risk'", False),
        ("s", 1, "validate: required, numeric", SLATE),
        ("m", 1, 2, "POST /api/predict/heart {values}", False),
        ("s", 2, "_check(d): unknown disease -> 404", ORANGE),
        ("m", 2, 3, "model, scaler, features = BUNDLES[d]", False),
        ("s", 2, "float(v) per feature: missing / non-finite -> 422", ORANGE),
        ("m", 2, 4, "scaler.transform(X); predict; predict_proba", False),
        ("m", 4, 2, "class, probabilities", True),
        ("m", 2, 1, "JSON: result, probability, model, accuracy", True),
        ("m", 1, 0, "result card: risk class, confidence bar", True),
    ]
    step = 5.0
    y0 = 82
    total = y0 - step * (len(rows) + 1.2)
    for x, n, c in zip(xs, names, cols):
        box(ax, x - 8, 86, 16, 7, n, fc="white", ec=c, lw=1.8, fs=8.2, bold=True)
        ax.plot([x, x], [86, total + 1], color="#CBD5E1", lw=1, ls="--")
    y = y0
    for r in rows:
        if r[0] == "m":
            _, a, b, t, ret = r
            arrow(ax, (xs[a], y), (xs[b], y), None, color=SLATE, ls="--" if ret else "-", lw=1.2)
            ax.text((xs[a] + xs[b]) / 2, y + 0.9, t, ha="center", va="bottom", fontsize=7.4, color=INK)
        else:
            _, a, t, col = r
            x = xs[a]
            ax.plot([x, x + 4.5, x + 4.5], [y + 1.4, y + 1.4, y - 1.2], color=col, lw=1.2)
            arrow(ax, (x + 4.5, y - 1.2), (x, y - 1.2), None, color=col, lw=1.2)
            ax.text(x + 5.6, y + 0.1, t, fontsize=7.3, color=INK if col == SLATE else col, va="center", ha="left")
        y -= step
    ax.text(50, total - 3, "The API holds no state between requests; nothing about the patient is stored.", ha="center", fontsize=7.8, color=SLATE, style="italic")
    save(fig, "07_sequence_diagram.png")


# ---------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(11.5, "Use-case diagram", ty=62, top=64)
    ax.add_patch(Rectangle((19, 3), 62, 54, fc="#FBFCFE", ec=LINE, lw=1.4))
    ax.text(50, 54.4, "Multi-Disease Prediction system (system boundary)", ha="center", fontsize=9.5, fontweight="bold", color=SLATE)
    user = ["Browse landing page and overview", "Choose a disease (4 forms)", "Enter patient values", "Load a real sample record", "Predict disease risk", "View model comparison", "View training datasets", "Read the about page"]
    dev = ["Generate synthetic datasets", "Train and select best models", "Run smoke test of the API"]

    def actor(cx, cy, label, col=ORANGE):
        ax.add_patch(Circle((cx, cy + 6), 2.2, fc="white", ec=col, lw=1.8))
        ax.plot([cx, cx], [cy + 3.8, cy - 3], color=col, lw=1.8)
        ax.plot([cx - 3.6, cx + 3.6], [cy + 1, cy + 1], color=col, lw=1.8)
        ax.plot([cx, cx - 3.6], [cy - 3, cy - 8.5], color=col, lw=1.8)
        ax.plot([cx, cx + 3.6], [cy - 3, cy - 8.5], color=col, lw=1.8)
        ax.text(cx, cy - 10.5, label, ha="center", va="top", fontsize=7.8, fontweight="bold", color=INK)

    actor(9, 28, "User\n(patient or\nclinician-style)")
    actor(91, 28, "Developer /\ntrainer")
    for i, t in enumerate(user):
        cy = 48 - i * 5.6
        ax.add_patch(Ellipse((38, cy), 34, 4.8, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(38, cy, t, ha="center", va="center", fontsize=7.6, color=INK)
        ax.plot([13, 21], [30, cy], color="#94A3B8", lw=0.8)
    for i, t in enumerate(dev):
        cy = 44 - i * 7.5
        ax.add_patch(Ellipse((70, cy), 22, 5.4, fc="#EFEAFB", ec=PURPLE, lw=1.3))
        ax.text(70, cy, t, ha="center", va="center", fontsize=7.4, color=INK)
        ax.plot([87, 81], [30, cy], color="#94A3B8", lw=0.8)
    ax.add_patch(Ellipse((70, 14), 22, 5.4, fc="#E8F0FC", ec=BLUE, lw=1.3, ls="--"))
    ax.text(70, 14, "Validate input values", ha="center", va="center", fontsize=7.4, color=INK)
    arrow(ax, (54.5, 24.4), (60.5, 15.4), "<<include>>", lp=(52.5, 17.5), fs=7.2, ls="--", rad=0.0)
    ax.text(50, 0.8, "Predicting needs trained models (Developer use cases first). There is no sign-in: every user sees every screen.", ha="center", fontsize=7.6, color=SLATE, style="italic")
    save(fig, "08_use_case_diagram.png")


# ---------------------------------------------------------------- 09 ER (logical)
def er():
    fig, ax = canvas(11.5, "Entity-relationship diagram (logical data model)", ty=70, top=72)

    def ent(x, y, w, name, attrs, color=BLUE):
        lh = 3.0
        h = 5 + len(attrs) * lh + 1
        ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=color, lw=1.6))
        ax.add_patch(Rectangle((x, y + h - 5), w, 5, fc=color, ec=color))
        ax.text(x + w / 2, y + h - 2.5, name, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        for i, a in enumerate(attrs):
            ax.text(x + 1.2, y + h - 5 - 1.8 - i * lh, a, fontsize=7.4, va="center", color=INK, family="DejaVu Sans Mono")
        return (x, y, w, h)

    d = ent(37, 42, 26, "DISEASE", ["PK key (diabetes|heart|", "       liver|kidney)", "   title, blurb", "   target_col", "   n_features"], NAVY)
    ds = ent(2, 44, 28, "DATASET_CSV", ["PK file (data/<d>.csv)", "FK disease", "   rows = 2000", "   positive, negative", "   synthetic = true"], GOLD)
    ft = ent(70, 42, 29, "FEATURE", ["PK disease + name", "   label, kind", "   min, max, median", "   options (categorical)"], BLUE)
    mb = ent(2, 5, 28, "MODEL_BUNDLE", ["PK,FK disease", "   model.pkl", "   scaler.pkl", "   features.pkl", "   best_model"], GOLD)
    ar = ent(37, 5, 26, "ALGORITHM_RESULT", ["PK disease + algorithm", "   accuracy, precision", "   recall, f1", "   is_best"], PURPLE)
    pr = ent(70, 5, 29, "PREDICTION (transient)", ["FK disease", "   values (per feature)", "   positive, result", "   probability", "   model, accuracy"], ORANGE)
    arrow(ax, (37, 54), (30, 54), None, head="-")
    ax.text(33.5, 56.4, "1 : 1", fontsize=7.4, color=SLATE, ha="center")
    ax.text(33.5, 51.4, "stored in", fontsize=7, color=SLATE, ha="center")
    arrow(ax, (63, 52), (70, 52), None, head="-")
    ax.text(66.5, 54.4, "1 : N", fontsize=7.4, color=SLATE, ha="center")
    ax.text(66.5, 49.4, "has inputs", fontsize=7, color=SLATE, ha="center")
    arrow(ax, (42, 42), (22, mb[1] + mb[3]), None, head="-")
    ax.text(28, 34, "1 : 1  has", fontsize=7.4, color=SLATE)
    arrow(ax, (50, 42), (50, ar[1] + ar[3]), None, head="-")
    ax.text(51.5, 34, "1 : 4  compares", fontsize=7.4, color=SLATE, va="center")
    arrow(ax, (58, 42), (78, pr[1] + pr[3]), None, head="-")
    ax.text(72, 34, "1 : N  asked", fontsize=7.4, color=SLATE)
    ax.text(50, 0.4, "No SQL database: DATASET_CSV lives in data/, MODEL_BUNDLE in models/*.pkl, ALGORITHM_RESULT in models/training_report.json;\n"
            "PREDICTION exists only for the duration of one request.", ha="center", va="top", fontsize=7.4, color=SLATE, style="italic")
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 core algorithm flowchart
def diamond(ax, cx, cy, w, h, text, fc="#FFF8E5", ec=GOLD, fs=8):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)


def terminator(ax, cx, cy, w, h, text):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=NAVY, ec=NAVY))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")


def flowchart():
    fig, ax = canvas(10.5, "Core algorithm: offline training and online prediction", ty=124, top=126)
    ax.set_ylim(-14, 126)
    fig.set_size_inches(10.5, 10.5 * 140 / 100)
    # ---- left: training
    lx = 22
    ax.text(lx, 118, "A. Offline training (train_models.py)", ha="center", fontsize=9.5, fontweight="bold", color=PURPLE)
    terminator(ax, lx, 111, 20, 5, "Start")
    box(ax, lx - 21, 98, 42, 8, "generate_data.py wrote data/<d>.csv\n(2,000 rows, 8 % label noise)", fs=7.6)
    box(ax, lx - 21, 85, 42, 8, "next disease d: read CSV;\nX = features, y = target", fs=7.8)
    box(ax, lx - 21, 72, 42, 8, "train_test_split 80/20, stratified,\nrandom_state 42", fs=7.8)
    box(ax, lx - 21, 59, 42, 8, "StandardScaler: fit on train,\ntransform train and test", fs=7.8)
    box(ax, lx - 21, 46, 42, 8, "fit LR, DT, RF, SVM on train;\naccuracy, precision, recall, F1 on test", fs=7.4)
    box(ax, lx - 21, 33, 42, 8, "best = model with max F1;\njoblib.dump model, scaler, features", fs=7.8)
    diamond(ax, lx, 21, 40, 12, "more diseases?\n(4 in total)", fs=7.6)
    box(ax, lx - 21, 3, 42, 8, "write models/training_report.json", fs=7.8)
    terminator(ax, lx, -6, 20, 5, "End")
    for y0, y1 in ((108.5, 106), (98, 93), (85, 80), (72, 67), (59, 54), (46, 41), (33, 27)):
        arrow(ax, (lx, y0), (lx, y1), None)
    arrow(ax, (lx, 15), (lx, 11), "no", off=(3, 0), fs=7.4, color=GREEN)
    ax.plot([lx + 20, 47, 47], [21, 21, 89], color=SLATE, lw=1.4)
    arrow(ax, (47, 89), (lx + 21, 89), None)
    ax.text(45.2, 55, "yes", fontsize=7.4, color=GREEN, rotation=90, va="center", ha="center")
    arrow(ax, (lx, 3), (lx, -3.5), None)
    # ---- right: prediction
    rx = 71
    ax.text(rx + 5, 118, "B. Online prediction (POST /api/predict/{d})", ha="center", fontsize=9.5, fontweight="bold", color=GREEN)
    terminator(ax, rx, 111, 20, 5, "Request")
    diamond(ax, rx, 98, 36, 12, "disease in\n{diabetes, heart,\nliver, kidney}?", fs=7.4)
    box(ax, rx - 18, 77, 36, 8, "for each feature in the saved\norder: v = float(value)", fs=7.6)
    diamond(ax, rx, 64, 36, 12, "every v present\nand finite?", fs=7.6)
    box(ax, rx - 18, 44, 36, 8, "X = scaler.transform([v ...])", fs=7.6)
    box(ax, rx - 18, 32, 36, 8, "pred = model.predict(X)\nprob = max(predict_proba(X)) x 100", fs=6.9)
    box(ax, rx - 18, 20, 36, 8, "Positive (High Risk) if pred = 1,\nelse Negative (Low Risk)", fs=7.4)
    box(ax, rx - 18, 8, 36, 8, "return JSON: result, probability,\nmodel, hold-out accuracy", fs=7.4)
    terminator(ax, rx, -6, 20, 5, "Response")
    box(ax, 90.5, 94, 9.5, 8, "HTTP\n404", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    box(ax, 90.5, 60, 9.5, 8, "HTTP\n422", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    for y0, y1 in ((108.5, 104), (92, 85), (77, 70), (58, 52), (44, 40), (32, 28), (20, 16), (8, -3.5)):
        arrow(ax, (rx, y0), (rx, y1), None)
    ax.text(rx + 2, 89, "yes", fontsize=7.4, color=GREEN)
    ax.text(rx + 2, 55, "yes", fontsize=7.4, color=GREEN)
    arrow(ax, (rx + 18, 98), (90.5, 98), None, color=ORANGE)
    ax.text(86.2, 101.2, "no", fontsize=7.4, color=ORANGE, ha="center")
    arrow(ax, (rx + 18, 64), (90.5, 64), None, color=ORANGE)
    ax.text(86.2, 67.2, "no", fontsize=7.4, color=ORANGE, ha="center")
    ax.text(50, -12, "The trained model files written by A are the ones loaded by app.py and used by B.", ha="center", fontsize=7.8, color=SLATE, style="italic")
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
