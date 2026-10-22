"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does:
  app/routes.py + app/api.py (Flask), app/services/*.py, scripts/*.py and the artifacts/ files.
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


def canvas(w, h, title=None, ty=99):
    """Work in a 100 x 100 coordinate space; the figure is cropped to its content when saved."""
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
        ax.text(lx, ly, label, fontsize=fs, color=color,
                ha=lab_ha, va="center", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


def mid(b, side):
    x, y, w, h = b
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]

# ---------------------------------------------------------------- DFD helpers
def process(ax, cx, cy, r, text, num, fs=8):
    ax.add_patch(Circle((cx, cy), r, fc="#E8F0FC", ec=BLUE, lw=1.6))
    ax.text(cx, cy + r * 0.42, num, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
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
    ax.text(x + w / 2 + 2.5, y + h / 2, text, ha="center", va="center", fontsize=8.5, color=INK, linespacing=1.2)
    return (x, y, w, h)


# ---------------------------------------------------------------- 06 UML class
def uml_class(ax, x, y, w, name, attrs, methods, stereo=None, color=BLUE, fs=7.6):
    lh = 2.15
    h = 4.6 + lh * (len(attrs) + len(methods)) + (1.2 if attrs and methods else 0)
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.6))
    ax.add_patch(Rectangle((x, y - 4.6), w, 4.6, fc=color, ec=color))
    if stereo:
        ax.text(x + w / 2, y - 1.1, f"<<{stereo}>>", ha="center", va="center", color="white", fontsize=6.8)
        ax.text(x + w / 2, y - 3.1, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    else:
        ax.text(x + w / 2, y - 2.3, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    cy = y - 4.6 - 1.2
    for a in attrs:
        ax.text(x + 1, cy, a, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    if attrs and methods:
        ax.plot([x, x + w], [cy + 0.2, cy + 0.2], color=color, lw=0.8)
        cy -= 1.0
    for m in methods:
        ax.text(x + 1, cy, m, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    return (x, y - h, w, h)


def diamond(ax, cx, cy, w, h, text, fc="#FFF8E5", ec=GOLD, fs=8):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.1)




# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11.5, 7.6, "System architecture of FinSight AI", ty=78)
    for x, w, label in ((1, 19, "Presentation tier"), (23, 28, "Application tier (Flask, port 8409)"), (54, 22, "Model and service tier"), (79, 20, "Data tier")):
        ax.add_patch(Rectangle((x, 8), w, 64, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 69.4, label, ha="center", fontsize=8.6, color=SLATE, fontweight="bold")
    box(ax, 2.5, 44, 16, 17, "React 19 SPA\nVite preview\nport 5409\n\nLanding, Sign in,\nDashboard, Assess,\nResult, Explain,\nForecast, What-if,\nPerformance, About", fc="#E8F0FC", ec=BLUE, fs=7.4)
    box(ax, 2.5, 14, 16, 13, "Server-rendered\nJinja pages\n(same Flask app,\nport 8409)", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    box(ax, 25, 53, 24, 11.5, "app/api.py  (api_bp)\n/api/options, /dashboard,\n/explain, /performance,\nPOST /api/whatif", fc="#E6F6EF", ec=GREEN, fs=7.6)
    box(ax, 25, 38, 24, 11.5, "app/routes.py  (bp)\n/, /assess, /explain, /whatif,\n/health, POST /api/predict,\nGET /api/forecast, /artifacts", fc="#E6F6EF", ec=GREEN, fs=7.6)
    box(ax, 25, 24, 24, 9.5, "app/utils/validation.py\nvalidate_assessment()\nrequired / allowed-set / range", fc="#EFEBFC", ec=PURPLE, fs=7.6)
    box(ax, 25, 11, 24, 9, "app/__init__.py\ncreate_app(), model preload,\nsession secret", fc="#EFEBFC", ec=PURPLE, fs=7.6)
    box(ax, 56, 54, 18, 10, "services/predictor.py\npredict_profile(), local_shap(),\nbuild_insights()", fc=PAPER, ec=NAVY, fs=7.2)
    box(ax, 56, 41, 18, 9, "services/whatif.py\nrun_whatif()", fc=PAPER, ec=NAVY, fs=7.6)
    box(ax, 56, 29, 18, 9, "services/forecaster.py\nget_forecast()", fc=PAPER, ec=NAVY, fs=7.6)
    box(ax, 56, 14, 18, 11, "scripts/feature_engineering.py\nclean_frame(),\nadd_derived_features()", fc=PAPER, ec=NAVY, fs=7.2)
    box(ax, 81, 55, 17, 10, "models/\nbest_model.pkl\n(sklearn Pipeline:\npreprocess + XGBoost)", fc="#FFF8E5", ec=GOLD, fs=7.4)
    box(ax, 81, 42, 17, 10, "artifacts/\nmetrics, shap_global,\nforecast, validation\n(JSON + PNG)", fc="#FFF8E5", ec=GOLD, fs=7.4)
    box(ax, 81, 29, 17, 9, "data/raw/\nadult.data, adult.test\n(UCI Adult)", fc="#FFF8E5", ec=GOLD, fs=7.4)
    box(ax, 81, 14, 17, 11, "Browser storage:\ntheme, demo login,\nlast result and\nbaseline (web storage)", fc="#FFF8E5", ec=GOLD, fs=7.2, ls="--")
    arrow(ax, (18.5, 58), (25, 58.5), "JSON /api", color=BLUE, off=(0, 2.3), fs=7)
    arrow(ax, (18.5, 48), (25, 44), None, color=BLUE)
    arrow(ax, (18.5, 20), (25, 42), None, color=ORANGE, ls="--")
    arrow(ax, (37, 53), (37, 49.5))
    arrow(ax, (37, 38), (37, 33.5))
    arrow(ax, (49, 44), (56, 58), None)
    ax.text(51.2, 53.6, "predict", fontsize=7, color=SLATE, rotation=55)
    arrow(ax, (49, 56), (56, 46), None)
    ax.text(50.6, 49.6, "what-if", fontsize=7, color=SLATE, rotation=-45)
    arrow(ax, (49, 42), (56, 33), None)
    arrow(ax, (65, 54), (65, 50))
    arrow(ax, (65, 41), (65, 38))
    arrow(ax, (74, 59), (81, 60), "load", ls="--", off=(0, 2.0), fs=7)
    arrow(ax, (74, 33), (81, 46), "read JSON", off=(1.2, -1.6), fs=7)
    arrow(ax, (74, 18), (81, 32), None, ls="--")
    ax.text(75.2, 24.5, "offline", fontsize=6.8, color=SLATE, rotation=60)
    ax.text(50, 2.6, "Offline: scripts/train.py trains four models, writes models/*.pkl and artifacts/*; the online path only loads them.", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11, 4.8, "High-level workflow of one assessment", ty=50)
    steps = [
        ("1  Sign in", "demo gate\n(browser only)", NAVY),
        ("2  Enter profile", "12 demographic and\nfinancial fields", BLUE),
        ("3  Validate", "required, allowed set,\nnumeric range", ORANGE),
        ("4  Engineer features", "clean, net capital,\nbands, region", PURPLE),
        ("5  Predict", "XGBoost P(income >50K)\n= strength score", GREEN),
        ("6  Profile and risk", ">=0.60 Established, >=0.35\nDeveloping, else Emerging", GOLD),
        ("7  Explain", "live SHAP drivers +\nplain-language insights", NAVY),
        ("8  Explore", "forecast, what-if,\nperformance screens", BLUE),
    ]
    w, gap = 22.9, 1.9
    for i, (t, s, c) in enumerate(steps):
        row_y = 28 if i < 4 else 7
        xx = 1.5 + (i % 4) * (w + gap)
        box(ax, xx, row_y, w, 14, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 9.6), w, 4.4, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 11.8, t, ha="center", va="center", color="white", fontsize=9.6, fontweight="bold")
        ax.text(xx + w / 2, row_y + 4.6, s, ha="center", va="center", color=INK, fontsize=8.6, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 6), (xx + w + gap, row_y + 6))
    xe = 1.5 + 3 * (w + gap) + w / 2
    ax.plot([xe, xe, 1.5 + w / 2], [28, 24.5, 24.5], color=SLATE, lw=1.4)
    arrow(ax, (1.5 + w / 2, 24.5), (1.5 + w / 2, 21.2))
    ax.text(50, 45.2, "A validation failure at step 3 returns HTTP 400 with a list of messages and runs no model.", ha="center", fontsize=8.5, color=SLATE, style="italic")
    save(fig, "02_high_level_workflow.png")


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(11, 5.4, "Data flow diagram, level 0 (context)", ty=56)
    entity(ax, 3, 27, 17, 14, "User\n(individual /\nanalyst)")
    process(ax, 50, 34, 15, "FinSight AI\nsystem", "0", fs=9.5)
    store(ax, 74, 42, 24, 8, "model files (.pkl)", "D1")
    store(ax, 74, 26, 24, 8, "result artifacts (JSON, PNG)", "D2")
    store(ax, 74, 9, 24, 8, "Adult census data (CSV)", "D3")
    arrow(ax, (20, 38), (35.3, 38), "profile fields,\nscenario changes,\nscreen requests", off=(0, 5.2), fs=7.8)
    arrow(ax, (35.3, 30), (20, 30), "profile, risk, SHAP drivers,\ninsights, forecast, metrics,\nwhat-if comparison", off=(0, -5.6), fs=7.8)
    arrow(ax, (63, 40), (74, 45), "load", off=(0, 2.4), fs=7.8)
    arrow(ax, (64.5, 35), (74, 31.5), "read", off=(0, 2.4), fs=7.8)
    arrow(ax, (74, 13), (57, 23), "training (offline)", off=(2, -2.6), fs=7.6, ls="--")
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11, 6.6, "Data flow diagram, level 1", ty=96)
    entity(ax, 1.5, 52, 12.5, 14, "User")
    process(ax, 29, 84, 7.8, "Validate\ninput", "1.0")
    process(ax, 50, 84, 8.4, "Engineer\nfeatures and\npredict", "2.0", fs=7.4)
    process(ax, 72, 84, 8.4, "Explain and\nadvise", "3.0", fs=7.8)
    process(ax, 50, 52, 8.4, "What-if\ncomparison", "4.0", fs=7.8)
    process(ax, 28, 20, 8, "Serve forecast\nand metrics", "5.0", fs=7.2)
    process(ax, 78, 20, 8.4, "Train and\nevaluate\n(offline)", "6.0", fs=7.4)
    store(ax, 68, 52, 31, 7, "model files (.pkl)", "D1")
    store(ax, 34, 1, 30, 6.5, "result artifacts (JSON, PNG)", "D2")
    store(ax, 84, 30, 15, 7, "Adult CSV", "D3")
    arrow(ax, (14, 64), (22.4, 78.6), "profile fields", lp=(10.5, 74.5), fs=7.4)
    arrow(ax, (36.8, 84), (41.6, 84), "valid\nrecord", off=(0, 3.5), fs=7.0)
    arrow(ax, (58.4, 84), (63.6, 84), "p, row", off=(0, 3.0), fs=7.0)
    arrow(ax, (72, 75.6), (14, 62), "profile, risk, drivers, insights", lp=(31, 69.2), fs=7.4)
    arrow(ax, (14, 58), (41.6, 55), "baseline + scenario", lp=(24, 59.6), fs=7.4)
    arrow(ax, (41.6, 49), (14, 55), "comparison", lp=(26, 49.2), fs=7.4)
    arrow(ax, (50, 60.4), (50, 75.6), "re-predict x2", off=(7.4, 0), fs=7.0)
    arrow(ax, (76, 59), (56.4, 78), "weights", lp=(70, 70.5), fs=7.0)
    arrow(ax, (9, 52), (22.5, 26), "screen request", lp=(9.5, 38), fs=7.4)
    arrow(ax, (23, 27), (13, 52), "forecast, metrics", lp=(24, 41), fs=7.4)
    arrow(ax, (30, 12), (40, 7.5), "read", lp=(32, 7.8), fs=7.2)
    arrow(ax, (82, 28.4), (82, 52), "write", lp=(85, 41), fs=7.2)
    arrow(ax, (74, 12), (62, 5.5), "write", lp=(71.5, 6.6), fs=7.2)
    arrow(ax, (88, 30), (84.4, 26.8), None)
    ax.text(99, 96.4, "Process 6.0 runs outside the web request path (python scripts/train.py).", fontsize=8.2, color=SLATE, style="italic", ha="right")
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(11, 6.6, "Data flow diagram, level 2: process 2.0 and 3.0 expanded", ty=96)
    labels = [("2.1", "Build input\nframe\n(fnlwgt=NaN)"), ("2.2", "clean_frame\n'?' -> NaN"), ("2.3", "add_derived_\nfeatures\n(26 columns)"),
              ("2.4", "Impute +\none-hot\n(+ scale for LR)"), ("2.5", "XGBoost\npredict_proba")]
    xs = [11, 28, 45, 62, 79]
    for (n_, t), x in zip(labels, xs):
        process(ax, x, 84, 7.8, t, n_, fs=6.8)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.8, 84), (b - 7.8, 84), None)
    entity(ax, 1, 62, 17, 8, "validated record")
    arrow(ax, (10, 70), (11, 76.2), "12 fields", off=(4.4, 0), fs=7.2)
    process(ax, 79, 58, 8, "Profile and\nrisk band", "2.6", fs=7.2)
    process(ax, 57, 58, 8, "TreeExplainer\nshap_values", "3.1", fs=7.0)
    process(ax, 34, 58, 8, "Top 5 up /\ndown drivers", "3.2", fs=7.0)
    process(ax, 11, 40, 8, "build_\ninsights", "3.3", fs=7.4)
    store(ax, 62, 22, 36, 8, "best_model.pkl, feature_names.pkl", "D1")
    entity(ax, 20, 14, 36, 11, "Result record: p, strength %, profile, risk,\nSHAP positives / negatives, insights")
    arrow(ax, (79, 76.2), (79, 66), "p = P(>50K)", off=(-8, 0), fs=7.2)
    arrow(ax, (71, 58), (65, 58), "row", off=(0, 2.5), fs=7.2)
    arrow(ax, (49, 58), (42, 58), "SHAP\nvalues", off=(0, 3.4), fs=7.0)
    arrow(ax, (28, 54), (17, 44), "drivers", off=(-1.5, 2.0), fs=7.2)
    arrow(ax, (79, 50), (50, 25.4), "profile, risk", off=(8, 1.5), fs=7.2)
    arrow(ax, (34, 50), (40, 25.4), "drivers", off=(-5, -0.4), fs=7.2)
    arrow(ax, (14, 32), (20, 20), "insights", off=(-4, -1.0), fs=7.2)
    arrow(ax, (94, 30), (86.5, 80), "model", lp=(97.5, 52), fs=7.2)
    ax.text(50, 1.2, "2.4 is the ColumnTransformer inside the saved Pipeline (fitted on training data only); 3.1 builds its TreeExplainer from the same model.", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML class
def class_diagram():
    fig, ax = canvas(12.2, 8.4, "UML class diagram (modules and the sklearn pipeline drawn as classes)", ty=98)
    uml_class(ax, 1.5, 94, 31, "RoutesBlueprint", ["+bp : Blueprint"],
              ["+index() / explain() / forecast()", "+assess()  [GET, POST]", "+whatif()  [GET, POST]", "+performance() / about()", "+health()", "+api_predict()  POST", "+api_forecast()  GET"],
              "module app.routes", GREEN)
    uml_class(ax, 1.5, 63, 31, "ApiBlueprint", ["+api_bp : Blueprint"],
              ["+options() / dashboard()", "+explain() / performance()", "+whatif()  POST", "-_parse_overrides(data)"], "module app.api", GREEN)
    uml_class(ax, 1.5, 42, 31, "Validation", ["+WORKCLASS, EDUCATION, ...", "+EDU_NUM_MAP : dict"], ["+validate_assessment(data)", "    : (dict, list)"], "module app.utils", PURPLE)
    uml_class(ax, 37, 94, 30, "Predictor", ["-_model : Pipeline", "-_explainer : TreeExplainer", "-_model_name : str"],
              ["+get_model() / get_explainer()", "+build_input_frame(cleaned)", "+profile_from_proba(p)", "+local_shap(pipe, frame)", "+predict_profile(cleaned)", "+build_insights(...)", "+load_json_artifact(name)"],
              "module services.predictor", ORANGE)
    uml_class(ax, 37, 62, 30, "WhatIf", [], ["+run_whatif(baseline,", "     overrides) : dict"], "module services.whatif", ORANGE)
    uml_class(ax, 37, 49, 30, "Forecaster", [], ["+get_forecast() : dict"], "module services.forecaster", ORANGE)
    uml_class(ax, 72, 94, 26.5, "Pipeline", ["+preprocess : ColumnTransformer", "+model : Classifier"], ["+fit(X, y)", "+predict_proba(X)"], "sklearn", SLATE)
    uml_class(ax, 72, 78, 26.5, "Classifier", ["LogisticRegression", "RandomForestClassifier", "GradientBoostingClassifier", "XGBClassifier  [best]"], [], "interface (4 realisations)", SLATE)
    uml_class(ax, 72, 60, 26.5, "FeatureEngineering", ["+COLUMN_NAMES, REGION_MAP", "+RANDOM_STATE = 42"],
              ["+clean_frame(df)", "+add_derived_features(df)", "+build_preprocessor(scale)", "+get_output_feature_names()", "+human_label(name)"], "module scripts", PURPLE)
    uml_class(ax, 72, 36, 26.5, "TrainScript", [], ["+main()", "+evaluate_binary(y, pred, p)", "+save_confusion_matrix()", "+save_roc_curves()"], "module scripts.train", BLUE)
    uml_class(ax, 72, 20, 26.5, "ForecastScript", ["+FORECAST_HORIZON = 12"], ["+build_index_series()", "+fit_forecast(df, h)"], "module scripts.forecast", BLUE)

    def link(p, q, label=None, head="-|>", ls="-", lp=None):
        arrow(ax, p, q, label, color=SLATE, lw=1.2, ls=ls, fs=7.2, head=head, lp=lp)

    link((32.5, 86), (37, 86), "calls", lp=(34.8, 88.2))
    link((32.5, 59.5), (37, 59.5), None)
    link((52, 62), (52, 66.7), None, ls="--")
    link((33, 72), (37, 46), None, ls="--")
    link((17, 46.5), (17, 42.2), None)
    link((67, 86), (72, 86), "loads", lp=(69.5, 88.2))
    link((85, 79.6), (85, 78.2), None, head="-")
    link((67, 70), (72, 57), None, ls="--")
    link((85, 36), (85, 39.1), None)
    link((85, 22.8), (85, 20.2), None)
    ax.text(40, 36.5, "Solid arrows: calls / imports.\nDashed: data or instance relationships.\nWhatIf calls predict_profile twice\n(baseline and scenario). The code base is\nfunction-oriented, so each Python module\nis drawn as a class.", fontsize=7.6, color=SLATE, style="italic", va="top", linespacing=1.4)
    save(fig, "06_uml_class_diagram.png")


# ---------------------------------------------------------------- 07 sequence
def sequence():
    fig, ax = canvas(11.5, 8.0, "Sequence diagram: one financial assessment", ty=90)
    actors = [("User", 8), ("React SPA", 23), ("Flask\n/api/predict", 39), ("validation", 54), ("Predictor +\nPipeline", 70), ("SHAP\nTreeExplainer", 88)]
    top = 76
    for n_, x in actors:
        box(ax, x - 7, top, 14, 7, n_, fc=NAVY, ec=NAVY, tc="white", fs=8.0, bold=True)
        ax.plot([x, x], [top, 12], color=LINE, lw=1, ls=(0, (4, 3)))
    X = dict(actors)
    A_, B_, C_, D_, E_, F_ = [a[0] for a in actors]
    seq = [
        (A_, B_, "fill 12 fields, press Analyse", 72, False),
        (B_, B_, "client check of ranges", 68.4, False),
        (B_, C_, "POST /api/predict  (JSON)", 64.6, False),
        (C_, D_, "validate_assessment(payload)", 60.8, False),
        (D_, C_, "cleaned dict  (or errors -> 400)", 57.2, True),
        (C_, E_, "predict_profile(cleaned)", 53.4, False),
        (E_, E_, "build frame, clean, derive, predict_proba", 49.6, False),
        (E_, F_, "shap_values(row)", 45.8, False),
        (F_, E_, "contributions", 42.2, True),
        (E_, E_, "profile_from_proba, build_insights", 38.6, False),
        (E_, C_, "result dict", 35, True),
        (C_, B_, "200 JSON {ok, result}", 31.4, True),
        (B_, B_, "store result, route to /app/result", 27.8, False),
        (B_, A_, "profile, risk, SHAP factors, forecast", 24.2, True),
    ]
    for a, b, label, y, ret in seq:
        xa, xb = X[a], X[b]
        if a == b:
            ax.add_patch(Rectangle((xa, y - 1.2), 3.6, 2.4, fc="#E8F0FC", ec=BLUE, lw=1))
            ax.text(xa + 4.6, y, label, fontsize=7.4, va="center", color=INK)
        else:
            arrow(ax, (xa, y), (xb, y), None, color=BLUE if not ret else GREEN, ls="--" if ret else "-", lw=1.4)
            ax.text((xa + xb) / 2, y + 1.4, label, fontsize=7.4, ha="center", color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
    ax.text(50, 9, "Alternative: invalid input -> HTTP 400 {ok: false, errors: [...]} and no model call.", ha="center", fontsize=8.2, color=SLATE, style="italic")
    save(fig, "07_sequence_diagram.png")


# ---------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(11, 7.6, "Use-case diagram", ty=78)
    ax.add_patch(Rectangle((24, 4), 52, 68, fc="#FBFCFE", ec="#D5DCE6", lw=1.4))
    ax.text(50, 69.2, "FinSight AI", ha="center", fontsize=10, fontweight="bold", color=NAVY)
    cases = [
        ("Sign in (demo gate)", 62), ("Enter demographic and\nfinancial profile", 55.5), ("View profile, risk band\nand strength score", 49),
        ("See SHAP drivers and insights", 42.5), ("Explore global explainability", 36), ("View 12-month forecast", 29.5),
        ("Run what-if scenario", 23), ("Review model performance", 16.5), ("Switch light / dark theme", 10),
    ]
    for t, y in cases:
        ax.add_patch(Ellipse((50, y), 38, 5.2, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(50, y, t, ha="center", va="center", fontsize=7.8, color=INK, linespacing=1.1)

    def actor(x, y, label, color):
        ax.add_patch(Circle((x, y + 8), 2.2, fc="white", ec=color, lw=1.8))
        ax.plot([x, x], [y + 5.8, y + 1.2], color=color, lw=1.8)
        ax.plot([x - 3, x + 3], [y + 4.2, y + 4.2], color=color, lw=1.8)
        ax.plot([x, x - 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.plot([x, x + 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.text(x, y - 5, label, ha="center", fontsize=8.6, fontweight="bold", color=INK, linespacing=1.15)
    actor(10, 36, "User\n(individual / analyst)", ORANGE)
    for t, y in cases:
        ax.plot([13, 31], [42, y], color=LINE, lw=0.9)
    actor(90, 26, "Developer", PURPLE)
    box(ax, 79, 6, 19, 8, "Train models, run tests\nand smoke checks\n(scripts, outside UI)", fc="#EFEBFC", ec=PURPLE, fs=7.2)
    ax.plot([90, 90], [20.5, 14], color=PURPLE, lw=1)
    ax.text(50, 1.0, "Every case except 'Sign in' sits behind the sample login gate.", ha="center", fontsize=8.2, color=SLATE, style="italic")
    save(fig, "08_use_case_diagram.png")


# ---------------------------------------------------------------- 09 ER (data model)
def er():
    fig, ax = canvas(11.5, 7.0, "Entity-relationship (data model) diagram", ty=76)

    def table(x, y, w, name, cols, color, dashed=False, lh=3.3, fs=7.4):
        h = 4.8 + lh * len(cols)
        ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.7, ls="--" if dashed else "-"))
        ax.add_patch(Rectangle((x, y - 4.8), w, 4.8, fc=color, ec=color))
        ax.text(x + w / 2, y - 2.4, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
        for i, (a, b) in enumerate(cols):
            yy = y - 4.8 - lh * (i + 0.5)
            ax.text(x + 1, yy, a, fontsize=fs, va="center", family="monospace", color=INK)
            ax.text(x + w - 1, yy, b, fontsize=fs - 0.4, va="center", ha="right", family="monospace", color=BLUE)
        return (x, y - h, w, h)

    table(1, 70, 29, "AssessmentRecord  (request)", [("age", "int 16-100"), ("workclass", "enum"), ("education", "enum"), ("education-num", "derived"), ("marital-status", "enum"), ("occupation", "enum"), ("relationship", "enum"), ("race", "enum"), ("sex", "enum"), ("native-country", "enum"), ("capital-gain", "0-1e6"), ("capital-loss", "0-1e6"), ("hours-per-week", "1-99")], ORANGE, dashed=True)
    table(37, 70, 28, "PredictionResult  (response)", [("proba", "float 0-1"), ("strength_pct", "float"), ("risk_pct", "float"), ("profile", "3 classes"), ("risk", "3 bands"), ("model", "str"), ("insights[]", "list[str]")], NAVY, dashed=True)
    table(37, 34, 28, "ShapContribution  (1..10)", [("feature", "str"), ("label", "str"), ("shap", "float"), ("value", "float"), ("sentence", "str")], GREEN, dashed=True)
    table(71, 70, 28, "ModelMetrics  (4 rows)", [("model", "str, key"), ("accuracy", "float"), ("precision", "float"), ("recall", "float"), ("f1", "float"), ("roc_auc", "float"), ("cv_roc_auc_mean", "float"), ("cv_roc_auc_std", "float")], GOLD)
    table(71, 36, 28, "ForecastPoint  (132 + 12)", [("date", "YYYY-MM"), ("value", "float"), ("lower", "float, forecast"), ("upper", "float, forecast")], BLUE)
    arrow(ax, (30, 52), (37, 56), "1 : 1", off=(0, 2.4), fs=7.4, head="-|>")
    arrow(ax, (51, 42.1), (51, 34), "1 : 1..10", off=(5.2, 0), fs=7.4, head="-")
    arrow(ax, (65, 61), (71, 61), "reads", off=(0, 2.0), fs=7.2, head="-|>", ls="--")
    arrow(ax, (65, 26), (71, 30), "context", off=(0, 2.6), fs=7.2, head="-|>", ls="--")
    ax.text(1, 19, "Dashed borders: transient objects (request and\nresponse JSON); nothing about a person is stored.\nSolid borders: persisted as JSON files\n(model_comparison.json, forecast.json).\nThere is NO relational database: trained pipelines\nare .pkl files, evaluation output is JSON, the\nwhat-if baseline is kept in browser sessionStorage\n(Flask session cookie on the Jinja pages), and the\ntheme and demo login live in browser localStorage.", fontsize=7.6, color=SLATE, style="italic", linespacing=1.45, va="top")
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 flowchart
def flowchart():
    fig, ax = canvas(10.5, 9.8, "Flowchart of the core algorithm (POST /api/predict)", ty=104)
    cx = 36

    def term(y, t):
        box(ax, cx - 11, y - 2.2, 22, 4.4, t, fc=NAVY, ec=NAVY, tc="white", fs=8.4, bold=True, rounding=2.2)

    def step(y, t, c=BLUE, w=34):
        box(ax, cx - w / 2, y - 2.8, w, 5.6, t, fc="#F4F8FE", ec=c, fs=7.8)
    ys = [96, 88.5, 80, 71.5, 63, 54.5, 46, 37.5, 29, 20.5, 12]
    term(ys[0], "Start: JSON profile received")
    diamond(ax, cx, ys[1], 32, 7.4, "all 12 fields present,\nin allowed set / range?")
    step(ys[2], "frame = build_input_frame(cleaned)\n(education-num from map, fnlwgt = NaN)")
    step(ys[3], "clean_frame + add_derived_features\n(net-capital, bands, tier, region, ...)", PURPLE)
    step(ys[4], "p = pipeline.predict_proba(frame)[0, 1]\n(impute, one-hot, XGBoost)", GREEN)
    diamond(ax, cx, ys[5], 32, 7.4, "p >= 0.60 ?")
    diamond(ax, cx, ys[6], 32, 7.4, "p >= 0.35 ?")
    step(ys[7], "shap_values(row): top 5 positive,\ntop 5 negative contributions", GOLD)
    step(ys[8], "build_insights(inputs, p, profile, risk, shap)")
    step(ys[9], "strength = 100p, risk = 100(1-p)", NAVY)
    term(ys[10], "Return 200 + JSON result")
    pairs = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10)]
    half = {1: 3.7, 5: 3.7, 6: 3.7}
    for a, b in pairs:
        ga = 2.2 if a == 0 else half.get(a, 2.8)
        gb = 2.2 if b == 10 else half.get(b, 2.8)
        arrow(ax, (cx, ys[a] - ga), (cx, ys[b] + gb), None, lw=1.3)
    box(ax, cx + 22, ys[1] - 2.6, 21, 5.2, "HTTP 400\n{ok: false, errors[]}", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    arrow(ax, (cx + 16, ys[1]), (cx + 22, ys[1]), None, color=ORANGE, lw=1.3)
    ax.text(cx + 19, ys[1] + 1.6, "no", fontsize=7.6, color=ORANGE, ha="center")
    ax.text(cx + 1.3, ys[1] - 4.7, "yes", fontsize=7.6, color=GREEN)
    box(ax, cx + 22, ys[5] - 3, 21, 6, "profile = Established\nrisk = Low", fc="#E6F6EF", ec=GREEN, fs=7.6)
    arrow(ax, (cx + 16, ys[5]), (cx + 22, ys[5]), None, color=GREEN, lw=1.3)
    ax.text(cx + 19, ys[5] + 1.6, "yes", fontsize=7.6, color=GREEN, ha="center")
    ax.text(cx + 1.3, ys[5] - 4.7, "no", fontsize=7.6, color=ORANGE)
    box(ax, cx + 22, ys[6] - 3, 21, 6, "yes: Developing / Moderate\nno: Emerging / High", fc="#FFF8E5", ec=GOLD, fs=7.4)
    arrow(ax, (cx + 16, ys[6]), (cx + 22, ys[6]), None, color=GOLD, lw=1.3)
    ax.text(cx + 1.3, ys[6] - 4.7, "(both branches continue)", fontsize=7.2, color=SLATE)
    save(fig, "10_core_algorithm_flowchart.png")


# ---------------------------------------------------------------- 11 training pipeline
def training():
    fig, ax = canvas(11.5, 5.8, "Offline training and evaluation pipeline (scripts/train.py)", ty=60)
    steps = [
        ("Load", "adult.data +\nadult.test\n48,842 rows", NAVY), ("Clean", "'?' -> NaN, strip,\ndrop missing target", BLUE),
        ("Engineer", "26 feature columns\nfrom 14 raw fields", PURPLE), ("Split", "stratified 80/20\n39,073 / 9,769", ORANGE),
        ("Train x4", "LR, RF, GB, XGB\n(Pipeline each)", GREEN), ("Validate", "5-fold stratified\nCV, ROC-AUC", GOLD),
        ("Select", "best test ROC-AUC\n-> XGBoost", NAVY), ("Persist", "pkl + JSON + PNG\nSHAP, forecast", BLUE),
    ]
    w, gap = 22.9, 1.9
    for i, (t, s_, c) in enumerate(steps):
        row_y = 33 if i < 4 else 11
        xx = 1.5 + (i % 4) * (w + gap)
        box(ax, xx, row_y, w, 15, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 10.6), w, 4.4, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 12.8, f"{i + 1}  {t}", ha="center", va="center", color="white", fontsize=9.6, fontweight="bold")
        ax.text(xx + w / 2, row_y + 5, s_, ha="center", va="center", color=INK, fontsize=8.6, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 7), (xx + w + gap, row_y + 7))
    xe = 1.5 + 3 * (w + gap) + w / 2
    ax.plot([xe, xe, 1.5 + w / 2], [33, 29.5, 29.5], color=SLATE, lw=1.4)
    arrow(ax, (1.5 + w / 2, 29.5), (1.5 + w / 2, 26.2))
    ax.text(50, 54.2, "Preprocessing lives inside each Pipeline, so imputation and encoding are fitted on training folds only.", ha="center", fontsize=8.5, color=SLATE, style="italic")
    save(fig, "11_training_pipeline.png")


def main():
    for fn in (architecture, workflow, dfd0, dfd1, dfd2, class_diagram, sequence, use_case, er, flowchart, training):
        fn()


if __name__ == "__main__":
    main()
