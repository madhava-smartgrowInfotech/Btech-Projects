"""Draw every design diagram for the VenturePulse documents into docs/diagrams/ (PNG, 150 dpi).

Every box and arrow mirrors the code: app/main.py and app/api_extra.py (routes), app/services/*.py, app/ml/*.py, app/config.py,
frontend/src/pages and scripts/run_experiments.py / extra_experiments.py. matplotlib only.
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
    fig, ax = canvas(10, 8.2, 100, 82)
    panel(ax, 2, 62, 96, 18, "Presentation tier - browser (React 18 + Vite 6 + Tailwind 4, port 5410)", PALE_BLUE, BLUE, tc=NAVY)
    box(ax, 17, 69, 28, 10.5, "Six screens (react-router)\nLanding - Login - Dashboard\nAnalyze - Performance - Insights", BLUE, fs=7.8)
    box(ax, 49, 69, 28, 10.5, "api.js client\nfetch + Bearer token\nVite proxy to port 8410", BLUE, fs=7.8)
    box(ax, 81, 69, 28, 10.5, "UI kit (Kinetic Mono)\nRecharts charts\nlight / dark theme", BLUE, fs=7.8)

    panel(ax, 2, 33, 96, 26, "Application tier - FastAPI (app/main.py + app/api_extra.py, port 8410)", PALE_TEAL, TEAL, tc=NAVY)
    box(ax, 14.5, 49.5, 22, 12.5, "Prediction\nPOST /predict (JSON)\nPOST /predict-form\n(Pydantic checks)", TEAL, fs=7.4)
    box(ax, 38.5, 49.5, 22, 12.5, "Model and data\nGET /api/health\nGET /api/model-metrics\nGET /api/insights", TEAL, fs=7.4)
    box(ax, 62.5, 49.5, 22, 12.5, "React helpers\nGET /api/config\nGET /api/feature-importance\n/api/auth/login, /me", TEAL, fs=7.2)
    box(ax, 86, 49.5, 20, 12.5, "Jinja pages\n/ /dashboard\n/predict /performance\n/insights", TEAL, fs=7.4)
    box(ax, 29, 38.4, 54, 5.2, "services: store.ensure_artifacts() - predictor.predict_one() - insights.compute_insights()", WHITE, tc=INK, ec=TEAL, fs=7.4)
    box(ax, 79, 38.4, 33, 5.2, "STATE dict held in memory (loaded once)", WHITE, tc=INK, ec=TEAL, fs=7.4)

    panel(ax, 2, 12, 96, 18, "Domain tier - app/ml/ (scikit-learn, XGBoost, sentence-transformers)", PALE_ORANGE, ORANGE, tc=NAVY)
    mods = [("dataset.py", "load_dataset\nsynthetic fallback"), ("preprocessing.py", "impute, scale,\none-hot (37 cols)"),
            ("embeddings.py", "all-MiniLM-L6-v2\n384-d"), ("retrieval.py", "fuse (alpha 0.5)\nbalanced top-k"),
            ("models.py", "LR, DT, RF,\nXGBoost"), ("evaluation.py", "5 x 80/20 study\nsave artefacts")]
    for i, (n, d) in enumerate(mods):
        box(ax, 10.2 + i * 15.9, 19.2, 14.4, 11, f"{n}\n{d}", ORANGE, fs=6.9)

    store(ax, 30, 5.2, 52, 5.8, "models/  best_model.joblib - preprocessor.joblib - train_fused.npz - metadata.json ...", PALE_TEAL, TEAL, fs=6.9)
    store(ax, 78, 5.2, 36, 5.8, "data/raw/*.csv or synthetic fallback", PALE_TEAL, TEAL, fs=7.2)

    arrow(ax, (50, 62), (50, 59), "HTTP + JSON (Vite proxies /api, /predict)", lo=(24, 0), fs=7.4, color=NAVY)
    arrow(ax, (50, 33), (50, 30), "Python calls", lo=(9, 0), fs=7.4, color=NAVY)
    arrow(ax, (30, 12), (30, 8.2), None, color=NAVY)
    arrow(ax, (78, 12), (78, 8.2), None, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 6.8, 100, 68)
    ax.text(50, 65, "A. Training path (first start via store.ensure_artifacts, or scripts/train.py)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    steps = [("Startup table\n(public CSV or\nsynthetic fallback)", BLUE), ("prepare_frame\ndedup, target map,\nlog funding,\nmask names", TEAL), ("Embed every\ndescription\n(MiniLM, 384-d)", TEAL),
             ("5 x stratified\n80/20 splits\nseed 42", TEAL), ("Preprocess (train\nonly) + fuse\nthen fit 4 models", ORANGE), ("Mean +/- std,\nbest by balanced\naccuracy", PURPLE), ("Refit best on all\nrows, save 7\nartefacts", NAVY)]
    xs = [7.5 + i * 14.2 for i in range(7)]
    for x, (t, c) in zip(xs, steps):
        box(ax, x, 52, 12.8, 15, t, c, fs=7.1)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 6.5, 52), (b - 6.5, 52), None, color=NAVY)

    ax.text(50, 36.5, "B. Inference path (every POST /predict from the Analyze screen)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    steps2 = [("Startup profile\n19 fields +\nk in 10/20/30/50", BLUE), ("Validate\n(Pydantic ranges,\ndescription <= 2000)", TEAL), ("Scale + one-hot\n(37 features) and\nMiniLM embedding", TEAL), ("Fuse\n[0.5 s, 0.5 t]\nL2-normalised", ORANGE),
              ("predict_proba +\nbalanced top-k\nretrieval", PURPLE), ("Outcome, confidence,\nrisk, explanation,\nsimilar startups", NAVY)]
    xs2 = [8.5 + i * 16.6 for i in range(6)]
    for x, (t, c) in zip(xs2, steps2):
        box(ax, x, 22, 14.8, 14.5, t, c, fs=7.2)
    for a, b in zip(xs2[:-1], xs2[1:]):
        arrow(ax, (a + 7.6, 22), (b - 7.6, 22), None, color=NAVY)
    box(ax, 50, 5.4, 92, 6.2, "The same fitted preprocessor, model and training matrix saved in models/ are loaded once into STATE and reused by every request and by the Jinja pages", WHITE, tc=INK, ec=NAVY, fs=7.4)
    arrow(ax, (xs[-1], 44.2), (xs2[3] + 3, 29.6), "saved artefacts", color=ORANGE, ls="--", rad=-0.12, lo=(12, 1.6), fs=7.4)
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(10, 5.6, 100, 56)
    circle(ax, 50, 28, 14.5, "0\nStartup outcome\nprediction\nsystem", BLUE, fs=9.5)
    box(ax, 11, 28, 18, 34, "Founder /\ninvestor\n(analyst)", NAVY, fs=9.5, bold=True)
    box(ax, 89, 38, 18, 20, "Model owner\n(trainer)", NAVY, fs=9.5, bold=True)
    box(ax, 89, 10, 18, 14, "Startup table\n(CSV or synthetic\ngenerator)", GREY, fs=8.4, bold=True)
    import math

    def edge(y, side):
        dx = math.sqrt(max(14.5 ** 2 - (y - 28) ** 2, 0))
        return 50 - dx if side == "L" else 50 + dx

    def hflow(y, x1, x2, text, color, fwd=True, lo=(0, 2.2)):
        a, b = (x1, x2) if fwd else (x2, x1)
        arrow(ax, (a, y), (b, y), text, color=color, lo=lo, fs=7.2)
    hflow(41, 20, edge(41, "L"), "startup profile,\ndescription, k", BLUE, lo=(-1, 3.0))
    hflow(33, 20, edge(33, "L"), "sign-in (demo\ncredentials)", BLUE, lo=(-1, 3.0))
    hflow(23, 20, edge(23, "L"), "outcome, probabilities,\nrisk, explanation", TEAL, fwd=False, lo=(-1.5, 3.0))
    hflow(15, 20, edge(15, "L"), "similar startups, charts,\nmetrics, insights", TEAL, fwd=False, lo=(-1.5, 3.0))
    hflow(42, edge(42, "R"), 80, "train / evaluate\nrequest", BLUE, fwd=False, lo=(1, 3.0))
    hflow(34, edge(34, "R"), 80, "evaluation results,\nsaved artefacts", TEAL, lo=(1, 3.0))
    arrow(ax, (80, 12), (59.6, 19.8), "startup records (CSV)", color=BLUE, lo=(0, -3.0), fs=7.2)
    save(fig, OUT / "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(10, 7.4, 100, 74)
    box(ax, 9, 44, 15, 48, "Founder /\ninvestor", NAVY, fs=9, bold=True)
    box(ax, 9, 10, 15, 10, "Model\nowner", NAVY, fs=9, bold=True)
    circle(ax, 45, 64, 6.6, "1.0\nValidate\ninput", BLUE, fs=7.6)
    circle(ax, 45, 50, 6.6, "2.0\nPredict\noutcome", BLUE, fs=7.6)
    circle(ax, 45, 36, 6.6, "3.0\nRetrieve and\nexplain", BLUE, fs=7.4)
    circle(ax, 45, 22, 6.6, "4.0\nServe metrics\nand insights", BLUE, fs=7.2)
    circle(ax, 45, 7, 4.6, "5.0\nTrain", BLUE, fs=7)
    store(ax, 88, 50, 20, 9, "D1  model + preprocessor\n(joblib), metadata.json", PALE_TEAL, TEAL, fs=6.9)
    store(ax, 88, 36, 20, 9, "D2  train_fused.npz +\ntrain_frame.pkl", PALE_TEAL, TEAL, fs=6.9)
    store(ax, 88, 22, 20, 9, "D3  evaluation_\nresults.json", PALE_TEAL, TEAL, fs=7.2)
    store(ax, 88, 6, 20, 7, "D4  startup CSV", PALE_TEAL, TEAL, fs=7.2)
    arrow(ax, (16.5, 66), (38.4, 65), "startup profile", color=BLUE, lo=(0, 2.0), fs=7.2)
    arrow(ax, (38.4, 61.5), (16.5, 61), "422 error", color=ORANGE, lo=(0, -2.0), fs=7.2)
    arrow(ax, (45, 57.4), (45, 56.6), None, color=BLUE)
    ax.text(47, 57.0, "valid payload", fontsize=6.9, color=INK, ha="left", va="center")
    arrow(ax, (51.6, 50), (78, 50), "load model", color=TEAL, lo=(0, 2.0), fs=7.0)
    arrow(ax, (45, 43.4), (45, 42.6), None, color=BLUE)
    ax.text(47, 43.0, "fused vector, probabilities", fontsize=6.9, color=INK, ha="left", va="center")
    arrow(ax, (51.6, 36), (78, 36), "cosine search (train rows only)", color=TEAL, lo=(0, 2.0), fs=6.9)
    arrow(ax, (38.4, 35), (16.5, 35), "outcome, confidence, risk,\nexplanation, similar startups", color=TEAL, lo=(0, 3.4), fs=6.9)
    arrow(ax, (16.5, 24.2), (38.6, 23.6), "view request", color=BLUE, lo=(0, 1.8), fs=7.0)
    arrow(ax, (38.6, 20.2), (16.5, 21.0), "metrics, insights,\nfeature weights", color=TEAL, lo=(0, -3.2), fs=7.0)
    arrow(ax, (78, 22), (51.6, 22), "results", color=TEAL, lo=(0, 2.0), fs=7.0)
    arrow(ax, (16.5, 10), (40.6, 7.4), "train request", color=BLUE, lo=(0, -2.2), fs=7.0)
    arrow(ax, (78, 6), (49.6, 6.8), "startup rows", color=BLUE, lo=(0, 2.0), fs=7.0)
    arrow(ax, (48.5, 10.6), (78, 18.6), "writes D1, D2, D3", color=TEAL, ls="--", lo=(2.5, -2.8), fs=7.0)
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.text(50, 71, "Decomposition of 2.0 Predict outcome and 3.0 Retrieve and explain  (predictor.predict_one)", ha="center", fontsize=9, color=NAVY, fontweight="bold")
    xs = [12, 37.5, 63, 88]
    y1, y2 = 56, 30
    for x, (n, t) in zip(xs, [("2.1", "build_input_row\nlog1p funding,\ntyped DataFrame"), ("2.2", "pre.transform\nimpute, scale,\none-hot (37-d)"),
                              ("2.3", "embed_texts\n(description or\n'<industry> startup')"), ("2.4", "fuse + L2\n[0.5 s, 0.5 t]\n(421-d)")]):
        circle(ax, x, y1, 7.6, f"{n}\n{t}", BLUE, fs=6.6)
    for a_, b_ in zip(xs[:-1], xs[1:]):
        arrow(ax, (a_ + 7.7, y1), (b_ - 7.7, y1), None, color=NAVY)
    for x, (n, t) in zip([88, 63, 37.5, 12], [("2.5", "model.\npredict_proba\nargmax, max"), ("3.1", "retrieve_similar\nbalanced top-k\ncosine"), ("3.2", "explanation\ntop-5 terms +\nretrieval stats"), ("3.3", "risk label\nand JSON\nresponse")]):
        circle(ax, x, y2, 7.6, f"{n}\n{t}", BLUE if n.startswith("2") else TEAL, fs=6.6)
    arrow(ax, (88, y1 - 7.7), (88, y2 + 7.7), "fused vector", color=NAVY, lo=(-7, 0), fs=7.0)
    arrow(ax, (80.3, y2), (70.7, y2), None, color=NAVY)
    ax.text(75.5, y2 + 2.4, "P(success)", fontsize=6.9, color=INK, ha="center")
    arrow(ax, (63, y1 - 7.7), (63, y2 + 7.7), "fused vector", color=NAVY, lo=(-7, 0), fs=7.0)
    arrow(ax, (55.4, y2), (45.2, y2), "similar rows", color=NAVY, lo=(0, 2.2), fs=7.0)
    arrow(ax, (29.9, y2), (19.7, y2), "bullets, risk", color=NAVY, lo=(0, 2.2), fs=7.0)
    box(ax, 12, 7.5, 20, 8, "Analyze screen\n(outcome, evidence)", NAVY, fs=7.4)
    arrow(ax, (12, y2 - 7.7), (12, 11.6), "JSON", color=TEAL, lo=(3.5, 0), fs=7.0)
    store(ax, 37.5, 43, 22, 7.5, "D1  preprocessor.joblib", PALE_TEAL, TEAL, fs=6.9)
    arrow(ax, (37.5, 46.8), (37.5, y1 - 7.7), None, color=TEAL, ls="--")
    store(ax, 88, 9, 22, 8.5, "D2  best_model.joblib,\nmetadata.json (also 3.2)", PALE_TEAL, TEAL, fs=6.7)
    arrow(ax, (88, 13.3), (88, y2 - 7.7), None, color=TEAL, ls="--")
    ax.text(89.5, 21.5, "fitted model", fontsize=6.9, color=INK, ha="left")
    store(ax, 63, 9, 22, 8.5, "D3  train_fused.npz,\ntrain_frame.pkl", PALE_TEAL, TEAL, fs=6.9)
    arrow(ax, (63, 13.3), (63, y2 - 7.7), None, color=TEAL, ls="--")
    ax.text(64.5, 21.5, "training matrix", fontsize=6.9, color=INK, ha="left")
    ax.text(12, 67.2, "from 1.0: validated payload", fontsize=7.0, color=INK, ha="center")
    arrow(ax, (12, 66), (12, 63.8), None, color=BLUE)
    save(fig, OUT / "05_dfd_level2.png")


# --------------------------------------------------------------------------------------------------
def uml_class_diagram():
    fig, ax = canvas(10, 8.4, 100, 84)
    W = 27.5
    xs = [1.5, 35.5, 69.0]
    t1, t2, t3 = 82.5, 45.0, 22.0
    fs = 6.2
    pp = uml_class(ax, xs[0], t1, W, "PredictPayload", ["funding_total_usd [0, 1e10]", "funding_rounds [0, 20]", "age_first/last_funding_year", "age_first/last_milestone_year",
                   "relationships [0,200]", "milestones [0,50], avg_participants", "has_VC, has_angel, has_roundA-D,", "is_top500: bool", "state, industry_type: str",
                   "description: str (<= 2000)", "k: int  in {10,20,30,50}"], ["check_desc(v)", "check_k(v)"], hdr=TEAL, stereotype="pydantic BaseModel", fs=fs)
    app = uml_class(ax, xs[1], t1, W, "FastAPI app", ["router: APIRouter (api_extra)", "templates: Jinja2Templates"],
                    ["predict_api(payload)", "predict_form_post(...)", "health()  model_metrics()", "insights()  config()", "feature_importance(top)", "login(p)  me(authorization)"],
                    hdr=NAVY, stereotype="main.py + api_extra.py", fs=fs)
    st = uml_class(ax, xs[2], t1, W, "Store", ["STATE: dict", "  model, pre, train_fused,", "  train_df, metadata, results"],
                   ["ensure_artifacts() -> dict"], hdr=PURPLE, stereotype="services/store.py", fs=fs)
    rt = uml_class(ax, xs[0], t2, W, "Retrieval", ["ALPHA = 0.5"], ["fuse(structured, text_emb, alpha)", "retrieve_similar(target_fused,", "   train_fused, train_df, k)"], hdr=BLUE, stereotype="ml/retrieval.py", fs=fs)
    pr = uml_class(ax, xs[1], t2, W, "Predictor", [], ["build_input_row(payload)", "predict_one(payload, state, k)"], hdr=BLUE, stereotype="services/predictor.py", fs=fs)
    em = uml_class(ax, xs[2], t2, W, "Embeddings", ["EMBEDDING_MODEL_NAME", "EMBEDDING_DIM = 384"], ["load_model()", "embed_texts(texts)", "l2norm(a)"], hdr=BLUE, stereotype="ml/embeddings.py", fs=fs)
    pp3 = uml_class(ax, xs[0], t3, W, "Preprocessing", ["NUMERIC / BINARY /", "CATEGORICAL_FEATURES"], ["prepare_frame(df)", "build_preprocessor()", "feature_names(pre)"], hdr=ORANGE, stereotype="ml/preprocessing.py", fs=fs)
    ev = uml_class(ax, xs[1], t3, W, "Evaluation + Models", ["N_SPLITS = 5, TEST_SIZE = 0.2", "RANDOM_STATE = 42", "RETRIEVAL_KS = [10,20,30,50]"], ["get_models() -> dict (4)", "run_evaluation(df, meta)", "compute_metrics(y, pred)"], hdr=ORANGE, stereotype="ml/evaluation.py, models.py", fs=fs)
    ds = uml_class(ax, xs[2], t3, W, "Dataset + Insights", ["EXPECTED_COLUMNS (20)", "STATES, INDUSTRIES"], ["load_dataset(force_synthetic)", "generate_synthetic(n, seed)", "map_target(s), clean_text(t)", "compute_insights(df)"], hdr=ORANGE, stereotype="ml/dataset.py, insights.py", fs=fs)

    def link(p1, p2, label=None, lo=(0, 1.3), fs_=6.4):
        arrow(ax, p1, p2, label, color=GREY, lw=1.2, fs=fs_, lo=lo, style="->")
    yl = 70.0
    link((xs[1], yl), (xs[0] + W, yl), "uses", lo=(0, 1.3))
    link((xs[1] + W, yl), (xs[2], yl), "ensure_\nartifacts()", lo=(0, 3.0))
    link((xs[1] + 14, app[1]), (xs[1] + 14, t2), "predict_one()", lo=(7.5, 0))
    yr = t2 - 8
    link((xs[1], yr), (xs[0] + W, yr), "fuse,\nretrieve", lo=(0, 3.0))
    link((xs[1] + W, yr), (xs[2], yr), "embed_\ntexts", lo=(0, 3.0))
    link((xs[1] + 4, pr[1]), (xs[0] + 20, t3), "pre.transform", lo=(-1.5, 1.2))
    yv = t3 - 8
    link((xs[1], yv), (xs[0] + W, yv), "build_\npreproc.", lo=(0, 3.0))
    link((xs[2], yv), (xs[1] + W, yv), "df, meta", lo=(0, 1.5))
    mx = xs[2] + W + 1.8
    ax.plot([xs[2] + W, mx, mx], [70.0, 70.0, 14.0], color=GREY, lw=1.2, zorder=3)
    arrow(ax, (mx, 14.0), (xs[2] + W, 14.0), None, color=GREY, lw=1.2, style="->")
    ax.text(mx + 1.1, 42.0, "first start: load_dataset, then run_evaluation", fontsize=6.2, color=INK, rotation=90, ha="center", va="center")
    save(fig, OUT / "06_uml_class_diagram.png")


# --------------------------------------------------------------------------------------------------
def sequence_diagram():
    fig, ax = canvas(10, 9.3, 100, 93)
    ax.text(50, 90.3, "POST /predict - main flow of the Analyze screen", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    names = [("Analyze.jsx\n(React)", BLUE), ("FastAPI\npredict_api", TEAL), ("store\nSTATE", PURPLE), ("predictor\npredict_one", TEAL), ("embeddings +\nretrieval", ORANGE), ("best model\n(joblib)", NAVY)]
    xs = [8, 24, 40, 56, 72, 89]
    for x, (n, c) in zip(xs, names):
        box(ax, x, 84, 14, 7, n, c, fs=7.3, bold=True)
        ax.plot([x, x], [80.3, 2], color="#9AA7B8", lw=1.0, ls=(0, (4, 3)), zorder=1)
    y = 77.0
    acts = {}

    def msg(a, b, text, dash=False):
        nonlocal y
        ax.add_patch(FancyArrowPatch((xs[a], y), (xs[b], y), arrowstyle="-|>", mutation_scale=11, color=TEAL if dash else NAVY, lw=1.3, ls="--" if dash else "-", zorder=4))
        ax.text((xs[a] + xs[b]) / 2, y + 0.9, text, fontsize=6.6, color=INK, ha="center", va="bottom", bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9), zorder=6)
        y0 = y
        y -= 4.7
        return y0

    def selfmsg(a, text):
        nonlocal y
        xa = xs[a]
        ax.plot([xa, xa + 6.0, xa + 6.0], [y, y, y - 2.4], color=NAVY, lw=1.3, zorder=4)
        ax.add_patch(FancyArrowPatch((xa + 6.0, y - 2.4), (xa, y - 2.4), arrowstyle="-|>", mutation_scale=11, color=NAVY, lw=1.3, zorder=4))
        ax.text(xa + 7.2, y - 1.2, text, fontsize=6.6, color=INK, va="center", ha="left", bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.9), zorder=6)
        y0 = y
        y -= 6.0
        return y0

    s1 = msg(0, 1, "1  POST /predict  {fields, description, k}")
    selfmsg(1, "2  PredictPayload: ranges, description <= 2000, k")
    msg(1, 2, "3  ensure_artifacts()")
    msg(2, 1, "4  STATE (model, pre, train_fused, train_df)", True)
    s5 = msg(1, 3, "5  predict_one(payload, state, k)")
    selfmsg(3, "6  build_input_row; S = pre.transform(row)")
    msg(3, 4, "7  embed_texts(description) -> T (384-d)")
    msg(3, 4, "8  F = fuse(S, T, 0.5)")
    msg(3, 5, "9  predict_proba(F)")
    msg(5, 3, "P(failure), P(success)", True)
    msg(3, 4, "10  retrieve_similar(F, train_fused, train_df, k)")
    msg(4, 3, "k comparable rows (half SUCCESS / half FAILURE)", True)
    selfmsg(3, "11  explanation bullets + risk label")
    s14 = msg(3, 1, "12  result dict (outcome, risk, similar[], explanation[])", True)
    s15 = msg(1, 0, "13  200 JSON  (422 / 500 with detail on error)", True)
    ax.add_patch(Rectangle((xs[1] - 0.9, s15 - 0.6), 1.8, s1 - s15 + 0.6, fc=PALE_BLUE, ec=BLUE, lw=1, zorder=2))
    ax.add_patch(Rectangle((xs[3] - 0.9, s14 - 0.6), 1.8, s5 - s14 + 0.6, fc=PALE_BLUE, ec=BLUE, lw=1, zorder=2))
    save(fig, OUT / "07_sequence_diagram.png")


# --------------------------------------------------------------------------------------------------
def use_case_diagram():
    fig, ax = canvas(10, 6.4, 100, 64)
    ax.add_patch(FancyBboxPatch((22, 1.5), 62, 61, boxstyle="round,pad=0,rounding_size=1.5", fc="#F8FAFC", ec=NAVY, lw=1.6, zorder=1))
    ax.text(53, 59.3, "VenturePulse (React 5410 + FastAPI 8410)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    L, Rr = 37, 70
    ucs = {
        "login": (L, 51, "Sign in (demo account)"),
        "dash": (L, 41, "View dashboard"),
        "analyze": (L, 30, "Analyze a startup"),
        "perf": (L, 18, "View model performance"),
        "ins": (L, 8, "View startup insights"),
        "val": (Rr, 41, "Validate inputs"),
        "sim": (Rr, 30, "Inspect comparable\nstartups"),
        "feat": (Rr, 19.5, "See key contributing\nfeatures"),
        "train": (Rr, 8, "Train / evaluate models"),
    }
    for k, (x, y, t) in ucs.items():
        ellipse(ax, x, y, 24, 7.6, t, fc=PALE_BLUE, ec=BLUE, fs=7.3)

    def actor(x, y, label):
        ax.add_patch(Circle((x, y + 6), 1.8, fc="white", ec=NAVY, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 4.2, y - 1.5], color=NAVY, lw=1.6, zorder=3)
        ax.plot([x - 3, x + 3], [y + 2.6, y + 2.6], color=NAVY, lw=1.6, zorder=3)
        ax.plot([x, x - 2.6], [y - 1.5, y - 6], color=NAVY, lw=1.6, zorder=3)
        ax.plot([x, x + 2.6], [y - 1.5, y - 6], color=NAVY, lw=1.6, zorder=3)
        ax.text(x, y - 8.6, label, ha="center", fontsize=8, fontweight="bold", color=NAVY)
    actor(9, 33, "Founder /\ninvestor")
    actor(92.5, 13, "Model owner")
    for k in ["login", "dash", "analyze", "perf", "ins"]:
        x, y, _ = ucs[k]
        arrow(ax, (13, 36), (x - 12, y), None, color=GREY, lw=1.0, style="-")
    arrow(ax, (89, 15), (Rr + 12, 8), None, color=GREY, lw=1.0, style="-")
    arrow(ax, (L + 12, 32.2), (Rr - 12, 40.0), "<<include>>", color=ORANGE, lw=1.2, ls="--", lo=(0, 2.2), fs=6.8)
    arrow(ax, (L + 12, 30), (Rr - 12, 30), "<<include>>", color=ORANGE, lw=1.2, ls="--", lo=(0, 1.8), fs=6.8)
    arrow(ax, (L + 12, 27.8), (Rr - 12, 21.4), "<<include>>", color=ORANGE, lw=1.2, ls="--", lo=(0, -2.2), fs=6.8)
    arrow(ax, (L, 47.2), (L, 44.8), None, color=ORANGE, lw=1.0, ls="--")
    ax.text(L + 1.2, 46.0, "<<precede>>", fontsize=6.6, color=INK, ha="left", va="center")
    save(fig, OUT / "08_use_case_diagram.png")


# --------------------------------------------------------------------------------------------------
def er_diagram():
    fig, ax = canvas(10, 9.2, 100, 92)
    ax.text(50, 90.3, "File-based data model (no SQL database): models/, evaluation/ and the request / response objects", ha="center", fontsize=8.8, color=NAVY, fontweight="bold")

    def ent(x, y, w, name, attrs, hdr=NAVY, fs=6.4):
        lh = 2.35
        h_head = 3.5
        h = h_head + lh * len(attrs) + 1.0
        ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.2, zorder=2))
        ax.add_patch(Rectangle((x, y - h_head), w, h_head, fc=hdr, ec=NAVY, lw=1.2, zorder=3))
        ax.text(x + w / 2, y - h_head / 2, name, ha="center", va="center", color=WHITE, fontsize=fs + 0.9, fontweight="bold", zorder=4)
        for i, a in enumerate(attrs):
            ax.text(x + 0.8, y - h_head - 1.5 - i * lh, a, ha="left", va="center", fontsize=fs, color=INK, zorder=4, family="DejaVu Sans Mono")
        return (x, y - h, w, h)

    W = 29.5
    X = [1.5, 35.5, 69.5]
    r1, r2, r3 = 86, 61, 30
    a = ent(X[0], r1, W, "STARTUP_RECORD (train_frame.pkl)", ["PK row_index", "20 raw columns (funding, rounds,", "  ages, relationships, flags,", "  state, industry_type, description)", "label  0 / 1", "outcome  SUCCESS / FAILURE", "log_funding_total_usd"], hdr=TEAL)
    b = ent(X[1], r1, W, "FUSED_MATRIX (train_fused.npz)", ["PK/FK row_index", "fused  float32 [n x 421]", "  = 0.5 * structured (37)", "  + 0.5 * text (384),", "  L2-normalised"], hdr=ORANGE)
    c = ent(X[2], r1, 29, "TEXT_EMBEDDING (.npz)", ["PK/FK row_index", "embeddings float32 [n x 384]", "  all-MiniLM-L6-v2", "  (text_embeddings.npz)"], hdr=ORANGE)
    d = ent(X[0], r2, W, "SIMILAR_CASE (item of similar[])", ["FK row_index (a STARTUP_RECORD)", "similarity  (cosine)", "outcome, industry, state", "funding_total_usd, funding_rounds", "relationships, milestones", "description  (first 280 chars)"], hdr=BLUE)
    e = ent(X[1], r2, W, "PREDICTION_RESULT (JSON)", ["outcome, model, risk, k", "probability_success / failure", "confidence", "similar_counts {SUCCESS, FAILURE}", "explanation[]  (bullets)", "embedding_backend", "similar[]  (up to k items)"], hdr=BLUE)
    f = ent(X[2], r2, 29, "PREDICTION_REQUEST (PredictPayload)", ["funding_total_usd, funding_rounds", "age_first/last_funding_year", "age_first/last_milestone_year", "relationships, milestones", "avg_participants", "has_VC, has_angel, has_roundA-D", "is_top500, state, industry_type", "description  (<= 2000 chars)", "k  in {10, 20, 30, 50}"], hdr=BLUE)
    g = ent(X[0], r3, W, "PREPROCESSOR + BEST_MODEL (.joblib)", ["preprocessor.joblib ColumnTransformer", "  num: median + StandardScaler", "  bin: most_frequent", "  cat: constant + OneHotEncoder", "best_model.joblib, fitted on", "  fused [n x 421]"], hdr=PURPLE)
    h = ent(X[1], r3, W, "METADATA (metadata.json)", ["best_model", "model_names[]  (4)", "feature_names_structured[] (37)", "structured_dim 37, embedding_dim 384", "alpha 0.5, n_train", "class_counts, dataset_meta"], hdr=PURPLE)
    i = ent(X[2], r3, 29, "EVALUATION_RESULTS (.json)", ["models{}  per model:", "  accuracy, balanced_accuracy,", "  precision, recall, F1 (mean, std)", "  confusion_matrix_mean / _last", "representations{}, retrieval_k{}"], hdr=PURPLE)

    def rel(p1, p2, label, lo=(0, 1.5)):
        arrow(ax, p1, p2, label, color=GREY, lw=1.3, fs=6.9, lo=lo, style="-")
    rel((X[0] + W, r1 - 8), (X[1], r1 - 8), "1 : 1")
    rel((X[1] + W, r1 - 8), (X[2], r1 - 8), "1 : 1")
    rel((X[2], r2 - 8), (X[1] + W, r2 - 8), "1 : 1")
    rel((X[1], r2 - 8), (X[0] + W, r2 - 8), "1 : N")
    rel((X[0] + 15, r2), (X[0] + 15, a[1]), None)
    ax.text(X[0] + 16.2, (r2 + a[1]) / 2, "N : 1  (each similar case is a training row)", fontsize=6.5, color=INK, va="center", ha="left")
    rel((X[1] + 15, e[1]), (X[1] + 15, r3), None)
    ax.text(X[1] + 16.2, (e[1] + r3) / 2, "model = best_model name", fontsize=6.5, color=INK, va="center", ha="left")
    rel((X[0] + W, r3 - 8), (X[1], r3 - 8), "1 : 1")
    rel((X[1] + W, r3 - 8), (X[2], r3 - 8), "1 : N")
    ax.text(50, 5.0, "Runtime state: STATE dict = {model, pre, train_fused, train_df, metadata, results}, built once by store.ensure_artifacts()", ha="center", fontsize=7.2, color=INK,
            bbox=dict(fc=PALE_TEAL, ec=TEAL, pad=3))
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------------------------------------------
def algo_flowchart():
    DY = 7.0
    fig, ax = canvas(10, 11.3, 100, 113)
    cx, rx = 32, 80

    def term(x, y, t, w=34, c=NAVY):
        box(ax, x, y + DY, w, 5.4, t, c, fs=7.8, bold=True, r=2.6)

    def proc(x, y, t, w=50, h=6.8, c=BLUE):
        box(ax, x, y + DY, w, h, t, c, fs=7.2)

    def dec(x, y, t, w=36, h=9.6):
        diamond(ax, x, y + DY, w, h, t, fs=7.0)

    def a(p1, p2, label=None, lo=(0, 1.3)):
        arrow(ax, (p1[0], p1[1] + DY), (p2[0], p2[1] + DY), label, color=NAVY, lw=1.4, fs=7.2, lo=lo)

    term(cx, 102.5, "POST /predict received")
    proc(cx, 93.5, "PredictPayload validation\n(types, ranges, description <= 2000, k)")
    dec(cx, 82.5, "payload valid?")
    term(rx, 82.5, "HTTP 422 + detail", w=28, c=ORANGE)
    proc(cx, 71.5, "state = ensure_artifacts()\n(train and save if files are missing)")
    proc(cx, 62.5, "build_input_row\nlog1p(funding), typed values")
    proc(cx, 53.5, "S = pre.transform(row)\n(median impute, scale, one-hot: 37 features)")
    dec(cx, 43.0, "description\nempty?")
    proc(rx, 43.0, "text = '<industry> startup'", w=32, c=GREY)
    proc(cx, 31.5, "T = embed_texts(text[:2000]);  F = fuse(S, T, 0.5)\nL2-normalised 421-d vector", w=56, h=7.4)
    proc(cx, 21.5, "proba = model.predict_proba(F)\npred = argmax;  confidence = max(proba)", w=52, h=7.2, c=PURPLE)
    proc(cx, 11.0, "retrieve_similar: cosine(F, train_fused), quota k//2 SUCCESS\n+ k - k//2 FAILURE, fill if short, sort by similarity", w=54, h=8.0, c=TEAL)
    proc(rx, 11.0, "explanation: top-5 |coef| (LR)\nor importance (trees)\n+ retrieval statistics", w=30, h=9.0, c=TEAL)
    proc(rx, -2.0, "risk label: SUCCESS and conf >= 0.70\n= Lower risk; conf >= 0.55 = Moderate risk;\notherwise Higher uncertainty", w=38, h=9.4, c=GREY)
    term(cx, -2.0, "200 JSON response", w=30)
    a((cx, 99.8), (cx, 96.9))
    a((cx, 90.1), (cx, 87.3))
    a((cx + 18, 82.5), (rx - 14, 82.5), "no", lo=(0, 1.4))
    a((cx, 77.7), (cx, 74.9), "yes", lo=(2.5, 0))
    a((cx, 68.1), (cx, 65.9))
    a((cx, 59.1), (cx, 56.9))
    a((cx, 50.1), (cx, 47.8))
    a((cx + 18, 43.0), (rx - 16, 43.0), "yes", lo=(0, 1.4))
    a((cx, 38.2), (cx, 35.2), "no", lo=(2.5, 0))
    ax.plot([rx, rx], [38.5 + DY, 34.4 + DY], color=NAVY, lw=1.4, zorder=4)
    a((rx, 34.4), (cx + 28, 34.4))
    a((cx, 27.8), (cx, 25.1))
    a((cx, 17.9), (cx, 15.0))
    a((cx + 27, 11.0), (rx - 15, 11.0))
    a((rx, 6.5), (rx, 2.8))
    a((rx - 19, -2.0), (cx + 15, -2.0))
    save(fig, OUT / "10_core_algorithm_flowchart.png")


# --------------------------------------------------------------------------------------------------
def evaluation_protocol():
    fig, ax = canvas(10, 8.6, 100, 86)
    panel(ax, 1.5, 46, 97, 38, "A. Shipped application - app/ml/evaluation.py run_evaluation()  (the model the screens use)", PALE_BLUE, BLUE, tc=NAVY)
    top = [("Startup table\nCSV in data/raw/ or\nsynthetic fallback\n(1,400 rows)", GREY), ("prepare_frame\ndedup, map target\n(acquired / IPO = 1,\nclosed = 0)", TEAL), ("Embed all\ndescriptions once\n(MiniLM, 384-d)", TEAL),
           ("5 x Stratified\nShuffleSplit\n80 / 20, seed 42", ORANGE)]
    xs = [12.5, 37.5, 62.5, 87.5]
    for x, (t, c) in zip(xs, top):
        box(ax, x, 69.5, 21, 12.5, t, c, fs=7.0)
    for a_, b_ in zip(xs[:-1], xs[1:]):
        arrow(ax, (a_ + 10.7, 69.5), (b_ - 10.7, 69.5), None, color=NAVY)
    mid = [("Per split: fit\npreprocessor on TRAIN\nonly; fuse train and\ntest (alpha 0.5)", PURPLE), ("Fit 4 models:\nLR, Decision Tree,\nRandom Forest,\nXGBoost", PURPLE), ("Studies on the split:\nLR on structured /\ntext / combined;\nretrieval k = 10-50", PURPLE),
           ("Metrics on test:\naccuracy, balanced acc.,\nprecision, recall, F1,\nconfusion matrix", NAVY)]
    for x, (t, c) in zip(xs, mid):
        box(ax, x, 52.5, 21, 12.5, t, c, fs=7.0)
    for a_, b_ in zip(xs[:-1], xs[1:]):
        arrow(ax, (a_ + 10.7, 52.5), (b_ - 10.7, 52.5), None, color=NAVY)
    arrow(ax, (87.5, 63.3), (12.5, 58.9), "repeat for each of the 5 splits", color=ORANGE, lo=(-6, -2.6), fs=7.2, ls="--")
    box(ax, 50, 40.0, 94, 7.0, "Mean +/- std over 5 splits  ->  best = highest balanced accuracy (Logistic Regression)  ->  refit on all rows\n->  save best_model, preprocessor, train_fused, text_embeddings, train_frame, metadata, evaluation_results",
        WHITE, tc=INK, ec=BLUE, fs=7.0)
    arrow(ax, (87.5, 46.2), (87.5, 43.6), None, color=NAVY)
    panel(ax, 1.5, 2.5, 97, 32, "B. Real-data studies: scripts/run_experiments.py, extra_experiments.py  (models/ untouched)", PALE_ORANGE, ORANGE, tc=NAVY)
    low = [("data/real/\nstartup_data.csv\n923 rows -> 922\nafter dedup", GREY), ("Same prepare_frame;\nstructured columns\nonly (no text exists)", TEAL), ("Same 5 x 80/20\nsplits, seed 42;\n+ 5 x 70:30 split", ORANGE),
           ("5 models + ROC-AUC, PR-AUC;\nimbalance, threshold,\ncalibration, RF size,\nsynthetic -> real transfer", PURPLE)]
    for x, (t, c) in zip(xs, low):
        box(ax, x, 23.5, 21, 12.5, t, c, fs=6.9)
    for a_, b_ in zip(xs[:-1], xs[1:]):
        arrow(ax, (a_ + 10.7, 23.5), (b_ - 10.7, 23.5), None, color=NAVY)
    box(ax, 50, 8.6, 92, 7.0, "extra_experiments.py: leakage ablation (drop relationships, milestones and the two milestone ages),\nretrieval-only classifier (balanced top-k vote), per-industry accuracy", WHITE, tc=INK, ec=ORANGE, fs=7.0)
    arrow(ax, (87.5, 17.2), (87.5, 12.2), None, color=NAVY)
    save(fig, OUT / "11_evaluation_protocol.png")


if __name__ == "__main__":
    system_architecture()
    high_level_workflow()
    dfd0()
    dfd1()
    dfd2()
    uml_class_diagram()
    sequence_diagram()
    use_case_diagram()
    er_diagram()
    algo_flowchart()
    evaluation_protocol()
