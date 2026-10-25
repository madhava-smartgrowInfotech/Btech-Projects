"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for SecurePay AI from facts.py (experiments/*.json), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper
from .refs import KEYS

pct, f2, f3 = F.pct, F.f2, F.f3

# references cited by the paper, in the order they are first cited (base paper is always [1])
USED = ["base"]


def R(*keys):
    """{r:..} marker; Paper.expand renumbers by first citation."""
    return "{r:" + ",".join(str(KEYS[k]) for k in keys) + "}"


def make_figures():
    """Compact figures for the paper, written to docs/figures/paper_*.png."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 12})
    NAVY, BLUE, TEAL, ORANGE, RED, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#C0392B", "#6B5BD2", "#7A8CA5"
    S, B = F.SAVED, F.BASE_BAL
    out = {}
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.8, 5.9), gridspec_kw={"hspace": 0.95})
    # (a) F1 and recall: RBM trainers (5-seed mean +/- sd, final epoch) and baselines (single split)
    names = ["PCD", "SAS", "QS", "LR", "RF", "XGB"]
    f1 = [F.SEEDS["classical"]["f1"]["mean"], F.SEEDS["sa"]["f1"]["mean"], F.SEEDS["qa"]["f1"]["mean"],
          B["Logistic Regression"]["f1"], B["Random Forest"]["f1"], B["XGBoost"]["f1"]]
    sd = [F.SEEDS["classical"]["f1"]["std"], F.SEEDS["sa"]["f1"]["std"], F.SEEDS["qa"]["f1"]["std"], 0, 0, 0]
    rc = [F.SEEDS["classical"]["recall"]["mean"], F.SEEDS["sa"]["recall"]["mean"], F.SEEDS["qa"]["recall"]["mean"],
          B["Logistic Regression"]["recall"], B["Random Forest"]["recall"], B["XGBoost"]["recall"]]
    x = np.arange(len(names))
    b1 = a.bar(x - 0.2, f1, 0.4, yerr=sd, color=[BLUE, ORANGE, PURPLE, GREY, GREY, GREY], capsize=3, label="F1")
    b2 = a.bar(x + 0.2, rc, 0.4, color=[BLUE, ORANGE, PURPLE, GREY, GREY, GREY], alpha=0.45, hatch="//", label="recall")
    for bars in (b1, b2):
        for bb in bars:
            a.text(bb.get_x() + bb.get_width() / 2, 0.03, f"{bb.get_height() * 100:.0f}", ha="center", fontsize=10, color="white", fontweight="bold")
    a.set_xticks(x)
    a.set_xticklabels(names, fontsize=11)
    a.set_ylim(0, 1.3)
    a.set_ylabel("score (test split)")
    a.legend(frameon=False, fontsize=10, loc="upper right", ncol=2)
    a.set_title("(a) Final-epoch F1 (solid, mean ± sd over 5 seeds) and recall (hatched)", fontsize=11)
    a.spines[["top", "right"]].set_visible(False)
    # (b) 1% fraud: precision and recall
    sel = [("LR", "Logistic Regression", "none"), ("XGB", "XGBoost", "none"), ("XGB\nSMOTE", "XGBoost", "SMOTE"),
           ("LR\nunder", "Logistic Regression", "undersample"), ("XGB\nunder", "XGBoost", "undersample"), ("RBM-SA\nunder", "GRBMC (SA)", "undersample")]
    xs = np.arange(len(sel))
    pr = [F.imb_row(m, s)["precision"]["mean"] for _, m, s in sel]
    re = [F.imb_row(m, s)["recall"]["mean"] for _, m, s in sel]
    c1 = b.bar(xs - 0.2, pr, 0.4, color=TEAL, label="precision")
    c2 = b.bar(xs + 0.2, re, 0.4, color=ORANGE, label="recall")
    for bars in (c1, c2):
        for bb in bars:
            b.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 0.015, f"{bb.get_height():.2f}", ha="center", fontsize=9.5)
    b.set_xticks(xs)
    b.set_xticklabels([n for n, _, _ in sel], fontsize=10)
    b.set_ylim(0, 1.4)
    b.set_ylabel("score (threshold 0.5)")
    b.legend(frameon=False, fontsize=10, loc="upper right", ncol=2)
    b.set_title("(b) 1 % fraud variant, mean of 5 seeds (78 fraud per test set)", fontsize=11)
    b.spines[["top", "right"]].set_visible(False)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    out["results"] = p

    # Fig. 2: compact scoring flow
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(6.8, 3.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis("off")

    def bx(cx, cy, w, h, txt, fc, ec=None, ls="-", tc="white", fs=9.5):
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.5", fc=fc, ec=ec or fc, lw=1.6, ls=ls, zorder=2))
        ax.text(cx, cy, txt, ha="center", va="center", color=tc, fontsize=fs, zorder=3, linespacing=1.2)

    def ar(p1, p2, col=NAVY, ls="-", rad=0.0):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13, color=col, lw=1.5, ls=ls, connectionstyle=f"arc3,rad={rad}", zorder=1))

    w, h = 23, 13
    xs4 = [12.5, 37.5, 62.5, 87.5]
    top = [("JSON fields\nor CSV rows", BLUE), ("Fill missing fields\n(mean or mode)", BLUE), ("One-hot encode\nmerchant, channel", TEAL), (None, None)]
    for x, (t, c) in zip(xs4, top):
        if t:
            bx(x, 40, w, h, t, c)
    bx(87.5, 40, w, h, "Scale 24 numeric\ncolumns (step fails,\nsilently skipped)", "white", ec=ORANGE, ls="--", tc=ORANGE, fs=9.5)
    for a_, b_ in zip(xs4[:-1], xs4[1:]):
        ar((a_ + w / 2, 40), (b_ - w / 2, 40))
    bot = [("Select the 18\ntraining columns", TEAL), ("PCD, SAS and QS\nfraud probabilities", PURPLE), ("Mean p > 0.5\n: FRAUD label", PURPLE), ("Band: < 0.4 approve\n0.4-0.7 challenge\n> 0.7 decline", ORANGE)]
    for x, (t, c) in zip(xs4, bot):
        bx(x, 12, w, h, t, c)
    for a_, b_ in zip(xs4[:-1], xs4[1:]):
        ar((a_ + w / 2, 12), (b_ - w / 2, 12))
    ar((87.5, 40 - h / 2), (12.5, 12 + h / 2), rad=-0.0)
    ax.text(50, 26.5, "continue with the unscaled values", ha="center", va="bottom", fontsize=10, color=ORANGE, style="italic", bbox=dict(fc="white", ec="none", pad=1))
    p = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    out["flow"] = p

    # Fig. 4: verify result panel (screen 04); Fig. 5: bulk result tiles (screen 05)
    s04 = Image.open(F.shot("04_verify.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_verify.png")
    s04.crop((862, 8, 1422, 480)).save(p)
    out["verify"] = p
    s05 = Image.open(F.shot("05_bulk.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_bulk.png")
    s05.crop((618, 364, 1412, 840)).save(p)
    out["bulk"] = p
    return out


def build(path):
    figs = make_figures()
    S, B, SV, IMB = F.SAVED, F.BASE_BAL, F.SERVING, F.IMB
    pcd, sas, qs, ens = S["classical"], S["sa"], S["qa"], S["ensemble"]
    lat = F.LATENCY
    served, scaled = SV["as_served_no_scaling"]["ensemble"], SV["with_scaling"]["ensemble"]
    lr, rf, xg = B["Logistic Regression"], B["Random Forest"], B["XGBoost"]
    r_lr_n, r_rf_n, r_xg_n = F.imb_row("Logistic Regression", "none"), F.imb_row("Random Forest", "none"), F.imb_row("XGBoost", "none")
    r_lr_u, r_rf_u, r_xg_u = F.imb_row("Logistic Regression", "undersample"), F.imb_row("Random Forest", "undersample"), F.imb_row("XGBoost", "undersample")
    r_xg_s, r_xg_cw = F.imb_row("XGBoost", "SMOTE"), F.imb_row("XGBoost", "class_weight")
    r_rbm = F.imb_row("GRBMC (SA)", "undersample")
    rule = IMB["rule_based"]
    seedsd = lambda m, k: f"{F.SEEDS[m][k]['mean'] * 100:.1f}±{F.SEEDS[m][k]['std'] * 100:.1f}"  # noqa: E731
    lh = lat["predict_single_fraud_example"]
    lb = lat["predict_batch_20_rows"]
    sp = F.SPLIT
    full = F.FULL

    P = Paper()
    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"])
    P.title_block("Credit Card Fraud Detection Using Machine Learning with Quantum-Inspired Restricted Boltzmann Machines", authors)
    P.begin_two_columns()

    P.abstract(
        "Fraud is rare among card transactions, so a classifier can score a high accuracy while finding almost no fraud, and fixed rules are quickly learned and bypassed. "
        "This paper builds and measures SecurePay AI, a fraud-screening application that follows a recent quantum-assisted study by training a Gaussian-Bernoulli restricted Boltzmann machine classifier "
        "three ways: persistent contrastive divergence, simulated-annealing sampling and a quantum-inspired sampler simulated on a CPU. A Flask service and a React interface offer single checks, CSV screening, "
        f"analytics and retraining. On a synthetic, balanced set of {F.DATASET['rows']:,} transactions the three-model ensemble reaches F1 {pct(ens['f1'])} (ROC-AUC {f3(ens['roc_auc'])}), "
        "but the classical model flags nearly every transaction at the default threshold, and logistic regression, random forest and XGBoost score higher on the same split. "
        "Across five seeds the classical trainer is unstable while simulated annealing is steady. At 1 % fraud, undersampling cuts the precision of the baselines to about 0.2. "
        f"A code audit found that the batch route skips feature scaling, which lowers accuracy from {pct(scaled['accuracy'])} to {pct(served['accuracy'])} on a fresh batch. "
        "The data are synthetic, so the figures are not comparable with the base paper's.",
        ["class imbalance", "credit card fraud", "fraud detection", "quantum annealing", "restricted Boltzmann machine", "simulated annealing", "undersampling"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para(f"Fraudulent card transactions are a tiny share of all payments: the dataset behind the base paper holds about 19 thousand fraud cases among 145 million transactions {R('base')}. "
           "Banks have long used fixed rules, which analysts must keep rewriting and which fraudsters learn to avoid, and they now add learned classifiers. Two costs pull in opposite directions: "
           "a missed fraud is a direct loss, while a false alarm blocks a genuine customer and occupies an analyst. Accuracy hides both, because a model that approves everything is almost always right; "
           f"an ANN and XGBoost, for example, both score about 99.96 % accuracy on imbalanced card data and differ only in fraud-class F1 {R('shi')}.")
    P.para(f"The base paper {R('base')} trains a Gaussian-Bernoulli restricted Boltzmann machine classifier (GRBMC) on a 39-thousand-transaction balanced subset and compares classical training with "
           "simulated-annealing and real quantum-annealer sampling. It uses proprietary data, reports no baseline from the usual classifier families, takes hours to train and offers no way to score a live transaction. "
           "Few readers can reproduce it, so it is unclear how much of its behaviour survives on ordinary hardware and how it compares with logistic regression, forests and boosting.")
    P.para("This work closes that gap at student scale. The contributions are: (1) an open NumPy implementation of the GRBMC with three trainers, wrapped in a Flask service and a React interface that scores one transaction "
           "or a CSV file; (2) a measured comparison with logistic regression, random forest and XGBoost, including five-seed stability and a threshold sweep; (3) a study of SMOTE, class weights and undersampling when "
           "fraud falls from 50 % to 1 % of the stream; and (4) an audit of the serving path with the measured cost of the defect found. Section II surveys related work, Section III the method, Section IV the "
           "results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All measurements used one desktop PC: Windows 11 Pro, an Intel Core i5-12500 processor and 15.7 GB of RAM, with no graphics processor. Every model trains on the CPU in NumPy, and the quantum samplers are classical simulations.")
    P.sub("B", "Software Requirements")
    P.para(f"Python 3.11.9 with NumPy 1.26.4, pandas 2.2.1, scikit-learn 1.5.0 {R('sklearn')}, imbalanced-learn 0.12.4 {R('imblearn')}, XGBoost 2.0.3 {R('xgb')} and Matplotlib 3.9.0; "
           "Flask 3.1.0 with Flask-CORS for the API; React 19 and Vite 8 with Recharts for the browser interface.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Neto et al. {R('base')} work with 145 million anonymised card transactions from a Brazilian fintech, about 19 thousand of them fraud. Categorical fields are one-hot encoded, numeric fields "
           "z-scored, highly correlated columns removed and the remainder ranked with CatBoost. SMOTE, Tomek links and their combinations failed because the minority class was so small, so the authors undersampled "
           "by hand to 39 thousand transactions, split 50/50 between classes and 80/20 into training and test sets. A GRBMC, in which the label units extend the visible layer, was trained for 50 epochs three ways: classical "
           "persistent contrastive divergence (200 hidden units, batch 512), simulated-annealing-assisted training on a D-Wave simulator and quantum sampling on D-Wave hardware (both 65 hidden units, batch 32). "
           "At the best epoch they report accuracy, precision, recall and F1 of 84, 86, 81 and 83 % (PCD, 2 minutes), 85, 94, 82 and 88 % (SAS, 4 hours) and 85, 91, 79 and 84 % (QS, 1.8 hours). "
           "The authors say that it remains open whether the advantage is general or specific to their data.")
    P.para(f"**Classifiers and ensembles.** Early comparisons found nonlinear ensembles stronger than linear models on card data {R('bhatt')}. A tuned random forest {R('breiman')} trained on SMOTE-balanced data "
           f"reached about 98 % accuracy and F1 on 94,682 transactions {R('rfpaper')}, and gradient boosting {R('xgb')} is a standard strong baseline. On the harder IEEE-CIS benchmark (3.5 % fraud) the best fusion of "
           f"random forest, XGBoost and LightGBM gives AUC 0.9405, AUPRC 0.6699 and F1 0.6373, and synthetic CTGAN fraud samples made results worse {R('cfa')}.")
    P.para(f"**Imbalance and evaluation.** SMOTE interpolates new minority points {R('smote')}; undersampling distorts posterior probabilities unless they are recalibrated {R('dp15')}; and precision-recall curves "
           f"are more informative than ROC curves when positives are rare {R('saito')}. Realistic fraud work also has to cope with delayed labels and changing patterns {R('dp18')}, and supervised classifiers "
           f"gain from unsupervised anomaly scores {R('carcillo')}.")
    P.para(f"**Boltzmann machines.** An RBM is trained by contrastive divergence {R('cd')}, in its persistent form {R('pcd')}, and can classify directly when the label is part of the visible layer {R('larochelle')}; "
           f"Gaussian visible units handle continuous inputs {R('liao')}. Simulated annealing {R('anneal')} supplies the cooling schedule used to replace Gibbs sampling in the annealing-assisted variants.")
    P.table("Representative related work",
            ["Work", "Approach", "Data", "Reported result", "Limitation"], [
                [R("base"), "GRBMC; PCD, SA, quantum sampling", "145 M real, 39 k balanced", "F1 83 / 88 / 84 %", "Private data; hours; no UI"],
                [R("rfpaper"), "Random forest + SMOTE", "94,682 online txns", "Acc., F1 about 98 %", "Resampled, accuracy-led"],
                [R("cfa"), "Fusion of 7 classifiers", "IEEE-CIS, 590,540", "AUPRC 0.670, F1 0.637", "Small gain; CTGAN hurt"],
                [R("shi"), "ANN vs XGBoost", "Imbalanced card data", "Both about 99.96 % acc.", "Accuracy uninformative"],
                [R("bhatt"), "LR, SVM, forest", "Real card data", "Ensembles stronger", "Old; no deployment"],
                [R("carcillo"), "Unsupervised + supervised", "Large real stream", "Scores complement", "Not one compact model"],
            ], widths=[0.3, 0.9, 0.78, 0.77, 0.65], size=7, align=["c", "l", "l", "l", "l"])
    P.para(f"**Reading the base paper critically.** Its strengths are the scale and realism of the data, access to annealing hardware and a systematic search over hidden units and learning-rate schedules. "
           "Its limits are equally clear from the text: results are given for one proprietary dataset and four metrics at the best of 50 epochs, chosen on the test split; metrics for several quantum-annealing epochs were "
           "unavailable because access to the hardware was limited; simulated annealing used only a few sweeps and oscillated strongly; the 4-hour simulated-annealing time is attributed partly to Julia-to-Python overhead on Windows; "
           "and no non-RBM classifier was trained for comparison. The authors themselves leave open whether the advantage is general. These are the points this project sets out to test on open, reproducible data.")
    P.para("**Gap.** The work surveyed studies classifiers and sampling methods separately, scores accuracy more than fraud-class recall, and stops at a notebook. No source tests whether the base paper's "
           "quantum-assisted GRBMC holds up against standard baselines on reproducible data, how it behaves at realistic imbalance, or whether it can sit behind a live scoring interface.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows four tiers. A React single-page application calls a Flask service through a Vite proxy; the service imports plain Python modules for preprocessing, the GRBMC, "
           "the samplers, training and evaluation; and all state is kept in local files (a CSV, a pickled pipeline, three pickled models and their histories). There is no SQL database, no login and "
           "no external call.")
    P.figure(F.diag("01_system_architecture.png"), "SecurePay AI architecture: browser tier, Flask API, model modules and file storage.")
    P.para(f"**Data.** The file `creditcard_synthetic.csv` has {F.DATASET['rows']:,} rows, half fraud, generated by the project (fixed seed). Fraud draws larger amounts "
           f"(mean {F.DATASET['amount_mean_fraud']:.0f} against {F.DATASET['amount_mean_legit']:.0f}), more online and card-not-present use, more country mismatches and shifted anonymised features V3, V7, V10, V14 and V17 (Table II). "
           "It imitates the size and balance of the base paper's subset but is not real data. The backend builds its pipeline from an 8,000-row sample: one-hot encoding of merchant category and channel, z-scoring of 24 numeric "
           "columns, a correlation filter at 0.95 (which removes nothing), random-forest importance ranking (CatBoost is not installed, so this replaces it) keeping the top 18 features, and a stratified 80/20 split "
           f"into {sp['train'][0]:,} training and {sp['test'][0]:,} test rows ({sp['test_fraud']} fraud). Balancing happens before the split, so selection saw the test rows.")
    import pandas as pd
    dfc = pd.read_csv(os.path.join(F.CODE, "data", "creditcard_synthetic.csv"))
    g0, g1 = dfc[dfc.Class == 0], dfc[dfc.Class == 1]
    P.table("Dataset statistics by class (all 39,000 rows)", ["Property", "Legitimate", "Fraud"], [
        ["Rows", f"{len(g0):,}", f"{len(g1):,}"],
        ["Mean amount", f"{g0.Amount.mean():.1f}", f"{g1.Amount.mean():.1f}"],
        ["Median amount", f"{g0.Amount.median():.1f}", f"{g1.Amount.median():.1f}"],
        ["Card present", pct((g0.Card_Present == 1).mean()), pct((g1.Card_Present == 1).mean())],
        ["Country matches card", pct((g0.Country_Match == 1).mean()), pct((g1.Country_Match == 1).mean())],
        ["Online channel", pct((g0.Transaction_Type == "Online").mean()), pct((g1.Transaction_Type == "Online").mean())],
        ["Mean of V3 / V17", f"{g0.V3.mean():.2f} / {g0.V17.mean():.2f}", f"{g1.V3.mean():.2f} / {g1.V17.mean():.2f}"],
        ["Mean of V7 / V14", f"{g0.V7.mean():.2f} / {g0.V14.mean():.2f}", f"{g1.V7.mean():.2f} / {g1.V14.mean():.2f}"],
    ], widths=[1.4, 1.0, 1.0], size=7, align=["l", "c", "c"])
    P.para("**Model.** With unit variance the GRBMC energy of visible vector v (continuous), hidden vector h (binary) and label y (one-hot) is")
    P.eq("E(v,h,y) = ½ Σ (v_i − c_i)² − Σ b_j h_j − Σ v_i W_ij h_j − Σ d_k y_k − Σ y_k U_kj h_j.")
    P.para("Because the visible bias term is the same for both labels, the class posterior used for prediction reduces to the free energy of the two label hypotheses,", indent=0)
    P.eq("p(y|v) ∝ exp( d_y + Σ_j log(1 + exp(b_j + Σ_i v_i W_ij + U_yj)) ).")
    P.para("The update of every weight is the learning rate times the difference between the data correlation and the model correlation of the two units it connects, and the trainers differ only in how the model term is sampled: "
           "**PCD** runs one persistent Gibbs step with 200 hidden units and batch 512; **SAS** (Table III) anneals a population of 16 binary samples through 10 sweeps with inverse temperature rising from 0.5 to 10, "
           "computing the hidden field from the batch-mean visible vector; **QS** follows the same plan but replaces the temperature by a schedule A(s) = 0.8(1 − s), B(s) = s and flips each hidden unit at random "
           "with probability 0.3 A(s), imitating a transverse field. SAS and QS use 65 hidden units, batch 32 and a random 3,000-row subsample per epoch. These are simplified classical stand-ins for the base paper's "
           "path-integral simulator and quantum hardware, not reproductions. Learning rates decay as 0.01·exp(−0.08 t) for PCD and SAS and as 0.005·exp(−0.15 t) + 0.0005 for QS over 20 epochs. "
           "The ensemble averages the three fraud probabilities, labels fraud above 0.5 and assigns the risk bands LOW (below 0.4, approve), MEDIUM (0.4 to 0.7, challenge) and HIGH (above 0.7, decline and alert). Fig. 2 traces one scoring request.")
    P.table("Settings of the three GRBMC trainers",
            ["Trainer", "Hidden / batch", "Model-phase sampler", "Learning rate", "Rows per epoch"], [
                ["PCD", "200 / 512", "One persistent Gibbs step", "0.01·exp(−0.08 t)", f"all {sp['train'][0]:,}"],
                ["SAS", "65 / 32", "10 sweeps, 16 reads, β 0.5 to 10", "0.01·exp(−0.08 t)", "3,000 random"],
                ["QS", "65 / 32", "10 sweeps, 16 reads, tunnelling flips", "0.005·exp(−0.15 t) + 0.0005", "3,000 random"],
            ], widths=[0.45, 0.62, 1.05, 0.83, 0.45], size=7, align=["l", "c", "l", "l", "c"])
    P.figure(figs["flow"], "Scoring flow of the API. The dashed scaler step raises an exception on the selected columns and is silently skipped.")
    P.para("**Serving.** Sixteen routes cover health, dataset and analytics, preprocessing, training, history, comparison, the QUBO matrix of each model, single and batch prediction and CSV export. "
           "Missing fields default to the dataset mean or mode, and any exception returns a JSON error with HTTP 500. The interface has a dashboard, a verify form, CSV bulk screening, four analytics tabs, "
           "a model-comparison page and a retraining lab.")
    P.para("**Metrics.** With TP, FP and FN the true positives, false positives and false negatives for the fraud class, precision is TP/(TP+FP), recall is TP/(TP+FN) and F1 is their harmonic mean. "
           f"ROC-AUC measures ranking over all thresholds and is unaffected by the threshold problem of PCD; average precision (PR-AUC) is reported for the 1 % study because precision-recall curves are more informative for rare positives {R('saito')}.")
    P.para(f"**Evaluation protocol.** Primary figures are final-epoch precision, recall, F1 and ROC-AUC at threshold 0.5 on the {sp['test'][0]:,}-row test split; the per-epoch best, which the interface also shows, "
           "is chosen on the test split and is therefore optimistic. Logistic regression, a 100-tree random forest and XGBoost (200 trees, depth 4) are trained on the same split. Stability uses five seeds; "
           "the imbalance study draws a 39,000-row set with 1 % fraud, splits it stratified into 31,200 and 7,800 rows (78 fraud in the test set), fits the scaler on training data only and resamples the training part only. "
           "A 20-check smoke test and an HTTP timing run exercise the running API. Every number in this paper is regenerated by `run_experiments.py`, `measure_latency.py` and `smoke_test.py` from fixed seeds, "
           "so a reader with the repository can repeat the study in under an hour on a CPU-only PC.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.table("Test-split results at threshold 0.5 (%)",
            ["Model", "Acc.", "Prec.", "Rec.", "F1", "AUC", "F1, 5 seeds"], [
                ["PCD", f"{pcd['accuracy'] * 100:.1f}", f"{pcd['precision'] * 100:.1f}", f"{pcd['recall'] * 100:.1f}", f"{pcd['f1'] * 100:.1f}", f3(pcd['roc_auc']), seedsd("classical", "f1")],
                ["SAS", f"{sas['accuracy'] * 100:.1f}", f"{sas['precision'] * 100:.1f}", f"{sas['recall'] * 100:.1f}", f"{sas['f1'] * 100:.1f}", f3(sas['roc_auc']), seedsd("sa", "f1")],
                ["QS", f"{qs['accuracy'] * 100:.1f}", f"{qs['precision'] * 100:.1f}", f"{qs['recall'] * 100:.1f}", f"{qs['f1'] * 100:.1f}", f3(qs['roc_auc']), seedsd("qa", "f1")],
                ["Ensemble", f"{ens['accuracy'] * 100:.1f}", f"{ens['precision'] * 100:.1f}", f"{ens['recall'] * 100:.1f}", f"{ens['f1'] * 100:.1f}", f3(ens['roc_auc']), "-"],
                ["Log. reg.", f"{lr['accuracy'] * 100:.1f}", f"{lr['precision'] * 100:.1f}", f"{lr['recall'] * 100:.1f}", f"{lr['f1'] * 100:.1f}", f3(lr['roc_auc']), "-"],
                ["Rand. forest", f"{rf['accuracy'] * 100:.1f}", f"{rf['precision'] * 100:.1f}", f"{rf['recall'] * 100:.1f}", f"{rf['f1'] * 100:.1f}", f3(rf['roc_auc']), "-"],
                ["XGBoost", f"{xg['accuracy'] * 100:.1f}", f"{xg['precision'] * 100:.1f}", f"{xg['recall'] * 100:.1f}", f"{xg['f1'] * 100:.1f}", f3(xg['roc_auc']), "-"],
            ], widths=[0.68, 0.38, 0.4, 0.38, 0.38, 0.4, 0.78], size=7, align=["l", "c", "c", "c", "c", "c", "c"])
    P.para(f"**Test conditions.** Shipped models and baselines are scored on the same {sp['test'][0]:,} held-out rows ({sp['test_fraud']} fraud) of the synthetic set; the five-seed column retrains each GRBMC for "
           "20 epochs and reports the final epoch (mean ± sd). Training takes about 4 to 5 s per model on this PC, and 19 s for PCD on the full file.")
    P.para(f"**Model comparison.** SAS and QS reach F1 {pct(sas['f1'])} and {pct(qs['f1'])}, and averaging all three gives {pct(ens['f1'])} with ROC-AUC {f3(ens['roc_auc'])} (Table IV). "
           f"The shipped PCD model has the same AUC ({f3(pcd['roc_auc'])}) but at threshold 0.5 it labels {pcd['fp']} of {pcd['tn'] + pcd['fp']} genuine transactions as fraud: its ranking is good and its probabilities are not "
           f"calibrated, and moving the threshold changes the picture completely (Fig. 3a shows five retrainings, F1 {seedsd('classical', 'f1')} for PCD against {seedsd('sa', 'f1')} for SAS). "
           f"Logistic regression, random forest and XGBoost reach F1 {pct(lr['f1'])}, {pct(rf['f1'])} and {pct(xg['f1'])}; on the whole 39,000-row file they reach {pct(full['Logistic Regression']['f1'])}, "
           f"{pct(full['Random Forest']['f1'])} and {pct(full['XGBoost']['f1'])} against {pct(full['sa']['f1'])} for SAS. On this synthetic data the simple baselines are better, faster to fit (under a second) and stable.")
    sw = {r["threshold"]: r for r in S["ensemble_threshold_sweep"]}
    P.para(f"**Threshold.** Sweeping the ensemble threshold shows how narrow the useful range is. At 0.4 precision is {f2(sw[0.4]['precision'])} and recall {f2(sw[0.4]['recall'])} ({sw[0.4]['fp']} false positives); "
           f"at 0.5 they are {f2(sw[0.5]['precision'])} and {f2(sw[0.5]['recall'])}; at 0.6 precision is {f2(sw[0.6]['precision'])} but recall falls to {f2(sw[0.6]['recall'])}; and at 0.7 nothing is flagged. "
           "No test transaction therefore reaches the HIGH band, so in practice the application can only approve or challenge on this data, and the 40 % and 70 % bands were not tuned to the model's output range.")
    imp = B["Random Forest"]["top_importances"]
    P.para("**What the models use.** The random forest ranks " + ", ".join(f"{n.replace('Transaction_Type_', 'channel ').replace('_', ' ')} ({v:.2f})" for n, v in imp[:6]) +
           " highest, matching the way the data were generated: large amounts, card-not-present use, country mismatch and a few shifted anonymised features. "
           f"Only {sum(1 for v in S['histories']['sa']['f1'] if v > 0.9)} of the 20 saved SAS epochs and {sum(1 for v in S['histories']['qa']['f1'] if v > 0.9)} of the 20 QS epochs exceed F1 0.9, "
           "so a model saved at an arbitrary epoch can be far from the best one; the five-seed figures use the last epoch for that reason. "
           f"The saved histories report training times of {S['histories']['classical']['elapsed_sec']:.1f} s (PCD), {S['histories']['sa']['elapsed_sec']:.1f} s (SAS) and {S['histories']['qa']['elapsed_sec']:.1f} s (QS), "
           "where the base paper reports minutes to hours; the difference comes from the 3,000-row subsampling and a heavily simplified sampler, not from faster quantum hardware.")
    P.figure(figs["results"], "Results: (a) F1 and recall of the trainers and baselines; (b) precision and recall when fraud is 1 % of the stream.")
    P.para(f"**Imbalance.** With 1 % fraud (Fig. 3b), unresampled logistic regression gives precision {f2(r_lr_n['precision']['mean'])} and recall {f2(r_lr_n['recall']['mean'])}, XGBoost "
           f"{f2(r_xg_n['precision']['mean'])} and {f2(r_xg_n['recall']['mean'])}. SMOTE lifts XGBoost recall to {f2(r_xg_s['recall']['mean'])} at precision {f2(r_xg_s['precision']['mean'])}, and class weights give "
           f"{f2(r_xg_cw['precision']['mean'])} and {f2(r_xg_cw['recall']['mean'])}. Random undersampling, the base paper's choice, raises recall above 0.95 for all three baselines but drops precision to "
           f"{f2(r_xg_u['precision']['mean'])} to {f2(r_rf_u['precision']['mean'])}, which means about {r_rf_u['mean_fp']:.0f} to {r_xg_u['mean_fp']:.0f} false alarms per 7,800 transactions. The GRBMC trained on the undersampled set keeps precision "
           f"{f2(r_rbm['precision']['mean'])} but recall only {f2(r_rbm['recall']['mean'])} (ROC-AUC {f2(r_rbm['roc_auc']['mean'])}), and a three-signal rule scores F1 {f2(rule['f1']['mean'])}.")
    rows4 = []
    for lab, m_, s_ in [("Log. reg., none", "Logistic Regression", "none"), ("XGBoost, none", "XGBoost", "none"), ("XGBoost, class weights", "XGBoost", "class_weight"),
                        ("XGBoost, SMOTE", "XGBoost", "SMOTE"), ("Log. reg., undersample", "Logistic Regression", "undersample"), ("Rand. forest, undersample", "Random Forest", "undersample"),
                        ("XGBoost, undersample", "XGBoost", "undersample"), ("GRBMC (SAS), undersample", "GRBMC (SA)", "undersample")]:
        r_ = F.imb_row(m_, s_)
        rows4.append([lab, f2(r_["precision"]["mean"]), f2(r_["recall"]["mean"]), f2(r_["f1"]["mean"]), f2(r_["pr_auc"]["mean"]), f"{r_['mean_fp']:.0f}", f"{r_['mean_fn']:.0f}"])
    rows4.append(["Three-signal rule", f2(rule["precision"]["mean"]), f2(rule["recall"]["mean"]), f2(rule["f1"]["mean"]), "-", f"{rule['mean_fp']:.0f}", f"{rule['mean_fn']:.0f}"])
    P.table("Results at 1 % fraud: strategy and model (mean of 5 seeds)", ["Model, strategy", "Prec.", "Rec.", "F1", "PR-AUC", "FP", "FN"], rows4,
            widths=[1.25, 0.38, 0.35, 0.33, 0.45, 0.32, 0.32], size=7, align=["l", "c", "c", "c", "c", "c", "c"])
    P.para("**Why the baselines win here.** The generator shifts a handful of Gaussian features and a few categorical probabilities, so the classes are nearly linearly separable and logistic regression is close to optimal. "
           "A generative RBM spends part of its capacity modelling the inputs and is trained with a noisy gradient estimate, so it is plausible, though not tested here, that it needs real, harder data before any advantage appears. "
           "The gap to the baselines is about two F1 points on the 1,600-row split, larger than the 0.1 to 1.2 point seed spread of SAS and QS, so it is not noise.")
    P.para(f"**Output screens.** Fig. 4 is the verify page after the high-risk example of the user guide (amount 1,200, online, card not present, country mismatch): the models give 50.9 % (PCD), 59.5 % (QS) and 94.7 % (SAS), "
           "the ensemble is 68.4 %, just inside the MEDIUM band, and the page recommends a 3-D Secure challenge. The three models disagree by more than forty points on one transaction, "
           "which is the instability of Section IV seen from the user's side. Fig. 5 is the bulk page after the bundled sample is uploaded: all 20 rows are flagged and the accuracy tile reads 50.0 %, "
           "the signature of the scaling defect rather than of the data, and the page itself warns that every row was flagged.")
    P.figure(figs["verify"], "Verify screen: a high-amount online transaction scored by the three models and the risk meter (the single-check route scales correctly).")
    P.figure(figs["bulk"], "Bulk screen: the bundled 20-row sample, all rows flagged because of the skipped scaling step.")
    P.para(f"**Serving defect.** The bulk route calls the scaler on the 13 selected numeric columns although it was fitted on 24, scikit-learn raises an error and a bare `except` hides it, so models receive unscaled values. "
           f"On a fresh 2,000-row batch the ensemble then reaches accuracy {pct(served['accuracy'])} with {served['fp']} false positives, against {pct(scaled['accuracy'])} and {scaled['fp']} when scaling is applied offline. "
           f"The bundled sample file (10 fraud rows) is flagged {SV['sample_batch_as_served_flagged']} of 20 as served and {SV['sample_batch_scaled_flagged']} when scaled (Fig. 5). The defect was recorded, not fixed.")
    P.table("API latency on 127.0.0.1 (ms)", ["Request", "n", "Median", "95th pct."], [
        [lab, str(lat[k]["n"]), f"{lat[k]['median_ms']:.1f}", f"{lat[k]['p95_ms']:.1f}"] for lab, k in [
            ("Single check, ensemble", "predict_single_fraud_example"), ("Single check, PCD only", "predict_single_classical"),
            ("Single check, SAS only", "predict_single_sa"), ("20-row CSV batch", "predict_batch_20_rows"),
            ("Dataset statistics", "dataset_stats"), ("Health", "health")]
    ], widths=[1.6, 0.4, 0.6, 0.8], size=7, align=["l", "c", "c", "c"])
    P.para(f"**Speed.** A single check takes a median {lh['median_ms']:.0f} ms (95th percentile {lh['p95_ms']:.0f} ms) and a 20-row CSV {lb['median_ms']:.0f} ms on the Flask development server (Table VI), "
           "after five warm-up calls. These timings say nothing about concurrent load.")
    P.para("**Comparison with the base paper.** The base paper's Table 1 gives F1 of 83, 88 and 84 % for PCD, SAS and QS on real data, and 2 minutes, 4 hours and 1.8 hours of training. This project measures "
           f"{pct(pcd['f1'], 0)}, {pct(sas['f1'], 0)} and {pct(qs['f1'], 0)} in seconds on synthetic data whose classes are easy to separate (logistic regression reaches AUC {f3(lr['roc_auc'])}). The datasets, "
           "sample sizes, simulators and epoch selection differ, so the two sets of figures are context for each other and neither supports a claim of improvement or of reproduction.")
    h_sa, h_qs = F.HIST["sa"], F.HIST["qa"]
    z_sa = sum(1 for v in h_sa["f1"] if v < 0.01)
    z_qs = sum(1 for v in h_qs["f1"] if v < 0.01)
    P.para(f"**Failure cases.** Four stand out. The shipped PCD model flags {pcd['fp']} of {pcd['tn'] + pcd['fp']} genuine transactions. Early epochs of SAS and QS collapse to predicting one class "
           f"(F1 of zero in {z_sa} and {z_qs} of 20 epochs of the saved runs), so the epoch at which training stops matters. The HIGH band is unreachable, as shown above. And on bulk uploads, which skip scaling, the ensemble flags "
           f"almost everything. Where the data carry a strong signal the system works: the dataset analytics show that electronics, online and card-not-present transactions have the highest fraud rates, and the random-forest importances point the same way.")
    P.para("**Practical reading.** For an operations team the useful question is not accuracy but how many alerts a fixed analyst budget can absorb. Table V answers it for the 1 % stream: an unresampled "
           "linear model or boosted trees raise a handful of false alarms per 7,800 transactions, whereas undersampling raises hundreds, so the base paper's balancing choice, made necessary there by an "
           "extremely small minority class, is a costly default elsewhere unless probabilities are recalibrated afterwards {r:11}. A deployment would also choose its threshold on a validation set from "
           "the cost of a missed fraud against the cost of a review, which this prototype does not do.")
    P.para("**Threats to validity.** Internal: the threshold (0.5) and the feature count (18) are the product's defaults and were not tuned here, but balancing and feature ranking used all rows of the 8,000-row sample, so the test rows "
           "influenced selection. External: one synthetic generator, one random sample and one machine. Construct: the quantum-inspired samplers approximate nothing quantum, so no statement about quantum advantage follows. "
           "Statistical: five seeds give a rough spread, not a confidence interval, and the 1 % study has only 78 fraud rows per test set.")
    P.para("**Limits.** The test set is drawn from the same generator as the training data, the best-epoch curves in the interface are selected on test rows, and the imbalance study covers one synthetic family, "
           "five seeds and a fixed threshold. Nothing here measures real fraud, drift, concurrency or user behaviour.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"SecurePay AI delivers what the objectives asked for in the interface and the metrics: preprocessing, an imbalance study, F1, recall, precision and ROC-AUC reporting, and a screen that flags a transaction. "
           f"The key finding is that the quantum-inspired RBM trainers reach F1 about {pct(sas['f1'], 0)} on synthetic data, while ordinary baselines reach {pct(rf['f1'], 0)} to {pct(lr['f1'], 0)}, so on this evidence "
           "the RBM is not the better model. PCD is unstable, undersampling is costly at realistic imbalance, and the largest practical risk was not the model but a swallowed exception in the serving path. "
           "Limits are the synthetic data, the classical simulation of quantum sampling, test-split epoch selection and the unfixed defect.")
    P.para("Future work: fix the scaling step and add a regression test; choose thresholds on a validation set and recalibrate PCD; train on real, time-ordered transactions with the base paper's data or a public set; "
           "implement path-integral annealing or use annealer access; and add authentication, monitoring for drift and a production server.")

    P.references()
    P.save(path)
    return path, P.order


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    path, order = build(out)
    print(path, "refs:", len(order), order)
