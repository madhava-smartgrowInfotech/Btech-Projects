"""Chapters 9 and 10 and the sections reused by the methodology, scope, design and conclusion documents (all numbers come from facts.py)."""

import os

from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import c
from . import facts as F
from . import ch1

_M = F.METRICS
_MS = _M["models"]
_SEL = _M["selected_model"]
_LR = _MS[_SEL]
_OPE = _M["policy_evaluation"]
_REC = F.REC["summary"]
_AB = F.REC["ablation_drop_one_term"]
_SU = F.SEEDS["summary"]["logistic_regression"]["test_auc"]
_FAIR = _M["fairness"]
_NC = len(F.CATALOG)
_NCAT = len({x["category"] for x in F.CATALOG})
_LAT = F.API_LAT["endpoints"]["GET /api/recommendations?top_n=8"]
_T = F.TESTS


def _src(rel, start, end=None, drop_else=False):
    """Text of a source file from the line containing `start` up to (not including) the line containing `end`."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if start in l)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i])
    chunk = lines[a:b]
    while chunk and (not chunk[-1].strip() or (drop_else and chunk[-1].strip() == "else:")):
        chunk.pop()
    return "\n".join(chunk)


# ------------------------------------------------------------------ methodology document extras
def novelty_blocks():
    return [
        P(f"The base paper {c('base')} is a research study: it estimates the effect of learning actions on real OULAD data {c('oulad')} with uplift models, embeds those estimates in an Actor-Critic reinforcement-learning agent through "
          "causal regularisation, evaluates the learned policy off-policy and audits it by subgroup. This project does not reproduce that study and its numbers are not comparable with the base paper's. "
          "Its contribution is of a different kind: a working, explainable course-recommendation application that borrows part of the base paper's evaluation toolkit and reports its own results candidly. "
          "The table separates what is new in this work from what is standard practice that it reuses."),
        TAB("Novelty against the base paper and standard practice", ["Aspect", "Base paper", "This project", "New here?"], [
            ["Task", "Prescribe learning actions and paths in MOOCs", f"Rank a {_NC}-course catalogue for one learner, explain each card, and suggest a next action", "Different task; the combination is the project's own design"],
            ["Data", "Real OULAD (32,593 enrolments)", f"Synthetic OULAD-like generator ({F.PROFILE['rows']:,} learner-weeks); real OULAD never used", "No: a limitation, stated everywhere"],
            ["Recommendation layer", "Policy over learning actions, not an explainable catalogue ranking", f"Eight-term hybrid score (content, skill, topic, success, behaviour, goal, rating, engagement) with plain-language reasons", "**Yes**, as an engineered, inspectable design (weights hand-set)"],
            ["Feedback loop", "Offline trajectories", "Nine event types logged through the API; ranking, engagement and success estimate recomputed on every request", "**Yes** as an implementation; measured in a recorded example"],
            ["Success model", "XGBoost, AUC 0.795 on real data", f"LR / RF / XGBoost, validation-AUC selection; deployed {F.MODEL_LABEL[_SEL]}, test AUC {_LR['roc_auc']:.3f}", "No: standard models"],
            ["Action benefit", "Uplift modelling of treatment effects", "One-vs-rest T-learner, two logistic regressions per action " + c("kunzel"), "No: standard method; shown as an estimate, not a causal effect"],
            ["Policy learning", "Actor-Critic agent with causal regularisation", "None: the highest estimated benefit is shown as a suggestion", "Not reproduced"],
            ["Policy evaluation", "IPS, SNIPS and doubly robust values with intervals", f"IPS, SNIPS, DR with the effective sample size ({_OPE['effective_sample_size']}) reported beside them", "Partly: same estimators; candid weak-evidence reporting is the addition"],
            ["Fairness", "Subgroup analysis by age and gender", "Audit by age band and gender, shown in the application", "Partly: same idea, exposed to the user"],
            ["Honest evaluation", "Benchmarks on OULAD", f"Six-seed repeat, a ceiling check, a drop-one-term ablation, a persona check, a latency study; the hybrid is shown *not* to beat content-only on the persona check ({_REC['hybrid (shipped)']['p@3']:.3f} vs {_REC['content-only (TF-IDF)']['p@3']:.3f} P@3)", "**Yes** for this project: the analysis exposes the system's weaknesses"],
        ], widths=[1.0, 1.5, 2.5, 1.4], size=8.5),
        P("**What is not new.** TF-IDF cosine similarity " + c("tfidf") + ", hybrid combination of signals, logistic regression, random forests, gradient boosting, meta-learner uplift estimation and importance-weighted policy evaluation are all established techniques, "
          "and the OULAD-style schema is public. The value of the project lies in joining them into one reproducible, tested and inspectable application and in measuring it honestly. "
          "In particular, no claim is made that the hybrid ranker, the T-learner or the policy values are better than any alternative."),
    ]


def contribution_blocks():
    return [
        P("The contributions of the project, in order of importance:"),
        N(f"**An end-to-end, explainable course-recommendation application.** FastAPI, SQLAlchemy and SQLite behind eighteen JSON routes, a React front end with twelve screens and the original server-rendered interface, with every recommendation card carrying a match percentage and up to three reasons.",
          f"**A transparent hybrid ranking engine.** Eight interpretable terms with documented weights, a drop-one-term ablation, and a persona check in which both personalised rankers reach P@3 of {_REC['hybrid (shipped)']['p@3']:.3f} (hybrid) and {_REC['content-only (TF-IDF)']['p@3']:.3f} (content-only) against {_REC['popularity (rating only)']['p@3']:.3f} for popularity.",
          f"**A measurable feedback loop.** In a recorded example six events raise the score of the studied course from {F.FB['tracked']['ML101']['score_before']:.4f} to {F.FB['tracked']['ML101']['score_after']:.4f} and move a dismissed course from rank {F.FB['tracked']['DA101']['rank_before']} to {F.FB['tracked']['DA101']['rank_after']}, without retraining.",
          f"**A reproducible success-and-action pipeline with honest diagnostics.** Three success models compared over six seeds (logistic regression {_SU['mean']:.3f} +- {_SU['std']:.3f} AUC), a ceiling check that explains the weak signal, a one-vs-rest T-learner, IPS/SNIPS/DR evaluation reported with its effective sample size ({_OPE['effective_sample_size']}) and a fairness audit.",
          f"**A verified engineering base.** {_T['pytest']['passed']} automated tests, a {_T['smoke']['checks']}-check smoke test, a responsive-layout check at three widths in light and dark themes, and measured latency ({_LAT['mean_ms']:.1f} ms mean for eight ranked courses).",
          "**A candid account of what is missing:** real data, collaborative filtering across learners, a reinforcement-learning agent, a prerequisite graph, real feedback and a live experiment."),
    ]


# ------------------------------------------------------------------ scope document
def scope_blocks():
    return [
        H2("1.1 In scope"),
        P("The system covers one complete loop: a learner registers, describes themselves, receives an explained ranking, acts on it and sees the ranking change. The table lists each capability and where it is delivered."),
        TAB("In scope", ["#", "Capability", "Delivered by"], [
            ["1", "Learner accounts with a stored ten-field profile (education, skill level, interests, preferred topics, goals, preferences, learning style, weekly hours, age band, gender)", "`users`, `profiles` tables; `/api/auth/*`, `/api/profile`"],
            ["2", f"A {_NC}-course catalogue in {_NCAT} categories with topic, level, duration, difficulty, prerequisites, outcomes, tags, format and rating, searchable by text, category and level", "`courses` table seeded from `data/catalog/courses.json`; `/api/courses`"],
            ["3", "Content-based matching of the learner's text to course text (TF-IDF cosine) plus skill, topic and goal terms", "`app/recommender.py`: `content_scores`, `skill_compat`, `topic_interest_score`"],
            ["4", "A hybrid eight-term ranking with match percentage and reasons on every card", "`rank_courses`; `/api/recommendations`"],
            ["5", "Feedback events (nine types) that change the next ranking at once", "`interactions` table; `behavioral_boost`, `engagement_level`; `/api/interactions`"],
            ["6", "A learner-success estimate and an estimated benefit for five learning actions, shown as a suggested next action", "Success model and T-learner bundle in `models/*.joblib`; `predict_success`, `uplift_scores`"],
            ["7", "A staged learning path of up to six courses ordered by skill level and then score", "`/api/learning-path`"],
            ["8", "Insights, activity log, recommendation history and a model-analytics area (model table, confusion matrices, offline policy values, fairness audit)", "`/api/insights`, `/api/activity`, `/api/history`, `/api/metrics`, `/api/fairness`"],
            ["9", "Tests and checks", f"{_T['pytest']['passed']} pytest tests, {_T['smoke']['checks']} smoke checks, a responsive check at 360, 768 and 1440 px"],
        ], widths=[0.3, 3.9, 2.1], size=9.5, align=["c", "l", "l"]),
        H2("1.2 Out of scope"),
        TAB("Out of scope", ["#", "Item", "Why it is out"], [
            ["1", "Collaborative filtering across learners (objective 3)", "No log of many learners' course histories exists; the behavioural term is per learner"],
            ["2", "The real OULAD data", "Never downloaded or used; the models are trained on a reproducible synthetic stand-in"],
            ["3", "The base paper's Actor-Critic agent and causal regularisation", "Not implemented; only uplift scoring, off-policy evaluation and a fairness audit are borrowed"],
            ["4", "Prerequisite graphs or knowledge tracing", "Prerequisites are stored as text and shown, not used to order the path"],
            ["5", "Live experiments and user studies", "No A/B test, no learner feedback collected, no precision/recall against real feedback"],
            ["6", "Production operation", "No cache, single SQLite file, local demonstration authentication, no containers, monitoring or load handling"],
        ], widths=[0.3, 2.6, 3.4], size=9.5, align=["c", "l", "l"]),
        P("The boundary is deliberate. The system is a demonstrator of an explainable recommendation loop on synthetic data; anything that would make claims about real learners or real platforms is outside the project."),
    ]


def assumption_blocks():
    return [
        TAB("Assumptions and what happens if they fail", ["#", "Assumption", "If it does not hold"], [
            ["1", "Learners type interests and goals as English free text", "The TF-IDF term (English stop words, no stemming) loses most of its signal; other terms still rank"],
            ["2", f"The {_NC}-course hand-written catalogue stands in for a real platform's catalogue", "Precision figures on the persona check do not transfer to a larger or noisier catalogue"],
            ["3", "The synthetic generator reproduces the *shape* of an online-learning log (weekly clicks, quizzes, forum posts, an outcome)", "All success, uplift and policy numbers are only about the generator, not about real learners"],
            ["4", "Event weights, score weights and limits are reasonable hand-set constants", "Rankings could be improved by tuning; the ablation shows two terms that do not help on the persona set"],
            ["5", "One trusted user group on one machine", "The token authentication and single SQLite file are not an identity or multi-user design"],
            ["6", "Python 3.11 or newer, Node.js 20 or newer and a modern browser are installed", "The back end or the React front end will not start; the original Jinja pages need only Python"],
        ], widths=[0.3, 3.0, 3.0], size=9.5, align=["c", "l", "l"]),
    ]


def limitation_blocks():
    old = _FAIR["age_band"]["55<="]
    return [
        P("Each limitation below is backed by a measurement in this project; none is a generic disclaimer."),
        TAB("Limitations with their evidence", ["Limitation", "Evidence", "Consequence"], [
            ["Synthetic training data", "Real OULAD never used; label generated by `train_pipeline.py`", "No external validity; results show recovery of the generator's rule"],
            ["Weak predictive signal", f"Test AUC {_LR['roc_auc']:.3f} (six-seed mean {_SU['mean']:.3f}); with the hidden assessment score {F.CEIL['with_assess_score']['logistic_regression']['test_auc']:.3f}", "The success term in the score is a weak signal; accuracy is a few points above the majority rate"],
            ["Weak policy evidence", f"IPS {_OPE['ips']:.4f}, SNIPS {_OPE['snips']:.4f}, DR {_OPE['doubly_robust']:.4f}; effective sample size {_OPE['effective_sample_size']} of {_OPE['test_samples']:,}", "No conclusion about the action policy can be drawn"],
            ["No collaborative filtering", "Objective 3 not met", "The system cannot learn from other learners' histories"],
            ["Hybrid does not beat content-only", f"P@3 {_REC['hybrid (shipped)']['p@3']:.3f} vs {_REC['content-only (TF-IDF)']['p@3']:.3f}; P@5 {_REC['hybrid (shipped)']['p@5']:.2f} vs {_REC['content-only (TF-IDF)']['p@5']:.2f}", "Extra terms add adaptation and cold-start safety, not persona-level precision"],
            ["Unstable action advice", f"Quiz benefit {F.FB['uplift_before']['quiz']:+.3f} to {F.FB['uplift_after']['quiz']:+.3f} after six events; best action {F.FB['best_action_before']} to {F.FB['best_action_after']}", "Estimates are not causal and must not steer real decisions"],
            ["Same suggested action on every card", "Action depends only on learner state, not on the course", "The per-card action line carries no course-specific information"],
            ["Fairness gap", f"F1 {old['f1']:.3f} for age 55+ against {_FAIR['age_band']['0-35']['f1']:.3f} for 0-35 (n = {old['n']})", "Weaker success prediction for the smallest, oldest group; no mitigation applied"],
            ["Empty contributing-features list", "`predict_success()` returns importances only for models with `feature_importances_`; the deployed logistic regression has none", "The Insights page cannot show per-feature contributions; coefficients are visible only in the analytics plot"],
            ["No real feedback", "No precision/recall from learners, no user study", "Objective 6 only partly met"],
            ["Demonstration-grade engineering", "No cache; one SQLite file; tokens are not expired server-side (the 72-hour limit is the cookie lifetime only)", "Not suitable for shared or production use"],
        ], widths=[1.5, 2.6, 2.2], size=8.5),
        TAB("Risks and mitigations", ["Risk", "Mitigation in the project"], [
            ["Suggestions mistaken for educational advice", "Interface text states that action scores are estimated benefits, not proven effects, and that offline estimates are not a live test"],
            ["Over-trust in a weak model", "The analytics page shows the real test metrics and the dataset name; the policy page carries the not-a-live-test notice"],
            ["Opaque ranking", "Every card shows a match percentage and reasons; the score weights are documented and ablated"],
            ["Unauthorised access", "Hashed passwords (PBKDF2-SHA256), random 256-bit tokens, HttpOnly cookie; 401 on protected routes (tested)"],
            ["Bad input", "Pydantic validation (422), unknown event types rejected (400), unknown course 404 (tested)"],
        ], widths=[2.0, 4.3], size=10),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured and are therefore stated as gaps, not estimated:"),
        B("Any result on real OULAD or any other real learner data.",
          "Precision, recall or relevance ratings from real learners; any user study or usability study.",
          "A live A/B test of the suggested action or of the ranking.",
          "The sensitivity of the offline policy values to the propensity clip (0.02 to 0.98) and the weight cap (10), which were fixed.",
          "Tuned or learned score weights; the eight weights are hand-set and only ablated.",
          "Load, concurrency and long-running behaviour: latency was measured with one client making sequential requests.",
          "Browsers other than Chrome, assistive technology, and any penetration test.",
          "Confidence intervals for the persona-check precision: ten personas on a 24-course catalogue are too few."),
    ]


# ------------------------------------------------------------------ design document extras
def walkthrough_blocks():
    s = _src
    return [
        H2("3.1 The hybrid score"),
        P("`rank_courses` computes one learner-level context (engagement, success probability, estimated action benefits) and then scores every course with eight terms. "
          "The weights sum to 1.00 and the result is clipped to [0, 1], rounded and sorted. The same function serves `/api/recommendations` and `/api/learning-path`."),
        CODE(s("app/recommender.py", "def rank_courses", "        reasons = []")),
        CODE(s("app/recommender.py", "        reasons = []", "    ranked.sort")),
        H2("3.2 Behaviour and engagement"),
        P("Interaction events change the next ranking through two functions. The behavioural boost adds a signed weight for each event on the same course, clipped to [-0.3, 0.35]; a dismissal costs -0.25. "
          "The engagement score is built from the learner's recent events, quizzes and completions and doubles as one of the eight success-model features."),
        CODE(s("app/recommender.py", "def behavioral_boost", "def engagement_level")),
        CODE(s("app/recommender.py", "def engagement_level", "def load_ml_bundle")),
        H2("3.3 Success estimate and action benefit"),
        P("The success model is the validation-AUC winner saved by the training script. The action benefit is the difference between two logistic regressions per action (action taken versus not taken); "
          "if the model files are missing, a small hand-written heuristic is returned instead so that the page never fails."),
        CODE(s("app/recommender.py", "            for a in actions:", "            # predictive fallback", drop_else=True)),
        H2("3.4 Authentication"),
        P("Registration hashes the password with PBKDF2-SHA256, stores a random URL-safe token in `auth_tokens` and sets it as an HttpOnly cookie; the same token is accepted in an `X-Token` or Bearer header for API clients."),
        CODE(s("app/api_routes.py", '@router.post("/api/auth/register")', '@router.post("/api/auth/login")')),
        H2("3.5 Offline policy evaluation in the training script"),
        P("The target policy picks the action with the highest estimated benefit for every test row; the behaviour policy is a multinomial logistic regression over the logged actions. "
          "Propensities are clipped, importance weights are capped, and the effective sample size is computed from the weights. The doubly robust value uses the selected success model as its outcome model without an action input, "
          "a simplification that is one more reason to read the values as rough."),
        CODE(s("scripts/train_pipeline.py", "        # propensities", "        ope = {\"ips\"")),
    ]


def decision_blocks():
    return [
        TAB("Decisions and reasons", ["Decision", "Alternatives considered", "Reason", "Consequence"], [
            ["FastAPI + SQLAlchemy + SQLite", "Django, Flask, PostgreSQL", "Typed request validation, automatic docs, one file to back up, no service to run " + c("fastapi", "sqlalchemy"), "Single node; not built for many concurrent writers"],
            ["Keep the Jinja2 UI and add a React front end on a Vite proxy", "Replace the original UI; cross-origin API calls", "Both screens use the same routes; the proxy keeps one origin so the HttpOnly cookie is first-party", "Two interfaces to maintain; a production setup would need a reverse proxy"],
            ["TF-IDF cosine at request time", "Pre-computed embeddings, a vector index, contrastive BERT " + c("khreis"), f"Only {_NC} short course texts; no training data for embeddings; a refit is a few milliseconds", "Vocabulary is refitted on every request; no semantic matching beyond shared words"],
            ["Hand-set score weights", "Learn the weights (learning to rank)", "No relevance labels from real learners to learn from; fixed weights are easy to explain and ablate", "Weights are untuned; the ablation shows two terms that do not help on the persona set"],
            ["Eight separate terms in one linear score", "A single opaque model", "Every reason shown to the learner maps to one term", "Cannot capture interactions between terms"],
            ["Success model chosen by validation AUC among LR, RF and XGBoost", "Always XGBoost; tune", "The base paper uses XGBoost, but here the simplest model is as good on the synthetic data (six seeds)", "The choice flips between logistic regression and XGBoost across seeds"],
            ["One-vs-rest T-learner with logistic regressions", "Causal forests, doubly robust learners, an RL agent " + c("hrl", "sutton"), "Few lines, no extra library, produces a benefit per action", "Unstable, extrapolates from a confounded log; presented only as an estimate"],
            ["Synthetic OULAD-like data", "Download real OULAD " + c("oulad"), "The training script only probes the dataset page and does not download it; the project needs a reproducible, licence-free table", "Every number describes the generator; stated in the interface and in every document"],
            ["Recompute recommendations on every request", "Cache by learner state", "A change in profile or in one event must show at once", f"{_LAT['mean_ms']:.1f} ms mean per ranked list; fine for one user, untested for many"],
            ["Learning path = ranked top 12, sorted by level then score, first six kept", "Prerequisite graph, knowledge tracing " + c("lpnav", "saito"), "No reliable prerequisite data; the rule is easy to explain", "Prerequisite text is shown but not enforced"],
            ["PBKDF2-SHA256 hashes and random tokens stored in a table", "JWT, OAuth", "Revocable by deleting a row (logout), no signing key to manage", "No server-side expiry check; local demonstration use only"],
        ], widths=[1.4, 1.3, 2.1, 1.5], size=8.5),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def conclusion_blocks():
    st = ch1.OBJECTIVE_STATUS
    fb = F.FB
    rows = [
        ["1", ch1.OBJECTIVES[0], st[0][0], "Ten-field profile stored per learner; completed courses recorded as `complete` events"],
        ["2", ch1.OBJECTIVES[1], st[1][0], f"{_NC} courses, {_NCAT} categories, nine metadata fields"],
        ["3", ch1.OBJECTIVES[2], st[2][0], "No real multi-learner history exists; the behavioural term is per learner"],
        ["4", ch1.OBJECTIVES[3], st[3][0], f"TF-IDF cosine plus skill, topic and goal terms; P@3 {_REC['content-only (TF-IDF)']['p@3']:.3f} on the persona check"],
        ["5", ch1.OBJECTIVES[4], st[4][0], f"Eight-term hybrid (P@3 {_REC['hybrid (shipped)']['p@3']:.3f}) and a six-step path ordered by level then score; no prerequisite graph"],
        ["6", ch1.OBJECTIVES[5], st[5][0], f"AUC {_LR['roc_auc']:.3f}, F1 {_LR['f1']:.3f}, persona P@k and MRR; no real-feedback precision or recall, no user study"],
    ]
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary"),
        P("The project set out to build a personalised course-recommendation system that profiles a learner, matches the catalogue by content, adapts to feedback and orders the result into a learning path, and to evaluate it honestly. "
          f"It delivers LearnPathIQ: a FastAPI and SQLite back end with eighteen JSON routes, a React front end with twelve screens and the original server-rendered interface, a {_NC}-course catalogue, "
          "an eight-term hybrid ranker with a plain-language reason on every card, a measurable feedback loop, a learner-success model, an estimated benefit for five learning actions, an offline policy evaluation and a fairness audit. "
          f"The work is backed by {_T['pytest']['passed']} automated tests, a {_T['smoke']['checks']}-check smoke test and a responsive-layout check. "
          "All learned models are trained on a reproducible synthetic data set that imitates the structure of the Open University Learning Analytics Dataset; the real data were never used."),
        H2("9.2 Objectives against outcomes"),
        TAB("The six objectives and their outcome", ["#", "Objective", "Status", "Evidence"], rows, widths=[0.3, 2.3, 0.9, 2.8], size=9, align=["c", "l", "l", "l"]),
        P("Four objectives were achieved (profiles, catalogue, content-based matching, and the hybrid score with its learning path, which is ordered by skill level and score and has no prerequisite graph), one partly (evaluation) and one not at all (collaborative filtering across learners). "
          "The reasons are stated plainly: no real multi-learner history was available, so the behavioural term in the score reflects only the one learner's own events, and no real learner feedback was collected."),
        H2("9.3 Key findings"),
        B(f"**The success model is weak.** The deployed {F.MODEL_LABEL[_SEL]} reaches a test AUC of {_LR['roc_auc']:.4f} (six-seed mean {_SU['mean']:.3f} +- {_SU['std']:.3f}) and an accuracy of {_LR['accuracy']:.3f}, only a few points above the {(1 - F.SEEDS['runs'][0]['sizes']['positive_rate_test']):.3f} majority-class rate. "
          f"Adding the hidden assessment score lifts AUC to {F.CEIL['with_assess_score']['logistic_regression']['test_auc']:.3f}, so the weak signal is a property of the synthetic data, not a coding fault.",
          f"**The hybrid beats popularity but not content-only matching.** On ten author-written personas P@3 is {_REC['popularity (rating only)']['p@3']:.3f} (popularity), {_REC['content-only (TF-IDF)']['p@3']:.3f} (content-only) and {_REC['hybrid (shipped)']['p@3']:.3f} (hybrid). "
          f"The drop-one-term ablation shows that the topic and content terms matter most (P@3 falls to {_AB['topic']['p@3']:.3f} and {_AB['content']['p@3']:.3f} without them).",
          f"**Ranking adapts at once.** Six events raise the score of the studied course from {fb['tracked']['ML101']['score_before']:.4f} to {fb['tracked']['ML101']['score_after']:.4f}, push the dismissed course from rank {fb['tracked']['DA101']['rank_before']} to {fb['tracked']['DA101']['rank_after']} and move the success estimate from {fb['p_success_before']:.3f} to {fb['p_success_after']:.3f}.",
          f"**Action advice is unstable and weak evidence supports it.** Estimated benefits change sign after a few events, and the offline policy values (IPS {_OPE['ips']:.4f}, SNIPS {_OPE['snips']:.4f}, DR {_OPE['doubly_robust']:.4f}) rest on an effective sample size of {_OPE['effective_sample_size']} of {_OPE['test_samples']:,} rows.",
          f"**The audit finds a gap.** F1 is {_FAIR['age_band']['55<=']['f1']:.3f} for the oldest age band against {_FAIR['age_band']['0-35']['f1']:.3f} for the youngest, on a small group.",
          f"**The engineering is sound at demonstration scale.** A ranked list of eight courses takes {_LAT['mean_ms']:.1f} ms on average (p95 {_LAT['p95_ms']:.1f} ms) on the development machine; {_T['pytest']['passed']} of {_T['pytest']['collected']} tests and {_T['smoke']['passed']} of {_T['smoke']['checks']} smoke checks pass."),
        FIG(F.fig("fig_model_comparison.png"), "Summary of the success-model comparison on the held-out test split", 5.6),
        FIG(F.fig("fig_persona_precision.png"), "Summary of the persona check: popularity, content-only and hybrid rankers", 5.2),
        H2("9.4 Practical applications"),
        B("A teaching demonstrator for how a hybrid ranking, a feedback loop and an explanation fit together in a small course platform.",
          "A research scaffold: the training script, the offline policy evaluation and the audit can be re-run on real OULAD data once it is loaded, and the persona check can be replaced by real feedback.",
          "A starting point for a recommendation module in a small learning portal, after the gaps listed below are closed."),
        H2("9.5 Honest summary of what is missing"),
        B("Real data: nothing here is validated on real learners.",
          "Collaborative filtering across learners and a prerequisite graph.",
          "The base paper's reinforcement-learning agent.",
          "Real feedback: no user study and no live experiment, so precision and recall against real relevance were not measured.",
          "Production hardening: caching, identity, a server database and load handling."),
    ]


def chapter9_blocks():
    return conclusion_blocks()


def future_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        P("Each item below is tied to a gap that the measurements in Chapter 8 exposed, so the order follows the strength of the evidence, not novelty."),
        H2("10.1 Real data"),
        B(f"**Train and evaluate on the real OULAD data** {c('oulad')} (CC BY 4.0). The synthetic generator caps the signal at AUC about {F.CEIL['shipped_features']['logistic_regression']['test_auc']:.2f}; real behaviour may carry more or less. "
          "The existing script already probes the dataset page; the missing step is loading the student, VLE and assessment tables into the same eight features.",
          "**Re-run the seed study, the ceiling check and the fairness audit** on the real data and report the results next to the synthetic ones."),
        H2("10.2 Better recommendation models"),
        B(f"**Collaborative filtering over learner histories** (objective 3), for example matrix-factorisation or graph models such as LightGCN {c('lightgcn')}, once a real interaction log exists; combine it with the content score, as the companion paper on time-to-event filtering does {c('gharahighehi')}.",
          f"**Semantic content matching.** Replace TF-IDF by sentence embeddings trained contrastively, as in the isotropy-optimised BERT approach {c('khreis')}, to match learners and courses that share meaning but not words.",
          f"**Learn the score weights** from feedback (learning to rank) instead of the hand-set 0.30/0.15/0.15/0.12/0.10/0.08/0.05/0.05; the ablation already shows two terms (skill and rating) that slightly lower P@3 as weighted.",
          "**Make the suggested action course-specific**, so that the action line on each card differs, which the current learner-state-only estimate cannot do."),
        H2("10.3 Policy learning and evaluation"),
        B(f"**Implement the base paper's policy learner:** a causal-regularised Actor-Critic agent {c('base', 'hrl', 'sutton')} on top of the uplift estimates, with fitted-Q baselines.",
          f"**Make the offline evaluation trustworthy:** sweep the propensity clip and weight cap, use an action-conditional outcome model for the doubly robust value, and report confidence intervals; the current effective sample size of {_OPE['effective_sample_size']} shows why.",
          "**Run a live randomised test** of the suggested action before any claim about its benefit."),
        H2("10.4 Learning paths"),
        B(f"**A prerequisite graph and knowledge tracing** {c('lpnav', 'saito')} so that the path is ordered by what a learner must know, not only by level and score.",
          "**Completed-course handling** as a first-class profile field rather than a `complete` event."),
        H2("10.5 Evaluation with learners"),
        B("**A user study** with real learners rating relevance, from which precision, recall and nDCG can be computed (objective 6).",
          "**Larger persona and catalogue sets** with relevance judged by more than the authors, and confidence intervals for the persona-check precision."),
        H2("10.6 Fairness"),
        B(f"**Investigate and mitigate the age-band gap** (F1 {_FAIR['age_band']['55<=']['f1']:.3f} against {_FAIR['age_band']['0-35']['f1']:.3f}) with more data for the oldest group, group-aware thresholds or reweighting, and re-audit."),
        H2("10.7 Engineering"),
        B("**Caching** of TF-IDF and per-learner rankings, invalidated on profile or event changes, and a **load test** of the API.",
          "**Authentication hardening:** token expiry checked on the server, rotation, rate limiting, and a managed identity provider.",
          "**A server database, containers and monitoring** for multi-user operation; **per-endpoint tests** beyond the current five pytest tests."),
    ]


def chapter10_blocks():
    return future_blocks()
