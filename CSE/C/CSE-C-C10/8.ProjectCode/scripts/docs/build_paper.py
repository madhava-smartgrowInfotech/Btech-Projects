"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for VenturePulse (batch C10) from facts.py (evaluation/*.json),
the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper

R = F.R
X = F.X
S = F.S


def make_figures():
    """Compact figures for the paper, written to docs/figures/paper_*.png (3.4 in column width)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 7.5,
                         "axes.spines.top": False, "axes.spines.right": False})
    NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#8B97A8"
    out = {}

    def bx(ax, cx, cy, w, h, t, c, fs=6.2):
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=c, ec=c, zorder=2))
        ax.text(cx, cy, t, ha="center", va="center", color="white", fontsize=fs, zorder=3, linespacing=1.15)

    def ar(ax, x1, y1, x2, y2, c="#334"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=c, lw=0.9, shrinkA=0, shrinkB=0), zorder=4)

    # ---- Fig. 1 architecture
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 78); ax.axis("off")
    tiers = [(64, "Browser: React 18 + Vite, port 5410", BLUE, ["Dashboard", "Analyze", "Performance", "Insights"]),
             (40, "FastAPI service, port 8410", TEAL, ["/predict", "/api/model-\nmetrics", "/api/insights", "/api/auth"]),
             (16, "Services and ML modules (app/)", ORANGE, ["predictor", "preproc.", "MiniLM\nembeddings", "retrieval"])]
    for cy, title, c, items in tiers:
        ax.add_patch(FancyBboxPatch((1, cy - 10.5), 98, 22, boxstyle="round,pad=0,rounding_size=1.5", fc="#F1F5FA", ec=c, lw=1.2, zorder=1))
        ax.text(3, cy + 8, title, fontsize=6.6, color="#14213D", fontweight="bold", va="center")
        for i, t in enumerate(items):
            bx(ax, 14 + i * 24, cy - 2, 21, 9.5, t, c, fs=5.9)
    ar(ax, 50, 52.5, 50, 50.6); ar(ax, 50, 28.5, 50, 26.6)
    ax.text(53, 51.6, "JSON over HTTP (Vite proxy)", fontsize=5.6, va="center")
    ax.text(53, 27.6, "Python calls", fontsize=5.6, va="center")
    ax.text(50, 1.2, "models/: best_model, preprocessor, train_fused, metadata - no SQL database", fontsize=5.7, ha="center", color="#14213D")
    p = os.path.join(F.FIGS, "paper_arch.png")
    fig.savefig(p, dpi=220, bbox_inches="tight"); plt.close(fig); out["arch"] = p

    # ---- Fig. 2 main flow (POST /predict)
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    ax.set_xlim(0, 100); ax.set_ylim(0, 80); ax.axis("off")
    bx(ax, 14, 68, 24, 13, "Form input\n18 fields + text\n+ k", BLUE)
    bx(ax, 42, 68, 24, 13, "Validate\n(Pydantic\nranges, k)", TEAL)
    bx(ax, 70, 68, 24, 13, "Structured\nvector s\n(37 features)", TEAL)
    bx(ax, 70, 46, 24, 13, "MiniLM\nembedding t\n(384-d, masked)", TEAL)
    bx(ax, 42, 46, 24, 13, "Fuse\n[0.5 s, 0.5 t]\nL2-normalise", ORANGE)
    bx(ax, 14, 46, 24, 13, "Model\nP(success)\nconfidence", PURPLE)
    bx(ax, 14, 22, 24, 13, "Balanced\ntop-k retrieval\n(train rows only)", PURPLE)
    bx(ax, 42, 22, 24, 13, "Explanation\n+ risk label", ORANGE)
    bx(ax, 72, 22, 28, 13, "JSON result:\noutcome, evidence,\ndrivers", NAVY)
    for a, b in [((26, 68), (30, 68)), ((54, 68), (58, 68)), ((70, 61.5), (70, 52.5)), ((58, 46), (54, 46)), ((30, 46), (26, 46)), ((14, 39.5), (14, 28.5)),
                 ((26, 22), (30, 22)), ((54, 22), (58, 22))]:
        ar(ax, *a, *b)
    ar(ax, 42, 39.5, 30, 28.5)
    ax.text(50, 6, "Median server time 148 ms (k=10) / 199 ms (k=50), CPU only", fontsize=5.8, ha="center", color="#14213D")
    p = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(p, dpi=220, bbox_inches="tight"); plt.close(fig); out["flow"] = p

    # ---- Fig. 3 results chart
    fig, (a, b) = plt.subplots(1, 2, figsize=(3.4, 2.15), gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.5})
    names = F.MODEL_ORDER_REAL
    short = ["LR", "DT", "RF", "XGB", "HGB"]
    x = np.arange(len(names))
    ba = [R["models"][n]["balanced_accuracy"]["mean"] for n in names]
    bs = [R["models"][n]["balanced_accuracy"]["std"] for n in names]
    au = [R["models"][n]["roc_auc"]["mean"] for n in names]
    us = [R["models"][n]["roc_auc"]["std"] for n in names]
    a.bar(x - 0.2, ba, 0.38, yerr=bs, color=BLUE, label="Balanced acc.", error_kw=dict(lw=0.7, capsize=1))
    a.bar(x + 0.2, au, 0.38, yerr=us, color=ORANGE, label="ROC-AUC", error_kw=dict(lw=0.7, capsize=1))
    a.set_xticks(x); a.set_xticklabels(short, fontsize=6.5)
    a.set_ylim(0.5, 0.9); a.tick_params(labelsize=6.5)
    a.legend(fontsize=5.8, frameon=False, loc="upper left", ncol=1)
    a.set_title("(a) Real table, 5 splits", fontsize=7)
    mods = ["Logistic Regression", "Random Forest", "XGBoost"]
    full = [X["with_all_features"][m]["roc_auc"]["mean"] for m in mods]
    drop = [X["without_posthoc_features"][m]["roc_auc"]["mean"] for m in mods]
    x2 = np.arange(3)
    b.bar(x2 - 0.2, full, 0.38, color=TEAL, label="all fields")
    b.bar(x2 + 0.2, drop, 0.38, color=PURPLE, label="no post-hoc")
    for xi, v in zip(x2 + 0.2, drop):
        b.text(xi, v + 0.006, f"{v:.2f}", ha="center", fontsize=5.5)
    b.set_xticks(x2); b.set_xticklabels(["LR", "RF", "XGB"], fontsize=6.5)
    b.set_ylim(0.5, 0.9); b.tick_params(labelsize=6.5)
    b.legend(fontsize=5.8, frameon=False, loc="upper right")
    b.set_title("(b) ROC-AUC, field ablation", fontsize=7)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=220, bbox_inches="tight"); plt.close(fig); out["results"] = p

    # ---- Fig. 4 drivers + threshold sweep
    fig, (a, b) = plt.subplots(1, 2, figsize=(3.4, 2.05), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.95})
    perm = R["feature_importance"]["random_forest_permutation_auc"][:6][::-1]
    lab = {"relationships": "relationships", "milestones": "milestones", "age_last_milestone_year": "age last milestone", "age_first_funding_year": "age first funding",
           "funding_total_usd": "funding total", "is_top500": "top-500 flag", "log_funding_total_usd": "log funding"}
    a.barh([lab.get(d["feature"], d["feature"]) for d in perm], [d["value"] for d in perm], color=BLUE, height=0.65)
    a.tick_params(labelsize=6.2)
    a.set_xlabel("ROC-AUC drop (permutation)", fontsize=6.3)
    a.set_title("(a) Random Forest drivers", fontsize=7)
    sw = R["threshold_sweep_logreg"]
    th = [d["threshold"] for d in sw]
    for key, col, nm in (("precision", BLUE, "precision"), ("recall", ORANGE, "recall"), ("f1", TEAL, "F1"), ("balanced_accuracy", PURPLE, "bal. acc.")):
        b.plot(th, [d[key] for d in sw], color=col, lw=1.1, label=nm)
    b.set_xlabel("Decision threshold on P(success)", fontsize=6.3)
    b.tick_params(labelsize=6.2)
    b.legend(fontsize=5.5, frameon=False, loc="lower left", ncol=2)
    b.set_ylim(0.2, 1.0)
    b.set_title("(b) Logistic Regression", fontsize=7)
    p = os.path.join(F.FIGS, "paper_drivers.png")
    fig.savefig(p, dpi=220, bbox_inches="tight"); plt.close(fig); out["drivers"] = p

    # ---- Fig. 4-5 output screens (crops of real captures)
    for name, src, box in (("shot1", "07_result.png", (288, 190, 1410, 680)), ("shot2", "08_performance.png", (288, 215, 1075, 470))):
        p = os.path.join(F.FIGS, f"paper_{name}.png")
        Image.open(F.shot(src)).convert("RGB").crop(box).save(p)
        out[name] = p
    return out


def pm3(blk, key):
    return f"{blk[key]['mean']:.3f}"


def cell(blk, key):
    return f"{blk[key]['mean']:.3f}±{blk[key]['std']:.3f}"


def build(path):
    figs = make_figures()
    P = Paper()
    m = R["models"]
    lat = F.LAT
    n_real, n_s, n_f = F.REAL_ROWS, F.REAL_SUCCESS, F.REAL_FAILURE

    authors = [[f"{n} ({r})", "Dept. of Computer Science and Engineering", "[College name]", "[City], India", "[email address]"] for n, r in F.STUDENTS]
    authors.append([f"{F.GUIDE} (guide)", f"{F.GUIDE_DESIGNATION}, Dept. of Computer Science and Engineering", "[College name]", "[City], India", "[email address]"])
    P.title_block("VenturePulse: Predicting Startup Success from Structured Signals, Text Embeddings and Comparable Startups", authors)
    P.begin_two_columns()

    P.abstract(
        "Most startups fail, yet investors and founders still judge early prospects largely by intuition. This paper builds and measures VenturePulse, a web application "
        "that estimates whether an early-stage startup will end in SUCCESS (acquisition or IPO) or FAILURE (closure). It combines 18 structured company fields with an "
        "optional business description embedded by a sentence encoder, predicts with a class-weighted classifier, and shows the comparable historical startups and the "
        "feature drivers behind each estimate. Four classifiers are compared with five repeated stratified 80/20 splits. On the public 922-row start-up table, Random Forest "
        f"and XGBoost lead with balanced accuracy {m['Random Forest']['balanced_accuracy']['mean']:.3f} and ROC-AUC {m['Random Forest']['roc_auc']['mean']:.3f} and {m['XGBoost']['roc_auc']['mean']:.3f}, ahead of "
        f"Logistic Regression ({m['Logistic Regression']['balanced_accuracy']['mean']:.3f}), but accuracy stays near {m['XGBoost']['accuracy']['mean']:.2f} and does not reach the 85-92 % "
        "reported in the base paper. Removing four fields that are recorded around the outcome lowers ROC-AUC by about 0.1. The shipped model was trained on a synthetic "
        "fallback table, and the text channel could not be tested on real data; both limits are stated.",
        ["startup success prediction", "machine learning", "random forest", "class imbalance", "business analytics", "similar-case retrieval", "feature importance"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Startups drive innovation and growth, but most fail within a few years because of weak funding, poor market fit, inexperienced management and competition {r:1,2}. "
           "Investors and founders mostly decide on experience and intuition, which is subjective and inconsistent {r:1}. Structured data on funding, team, sector and "
           "location exist from the earliest stage, and machine-learning classifiers can learn which combinations of them preceded success {r:4,7}. Ensembles such as Random "
           "Forest {r:18} and gradient boosting {r:19} handle the mixed categorical and numeric nature of such data well, but published studies leave four problems open: "
           "results are reported without dataset sizes or per-model tables {r:1}, information recorded after the outcome can leak into the features {r:9,29}, the "
           "successful class is imbalanced {r:22}, and a bare probability gives a founder nothing to act on.")
    P.para("This work therefore builds a complete, locally running system and measures it carefully. The contributions are: (1) VenturePulse, a FastAPI and React application that returns an "
           "outcome estimate, the comparable historical startups and the feature drivers for every request; (2) a fused representation of scaled structured features and "
           "MiniLM text embeddings with balanced, training-only cosine retrieval, adapted from the retrieval idea of {r:2,30} without a language model; (3) a reproducible benchmark on the real "
           "922-row public table with ten studies covering models, imbalance, thresholds, calibration, leakage-like fields and retrieval-only prediction; and (4) findings reported "
           "as found, including where the base paper's accuracy level is not reproduced. Section II reviews related work, Section III the method, Section IV the results, "
           "and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All training, evaluation and latency measurements ran on one desktop computer: {F.HARDWARE}.")
    P.sub("B", "Software Requirements")
    P.para(f"{F.SOFTWARE}. Models use scikit-learn {{r:21}} and XGBoost {{r:19}}; the sentence encoder is all-MiniLM-L6-v2 {{r:25}}.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Panjwani et al. {r:1} build a Flask-based startup success predictor. Funding history, team size, industry and location features come from Crunchbase and "
           "Kaggle data; missing values are imputed by mean or mode, categories are label or one-hot encoded, numbers are standardised, and ADASYN oversampling {r:24} balances the "
           "classes. Logistic Regression, Random Forest, SVM and Gradient Boosting are trained on a 70:30 split and scored by accuracy, precision, recall, F1 and ROC-AUC. "
           "The paper reports that Random Forest and Gradient Boosting are best, with accuracy between 85 and 92 %, that SVM is accurate but slower, and that funding amount, "
           "rounds, team experience, industry and location matter most. It gives neither the dataset size nor a table of per-model scores. Its own limitations are scarce "
           "real-time data, imbalance and external market conditions, and it names look-ahead bias as a risk {r:9}. This project keeps the model set, the metrics and the web "
           "tool, and adds retrieval of comparable startups, explanations, leakage checks and a protocol that reports spread over repeated splits.")
    P.para("**Machine-learning prediction.** Earlier studies compare Random Forest, Bayesian networks, SVM and boosting on funding and milestone features {r:4,7}; as summarised by "
           "{r:1}, ensembles exceed 80 % accuracy {r:7} and an ensemble over several sources reaches up to 90 % {r:11}. PCA-enhanced models improve classification {r:13}, "
           "and a bias-free design avoids look-ahead bias {r:9}. **Retrieval and text.** Maarouf et al. {r:2} retrieve the k most similar past startups and show them with "
           "their outcomes to a language model; on 4,034 Crunchbase startups (35.15 % successful) kNN in-context learning reaches balanced accuracy 0.713 at k=50, against "
           "0.631 for logistic regression, 0.634 for Random Forest and 0.618 for XGBoost, while a fused language model trained on 20,172 startups {r:14} reaches 0.743. Their study uses five repeated stratified 80/20 splits, masks company names to prevent "
           "memorisation, finds that performance saturates near 50 examples, and shows that structured fields alone are slightly better than text at very small k. "
           "**Interpretable and temporal models.** Mashhadi et al. {r:3} fit preprocessing on a 2010-2019 development window and apply it unchanged to later cohorts, weight "
           "classes by inverse prevalence, and compare logistic regression with Random Forest, XGBoost, LightGBM and CatBoost by PR-AUC with AUROC as tie-breaker. They "
           "obtain AUROC 0.817 for next funding (LightGBM), 0.872 for exit (Random Forest) and 0.921 for patenting (Random Forest); SHAP names time since the last round and "
           "age as first-order drivers, and reliability curves show optimism at high scores. **Economic evidence.** Judge disagreement in 67 venture competitions predicts success {r:16}, and a survey of 120 respondents "
           "links venture capital with startup success {r:17}.")
    rows = [
        ["Panjwani {r:1} (base)", "LR, RF, SVM, GB; ADASYN; 70:30", "Crunchbase / Kaggle, size not stated", "Accuracy 85-92 % (best)", "No dataset size or table"],
        ["Maarouf {r:2}", "kNN in-context learning with a language model", "4,034 startups, 35 % success", "Bal. acc. 0.713 (k=50)", "Needs an LLM and text"],
        ["Mashhadi {r:3}", "LR, RF, XGBoost, LightGBM; temporal splits", "Crunchbase panel 2010-2023", "AUROC 0.817-0.921", "Panel not available here"],
        ["Bidgoli {r:7}", "RF, GB, SVM, LR compared", "as summarised by {r:1}", "Ensembles above 80 %", "Not re-read"],
        ["Zbikowski {r:9}", "Bias-free prediction", "Crunchbase", "Look-ahead bias shown", "Not re-read"],
        ["Ross {r:11}", "Ensemble of several sources", "as summarised by {r:1}", "Up to 90 %", "Not re-read"],
        ["Gius {r:16}", "Judge disagreement", "67 venture competitions", "Predicts success", "Not a classifier"],
        ["Bhandari {r:17}", "Survey regression", "120 respondents", "VC linked to success", "Association only"],
    ]
    P.table("Related work: approach, data, reported result, limitation", ["Work", "Approach", "Data", "Reported result", "Limitation"], rows,
            widths=[0.62, 0.8, 0.72, 0.62, 0.64], size=6.5, align=["l", "l", "l", "l", "l"])
    P.para("**Research gap.** The surveyed work applies ensembles to startup success but rarely reports dataset sizes, controls fields recorded after the outcome, treats the imbalance "
           "explicitly, or tells the user which drivers and which comparable startups support a prediction. This work closes that gap with an application and with measurements "
           "of each of these points.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("Fig. 1 shows the three tiers. The browser interface (React 18 with Vite) calls a FastAPI service, which loads the saved artefacts once and calls the "
           "preprocessing, embedding, retrieval and prediction modules. State is held in files and in memory; no SQL database is used.")
    P.figure(figs["arch"], "System architecture: browser, FastAPI service, services and ML modules, and the saved model artefacts.")
    P.para(f"**Data.** Two tables are used and never mixed. The shipped application serves a {F.SYN_ROWS:,}-row synthetic fallback table ({F.SYN_SUCCESS} SUCCESS, {F.SYN_FAILURE} FAILURE) "
           "with the schema of the public table and template-generated descriptions, because the public download needs a login when the models were built; the wording of its "
           "success and failure templates differs, so its text channel leaks the label by construction. All real measurements use the public Kaggle 'Startup Success Prediction' "
           f"table {{r:32}}: {n_real} rows after de-duplication ({n_s} acquired = SUCCESS, {n_f} closed = FAILURE, 64.6 % success), US companies, structured columns only and "
           "no text. Nine numeric fields (funding total and rounds, ages at first and last funding and milestone, relationships, milestones, average participants), seven "
           "flags (VC, angel, rounds A to D, top-500) and the categorical state and industry give 37 encoded features plus log funding.")
    P.para("**Feature construction.** The public table's category code is mapped to the application's ten industry names (for example software, web and enterprise to Software; "
           "biotech to Biotech; medical and health to HealthTech) and the rest to Other, and the ten most frequent states are kept with the others grouped as Other. Funding "
           "velocity is approximated by the ages at first and last funding and the number of rounds; a log transform of total funding reduces the effect of a few very large "
           "rounds. No team-experience or market-trend field exists in either table, so the objective of engineering such features could only be met in part.")
    P.para("**Preprocessing.** Numbers are median-imputed and standardised, flags are most-frequent imputed, categories are one-hot encoded with unknown values ignored, and the target is "
           "mapped (acquired or IPO to 1, closed to 0). Preprocessing is fitted on the training part only. Descriptions are cleaned and the company name is masked, to prevent "
           "memorisation {r:2}. Each description (at most 2,000 characters) is embedded by all-MiniLM-L6-v2 into a 384-d vector t {r:25}; if no description is given an industry "
           "sentence is embedded instead.")
    P.para("**Models.** Logistic Regression (L-BFGS, balanced weights, C=1), a Decision Tree (depth 8, balanced), a Random Forest {r:18} (300 trees, minimum leaf 2, balanced) "
           "and XGBoost {r:19} (400 trees, depth 6, learning rate 0.05, subsample 0.8) are trained; HistGradientBoosting is added in the real-data study. The application serves the model "
           "with the best balanced accuracy, because the classes are unequal and plain accuracy rewards the majority class. With s the scaled structured vector and t the text "
           "vector, the fused representation and the success probability are")
    P.eq("x_f = [α s, (1 − α) t] / ||[α s, (1 − α) t]||,   α = 0.5,")
    P.eq("P(success | x) = 1 / (1 + exp(−(w·x + b))),")
    P.para("shown for the linear model. Evidence is retrieved by cosine similarity against training rows only, with a balanced quota of k/2 SUCCESS and k/2 FAILURE neighbours, "
           "k in {10, 20, 30, 50} {r:30}; the similarity-weighted vote over the k retrieved neighbours is")
    P.eq("p(x) = Σ_i sim(x, x_i) y_i / Σ_i sim(x, x_i),   i over the k neighbours.")
    P.figure(figs["flow"], "Main flow of one prediction request (POST /predict).")
    P.para("The prediction procedure is: (1) validate the payload (funding between 0 and 10^10 USD, rounds up to 20, relationships up to 200, milestones up to 50, description at most "
           "2,000 characters, k in the allowed set); (2) build one input row and derive log funding; (3) transform it with the fitted preprocessor; (4) embed the description; (5) fuse "
           "and normalise; (6) obtain P(success) and the larger class probability as confidence; (7) retrieve k balanced neighbours from the stored training vectors; (8) assemble "
           "the explanation and the risk label; (9) return the JSON result. Invalid input gets HTTP 422, an internal failure HTTP 500 with a message.")
    P.para("**Application.** The React interface has a landing page, a demo sign-in, a dashboard of the training data, the Analyze form and result screen, a Model performance page "
           "and an Insights page, all served from the same FastAPI back end through a proxy; the original server-rendered pages remain available. Sign-in uses an HMAC-signed, "
           "expiring token and only protects the demonstration screens; it is not a multi-user account system. If the saved artefacts are missing the service trains them on first "
           "start, so a clean checkout runs without manual steps.")
    P.para("**Explanation and risk.** The five largest signed coefficient or importance terms are returned with the retrieval statistics (neighbours per class, top similarity, mean "
           "similarity to each class). The label is 'Lower risk' for a SUCCESS verdict with confidence of at least 0.70, 'Moderate risk' from 0.55, otherwise 'Higher uncertainty'. "
           "The confidence is the larger class probability and is not a guarantee.")
    P.eq("BA = (TPR + TNR) / 2,   F1 = 2 P R / (P + R).")
    P.para("**Design decisions.** Logistic Regression is served on the synthetic table because it has the best balanced accuracy there, and its signed weights give a direct explanation; the "
           "ensembles are compared but not served, because the real-data study was run after the application was built. Retrieval searches training rows only and uses a balanced "
           "quota so that a majority class cannot crowd out the minority neighbours, and nothing leaves the computer: no external prediction service or key is used. Artefacts are "
           "plain files loaded once into memory, which keeps start-up simple at the cost of single-user operation.")
    P.para("**Evaluation protocol.** Five repeated stratified 80/20 splits (seed 42) give the mean and standard deviation of accuracy, balanced accuracy, precision, recall and F1, "
           "plus ROC-AUC {r:22} for the real table; a 70:30 protocol with five seeds mirrors the base paper. The same code and hyper-parameters run on the real table through "
           "a separate script, which writes its results to a JSON file read by this paper. Implementation and testing: the back end is about 1,350 lines of Python, the front end "
           f"about 3,000 lines of JavaScript, and {F.N_TESTS} automated checks ({F.N_UNIT} unit tests, {F.N_SMOKE} smoke checks and {F.N_EDGE} API edge cases) pass.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** The table is the public {n_real}-row table with {n_s} successful and {n_f} failed companies; each of the five stratified 80/20 splits tests on "
           "185 companies. Models are class-weighted and use the 0.5 threshold; values are mean ± standard deviation over the splits. Table II lists the results; the first block "
           "uses all fields, the second drops four fields recorded around the outcome (relationships, milestones, and the ages at first and last milestone), the third is a "
           "classifier-free retrieval vote, and the last row is the shipped model on its synthetic table.")
    rk = X["retrieval_only_structured"]["10"]
    rows = []
    for n, lab in zip(F.MODEL_ORDER_REAL, ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost", "HistGradientBoosting"]):
        b = m[n]
        rows.append([lab, f"{b['accuracy']['mean']:.3f}", cell(b, "balanced_accuracy"), f"{b['f1']['mean']:.3f}", f"{b['roc_auc']['mean']:.3f}"])
    for n, lab in (("Random Forest", "RF, no post-hoc fields"), ("XGBoost", "XGBoost, no post-hoc fields")):
        b = X["without_posthoc_features"][n]
        rows.append([lab, f"{b['accuracy']['mean']:.3f}", cell(b, "balanced_accuracy"), f"{b['f1']['mean']:.3f}", f"{b['roc_auc']['mean']:.3f}"])
    rows.append(["Retrieval vote only (k=10)", f"{rk['accuracy']['mean']:.3f}", cell(rk, "balanced_accuracy"), f"{rk['f1']['mean']:.3f}", f"{rk['roc_auc']['mean']:.3f}"])
    sl = S["models"]["Logistic Regression"]
    rows.append(["Shipped LR (synthetic, fused)", f"{sl['accuracy']['mean']:.3f}", cell(sl, "balanced_accuracy"), f"{sl['f1']['mean']:.3f}", "n/r"])
    P.table("Results on the real 922-row table (5 x 80/20 splits)", ["Model", "Acc.", "Bal. acc.", "F1", "AUC"], rows, widths=[1.3, 0.38, 0.68, 0.38, 0.38], size=6.5,
            align=["l", "c", "c", "c", "c"])
    P.para(f"Random Forest and XGBoost are best, both with balanced accuracy {m['Random Forest']['balanced_accuracy']['mean']:.3f}, accuracy {m['Random Forest']['accuracy']['mean']:.3f} and "
           f"{m['XGBoost']['accuracy']['mean']:.3f} and F1 near 0.83; Random Forest has the highest ROC-AUC ({m['Random Forest']['roc_auc']['mean']:.3f}). They are within one standard deviation "
           f"of HistGradientBoosting ({m['HistGradientBoosting']['balanced_accuracy']['mean']:.3f}) and clearly above Logistic Regression ({m['Logistic Regression']['balanced_accuracy']['mean']:.3f}, "
           f"ROC-AUC {m['Logistic Regression']['roc_auc']['mean']:.3f}) and the Decision Tree (ROC-AUC {m['Decision Tree']['roc_auc']['mean']:.3f}). With the base paper's 70:30 split over five seeds, Random "
           f"Forest scores accuracy {R['split_70_30']['Random Forest']['accuracy']['mean']:.3f} and Logistic Regression "
           f"{R['split_70_30']['Logistic Regression']['accuracy']['mean']:.3f}. The F1 values under that protocol are {R['split_70_30']['Random Forest']['f1']['mean']:.3f} (Random Forest), {R['split_70_30']['HistGradientBoosting']['f1']['mean']:.3f} (HistGradientBoosting) and {R['split_70_30']['Logistic Regression']['f1']['mean']:.3f} (Logistic Regression), with ROC-AUC {R['split_70_30']['Random Forest']['roc_auc']['mean']:.3f}, {R['split_70_30']['HistGradientBoosting']['roc_auc']['mean']:.3f} and {R['split_70_30']['Logistic Regression']['roc_auc']['mean']:.3f}. The ranking of ensembles over the linear baseline therefore agrees with {{r:1}}, but its 85-92 % accuracy is "
           "not reached, and since that paper states neither its data nor a table, the gap cannot be explained.")
    P.figure(figs["results"], "(a) Balanced accuracy and ROC-AUC of five models on the real table; (b) ROC-AUC with all fields and without the four post-hoc fields.", width=3.3)
    P.para("**Leakage-like fields.** relationships, milestones and the two milestone ages can be recorded after the outcome window, and the table has no dates to remove them {r:9,29}. "
           f"Dropping them lowers ROC-AUC from {X['with_all_features']['Random Forest']['roc_auc']['mean']:.3f} to {X['without_posthoc_features']['Random Forest']['roc_auc']['mean']:.3f} "
           f"for Random Forest and from {X['with_all_features']['XGBoost']['roc_auc']['mean']:.3f} to {X['without_posthoc_features']['XGBoost']['roc_auc']['mean']:.3f} for XGBoost, "
           "and removes the ensembles' lead over Logistic Regression (0.724). The headline numbers are therefore an upper bound for genuine early-stage prediction. "
           "**Features.** relationships ranks first by Random Forest Gini (0.162) and by permutation importance (drop of 0.060 in ROC-AUC), followed by milestones, the age of the last "
           "milestone, funding amount and age at first funding; the Logistic Regression weights are led by state, top-500 and industry indicators, so the two rankings differ.")
    im = R["imbalance"]
    rows3 = []
    for mo, ab in (("Logistic Regression", "LR"), ("Random Forest", "RF")):
        for st, lab in (("none", "none"), ("class_weight", "class weights"), ("oversample", "oversampling")):
            b = im[mo][st]
            rows3.append([f"{ab}, {lab}", cell(b, "balanced_accuracy"), f"{b['recall']['mean']:.3f}", f"{b['f1']['mean']:.3f}", f"{b['roc_auc']['mean']:.3f}"])
    P.table("Imbalance handling on the real table (SUCCESS is the majority class)", ["Model, strategy", "Bal. acc.", "Recall", "F1", "AUC"], rows3,
            widths=[1.1, 0.7, 0.45, 0.45, 0.45], size=6.5, align=["l", "c", "c", "c", "c"])
    P.para(f"**Imbalance and threshold.** SUCCESS is the majority class here (64.6 %), the reverse of the rare-success assumption {{r:22}}. As Table III shows, class weights and oversampling "
           "did not raise ROC-AUC (Random Forest 0.820 without any treatment, 0.816 with either); they trade recall of the success class for precision (Logistic Regression recall "
           "0.815 unweighted, 0.673 weighted). For weighted Logistic Regression, balanced accuracy is flat (0.709-0.714) for thresholds between 0.30 and 0.50 while recall rises from 0.673 to 0.875, and "
           "calibration is poor: in the 0.3-0.4 bin the predicted success probability is 0.348 but 0.648 of companies succeeded. **Retrieval.** The retrieval vote alone, "
           "with no trained model, scores balanced accuracy 0.70-0.71 and ROC-AUC 0.77-0.79 for every k, equal to Logistic Regression, so the retrieved evidence is as informative as the "
           "linear model; k matters little on real data, whereas on the synthetic table accuracy grows from 0.654 (k=10) to 0.698 (k=50).")
    P.para(f"**Synthetic data.** The shipped Logistic Regression reaches balanced accuracy {sl['balanced_accuracy']['mean']:.3f} on its synthetic table (structured only 0.714, text only "
           "0.599, combined 0.749). Because the synthetic text leaks the label, this does not show that text helps; the text half of the fusion is untested on real data. "
           f"Trained on the synthetic rows and tested on all {n_real} real rows, Logistic Regression gives balanced accuracy "
           f"{R['synthetic_to_real']['results']['Logistic Regression']['balanced_accuracy']:.3f} and ROC-AUC {R['synthetic_to_real']['results']['Logistic Regression']['roc_auc']:.3f}.")
    P.figure(figs["shot1"], "Output screen (Analyze): SUCCESS, confidence 83.3 %, Lower risk, key drivers and the 25 + 25 comparable startups, for a submitted software startup.", width=3.3)
    P.figure(figs["shot2"], "Output screen (Model performance): model comparison and charts of the shipped model on its synthetic table.", width=3.3)
    P.para("Fig. 4 is a capture of the Analyze result for a software startup in California with USD 2.5 million raised over two rounds, six relationships, three milestones, venture "
           "backing and a round A: the model returns SUCCESS with 83.3 % confidence and 'Lower risk', cites has_roundC, funding rounds, relationships, venture backing and milestones "
           "as its largest terms, and lists 50 comparable startups (25 and 25) with top similarity 0.580. This screen is served by the model trained on the synthetic table, so "
           "its confidence reflects that table and not the real one. Fig. 5 shows the Model performance page of the same model. Fig. 6 plots the permutation drivers on the real "
           "table and the threshold sweep of Logistic Regression.")
    P.figure(figs["drivers"], "(a) Top permutation drivers of Random Forest on the real table; (b) precision, recall, F1 and balanced accuracy of Logistic Regression against the decision threshold.", width=3.3)
    P.para("**Size and industries.** Random Forest with 50, 100, 300 and 600 trees reaches balanced accuracy 0.742, 0.744, 0.746 and 0.741, so the 300 trees used are adequate and "
           "more trees add nothing. Accuracy by industry on one test split is 0.73 for Software (106 companies) and 0.89 for Media (35), but groups of six or ten companies cannot be read.")
    P.para(f"**Comparison and cost.** Maarouf et al. {{r:2}} score 0.713 balanced accuracy for retrieval with a language model and 0.618-0.634 for supervised baselines on 4,034 startups with "
           "35 % successes; this work measures 0.709 (Logistic Regression) to 0.746 (ensembles) on a different table with no text and 65 % successes, so the numbers are not comparable. "
           f"The temporal study {{r:3}} reports AUROC 0.817-0.921 with leakage-safe splits, whereas this work has no temporal split. The server answers POST /predict in a median "
           f"{lat['predict_k10']['median_ms']:.0f} ms (k=10) and {lat['predict_k50']['median_ms']:.0f} ms (k=50), 95th percentile about 590 ms, and read endpoints in 3-15 ms (CPU, local requests).")
    P.para(f"**Testing and objectives.** The {F.N_UNIT} unit tests cover health, dataset loading, preprocessing with missing values, embedding and fusion, balanced retrieval, prediction "
           f"and pages; the {F.N_SMOKE} smoke checks run against the live server; and the {F.N_EDGE} edge cases confirm that a wrong k, negative or oversized funding, too many rounds, an "
           "over-long description, a non-numeric value and a tampered token are rejected with 422 or 401, while an empty body, an unknown industry or state, and maximum values are "
           "accepted. Against the six objectives, collecting data and engineering features are only partly met (the real table lacks team-experience and market fields, and funding "
           "velocity is approximated by the ages at first and last funding), while model comparison, imbalance handling, driver analysis and the full metric set are met.")
    P.para("**Calibration and confidence.** The class-weighted Logistic Regression under-states the success probability on this majority-success table: observed success rates "
           "exceed the mean predicted probability in every bin below 0.9 (for example 0.436 against 0.252 in the 0.2-0.3 bin and 0.755 against 0.550 in the 0.5-0.6 bin), and only the "
           "top bin (0.953 predicted, 0.931 observed) is close. The 'confidence' shown by the application is the larger class probability and the three risk labels are fixed rules, so "
           "neither is a calibrated statement; isotonic recalibration, which {r:3} recommends when calibrated probabilities are needed, was not applied.")
    P.para("**Reproducibility.** The real-table study of five models, six imbalance settings, two protocols, the threshold sweep and the transfer test runs in 139 s on the CPU, and "
           "the leakage, retrieval and industry studies in 14 s; every number here is read from the JSON files they write. Hyper-parameters were fixed from the application and "
           "not tuned per model, so the ranking of the three boosted or bagged ensembles, which differ by less than one standard deviation, should not be over-read.")
    P.para("**Failure cases and limits.** Random Forest misses 19.6 of 120 successes and wrongly accepts 22.4 of 65 failures per test fold; small industries are unreliable (Biotech and "
           "CleanTech groups of six companies, accuracy 0.33 and 0.50). Test folds have only 185 rows, the data are US-only and have no founder or market fields, and no significance test, "
           "load test or user study was run.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("VenturePulse meets its engineering goals: a local application that returns an outcome estimate with comparable startups and feature drivers, backed by "
           f"{F.N_TESTS} passing checks. Against the objectives, four classifiers were compared, imbalance was handled and examined, the features separating the classes were "
           "identified, and accuracy, precision, recall, F1 and ROC-AUC were measured. The key finding is that ensembles beat Logistic Regression on the real table "
           f"(balanced accuracy {m['Random Forest']['balanced_accuracy']['mean']:.3f} against {m['Logistic Regression']['balanced_accuracy']['mean']:.3f}) but fall short of the 85-92 % accuracy "
           "of the base paper, and that about a tenth of ROC-AUC rests on fields recorded around the outcome. Limitations are the synthetic fallback in the shipped model, the "
           "untested text channel, the absence of founder, team-experience and market data, and the absence of a temporal split. Future work: temporal validation on dated data, "
           "founder and market features, SHAP-based explanations, calibrated probabilities, and testing text retrieval on real descriptions. A larger dated dataset, such as a "
           "firm-quarter panel {r:3}, would allow leakage-safe evaluation, and a user study with founders and investors would show whether the comparable startups and drivers "
           "make an estimate easier to act on, which this work did not test.")

    P.references()
    P.save(path)


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    build(out)
    print("wrote", out)
