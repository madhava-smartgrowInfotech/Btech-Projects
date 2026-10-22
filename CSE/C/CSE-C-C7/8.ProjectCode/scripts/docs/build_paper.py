"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for batch C7 (LearnPathIQ).
Every number is read from artifacts/metrics/model_metrics.json and experiments/*.json (via facts.py).

    python -m scripts.docs.build_paper
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper
from .refs import K


def r(*keys):
    """Citation marker; Paper.expand numbers references by first appearance."""
    return "{r:" + ",".join(str(K[k]) for k in keys) + "}"


def crop_shot(name, out, box=(0, 0, 1440, 900)):
    p = os.path.join(F.FIGS, out)
    Image.open(F.shot(name)).convert("RGB").crop(box).save(p)
    return p


def build(path):
    M, S, C, R, FB, D, E = F.METRICS, F.SEEDS, F.CEIL, F.REC, F.FB, F.PROFILE, F.ENV
    api = F.API_LAT["endpoints"]
    lr, rf, xg = (M["models"][k] for k in ("logistic_regression", "random_forest", "xgboost"))
    sm = S["summary"]
    pol = M["policy_evaluation"]
    rs = R["summary"]
    pop, con, hyb = rs["popularity (rating only)"], rs["content-only (TF-IDF)"], rs["hybrid (shipped)"]
    ab = R["ablation_drop_one_term"]
    fa = M["fairness"]
    rec = api["GET /api/recommendations?top_n=8"]
    f3, f2, pct = F.f3, F.f2, F.pct
    cat_n = len(F.CATALOG)
    cats = len({c["category"] for c in F.CATALOG})
    T = F.TESTS

    P = Paper()
    authors = [[n.title(), f"Roll No. {rn}", "Dept. of Computer Science and Engineering", f"{F.COLLEGE}, {F.CITY}", "[email address]"] for n, rn in F.STUDENTS]
    authors.append([F.GUIDE.title(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", f"{F.COLLEGE}, {F.CITY}", "[email address]"])
    P.title_block("LearnPathIQ: Hybrid Personalized Course Recommendation with Learner-Success Prediction and Action-Benefit Estimation", authors)
    P.begin_two_columns()

    P.abstract(
        "Learners on online platforms face large catalogues and little guidance, and popularity-ranked lists ignore who is asking. This paper presents LearnPathIQ, "
        "a web application that ranks a 24-course catalogue for each learner with an eight-term hybrid score (TF-IDF content similarity, skill and topic fit, goal match, "
        "rating, a behavioural boost from logged events, an engagement score and a predicted success probability), orders the result into a staged learning path, and "
        "attaches an estimated benefit for five study actions using a one-vs-rest uplift model. The success model is trained on a synthetic OULAD-like dataset of 2,200 learners "
        f"over 12 weeks; the real OULAD data were not used. The selected logistic regression reaches a test AUC of {f3(lr['roc_auc'])} (six-seed mean {f3(sm['logistic_regression']['test_auc']['mean'])}), "
        f"which is modest. On ten hand-written learner personas the hybrid reaches precision@3 of {f2(hyb['p@3'])} against {f2(pop['p@3'])} for a popularity baseline, but does not beat "
        f"content-only TF-IDF ({f2(con['p@3'])}). Offline policy estimates rest on an effective sample size of {pol['effective_sample_size']:.1f} and are not evidence of gain. "
        "No user study was run and collaborative filtering across learners is not implemented.",
        ["course recommendation", "e-learning", "hybrid recommendation", "learning analytics", "offline policy evaluation", "personalization", "uplift modelling"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Online learning platforms list hundreds of courses, and a learner who is new to a field cannot tell which one fits their level, interests and goal. Catalogue search and "
           f"popularity ranking are the usual answer, but they return the same list to everyone and ignore what the learner does next. Dropout is a long-standing problem on such platforms {r('gharahighehi')}, "
           f"and recent work argues that guidance should move from predicting who will fail to prescribing what to do next {r('base')}.")
    P.para(f"Course recommendation has been approached with collaborative filtering and graph models {r('lightgcn')}, text embeddings {r('khreis')}, TF-IDF similarity {r('eduguide', 'tfidf')} and reinforcement learning {r('hrl')}. "
           "Each needs something a new project rarely has: a large interaction log, a trained language model or a simulator. A small institution or a student project has a short "
           "catalogue, no log and a learner who arrives with only a profile, yet still needs a ranking that explains itself and that reacts when the learner clicks, starts or dismisses a course.")
    P.para("This paper reports LearnPathIQ and what was measured on it. Its contributions are: (1) a transparent eight-term hybrid score that works from the first visit and adapts after every "
           "logged event without retraining; (2) a learner-success model and a one-vs-rest uplift model that attach a success estimate and an estimated action benefit to every recommendation, "
           "following the base paper's prediction-to-prescription idea at small scale; (3) an offline policy evaluation and a fairness audit that are reported with their weaknesses; and "
           "(4) a tested FastAPI and React application. Section II reviews related work, Section III gives the method, Section IV the results and Section V concludes.")
    P.para("The project set six objectives: (1) build learner profiles from education, skill level, interests, goals and weekly hours; (2) assemble a course catalogue with level, topic, tags and rating; "
           "(3) apply collaborative filtering; (4) apply content-based filtering; (5) combine them into a hybrid ranker with a learning path; and (6) evaluate with precision, recall and learner feedback. "
           "Section V states which were met; objective 3 was not implemented and objective 6 was met only in part.")
    P.sub("A", "System Hardware")
    P.para(f"All training and timing ran on one desktop: {E['cpu'].replace('(R)', '').replace('(TM)', '')} ({E['cores']} cores, {E['logical_processors']} threads), {E['ram_gb']} GB RAM, "
           "no GPU, Windows 11. The application and the load measurements shared that machine, so the latencies below are loopback figures.")
    P.sub("B", "Software Requirements")
    pk = E["packages"]
    P.para(f"Python {E['python']}, scikit-learn {pk['scikit-learn']} {r('sklearn')}, XGBoost {pk['xgboost']} {r('xgboost')}, pandas {pk['pandas']}, FastAPI {pk['fastapi']} {r('fastapi')}, "
           f"SQLAlchemy {pk['sqlalchemy']}, Pydantic {pk['pydantic']}, Node.js {E['node'].lstrip('v')} with React 19 and Vite, SQLite storage, and pytest and Playwright for testing.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Isiwu, Nnadi and Watanobe {r('base')} frame learning-path optimisation for MOOCs as prediction followed by prescription. On the Open University Learning "
           f"Analytics Dataset (OULAD) {r('oulad')}, with 32,593 enrolments and 25,516 learners, they train XGBoost to predict success (AUC 0.795, Brier 0.074), estimate heterogeneous "
           f"action effects with uplift models {r('uplift', 'kunzel')}, choose actions with a causally regularised Actor-Critic agent, and judge the policies offline with IPS, self-normalised IPS "
           f"and doubly robust estimators {r('dudik')}. Their greedy-uplift policy reaches a SNIPS value of 0.619, against a logged pass rate of 0.589, and the paper reports that older learners "
           "fare worst (SNIPS 0.139). It also shows IPS and SNIPS can differ by an order of magnitude (9.956 against 0.643) when weights are heavy-tailed, reports that its SNIPS value moves from 0.603 "
           "to between 0.625 and 0.642 as the causal-regularisation weight is varied, and finds that a fitted-Q-iteration baseline scores close to zero (IPS about 0.0039, SNIPS about 0.0010). "
           "Their measurements ran on a laptop-class machine (i7-6600U, 16 GB). Two things make this paper a natural starting point for a smaller system: the pipeline is built from components "
           f"(a success model, an uplift model, an offline estimator, a fairness audit) that can be reproduced without a cluster, and the authors state their limits openly. Causal estimates from an "
           f"observational log rest on assumptions such as ignorability {r('imbens')}, a caveat that carries over to this work.")
    P.para(f"**Embedding and text methods.** Khreis et al. {r('khreis')} fine-tune BERT with a contrastive loss and an isotropy regulariser to rank more than 500 university courses for a text query. "
           f"EduGuide {r('eduguide')} combines TF-IDF cosine similarity {r('tfidf')} with course ratings in a weighted score on a Coursera dataset. These approaches work from the first query but do not "
           "use what the learner later does.")
    P.para(f"**Interaction-based methods.** LightGCN {r('lightgcn')} simplifies graph convolution for collaborative filtering; Gharahighehi et al. {r('gharahighehi')} add survival analysis to collaborative "
           f"filtering to use time-to-dropout and time-to-completion on three public MOOC datasets. Both need a log of many learners. Hierarchical reinforcement learning {r('hrl')}, "
           f"knowledge-tracing agents {r('lpnav')} and neural path generators {r('saito')} personalise sequences, again from large logs or simulators.")
    P.para(f"**Personalisation and cold start.** Yu et al. {r('yu')} survey AI-powered personalisation in MOOCs, and retrieval-augmented generation has been proposed for cold-start MOOC "
           f"recommendation {r('ramo')}. The gap this paper addresses is the small-scale case: a short catalogue, no cross-learner log and a need for explanations, where a transparent score plus a "
           "success estimate and an estimated action benefit can be built, tested and measured honestly.")
    P.table("Related work compared with this paper",
            ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [[f"Base {r('base')}", "XGBoost success + uplift + Actor-Critic + OPE", "OULAD, 25,516 learners", "AUC 0.795; SNIPS 0.619", "Observational log; older learners 0.139"],
             [r("khreis"), "BERT, contrastive + isotropy loss", "500+ uOttawa courses", "Better separation than vanilla BERT", "Text query only; no feedback"],
             [r("gharahighehi"), "Collaborative filtering + survival analysis", "3 public MOOC datasets", "Beats CF baselines on 2 measures", "Needs cross-learner log"],
             [r("lightgcn"), "Graph convolution for CF", "Benchmark interaction graphs", "See source", "Needs interaction graph"],
             [r("eduguide"), "TF-IDF + rating weighted score", "Coursera course data", "See source", "No learner state or outcome"],
             [r("hrl"), "Hierarchical RL", "MOOC logs", "See source", "Large logs required"],
             ["This paper", "8-term hybrid + LR success + T-learner", "Synthetic OULAD-like, 24 courses", f"AUC {f3(lr['roc_auc'])}; P@3 {f2(hyb['p@3'])}", "Synthetic; no user study"]],
            widths=[0.55, 0.85, 0.7, 0.7, 0.6], size=6.5)

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Data")
    P.para(f"The real OULAD was not downloaded or used. The training script generates a reproducible OULAD-like fallback (seed 42): {D['learners']:,} learners over {D['weeks']} weeks, {D['rows']:,} learner-week rows, "
           f"eight observable features (cumulative and recent clicks, quiz count, forum count, completions, engagement, weekly hours, skill level) and a hidden assessment score. The label is "
           f"success = assessment score of at least 50 and a noise draw, with a {pct(D['success_rate'])} positive rate; learners are split 80/10/10, so the test split holds 220 learners and "
           f"{M['test_samples']:,} learner-weeks. In the generator the label is success = (score >= 50) and (U < 0.55 + 0.2 (score - 50)/50) with U uniform noise, so the label is noisy by design and the "
           f"score is not an input to the deployed model. Correlations with success are small: recent clicks {f3(D['corr_with_success']['recent_clicks'])}, engagement {f3(D['corr_with_success']['engagement'])}, cumulative clicks "
           f"{f3(D['corr_with_success']['cum_clicks'])}, skill level {f3(D['corr_with_success']['skill_code'])} and forum count {f3(D['corr_with_success']['forum_count'])}. The logged actions are quiz ({D['action_counts']['quiz']:,}), "
           f"content ({D['action_counts']['content']:,}), continue course ({D['action_counts']['continue_course']:,}), homepage ({D['action_counts']['homepage']:,}) and forum ({D['action_counts']['forum']:,}). "
           f"The catalogue is {cat_n} hand-written courses in {cats} categories (levels from Beginner to Advanced); no real learner-course log exists, which is why cross-learner collaborative filtering was not built.")
    P.sub("B", "Hybrid ranking")
    P.para(f"For learner profile p and course c the score is s(c) = 0.30 content + 0.15 skill + 0.15 topic + 0.12 success + 0.10 (0.5 + behaviour) + 0.08 goal + 0.05 rating + 0.05 engagement, clipped to [0, 1]. "
           f"Content is the cosine similarity of TF-IDF vectors {r('tfidf')} of the profile text and the course text, fitted per request; skill is 1.0, 0.6 or 0.3 for a level gap of 0, 1 or 2; topic "
           "and goal are keyword overlaps; rating is rescaled from 3.5-5.0. The behavioural boost sums event weights per course (view 0.05, start 0.12, quiz 0.14, complete 0.20, dismiss -0.25 and "
           "others) and is clipped to [-0.3, 0.35]; engagement is min(1, 0.25 + 0.04 recent events + 0.03 quizzes + 0.08 completions). The top-N courses get up to three reasons, and a staged path orders "
           "the top 12 by level, then score. The profile text joins interests, preferred topics, goals, course preferences, education and skill level; the vectoriser keeps at most 2,000 terms and drops English "
           "stop words. A weighted sum was chosen over a learned ranker because there is no label to learn it from and every term can be explained to the learner; the weights were set by hand, not tuned.")
    P.figure(F.diag("01_system_architecture.png"), "Architecture of LearnPathIQ: React interface, FastAPI routes, recommendation module with the cached model bundle, and the SQLite and file stores.")
    P.sub("C", "Success model and action benefit")
    P.para(f"Logistic regression, random forest {r('breiman')} and XGBoost {r('xgboost')} are trained on the eight features; the model with the best validation AUC is deployed (logistic regression, "
           f"validation AUC {f3(lr['val_auc'])}). For each of five actions (quiz, content, forum, homepage, continue course) two logistic regressions are fitted on treated and untreated "
           f"learner-weeks, and the estimated benefit is the difference of their predicted success, a T-learner {r('kunzel')} used one-vs-rest. The label is observational, so this is an estimated benefit, "
           "not a proven causal effect. Features are standardised, the split is by learner (1,760 train, 220 validation, 220 test) so that no learner appears on both sides, and the reported "
           "metrics are AUC, accuracy, precision, recall, F1 and the Brier score. Because one seed gives one number, the whole generate-split-train pipeline was also repeated for six seeds.")
    P.sub("D", "Offline policy evaluation and fairness audit")
    P.para(f"A multinomial logistic behaviour policy gives propensities, clipped to [0.02, 0.98] with importance weights capped at 10; the target policy picks the action with the largest estimated benefit. "
           f"IPS, SNIPS and doubly robust values {r('dudik')} are computed on the test split. A fairness audit reports observed rate, mean prediction and F1 by age band and gender; it audits only and does not change the ranking.")
    P.figure(F.diag("02_high_level_workflow.png"), "Main flow of a learner session: profile, scoring, success and uplift estimation, ranking with reasons, event logging and immediate re-ranking.")
    P.sub("E", "Implementation")
    P.para(f"FastAPI serves 18 JSON routes with Pydantic validation, PBKDF2-SHA256 password hashes and an HttpOnly cookie token; SQLAlchemy keeps six tables (users, profiles, courses, "
           "interactions, recommendation logs, tokens) in SQLite. The model bundle is loaded once; recommendations are recomputed on every request, with no cache. A React 19 interface has "
           "twelve pages, and a model-analytics page shows the metrics, confusion matrices, offline policy values and fairness audit.")

    P.sub("F", "Reproducibility")
    P.para("One script (train_pipeline.py, seed 42) generates the data, trains the three models and the uplift models, runs the offline policy evaluation and the fairness audit, and writes the bundle and "
           "the metrics file that the application reads; a second script repeats the pipeline for six seeds without touching the shipped artefacts, a third scores the ten personas, and a fourth times the API. "
           "Every number in this paper is read from those outputs, and the tests (pytest, a smoke script and a responsive check) run against the live application.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** Metrics are on the 220 held-out learners ({M['test_samples']:,} learner-weeks) of the seed-42 run that produced the deployed bundle, at a 0.5 threshold. Recommendation "
           "checks use ten hand-written personas (for example a Python beginner or a data analyst) whose relevant categories were fixed before any ranking was run; a course counts as relevant when its category "
           "is in the persona's set. Latency was measured on 127.0.0.1 with 30 sequential requests per read endpoint, because on this machine the name localhost adds about two seconds through an IPv6 fallback.")
    mrow = lambda name, m, sd: [name, f3(m["val_auc"]), f3(m["roc_auc"]), f3(sd["test_auc"]["mean"]) + " ± " + f3(sd["test_auc"]["std"]), f3(m["accuracy"]), f3(m["f1"]), f3(m["brier"])]
    P.table("Success-prediction results on the held-out test split (seed 42) and six-seed mean AUC",
            ["Model", "Val AUC", "Test AUC", "6-seed AUC", "Acc.", "F1", "Brier"],
            [mrow("Logistic reg. (deployed)", lr, sm["logistic_regression"]), mrow("Random forest", rf, sm["random_forest"]), mrow("XGBoost", xg, sm["xgboost"])],
            widths=[1.0, 0.4, 0.4, 0.62, 0.38, 0.38, 0.4], size=7, align=["l", "c", "c", "c", "c", "c", "c"])
    P.para(f"**Recommendation quality.** The hybrid beats popularity by a wide margin (P@3 {f2(hyb['p@3'])} against {f2(pop['p@3'])}; P@5 {f2(hyb['p@5'])} against {f2(pop['p@5'])}), "
           f"but not content-only TF-IDF (P@3 {f2(con['p@3'])}, P@5 {f2(con['p@5'])}); both similarity-based rankers place a relevant course first for every persona (P@1 {f2(hyb['p@1'])}, MRR {f2(hyb['mrr'])}), "
           f"while popularity reaches an MRR of only {f2(pop['mrr'])} (Fig. 3). The extra terms of the hybrid therefore do not raise precision on these personas; what they add is behaviour-driven adaptation and a "
           f"success estimate. This is a sanity check on {cat_n} courses with author-defined relevance, not a user study, and no precision or recall against real learner feedback was measured.")
    P.figure(F.fig("fig_persona_precision.png"), "Precision@k and MRR on ten personas for a popularity baseline, content-only TF-IDF and the deployed hybrid score.")
    P.figure(crop_shot("08_recommendations.png", "paper_recs.png"), "Output screen: ranked recommendations with match percentage, success estimate and the reasons for each course.")
    P.figure(crop_shot("17_analytics_diagnostics.png", "paper_diag.png"), "Output screen: model analytics page with confusion matrices, ROC curve and feature importance.")
    cm = lr["confusion_matrix"]
    P.para(f"**Success model.** Discrimination is modest: the deployed logistic regression reaches a test AUC of {f3(lr['roc_auc'])}, an F1 of {f3(lr['f1'])}, precision {f3(lr['precision'])} and recall {f3(lr['recall'])}; its confusion matrix "
           f"(Fig. 6) is {cm[0][0]:,} true negatives, {cm[0][1]:,} false positives, {cm[1][0]:,} false negatives and {cm[1][1]:,} true positives, so it misses {pct(cm[1][0] / sum(cm[1]))} of the successful learner-weeks. "
           f"The random forest trades precision ({f3(rf['precision'])}) for recall ({f3(rf['recall'])}) but has the worst AUC ({f3(rf['roc_auc'])}) and Brier score ({f3(rf['brier'])}). "
           f"Over six seeds the mean AUC is {f3(sm['logistic_regression']['test_auc']['mean'])} for logistic regression, {f3(sm['xgboost']['test_auc']['mean'])} for XGBoost and "
           f"{f3(sm['random_forest']['test_auc']['mean'])} for the random forest, and the validation winner changes between logistic regression ({S['selected_counts']['logistic_regression']} seeds) and XGBoost ({S['selected_counts']['xgboost']}). "
           f"Giving the models the hidden assessment score lifts the test AUC to {f3(C['with_assess_score']['logistic_regression']['test_auc'])}, {f3(C['with_assess_score']['random_forest']['test_auc'])} and "
           f"{f3(C['with_assess_score']['xgboost']['test_auc'])} (logistic regression, forest, XGBoost), so the weak signal comes from the synthetic label, not from a defect in the training code (Fig. 7).")
    P.figure(F.fig("fig_confusion_matrices.png"), "Confusion matrices of the three models at threshold 0.5 on the 2,640 test learner-weeks.")
    P.figure(F.fig("fig_ceiling.png"), "Test AUC with the eight shipped features and with the hidden assessment score added (ceiling check).", width=3.0)
    P.para(f"**Ablation.** Dropping one term at a time shows where the signal sits (Fig. 8): removing topic overlap lowers P@3 from {f3(ab['full']['p@3'])} to {f3(ab['topic']['p@3'])} and removing content similarity "
           f"to {f3(ab['content']['p@3'])}, while removing the success, behaviour, goal or engagement term changes nothing on these personas. Removing the skill or the rating term even raises P@3 to {f3(ab['skill']['p@3'])}, "
           "so this check does not justify those two weights; they remain because skill fit and quality matter to a real learner, which ten personas cannot show.")
    P.figure(F.fig("fig_ablation.png"), "Precision@3 when each term of the hybrid score is removed; the dashed line is the full score.")
    P.para(f"**Feedback loop.** In one scripted learner, six logged events (start, quiz, quiz and complete on one course, a view and a dismiss) raise the score of the engaged course from "
           f"{f3(FB['tracked']['ML101']['score_before'])} to {f3(FB['tracked']['ML101']['score_after'])}, push the dismissed course from rank 3 to 4, and raise the success estimate from "
           f"{f3(FB['p_success_before'])} to {f3(FB['p_success_after'])}. The adaptation is immediate, but the estimated action benefits also flip sign: the benefit of a quiz (Fig. 9) goes from "
           f"{FB['uplift_before']['quiz']:+.3f} to {FB['uplift_after']['quiz']:+.3f} and the suggested best action changes from {FB['best_action_before']} to {FB['best_action_after']}, "
           f"so they should not be trusted on a handful of events. The suggested action depends on learner state only, so every card of one learner shows the same action.")
    P.figure(F.fig("fig_feedback_loop.png"), "Left: estimated action benefit before and after six events. Right: course scores and ranks after the events.")
    P.para(f"**Offline policy evaluation.** IPS is {F.f4(pol['ips'])}, SNIPS {f3(pol['snips'])} and doubly robust {f3(pol['doubly_robust'])} against a logged success rate of 0.438, with an effective sample size "
           f"of {pol['effective_sample_size']:.1f} out of {pol['test_samples']:,} rows. The gap between IPS and SNIPS and the tiny effective sample show that a handful of rows dominate the estimate, so it is not "
           "evidence that the policy improves outcomes; the base paper reports the same IPS-SNIPS instability.")
    a0, a1, a2 = fa["age_band"]["0-35"], fa["age_band"]["35-55"], fa["age_band"]["55<="]
    P.para(f"**Fairness and failure cases.** F1 (Fig. 10) is {f3(a0['f1'])} for ages up to 35, {f3(a1['f1'])} for 35-55 and {f3(a2['f1'])} for 55 and over (n = {a2['n']}); the oldest group has the lowest "
           f"observed success ({f3(a2['success_rate'])}) and is over-predicted ({f3(a2['avg_predicted'])}). By gender, F1 is {f3(fa['gender']['F']['f1'])} for F and {f3(fa['gender']['M']['f1'])} for M. "
           "The base paper likewise finds older learners worst served. The audit only reports; it does not correct the ranking.")
    P.figure(F.fig("fig_fairness.png"), "Observed success rate, mean predicted success and F1 by age band and gender (audit only).")
    t24, lp, ins, crs = api["GET /api/recommendations?top_n=24"], api["GET /api/learning-path"], api["GET /api/insights"], api["GET /api/courses"]
    P.para(f"**Performance and tests.** A recommendation call with eight results takes {rec['mean_ms']:.1f} ms on average (p95 {rec['p95_ms']:.1f} ms) and with all {cat_n} courses {t24['mean_ms']:.1f} ms (p95 {t24['p95_ms']:.1f} ms); "
           f"the learning path takes {lp['mean_ms']:.1f} ms, insights {ins['mean_ms']:.1f} ms and the catalogue {crs['mean_ms']:.1f} ms. The first registration takes "
           f"{api['POST /api/auth/register']['mean_ms']:.0f} ms because of password hashing. {T['pytest']['passed']} of {T['pytest']['collected']} pytest tests and {T['smoke']['passed']} of {T['smoke']['checks']} "
           "end-to-end smoke checks pass, and a responsive check at 360, 768 and 1440 px in light and dark themes found no overflow or console errors. Load beyond 30 sequential requests was not tested.")
    P.para("**Comparison with the base paper.** The datasets and tasks differ, so this is context, not a ranking. The base paper uses real OULAD, roughly 1.7 million learner-week rows, a "
           f"reinforcement-learning agent and an AUC of 0.795; this work uses {D['rows']:,} synthetic rows, no agent and an AUC of {f3(lr['roc_auc'])}. Its SNIPS of 0.619 and the "
           f"{f3(pol['snips'])} here are not comparable, because the logged policies, rewards and sample sizes are different. What carries over is the method (success model, uplift, offline estimator, "
           "fairness audit) and the lesson that offline policy values need their weights inspected before they are believed.")
    P.para("**Lessons.** Three practical lessons follow. First, a short catalogue is served well by transparent terms, and the ablation tells the authors which terms to revisit. Second, a success model "
           "trained on a weakly informative label should be shown with its AUC, because a confident-looking percentage on a card suggests more than the model knows. Third, every estimate that looks "
           "like a gain, here the SNIPS value, needs its effective sample size printed next to it.")
    P.para("**Threats to validity.** The data are synthetic, so no external validity is claimed. The persona relevance sets were written by the authors, who also wrote the catalogue. Weights were set by hand, "
           "and the six-seed study re-draws data but not the catalogue. The uplift models extrapolate from a confounded log, and the interface shows their output as an estimated benefit only.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("Of the six objectives, four were met: learner profiles, a 24-course catalogue, content-based filtering, and a hybrid ranker with a staged learning path. The evaluation objective was met "
           "in part (precision and MRR on personas, model metrics, no real learner feedback), and collaborative filtering across learners was not implemented. The main finding is that "
           "a transparent eight-term score beats popularity clearly, matches content-only ranking closely and adapts at once to logged events, while the learned success and action-benefit "
           f"estimates are weak (AUC {f3(lr['roc_auc'])}, effective sample size {pol['effective_sample_size']:.1f}) and are best read as soft signals. "
           "Limits: synthetic data, one catalogue of 24 courses, no user study, no cache, single-node SQLite and demonstration-grade authentication; the system is a prototype.")
    P.para(f"Future work: evaluate on the real OULAD {r('oulad')}, add collaborative filtering once a learner log exists, learn the term weights from feedback, explore a reinforcement-learning agent as in the base paper {r('base')}, "
           f"and run a user study with real precision and recall.")

    P.references()
    P.save(path)
    return path, len(P.order)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "19.IEEE_Paper.docx")))
