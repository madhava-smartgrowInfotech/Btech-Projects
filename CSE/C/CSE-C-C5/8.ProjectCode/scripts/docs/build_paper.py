"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for the Smart Campus Placement System from facts.py (metrics.json,
experiments.json, tests.json), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper
from .refs import N_VERIFIED

pct, f3, f4 = F.pct, F.f3, F.f4


def c(*nums):
    """Citation marker resolved by Paper.expand (global reference numbers in refs.py)."""
    return "{r:%s}" % ",".join(str(n) for n in nums)


# --------------------------------------------------------------------------- figures
def _box(ax, x, y, w, h, text, fc="#F2F5FA", ec="#1F4E79", fs=11, bold=False):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=1.6))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, p, q, color="#475569", ls="-", lw=1.6):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0))


def make_figures():
    """Compact figures for the paper, written to docs/figures/paper_*.png."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 12})
    out = {}
    BLUE, GREEN, ORANGE, PURPLE, GOLD = "#2B6CB0", "#14907F", "#D9772F", "#6B52D6", "#C98A0B"

    # ---- Fig. 1 architecture (compact)
    fig, ax = plt.subplots(figsize=(6.8, 4.5))
    ax.set_xlim(0, 100); ax.set_ylim(0, 66); ax.axis("off")
    _box(ax, 1, 48, 25, 15, "Browser\nReact 19 SPA\nport 5405", "#E8F0FC", BLUE, 11, True)
    _box(ax, 37, 48, 27, 15, "FastAPI service\n9 routes, Pydantic\nport 8405", "#E6F6EF", GREEN, 11, True)
    _box(ax, 74, 48, 25, 15, "recommend.py\npredict_for()\nrecommend()", "#EFE9FB", PURPLE, 11, True)
    _box(ax, 1, 25, 25, 12, "Flask UI\n(original, port 5000)", "#FFF1EA", ORANGE, 10.5)
    _box(ax, 37, 25, 27, 12, "preprocess.py\n24 features", "#F2F5FA", "#1B2A41", 10.5)
    _box(ax, 74, 25, 25, 12, "models/*.pkl\nXGB+Platt, kNN, SVM", "#FFF8E5", GOLD, 10)
    _box(ax, 1, 2, 25, 12, "generate_dataset.py\nhybrid_model.py", "#F2F5FA", "#1B2A41", 10)
    _box(ax, 37, 2, 27, 12, "data/*.csv\n3,000 students\n30 companies", "#FFF8E5", GOLD, 10)
    _box(ax, 74, 2, 25, 12, "metrics.json\nSHAP, PCA plots", "#FFF8E5", GOLD, 10)
    _arrow(ax, (26, 55.5), (37, 55.5), BLUE); ax.text(31.5, 57.5, "JSON", ha="center", fontsize=10, color=BLUE)
    _arrow(ax, (64, 55.5), (74, 55.5), GREEN); ax.text(69, 57.5, "calls", ha="center", fontsize=10, color=GREEN)
    _arrow(ax, (86.5, 48), (86.5, 37), PURPLE); ax.text(91, 42.5, "load", fontsize=10, color=PURPLE)
    _arrow(ax, (74, 51), (64, 33), "#1B2A41")
    _arrow(ax, (26, 31), (37, 31), ORANGE, "--")
    _arrow(ax, (13.5, 14), (13.5, 25), "#1B2A41", "--")
    _arrow(ax, (26, 8), (37, 8), "#1B2A41"); _arrow(ax, (64, 8), (74, 8), "#1B2A41")
    _arrow(ax, (50.5, 14), (50.5, 25), "#1B2A41", "--")
    ax.text(50, 64.5, "online (per request)", fontsize=10, ha="center", color=GREEN)
    ax.text(50, 16.2, "offline (training)", fontsize=10, ha="center", color="#475569", style="italic")
    out["arch"] = os.path.join(F.FIGS, "paper_architecture.png")
    fig.savefig(out["arch"], dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---- Fig. 2 main flow (compact)
    fig, ax = plt.subplots(figsize=(6.8, 5.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 78); ax.axis("off")
    _box(ax, 3, 66, 38, 9, "Profile + company + role", "#E6F6EF", GREEN, 11, True)
    _box(ax, 3, 52, 38, 9, "Build 24 features\n(gaps vs cutoffs)", fs=11)
    _box(ax, 3, 38, 38, 9, "p = XGBoost + Platt", "#EFE9FB", PURPLE, 11)
    ax.add_patch(Polygon([(22, 35), (41, 28), (22, 21), (3, 28)], fc="#FFF8E5", ec=GOLD, lw=1.6))
    ax.text(22, 28, "0.4 <= p <= 0.6 ?", ha="center", va="center", fontsize=11)
    _box(ax, 52, 24, 45, 8, "p = 0.5 p + 0.5 kNN(x)", "#EFE9FB", PURPLE, 11)
    ax.add_patch(Polygon([(22, 17), (36, 11.5), (22, 6), (8, 11.5)], fc="#FFF8E5", ec=GOLD, lw=1.6))
    ax.text(22, 11.5, "p >= 0.5 ?", ha="center", va="center", fontsize=11)
    _box(ax, 52, 2, 45, 9, "READY  /  NEEDS IMPROVEMENT\n+ rule-based skill-gap tips", "#E6F6EF", GREEN, 10.5, True)
    for p, q in (((22, 66), (22, 61)), ((22, 52), (22, 47)), ((22, 38), (22, 35)), ((22, 21), (22, 17))):
        _arrow(ax, p, q)
    _arrow(ax, (41, 28), (52, 28)); ax.text(46.5, 30, "yes", fontsize=10, ha="center", color=GREEN)
    _arrow(ax, (74.5, 24), (74.5, 11)); _arrow(ax, (36, 11.5), (52, 6.5))
    ax.text(4, 19, "no: keep p", fontsize=10, color=ORANGE)
    # recommendation loop
    _box(ax, 52, 66, 45, 9, "Recommendation (30 companies)", "#FFF1EA", ORANGE, 11, True)
    _box(ax, 52, 53, 45, 9, "feasibility filters\n|CGPA - cutoff| <= delta(tier)", fs=10.5)
    _box(ax, 52, 40, 45, 9, "score 4 roles per company\ns = p + 0.05 prox + 0.02 loc", fs=10.5)
    _arrow(ax, (74.5, 66), (74.5, 62)); _arrow(ax, (74.5, 53), (74.5, 49)); _arrow(ax, (74.5, 40), (74.5, 32.2), ORANGE)
    ax.text(76, 35, "top-5", fontsize=10, color=ORANGE)
    _arrow(ax, (41, 70.5), (52, 70.5), ORANGE, "--")
    out["flow"] = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(out["flow"], dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---- Fig. 3 results chart: five-seed accuracy (mean +/- sd) per model
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.8, 6.6), gridspec_kw={"hspace": 0.62})
    keys = ["logreg", "tree", "rf", "svm", "knn", "xgb_calibrated", "hybrid_xgb_knn", "hybrid_knn_serving"]
    lab = {"logreg": "LogReg", "tree": "Tree", "rf": "RF", "svm": "SVM", "knn": "kNN", "xgb_calibrated": "XGB+Platt",
           "hybrid_xgb_knn": "Hybrid\n(labels)", "hybrid_knn_serving": "Hybrid\n(serving)"}
    mu = [F.MS[k]["accuracy"]["mean"] for k in keys]
    sd = [F.MS[k]["accuracy"]["sd"] for k in keys]
    cols = [BLUE] * 6 + [ORANGE, GREEN]
    a.bar(range(len(keys)), mu, yerr=sd, color=cols, capsize=3, error_kw={"lw": 1.2})
    a.set_xticks(range(len(keys))); a.set_xticklabels([lab[k] for k in keys], fontsize=10.5)
    a.set_ylim(0.70, 0.88); a.set_ylabel("Accuracy (mean ± sd, 5 splits)")
    a.set_title("(a) Test accuracy over five random splits", fontsize=12.5)
    a.spines[["top", "right"]].set_visible(False)
    th = [r["threshold"] for r in F.THR]
    b.plot(th, [r["precision"] for r in F.THR], "o-", color=BLUE, lw=2, label="precision")
    b.plot(th, [r["recall"] for r in F.THR], "s-", color=ORANGE, lw=2, label="recall")
    b.plot(th, [r["accuracy"] for r in F.THR], "^-", color=GREEN, lw=2, label="accuracy")
    b.axvline(0.5, color="#888", ls="--", lw=1.3)
    b.set_xlabel("decision threshold (calibrated XGBoost)"); b.set_ylabel("score"); b.set_ylim(0.74, 0.95)
    b.legend(loc="center left", fontsize=11, frameon=False)
    b.set_title("(b) Threshold analysis, seed 42", fontsize=12.5)
    b.spines[["top", "right"]].set_visible(False)
    out["results"] = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(out["results"], dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---- Fig. 4 / 5: real screenshots cropped to the application area
    for name, src, box in (("predict", "02_predict.png", (256, 60, 1440, 880)), ("recommend", "03_recommend.png", (256, 100, 1415, 690))):
        p = os.path.join(F.FIGS, f"paper_{name}.png")
        Image.open(F.shot(src)).convert("RGB").crop(box).save(p)
        out[name] = p
    return out


# --------------------------------------------------------------------------- text
def build(path):
    figs = make_figures()
    env = F.ENV
    R = F.R
    cf = F.CONF
    P = Paper()
    authors = [[n, "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY]", "Roll No. " + r, "[email address]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION}, Project Guide", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY]", "[email address]"])
    P.title_block("Smart Campus Placement System: Calibrated Hybrid XGBoost-kNN Placement Prediction with Company-Role Recommendation", authors)
    P.begin_two_columns()

    P.abstract(
        "Campus placement cells keep student records but rarely use them to tell a student, early and with a probability, whether a target company is within reach. "
        "This paper presents the Smart Campus Placement System, which estimates the probability that a student is placed at a chosen company and role, shows the gaps "
        "against that company's cutoffs, and recommends company-role alternatives. It adapts a hybrid framework from graduate-admission prediction: a Platt-calibrated "
        "XGBoost model whose borderline cases are refined by a nearest-neighbour model, served through a FastAPI back end and a React interface. On a synthetic dataset of "
        f"{F.DS['rows']:,} students and {F.DS['companies']} companies, calibrated XGBoost reaches {R['xgb_calibrated']['accuracy']:.4f} accuracy on {F.TEST_N} held-out students and logistic "
        f"regression has the highest AUC ({R['logreg']['roc_auc']:.4f}). The hybrid reaches {R['hybrid_xgb_knn']['accuracy']:.4f} only when the refined cases are chosen using the true test labels; "
        f"with a rule that can run at serving time it scores {R['hybrid_knn_serving']['accuracy']:.4f}. Recommendations raise the estimated probability for most weak profiles but take "
        "three to eight seconds per request. All data are synthetic, so the figures describe software behaviour, not real placement outcomes.",
        ["calibration", "campus placement", "educational data mining", "gradient boosting", "hybrid model", "placement prediction", "recommendation"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para(f"Campus recruitment shapes the careers of students and the reputation of the institution, and placement cells manage it with spreadsheets, notices and manual "
           f"shortlisting. Student records already hold predictive signals - academic scores, aptitude and technical tests, internships, backlogs - and machine learning "
           f"can turn them into a placement probability before the season starts {c(1)}. Recent work on graduate admissions adds two ideas that transfer to placement: "
           f"probabilities that are calibrated, and a local model that revisits the borderline cases a global model finds hard {c(2)}.")
    P.para("Today, a student usually learns whether a company was within reach only after applying, with no estimate beforehand and no statement of which gap - "
           "grade, aptitude or technical skill - decided the outcome. A recruiter filters a long list by hand, and the placement officer cannot see readiness across "
           "branches or which training would help most. The cost is late preparation, wasted applications and uneven shortlisting.")
    P.para("A placement officer therefore needs three answers that a stored table cannot give: which students are close to ready for which kind of company, what separates "
           "a borderline student from a ready one, and where a student who is unlikely to be placed at a dream company has a realistic alternative. A student needs the same "
           "answers in personal form. Because wrong advice has a cost - a student who aims too low loses an opportunity and one who aims too high loses a season - the "
           "estimate must be a probability that can be checked, not only a yes or no.")
    P.para("The studies surveyed in Section II mostly report a classification accuracy on a small table of student records. Few give a calibrated probability, name the "
           "gap that holds a student back, or recommend alternative companies, and fewer still ship a working application. The declared base paper reports "
           "no numeric result at all, and the technique paper solves admissions, not placement. This work fills that gap and, in addition, "
           "measures how much of the hybrid model's advantage survives when it is evaluated without peeking at the answers.")
    P.para("The contributions are: (1) a working placement-prediction system that returns a calibrated probability and rule-based skill-gap tips for a chosen "
           "company and role; (2) a three-strategy company-role recommendation module with feasibility filters; (3) an officer dashboard and recruiter shortlist behind a "
           "FastAPI service and a React interface over unchanged model code; and (4) an evaluation across nine models, five random splits, a threshold and band "
           "analysis, calibration, a label-free hybrid rule, 46 automated checks and latency, stated together with what was not measured. "
           "Section II reviews related work, Section III gives the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All training and measurement ran on one desktop: {env['cpu']}, {env['ram']} RAM, {env['gpu']}, {env['os']}. Retraining one full split (six "
           "baselines, calibration and two local models) takes about three seconds.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}, scikit-learn {env['sklearn']} {c(6)}, XGBoost {env['xgboost']} {c(3)}, SHAP {env['shap']} {c(5)}, pandas {env['pandas']}, NumPy {env['numpy']}, "
           f"FastAPI {env['fastapi']} with Pydantic {env['pydantic']}, Flask {env['flask']} for the original interface, and React {env['react']} with Vite {env['vite']} "
           f"on Node {env['node']} for the browser interface.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Declared base paper.** Prasanna Kumari et al. {c(1)} describe a Streamlit placement-prediction application: a synthetic dataset of student records, "
           "Logistic Regression, Random Forest and Gradient Boosting trained on an 80:20 split, scaling and tuning, and extras such as batch CSV prediction, skill-gap "
           "analysis, a PDF report and e-mail delivery. The paper states the metrics it would use - accuracy, precision, recall, F1 and ROC-AUC - but reports no value "
           "for any of them, gives no dataset size, and offers no company recommendation. It is therefore a design reference, not a numeric benchmark.")
    P.para(f"**Technique base.** Heidari Fard and Tabrizi {c(2)} predict graduate admission on 13,000 real GradCafe records enriched with QS rankings. XGBoost {c(3)} "
           f"is calibrated by Platt scaling {c(4)} and its residual cases - those it gets wrong or scores between 0.4 and 0.6 - are re-predicted by a k-nearest-neighbour "
           f"model {c(7)}; accuracy rises from 0.7241 to 0.8723 and Brier score {c(8)} is 0.1864. A dual-axis recommendation module with feasibility filters raises "
           "the mean acceptance probability of rejected applicants by 65.1 %. This project reuses that framework, replacing universities by companies, programs by roles "
           "and QS rank by company tier.")
    P.para(f"**Placement prediction.** Thangavel et al. {c(21)} classify students into placement statuses with decision trees; Khandale and Bhoite {c(22)} compare eight "
           f"classifier families and report about 78 % accuracy for XGBoost and AdaBoost. Baffa et al. {c(15)} reach 98 % with a random forest {c(10)} on 218 graduates of "
           f"one department; Ambili and Abraham {c(16)} report 90.21 % for a stacking ensemble; Gupta et al. {c(17)} 0.9524 accuracy; Pathak et al. {c(18)} 0.8923 accuracy "
           f"and 0.9433 AUC for a voting classifier on a public Kaggle table; and Sanjana et al. {c(20)} pair a support-vector classifier {c(11)} with a deep Q-network "
           f"for scheduling and job matching. Surveys of educational data mining {c(23)} list placement and performance prediction among its standard tasks.")
    P.table("Representative work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        [c(1), "LR, RF, gradient boosting; Streamlit app", "Synthetic, size not stated", "No numeric result", "No evaluation; no recommendation"],
        [c(2), "XGBoost + Platt; kNN/SVM residual; recommendation", "13,000 GradCafe records", "Acc. 0.7241 to 0.8723", "Residual set uses labels; admissions"],
        [c(21), "Decision trees, five statuses", "Historical records", "Abstract only", "No probability"],
        [c(22), "Eight classifier families", "Past placed/unplaced", "About 78 %", "Moderate accuracy"],
        [c(15), "LR, DT, RF on six variables", "218 graduates, one university", "RF 98 %, F1 0.99", "Tiny single-department set"],
        [c(16), "Stacking, 20 attributes", "Size not stated", "90.21 %", "No calibration"],
        [c(17), "Classifiers + ensemble", "Recruitment data", "Acc. 0.9524, F1 0.9286", "Single split"],
        [c(18), "Tuned voting classifier", "Public Kaggle set", "Acc. 0.8923, AUC 0.9433", "No recommendation"],
        [c(20), "SVM + deep Q-network", "Not described", "87.4 % (SVM)", "Data undescribed"],
    ], widths=[0.3, 0.95, 0.7, 0.7, 0.75], size=6.5, align=["c", "l", "l", "l", "l"])
    P.para(f"**Methods used by this line of work.** Gradient-boosted trees such as XGBoost {c(3)} and random forests {c(10)} dominate tabular prediction because they capture "
           "thresholds and interactions, such as a CGPA cutoff that depends on company tier, without hand-built features. Their raw scores are not probabilities, which "
           f"matters when a student is told a percentage and when candidates are ranked; Platt scaling {c(4)} and the comparison of calibration methods by Niculescu-Mizil and "
           f"Caruana {c(9)} address this. Nearest-neighbour rules {c(7)} give a local view of the training data, which is the intuition behind the residual refinement. "
           "The studies above mostly stop at accuracy; they rarely report calibration, ranking quality, variation over random splits or a cost for the answer that a "
           "deployed service gives.")
    P.para(f"**Recommendation and explanation.** Recommendation applications {c(13)} rank candidates by predicted suitability; SHAP {c(5)} attributes a model's output to "
           f"features, and calibration {c(9)} makes probabilities usable for ranking. Results in Table I come from different data and metrics and are not ranked: "
           "several use small or undescribed tables, and none combines a calibrated probability, skill-gap feedback and company recommendation in one application. "
           "That combination, evaluated honestly on the data available, is the gap this paper addresses.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para(f"**Data.** No real placement records were available, so {F.DS['rows']:,} students with {F.DS['columns']} columns and a table of {F.DS['companies']} companies "
           "(7 Tier-1, 15 Tier-2, 8 Tier-3, with CGPA, aptitude and technical cutoffs, package, location and hiring rate) were generated with seed 42. Scores derive "
           "from CGPA plus noise; the label is drawn from a logistic score of the gaps between the student and the target company's cutoffs, a skill index, internships, "
           "projects, certifications, backlogs, a bonus for CSE and IT, a penalty by tier and Gaussian noise. Of the students, "
           f"{pct(F.DS['placed_rate'])} are placed; the placed rate falls from {pct(F.DS['by_tier']['3']['mean'])} for Tier-3 targets to {pct(F.DS['by_tier']['1']['mean'])} for Tier-1. Because the "
           "label follows a known rule, models recover the rule, and every number below describes software, not campuses.")
    P.para(f"**Features and split.** Five categorical columns are frequency-encoded and 13 numeric plus six engineered columns are standardised, giving 24 features. "
           "The engineered columns are the skill index (0.4 technical + 0.3 aptitude + 0.15 communication + 0.15 DSA, over 100), the company hiring rate, CGPA times "
           "tier, and the three gaps CGPA, aptitude and technical score minus the company cutoff. Encoders and scalers are fitted on the training part only. A stratified "
           f"70/15/15 split gives {F.TRAIN_N:,} training, {F.VAL_N} validation and {F.TEST_N} test students.")
    P.para("**Skill-gap tips.** Tips are rules, not model output: for the target company the system compares CGPA, aptitude and technical score with its cutoffs and "
           "names each one that falls short, adds a prompt for an internship when there is none, and otherwise states that the profile is strong. They are deliberately "
           "transparent so that a student can act on them; the global SHAP ranking shown to officers explains the model, not the individual.")
    P.para(f"**Models.** Six baselines are trained: logistic regression, a decision tree, a random forest {c(10)} of 200 trees, an RBF support-vector machine {c(11)}, "
           "k-nearest neighbours with k = 9, and XGBoost with 100 trees, depth 8, learning rate 0.1, subsample and column sampling 0.8, L1 0.1 and L2 1. XGBoost is "
           f"calibrated with Platt scaling {c(4)} (sigmoid, three folds),")
    P.eq("P(y = 1 | f) = 1 / (1 + exp(A f + B)),")
    P.para(indent=0, text="and a 9-fold cross-validation of the uncalibrated model on the training part serves as a stability check. Hyper-parameters are those of the technique "
           "paper and were not tuned further, so the baselines are not individually optimised; this keeps the comparison simple but means a tuned model could score differently.")
    P.figure(figs["arch"], "System architecture: browser, FastAPI service, shared prediction modules and file storage; training runs offline.")
    P.para("**Hybrid residual rule.** Following the technique paper, the residual set is")
    P.eq("R = { i : ŷ_i ≠ y_i  or  0.4 ≤ p_i ≤ 0.6 },")
    P.para(indent=0, text="and predictions in R are replaced by those of a kNN (or SVM) fitted on all training rows. The first condition needs the true label of the student, so it "
           "cannot be evaluated for a new student. Two label-free variants are therefore also measured: replacing only the borderline rows by the kNN label, and "
           "the serving rule that the application actually uses for a borderline probability p,")
    P.eq("p' = 0.5 p + 0.5 p_kNN,    0.4 ≤ p ≤ 0.6.")
    P.para(indent=0, text="A student is labelled placement ready when the final probability reaches 0.5, and rule-based tips name each of CGPA, aptitude and technical score "
           "that is below the company cutoff and a missing internship.")
    P.para("**Recommendation.** For a profile, each of the 30 companies is kept only if |CGPA - cutoff| is within Δ_max (0.6, 1.0 or 1.5 for tiers 1, 2 and 3), the aptitude is "
           "at most 15 points below the cutoff, and the student has at most two backlogs for a Tier-1 company. For each kept company four roles are scored with")
    P.eq("s = p + 0.05 prox + 0.02 loc,")
    P.eq("prox = max(0, 1 − |CGPA − c| / Δ_max),")
    P.para(indent=0, text="and three lists are returned: the best role per company, the target company with other roles, and the best five company-role pairs overall. "
           "The reported gain is the mean of p minus the probability for the original target over the pairs that beat it (Fig. 2).")
    P.figure(figs["flow"], "Main flow: probability with borderline refinement (left) and company-role recommendation (right).")
    P.para("**Evaluation protocol.** Accuracy, precision, recall, F1 and ROC-AUC are computed on the test part at the 0.5 threshold; the Brier score is the mean squared "
           "difference between the predicted probability and the outcome. With precision P and recall R,")
    P.eq("F1 = 2PR / (P + R).")
    P.para(indent=0, text=f"Because one split of {F.TEST_N} students gives noisy differences, the whole procedure - split, encoders, six baselines, calibration and both hybrids - is "
           "repeated for five seeds and means and standard deviations are reported. The shipped model files (seed 42) are used for the confusion matrices, band and threshold "
           "sweeps, SHAP ranking and recommendation study, so that they match the application's own dashboard.")
    P.para("**Implementation.** Fig. 1 shows the layers. A FastAPI service exposes nine routes: health, metadata, companies, metrics, dataset statistics, three explanation plots, prediction, "
           "recommendation and recruiter shortlist. Pydantic limits every field (CGPA 0-10, scores 0-100, counts 0-20), an unknown company returns 404 and the "
           "browser origin is the only one allowed. The service imports the original prediction functions unchanged; each request reloads four pickle files. "
           "The React interface has pages for eligibility, recommendations, an officer dashboard (metrics, SHAP, PCA, probability histogram, branch rates), a recruiter "
           "shortlist and a company board, with dark and light themes, a command palette and an activity log that lists every call the interface makes. Forty-six automated checks "
           "(unit, integration, functional, validation, security) and a 15-check smoke test pass.")
    P.para("**Design decisions.** The FastAPI layer imports the existing prediction code instead of rewriting it, so the original Flask interface and the new one give the "
           "same numbers. Pickle files are reloaded on every request, which keeps the code simple and the models always current but costs seconds for recommendations. "
           "Frequency encoding avoids a sparse one-hot expansion for company and role names; the gap features give the model the quantity that matters, the distance to a "
           "company's cutoffs. A single 0.5 threshold is used because accuracy is flat across thresholds (Section IV), and CSV and pickle files replace a database because "
           "the dataset is small and read-only.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** Models are scored on the {F.TEST_N} held-out students of the stratified split with seed 42 (59.6 % placed). The shipped model files "
           "reproduce the stored metrics exactly. Differences between models are small against the sampling noise of 450 students: one standard deviation of accuracy "
           "over five random splits is 0.01-0.02. Table II lists the single-split metrics. The data are synthetic, so no claim is made about real campuses.")

    def row(name, label):
        r = R[name]
        return [label, f"{r['accuracy']:.4f}", f"{r['roc_auc']:.4f}", f"{r['f1']:.4f}", f"{r['precision']:.4f}", f"{r['recall']:.4f}"]

    P.table("Test-set metrics, seed 42 (450 students)", ["Model", "Acc.", "AUC", "F1", "Prec.", "Rec."], [
        row("logreg", "Logistic Reg."), row("tree", "Decision Tree"), row("rf", "Random Forest"), row("svm", "SVM (RBF)"), row("knn", "kNN (k = 9)"),
        row("xgb", "XGBoost"), row("xgb_calibrated", "XGBoost + Platt"), row("hybrid_xgb_knn", "Hybrid, labels used"),
        row("hybrid_knn_labelfree", "Hybrid, label-free"), row("hybrid_knn_serving", "Hybrid, serving rule"),
    ], widths=[1.15, 0.45, 0.45, 0.45, 0.45, 0.45], size=7, align=["l", "c", "c", "c", "c", "c"])
    rl, xg = R["logreg"], R["xgb_calibrated"]
    P.para(f"**Key finding.** The hybrid with the technique paper's residual rule scores {R['hybrid_xgb_knn']['accuracy']:.4f} against {xg['accuracy']:.4f} for calibrated XGBoost "
           f"(+3.3 points, recall {xg['recall']:.4f} to {R['hybrid_xgb_knn']['recall']:.4f}). The gain comes from the selection: XGBoost is wrong on {F.RES['xgb_errors']} of the "
           f"{F.RES['n_test']} test students, {F.RES['xgb_errors'] - F.RES['xgb_errors_inside_band']} of them outside the borderline band, and they enter the {F.RES['oracle_residual']}-student "
           f"residual set only because their true label shows they are wrong. On that set the kNN is right for {pct(F.RES['knn_acc_on_oracle'])} against "
           f"{pct(F.RES['xgb_acc_on_oracle'])} for XGBoost - a selection effect. When only the {F.RES['borderline_only']} borderline students are re-predicted, which is possible "
           f"for a new student, accuracy is {R['hybrid_knn_labelfree']['accuracy']:.4f} (serving rule {R['hybrid_knn_serving']['accuracy']:.4f}), one student more than XGBoost. "
           f"The kNN is right on {pct(F.RES['knn_acc_on_borderline'])} of the borderline rows against {pct(F.RES['xgb_acc_on_borderline'])}. The technique paper's 0.8723 uses the same "
           "label-dependent rule, so it should be read with the same caution.")
    P.figure(figs["results"], "Accuracy over five random splits (a) and threshold analysis of the calibrated model (b).")
    lf, sv = F.MS["hybrid_knn_labelfree"]["accuracy"], F.MS["hybrid_knn_serving"]["accuracy"]
    P.para(f"**Five splits.** Over seeds 42, 1, 2, 3 and 4 the mean accuracy is {F.ms('hybrid_xgb_knn')} for the labels-used hybrid, {F.ms('hybrid_knn_labelfree')} label-free, "
           f"{F.ms('hybrid_knn_serving')} for the serving rule, {F.ms('xgb_calibrated')} for XGBoost with Platt scaling and {F.ms('logreg')} for logistic regression; "
           f"the latter has the highest AUC ({F.ms('logreg', 'roc_auc')}) because the synthetic label is a logistic function. The labels-used hybrid is ahead of XGBoost by 2.5 points "
           "on average and the label-free versions by 0.0-0.1 points, well inside one standard deviation (Fig. 3a).")
    P.table("Five-split accuracy and test confusion counts", ["Model", "Acc. (mean ± sd)", "TN", "FP", "FN", "TP"], [
        ["Logistic Reg.", F.ms("logreg"), cf["logreg"]["tn"], cf["logreg"]["fp"], cf["logreg"]["fn"], cf["logreg"]["tp"]],
        ["XGBoost + Platt", F.ms("xgb_calibrated"), cf["xgb_calibrated"]["tn"], cf["xgb_calibrated"]["fp"], cf["xgb_calibrated"]["fn"], cf["xgb_calibrated"]["tp"]],
        ["Hybrid, labels used", F.ms("hybrid_xgb_knn"), cf["hybrid_oracle"]["tn"], cf["hybrid_oracle"]["fp"], cf["hybrid_oracle"]["fn"], cf["hybrid_oracle"]["tp"]],
        ["Hybrid, serving", F.ms("hybrid_knn_serving"), cf["hybrid_serving"]["tn"], cf["hybrid_serving"]["fp"], cf["hybrid_serving"]["fn"], cf["hybrid_serving"]["tp"]],
    ], widths=[1.0, 1.1, 0.3, 0.3, 0.3, 0.3], size=7, align=["l", "c", "c", "c", "c", "c"])
    bw = F.BAND
    P.table("Replacing borderline predictions by kNN (seed 42)", ["Band of p", "Replaced", "Acc.", "F1", "AUC"],
            [[("none" if x["replaced"] == 0 else f"{x['lo']:.2f}-{x['hi']:.2f}"), x["replaced"], f"{x['accuracy']:.4f}", f"{x['f1']:.4f}", f"{x['roc_auc']:.4f}"] for x in bw],
            widths=[0.8, 0.7, 0.6, 0.6, 0.6], size=7, align=["l", "c", "c", "c", "c"])
    P.para(f"**Band, threshold and calibration.** Table IV shows that widening the band from none to 0.2-0.8 replaces up to {bw[-1]['replaced']} students and keeps accuracy between "
           f"{min(b['accuracy'] for b in bw):.4f} and {max(b['accuracy'] for b in bw):.4f}: the local model adds no measurable value on these data. Moving the decision threshold from 0.30 to 0.70 changes "
           f"accuracy by under 1.5 points ({min(t['accuracy'] for t in F.THR):.4f}-{max(t['accuracy'] for t in F.THR):.4f}) but trades precision ({F.THR[0]['precision']:.3f} to {F.THR[-1]['precision']:.3f}) against recall "
           f"({F.THR[0]['recall']:.3f} to {F.THR[-1]['recall']:.3f}), so 0.5 is a reasonable middle (Fig. 3b). Platt scaling lowers the Brier score {c(8)} only from {F.CAL['brier_raw_xgb']:.4f} to "
           f"{F.CAL['brier_platt']:.4f}; logistic regression is better ({F.CAL['brier_logreg']:.4f}) and the mean predicted probability ({F.CAL['mean_prob_test']:.3f}) matches the observed rate ({F.CAL['base_rate_test']:.3f}).")
    d = F.DS
    P.para(f"**Patterns in the data.** The placed rate depends strongly on the target tier ({pct(d['by_tier']['1']['mean'])}, {pct(d['by_tier']['2']['mean'])} and {pct(d['by_tier']['3']['mean'])} for tiers 1-3), falls with "
           f"backlogs from {pct(d['backlog_effect']['0'])} with none to {pct(d['backlog_effect']['4'])} with four, and rises with internships from {pct(d['internship_effect']['0'])} to {pct(d['internship_effect']['4'])}; "
           f"branches differ by under three points ({pct(min(v['mean'] for v in d['by_branch'].values()))}-{pct(max(v['mean'] for v in d['by_branch'].values()))}). These patterns are built into the generator, "
           "which is why the models find them.")
    sh = F.SHAP
    P.para(f"**Explanation.** Mean absolute SHAP value {c(5)} ranks the CGPA gap ({sh[0]['mean_abs_shap']:.2f}), backlogs ({sh[1]['mean_abs_shap']:.2f}), the technical gap "
           f"({sh[2]['mean_abs_shap']:.2f}), the aptitude gap ({sh[3]['mean_abs_shap']:.2f}) and CGPA times tier ({sh[4]['mean_abs_shap']:.2f}) first, well above all other features (below 0.18). "
           "This mirrors how the labels were generated, so it validates the explanation tool, not a fact about real placements (Fig. 4). Fig. 5 shows the eligibility screen that "
           "presents one such prediction with its cutoff checks.")
    P.figure(F.fig("shap_top10.png"), "Mean absolute SHAP value of the ten most influential features for XGBoost on the test students.")
    P.figure(figs["predict"], "Eligibility screen: Microsoft, SDE, CGPA 8.4, aptitude 84, technical 79 gives 22.2 %, with cutoff checks and a tip.")
    rc = F.REC
    P.para(f"**Recommendation.** For {rc['students']} test students rated below 0.5 for their own target, the mean probability is {rc['mean_base_prob']:.3f}; "
           f"{rc['with_at_least_one_better_alt']} of {rc['students']} receive at least one better pair, the top pair averages {rc['mean_top1_prob']:.3f}, and it reaches 0.5 for "
           f"{rc['top1_reaches_ready']} of {rc['students']} ({pct(rc['top1_reaches_ready'] / rc['students'], 0)}). These are model estimates, not realised placements. In Fig. 6 a profile aimed at Google "
           "(10.8 %) is steered to ValueLabs and Infosys, Tier-3 companies, because the score maximises probability, not package or fit; and when the target fails the CGPA "
           "filter the role-only list is empty.")
    P.figure(figs["recommend"], "Recommendation screen: base probability 10.8 %, mean gain +78.8 points, top pick ValueLabs QA Engineer 89.9 %.")
    pr = F.PERF
    P.para(f"**Speed and tests.** On localhost (127.0.0.1) a prediction takes {pr['POST /api/predict']['mean_ms']:.0f} ms on average ({pr['POST /api/predict']['p95_ms']:.0f} ms at the 95th percentile) and a shortlist "
           f"{pr['POST /api/recruiter/shortlist']['mean_ms']:.0f} ms, but a recommendation takes {pr['POST /api/recommend']['mean_ms'] / 1000:.1f} s on average, and {rc['recommend_latency_s']['mean']:.1f} s in process, because every "
           "scored pair reloads the four model files; caching them is the obvious fix and was not done. All "
           f"{F.TEST_SUMMARY['total']} automated checks pass, including malformed input, injection-style strings and path traversal; an unknown branch or role is silently accepted, and there is "
           "no authentication.")
    P.para(f"**Failure cases.** Calibrated XGBoost makes {cf['xgb_calibrated']['fp']} false placements and {cf['xgb_calibrated']['fn']} missed placements among {F.TEST_N} students; moving the "
           "threshold shifts errors between the two kinds but not their total. The model has not seen real borderline students, so its probability near 0.5 should be read as "
           "an ordering, not a promise. Further observed limits: the recommendation module sends a weak profile to the easiest companies, the role-only list is empty when the target "
           "fails the CGPA filter, unseen categories get a frequency of zero instead of an error, and tips cannot say how large a gap is worth closing.")
    t = F.TEST_SUMMARY["by_group"]
    P.para(f"**Test coverage.** The {F.TEST_SUMMARY['total']} checks are {t['unit'][1]} unit, {t['integration'][1]} integration, {t['functional'][1]} functional, {t['validation'][1]} validation and {t['security'][1]} security checks. "
           "They confirm that probabilities stay between 0 and 1, rise with CGPA and fall with backlogs, that an all-zero profile scores 0.139 and an all-maximum profile 0.799 at "
           "Google, that out-of-range values return 422, and that a 100 kB company name, a script tag and a path-traversal plot name are all rejected with 404. They do not "
           "include a browser-automation suite, a load test or any real student data.")
    P.para("**Comparison with the base papers.** The declared base paper reports no numbers, so no comparison is possible. The technique paper's 0.7241 (XGBoost) and 0.8723 (hybrid) "
           f"are on 13,000 real, noisy admission records; our {xg['accuracy']:.4f} and {R['hybrid_xgb_knn']['accuracy']:.4f} are on a synthetic table generated by a logistic rule, on which even logistic regression "
           f"reaches {rl['accuracy']:.4f}. The two sets differ in size, origin, noise and task, so the numbers are not comparable; the relative result that carries over is that the "
           "hybrid's advantage depends on how the residual set is chosen.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("The system delivers what the batch objectives asked for in software: a calibrated placement probability with skill-gap tips, a three-strategy company-role "
           "recommendation, an officer dashboard and a recruiter shortlist, all behind a tested API. Six classifiers, a calibrated XGBoost and two hybrids were compared over five splits. "
           "The central finding is negative for the hybrid: its 0.84 accuracy depends on selecting residual cases with the true labels, and with a rule usable for a new student "
           f"it equals calibrated XGBoost ({R['hybrid_knn_serving']['accuracy']:.4f} against {xg['accuracy']:.4f}); logistic regression ties or beats every model on AUC.")
    P.para("Against the six objectives: data were generated, not collected; encoding was done and the 59.7/40.3 class ratio needed no resampling; classifiers were trained "
           "and compared; recommendation, skill-gap tips and dashboards were built; and accuracy, precision, recall, F1, AUC and Brier score were reported. The experiment also "
           "shows that a simple linear model is a strong baseline when the signal is linear, and that any claimed gain from refining borderline cases must be checked "
           "without access to the answers.")
    P.para("The limits are plain: the data and company table are synthetic, so no real-campus accuracy is claimed; recommendation gains are unverified estimates; recommendations "
           "take seconds; tips are fixed rules; and there is no database, login, e-mail or PDF report. Future work: train on real placement records from the cell, cache "
           "the model files, train the refinement without label leakage, add per-student SHAP, authentication with roles and a database, batch CSV prediction and a fairness audit across branches.")

    P.references()
    P.save(path)
    return P


def main():
    path = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    P = build(path)
    print("wrote", path)
    print("references cited:", len(P.order), "global numbers:", P.order)
    bad = [g for g in P.order if g > N_VERIFIED]
    print("unverified cited:", bad)


if __name__ == "__main__":
    main()
