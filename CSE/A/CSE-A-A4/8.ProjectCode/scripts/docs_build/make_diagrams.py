"""Draw the SecurePay AI design diagrams into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: backend/app.py + api_extra.py (routes), preprocessing.py, rbm_classifier.py,
samplers.py, train.py, evaluation.py, and the React pages in frontend/src/pages.
    python scripts/docs_build/make_diagrams.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def title(ax, x, y, text):
    ax.text(x, y, text, ha="center", fontsize=10, color=NAVY, fontweight="bold")


def pbox(ax, cx, cy, w, h, text, fc=NAVY, fs=7.6, **kw):
    return box(ax, cx, cy, w, h, text, fc, fs=fs, **kw)


# --------------------------------------------------------------------------------------------------
def system_architecture():
    fig, ax = canvas(10, 8.6, 100, 86)
    panel(ax, 2, 67, 96, 18, "Presentation tier - React + Vite single-page app (dev server, port 5304)", PALE_BLUE, BLUE)
    pbox(ax, 17, 73, 28, 10, "Pages (frontend/src/pages)\nLanding - Dashboard - Verify\nBulk - Analytics - Models - Lab", BLUE)
    pbox(ax, 48, 73, 26, 10, "lib/api.js\nfetch wrapper over /api\nVite proxy -> 127.0.0.1:8304", BLUE)
    pbox(ax, 77, 73, 30, 10, "UI kit\nRecharts charts, motion, theme\n(light / dark), toasts", BLUE)

    panel(ax, 2, 45, 96, 20, "Application tier - Flask 3.1 + Flask-CORS (port 8304)", PALE_TEAL, TEAL)
    pbox(ax, 16, 51.5, 26, 11, "backend/app.py\n12 routes: health, dataset,\npreprocess, train, comparison,\nqubo, predict_single/batch, export", TEAL, fs=7.2)
    pbox(ax, 44, 51.5, 26, 11, "backend/api_extra.py\n(blueprint, read-only)\ndataset_stats, model_history,\nfeature_importance, sample_batch", TEAL, fs=7.2)
    pbox(ax, 72, 51.5, 24, 11, "In-memory store\ndf_raw, pipeline_res,\nmodels, histories,\nfeature_importance", TEAL, fs=7.2)
    pbox(ax, 91, 51.5, 12, 11, "Guards\nCORS\ntry/except\n500 JSON", TEAL, fs=6.8)

    panel(ax, 2, 22, 96, 21, "Model tier - Python modules (backend/)", PALE_ORANGE, ORANGE)
    mods = [("preprocessing.py", "one-hot, z-score,\ncorr. filter, RF top-k,\nundersampling"), ("rbm_classifier.py", "GRBMC: W, U, b, c, d,\nGibbs / PCD,\nfree-energy scoring"),
            ("samplers.py", "simulated-annealing and\nquantum-inspired\ngradient samplers"), ("train.py", "per-epoch loop,\nlr schedules,\nhistory metrics"),
            ("evaluation.py", "accuracy, precision,\nrecall, F1, ROC-AUC,\nconfusion matrix")]
    for i, (n, d) in enumerate(mods):
        pbox(ax, 10.8 + i * 19.1, 34, 17.4, 11, f"{n}\n{d}", ORANGE, fs=6.8)
    pbox(ax, 50, 25.2, 90, 3.0, "synthetic_data.py generates the 39,000-row transaction file", WHITE, tc=INK, ec=ORANGE, fs=7.2)

    panel(ax, 2, 1.5, 96, 18.5, "Data tier - local files (no SQL database, nothing leaves the machine)", LIGHT, "#B7C3D3")
    store(ax, 14, 9, 22, 9.5, "data/\ncreditcard_synthetic.csv\n39,000 rows x 29 cols", fs=6.9)
    store(ax, 38, 9, 22, 9.5, "models/pipeline.pkl\nscaler, columns,\nfeature importance", fs=6.9)
    store(ax, 61, 9, 22, 9.5, "models/grbmc_*.pkl (3)\nhistory_*.json (3)", fs=6.9)
    store(ax, 85, 9, 24, 9.5, "data/batch_predictions.csv\nwritten after each\nbulk upload", fs=6.9)

    arrow(ax, (50, 67), (50, 65), "JSON over HTTP, multipart CSV", lo=(18, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 45), (50, 43), "Python imports", lo=(9, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 22), (50, 20), "joblib / pandas read-write", lo=(13, 0), fs=7.2, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 6.4, 100, 64)
    title(ax, 50, 61, "Two paths through the system: build the models, then score transactions")
    ax.text(2, 55, "A. Build path (Model lab or seed_models.py)", fontsize=8.6, color=NAVY, fontweight="bold")
    top = [("Generate data", "synthetic fraud and\nlegitimate rows", BLUE), ("Preprocess", "one-hot, z-score,\ncorr. filter, balance", BLUE),
           ("Select features", "RF importance,\ntop-k columns", TEAL), ("Split 80 / 20", "stratified,\nrandom_state 42", TEAL), ("Train 3 models", "PCD, SAS, QS,\nper-epoch metrics", PURPLE),
           ("Save", "grbmc_*.pkl,\nhistory_*.json", NAVY)]
    xs = [9.5 + i * 16.2 for i in range(6)]
    for x, (t, d, c) in zip(xs, top):
        pbox(ax, x, 45, 14, 11, f"{t}\n{d}", c, fs=7.4)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.1, 45), (b - 7.1, 45), color=NAVY)
    arrow(ax, (xs[-1], 39.3), (xs[-1], 29), "models loaded\nat start-up", lo=(-9, 0), fs=7, color=GREY, ls="--")

    ax.text(2, 31, "B. Score path (Verify and Bulk pages)", fontsize=8.6, color=NAVY, fontweight="bold")
    bot = [("Input", "form values or\nCSV upload", BLUE), ("Build features", "fill defaults,\none-hot, align", TEAL), ("Scale", "z-score step\n(skipped in code)", ORANGE),
           ("Score", "3 models,\nfraud probability", PURPLE), ("Ensemble", "mean of 3,\nthreshold 0.5", PURPLE), ("Decision", "risk band, label,\nCSV export", NAVY)]
    for x, (t, d, c) in zip(xs, bot):
        pbox(ax, x, 18, 14, 11, f"{t}\n{d}", c, fs=7.4)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.1, 18), (b - 7.1, 18), color=NAVY)
    ax.text(50, 6, "Risk bands: below 40 % LOW (approve), 40-70 % MEDIUM (3-D Secure challenge), above 70 % HIGH (decline and alert)", ha="center", fontsize=7.8, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(9.4, 5.6, 100, 60)
    circle(ax, 50, 30, 13.5, "0\nSecurePay AI\nfraud screening", BLUE, fs=10.5)
    pbox(ax, 12, 46, 20, 9, "Merchant /\nanalyst", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    pbox(ax, 12, 14, 20, 9, "Risk-operations\nteam", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    store(ax, 88, 30, 20, 10, "Local files\n(CSV, pickles, JSON)", fs=8.5)
    arrow(ax, (22, 47), (39, 38.5), "transaction fields,\nCSV file", lo=(-3, 5.5), fs=7.8)
    arrow(ax, (39.5, 34), (22, 43), "fraud score, risk level,\ndecision", lo=(-3, -6.8), fs=7.8)
    arrow(ax, (22, 15), (39, 24), "retrain request,\nview requests", lo=(-3, 5.5), fs=7.8)
    arrow(ax, (39.5, 21.5), (22, 12), "analytics, model metrics,\npredictions CSV", lo=(1, -5.2), fs=7.8)
    arrow(ax, (63.5, 33), (78, 33), "read / write", lo=(0, 3.2), fs=7.8)
    arrow(ax, (78, 27), (63.5, 27), "data, models", lo=(0, -2.8), fs=7.8)
    ax.text(50, 5, "No external system: the application needs no login, no network service and no quantum hardware.", ha="center", fontsize=7.8, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


# --------------------------------------------------------------------------------------------------
def dfd1():
    fig, ax = canvas(10, 7.4, 100, 74)
    title(ax, 50, 72.5, "DFD level 1 - six processes, four data stores (no SQL database)")
    pbox(ax, 8, 60, 13, 7.5, "Risk-ops\nteam", WHITE, tc=INK, ec=NAVY, fs=7.6, bold=True)
    pbox(ax, 8, 36, 13, 7.5, "Merchant /\nanalyst", WHITE, tc=INK, ec=NAVY, fs=7.6, bold=True)
    pbox(ax, 8, 12, 13, 7.5, "Risk-ops\nteam *", WHITE, tc=INK, ec=NAVY, fs=7.6, bold=True)
    for k, (x, y, t) in {"1": (30, 60, "1.0\nGenerate and\npreprocess"), "2": (64, 60, "2.0\nTrain three\nmodels"), "3": (30, 43, "3.0\nScore one\ntransaction"),
                         "4": (30, 26, "4.0\nScore a\nCSV batch"), "5": (30, 9, "5.0\nAnalytics and\nmodel reports"), "6": (64, 9, "6.0\nExport\npredictions")}.items():
        circle(ax, x, y, 7.4, t, BLUE, fs=6.8)
    store(ax, 46, 68.2, 20, 4.2, "D1  creditcard_synthetic.csv", fs=6.4)
    store(ax, 64, 43, 22, 4.2, "D2  pipeline_res / pipeline.pkl", fs=6.8)
    store(ax, 91, 36, 14, 8, "D3\nmodels +\nhistory", fs=6.8)
    store(ax, 91, 16, 14, 8, "D4\nbatch_predictions\n.csv", fs=6.5)
    arrow(ax, (14.5, 60), (22.6, 60), "size, method,\ntop-k", lo=(0, 3.4), fs=6.5)
    arrow(ax, (35.5, 63.6), (40, 66.1), "rows", lo=(-2.5, 1.8), fs=6.5)
    arrow(ax, (33, 53.6), (53, 45.2), "train / test\nsplit", lo=(-3, 2.6), fs=6.5)
    arrow(ax, (64, 45.2), (64, 52.6), "split", lo=(3, 0), fs=6.5)
    arrow(ax, (71, 55), (86, 40), "models,\nhistory", lo=(2, 3.6), fs=6.5)
    arrow(ax, (14.5, 38), (22.8, 42), "transaction\nfields", lo=(-1, 4.6), fs=6.5)
    arrow(ax, (22.8, 40.5), (14.5, 35), "score, risk,\nlabel", lo=(-1.5, -4.6), fs=6.5)
    arrow(ax, (14.5, 34), (22.8, 27), "CSV file", lo=(-3.5, -1), fs=6.5)
    arrow(ax, (53, 43), (37.4, 43), "scaler, columns", lo=(0, 1.8), fs=6.5)
    arrow(ax, (84, 38.5), (37.4, 44.8), "3 models", lo=(18, 3.4), fs=6.5)
    arrow(ax, (84, 34), (37.4, 26.5), "", color=GREY)
    arrow(ax, (37.4, 24.5), (84, 17), "predictions", lo=(0, -3.0), fs=6.5)
    arrow(ax, (53, 41), (36, 28.5), "", color=GREY)
    arrow(ax, (14.5, 12), (22.6, 10), "view requests", lo=(0, 3.2), fs=6.5)
    arrow(ax, (84, 32.5), (37, 11.5), "metrics, history", lo=(14, 4.2), fs=6.5)
    arrow(ax, (84, 14), (71, 10.5), "rows", lo=(0, 2.2), fs=6.5)
    arrow(ax, (57, 5.5), (14.5, 8.6), "CSV download", lo=(0, -3.0), fs=6.5, rad=-0.18)
    ax.text(50, 0.8, "* duplicate of the external entity.  5.0 also reads D1 (dataset statistics) and D2 (feature importance).", ha="center", fontsize=6.6, color=GREY, style="italic")
    save(fig, OUT / "04_dfd_level1.png")


# --------------------------------------------------------------------------------------------------
def dfd2():
    fig, ax = canvas(10, 5.4, 100, 54)
    title(ax, 50, 51, "DFD level 2 - process 3.0 'Score one transaction' (POST /api/predict_single)")
    pbox(ax, 7, 33, 11, 7, "Client\n(Verify page)", WHITE, tc=INK, ec=NAVY, fs=7.6, bold=True)
    xs = [24, 43, 62, 81]
    names = ["3.1\nValidate,\nfill defaults,\none-hot", "3.2\nAlign columns,\nscale numeric\ncolumns", "3.3\nScore with\nPCD, SAS, QS", "3.4\nAverage and\nthreshold 0.5"]
    for x, t in zip(xs, names):
        circle(ax, x, 33, 7.6, t, BLUE, fs=6.6)
    circle(ax, 81, 12, 7.6, "3.5\nRisk band\n(0.4 / 0.7)", BLUE, fs=6.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.8, 33), (b - 7.8, 33), color=NAVY)
    arrow(ax, (12.6, 33), (16, 33), "JSON", lo=(0, 2.5), fs=6.8, color=NAVY)
    arrow(ax, (81, 25.2), (81, 19.8), "p(fraud)", lo=(4.5, 0), fs=6.8, color=NAVY)
    arrow(ax, (73.2, 12), (7, 12), "prediction, label, fraud_probability, risk_level, individual_models", lo=(-4, -2.3), fs=7, color=NAVY, style="-")
    arrow(ax, (7, 12), (7, 29.4), "", color=NAVY)
    store(ax, 24, 47.2, 17, 4.2, "D1 dataset (defaults)", fs=6.6)
    store(ax, 43, 47.2, 17, 4.2, "D2 scaler + columns", fs=6.6)
    store(ax, 62, 47.2, 17, 4.2, "D3 grbmc_*.pkl", fs=6.6)
    arrow(ax, (24, 45), (24, 40.8), "means / modes", lo=(7, 0), fs=6.5, color=GREY)
    arrow(ax, (43, 45), (43, 40.8), "", color=GREY)
    arrow(ax, (62, 45), (62, 40.8), "", color=GREY)
    ax.text(43, 21.5, "the scaler is applied to all 24 numeric columns before the 18 model columns are picked\n(the bulk route picks first, so its scaler step raises and is swallowed - see the decision flowchart)", ha="center", fontsize=7, color=ORANGE, style="italic")
    save(fig, OUT / "05_dfd_level2.png")


# --------------------------------------------------------------------------------------------------
def uml_diagram():
    fig, ax = canvas(10, 9.8, 100, 98)
    title(ax, 50, 95.5, "Class and module diagram (Python backend)")
    uml_class_box(ax, 36, 92, 30, "GRBMC", ["n_visible, n_hidden, n_label", "sigma, lr, batch_size", "W, U  (weights)", "b, c, d  (biases)", "rng, persistent_v/y/h"],
                  ["_visible_to_hidden_prob(v, y)", "_hidden_to_visible_params(h)", "_hidden_to_label_prob(h)", "gibbs_step(v, y)", "pcd_step(v, y, k)", "train_epoch(X, y, sampler)",
                   "predict_proba(X)", "predict(X)", "get_qubo_matrix()"])
    uml_class_box(ax, 70, 92, 29, "samplers  <<module>>", [], ["simulated_annealing_grad(", "  model, v, y, n_sweeps, n_reads)", "quantum_sampling_grad(", "  model, v, y, n_sweeps, n_reads, gamma)"], hdr=ORANGE)
    uml_class_box(ax, 70, 74, 29, "train  <<module>>", [], ["get_lr_schedule(epoch, mode)", "train_model(X, y, Xt, yt,", "  mode, n_hidden, epochs)", "ensemble_predict(models, X)"], hdr=ORANGE)
    uml_class_box(ax, 3, 92, 30, "preprocessing  <<module>>", ["NUMERICAL_COLS (24)", "CATEGORICAL_COLS (2)"],
                  ["one_hot_encode(df)", "zscore_normalize(df, cols)", "correlation_filter(df, 0.95)", "feature_importance_filter(df, y, k)", "balancing_manual_undersampling(df)",
                   "balancing_smote(df)", "balancing_tomek(df)", "full_pipeline(df, method, top_k)"], hdr=ORANGE)
    uml_class_box(ax, 3, 56, 30, "evaluation  <<module>>", [], ["evaluate(y_true, y_pred, y_proba)", " -> accuracy, precision, recall,", "    F1, ROC-AUC, confusion matrix"], hdr=ORANGE)
    uml_class_box(ax, 36, 50, 30, "Flask app + store", ["store.df_raw", "store.pipeline_res", "store.models{classical,sa,qa}", "store.histories{...}", "MODEL_DIR, DATA_PATH"],
                  ["ensure_data(), ensure_pipeline()", "predict_single(), predict_batch()", "train(), preprocess(), comparison()", "qubo(), export_predictions()"], hdr=TEAL)
    uml_class_box(ax, 36, 20, 30, "api_extra  <<blueprint>>", [], ["dataset_stats()", "model_history()", "feature_importance()", "sample_batch()"], hdr=TEAL)
    uml_class_box(ax, 70, 52, 29, "synthetic_data  <<module>>", ["RNG (seed 42)"], ["generate_synthetic_transactions(", "  n_fraud, n_legit)", "create_balanced_39k()"], hdr=ORANGE)
    arrow(ax, (70, 83), (66, 83), "calls", lo=(0, 1.4), fs=7, color=NAVY)
    arrow(ax, (70, 66), (66, 66), "creates, trains", lo=(-1, 2.2), fs=7, color=NAVY)
    arrow(ax, (51, 50), (51, 54.6), "has 3 (0..1 each)", lo=(8.5, 0), fs=7, color=NAVY)
    arrow(ax, (30, 63.6), (36, 47), "uses", lo=(-2.5, 0), fs=7, color=NAVY)
    arrow(ax, (33, 47), (36, 43), "uses", lo=(-2.5, 1.5), fs=7, color=NAVY)
    arrow(ax, (70, 46), (66, 44), "feeds", lo=(0, 2), fs=7, color=NAVY)
    arrow(ax, (51, 20), (51, 24.2), "reads store", lo=(7, 0), fs=7, color=NAVY)
    save(fig, OUT / "06_uml_class.png")


def uml_class_box(ax, x, y, w, name, attrs, methods, hdr=NAVY):
    return uml_class(ax, x, y, w, name.split("  <<")[0] if "<<" in name else name, attrs, methods, hdr=hdr,
                     stereotype=(name.split("<<")[1].rstrip(">") if "<<" in name else None), fs=6.4)


# --------------------------------------------------------------------------------------------------
def sequence():
    fig, ax = canvas(10, 6.8, 100, 68)
    title(ax, 50, 65, "Sequence: Verify transaction (POST /api/predict_single, mode = ensemble)")
    lanes = [("Verify page\n(React)", 8), ("Vite dev\nproxy", 27), ("Flask\npredict_single", 46), ("pipeline_res\n(scaler, cols)", 65), ("GRBMC x3\n(PCD, SAS, QS)", 85)]
    for n, x in lanes:
        pbox(ax, x, 59, 16, 6, n, NAVY, fs=7.4)
        ax.plot([x, x], [56, 4], color="#9AA7B8", lw=1, ls="--", zorder=1)
    ys = iter([52, 47, 42, 37, 32, 27, 22, 17, 12, 7])

    def msg(a, b, text, ret=False):
        y = next(ys)
        xa, xb = dict((n, x) for n, x in lanes).get(a), dict((n, x) for n, x in lanes).get(b)
        if a == b:
            ax.add_patch(Rectangle((xa - 0.8, y - 2.2), 1.6, 4.4, fc="#DDE7F3", ec=NAVY, lw=1, zorder=3))
            ax.text(xa + 2.2, y, text, ha="left", va="center", fontsize=6.9, color=INK, zorder=5)
            return
        arrow(ax, (xa, y), (xb, y), text, color=GREY if ret else NAVY, ls="--" if ret else "-", fs=6.9, lo=(0, 1.7))

    names = [n for n, _ in lanes]
    msg(names[0], names[1], "Run fraud check: POST /api/predict_single {Amount, Merchant, ...}")
    msg(names[1], names[2], "forward to 127.0.0.1:8304")
    msg(names[2], names[3], "ensure_pipeline(): columns, scaler")
    msg(names[3], names[2], "pipeline_res (loaded or rebuilt)", ret=True)
    msg(names[2], names[2], "fill defaults, one-hot, align, scaler step")
    msg(names[2], names[4], "predict_proba(x) for each model")
    msg(names[4], names[2], "p(fraud) per model", ret=True)
    msg(names[2], names[2], "mean, threshold 0.5, risk band")
    msg(names[2], names[0], "JSON {prediction, fraud_probability, label, risk_level, individual_models}", ret=True)
    msg(names[0], names[0], "render risk meter and per-model bars")
    save(fig, OUT / "07_sequence_prediction.png")


# --------------------------------------------------------------------------------------------------
def use_case():
    fig, ax = canvas(10, 6.4, 100, 64)
    title(ax, 50, 61.5, "Use cases (no login in the application; the two roles are conceptual)")
    ax.add_patch(FancyBboxPatch((26, 3), 52, 55, boxstyle="round,pad=0,rounding_size=1.5", fc="#FAFBFD", ec=NAVY, lw=1.4, zorder=1))
    ax.text(52, 55.4, "SecurePay AI", ha="center", fontsize=9, color=NAVY, fontweight="bold")
    ucs = [(52, 49, "Verify one transaction"), (52, 42, "Bulk-verify a CSV file"), (52, 35, "Download predictions CSV"), (52, 28, "Download sample CSV"),
           (52, 21, "View analytics (where / when / how much)"), (52, 14, "Compare models and training curves"), (52, 7.6, "Retrain models in the Model lab")]
    for x, y, t in ucs:
        ellipse(ax, x, y, 44, 5.2, t, fs=8)
    for y, t in ((46, "Merchant /\nanalyst"), (22, "Risk-operations\nteam")):
        ax.add_patch(Circle((10, y + 4), 2.4, fc=WHITE, ec=NAVY, lw=1.4, zorder=3))
        ax.plot([10, 10], [y + 1.6, y - 3], color=NAVY, lw=1.4)
        ax.plot([6.5, 13.5], [y, y], color=NAVY, lw=1.4)
        ax.plot([10, 7], [y - 3, y - 7], color=NAVY, lw=1.4)
        ax.plot([10, 13], [y - 3, y - 7], color=NAVY, lw=1.4)
        ax.text(10, y - 10.5, t, ha="center", fontsize=8.5, color=INK, fontweight="bold")
    for y in (49, 42, 35, 28):
        arrow(ax, (13.5, 46), (29.5, y), color=GREY, lw=1.0, style="-")
    for y in (21, 14, 7.6):
        arrow(ax, (13.5, 22), (29.5, y), color=GREY, lw=1.0, style="-")
    ax.text(90, 40, "Both roles can use\nevery screen; the split\nshows who typically\nneeds which function", ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")


# --------------------------------------------------------------------------------------------------
def er_diagram():
    fig, ax = canvas(10, 6.8, 100, 68)
    title(ax, 50, 65.5, "Entity-relationship view of the persisted data - file-based, the project has no SQL database")

    def entity(x, ytop, w, name, rows, fc=NAVY, fs=6.5, lh=2.5):
        h = 4.2 + lh * len(rows) + 1.0
        ax.add_patch(Rectangle((x, ytop - h), w, h, fc=WHITE, ec=NAVY, lw=1.4, zorder=2))
        ax.add_patch(Rectangle((x, ytop - 4.2), w, 4.2, fc=fc, ec=NAVY, lw=1.4, zorder=3))
        ax.text(x + w / 2, ytop - 2.1, name, ha="center", va="center", color=WHITE, fontsize=8.4, fontweight="bold", zorder=4)
        for i, r in enumerate(rows):
            ax.text(x + 0.9, ytop - 4.2 - 1.7 - lh * i, r, ha="left", va="center", fontsize=fs, zorder=4, family="DejaVu Sans Mono")
        return h

    entity(2, 60, 28, "creditcard_synthetic.csv", ["Amount, Time", "Merchant_Category (7)", "Transaction_Type (4)", "Card_Present, Country_Match", "V1 .. V22", "Class  (0 legit, 1 fraud)", "39,000 rows x 29 cols"], BLUE)
    entity(36, 60, 28, "pipeline.pkl", ["X_train, X_test", "y_train, y_test", "scaler (StandardScaler)", "columns (18 selected)", "feature_importance{}", "dropped_corr[]", "df_processed"], TEAL)
    entity(70, 60, 28, "grbmc_{classical,sa,qa}.pkl", ["n_visible, n_hidden, n_label", "W (visible x hidden)", "U (label x hidden)", "b, c, d  (biases)", "sigma, lr, batch_size", "persistent chain state"], PURPLE)
    entity(70, 33, 28, "history_{mode}.json", ["accuracy[], precision[]", "recall[], f1[], loss[]", "paper_time", "elapsed_sec"], ORANGE)
    entity(36, 33, 28, "batch_predictions.csv", ["(uploaded CSV columns)", "Predicted_Class", "Fraud_Probability", "Risk  LOW / MEDIUM / HIGH"], GREY)
    entity(2, 33, 28, "sample_batch.csv", ["20 random rows of the dataset", "same 28 feature columns", "Class label included"], BLUE)
    arrow(ax, (30, 50), (36, 50), "preprocess\n1 : 1", lo=(0, 3.2), fs=7, color=NAVY)
    arrow(ax, (64, 50), (70, 50), "train\n1 : 3", lo=(0, 3.2), fs=7, color=NAVY)
    arrow(ax, (84, 39.6), (84, 33.4), "1 : 1", lo=(4, 0), fs=7, color=NAVY)
    arrow(ax, (50, 37.3), (50, 33.4), "predict_batch\n(+ the 3 models)", lo=(10, 0), fs=7, color=NAVY)
    arrow(ax, (16, 37.3), (16, 33.4), "extract", lo=(6, 0), fs=7, color=GREY)
    ax.text(50, 6, "Relations are produced by code, not by foreign keys: dataset -> pipeline (POST /api/preprocess), pipeline -> models and histories (POST /api/train),\n"
            "pipeline + models -> batch_predictions.csv (POST /api/predict_batch). pipeline.pkl is written by seed_models.py; the API keeps it in memory.", ha="center", fontsize=7, color=INK)
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------------------------------------------
def flow_training():
    fig, ax = canvas(8.6, 9.4, 100, 109)
    title(ax, 50, 106, "Flowchart: building the three models (preprocess + train_model)")
    ys = [97, 88, 79, 70, 61, 52]
    labs = [("Load or generate dataset (39,000 rows, 50/50)", BLUE), ("One-hot encode Merchant_Category, Transaction_Type", BLUE), ("Z-score the 24 numeric columns", BLUE),
            ("Correlation filter: drop features with |r| > 0.95", BLUE), ("Balance: manual undersampling (SMOTE / Tomek optional)", BLUE), ("Rank features with a random forest; keep top-k (18)", TEAL)]
    for y, (t, c) in zip(ys, labs):
        pbox(ax, 50, y, 62, 6.2, t, c, fs=8)
    for a, b in zip(ys[:-1], ys[1:]):
        arrow(ax, (50, a - 3.1), (50, b + 3.1), color=NAVY)
    pbox(ax, 50, 43, 62, 6.2, "Stratified 80 / 20 train-test split (random_state 42)", TEAL, fs=8)
    arrow(ax, (50, 48.9), (50, 46.1), color=NAVY)
    diamond(ax, 50, 32.5, 46, 9.5, "mode?", fs=9)
    arrow(ax, (50, 39.9), (50, 37.3), color=NAVY)
    pbox(ax, 14, 18, 27, 12, "classical\nhidden 200, batch 512\nPCD, 1 Gibbs step\nlr 0.01*exp(-0.08 e)", PURPLE, fs=7)
    pbox(ax, 50, 18, 27, 12, "sa\nhidden 65, batch 32\n3,000-row subsample\n10 sweeps x 16 reads", PURPLE, fs=7)
    pbox(ax, 86, 18, 27, 12, "qa\nhidden 65, batch 32\n10 sweeps, gamma 0.8\nlr 0.005*exp(-0.15 e)+0.0005", PURPLE, fs=6.8)
    arrow(ax, (27, 32.5), (14, 24.2), color=NAVY, rad=0.1)
    arrow(ax, (50, 27.8), (50, 24.2), color=NAVY)
    arrow(ax, (73, 32.5), (86, 24.2), color=NAVY, rad=-0.1)
    pbox(ax, 50, 5.5, 66, 6.4, "Each epoch: update W, U, b, c, d  ->  evaluate on test split\n(accuracy, precision, recall, F1, loss)  ->  after the last epoch save .pkl + .json", NAVY, fs=7.4)
    for x in (14, 50, 86):
        arrow(ax, (x, 12), (50 + (x - 50) * 0.55, 8.8), color=NAVY, lw=1.2)
    save(fig, OUT / "10_flowchart_training.png")


# --------------------------------------------------------------------------------------------------
def flow_decision():
    fig, ax = canvas(8.6, 10, 100, 116)
    title(ax, 50, 113, "Flowchart: scoring in the bulk route (predict_batch); predict_single scales before selecting columns")
    rows = [(104, "Receive JSON fields (or CSV rows)", BLUE, False), (94, "Fill missing columns: dataset mean (numeric) or mode (categorical)", BLUE, False),
            (84, "pd.get_dummies on Merchant_Category, Transaction_Type", TEAL, False), (74, "Add any expected column that is missing, value 0", TEAL, False)]
    for y, t, c, d in rows:
        pbox(ax, 50, y, 70, 6.2, t, c, fs=7.8)
    for a, b in zip([104, 94, 84], [94, 84, 74]):
        arrow(ax, (50, a - 3.1), (50, b + 3.1), color=NAVY)
    pbox(ax, 50, 63, 70, 8, "scaler.transform(numeric_after)\n(scaler fitted on 24 columns, only 13 selected are present)", WHITE, tc=ORANGE, ec=ORANGE, fs=7.6, ls="--", lw=1.8)
    arrow(ax, (50, 70.9), (50, 67), color=NAVY)
    ax.text(91.5, 66.5, "raises ValueError", ha="center", fontsize=7.2, color=ORANGE, fontweight="bold")
    arrow(ax, (85.2, 61), (85.2, 54), color=ORANGE, ls="--")
    pbox(ax, 78, 51, 36, 6.2, "except: pass  -> step skipped,\nvalues stay unscaled", WHITE, tc=ORANGE, ec=ORANGE, fs=7.2, ls="--")
    pbox(ax, 50, 41, 70, 6.2, "Select the 18 model columns in training order", TEAL, fs=7.8)
    arrow(ax, (50, 59), (50, 44.1), color=NAVY)
    arrow(ax, (60, 51), (60, 44.1), color=ORANGE, ls="--")
    pbox(ax, 50, 31, 70, 6.2, "predict_proba from the PCD, SAS and QS models", PURPLE, fs=7.8)
    arrow(ax, (50, 37.9), (50, 34.1), color=NAVY)
    pbox(ax, 50, 21, 70, 6.2, "Ensemble: mean of the three p(fraud);  label FRAUD if mean > 0.5", PURPLE, fs=7.8)
    arrow(ax, (50, 27.9), (50, 24.1), color=NAVY)
    diamond(ax, 50, 13, 44, 10, "p > 0.7 ?   p > 0.4 ?", fs=8)
    arrow(ax, (50, 17.9), (50, 18.0), color=NAVY)
    pbox(ax, 11, 6, 20, 6, "LOW\napprove", TEAL, fs=7.6)
    pbox(ax, 50, 3.0, 24, 4.4, "MEDIUM: challenge", ORANGE, fs=7)
    pbox(ax, 89, 6, 20, 6, "HIGH\ndecline, alert", "#B3372E", fs=7.4)
    arrow(ax, (28, 13), (21, 9.2), color=NAVY)
    arrow(ax, (50, 8.0), (50, 5.3), color=NAVY, lw=1.2)
    arrow(ax, (72, 13), (79, 9.2), color=NAVY)
    save(fig, OUT / "11_flowchart_decision.png")


# --------------------------------------------------------------------------------------------------
def grbmc_structure():
    fig, ax = canvas(10, 6.2, 100, 62)
    title(ax, 50, 59.5, "Gaussian-Bernoulli RBM classifier (GRBMC) and its three negative-phase samplers")
    import numpy as np
    vx, hx, yx = 10, 36, 36
    for i in range(6):
        ax.add_patch(Circle((vx, 50 - i * 5.5), 1.7, fc=BLUE, ec=NAVY, zorder=3))
    ax.text(vx, 16.5, "v: 18 visible units\n(Gaussian, z-scored)\nbias c", ha="center", fontsize=7.4, color=INK)
    for i in range(7):
        ax.add_patch(Circle((hx, 52 - i * 5.2), 1.7, fc=PURPLE, ec=NAVY, zorder=3))
    ax.text(hx, 15, "h: 200 (PCD) or 65 (SAS, QS)\nbinary hidden units, bias b", ha="center", fontsize=7.4, color=INK)
    for i in range(2):
        ax.add_patch(Circle((hx + 0, 6 - i * 0), 0.0, fc=WHITE))
    ax.add_patch(Circle((62, 41), 1.7, fc=ORANGE, ec=NAVY, zorder=3))
    ax.add_patch(Circle((62, 33), 1.7, fc=ORANGE, ec=NAVY, zorder=3))
    ax.text(62, 25, "y: 2 label units\n(one-hot, bias d)", ha="center", fontsize=7.4, color=INK)
    for i in range(6):
        for j in range(7):
            ax.plot([vx + 1.7, hx - 1.7], [50 - i * 5.5, 52 - j * 5.2], color="#B7C3D3", lw=0.5, zorder=1)
    for yy in (41, 33):
        for j in range(7):
            ax.plot([hx + 1.7, 62 - 1.7], [52 - j * 5.2, yy], color="#D9C9B5", lw=0.5, zorder=1)
    ax.text(23, 54.5, "W (18 x h)", ha="center", fontsize=8, color=NAVY, fontweight="bold")
    ax.text(49, 54.5, "U (2 x h)", ha="center", fontsize=8, color=NAVY, fontweight="bold")
    ax.text(36, 8.5, "p(h=1 | v, y) = sigmoid( b + vW/sigma + yU )     p(y | v) from free energy, softmax over y = 0, 1", ha="center", fontsize=7, color=INK)
    ax.text(36, 4.5, "update:  dW = ( <v h>data - <v h>model ) / (batch x sigma),   dU, db, dc, dd likewise;  W += lr * dW", ha="center", fontsize=7, color=INK)
    panel(ax, 71, 4, 28, 52, "Negative phase <.>model", LIGHT)
    pbox(ax, 85, 42, 25, 13, "Classical PCD\npersistent chain, k = 1\nGibbs step: h | v,y then\nv ~ N(c + sigma W h), y ~ softmax", BLUE, fs=6.6)
    pbox(ax, 85, 26, 25, 13, "SA sampling\nreads = 16, sweeps = 10\nbeta 0.5 -> 10 (temp 2.0 -> 0.1)\nsample h, y; expectations\nfrom the reads", PURPLE, fs=6.6)
    pbox(ax, 85, 10.5, 25, 13, "Quantum-inspired (QS)\ns in [0, 1], A = 0.8(1-s), B = s\ntunnelling flips with 0.3 A\nclassical simulation only", ORANGE, fs=6.6)
    save(fig, OUT / "12_grbmc_structure.png")


def main():
    for fn in (system_architecture, high_level_workflow, dfd0, dfd1, dfd2, uml_diagram, sequence, use_case, er_diagram, flow_training, flow_decision, grbmc_structure):
        fn()


if __name__ == "__main__":
    main()
