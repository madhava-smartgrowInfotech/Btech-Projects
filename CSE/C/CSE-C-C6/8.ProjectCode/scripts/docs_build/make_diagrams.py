"""Draw every design diagram for the TruthGlow / PCA + Firefly + MSVM documents into docs/diagrams/ (PNG, 150 dpi).

Every box and arrow mirrors the code: backend/main.py (routes), src/pipeline.py, src/firefly.py, src/preprocessing.py,
src/dataset.py and frontend/src/pages. matplotlib only.
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
    fig, ax = canvas(10, 7.6, 100, 76)
    panel(ax, 2, 56, 96, 18, "Presentation tier - browser (React 18 + TypeScript + Vite + Tailwind, port 5406)", PALE_BLUE, BLUE, tc=NAVY)
    box(ax, 17, 62.5, 28, 9.5, "Six screens (react-router)\nLanding - Detect - Batch check\nAnalytics - Retrain - About", BLUE, fs=8.2)
    box(ax, 48, 62.5, 28, 9.5, "Data layer\naxios client on /api\nTanStack Query hooks", BLUE, fs=8.2)
    box(ax, 79, 62.5, 28, 9.5, "UI kit (Aurora Glass)\nRecharts charts - GSAP\nlight / dark theme", BLUE, fs=8.2)

    panel(ax, 2, 31, 96, 22, "Application tier - FastAPI (backend/main.py, port 8406, all routes under /api)", PALE_TEAL, TEAL, tc=NAVY)
    box(ax, 15, 44, 25, 10.5, "Model and info\nGET /health\nGET /model\nGET /samples", TEAL, fs=7.8)
    box(ax, 41, 44, 25, 10.5, "Detection\nPOST /predict\nPOST /batch/preview\nPOST /batch/run", TEAL, fs=7.8)
    box(ax, 67, 44, 25, 10.5, "Retraining\nPOST /retrain  (202)\nGET /retrain/{job_id}", TEAL, fs=7.8)
    box(ax, 90, 44, 14, 10.5, "Validation\n422 / 400\n409 / 413", TEAL, fs=7.8)
    box(ax, 28, 34.3, 50, 4.0, "get_pipe(): one pipeline held in memory behind an RLock", WHITE, tc=INK, ec=TEAL, fs=7.8)
    box(ax, 76, 34.3, 38, 4.0, "Retrain job: daemon thread + _jobs dict", WHITE, tc=INK, ec=TEAL, fs=7.8)

    panel(ax, 2, 11, 96, 17, "Domain tier - src/ (the pure-Python library, shared with the CLI and the Streamlit app)", PALE_ORANGE, ORANGE, tc=NAVY)
    mods = [("preprocessing", "clean_text\n25 stylometric"), ("dataset", "load_csv\ndemo corpus"), ("firefly", "FireflyOptimizer\nmask + C + gamma"),
            ("pipeline", "FakeNewsMSVM\nPipeline"), ("scikit-learn", "TF-IDF, scaler\nPCA, SVC")]
    for i, (n, d) in enumerate(mods):
        box(ax, 11 + i * 19.5, 18.5, 17.6, 9.5, f"{n}\n{d}", ORANGE, fs=7.6)

    store(ax, 28, 4.4, 50, 5.4, "models/msvm_model.pkl (joblib bundle) - metrics.json", PALE_TEAL, TEAL, fs=7.8)
    store(ax, 76, 4.4, 38, 5.4, "labelled CSV uploads (temp file, then deleted)", PALE_TEAL, TEAL, fs=7.4)

    arrow(ax, (45, 56), (45, 53), "HTTP + JSON + multipart CSV (Vite proxies /api)", lo=(25, 0), fs=7.8, color=NAVY)
    arrow(ax, (45, 31), (45, 28), "Python calls", lo=(9, 0), fs=7.8, color=NAVY)
    arrow(ax, (28, 11), (28, 7.1), None, color=NAVY)
    arrow(ax, (76, 11), (76, 7.1), None, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(50, 63.5, "A. Training path (offline, or the Retrain screen)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    steps = [("Labelled\ntext + label", BLUE), ("Clean text\nTF-IDF 1-2 grams\n+ 25 stylometric", TEAL), ("StandardScaler\nthen PCA\n(95%, <= 300)", TEAL),
             ("80/20 stratified\nsplit", TEAL), ("Firefly search\nmask + C + gamma\n(3-fold CV F1)", ORANGE), ("RBF MSVM\none-vs-rest\nbalanced weights", PURPLE), ("Evaluate,\nsave .pkl +\nmetrics.json", NAVY)]
    xs = [7.5 + i * 14.2 for i in range(7)]
    for x, (t, c) in zip(xs, steps):
        box(ax, x, 51, 12.6, 14, t, c, fs=7.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 6.4, 51), (b - 6.4, 51), None, color=NAVY)

    ax.text(50, 36.5, "B. Inference path (every request: Detect screen, Batch check)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    steps2 = [("News text\n(headline + body)", BLUE), ("Clean + TF-IDF\n+ 25 stylometric\n(fitted vocabulary)", TEAL), ("Scaler, then\nPCA transform", TEAL), ("Keep the\nFirefly-selected\ncomponents", ORANGE),
              ("MSVM\npredict_proba", PURPLE), ("Verdict + confidence\n+ cue words", NAVY)]
    xs2 = [8.5 + i * 16.6 for i in range(6)]
    for x, (t, c) in zip(xs2, steps2):
        box(ax, x, 22, 14.6, 14, t, c, fs=7.8)
    for a, b in zip(xs2[:-1], xs2[1:]):
        arrow(ax, (a + 7.5, 22), (b - 7.5, 22), None, color=NAVY)
    box(ax, 50, 5.2, 90, 6.2, "The same fitted objects (vectorizer, scaler, PCA, mask, C, gamma, classifier) are saved once in models/msvm_model.pkl and reused by the API, the CLI and Streamlit", WHITE, tc=INK, ec=NAVY, fs=7.8)
    arrow(ax, (xs[-1], 44), (xs2[3], 29.2), "saved bundle", color=ORANGE, ls="--", rad=-0.1, lo=(12, 1.6), fs=7.8)
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(10, 5.4, 100, 54)
    circle(ax, 50, 27, 14.5, "0\nFake news\ndetection\nsystem", BLUE, fs=10)
    box(ax, 11, 27, 18, 34, "Reader /\nanalyst", NAVY, fs=10, bold=True)
    box(ax, 89, 34, 18, 22, "Model owner\n(trainer)", NAVY, fs=10, bold=True)
    box(ax, 89, 9, 18, 12, "Labelled\ncorpus (CSV)", GREY, fs=9, bold=True)
    import math

    def edge(y, side):
        dx = math.sqrt(max(14.5 ** 2 - (y - 27) ** 2, 0))
        return 50 - dx if side == "L" else 50 + dx

    def hflow(y, x1, x2, text, color, fwd=True):
        a, b = (x1, x2) if fwd else (x2, x1)
        arrow(ax, (a, y), (b, y), text, color=color, lo=(0, 1.9), fs=7.6)
    hflow(38, 20, edge(38, "L"), "article text (title + body)", BLUE)
    hflow(32, 20, edge(32, "L"), "CSV of articles", BLUE)
    hflow(22, 20, edge(22, "L"), "verdict, confidence,\nprobabilities, cues", TEAL, fwd=False)
    hflow(16, 20, edge(16, "L"), "results CSV + distribution", TEAL, fwd=False)
    hflow(37, edge(37, "R"), 80, "retrain request", BLUE, fwd=False)
    hflow(31, edge(31, "R"), 80, "accuracy, macro-F1,\nmodel statistics", TEAL)
    arrow(ax, (80, 11), (61.2, 19.4), "labelled rows (CSV)", color=BLUE, lo=(3.5, -2.2), fs=7.6)
    save(fig, OUT / "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(10, 7.0, 100, 70)
    box(ax, 9, 50, 15, 9, "Reader /\nanalyst", NAVY, fs=8.8, bold=True)
    box(ax, 9, 14, 15, 9, "Model\nowner", NAVY, fs=8.8, bold=True)
    circle(ax, 46, 62, 7.6, "1.0\nDetect\nsingle article", BLUE, fs=7.8)
    circle(ax, 46, 44, 7.6, "2.0\nBatch detect\nCSV", BLUE, fs=7.8)
    circle(ax, 46, 27, 7.6, "4.0\nReport model\nstatistics", BLUE, fs=7.8)
    circle(ax, 46, 9.5, 7.6, "3.0\nTrain / retrain\nmodel", BLUE, fs=7.8)
    store(ax, 90, 38, 17, 8, "D1  model\nbundle (.pkl)", PALE_TEAL, TEAL, fs=7.8)
    store(ax, 90, 9.5, 17, 8, "D2  labelled\nCSV (temp file)", PALE_TEAL, TEAL, fs=7.6)
    arrow(ax, (16.5, 53), (39.3, 61), "article text", color=BLUE, lo=(-3, 3.2), fs=7.6)
    arrow(ax, (39.5, 58), (16.5, 49.5), "verdict, confidence,\nprobabilities, cues", color=TEAL, lo=(-2, -3.4), fs=7.4)
    arrow(ax, (16.5, 47), (39.3, 44.5), "CSV of articles", color=BLUE, lo=(-1, 2.4), fs=7.6)
    arrow(ax, (39.4, 41.2), (16.5, 45.2), "results CSV,\ndistribution", color=TEAL, lo=(3, -3.4), fs=7.4)
    arrow(ax, (39.5, 29.5), (16.5, 46.3), "statistics", color=TEAL, lo=(-1.5, -4.2), fs=7.4)
    arrow(ax, (16.5, 17.5), (39.5, 25.0), None, color=TEAL)
    ax.text(25.5, 24, "statistics", fontsize=7.4, color=INK, ha="center")
    arrow(ax, (16.5, 15.5), (38.5, 11.5), "retrain request", color=BLUE, lo=(-1, 2.4), fs=7.6)
    arrow(ax, (38.5, 7.2), (16.5, 11.2), "accuracy, macro-F1", color=TEAL, lo=(1, -2.6), fs=7.6)
    arrow(ax, (81.5, 40.5), (52.5, 60.0), "fitted vectorizer, scaler,\nPCA, mask, C, gamma, SVC", color=GREY, ls="--", lo=(8.5, 4.0), fs=7.2)
    arrow(ax, (81.5, 38.5), (53.0, 45.5), None, color=GREY, ls="--")
    arrow(ax, (81.5, 36.5), (53.0, 28.5), "stats_ (read)", color=GREY, ls="--", lo=(3.0, -2.6), fs=7.4)
    arrow(ax, (53.0, 13.0), (83.0, 34.0), "new bundle (save)", color=ORANGE, ls="--", lo=(7.5, -1.5), fs=7.4)
    arrow(ax, (81.5, 9.5), (53.6, 9.5), "labelled rows", color=GREY, ls="--", lo=(0, 2.0), fs=7.6)
    ax.text(47, 0.6, "Process 3.0 is decomposed in the level-2 diagram. Reader / analyst and Model owner use the same screens; they are drawn apart only to show who typically starts each flow.", fontsize=6.6, color=GREY, ha="center", va="bottom")
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 7.6, 100, 76)
    ax.text(50, 73.5, "DFD level 2 - process 3.0 'Train / retrain model' decomposed", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    box(ax, 8, 56, 13, 7, "Model owner", NAVY, fs=8.4, bold=True)
    store(ax, 8, 68, 15, 6.5, "D2  labelled\nCSV (temp)", PALE_TEAL, TEAL, fs=7.4)
    pos = {"3.1": (30, 58), "3.2": (54, 58), "3.3": (78, 58), "3.4": (78, 36), "3.5": (54, 36), "3.6": (30, 36), "3.7": (30, 13)}
    labels = {"3.1": "3.1\nValidate request\n+ load labels", "3.2": "3.2\nClean text, TF-IDF\n+ stylometric", "3.3": "3.3\nStandardise\n+ PCA", "3.4": "3.4\nStratified\n80/20 split",
              "3.5": "3.5\nFirefly search\n(mask, C, gamma)", "3.6": "3.6\nFit final MSVM\n+ evaluate", "3.7": "3.7\nSave bundle,\nswap in memory"}
    for k, (x, y) in pos.items():
        circle(ax, x, y, 8.2, labels[k], BLUE, fs=7.1)
    store(ax, 70, 13, 17, 7, "D1  model\nbundle (.pkl)", PALE_TEAL, TEAL, fs=7.6)
    arrow(ax, (14.5, 57), (21.8, 57.6), "request", fs=7.4, lo=(0, 2.0), color=NAVY)
    arrow(ax, (15.5, 66), (23.5, 62.5), "rows", fs=7.4, lo=(-1.5, 2.4), color=NAVY, ls="--")
    arrow(ax, (38.2, 58), (45.8, 58), "texts, y", fs=7.4, lo=(0, 2.0), color=NAVY)
    arrow(ax, (62.2, 58), (69.8, 58), "X (4025 cols)", fs=7.4, lo=(0, 2.0), color=NAVY)
    arrow(ax, (78, 49.8), (78, 44.2), "X_pca", fs=7.4, lo=(3.2, 0), color=NAVY)
    arrow(ax, (69.8, 36), (62.2, 36), "X_train, y", fs=7.4, lo=(0, 2.0), color=NAVY)
    arrow(ax, (45.8, 36), (38.2, 36), "mask, C, gamma", fs=7.4, lo=(0, 2.0), color=NAVY)
    arrow(ax, (73, 29), (35, 29), "X_train, X_test, y_test", fs=7.4, lo=(0, -2.6), color=NAVY, ls="--", rad=0.18)
    arrow(ax, (30, 27.8), (30, 21.4), "fitted pipeline,\nstats_", fs=7.4, lo=(8.0, 0), color=NAVY)
    arrow(ax, (38.2, 13), (61.5, 13), "pickle (atomic replace)", fs=7.4, lo=(0, 2.0), color=ORANGE, ls="--")
    arrow(ax, (21.8, 11.5), (8, 52.2), "accuracy, macro-F1\n(job status)", color=TEAL, ls="--", rad=-0.12, fs=7.4, lo=(-3.5, -14))
    save(fig, OUT / "05_dfd_level2.png")


def class_diagram():
    fig, ax = canvas(10, 7.7, 100, 90)
    ax.set_ylim(12, 89)
    api = uml_class(ax, 2, 86, 28, "backend.main (FastAPI)", ["_pipe: pipeline", "_lock: RLock", "_jobs: dict", "MAX_UPLOAD_BYTES = 25 MB", "MAX_BATCH_ROWS = 20000"],
                    ["get_pipe()", "predict(PredictBody)", "batch_preview(file)", "batch_run(file, column)", "retrain(file, ...)", "retrain_status(job_id)"], hdr=TEAL, fs=6.4)
    p = uml_class(ax, 36, 86, 31, "FakeNewsMSVMPipeline",
                  ["max_tfidf, pca_variance=0.95", "pca_max=300", "n_fireflies, n_generations", "test_size=0.2, random_state", "vectorizer: TfidfVectorizer", "scaler: StandardScaler", "pca: PCA", "optimizer: FireflyOptimizer", "clf: SVC", "stats_: dict"],
                  ["fit(raw_texts, y)", "transform(raw_texts)", "predict(raw_texts)", "save(path)", "load(path)  <<static>>"], fs=6.4)
    f = uml_class(ax, 73, 86, 25, "FireflyOptimizer",
                  ["n_fireflies, n_generations", "alpha, beta0, gamma", "penalty=0.02, cv=3", "history_: list", "best_mask_: bool[]", "best_C_, best_gamma_val_", "best_score_: float"],
                  ["_decode(vec, n_features)", "_fitness(vec, X, y)", "optimize(X, y)"], fs=6.1)
    ds = uml_class(ax, 2, 44, 28, "dataset", [], ["load_csv(path_or_dir)", "build_demo_dataset(n)", "_canon_label(value)"], hdr=GREY, fs=6.4, stereotype="module")
    sk = uml_class(ax, 36, 44, 31, "scikit-learn parts", ["TfidfVectorizer(1-2 grams)", "StandardScaler", "PCA(n_components)", "SVC(rbf, ovr, balanced)"], [], hdr=PURPLE, fs=6.4, stereotype="library")
    pre = uml_class(ax, 73, 44, 25, "preprocessing", ["LABELS, STOPWORDS"], ["clean_text(text)", "stylometric_features(texts)"], hdr=GREY, fs=6.1, stereotype="module")
    arrow(ax, (30, 78), (36, 78), None, color=NAVY, lw=1.3)
    ax.text(33, 79.4, "calls", fontsize=7, ha="center")
    arrow(ax, (67, 78), (73, 78), None, color=NAVY, lw=1.3)
    ax.text(70, 79.4, "owns 1", fontsize=7, ha="center")
    arrow(ax, (16, 60.5), (16, 44), None, color=NAVY, lw=1.1, ls="--")
    ax.text(17.5, 52, "uses", fontsize=7, ha="left")
    arrow(ax, (51, 50.0), (51, 44), None, color=NAVY, lw=1.2)
    ax.text(52.5, 47.2, "composes", fontsize=7, ha="left")
    arrow(ax, (67, 53), (73, 44), None, color=NAVY, lw=1.1, ls="--")
    ax.text(70.8, 51.4, "uses", fontsize=7, ha="left")
    ax.text(2, 21.5, "get_pipe() loads (or trains on the demo corpus) exactly one FakeNewsMSVMPipeline; predict, batch_run and retrain all call predict() / fit() on it.\n"
                   "Two fitted objects make up the model: the three-stage feature transformer (vectorizer, scaler, PCA) and the masked SVC.\n"
                   "FireflyOptimizer is used only while fitting; at prediction time only its best mask is kept.", fontsize=7.4, color=GREY, ha="left", va="top")
    save(fig, OUT / "06_uml_class_diagram.png")


def sequence_diagram():
    fig, ax = canvas(10, 8.4, 100, 84)
    names = ["User", "React UI\n(Detect)", "FastAPI\n/api", "Pipeline\n.predict", "Preproc.\n+ TF-IDF", "Scaler +\nPCA", "MSVM\n(SVC)"]
    xs = [6, 20, 36, 52, 66, 80, 93]
    top = 81
    for x, n in zip(xs, names):
        box(ax, x, top, 11.8, 6.2, n, NAVY, fs=8.0, bold=True)
        ax.plot([x, x], [top - 3.1, 1], color="#9AA7B8", lw=1.1, ls="--", zorder=1)
    y = [top - 8.5]

    def msg(i, j, text, ret=False, gap=5.2):
        arrow(ax, (xs[i], y[0]), (xs[j], y[0]), None, color=(GREY if ret else BLUE), ls="--" if ret else "-", lw=1.4)
        lo, hi = sorted((xs[i], xs[j]))
        ax.text((lo + hi) / 2, y[0] + 1.1, text, ha="center", fontsize=7.6, va="bottom", color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
        y[0] -= gap

    def self_call(i, text):
        yy = y[0]
        ax.plot([xs[i], xs[i] + 3.2, xs[i] + 3.2, xs[i]], [yy + 0.9, yy + 0.9, yy - 2.1, yy - 2.1], color=BLUE, lw=1.3, zorder=4)
        arrow(ax, (xs[i] + 3.2, yy - 2.1), (xs[i], yy - 2.1), None, color=BLUE, lw=1.3)
        ax.text(xs[i] + 4.2, yy - 0.6, text, fontsize=7.4, ha="left", va="center", color=INK)
        y[0] -= 6.2

    msg(0, 1, "1  Type or pick an example, press Detect")
    msg(1, 2, "2  POST /api/predict {title, text}")
    self_call(2, "3  join title + text, require >= 5 words (else 422)")
    msg(2, 3, "4  get_pipe().predict([text])")
    msg(3, 4, "5  clean_text; stylometric_features; TF-IDF transform")
    msg(4, 3, "6  X_full (4025 columns, scaled later)", ret=True)
    msg(3, 5, "7  scaler.transform; pca.transform")
    msg(5, 3, "8  X_pca (up to 300 columns)", ret=True)
    msg(3, 6, "9  X_pca[:, mask]; predict, predict_proba")
    msg(6, 3, "10  class id, 3 probabilities", ret=True)
    msg(3, 2, "11  (ids, proba)", ret=True)
    self_call(2, "12  label, confidence, latency_ms, cue words")
    msg(2, 1, "13  JSON verdict", ret=True)
    msg(1, 0, "14  verdict badge, class-probability chart, cues", ret=True, gap=4.5)
    ax.add_patch(Rectangle((11, 2.0), 87, 0.0001, fc="none", ec="none"))
    save(fig, OUT / "07_sequence_diagram.png")


def use_case():
    fig, ax = canvas(10, 6.9, 100, 69)
    ax.add_patch(Rectangle((28, 5.0), 44, 61.0, fc="#FAFBFD", ec=NAVY, lw=1.6, zorder=0))
    ax.text(50, 64.0, "TruthGlow web application", ha="center", fontsize=11, color=NAVY, fontweight="bold")
    ax.text(50, 1.5, "The application has no login: every user can open every screen. The actors show who typically starts which use case.", ha="center", fontsize=7.4, color=GREY, va="center")
    names = ["UC1  Check one article", "UC2  See cue words\nand class probabilities", "UC3  Check a CSV of articles\n(batch)", "UC4  Download results CSV", "UC5  View model analytics", "UC6  Retrain the model\n(demo corpus or own CSV)", "UC7  Read how it works"]
    ys = [58, 49.5, 41, 33, 25, 16.5, 9]
    for t, yy in zip(names, ys):
        ellipse(ax, 50, yy, 38, 7, t, fs=8)

    def actor(x, y, name):
        ax.add_patch(Circle((x, y + 6.5), 1.6, fc="white", ec=NAVY, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 4.9, y + 1.0], color=NAVY, lw=1.6)
        ax.plot([x - 3, x + 3], [y + 3.8, y + 3.8], color=NAVY, lw=1.6)
        ax.plot([x, x - 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.plot([x, x + 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.text(x, y - 5.0, name, ha="center", fontsize=9.5, fontweight="bold", color=INK)
    actor(11, 40, "Reader /\nanalyst")
    actor(89, 14, "Model\nowner")
    for yy in ys[:5] + [ys[6]]:
        arrow(ax, (15, 43), (31, yy), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (85, 16), (69, ys[5]), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (85, 15), (69, ys[4]), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (69, 55.0), (69, 53.0), None, color=GREY, lw=1.0, ls="--")
    ax.text(70.5, 54.0, "<<include>>", fontsize=7.2, color=GREY, style="italic", ha="left", va="center")
    arrow(ax, (69, 38.0), (69, 36.0), None, color=GREY, lw=1.0, ls="--")
    ax.text(70.5, 37.0, "<<extend>>", fontsize=7.2, color=GREY, style="italic", ha="left", va="center")
    save(fig, OUT / "08_use_case_diagram.png")


def er_diagram():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(1, 63.5, "Data model (file based; no SQL database)", ha="left", fontsize=9.5, color=NAVY, fontweight="bold")

    def entity(cx, cy, w, title, fields, color=NAVY):
        h = 5.2 + 2.9 * len(fields)
        ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc=WHITE, ec=color, lw=1.4, zorder=2))
        ax.add_patch(Rectangle((cx - w / 2, cy + h / 2 - 4.6), w, 4.6, fc=color, ec=color, zorder=3))
        ax.text(cx, cy + h / 2 - 2.3, title, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold", zorder=4)
        for i, f_ in enumerate(fields):
            ax.text(cx - w / 2 + 1.0, cy + h / 2 - 7.0 - i * 2.9, f_, ha="left", va="center", fontsize=7.0, color=INK, zorder=4, family="DejaVu Sans Mono")
        return h

    entity(17, 48, 28, "TrainingCSV (upload)", ["text / title+text / statement", "label (REAL|PARTIALLY TRUE|FAKE", "      or 0|1|2, LIAR/ISOT names)"], GREY)
    entity(50, 50, 30, "RetrainJob (in memory)", ["PK job_id", "status running|done|error", "started, finished, source", "settings{fireflies,", "  generations, max_tfidf}", "result{accuracy, f1_macro...}", "error"], TEAL)
    entity(83, 46, 28, "ModelBundle (.pkl)", ["vectorizer, scaler, pca", "optimizer_mask, best_C,", "best_gamma, clf", "params{max_tfidf}", "stats (ModelStats)"], ORANGE)
    entity(83, 15, 28, "ModelStats (inside bundle)", ["n_docs, n_tfidf, n_pca", "pca_variance, n_selected", "firefly_history[]", "accuracy, f1_macro, report", "confusion_matrix[3][3]", "baseline_accuracy/f1", "train_time_s"], PURPLE)
    entity(17, 15, 28, "Prediction (transient)", ["label, label_id", "confidence, probabilities{3}", "latency_ms, word_count", "cues{sensational[],", "  credibility[]}"], BLUE)
    entity(50, 14, 30, "BatchResult (transient)", ["filename, column, n_rows", "rows[{row,text,predicted,", "  confidence}]", "distribution{3}", "csv (download)"], BLUE)
    arrow(ax, (31, 48), (35, 49), "1 : 0..1", fs=7.2, lo=(0, 2.2), color=NAVY, style="-")
    ax.text(33, 44.0, "feeds", fontsize=7.2, ha="center", color=GREY)
    arrow(ax, (65, 49), (69, 49), "1 : 1", fs=7.2, lo=(0, 2.2), color=NAVY, style="-")
    ax.text(67, 44.8, "replaces", fontsize=7.2, ha="center", color=GREY)
    arrow(ax, (83, 36.2), (83, 28.0), "1 : 1", fs=7.2, lo=(3.2, 0), color=NAVY, style="-")
    arrow(ax, (69, 36.5), (31, 26.5), None, color=GREY, lw=1.1, ls="--")
    arrow(ax, (69, 36.0), (56, 27.0), None, color=GREY, lw=1.1, ls="--")
    ax.text(50, 34.2, "produces  (1 bundle : many)", fontsize=7.2, color=GREY, ha="center")
    save(fig, OUT / "09_er_diagram.png")


def flowchart():
    fig, ax = canvas(10, 10.6, 100, 106)
    L, Rr = 22, 74

    def step(cx, cy, t, c=NAVY, w=34, h=7, fs=8.0):
        box(ax, cx, cy, w, h, t, c, fs=fs)

    ax.text(L, 104, "A. Firefly search (src/firefly.py)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ax.text(Rr, 104, "B. Final model and inference", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    box(ax, L, 98.5, 26, 5, "Start: X_train (PCA), y_train", GREY, fs=8.2, bold=True, r=2.4)
    step(L, 89.5, "Population of 10 fireflies\nvector = 300 mask logits + log10 C + log10 gamma", BLUE, w=38, h=8)
    step(L, 79, "Brightness = 3-fold CV macro-F1\n- 0.02 x (selected / total)", TEAL, w=38, h=8)
    diamond(ax, L, 66, 32, 11, "generation <\n12 ?", fs=8.2)
    step(L, 52, "For each firefly i, for each brighter j:\nbeta = exp(-gamma r^2 / d)\nx_i += beta (x_j - x_i) + alpha_t * noise", PURPLE, w=40, h=10, fs=7.6)
    step(L, 40, "Clip log10 C to [-1, 3], log10 gamma to [-4, 1];\nre-evaluate brightness of i", TEAL, w=40, h=8, fs=7.6)
    step(L, 29, "Keep global best vector;\nreplace the dimmest firefly by best + noise", TEAL, w=38, h=8, fs=7.8)
    step(L, 18.5, "Record best brightness in history;\nalpha_t = 0.2 x 0.97^generation", NAVY, w=38, h=8, fs=7.8)
    step(L, 7, "Decode best vector:\nmask = sigmoid > 0.5, C, gamma", ORANGE, w=36, h=8, fs=8)
    for a_, b_ in [(96, 93.5), (85.5, 83.2), (75.2, 71.5), (60.5, 57.2), (47, 44.2), (36, 33.2), (25, 22.6), (14.4, 11.2)]:
        arrow(ax, (L, a_), (L, b_), None, color=NAVY)
    ax.plot([L + 19, L + 26, L + 26], [18.5, 18.5, 66], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (L + 26, 66), (L + 16, 66), None, color=NAVY)
    ax.text(L + 27, 42, "next generation", fontsize=7.4, color=GREY, rotation=90, va="center", ha="left")
    ax.text(L + 5.5, 62.5, "yes", fontsize=7.8, color=ORANGE)
    ax.plot([L - 16, L - 21, L - 21], [66, 66, 7], color=NAVY, lw=1.5, zorder=4)
    ax.text(L - 20, 36, "no: stop", fontsize=7.4, color=ORANGE, rotation=90, va="center", ha="right")
    arrow(ax, (L - 21, 7), (L - 18, 7), None, color=NAVY)
    # right column
    ax.plot([L + 18, 51, 51], [7, 7, 98.5], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (51, 98.5), (Rr - 13, 98.5), None, color=NAVY)
    box(ax, Rr, 98.5, 26, 5, "best mask, C, gamma", GREY, fs=8.2, bold=True, r=2.4)
    step(Rr, 88, "Final SVC: RBF kernel, C, gamma,\nclass_weight=balanced, one-vs-rest,\nprobability=True; fit on masked X_train", PURPLE, w=40, h=10, fs=7.8)
    step(Rr, 74, "Score the 20% test split:\naccuracy, macro-F1, confusion matrix", TEAL, w=36, h=8)
    step(Rr, 62, "Baseline: default RBF SVC on all PCA\ncomponents (no Firefly), same split", TEAL, w=38, h=8, fs=7.8)
    step(Rr, 50, "Save bundle: vectorizer, scaler, PCA, mask,\nC, gamma, classifier, stats", ORANGE, w=40, h=8, fs=7.8)
    ax.plot([Rr - 22, Rr - 22], [43, 43], color=NAVY)
    step(Rr, 37, "New text: clean + TF-IDF + stylometric\n-> scaler -> PCA -> keep mask columns", BLUE, w=40, h=8, fs=7.8)
    step(Rr, 25, "predict_proba over REAL / PARTIALLY TRUE / FAKE", PURPLE, w=40, h=6.5, fs=7.8)
    box(ax, Rr, 14, 36, 6.5, "Verdict = argmax, confidence = max", GREY, fs=8, bold=True, r=2.4)
    for a_, b_ in [(96, 93.2), (83, 78.2), (70, 66.2), (58, 54.2), (46, 41.2), (33, 28.4), (21.7, 17.4)]:
        arrow(ax, (Rr, a_), (Rr, b_), None, color=NAVY)
    save(fig, OUT / "10_core_algorithm_flowchart.png")


def feature_pipeline():
    fig, ax = canvas(11, 3.9, 110, 39)
    blocks = [("Raw text", "1 article", "title + body", GREY, 10), ("Clean text", "tokens", "lower-case, drop URLs,\n@/#, stop words, len<=2", BLUE, 13),
              ("TF-IDF", "<= 4000 cols", "1-2 grams, sublinear tf,\nmin_df 2, max_df 0.9", BLUE, 12),
              ("+ 25 stylometric", "4025 cols", "caps, !, ?, digits, URLs,\nlexicon ratios ...", TEAL, 14), ("Standardise", "4025", "zero mean, unit variance", TEAL, 11),
              ("PCA", "<= 300 comps", "95% variance target,\ncapped at 300", ORANGE, 11), ("Firefly mask", "k of n comps", "binary selection", ORANGE, 11), ("RBF MSVM", "3 classes", "C, gamma from Firefly", PURPLE, 11)]
    x = 1.0
    centers = []
    for t, shape, note, c, w in blocks:
        box(ax, x + w / 2, 19, w, 12, t, c, fs=7.8)
        ax.text(x + w / 2, 19 + 6 + 2.4, shape, ha="center", fontsize=7.8, color=INK, fontweight="bold")
        ax.text(x + w / 2, 19 - 6 - 4.6, note, ha="center", fontsize=6.6, color=INK, va="center", linespacing=1.2)
        centers.append((x, w))
        x += w + 1.8
    for (a, wa), (b, wb) in zip(centers[:-1], centers[1:]):
        arrow(ax, (a + wa, 19), (b, 19), None, color=NAVY, lw=1.2)
    ax.text(55, 36.6, "Feature pipeline: how one article becomes a class decision (shapes after each stage)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    save(fig, OUT / "11_feature_pipeline.png")


def retrain_sequence():
    fig, ax = canvas(10, 7.4, 100, 74)
    names = ["User", "React UI\n(Retrain)", "FastAPI\n/api", "Worker\nthread", "Pipeline\n.fit", "models/\n.pkl"]
    xs = [7, 23, 42, 60, 77, 92]
    top = 71
    for x, n in zip(xs, names):
        box(ax, x, top, 12.5, 6.2, n, NAVY, fs=8.0, bold=True)
        ax.plot([x, x], [top - 3.1, 1], color="#9AA7B8", lw=1.1, ls="--", zorder=1)
    y = [top - 8.5]

    def msg(i, j, text, ret=False, gap=5.0):
        arrow(ax, (xs[i], y[0]), (xs[j], y[0]), None, color=(GREY if ret else BLUE), ls="--" if ret else "-", lw=1.4)
        lo, hi = sorted((xs[i], xs[j]))
        ax.text((lo + hi) / 2, y[0] + 1.1, text, ha="center", fontsize=7.4, va="bottom", color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
        y[0] -= gap

    msg(0, 1, "1  Attach CSV, set sliders, confirm")
    msg(1, 2, "2  POST /api/retrain (multipart)")
    msg(2, 2, "") if False else None
    msg(2, 3, "3  validate, load_csv, start thread")
    msg(2, 1, "4  202 {job_id}", ret=True)
    msg(3, 4, "5  FakeNewsMSVMPipeline(...).fit(texts, y)")
    msg(1, 2, "6  GET /api/retrain/{job_id}  (polled)")
    msg(2, 1, "7  {status: running, elapsed_s}", ret=True)
    msg(4, 3, "8  fitted pipeline + stats_", ret=True)
    msg(3, 5, "9  save to .tmp, os.replace()")
    msg(3, 2, "10  swap _pipe under the lock; status = done", ret=True)
    msg(1, 2, "11  GET /api/retrain/{job_id}")
    msg(2, 1, "12  {status: done, result{accuracy, f1}}", ret=True)
    msg(1, 0, "13  success card, new statistics", ret=True)
    save(fig, OUT / "12_retrain_sequence.png")


def all_():
    system_architecture()
    high_level_workflow()
    dfd0()
    dfd1()
    dfd2()
    class_diagram()
    sequence_diagram()
    use_case()
    er_diagram()
    flowchart()
    feature_pipeline()
    retrain_sequence()


if __name__ == "__main__":
    all_()
