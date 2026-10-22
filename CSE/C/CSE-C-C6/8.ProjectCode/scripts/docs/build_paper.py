"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for the Fake News Detection System (batch C6) from facts.py (experiments/liar2/metrics.json),
the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from .lit import LIT_TABLE
from .paper import Paper

A = F.A
PT = A["proposed_test"]


def make_figures():
    """Compact figures for the paper, written to docs/figures/paper_*.png (3.4 in column width)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False})
    out = {}
    fig, (a, b) = plt.subplots(2, 1, figsize=(3.4, 4.3), gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.62})
    rows = [("Majority class", A["majority_test"], "#8B97A8"), ("Compl. NB (all data)", A["ref_full_ComplementNB_test"], "#8B97A8"),
            ("Linear SVM (all data)", A["ref_full_LinearSVC_test"], "#8B97A8"), ("Log. regression (all data)", A["ref_full_LogisticRegression_test"], "#6C7A8C"),
            ("PCA + default SVM", A["pca_svc_default_test"], "#2B6CB0"), ("PCA + random search", A["random_search_test"], "#D9772F"),
            ("PCA + Firefly + MSVM", A["proposed_test"], "#6B5BD2")]
    y = np.arange(len(rows))[::-1]
    for yi, (n, blk, c) in zip(y, rows):
        m, s = blk["f1_macro"]["mean"], blk["f1_macro"]["std"]
        a.barh(yi, m, color=c, height=0.62, xerr=s if s else None, error_kw=dict(lw=0.8, capsize=1.5))
        a.text(m + s + 0.008, yi, f"{m:.3f}", va="center", fontsize=7)
    a.set_yticks(y)
    a.set_yticklabels([r[0] for r in rows], fontsize=7)
    a.set_xlim(0, 0.62)
    a.set_xlabel("Test macro-F1 (mean of 3 seeds, whiskers: std)", fontsize=7)
    a.set_title("(a) Models on the LIAR2 test split", fontsize=8)
    bins = F.EA["by_confidence"]
    lab = ["<0.4", "0.4-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", ">=0.8"]
    x = np.arange(len(bins))
    b.bar(x, [q["accuracy"] for q in bins], color="#2B6CB0", width=0.62)
    for xi, q in zip(x, bins):
        b.text(xi, q["accuracy"] + 0.02, f"{q['accuracy']:.2f}\nn={q['n']}", ha="center", fontsize=6.3)
    b.set_xticks(x)
    b.set_xticklabels(lab, fontsize=7)
    b.set_ylim(0, 1.2)
    b.set_xlabel("Highest class probability of the prediction", fontsize=7)
    b.set_ylabel("Accuracy", fontsize=7)
    b.set_title("(b) Accuracy by confidence (seed 42)", fontsize=8)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=220, bbox_inches="tight")
    plt.close(fig)
    out["results"] = p
    fig, (c, d) = plt.subplots(1, 2, figsize=(3.4, 1.75), gridspec_kw={"width_ratios": [1.1, 1], "wspace": 0.55})
    cols = ["#6B5BD2", "#2B6CB0", "#14907F"]
    for r, col in zip(sorted(F.SEEDS), cols):
        h = F.A["firefly_history"][F.SEEDS.index(r)]
        c.plot(range(1, len(h) + 1), h, marker="o", ms=2.2, lw=1, color=col, label=f"seed {r}")
    c.set_xlabel("Generation", fontsize=7)
    c.set_ylabel("Best fitness", fontsize=7)
    c.legend(fontsize=6, frameon=False)
    c.set_title("(a) Firefly convergence", fontsize=7.5)
    cm = np.array(F.A["confusion_matrix_seed42"])
    nm = cm / cm.sum(axis=1, keepdims=True)
    d.imshow(nm, cmap="Blues", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            d.text(j, i, f"{cm[i, j]}", ha="center", va="center", fontsize=6.5, color="white" if nm[i, j] > 0.5 else "black")
    d.set_xticks(range(3))
    d.set_yticks(range(3))
    d.set_xticklabels(["R", "P", "F"], fontsize=6.5)
    d.set_yticklabels(["R", "P", "F"], fontsize=6.5)
    d.set_xlabel("Predicted", fontsize=7)
    d.set_ylabel("True", fontsize=7)
    d.set_title("(b) Test confusion (seed 42)", fontsize=7.5)
    for sp in d.spines.values():
        sp.set_visible(False)
    p = os.path.join(F.FIGS, "paper_firefly.png")
    fig.savefig(p, dpi=220, bbox_inches="tight")
    plt.close(fig)
    out["firefly"] = p
    out.update(make_diagrams(plt))
    for name, src, box in (("detect", "11_liar2_detect_fake.png", (288, 95, 955, 700)), ("analytics", "18_liar2_analytics_charts.png", (288, 98, 1410, 575))):
        p = os.path.join(F.FIGS, f"paper_{name}.png")
        Image.open(F.shot(src)).convert("RGB").crop(box).save(p)
        out[name] = p
    return out


def make_diagrams(plt):
    """Two redrawn diagrams with column-width text (the full-size ones in docs/diagrams are too small at 3.4 in)."""
    from matplotlib.patches import FancyBboxPatch

    NAVY, BLUE, TEAL, ORANGE, PURPLE = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2"

    def bx(ax, cx, cy, w, h, t, c, fs=6.4):
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=c, ec=c, zorder=2))
        ax.text(cx, cy, t, ha="center", va="center", color="white", fontsize=fs, zorder=3, linespacing=1.15)

    def ar(ax, x1, y1, x2, y2, c="#334"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=c, lw=0.9, shrinkA=0, shrinkB=0), zorder=4)

    out = {}
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ax.set_xlim(0, 100); ax.set_ylim(0, 74); ax.axis("off")
    tiers = [(62, "Browser: React + Vite, 6 screens", BLUE, ["Detect", "Batch", "Analytics", "Retrain"]),
             (38, "FastAPI service: 8 routes under /api", TEAL, ["/predict", "/batch/run", "/retrain", "/model"]),
             (14, "Library src/: shared with CLI and Streamlit", ORANGE, ["clean + features", "PCA", "Firefly", "MSVM"])]
    for cy, title, c, items in tiers:
        ax.add_patch(FancyBboxPatch((1, cy - 10), 98, 21, boxstyle="round,pad=0,rounding_size=1.5", fc="#F1F5FA", ec=c, lw=1.2, zorder=1))
        ax.text(3, cy + 7.5, title, fontsize=6.8, color="#14213D", fontweight="bold", va="center")
        for i, t in enumerate(items):
            bx(ax, 14 + i * 24, cy - 2, 21, 9, t, c)
    ar(ax, 50, 51, 50, 49); ar(ax, 50, 27, 50, 25)
    ax.text(52, 50, "JSON / CSV over HTTP", fontsize=5.8, va="center")
    ax.text(52, 26, "Python calls", fontsize=5.8, va="center")
    ax.text(50, 0.8, "models/msvm_model.pkl (joblib bundle) - no database", fontsize=6, ha="center", va="center", color="#14213D")
    p = os.path.join(F.FIGS, "paper_arch.png")
    fig.savefig(p, dpi=220, bbox_inches="tight"); plt.close(fig); out["arch"] = p

    fig, ax = plt.subplots(figsize=(3.4, 2.55))
    ax.set_xlim(0, 100); ax.set_ylim(0, 76); ax.axis("off")
    ax.text(1, 73, "Training (offline or Retrain screen)", fontsize=6.8, fontweight="bold", color="#14213D")
    tr = [("Text +\nlabel", BLUE), ("Clean,\nTF-IDF,\n25 style", TEAL), ("Scale,\nPCA", TEAL), ("80/20\nsplit", TEAL), ("Firefly:\nmask, C,\ngamma", ORANGE), ("RBF\nMSVM", PURPLE)]
    for i, (t, c) in enumerate(tr):
        bx(ax, 8.5 + i * 16.6, 58, 14.6, 17, t, c, fs=6)
        if i:
            ar(ax, 8.5 + i * 16.6 - 8.4, 58, 8.5 + i * 16.6 - 7.4, 58)
    ax.text(1, 40, "Inference (every request)", fontsize=6.8, fontweight="bold", color="#14213D")
    inf = [("News\ntext", BLUE), ("Clean,\nTF-IDF,\n25 style", TEAL), ("Scale,\nPCA", TEAL), ("Keep\nmasked\ncomponents", ORANGE), ("MSVM", PURPLE), ("Verdict +\nconfidence\n+ cues", NAVY)]
    for i, (t, c) in enumerate(inf):
        bx(ax, 8.5 + i * 16.6, 24, 14.6, 17, t, c, fs=6)
        if i:
            ar(ax, 8.5 + i * 16.6 - 8.4, 24, 8.5 + i * 16.6 - 7.4, 24)
    ar(ax, 91.5, 49.5, 58.2, 33.0, "#D9772F")
    ax.text(88, 44, "saved bundle", fontsize=5.8, color="#D9772F", ha="right")
    ax.text(50, 4, "Fitted vectorizer, scaler, PCA, mask, C, gamma and SVM are saved once and reused", fontsize=5.8, ha="center", color="#14213D")
    p = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(p, dpi=220, bbox_inches="tight"); plt.close(fig); out["flow"] = p
    return out


def build(path):
    figs = make_figures()
    L = F.LAT[0]
    lv = F.LV
    ea = F.EA
    pc = A["per_class_test"]
    P = Paper()

    authors = [[n, "Dept. of Computer Science and Engineering", "[College name]", "[City], India", "[email address]"] for n, _ in F.STUDENTS]
    authors = [[f"{n} ({r})"] + a[1:] for (n, r), a in zip(F.STUDENTS, authors)]
    authors.append([f"{F.GUIDE} (guide)", f"{F.GUIDE_DESIGNATION}, Dept. of Computer Science and Engineering", "[College name]", "[City], India", "[email address]"])
    P.title_block("Fake News Detection Using a Feature-Based Optimised Multi-Class SVM: PCA, Firefly Search and a PARTIALLY TRUE Class", authors)
    P.begin_two_columns()

    P.abstract(
        "Fabricated news spreads faster than fact-checks, and many detectors rely on heavy neural models. This paper builds and measures a light alternative: "
        "TF-IDF and 25 stylometric features are reduced by principal component analysis (PCA), and the Firefly algorithm chooses the PCA components and the parameters of a "
        "multi-class RBF support vector machine (MSVM) that labels a statement REAL, PARTIALLY TRUE or FAKE. The pipeline is packaged as a web application with single and "
        f"batch checking, analytics and retraining. On the LIAR2 fact-checking dataset, trained on {F.NTRAIN:,} statements and scored on {F.NTEST:,} unseen statements over three seeds, "
        f"it reaches macro-F1 {F.pm(PT)} and accuracy {F.pm(PT, 'accuracy')}. A default SVM on the same features, an equal-budget random search and the Firefly search are within noise "
        f"of each other, and a logistic regression on plain TF-IDF trained in under a second reaches {A['ref_full_LogisticRegression_test']['f1_macro']['mean']:.3f}. "
        f"The optimiser therefore did not improve accuracy and cost about {A['train_time_s']['mean']:.0f} s of training. PARTIALLY TRUE is the hardest class, and the displayed "
        "probabilities disagree with the verdict on about half of the statements.",
        ["Fake news detection", "feature selection", "Firefly algorithm", "LIAR2", "multi-class SVM", "principal component analysis", "TF-IDF"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Automatic fake news detection is an active research area {r:1}. False stories reach large audiences before any fact-check is published, and they travel farther and faster than true ones {r:17}. Manual fact-checking cannot match "
           "the volume of online publication, so text classifiers are used to flag suspicious items {r:16}. Text can be classified from word statistics and writing style {r:19,21}, "
           "but the usual choices are costly in different ways: neural and transformer detectors need GPUs and large corpora {r:1,3}, while classical pipelines on high-dimensional "
           "TF-IDF vectors are slow to tune and easy to overfit.")
    P.para("Most detectors also answer a binary question. Fact-checkers, however, grade claims on a scale, and language differs between false, half-true and true claims {r:22}; a "
           "claim that mixes accurate figures with an exaggerated conclusion is neither real nor fake. Benchmark studies show that such graded data, for example LIAR-PLUS, are the hardest "
           "for nearly all models even after the labels are collapsed to two classes {r:2}. The gap this work addresses is a computationally light pipeline in which feature reduction "
           "and metaheuristic tuning aim to deliver useful accuracy at low cost, with an explicit PARTIALLY TRUE class, and an honest measurement of whether it does.")
    P.para("The contributions are: (1) an end-to-end pipeline of TF-IDF and stylometric features, PCA, a Firefly search over the retained components and the SVM parameters, and an "
           "RBF multi-class SVM with balanced class weights; (2) a web application that wraps it with single and batch detection, model analytics and retraining; (3) a "
           "reproducible benchmark on LIAR2 against mask-only, equal-budget random-search and linear baselines; and (4) findings that are stated as found, including that "
           "the optimiser gave no gain beyond noise. Section II reviews related work, Section III the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"Every training run and measurement used one desktop computer: {F.HARDWARE}. Training and prediction ran on the CPU only.")
    P.sub("B", "Software Requirements")
    P.para(f"{F.SOFTWARE}. The model code uses scikit-learn {{r:14}}; the web application is a FastAPI service with a React interface.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Saad et al. {r:1} detect Arabic fake news. They compile 7,474 articles from trusted outlets, unverified online content labelled by the authors "
           "(Fleiss' kappa 0.80 on a 500-sample subset) and benchmark data partly translated from LIAR and WELFake, and split them 80/20. A neural network on CAMeLBERT contextual "
           "embeddings is compared with AraBERT, AraELECTRA and MARBERTv2 embeddings and with resampling (oversampling, undersampling, SMOTE) against class weighting in the loss {r:15}. "
           "Its data come about 45 % from trusted outlets, 30 % from unverified online content and 25 % from benchmark sets; the classifier is a dense layer of 256 units with dropout 0.2, trained with "
           "Adam (learning rate 5e-4, batch 16, 10 epochs) on embeddings of at most 128 tokens. "
           "The TF-IDF plus neural-network baseline reaches 90.97 % accuracy; CAMeLBERT with class weighting reaches 95.52 % accuracy, 96.19 % F1, 95.48 % precision and 96.90 % recall "
           "on a Tesla T4 GPU, and LIME and SHAP explain the decisions. The task is binary and Arabic, and the authors leave cross-domain generalisation and real-time use as future "
           "work. This project keeps three ideas: weight classes instead of resampling, report several metrics, and compare against baselines; it differs in features (TF-IDF, "
           "stylometry, PCA), classifier (SVM), a metaheuristic, three classes, English text and CPU-only compute.")
    P.para("**Related work.** Dataset and benchmark studies: LIAR {r:5} and its extension LIAR2 {r:4} supply short fact-checked statements with six truthfulness labels, and an experimental "
           "comparison of 12 approaches on 10 English datasets {r:2} finds LIAR-PLUS the hardest (F1 0.56 for logistic regression, 0.57 for SVM, binary labels). Feature-based detection: "
           "n-gram TF-IDF with a linear SVM is a strong classical choice {r:19}, style features separate hyperpartisan from mainstream news but are a weak proxy for truth {r:21}, and "
           "language cues differ across degrees of falsehood {r:22}. Neural models: transformer embeddings dominate recent results {r:1}, and a Transformer with a BiGRU and Bayesian "
           "optimisation reports 99.73 % test accuracy on its own corpus {r:3}. Optimisation: the Firefly algorithm {r:6} and evolutionary feature selection {r:24} shrink feature sets "
           "for classification {r:25}, and multi-class SVMs are usually built from binary ones {r:9}.")
    rows = [
        ["Saad {r:1} (base)", "CAMeLBERT + NN, class weights", "7,474 Arabic articles, binary", "Acc. 95.52, F1 96.19 %", "Arabic, binary, GPU"],
        ["Dell'Oglio {r:2}", "12 approaches compared", "10 English sets, binary", "LIAR-PLUS F1 0.56-0.57 (LR, SVM)", "No middle class"],
        ["Huang {r:3}", "TF-IDF, Transformer, BiGRU, Bayesian opt.", "News corpus, binary", "99.73 % test acc.", "Easy own data"],
        ["Xu {r:4}", "Fuzzy deep hybrid net; LIAR2", "18,369 / 2,297 / 2,296", "Benchmark used here", "Deep model"],
        ["Ahmed {r:19}", "N-gram TF-IDF, linear SVM", "News corpora, binary", "Linear SVM strong", "Binary"],
        ["Potthast {r:21}", "Style features", "Fact-checked news", "Detects hyperpartisan style", "Weak truth proxy"],
        ["Rashkin {r:22}", "Language of falsehood levels", "PolitiFact, news", "Cues differ by level", "Analysis"],
        ["Zhang {r:25}", "Firefly feature selection", "Benchmark sets", "Smaller feature sets", "Search cost"],
    ]
    P.table("Related work: approach, data, reported result, limitation", ["Work", "Approach", "Data", "Reported result", "Limitation"], rows,
            widths=[0.62, 0.8, 0.72, 0.7, 0.56], size=6.5, align=["l", "l", "l", "l", "l"])
    P.para("Table I shows the gap: transformer detectors report high binary accuracy on their own data, while the cheap, graded and explicit three-class setting is rarely "
           "measured. The reported figures come from different data and metrics and are not ranked here.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the system: a React interface with six screens, a FastAPI service with eight routes (health, model information, samples, single prediction, "
           "batch preview and run, retrain and job status) and a pure-Python library that the service, a command-line tool and a Streamlit app all share. The fitted objects are saved "
           "once as a joblib bundle and held in memory behind a lock; retraining runs in a background thread and swaps the model in atomically. There is no database.")
    P.figure(figs["arch"], "System architecture: browser, FastAPI service, shared library and the saved model bundle (full diagram: docs/diagrams/01).")
    P.para("**Pipeline.** Fig. 2 shows the two paths. A text is lower-cased, URLs, mentions and non-letters are removed, stop words and tokens of two characters or fewer are dropped, and "
           "TF-IDF {r:13} with unigrams and bigrams (sublinear term frequency, minimum document frequency 2, at most 4,000 terms) is computed. 25 stylometric features are appended: length "
           "and sentence statistics, capital letters, exclamation and question marks, digits, URLs, first-person and superlative rates, and lexicon ratios of sensational and credibility words. "
           "The 4,025 columns are standardised and projected by PCA {r:10}, which keeps components up to 95 % of the variance but at most 300.")
    P.figure(figs["flow"], "Training path (top) and inference path (bottom) of the pipeline.")
    P.para("**Features and projection.** The stylometric block is deliberately cheap: 25 numbers per text that need no language model. PCA {r:10} finds the orthonormal directions of largest variance "
           "of the standardised feature matrix X; with eigenvalues λ₁ ≥ λ₂ ≥ … of its covariance matrix, the first c components are kept, where c is the smallest number with")
    P.eq("(λ₁ + … + λ_c) / (λ₁ + … + λ_n) ≥ 0.95,   c ≤ 300.")
    P.para(indent=0, text="The cap bounds the cost of the search; on short statements it binds, as Section IV shows. Standardising every TF-IDF column before PCA gives rare terms the same weight "
           "as common ones, a design choice that is revisited in the discussion.")
    P.para(f"**Data.** LIAR2 {{r:4}} has {F.NTRAIN_FULL:,} training, {F.NVALID:,} validation and {F.NTEST:,} test statements of about 18 words, each with one of six PolitiFact labels (licence "
           "Apache-2.0). Only the statement text is used; speaker, justification and count columns would leak the label. The project mapping is true and mostly-true to REAL, half-true to "
           f"PARTIALLY TRUE, and barely-true, false and pants-on-fire to FAKE, giving {F.A['test_class_counts'][0]} REAL, {F.A['test_class_counts'][1]} PARTIALLY TRUE and "
           f"{F.A['test_class_counts'][2]:,} FAKE test statements; always answering FAKE scores {A['majority_test']['accuracy']['mean']:.3f} accuracy but only {A['majority_test']['f1_macro']['mean']:.3f} macro-F1. "
           f"Because the Firefly search needs hundreds of SVM fits, each run trains on a stratified random subsample of {F.NTRAIN:,} statements, of which 80 % fit the classifier; seeds "
           f"{', '.join(str(s) for s in sorted(F.SEEDS))} change the subsample and the search.")
    P.para("**Firefly search.** Each of 10 fireflies encodes a logit for every PCA component and log10 C in [-1, 3] and log10 gamma in [-4, 1]. A component is kept when its sigmoid "
           "exceeds 0.5. The brightness of a firefly is the three-fold cross-validated macro-F1 of a class-weighted RBF SVM on the kept components, minus a size penalty,")
    P.eq("f(x) = F1_cv(m, C, γ) − 0.02 · k / n,")
    P.para(indent=0, text="where k components of n are kept. Following Yang {r:6}, a firefly i moves towards each brighter firefly j with attractiveness β = β₀ exp(−γ₀ r²/d) and a "
           "decaying random step,")
    P.eq("x_i ← x_i + β (x_j − x_i) + α_t ε,   α_t = 0.2 · 0.97^t.")
    P.para(indent=0, text="The dimmest firefly is reset near the best one each generation. After 12 generations (about "
           f"{A['n_firefly_evals']['mean']:.0f} fitness evaluations) the best mask, C and gamma train the final classifier: an RBF SVM {{r:8}} with balanced class weights, one-vs-rest decision "
           "shape and Platt-scaled probabilities {r:12}; the three-class problem is handled internally by pairwise coupling {r:9}. Class weights, as in the base paper {r:1}, counter the "
           "imbalance {r:15}.")
    P.para("**Classifier.** For a masked component vector z, the RBF kernel is K(z, z′) = exp(−γ‖z − z′‖²), and the SVM {r:8} solves for each class k a one-vs-rest problem with "
           "penalty C·w_k, where the balanced weight is w_k = N / (3 N_k) for N_k training statements in class k; rarer classes therefore cost more to misclassify. The label is the class "
           "with the largest decision value, and Platt scaling {r:12} maps decision values to probabilities in a separate cross-validated fit. This is why the label and the probabilities can disagree.")
    P.para("**Cost of the search.** Every fitness evaluation fits three SVMs on about 1,600 statements, so a search of roughly 550 evaluations means over 1,600 fits. This, not the final "
           "fit (about a second), is what takes minutes, and it grows with the number of fireflies and generations, which the Retrain screen exposes as sliders (4-20 fireflies, "
           "3-30 generations, 1,000-8,000 TF-IDF terms).")
    P.para("**Application.** The Detect screen takes a headline and text (at least five words), returns the verdict, confidence, probabilities and lists of sensational and credibility cue "
           "words found in the text. Batch check previews an uploaded CSV, lets the user pick the text column (limits: 25 MB, 20,000 rows) and returns a verdict per row, the class "
           "distribution and a results file. Analytics reads the loaded model's statistics, and Retrain accepts a labelled CSV (REAL, PARTIALLY TRUE, FAKE or 0-2, or LIAR names; at "
           "least 30 rows), runs the fit in the background and replaces the model without a restart. Invalid input returns 400, 413 or 422 with a message.")
    P.para("**Protocol and baselines.** Models are scored on the full official test split; macro-F1 (the mean of the three class F1 values) is the main metric because accuracy rewards the "
           "majority class. Comparisons use the same features and split: the product's baseline (default RBF SVM on all PCA components); a mask-only variant (Firefly mask, default C and "
           "gamma); random search with the same number of evaluations and the same fitness; and linear SVM, logistic regression and complement naive Bayes on plain TF-IDF, on the "
           f"{F.NTRAIN:,}-statement subsample and on all {F.NTRAIN_FULL:,} statements. The shipped demonstration model, trained on 750 synthetic template sentences, is also scored on LIAR2.")
    P.para("**Design rationale.** TF-IDF with bigrams captures topical and phrasal cues at a cost of milliseconds; the stylometric block adds signals that vocabulary misses, such as shouting, "
           "urgency and numeric density. PCA was chosen because a 4,025-dimensional sparse space with a few thousand statements invites overfitting; an RBF SVM copes with "
           "the remaining dense space and needs only two parameters. Searching the mask together with C and gamma lets the optimiser trade feature count against accuracy through the size penalty, "
           "and a metaheuristic is used because the fitness, a cross-validated score of a discrete mask and two continuous values, has no gradient. Macro-F1 is preferred to accuracy because the "
           "classes are unbalanced and the middle class is the one of interest.")
    P.para(f"**Reproducibility.** Every random choice (subsample, split, search, Platt folds) is seeded; one script, run_experiments.py, trains each seed, scores the validation and test splits and "
           f"writes a JSON file per seed, and the aggregate numbers in this paper are read from those files. LIAR2 is downloaded from its public repository and is not redistributed with the code.")
    P.para(f"**Verification.** {F.N_TESTS} automated checks pass: {F.N_SMOKE} end-to-end API checks, {F.N_UNIT_LIB} library checks (cleaning, features, label mapping, Firefly decoding, "
           f"save and load) and {F.N_UNIT_API} API edge cases (word-count rule, oversized or malformed CSV, parameter ranges, non-English text). The interface was exercised in a browser "
           f"and the screens of Section IV are captures of it. The server needs {L['predict_server_ms']['mean']:.1f} ms on average per article and scores {F.NTEST:,} statements in "
           f"{L['batch']['2296']['server_s']:.1f} s (idle machine, local requests).")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** All scores are on the {F.NTEST:,} official LIAR2 test statements, never used for fitting, for three seeds (mean ± standard deviation), on the CPU "
           f"described in Section I. Table II lists accuracy, macro-F1 and training time. The proposed pipeline reaches macro-F1 {F.pm(PT)} and accuracy {F.pm(PT, 'accuracy')} "
           f"(validation split: {F.pm(A['proposed_valid'])} and {F.pm(A['proposed_valid'], 'accuracy')}).")

    def tt(blk):
        return f"{blk['mean']:.2f} s"
    P.table("Test results on LIAR2 (3 classes, mean of 3 seeds)", ["Model", "Accuracy", "Macro-F1", "Train time"], [
        ["Always FAKE", f"{A['majority_test']['accuracy']['mean']:.3f}", f"{A['majority_test']['f1_macro']['mean']:.3f}", "-"],
        ["Compl. NB, TF-IDF, all data", f"{A['ref_full_ComplementNB_test']['accuracy']['mean']:.3f}", f"{A['ref_full_ComplementNB_test']['f1_macro']['mean']:.3f}", tt(A["ref_full_ComplementNB_time"])],
        ["Linear SVM, TF-IDF, all data", f"{A['ref_full_LinearSVC_test']['accuracy']['mean']:.3f}", f"{A['ref_full_LinearSVC_test']['f1_macro']['mean']:.3f}", tt(A["ref_full_LinearSVC_time"])],
        ["Log. regression, TF-IDF, all data", f"{A['ref_full_LogisticRegression_test']['accuracy']['mean']:.3f}", f"{A['ref_full_LogisticRegression_test']['f1_macro']['mean']:.3f}", tt(A["ref_full_LogisticRegression_time"])],
        [f"Log. regression, TF-IDF, {F.NTRAIN:,}", f"{F.pm(A['ref_subsample_LogisticRegression_test'], 'accuracy')}", f"{F.pm(A['ref_subsample_LogisticRegression_test'])}", "-"],
        ["PCA + default RBF SVM", F.pm(A["pca_svc_default_test"], "accuracy"), F.pm(A["pca_svc_default_test"]), tt(A["baseline_time_s"]) + " (fit only)"],
        ["PCA + Firefly mask only", F.pm(A["pca_svc_mask_only_test"], "accuracy"), F.pm(A["pca_svc_mask_only_test"]), "-"],
        ["PCA + random search (equal budget)", F.pm(A["random_search_test"], "accuracy"), F.pm(A["random_search_test"]), f"{A['random_search_time_s']['mean']:.0f} s"],
        ["**PCA + Firefly + MSVM**", F.pm(PT, "accuracy"), F.pm(PT), f"{A['train_time_s']['mean']:.0f} s"],
        ["Shipped demo model (synthetic)", f"{A['demo_model_on_liar2_test']['accuracy']:.3f}", f"{A['demo_model_on_liar2_test']['f1_macro']:.3f}", "-"],
    ], widths=[1.35, 0.78, 0.78, 0.49], size=6.5, align=["l", "c", "c", "c"])
    P.para(f"**What the numbers say.** The three PCA-based variants are within about one standard deviation of each other (Table II): Firefly {F.pm(PT)}, random search "
           f"{F.pm(A['random_search_test'])}, default SVM {F.pm(A['pca_svc_default_test'])}. On the training split the Firefly fitness is slightly higher than the best random-search fitness "
           f"({A['firefly_fitness_best']['mean']:.3f} against {A['random_fitness_best']['mean']:.3f}), but this does not carry to the test split. Plain TF-IDF linear models are better and "
           f"far cheaper: logistic regression on all statements scores {A['ref_full_LogisticRegression_test']['f1_macro']['mean']:.3f} in {A['ref_full_LogisticRegression_time']['mean']:.1f} s, against about "
           f"{A['train_time_s']['mean']:.0f} s for the Firefly pipeline. PCA is capped at {A['n_pca']['mean']:.0f} components and keeps only {A['pca_variance']['mean'] * 100:.0f} % of the variance of "
           f"the standardised features; Firefly keeps {A['n_selected']['mean']:.0f} ± {A['n_selected']['std']:.0f} of them. The synthetic-data model, whose own hold-out score is "
           f"{F.DEMO['f1_macro']:.3f}, falls to {A['demo_model_on_liar2_test']['f1_macro']:.3f} macro-F1 on real statements and answers PARTIALLY TRUE for "
           f"{A['demo_model_prediction_counts'][1]:,} of {F.NTEST:,}.")
    P.para(f"**Hold-out versus test.** The Analytics screen reports the score of the model on a 20 % hold-out of its own training subsample ({A['internal_holdout_acc']['mean'] * 100:.1f} % accuracy, "
           f"macro-F1 {A['internal_holdout_f1']['mean']:.3f} ± {A['internal_holdout_f1']['std']:.3f}); the official test split gives {F.pm(PT)}, so the in-application figure is a fair "
           "estimate here, unlike the 1.000 that the demonstration model shows for its synthetic data.")
    P.para(f"**Data size and simple models.** With the same {F.NTRAIN:,} statements, logistic regression on TF-IDF scores {F.pm(A['ref_subsample_LogisticRegression_test'])}, above the proposed "
           f"pipeline; trained on all statements it reaches {A['ref_full_LogisticRegression_test']['f1_macro']['mean']:.3f}. More data therefore helps a linear model by "
           f"{(A['ref_full_LogisticRegression_test']['f1_macro']['mean'] - A['ref_subsample_LogisticRegression_test']['f1_macro']['mean']):.3f} macro-F1, which suggests that the "
           "3,000-statement budget of the Firefly pipeline, not only its design, limits it. The Firefly pipeline was not run on all statements.")
    P.figure(figs["results"], "(a) Test macro-F1 of the proposed pipeline and its comparisons; (b) accuracy of the proposed pipeline by confidence bin.", width=3.2)
    P.para(f"**Per class.** FAKE is the easiest class (F1 {pc['FAKE']['f1-score']['mean']:.2f}, precision {pc['FAKE']['precision']['mean']:.2f}), REAL is middling "
           f"({pc['REAL']['f1-score']['mean']:.2f}) and PARTIALLY TRUE is the hardest ({pc['PARTIALLY TRUE']['f1-score']['mean']:.2f}, precision {pc['PARTIALLY TRUE']['precision']['mean']:.2f}): "
           "half-true claims have no distinctive wording and are spread over the other classes. Accuracy falls slowly with statement length, from "
           f"{ea['by_length'][0]['accuracy']:.2f} for under 10 words to {ea['by_length'][-1]['accuracy']:.2f} for 30 words or more. Confidence is informative (Fig. 3b): accuracy is "
           f"{ea['by_confidence'][1]['accuracy']:.2f} when the top probability is 0.4-0.5 and {ea['by_confidence'][3]['accuracy']:.2f} at 0.6-0.7.")
    P.para(f"**Verdict versus probability.** The verdict comes from the SVM decision function and the probabilities from Platt scaling, and they disagree: on {lv['disagree_n']:,} of {F.NTEST:,} "
           f"statements ({lv['disagree_rate'] * 100:.1f} %, seed 42) the verdict is not the most probable class, because the probabilities almost always favour FAKE ({lv['argmax_counts'][2]:,} statements) "
           f"and never PARTIALLY TRUE. Fig. 4 shows the Detect screen; for the PARTIALLY TRUE example captured the same way, the verdict was PARTIALLY TRUE at a displayed 47.2 % while the FAKE bar was the tallest, because the "
           "interface reports the largest probability as confidence, which can belong to a different class from the verdict. Using the most probable class as the verdict instead would give "
           f"accuracy {lv['acc_if_argmax']:.3f} but macro-F1 {lv['f1_if_argmax']:.3f}.")
    P.figure(figs["detect"], "Output screen (Detect): a real test statement scored FAKE with class probabilities and cue words, from the model trained on LIAR2.", width=3.1)
    P.para("**Failure cases.** A FAKE-labelled test statement about the signers of the Declaration of Independence is read as REAL with 53.4 % confidence, and a REAL-labelled one about "
           "a public figure's degree is read as FAKE with 72.8 % probability: the model sees wording, not facts, and cannot check a claim against evidence. Because it uses text alone, its "
           "verdicts are screening aids, not fact-checks.")
    P.figure(figs["firefly"], "(a) Best fitness per Firefly generation for each seed; (b) test confusion matrix of seed 42 (R: REAL, P: PARTIALLY TRUE, F: FAKE).", width=3.4)
    f_v = A["proposed_test"]["f1_macro"]["values"]
    d_v = A["pca_svc_default_test"]["f1_macro"]["values"]
    r_v = A["random_search_test"]["f1_macro"]["values"]
    P.para("**Optimiser behaviour.** The search converges within about five generations (Fig. 5a) and then stalls, so most of its 12 generations add nothing. Per seed (" +
           ", ".join(str(sd) for sd in F.SEEDS) + f") the test macro-F1 of Firefly is {', '.join(f'{x:.3f}' for x in f_v)}, of the default SVM {', '.join(f'{x:.3f}' for x in d_v)} and of random search "
           f"{', '.join(f'{x:.3f}' for x in r_v)}; the order changes from seed to seed, which is what 'within noise' means here. Plausible reasons, none of which was tested, are that three-fold "
           "cross-validation on about 2,400 statements is noisy at the level of ±0.01 F1, that the fitness surface is flat for C and gamma near their useful range, and that a mask over 300 "
           "components of a projection that keeps 29 % of the variance has little signal to select. Confusions (Fig. 5b) run mostly between neighbouring grades: "
           f"{ea['pairs']['FAKE -> REAL']} FAKE statements read as REAL and {ea['pairs']['REAL -> FAKE']} REAL read as FAKE in seed 42, and {ea['pairs']['PARTIALLY TRUE -> FAKE'] + ea['pairs']['PARTIALLY TRUE -> REAL']} "
           f"of {F.A['test_class_counts'][1]} PARTIALLY TRUE statements fall into the other two classes.")
    P.para(f"**Speed and use.** With the machine idle, a single prediction takes {L['predict_server_ms']['mean']:.1f} ms in the server (95th percentile {L['predict_server_ms']['p95']:.1f} ms) and "
           f"{L['predict_client_ms']['mean']:.1f} ms round trip including HTTP (95th percentile {L['predict_client_ms']['p95']:.1f} ms); a batch of 1,000 statements takes {L['batch']['1000']['server_s']:.2f} s and "
           f"the whole test split {L['batch']['2296']['server_s']:.1f} s; the service starts in {L['startup_s']:.0f} s. The Retrain screen was exercised end to end on a 600-statement CSV with "
           "4 fireflies and 3 generations: it finished in 199 s and reported accuracy 42.5 % and macro-F1 0.411, a reminder that the cost scales with the search settings and that very small "
           "training sets give weaker models. All of these figures are for local, sequential requests; concurrency was not tested.")
    P.figure(figs["analytics"], "Output screen (Model analytics): confusion matrix and Firefly curve of the model trained on LIAR2 (hold-out of its own training subsample).", width=3.4)
    P.para("**Comparison with the base paper.** The base paper's 95.52 % accuracy and 96.19 % F1 {r:1} are not comparable with these numbers. It classifies Arabic articles into two classes with "
           "CAMeLBERT embeddings on a GPU, whereas this project classifies short English statements into three classes with classical features on a CPU, on a dataset where even "
           "binary classifiers score F1 of about 0.56-0.57 {r:2}. The two results show different tasks, not a better or worse method. The project did reproduce the base paper's practice of "
           "weighting classes and comparing with baselines.")
    P.para("**Threats to validity.** The data are political statements from one fact-checking organisation, so the results say nothing about other genres or languages. The three seeds share the "
           "same test split, so the standard deviations measure training variation, not test-sample variation; with 2,296 statements a binomial interval on accuracy is about ±2 points. Label "
           "mapping is a modelling choice: barely-true is counted as FAKE, as in the project's loader, and a different mapping would change every score. Finally, scores were not tuned on the "
           "test split, but the Firefly and random searches shared one fitness function, which favours neither.")
    P.para("**Limits.** Training used 3,000 of 18,369 statements for compute reasons; three seeds were run and no significance test was made; Firefly's own parameters were not tuned; stemming, "
           "listed among the project's preprocessing aims, is not implemented; no other dataset, user study or load test was run; and a CSV label column that holds only the words true and false "
           "is parsed as booleans and mislabelled by the loader.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"The system was built and measured: a PCA, Firefly and MSVM pipeline with a PARTIALLY TRUE class, behind a web application, with {F.N_TESTS} automated checks passing. On LIAR2 it reaches "
           f"macro-F1 {F.pm(PT)} and accuracy {F.pm(PT, 'accuracy')}, well above always answering FAKE on macro-F1 but below a TF-IDF logistic regression ({A['ref_full_LogisticRegression_test']['f1_macro']['mean']:.3f}). "
           "Against the objectives: the dataset, preprocessing (without stemming), PCA, Firefly selection, MSVM training and evaluation against an unoptimised baseline were done; the claimed "
           "improvement in accuracy and cost was not achieved on this data, since the Firefly search matched random search and the default SVM within noise at far higher training cost.")
    P.para("The main finding is that the optimiser's benefit is not demonstrated, that PARTIALLY TRUE is hard to recognise from wording alone, and that confidence is only partly reliable because verdict "
           "and probabilities come from different mechanisms. Future work: calibrate the probabilities on class-weighted data; keep more PCA variance or skip standardising sparse TF-IDF; tune the "
           "Firefly parameters and train on all statements; add evidence retrieval; and test on further datasets and with users. Until such work shows a gain, the simpler linear baseline is the "
           "better engineering choice on this data, and the application's value lies in its packaging, explanations and honest analytics rather than in the optimiser.")

    P.references()
    P.save(path)
    return path, P.order


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    path, order = build(out)
    print(path, "refs:", len(order), order)
