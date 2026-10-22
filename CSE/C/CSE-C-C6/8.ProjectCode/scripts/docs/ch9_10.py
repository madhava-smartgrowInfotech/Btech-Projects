"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import cite

A = F.A
PROP, DEF, RND, MAJ = A["proposed_test"], A["pca_svc_default_test"], A["random_search_test"], A["majority_test"]
LR_FULL = A["ref_full_LogisticRegression_test"]
LV = F.LV
EA = F.EA
PC = A["per_class_test"]


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def m(blk, key="f1_macro", d=3):
    return f"{blk[key]['mean']:.{d}f}"


def _cost_ratio():
    return A["train_time_s"]["mean"] / A["ref_full_LinearSVC_time"]["mean"]


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    return [
        P("The project does not propose a new learning algorithm and does not claim one. Principal component analysis, the Firefly algorithm and the support vector machine are all established methods "
          f"{cite('pca', 'firefly09', 'svm')}. What the project contributes is a particular combination of them, the way the combination is packaged as an application and, above all, a measurement of how well the combination works on real fact-checked text. "
          "This document states first how the work differs from the base paper, then what is and is not new, and finally what the evidence supports."),
        H2("Difference from the base paper"),
        TAB("The base paper and this project compared", ["Dimension", "Base paper (Saad et al. 2026) [1]", "This project", "What differs"],
            [["Problem", "Arabic fake news detection, binary", "English news-statement screening with an explicit PARTIALLY TRUE class", "Language and number of classes"],
             ["Data", "7,474 articles from several sources, part translated from LIAR and WELFake", f"LIAR2 statements ({F.NTRAIN_FULL:,} / {F.NVALID:,} / {F.NTEST:,}) for evaluation; a 750-document synthetic corpus in the shipped model", "Different language, text length and label scheme"],
             ["Features", "Contextual CAMeLBERT embeddings", "TF-IDF (1-2 grams) plus 25 stylometric features, reduced by PCA", "Classical sparse features instead of transformer embeddings"],
             ["Classifier", "Neural network", "RBF multi-class SVM", "Different learner"],
             ["Optimisation", "Hand-run hyper-parameter grid (learning rate, batch size, dense units)", "Firefly search over a component mask, C and gamma with a size penalty", "A metaheuristic chooses features and parameters together"],
             ["Imbalance", "Class weighting, compared with oversampling, undersampling and SMOTE", "Balanced class weights; no resampling comparison", "The idea of algorithm-level weighting is adopted"],
             ["Compute", "GPU (Tesla T4)", "CPU only", "The project targets a light pipeline"],
             ["Delivery", "Experimental framework with LIME and SHAP analyses", "Web application with single and batch detection, analytics and retraining", "Packaged for a non-expert user"]],
            widths=[0.9, 1.9, 2.2, 1.7], align=["l", "l", "l", "l"], size=9),
        H2("What is new and what is not"),
        TAB("Elements of the work and their status", ["Element", "Status", "Note"],
            [["PCA, RBF SVM, TF-IDF, Firefly algorithm", "Standard", f"Used through scikit-learn {cite('sklearn')} and a short own implementation of the Firefly update {cite('firefly09')}"],
             ["Firefly-based feature selection for classification", "Known idea", f"Metaheuristic feature selection is established {cite('fs_survey', 'ffs')}"],
             ["Joint search of a binary component mask, log C and log gamma, with a penalty on the share of components kept", "Design choice of this project", "One encoding handles feature selection and parameter tuning in one run; the fitness is the 3-fold macro-F1"],
             ["Explicit PARTIALLY TRUE class mapped from half-true", "Adopted from the LIAR label scale", f"The idea of graded truth labels is in the dataset {cite('liar', 'rashkin')}; the product exposes it as a verdict"],
             ["Application with batch check, analytics and retraining on a user's own CSV", "New in this project", "Six screens, eight endpoints, background retraining with atomic model replacement"],
             ["Equal-budget random-search and mask-only baselines on a real benchmark", "New in this project", "Lets the benefit of the swarm be separated from the benefit of the other steps"],
             ["Observations: no clear gain from the optimiser; PCA cap keeps 29 % of the variance; verdict and probabilities disagree", "Findings of this project", "Reported with the data that supports them"]],
            widths=[2.7, 1.4, 2.6], align=["l", "l", "l"], size=9.5),
        H2("What the evidence supports"),
        P(f"The evidence supports the statement that the combination works end to end and gives a three-class macro-F1 of {F.pm(PROP)} and an accuracy of {F.pm(PROP, 'accuracy')} on the LIAR2 test split, well above a majority-class baseline (macro-F1 {m(A['majority_test'])}). "
          f"It does not support the statement that the Firefly search improves on an untuned SVM (macro-F1 {m(DEF)}) or on random search with the same budget ({m(RND)}), nor that the pipeline is cheaper than simple alternatives: it is about {_cost_ratio():.0f} times slower to train than a linear SVM that scores better. "
          "These are limits of the present experiment (three seeds, a 3,000-statement training subsample, default Firefly parameters) and are discussed under limitations."),
    ]


def contribution_blocks():
    return [
        N("An end-to-end pipeline that turns the text of a news statement into one of three verdicts: TF-IDF and 25 stylometric features, standardisation, PCA, Firefly selection of components and SVM parameters, and an RBF multi-class SVM with balanced class weights.",
          "A joint Firefly encoding of a component mask, log C and log gamma, scored by 3-fold cross-validated macro-F1 minus a penalty on the share of components kept (src/firefly.py).",
          "A usable application, TruthGlow: a React interface over a thin FastAPI layer, with single-text detection, cue words, class probabilities, CSV batch screening with download, model analytics read live from the model, and background retraining on a user's own labelled CSV.",
          f"A reproducible real-data benchmark on LIAR2 (scripts/run_experiments.py): the pipeline against the majority class, a default SVM on the same PCA features, a mask-only variant, random search with an equal budget and TF-IDF linear models, over three seeds.",
          f"A set of honest findings: macro-F1 {F.pm(PROP)} on three classes; no clear gain from the Firefly search; PARTIALLY TRUE the weakest class (F1 {PC['PARTIALLY TRUE']['f1-score']['mean']:.2f}); the shipped synthetic model's 1.000 does not transfer (macro-F1 {F.f3(A['demo_model_on_liar2_test']['f1_macro'])} on real statements); "
          f"verdict and displayed probabilities disagree on {LV['disagree_rate'] * 100:.0f} % of the test statements.",
          f"A test suite of {F.N_TESTS} automated checks (API smoke test, library unit tests and API edge cases) and a documented set of diagrams, screens and measurements."),
    ]


def scope_blocks():
    return [
        H2("In scope"),
        B("Text-only classification of an English news statement or article into REAL, PARTIALLY TRUE or FAKE, with a confidence and the three class probabilities.",
          "A feature pipeline of text cleaning, TF-IDF with word unigrams and bigrams, 25 handcrafted stylometric features, standardisation and PCA.",
          "Firefly optimisation of the PCA component subset and of the SVM parameters C and gamma; an RBF SVM with balanced class weights.",
          "A web application on one machine: single-text detection, batch CSV screening, model analytics, retraining on a user's labelled CSV, an About page. The command-line tools and the Streamlit app of the original library are kept.",
          f"Evaluation on LIAR2 against stated baselines: accuracy, macro-F1, per-class precision, recall and F1, confusion matrix, cost and response time. Hardware used: {F.HARDWARE}."),
        H2("Out of scope"),
        B("Checking a claim against sources or a knowledge base. The system judges how text is written, not whether it is true.",
          "Images, video, audio, propagation patterns, user or source credibility, and any other metadata.",
          "Languages other than English (the stop-word list and the cue lists are English).",
          "Transformer or neural-network classifiers, stemming and lemmatisation, and any GPU training.",
          "Authentication, multi-user operation, a database, cloud deployment and concurrent load handling.",
          "Use for moderation, legal or editorial decisions."),
        H2("Users and environment"),
        P("The intended user is a student, teacher or analyst who runs the application locally (Windows, Python 3.11 and Node.js 20 or newer, started with run.bat) and uses it as a screening aid and as a teaching example of a PCA, Firefly and SVM pipeline. "
          "The backend listens on 127.0.0.1:8406 and the frontend on port 5406; no data leaves the computer."),
    ]


def assumption_blocks():
    return [
        B("The text of a statement carries some signal about its truthfulness through vocabulary, word pairs and style. The experiments confirm a weak signal; they do not show that style causes or determines truth.",
          "The labels of LIAR2 are correct and the three-class mapping (true and mostly-true to REAL, half-true to PARTIALLY TRUE, the rest to FAKE) is a reasonable reading of the project's three verdicts.",
          "A stratified subsample of 3,000 training statements represents the full training split.",
          "A 3-fold cross-validated macro-F1 on the training part is a fair fitness for the Firefly search.",
          "Input is English text of at least five words. The API rejects shorter input.",
          "The application runs on a trusted local machine; the uploaded CSV is the user's own and is read by the local backend only.",
          "The scikit-learn version that unpickles the model is the one that produced it (1.9.x); an older version may fail to load it."),
    ]


def limitation_blocks():
    lim = [
        ("L1. The shipped model is trained on synthetic data.", f"The model in models/msvm_model.pkl was fitted to 750 template sentences. Its perfect scores prove nothing about real news; on LIAR2 it reaches an accuracy of {A['demo_model_on_liar2_test']['accuracy']:.3f} and a macro-F1 of {F.f3(A['demo_model_on_liar2_test']['f1_macro'])}."),
        ("L2. The system cannot check facts.", "It sees words and style only. A carefully worded false claim is called REAL, and a true claim written in an accusatory tone is called FAKE (Section 8.5 of the report)."),
        ("L3. The optimiser gives no demonstrated gain.", f"Test macro-F1 is {F.pm(PROP)} for Firefly, {F.pm(DEF)} for the default SVM and {F.pm(RND)} for random search; the differences are within the seed-to-seed spread. Training takes about {A['train_time_s']['mean']:.0f} s against {A['ref_full_LinearSVC_time']['mean']:.1f} s for a linear SVM that scores better."),
        ("L4. PARTIALLY TRUE is barely learned.", f"Its F1 is {PC['PARTIALLY TRUE']['f1-score']['mean']:.2f}, with a precision of {PC['PARTIALLY TRUE']['precision']['mean']:.2f}; half-truths do not differ from other classes in vocabulary or style."),
        ("L5. PCA is capped at 300 components.", f"On real text this keeps only {A['pca_variance']['mean'] * 100:.1f} % of the variance, although the interface and the About page say that PCA keeps 95 %. The target is reached only on the synthetic corpus."),
        ("L6. The verdict and the probabilities disagree.", f"The verdict is SVC.predict; the probabilities are Platt-scaled and ignore the class weights. They disagree for {LV['disagree_n']:,} of {F.NTEST:,} test statements ({LV['disagree_rate'] * 100:.1f} %), and PARTIALLY TRUE is never the most probable class. The confidence shown can therefore belong to another class than the verdict."),
        ("L7. Small training subsample and few seeds.", f"The pipeline was fitted on {F.NTRAIN:,} of {F.NTRAIN_FULL:,} training statements because the Firefly search needs hundreds of SVM fits; three seeds give no significance test. Larger training data would very likely help (logistic regression improves from {m(A['ref_subsample_LogisticRegression_test'])} to {m(LR_FULL)})."),
        ("L8. One dataset, short English statements.", "Only LIAR2 (PolitiFact statements of about 18 words) was used. Longer articles, other sources, other languages and cross-dataset transfer were not tested."),
        ("L9. Stemming is not implemented.", "Objective 2 lists stemming; the preprocessing does cleaning, stop-word removal and TF-IDF only. The effect of stemming was not measured."),
        ("L10. Some interface wording assumes the demo model.", "The landing page strip, the note on the Analytics screen and the example chips describe a synthetic demo corpus, and stay visible when a model trained on real data is loaded."),
        ("L11. A label-column bug in the CSV loader.", "pandas reads a label column that contains only the words true and false as booleans, and load_csv then maps true to PARTIALLY TRUE and false to REAL. Columns with mixed LIAR labels or the project's own names are read correctly."),
        ("L12. Operational limits.", "There is no login, no concurrency or load test and no database; the retrain endpoint replaces the model file and allows one job at a time; uploads are limited to 25 MB and 20,000 rows for batch checks."),
        ("L13. Fixed cue lists.", "The sensational and credibility cue words shown on the Detect screen come from two short fixed lists, so for political claims they are usually empty."),
    ]
    out = [P("The following limitations apply to the system and to the conclusions of this report. They are numbered so that other chapters can refer to them.")]
    for t, body in lim:
        out.append(P(f"**{t}** {body}"))
    return out


def not_measured_blocks():
    return [
        P("The following were not measured, and no figure for them appears in this report."),
        TAB("Items not measured", ["Item", "Why it matters", "Status"],
            [["Pipeline fitted on all 18,369 training statements", "Shows how much of the gap to the linear models is training size", "Not run (Firefly cost)"],
             ["Other datasets (for example ISOT) and cross-dataset transfer", "Generalisation beyond one fact-checker's statements", "Not run"],
             ["Statistical significance of the differences between models", "Differences of 0.01 macro-F1 are within the spread of three seeds", "Not tested"],
             ["Different Firefly parameters, population sizes, generations and PCA caps", "The defaults may be far from the best", "Not varied"],
             ["Effect of stemming, of the stylometric block alone and of the TF-IDF block alone", "Objective 2 lists stemming; the contribution of each block is unknown", "Not run"],
             ["Probability calibration (reliability curve, Brier score)", "Verdict and probabilities disagree", "Only the accuracy per confidence bin and the disagreement rate were measured"],
             ["Contextual embeddings (transformer) as features", "The base paper's main ingredient", "Not tried"],
             ["Concurrent users, memory use under load, long-running behaviour", "Deployment readiness", "Not tested; only sequential requests were timed"],
             ["A user study of the interface", "Whether non-experts understand the verdicts", "Not carried out"],
             ["Security review", "Upload handling and exposure beyond localhost", "Input validation checked only"]],
            widths=[2.7, 2.4, 1.6], align=["l", "l", "l"], size=9.5),
    ]


def walkthrough_blocks():
    return [
        P("This section walks through the code that matters most, quoting the repository as it was when the results of this report were measured."),
        H2("Cleaning the text"),
        P("`clean_text` lower-cases the text, removes URLs, mentions and hashtags, drops everything that is not a letter, then removes stop words and tokens of two characters or fewer. What remains is a space-separated string of content words that TF-IDF can use. "
          "No stemming is done (limitation L9)."),
        CODE(src("src/preprocessing.py", 32, 43), 8.5),
        H2("Building the feature matrix and reducing it"),
        P("The first part of `fit` builds the TF-IDF matrix (word unigrams and bigrams, sublinear term frequency, terms in at least two and at most 90 % of the documents), appends the 25 stylometric columns, standardises every column and fits a full PCA only to find "
          "how many components reach 95 % of the variance. The number is then limited to 300 (and to fewer than the number of documents), and a PCA with that many components is fitted. On the LIAR2 subsample the cap always applies."),
        CODE(src("src/pipeline.py", 37, 66), 8.5),
        H2("The Firefly search"),
        P("A firefly is a vector of 302 numbers: 300 logits that become a component mask when their sigmoid exceeds 0.5, then log10 C and log10 gamma. `_decode` turns a vector into a mask and the two parameters and never returns an empty mask. "
          "`_fitness` is the 3-fold cross-validated macro-F1 of an RBF SVM with balanced class weights on the masked features, minus 0.02 times the share of components kept. In `optimize`, every firefly moves towards each brighter one by an attractiveness "
          "that decays with the squared distance, plus a random step whose size shrinks by 3 % per generation; the dimmest firefly is replaced by the best vector plus noise at the end of each generation (elitism), and the best brightness is stored for the convergence curve."),
        CODE(src("src/firefly.py", 34, 106), 8),
        H2("The final classifier and the baseline"),
        P("The mask and the two parameters found by the search define the final SVM. It is fitted on the training part, scored on the 20 % hold-out, and a default SVM on all components is fitted beside it to fill the baseline row of the Analytics screen. "
          "`probability=True` makes scikit-learn fit a Platt scaling by internal cross-validation, which is the source of the probabilities discussed in limitation L6."),
        CODE(src("src/pipeline.py", 91, 110), 8.5),
        H2("The prediction endpoint"),
        P("The endpoint joins the headline and the text, rejects anything under five words (HTTP 422), takes the pipeline from `get_pipe()` and measures only the model call for `latency_ms`. The verdict is the predicted class, the probabilities come from `predict_proba`, "
          "and the confidence is their maximum."),
        CODE(src("backend/main.py", 171, 195), 8.5),
        H2("Retraining on a background thread"),
        P("The retrain endpoint validates the sliders and the upload, starts a daemon thread and answers 202 with a job id at once. The worker fits a new pipeline, writes it to a temporary file, replaces the model file atomically with `os.replace` and swaps the in-memory pipeline under a lock, "
          "so that requests served during the swap see either the old or the new model and never a partial one."),
        CODE(src("backend/main.py", 250, 272), 8.5),
        H2("The equal-budget random search"),
        P("The experiment script counts the number of fitness evaluations that the Firefly search used and gives random search the same number, using the same fitness function and the same initial ranges. This is what makes the comparison in Chapter 8 fair."),
        CODE(src("scripts/run_experiments.py", 121, 137), 8.5),
    ]


def decision_blocks():
    return [
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "What was observed"],
            [["Keep the model code a pure-Python library (src/) and add a thin FastAPI layer", "The CLI, the Streamlit app and the web app then share one tested pipeline", f"No model logic is duplicated; {F.N_UNIT_API} API edge checks run against the same code"],
             ["TF-IDF with 1-2 grams plus 25 stylometric features", "Cheap, interpretable, no GPU; stylometric signals such as capital letters and exclamation marks are classic fake-news cues " + cite("potthast"), "On real statements the TF-IDF linear models do at least as well, so the features are adequate but not the limit"],
             ["Standardise all columns before PCA", "PCA is sensitive to scale; stylometric counts and TF-IDF weights differ by orders of magnitude", "Standardising sparse TF-IDF columns gives rare terms the same variance as common ones; whether this hurts was not tested"],
             ["PCA to 95 % variance, capped at 300 components", "A cap keeps the Firefly search space and the SVM fits affordable", f"On real text the cap is always reached and keeps {A['pca_variance']['mean'] * 100:.1f} % of the variance (L5)"],
             ["One Firefly vector for the mask, log C and log gamma", "Features and parameters interact, so a joint search avoids tuning them in two steps", f"About {A['n_selected']['mean']:.0f} of 300 components are kept; no gain on the test split over defaults"],
             ["Penalise the share of components kept (0.02)", "Prefer smaller feature sets at equal score", "The penalty is small; the mask-only variant scored lower than the default SVM"],
             ["Fitness: 3-fold macro-F1 inside the training part", "Macro-F1 does not reward ignoring the minority classes; 3 folds keep each evaluation cheap", f"Training-split fitness is higher for Firefly than for random search ({A['firefly_fitness_best']['mean']:.3f} against {A['random_fitness_best']['mean']:.3f}); test scores are equal within noise"],
             ["Balanced class weights", "The FAKE class is 58 % of the test split; the idea follows the base paper's class weighting " + cite("base", "imbalance"), "Macro-F1 well above the majority baseline; accuracy below it"],
             ["probability=True on the SVC", "The interface needs class probabilities for the chart and the confidence", f"Platt probabilities ignore the class weights and disagree with the verdict on {LV['disagree_rate'] * 100:.0f} % of the statements (L6)"],
             ["Retraining on a daemon thread with atomic file replacement", "A request must not time out for minutes, and a crash must not leave a half-written model", "The Retrain screen polls the job; the tests and the screen captures retrained a copy of the model, so the shipped file was not touched"],
             ["Limits: 25 MB per upload, 20,000 rows per batch, 5 words minimum", "Protect the single local process from oversized and empty input", "Covered by edge-case tests (413 and 422 responses)"],
             ["No login and no database", "A local, single-user teaching application; the original product had neither", "Simplest to run; unsuitable for shared deployment (L12)"],
             ["Experiments on LIAR2, three seeds, a 3,000-statement subsample", "A real, public, licensed benchmark; the Firefly search is the cost driver", "About 8 min per fit; full-data results not measured (L7)"]],
            widths=[2.0, 2.4, 2.3], align=["l", "l", "l"], size=9),
    ]


# ------------------------------------------------------------------ conclusion and future scope
def _conclusion_body():
    return [
        H2("Summary"),
        P("The project set out to build a fake news detection system around a feature-based, optimised multi-class SVM: text features reduced by PCA, with the Firefly algorithm choosing features and parameters, and an explicit PARTIALLY TRUE class. "
          "The system was built and works end to end as a web application, a command-line tool and a Streamlit app over one library. It accepts a statement or a CSV, returns a verdict with a confidence, class probabilities and cue words, shows its own statistics and can be retrained on a user's labelled data."),
        P(f"The report measured the system honestly. The model shipped with the project was trained on a synthetic template corpus and scores 1.000 on its own hold-out, but only {F.f3(A['demo_model_on_liar2_test']['f1_macro'])} macro-F1 on real statements. "
          f"A model trained on {F.NTRAIN:,} real LIAR2 statements reaches a macro-F1 of {F.pm(PROP)} and an accuracy of {F.pm(PROP, 'accuracy')} on the {F.NTEST:,} test statements, over three seeds."),
        H2("Objectives achieved"),
        B("Achieved: a labelled dataset was obtained and mapped to three classes (objective 1, for evaluation); PCA reduces 4,025 features to at most 300 components (3); the Firefly algorithm is implemented and selects components and SVM parameters (4, implemented); an RBF multi-class SVM is trained on the selected features (5); accuracy, precision, recall and F1 are evaluated against unoptimised baselines (6).",
          "Partly achieved: preprocessing (2) covers cleaning, stop-word removal and vectorisation but not stemming.",
          f"Not achieved: the aim of improving accuracy and computational cost. The optimised pipeline is not better than a default SVM or random search on the test split, and it is about {_cost_ratio():.0f} times slower to train than a linear SVM that scores better."),
        H2("Key findings"),
        N(f"On real, short, fact-checked statements the three-class task is hard: macro-F1 is about {m(PROP, 'f1_macro', 2)}, and the best simple model (logistic regression on all training statements) reaches {m(LR_FULL, 'f1_macro', 2)}.",
          f"The Firefly search improves its own training fitness over random search ({A['firefly_fitness_best']['mean']:.3f} against {A['random_fitness_best']['mean']:.3f}) but not the test score; on this data the optimiser does not pay for its cost of about {A['train_time_s']['mean']:.0f} s per fit.",
          f"FAKE is recognised best (F1 {PC['FAKE']['f1-score']['mean']:.2f}) and PARTIALLY TRUE worst ({PC['PARTIALLY TRUE']['f1-score']['mean']:.2f}); half-truths cannot be told apart by vocabulary and style.",
          f"Confidence is informative: accuracy rises from {EA['by_confidence'][1]['accuracy']:.2f} for confidence between 0.4 and 0.5 to {EA['by_confidence'][4]['accuracy']:.2f} between 0.7 and 0.8; but the verdict and the displayed probabilities disagree on {LV['disagree_rate'] * 100:.0f} % of the statements.",
          f"A perfect score on a synthetic corpus says nothing about real text, and the PCA step keeps only {A['pca_variance']['mean'] * 100:.0f} % of the variance on real text because of its cap.",
          f"The software is sound: {F.N_TESTS} automated checks pass, a statement is classified in about {F.LAT[0]['predict_server_ms']['mean']:.0f} ms and {F.NTEST:,} statements in about {F.LAT[0]['batch']['2296']['server_s']:.1f} s."),
        H2("Practical applications"),
        B("A teaching and demonstration tool for a complete classical machine-learning pipeline (features, PCA, metaheuristic tuning, SVM) with a working interface and honest analytics.",
          "A screening aid that flags writing in a sensational or one-sided style for a human to look at, and a baseline for comparison with heavier models.",
          "A starting point for retraining on a newsroom's or a class's own labelled data through the Retrain screen.",
          "It is not suitable for deciding whether a claim is true, nor for moderation or legal decisions."),
        H2("Known limitations"),
        P("The main limitations are the synthetic shipped model (L1), the absence of any fact-checking (L2), the missing gain from the optimiser (L3), the weak PARTIALLY TRUE class (L4), the capped PCA (L5), the mismatch between verdict and probabilities (L6) and the small training subsample with few seeds (L7). "
          "The full list L1 to L13 is given in the document on scope and limitations."),
    ]


def _future_body():
    return [
        H2("Improvements to the model"),
        N("Make the verdict and the probabilities consistent (untested): calibrate the probabilities with class priors taken into account, or derive both from the decision function, and show the calibrated confidence. This removes the mismatch of L6.",
          "Remove the PCA cap or use incremental or truncated PCA on the sparse matrix without standardising it (untested), and measure the variance kept and the effect on the score (L5).",
          "Train the pipeline on all 18,369 LIAR2 training statements, for example with a cheaper fitness (a subsample inside each fold) or a surrogate, and report the result with confidence intervals over more seeds (L7).",
          "Tune the Firefly parameters (population, generations, alpha, beta0, gamma, penalty) and compare with Bayesian optimisation, as in the related work " + cite("hybrid") + " (untested).",
          "Add the missing preprocessing (stemming or lemmatisation) and measure each feature block separately (L9).",
          "Try contextual embeddings as features, which the base paper found to add about three points of accuracy over TF-IDF " + cite("base") + " (untested here), possibly followed by the same PCA and Firefly steps to keep the classifier light.",
          "Treat PARTIALLY TRUE as an ordinal rather than a nominal class, using the six original labels (for example ordinal regression), because the errors follow the truthfulness scale (Chapter 8)."),
        H2("Improvements to the application"),
        B("Show the verdict, the calibrated probabilities and a warning when the confidence is below a chosen level.",
          "Replace the fixed wording about the demo corpus by text read from the loaded model (L10), and fix the true/false label parsing in load_csv (L11).",
          "Explain a verdict by listing the TF-IDF terms and stylometric features that contributed most, in the spirit of LIME and SHAP used by the base paper.",
          "Support more languages by language-specific stop-word and cue lists.",
          "Export and import of models with version information, and keep a history of retraining runs."),
        H2("Scalability and deployment"),
        B("Serve the backend with several worker processes behind a reverse proxy, add authentication and rate limits, and store models and retraining jobs outside the process (L12).",
          "Move retraining to a job queue so that long Firefly searches do not share the machine with the API.",
          "Run a load test and measure memory use; the model files are 0.85 MB (demo) and 12.6 MB (LIAR2, 3,000 documents) and load in a few seconds.",
          "Package the application as a container image for one-command deployment."),
        H2("Further research"),
        B("Evaluate on several datasets and across datasets (ISOT, LIAR-PLUS, article-level corpora) and measure the transfer from one to another.",
          "Combine the text classifier with evidence retrieval so that a claim is checked against sources, which is what the present approach cannot do (L2).",
          "Study which metaheuristics help text classification at all, with equal budgets and many seeds, since this report found no gain for one of them.",
          "Run a user study on whether readers understand and trust a three-level verdict with a confidence."),
    ]


def conclusion_blocks():
    return _conclusion_body()


def future_blocks():
    return _future_body()


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + renum(_conclusion_body(), "9")


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(_future_body(), "10")
