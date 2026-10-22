"""Chapter 8: Results and output screens. Every number is read from artifacts/metrics and experiments/*.json at build time."""

import json
import os

from .blocks import B, FIG, H1, H2, H3, P, TAB
from .refs import c
from . import facts as F

MODELS = ["logistic_regression", "random_forest", "xgboost"]
ACTION_NAME = {"quiz": "quiz", "content": "content", "forum": "forum", "homepage": "homepage (Visit course resources)", "continue_course": "continue_course"}


def _sweep():
    p = os.path.join(F.EXP, "threshold_sweep.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def _plot(name):
    return os.path.join(F.CODE, "artifacts", "plots", name)


def analysis():
    """Derived statements used in the prose and by the paper (computed, never typed)."""
    M = F.METRICS
    out = {}
    if not M:
        return out
    sel = M["selected_model"]
    ms = M["models"]
    s = _sweep() or {}
    pos = s.get("positive_rate", 0.4375)
    out["selected"] = sel
    out["selected_label"] = F.MODEL_LABEL[sel]
    out["majority_accuracy"] = 1 - pos
    out["positive_rate"] = pos
    out["best_auc_model"] = max(ms, key=lambda m: ms[m]["roc_auc"])
    out["worst_auc_model"] = min(ms, key=lambda m: ms[m]["roc_auc"])
    cm = ms[sel]["confusion_matrix"]
    out["cm"] = cm
    out["fp_rate"] = cm[0][1] / sum(cm[0])
    out["fn_rate"] = cm[1][0] / sum(cm[1])
    rec = F.REC["summary"]
    out["hybrid_p3"] = rec["hybrid (shipped)"]["p@3"]
    out["content_p3"] = rec["content-only (TF-IDF)"]["p@3"]
    out["pop_p3"] = rec["popularity (rating only)"]["p@3"]
    return out


def blocks():
    M, S, C, D, R, FB, AC, L, T, E = F.METRICS, F.SEEDS, F.CEIL, F.PROFILE, F.REC, F.FB, F.ACT, F.API_LAT, F.TESTS, F.ENV
    ms = M["models"]
    sel = M["selected_model"]
    A = analysis()
    sw = _sweep()
    P_ = M["policy_evaluation"]
    fair = M["fairness"]
    sizes = S["runs"][0]["sizes"]
    tr_n, va_n, te_n = M["train_samples"], M["val_samples"], M["test_samples"]
    summ = S["summary"]
    cm = ms[sel]["confusion_matrix"]
    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1 setup and data
    out += [
        H2("8.1 Experimental setup and data"),
        P("Every number in this chapter was produced by this project's own code on this project's own data and is read from `artifacts/metrics/model_metrics.json` (the shipped training run) "
          "or from `experiments/*.json` (re-runs and measurements made for this report by `scripts/run_experiments.py`, `scripts/threshold_sweep.py`, `scripts/measure_api.py` and `scripts/collect_env.py`). "
          "Nothing was copied from another study except where a table says so and cites it."),
        P("**The data are synthetic.** The training script `scripts/train_pipeline.py` probes the Open University Learning Analytics Dataset page " + c("oulad") +
          " but does not download or use it. It generates an OULAD-like table of learner-weeks with a fixed random seed (`synthetic-oulad-like-fallback-v1`). "
          "All model results below therefore describe how well the models recover a rule that this project's generator itself defined; they say nothing about real learners and no claim of external validity is made."),
        TAB("Dataset and split used in the shipped run (seed 42)", ["Item", "Value"], [
            ["Source", "`synthetic-oulad-like-fallback-v1` (generated; real OULAD never used)"],
            ["Learners x weeks", f"{D['learners']:,} learners x {D['weeks']} weeks = {D['rows']:,} learner-week rows"],
            ["Success rate (label = 1)", F.pct(D["success_rate"])],
            ["Observable features (8)", "cum_clicks, recent_clicks, quiz_count, forum_count, completions, engagement, weekly_hours, skill_code"],
            ["Logged action", ", ".join(f"{k} {v:,}" for k, v in D["action_counts"].items())],
            ["Split (learner level, 80/10/10)", f"train {tr_n:,} rows ({sizes['train_learners']:,} learners) / validation {va_n:,} / test {te_n:,} ({sizes['test_learners']} learners)"],
            ["Positive rate on the test split", F.pct(sizes["positive_rate_test"])],
            ["Environment", f"{E['cpu']} ({E['cores']} cores, {E['logical_processors']} threads), {E['ram_gb']} GB RAM, {E['gpu']}; Python {E['python']}, scikit-learn {E['packages']['scikit-learn']}, XGBoost {E['packages']['xgboost']}"],
        ], widths=[1.7, 4.6], size=10),
        P("The label is generated as `success = (assess_score >= 50) AND (U < 0.55 + 0.2 (assess_score - 50) / 50)` with U uniform noise, so it is noisy by construction. The assessment score itself is "
          "**not** one of the eight features the deployed model receives."),
    ]

    # ------------------------------------------------------------------ 8.2 model performance
    rows = []
    for m in MODELS:
        x = ms[m]
        rows.append([F.MODEL_LABEL[m] + (" (selected)" if m == sel else ""), F.f4(x["val_auc"]), F.f4(x["roc_auc"]), F.f4(x["accuracy"]), F.f4(x["precision"]), F.f4(x["recall"]), F.f4(x["f1"]), F.f4(x["brier"])])
    out += [
        H2("8.2 Success-prediction performance"),
        P("Three classifiers were trained on the same standardised features: logistic regression (`max_iter=1000`), a 200-tree random forest and a 300-tree XGBoost model " + c("xgboost", "breiman", "sklearn") +
          f" (depth 5, learning rate 0.05). The model with the highest **validation** AUC is saved as the deployed success model, which here is {F.MODEL_LABEL[sel]}. "
          f"All figures below are on the held-out test split of {te_n:,} learner-weeks ({sizes['test_learners']} learners never seen in training)."),
        TAB("Test-split results of the three success models (threshold 0.5)", ["Model", "Val AUC", "Test AUC", "Accuracy", "Precision", "Recall", "F1", "Brier"], rows,
            widths=[1.7, 0.6, 0.65, 0.7, 0.7, 0.6, 0.55, 0.55], size=9.5, align=["l", "c", "c", "c", "c", "c", "c", "c"]),
        FIG(F.fig("fig_model_comparison.png"), "Test AUC, F1 and Brier score of the three success models", 5.9),
        P(f"The ordering is Logistic Regression ({F.f3(ms['logistic_regression']['roc_auc'])}), XGBoost ({F.f3(ms['xgboost']['roc_auc'])}) and Random Forest ({F.f3(ms['random_forest']['roc_auc'])}). "
          f"An AUC of 0.5 is chance, so the discrimination is modest: about {F.f2(ms[sel]['roc_auc'])} for the deployed model. "
          f"The accuracy of {F.f3(ms[sel]['accuracy'])} must be read against the majority-class rate: a model that always predicted \"not success\" would be right {F.pct(A['majority_accuracy'])} of the time, "
          f"so the deployed model is only about {(ms[sel]['accuracy'] - A['majority_accuracy']) * 100:.1f} percentage points better than that trivial rule. "
          f"The Brier score ({F.f3(ms[sel]['brier'])} for logistic regression) is likewise close to what a constant prediction of the base rate would give ({A['positive_rate'] * (1 - A['positive_rate']):.3f})."),
        H3("Confusion matrices and ROC"),
        FIG(F.fig("fig_confusion_matrices.png"), "Confusion matrices of the three models on the test split at threshold 0.5", 6.0),
        P(f"For the deployed logistic regression the matrix is [[{cm[0][0]:,}, {cm[0][1]:,}], [{cm[1][0]:,}, {cm[1][1]:,}]]: {cm[0][0]:,} true negatives, {cm[0][1]} false positives, "
          f"{cm[1][0]} false negatives and {cm[1][1]} true positives. Recall is only {F.pct(ms[sel]['recall'])}: the model misses {F.pct(A['fn_rate'])} of the learner-weeks that did succeed, "
          f"while {F.pct(A['fp_rate'])} of the learner-weeks that did not succeed are wrongly flagged as likely successes. Random Forest has the highest recall ({F.pct(ms['random_forest']['recall'])}) "
          "but pays for it with the lowest precision and the worst calibration."),
        FIG(_plot("roc_curve.png"), "ROC curves of the three models on the test split (artifacts/plots/roc_curve.png, drawn by the training script)", 4.6),
        FIG(_plot("feature_importance.png"), "Absolute logistic-regression coefficients of the eight features (artifacts/plots/feature_importance.png)", 4.6),
        P("The feature plot reports absolute coefficients on standardised inputs because the selected model is logistic regression and has no tree importances. "
          "The recent-click, cumulative-click, engagement and skill-code features carry most of the weight; quiz count and completions carry almost none. These coefficients appear only in this plot and on the Diagnostics tab: because `predict_success()` returns importances only for models that have `feature_importances_`, the `contributing_features` field of the API and the corresponding list on the Insights page are empty for the deployed logistic regression."),
    ]

    # ------------------------------------------------------------------ 8.3 stability + ceiling
    rows = []
    for m in MODELS:
        s_ = summ[m]
        rows.append([F.MODEL_LABEL[m], f"{s_['test_auc']['mean']:.4f} +- {s_['test_auc']['std']:.4f}", f"{s_['test_auc']['min']:.4f} - {s_['test_auc']['max']:.4f}",
                     f"{s_['f1']['mean']:.4f} +- {s_['f1']['std']:.4f}", f"{s_['accuracy']['mean']:.4f}", f"{s_['brier']['mean']:.4f}"])
    cr = []
    for m in MODELS:
        cr.append([F.MODEL_LABEL[m], F.f4(C["shipped_features"][m]["test_auc"]), F.f4(C["with_assess_score"][m]["test_auc"]), F.f4(C["with_assess_score"][m]["accuracy"]), F.f4(C["with_assess_score"][m]["f1"])])
    out += [
        H2("8.3 Stability across seeds and the information ceiling"),
        P(f"The shipped run uses one seed, so a single AUC could be lucky. `scripts/run_experiments.py` re-generates the synthetic data and the learner split for {len(S['seeds'])} seeds "
          f"({', '.join(str(x) for x in S['seeds'])}) with the shipped settings, without overwriting the deployed artefacts. Seed 42 reproduces the shipped metrics exactly."),
        TAB(f"Test metrics over {len(S['seeds'])} seeds (mean +- standard deviation)", ["Model", "Test AUC", "AUC range", "F1", "Accuracy", "Brier"], rows,
            widths=[1.6, 1.3, 1.2, 1.2, 0.7, 0.6], size=9.5, align=["l", "c", "c", "c", "c", "c"]),
        FIG(F.fig("fig_seed_study.png"), "Test AUC of the three models for each of the six seeds", 5.0),
        P(f"The ranking is stable: logistic regression and XGBoost are within about {abs(summ['logistic_regression']['test_auc']['mean'] - summ['xgboost']['test_auc']['mean']):.3f} AUC of each other and both beat Random Forest on every seed. "
          f"Validation-AUC selection picked logistic regression on {S['selected_counts'].get('logistic_regression', 0)} seeds and XGBoost on {S['selected_counts'].get('xgboost', 0)}, so the choice of the deployed model is not decisive. "
          f"The mean test AUC of the deployed model family is {summ['logistic_regression']['test_auc']['mean']:.3f} (standard deviation {summ['logistic_regression']['test_auc']['std']:.3f}); a run takes about {S['runs'][0]['seconds']:.0f} s on this CPU."),
        H3("Why the AUC is only about 0.6"),
        P("To find out whether the weak result is a modelling flaw or a property of the data, the same pipeline was run with the hidden assessment score added as a ninth feature. "
          "The score is what the generator uses to decide success, so it shows how much of the label is recoverable at all."),
        TAB("Test AUC with and without the hidden assessment score (seed 42)", ["Model", "Shipped 8 features", "+ assessment score", "Accuracy (+ score)", "F1 (+ score)"], cr,
            widths=[1.6, 1.2, 1.3, 1.2, 1.0], size=9.5, align=["l", "c", "c", "c", "c"]),
        FIG(F.fig("fig_ceiling.png"), "Ceiling check: adding the hidden assessment score lifts AUC to about 0.8", 5.0),
        P("With the hidden score the logistic-regression AUC rises from "
          f"{F.f3(C['shipped_features']['logistic_regression']['test_auc'])} to {F.f3(C['with_assess_score']['logistic_regression']['test_auc'])}. The gap is the information the deployed features do not carry: "
          "a learner's click counts, quiz counts and engagement only weakly reveal the assessment outcome in this generator. The low AUC is therefore a property of the synthetic data, not a coding fault, "
          "and the same weak signal would not be expected, or assumed, on real learner logs."),
    ]

    # ------------------------------------------------------------------ 8.4 thresholds and parameters
    out += [H2("8.4 Threshold and parameter analysis")]
    if sw:
        rows = [[f"{r['threshold']:.2f}", f"{r['predicted_positive']:,}", F.f3(r["accuracy"]), F.f3(r["precision"]), F.f3(r["recall"]), F.f3(r["f1"])] for r in sw["sweep"]]
        best_f1 = max(sw["sweep"], key=lambda r: r["f1"])
        best_acc = max(sw["sweep"], key=lambda r: r["accuracy"])
        out += [
            H3("Decision threshold of the success model"),
            P("The deployed model turns a probability into a label at 0.5. `scripts/threshold_sweep.py` re-fits the logistic regression with the shipped settings on the same split (its confusion matrix at 0.5 matches the shipped one exactly) "
              "and sweeps the threshold. The recommender itself uses the probability, not the label, so this sweep matters only for reporting."),
            TAB("Logistic regression on the test split at different thresholds", ["Threshold", "Predicted success", "Accuracy", "Precision", "Recall", "F1"], rows,
                widths=[0.9, 1.2, 0.9, 0.9, 0.9, 0.9], size=10, align=["c"] * 6),
            P(f"Raising the threshold buys precision at the cost of recall: precision climbs from {F.f3(sw['sweep'][0]['precision'])} at {sw['sweep'][0]['threshold']:.2f} to {F.f3(sw['sweep'][-1]['precision'])} at {sw['sweep'][-1]['threshold']:.2f}, "
              f"but only {sw['sweep'][-1]['predicted_positive']} of {sw['test_rows']:,} rows are then flagged. Accuracy is highest at {best_acc['threshold']:.2f} ({F.f3(best_acc['accuracy'])}) and F1 is highest at {best_f1['threshold']:.2f} ({F.f3(best_f1['f1'])}), "
              f"where the model flags {best_f1['predicted_positive']:,} of {sw['test_rows']:,} rows and recall is {F.f3(best_f1['recall'])}. That F1 gain is mostly the effect of predicting success almost everywhere; "
              f"accuracy at that threshold ({F.f3(best_f1['accuracy'])}) is below the majority-class rate of {F.f3(A['majority_accuracy'])}. The default 0.5 is the accuracy-maximising choice and is kept."),
        ]
    keys = [k for k in R["ablation_drop_one_term"] if k != "full"]
    ab = R["ablation_drop_one_term"]
    rows = [["none (full score)", "1.00", F.f3(ab["full"]["p@3"]), F.f2(ab["full"]["p@5"]), "1.00"]]
    for k in keys:
        rows.append([k, F.f2(R["weights"][k]), F.f3(ab[k]["p@3"]), F.f2(ab[k]["p@5"]), F.f2(ab[k]["top3_overlap_with_full"])])
    helpful = [k for k in keys if ab[k]["p@3"] < ab["full"]["p@3"] - 1e-9]
    harmful = [k for k in keys if ab[k]["p@3"] > ab["full"]["p@3"] + 1e-9]
    neutral = [k for k in keys if abs(ab[k]["p@3"] - ab["full"]["p@3"]) <= 1e-9]
    out += [
        H3("Weights of the hybrid score"),
        P("The ranker adds eight terms with fixed weights chosen by hand (0.30, 0.15, 0.15, 0.12, 0.10, 0.08, 0.05, 0.05); no weight search or learning was done. "
          "To see what each term contributes, each one was removed in turn and the remaining score was ranked again for the 10 personas of Section 8.5 (P@3 and P@5 against the author-defined relevant categories; "
          "the last column is how many of the full score's top three survive)."),
        TAB("Drop-one-term ablation of the hybrid score (mean over 10 personas)", ["Term removed", "Weight", "P@3", "P@5", "Top-3 overlap"], rows,
            widths=[1.8, 0.8, 0.9, 0.9, 1.2], size=10, align=["l", "c", "c", "c", "c"]),
        FIG(F.fig("fig_ablation.png"), "Mean P@3 after removing each term of the hybrid score", 5.0),
        P(f"Removing {', '.join(helpful)} lowers P@3, so these terms help on this persona set; removing {', '.join(harmful)} *raises* P@3 slightly, which means those terms, as weighted, do not help here; "
          f"removing {', '.join(neutral)} changes nothing at the top of the list. The topic-overlap and content terms matter most (P@3 falls from {F.f3(ab['full']['p@3'])} to {F.f3(ab['topic']['p@3'])} and {F.f3(ab['content']['p@3'])}). "
          "The success, behaviour, goal and engagement terms leave P@3 unchanged because, for a fresh persona, they are nearly constant across courses; their job is to react to a learner's history (Section 8.6), which this static test cannot show."),
        H3("Settings that were not varied"),
        B("**Importance weights and propensities** in the offline policy evaluation: propensities are clipped to [0.02, 0.98] and importance weights are capped at 10. These were fixed in the training script and not swept, so the sensitivity of the IPS, SNIPS and doubly robust values to them is unknown.",
          "**Behavioural boost** limits (-0.3 to 0.35) and the event weights (view 0.05 ... complete 0.20, dismiss -0.25) are hand-set constants and were not tuned.",
          "**TF-IDF** uses `max_features=2000` and English stop words, fitted on the learner text and the 24 course texts at every request; no vocabulary or n-gram setting was compared.",
          "**Model hyper-parameters** (random-forest and XGBoost depth, trees, learning rate) were fixed, not searched."),
    ]

    # ------------------------------------------------------------------ 8.5 persona evaluation
    rs = R["summary"]
    per = R["per_persona"]
    rows = [[k.replace(" (rating only)", "").replace(" (TF-IDF)", "").replace(" (shipped)", ""), F.f2(v["p@1"]), F.f3(v["p@3"]), F.f2(v["p@5"]), F.f3(v["mrr"])] for k, v in rs.items()]
    rows2 = [[p["persona"], p["skill"], ", ".join(p["relevant_categories"]), str(p["relevant_courses"]), ", ".join(p["top3_hybrid"]), F.f2(p["hybrid (shipped)"]["p@3"]), F.f2(p["content-only (TF-IDF)"]["p@3"])] for p in per]
    below = [p["persona"] for p in per if p["hybrid (shipped)"]["p@3"] < p["content-only (TF-IDF)"]["p@3"] - 1e-9]
    out += [
        H2("8.5 Recommendation quality on a persona check"),
        P(f"The project has no log of real learners choosing real courses, so precision and recall against real feedback could not be measured (objective 6 is therefore only partly met). "
          f"As a sanity check, {R['personas']} learner personas were written by the authors, each with the course *categories* that would be relevant to them, and these expected sets were written down before any ranking was run. "
          f"A course counts as relevant when its category is in the persona's set; the catalog has {R['catalog_size']} courses. Three rankers were compared: popularity (rating only), content-only TF-IDF similarity, and the shipped hybrid score."),
        TAB("Precision@k and MRR over 10 personas", ["Ranker", "P@1", "P@3", "P@5", "MRR"], rows, widths=[2.2, 0.8, 0.8, 0.8, 0.8], size=10.5, align=["l", "c", "c", "c", "c"]),
        FIG(F.fig("fig_persona_precision.png"), "P@1, P@3, P@5 and MRR of the three rankers on the persona check", 5.4),
        P(f"Both personalised rankers are far better than popularity (P@3 {F.f3(rs['popularity (rating only)']['p@3'])} against {F.f3(rs['content-only (TF-IDF)']['p@3'])} and {F.f3(rs['hybrid (shipped)']['p@3'])}), "
          f"and both put a relevant course first for every persona (MRR 1.00). **The hybrid score does not beat content-only TF-IDF on this check**: its P@3 is {F.f3(rs['hybrid (shipped)']['p@3'])} against {F.f3(rs['content-only (TF-IDF)']['p@3'])}, "
          f"and its P@5 is {F.f2(rs['hybrid (shipped)']['p@5'])} against {F.f2(rs['content-only (TF-IDF)']['p@5'])}. The extra terms (rating, skill fit, success estimate, engagement) pull a few generally popular or beginner-level courses into the top three for "
          f"{len(below)} personas ({', '.join(below)}). What the hybrid adds is behaviour that content-only ranking cannot have: cold-start-safe fallbacks and adaptation to a learner's own events, shown next."),
        TAB("Persona-by-persona result (hybrid vs content-only P@3)", ["Persona", "Skill", "Relevant categories", "Rel. courses", "Hybrid top 3", "Hyb. P@3", "Cont. P@3"], rows2,
            widths=[1.2, 0.8, 1.2, 0.5, 1.3, 0.45, 0.45], size=8, align=["l", "l", "l", "c", "l", "c", "c"]),
        P("These numbers are a sanity check on a 24-course catalog with ten hand-written personas. They are not a user study, the relevance labels are category-level and chosen by the authors, and the differences "
          "between the two personalised rankers (one or two courses for a few personas) are far too small to rank them statistically."),
    ]

    # ------------------------------------------------------------------ 8.6 feedback loop
    tr = FB["tracked"]
    rows = [[cid, str(v["rank_before"]), str(v["rank_after"]), F.f4(v["score_before"]), F.f4(v["score_after"])] for cid, v in tr.items()]
    ev = ", ".join(f"{e[1]} {e[0]}" for e in FB["events"])
    out += [
        H2("8.6 Adaptation to learner feedback"),
        P(f"The main behavioural claim of the system is that ranking changes as a learner acts. For one persona (Beginner; interests python, data science, machine learning) six events were logged through the same code path as the API: {ev}. "
          "The ranking was recomputed before and after."),
        TAB("Effect of six events on three tracked courses", ["Course", "Rank before", "Rank after", "Score before", "Score after"], rows, widths=[1.2, 1.1, 1.1, 1.2, 1.2], size=10.5, align=["c"] * 5),
        P(f"The top three changes from {', '.join(FB['top3_before'])} to {', '.join(FB['top3_after'])}: the dismissed course (DA101) falls from rank {tr['DA101']['rank_before']} to {tr['DA101']['rank_after']} and is replaced in the top three, "
          f"while ML101, on which the learner started, took two quizzes and finished, rises in score from {F.f3(tr['ML101']['score_before'])} to {F.f3(tr['ML101']['score_after'])}. "
          f"The estimated success probability moves from {F.f3(FB['p_success_before'])} to {F.f3(FB['p_success_after'])} and the engagement label from {FB['engagement_before']['label']} to {FB['engagement_after']['label']} "
          f"(score {FB['engagement_before']['score']:.2f} to {FB['engagement_after']['score']:.2f}). Ranking adapts at once, without retraining, because the behavioural term and the engagement features are recomputed from the interaction table on every request."),
    ]

    # ------------------------------------------------------------------ 8.7 action benefit
    ub, ua = FB["uplift_before"], FB["uplift_after"]
    rows = [[ACTION_NAME[a], f"{ub[a]:+.4f}", f"{ua[a]:+.4f}"] for a in F.ACTIONS]
    cnt = AC["best_action_counts"]
    out += [
        H2("8.7 Estimated action benefit"),
        P("Beside the ranking, the application shows an estimated benefit for five learner actions (quiz, content, forum, homepage visit, continue course). It comes from a one-vs-rest T-learner " + c("kunzel", "uplift") +
          ": two logistic regressions per action, one fitted on learner-weeks where the action was taken and one where it was not, and the benefit is the difference of their predicted success probabilities. "
          "The interface calls it an estimate from observed patterns, not a proven causal effect, and the data support that caution."),
        TAB("Estimated benefit of each action for the persona of Section 8.6", ["Action", "Before six events", "After six events"], rows, widths=[2.6, 1.6, 1.6], size=10.5, align=["l", "c", "c"]),
        FIG(F.fig("fig_feedback_loop.png"), "Estimated action benefit before and after six events (left) and the scores of the three tracked courses (right)", 5.9),
        P(f"After only six events the sign of several estimates flips: the estimated benefit of a quiz goes from {ub['quiz']:+.3f} to {ua['quiz']:+.3f}, and the best action changes from {FB['best_action_before']} to {FB['best_action_after']}. "
          f"Across a grid of {AC['grid_states']} learner states (three skill levels x weekly hours of 2, 6 and 12 x 0, 5, 15, 40 and 80 logged interactions) the best action is {', '.join(f'{ACTION_NAME[k]} in {v}' for k, v in cnt.items())} states, "
          f"and the predicted success probability ranges from {F.f3(AC['p_success_min'])} to {F.f3(AC['p_success_max'])} (mean {F.f3(AC['p_success_mean'])}). "
          "Two consequences follow. First, the estimates extrapolate from a confounded synthetic log and should not guide real decisions. "
          "Second, the suggested action depends only on the learner's state, not on the course, so every card in one learner's list shows the same suggested action (visible on the recommendation cards in Section 8.12)."),
    ]

    # ------------------------------------------------------------------ 8.8 OPE
    out += [
        H2("8.8 Offline policy evaluation"),
        P("To ask whether following the highest-benefit action would have helped, the training script estimates the value of that policy on the logged test rows with three off-policy estimators " + c("dudik", "imbens") +
          f": inverse propensity scoring (IPS), self-normalised IPS (SNIPS) and the doubly robust estimator (DR). The behaviour policy is a multinomial logistic regression over the five actions, propensities are clipped to {P_['clipping']}, "
          f"importance weights are capped at {P_['weight_cap']}, and the reward is the observed success."),
        TAB("Offline policy value estimates on the test split", ["Quantity", "Value"], [
            ["IPS", F.f4(P_["ips"])], ["SNIPS", F.f4(P_["snips"])], ["Doubly robust", F.f4(P_["doubly_robust"])],
            ["Effective sample size of the importance weights", f"{P_['effective_sample_size']} of {P_['test_samples']:,} rows"],
            ["Logged success rate on the same rows", F.f4(sizes["positive_rate_test"])],
        ], widths=[3.6, 2.0], size=10.5, align=["l", "c"]),
        P(f"These values must not be read as a gain. The IPS value ({F.f3(P_['ips'])}) and the SNIPS value ({F.f3(P_['snips'])}) disagree by a factor of about {P_['snips'] / P_['ips']:.0f}, and the effective sample size is only {P_['effective_sample_size']} of {P_['test_samples']:,} rows: "
          "a handful of rows carry the whole estimate. The SNIPS value happens to be above the logged success rate and the DR value below it, so even the sign of the apparent effect depends on the estimator. "
          "The honest reading is that the logged data do not support any conclusion about the action policy; a live randomised test would be needed."),
    ]

    # ------------------------------------------------------------------ 8.9 fairness
    rows = []
    for k, v in fair["age_band"].items():
        rows.append([f"age band {k}", f"{v['n']:,}", F.pct(v["success_rate"]), F.pct(v["avg_predicted"]), F.f3(v["f1"])])
    for k, v in fair["gender"].items():
        rows.append([f"gender {k}", f"{v['n']:,}", F.pct(v["success_rate"]), F.pct(v["avg_predicted"]), F.f3(v["f1"])])
    old = fair["age_band"]["55<="]
    young = fair["age_band"]["0-35"]
    out += [
        H2("8.9 Fairness audit"),
        P("The training script reports the deployed model's behaviour by age band and gender on the test split. This is an audit only: no mitigation is applied, and the groups come from the synthetic generator."),
        TAB("Success model by group (test split)", ["Group", "Learner-weeks", "Observed success", "Mean predicted", "F1"], rows, widths=[1.6, 1.2, 1.2, 1.2, 0.8], size=10.5, align=["l", "c", "c", "c", "c"]),
        FIG(F.fig("fig_fairness.png"), "Observed success rate, mean predicted probability and F1 by age band and gender", 5.4),
        P(f"The gender groups are close (F1 {F.f3(fair['gender']['F']['f1'])} and {F.f3(fair['gender']['M']['f1'])}). The oldest age band stands out: its F1 is {F.f3(old['f1'])} against {F.f3(young['f1'])} for the youngest, and the model "
          f"over-predicts its success ({F.pct(old['avg_predicted'])} predicted against {F.pct(old['success_rate'])} observed) on only {old['n']} learner-weeks. With a group this small the gap could be partly noise, "
          "but it is the pattern an audit exists to flag. The base paper also reports a weaker policy value for older learners on real data (SNIPS 0.139) " + c("base") + "."),
    ]

    # ------------------------------------------------------------------ 8.10 performance and tests
    ep = L["endpoints"]
    keys = ["GET /api/health", "GET /api/courses", "GET /api/courses/{id}", "GET /api/recommendations?top_n=8", "GET /api/recommendations?top_n=24", "GET /api/learning-path", "GET /api/insights", "GET /api/activity", "GET /api/metrics",
            "POST /api/auth/login", "PUT /api/profile", "POST /api/auth/register"]
    rows = [[k, str(ep[k]["n"]), f"{ep[k]['mean_ms']:.1f}", f"{ep[k]['median_ms']:.1f}", f"{ep[k]['p95_ms']:.1f}"] for k in keys]
    r8 = ep["GET /api/recommendations?top_n=8"]
    out += [
        H2("8.10 Performance and testing"),
        P(f"`scripts/measure_api.py` calls the running service on the loopback address (127.0.0.1) with a freshly registered account, after a warm-up. It uses the real model bundle and the real SQLite file. "
          f"Environment: {E['cpu']}, {E['ram_gb']} GB RAM, no GPU."),
        TAB("API latency in milliseconds", ["Endpoint", "n", "Mean", "Median", "p95"], rows, widths=[3.0, 0.5, 0.8, 0.8, 0.8], size=9.5, align=["l", "c", "c", "c", "c"]),
        P(f"A ranked list of eight courses takes {r8['mean_ms']:.1f} ms on average (p95 {r8['p95_ms']:.1f} ms). "
          "Recommendations are recomputed on every call, including fitting TF-IDF over 25 short documents and scoring 24 courses; there is no cache. The first registration is slow "
          f"({ep['POST /api/auth/register']['mean_ms']:.0f} ms) because it includes password hashing. The measurement is a single client making 30 sequential requests: it says nothing about concurrent load."),
        TAB("Automated checks", ["Check", "Result"], [
            ["pytest (`tests/test_app.py`)", f"{T['pytest']['passed']} of {T['pytest']['collected']} passed in {T['pytest']['seconds']} s ({', '.join(T['pytest']['tests'])})"],
            ["Smoke test (`scripts/smoke_test.py`, through the Vite proxy)", f"{T['smoke']['passed']} of {T['smoke']['checks']} checks passed"],
            ["Responsive check (`scripts/check_responsive.py`, Chrome)", f"11 screens x {len(T['responsive']['widths_px'])} widths ({'/'.join(str(w) for w in T['responsive']['widths_px'])} px) x light and dark: no horizontal overflow, no console errors, no failed requests"],
        ], widths=[2.6, 3.7], size=10, align=["l", "l"]),
    ]

    # ------------------------------------------------------------------ 8.11 base paper
    base_auc, base_snips = 0.795, 0.619
    out += [
        H2("8.11 Comparison with the base paper"),
        P("The base paper " + c("base") + " studies personalised learning-path optimisation on the real OULAD data " + c("oulad") + ". This project borrows three of its components (uplift scoring, off-policy evaluation, a fairness audit) "
          "and applies them to synthetic data with a much smaller model set. The two sets of numbers are therefore **not comparable** and the table is context, not a ranking."),
        TAB("Base paper and this project", ["Aspect", "Base paper", "This project"], [
            ["Data", "Real OULAD: 32,593 enrolments, about 1.7 million learner-week rows, 25,516 learners", f"Synthetic OULAD-like table: {D['rows']:,} learner-week rows, {D['learners']:,} learners; real OULAD never used"],
            ["Outcome model", f"XGBoost, AUC {base_auc}, Brier 0.074", f"{F.MODEL_LABEL[sel]}, AUC {F.f3(ms[sel]['roc_auc'])} (six-seed mean {summ['logistic_regression']['test_auc']['mean']:.3f}); XGBoost {F.f3(ms['xgboost']['roc_auc'])}; Brier {F.f3(ms[sel]['brier'])}"],
            ["Action benefit", "Uplift / treatment-effect scoring for learning actions", "One-vs-rest T-learner over five actions (two logistic regressions each)"],
            ["Policy learning", "Actor-Critic reinforcement-learning agent with causal regularisation; fitted Q-iteration baseline", "**Not implemented**: greedy argmax of estimated benefit only"],
            ["Policy evaluation", f"Greedy-Uplift SNIPS 0.619 (95% interval 0.613 to 0.625) against a logged pass rate of 0.589; IPS 9.956 vs SNIPS 0.643 shown to expose IPS instability", f"IPS {F.f3(P_['ips'])}, SNIPS {F.f3(P_['snips'])}, DR {F.f3(P_['doubly_robust'])}; effective sample size {P_['effective_sample_size']}; logged rate {F.f3(sizes['positive_rate_test'])}; **not evidence of gain**"],
            ["Fairness", "Audit with weaker results for older learners (SNIPS 0.139)", f"Audit by age band and gender; F1 {F.f3(old['f1'])} for the oldest band against {F.f3(young['f1'])} for the youngest"],
            ["Recommendation layer", "Learning-path recommendation as a policy", "Eight-term hybrid ranker, learning path ordered by skill level then score, explanations on every card"],
            ["Deliverable", "Research study", "Working web application with login, profile, catalog, dashboard, insights, analytics and tests"],
            ["Hardware", "Intel i7-6600U, 16 GB", f"{E['cpu']}, {E['ram_gb']} GB, no GPU"],
        ], widths=[1.1, 2.6, 2.7], size=8.5),
        P(f"Two points need saying plainly. First, the base paper's AUC of {base_auc} comes from real learner behaviour; this project's {F.f3(ms[sel]['roc_auc'])} comes from a generator whose label is only weakly tied to the eight features, "
          f"so a difference of about {base_auc - ms[sel]['roc_auc']:.2f} AUC says nothing about which method is better. Second, the base paper's SNIPS value of {base_snips} is reported with a confidence interval and an agent that was trained to maximise it; "
          f"this project's SNIPS value of {F.f3(P_['snips'])} rests on an effective sample size of {P_['effective_sample_size']} and is no evidence at all."),
    ]

    # ------------------------------------------------------------------ 8.12 output screens
    def shot(fn, cap, w=5.8):
        p = F.shot_view(fn)
        return FIG(p, cap, F.shot_w(p, w))

    out += [
        H2("8.12 Output screens"),
        P("The screens below are captures of the running React front end at 1440 x 900 pixels. They were taken with real data: one registered learner (display name \"Capture Learner\") who filled in the profile form "
          "and then generated 12 interaction events (opens, saves, dismissals, quizzes, a discussion and a completion) through the interface. "
          "Every figure on these pages, including the 43% estimated success and the 0.244 estimated benefit, was computed by the backend for that learner; nothing is mocked."),
        shot("03_login.png", "Sign-in screen with the statement that suggestions ship with their reasons"),
        shot("05_catalog.png", "Public course catalog: 24 courses with category, level, duration, rating and search and filter controls"),
        shot("06_profile_first_run.png", "Learner profile form filled in during onboarding (education, skill level, learning style, weekly hours, interests, topics, goals, preferences, age band)"),
        shot("07_dashboard.png", "Dashboard after 12 events: learning status (Highly engaged, score 75%), estimated success 43%, 12 interactions, 2 quizzes, the recommended next action and recent activity"),
        shot("08_recommendations.png", "Ranked recommendations: match percentage, estimated success, a three-part explanation, the suggested action and the View, Start and Dismiss buttons"),
        shot("09_learning_path.png", "Staged learning path: beginner courses first, each step with match percentage and estimated benefit, and the next best action"),
        shot("10_insights.png", "Insights: engagement, estimated success and risk, strengths, attention points and the estimated benefit of each of the five actions"),
        shot("14_course_detail.png", "Course detail for Machine Learning Basics with the \"Why it is recommended\" panel (57% match, estimated success 43%, suggested action) and the progress buttons"),
        shot("17_analytics_diagnostics.png", "Model analytics, Diagnostics tab: confusion matrices of the three models on the test split"),
        shot("18_analytics_policy.png", "Model analytics, Offline policy tab: IPS 0.009, SNIPS 0.665 and doubly robust 0.435 with the statement that this is not a live A/B result"),
        P("Three observations follow from the screens. The dashboard, recommendation cards, course page and insights page all quote the same 43% success estimate, because that value depends on the learner's state, not on the course. "
          "All recommendation cards show the same suggested action (Visit course resources, estimated benefit 0.244), which confirms the finding of Section 8.7. And the analytics pages show the same numbers as Tables in this chapter, "
          "because they read `artifacts/metrics/model_metrics.json` directly."),
    ]

    # ------------------------------------------------------------------ 8.13 limits
    out += [
        H2("8.13 Limitations of the results"),
        B("All model results come from a synthetic generator; they measure recovery of a rule written by the authors, not behaviour of real learners, and the real OULAD data were never used.",
          f"The success model's discrimination is modest (AUC about {F.f2(ms[sel]['roc_auc'])}) and its accuracy is only a few points above the majority-class rate.",
          "The recommendation check uses 10 author-written personas and category-level relevance on 24 courses; it is not a user study, and precision and recall against real learner feedback were not measured.",
          "The hybrid score did not beat content-only TF-IDF on that check, and its eight weights were set by hand and never tuned.",
          f"The offline policy values rest on an effective sample size of {P_['effective_sample_size']} and are not evidence that the action policy helps.",
          "Estimated action benefits are unstable (they change sign after a few events) and are not causal effects.",
          "Latency was measured with one client on one machine; no load test, cross-browser test or penetration test was done.",
          "No live A/B test was run."),
    ]
    return out
