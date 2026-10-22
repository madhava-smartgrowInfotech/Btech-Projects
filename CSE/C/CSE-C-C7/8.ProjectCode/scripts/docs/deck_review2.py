"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, prepare, set_title, thank_you, title_slide, wipe
from .refs import K as RK

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def lat(name):
    return F.API_LAT["endpoints"][name]


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    M = F.METRICS
    LR = M["models"]["logistic_regression"]
    py, sm, rs = F.TESTS["pytest"], F.TESTS["smoke"], F.TESTS["responsive"]
    R = F.REC["summary"]
    P = M["policy_evaluation"]
    rec8 = lat("GET /api/recommendations?top_n=8")

    # ---- 1 title
    title_slide(S[0], "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS",
                f"Design, methodology and progress: an eight-term hybrid ranker, a learner-success model and action-benefit estimates behind a FastAPI service and a React interface")
    notes[1] = "This review shows how the system is designed and built: the data and models, what has been implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Learners face long catalogues and no reliable way to judge which course suits them. Popularity lists ignore skill, goals and behaviour, new learners have no history, and courses are not put in order.", K.ORANGE, "!"),
        ("Proposed system", "LearnPathIQ ranks every course with an eight-term hybrid score, adds a learner-success estimate and an estimated best learning action, explains each recommendation and orders a staged learning path.", K.BLUE, "i"),
        ("Base paper link", "Reuses its ideas of a predictive success model, uplift-style action benefit, off-policy evaluation and a fairness audit. It does not implement the Actor-Critic agent and does not use real OULAD data.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.6, t, b_, col, gl, body_size=16)
    notes[3] = "One-minute recap of Review 1. The base paper prescribes actions on real OULAD data; we adapt its components to course recommendation on synthetic OULAD-like data and say so on every results slide."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.7, 5.5)
    K.text(s, 8.6, 1.5, 4.15, 5.3, [
        ("**Four tiers**", {"space_after": 8}),
        ("Presentation: React 19 SPA (port 5407, 12 pages) and the original Jinja pages (port 8407).", {"bullet": True}),
        ("Application: FastAPI with 18 JSON routes, HttpOnly cookie or header token, Pydantic validation.", {"bullet": True}),
        ("Recommendation: hybrid ranker, success model, action-benefit models loaded from joblib files.", {"bullet": True}),
        ("Data: SQLite (6 tables), 24-course catalogue, model artifacts.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=8)
    notes[4] = "Four tiers. The React app proxies /api to the FastAPI service, so the login cookie stays same-origin."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.35, [("Learner profile", K.NAVY), ("TF-IDF + rule terms", K.PURPLE), ("Success + action models", K.GREEN), ("8-term hybrid score", K.ORANGE),
                                      ("Top-N + reasons + log", K.BLUE), ("Events update next ranking", K.NAVY)], size=14, gap=0.22)
    for i, (t, b_) in enumerate([("Trained offline", "scripts/train_pipeline.py generates the data, fits three success models and the action models, runs policy evaluation and the fairness audit, and saves every artifact. Seed 42."),
                                 ("Computed per request", "Every recommendation call re-fits TF-IDF over the profile and 24 course texts, scores all courses and logs the result. No cache; about %.0f ms on this machine." % rec8["mean_ms"]),
                                 ("Honest scope", "No collaborative filtering across learners (no real interaction log) and no reinforcement-learning agent. The behavioural term is per learner.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.3, 3.85, 3.2)
        K.text(s, x + 0.25, 3.45, 3.4, 0.5, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 4.05, 3.4, 2.4, b_, size=15, color=K.TXT)
    notes[5] = "The workflow splits into an offline training step and an online ranking step. The online step needs no retraining to adapt: new events change the behaviour and engagement terms at once."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset")
    wipe(s)
    D = F.PROFILE
    for i, (v, l, c) in enumerate([(f"{D['rows']:,}", "learner-week rows (synthetic)", K.BLUE), (f"{D['learners']:,} x {D['weeks']}", "learners x weeks", K.GREEN),
                                   (F.pct(D["success_rate"]), "positive (success) rate", K.ORANGE), ("24", "hand-written courses, 9 categories", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("fig_data_profile.png"), 0.6, 2.95, 6.6, 3.85)
    K.text(s, 7.5, 3.0, 5.2, 3.8, [
        ("Source is a reproducible OULAD-like generator (synthetic-oulad-like-fallback-v1); the real OULAD was not downloaded or used.", {"bullet": True}),
        ("Learner-level split 80/10/10: train 21,120, validation 2,640, test 2,640 rows (seed 42).", {"bullet": True}),
        ("Success is a noisy function of a hidden assessment score that the app never sees.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[6] = "State the data source first. Every model number in this deck comes from the synthetic generator; no claim is made about real learners."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preparation and features")
    wipe(s)
    K.picture(s, F.fig("fig_feature_signal.png"), 0.6, 1.4, 7.9, 3.0)
    K.text(s, 0.6, 4.6, 7.9, 2.2, [
        ("**Text:** profile text (interests, topics, goals, preferences, education, skill) and course text (title, description, topic, category, tags, level) go into TF-IDF with English stop words, at most 2,000 terms.", {"bullet": True}),
        ("**State:** 8 features from the profile and logged events, standardised before the models.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=6)
    K.text(s, 8.8, 1.5, 3.95, 5.2, [
        ("1  Profile text and course text", {}), ("2  TF-IDF and cosine similarity", {}), ("3  Engagement from recent events", {}), ("4  8-feature learner state", {}), ("5  Standard scaling", {}),
        ("Weak signal: the strongest feature correlates with success at only r = 0.18.", {"italic": True, "size": 14, "color": K.TXT}),
    ], size=16, color=K.INK, space_after=10)
    notes[7] = "The same state vector is used in training and at request time. Feature correlations are modest by construction of the generator, which is why test AUC is about 0.60."

    # ---- 8 model architecture
    s = S[7]
    set_title(s, "Models")
    wipe(s)
    rows = [["Model", "Settings", "Val AUC", "Test AUC"],
            ["Logistic regression (selected)", "max_iter 1000, standardised inputs", F.f3(LR["val_auc"]), F.f3(LR["roc_auc"])],
            ["Random forest", "200 trees", F.f3(M["models"]["random_forest"]["val_auc"]), F.f3(M["models"]["random_forest"]["roc_auc"])],
            ["XGBoost", "300 trees, depth 5, rate 0.05, subsample 0.9", F.f3(M["models"]["xgboost"]["val_auc"]), F.f3(M["models"]["xgboost"]["roc_auc"])],
            ["Action-benefit (T-learner)", "5 actions x 2 logistic regressions", "-", "-"],
            ["Behaviour policy", "multinomial logistic regression", "-", "-"]]
    K.table(s, 0.6, 1.5, [3.4, 3.6, 1.0, 1.0], rows, font_size=13, row_h=0.62, align=["l", "l", "c", "c"])
    K.tile(s, 9.9, 1.5, 2.83, 1.45, F.f3(LR["val_auc"]), "validation AUC of the saved model", K.BLUE, vsize=26)
    K.tile(s, 9.9, 3.15, 2.83, 1.45, "5 x 2", "uplift models, one pair per action", K.GREEN, vsize=26)
    K.tile(s, 9.9, 4.8, 2.83, 1.45, "No GPU", "all training on a desktop CPU", K.ORANGE, vsize=24)
    K.text(s, 0.6, 5.5, 8.8, 1.2, "Estimated benefit of an action = P(success | action) - P(success | no action). It is an estimate from a confounded synthetic log, not a proven causal effect.", size=14, color=K.TXT, italic=True)
    notes[8] = "The selected model is whichever has the best validation AUC; on the shipped seed that is logistic regression, with XGBoost a close second. Test AUC is reported on the held-out learners."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    sd = F.SEEDS
    rows = [["Setting", "Value"],
            ["Data and split", "synthetic OULAD-like generator, 2,200 learners x 12 weeks; learner-level 80/10/10 split, seed 42"],
            ["Features", "cum_clicks, recent_clicks, quiz_count, forum_count, completions, engagement, weekly_hours, skill_code"],
            ["Success models", "logistic regression, random forest (200 trees), XGBoost (300 trees, depth 5); best validation AUC kept"],
            ["Action models", "for quiz, content, forum, homepage, continue_course: two logistic regressions (treated, not treated)"],
            ["Offline policy evaluation", "propensities clipped to [0.02, 0.98], weights capped at 10; IPS, SNIPS, doubly robust"],
            ["Fairness audit", "F1 and mean prediction by age band and gender; audit only, no mitigation"],
            ["Run time / hardware", f"about {sd['runs'][0]['seconds']:.0f} s per seed run; {F.ENV['cpu'].replace('12th Gen Intel(R) Core(TM) ', '')}, {F.ENV['ram_gb']} GB RAM, CPU only"]]
    K.table(s, 0.6, 1.5, [3.0, 9.13], rows, font_size=14, row_h=0.64, first_bold=True)
    notes[9] = "The whole training run takes seconds, so we could repeat it with six seeds to measure variation (next slides and the final review)."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: the hybrid score")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 5.2, 5.5)
    K.text(s, 6.1, 1.45, 6.65, 5.4, [
        ("**Score** = 0.30 content + 0.15 skill + 0.15 topic + 0.12 predicted success + 0.10 (0.5 + behaviour) + 0.08 goal + 0.05 rating + 0.05 engagement, clipped to [0, 1].", {"bullet": True, "space_after": 9}),
        ("**Behaviour** adds event weights per course (view 0.05 up to complete 0.20, dismiss -0.25), clipped to [-0.3, 0.35].", {"bullet": True, "space_after": 9}),
        ("**Reasons.** Up to three plain-language reasons are attached to each card (interest match, skill fit, prior engagement, success estimate).", {"bullet": True, "space_after": 9}),
        ("**Next action.** The action with the largest estimated benefit is attached; it depends on the learner state only, so every card of one learner shows the same action.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[10] = "The flowchart follows rank_courses() in app/recommender.py. The last bullet is a known limitation that we report rather than hide."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 7.3, 5.5)
    rows = [["Module", "Role"], ["app/recommender.py", "hybrid ranker, success, uplift"], ["app/api_routes.py", "18 JSON routes"], ["app/models.py", "6 ORM tables"], ["app/security.py", "hashing, tokens"],
            ["scripts/train_pipeline.py", "offline training"], ["frontend/src/pages", "12 React pages"]]
    K.table(s, 8.2, 1.5, [2.65, 1.88], rows, font_size=12, row_h=0.5)
    notes[11] = "Level-1 data flow: five processes. Levels 0 and 2 are in the report."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.0, 5.1)
    K.picture(s, F.diag("06_uml_class_diagram.png"), 6.8, 1.35, 5.9, 5.1)
    K.text(s, 0.6, 6.55, 12.13, 0.35, "Six tables; users-profiles is 1:1, users-interactions and users-tokens are 1:n; the UML draws the recommender module as a class.", size=12, color=K.TXT, align="c", italic=True)
    notes[12] = "Foreign keys link profiles, interactions and tokens to users. Interaction course ids and recommendation-log columns are plain columns, not constraints."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    pk = F.ENV["packages"]
    rows = [["Layer", "Technology"],
            ["Models", f"scikit-learn {pk['scikit-learn']}, XGBoost {pk['xgboost']}, pandas {pk['pandas']}, NumPy {pk['numpy']}, joblib"],
            ["API", f"FastAPI {pk['fastapi']}, Uvicorn, Pydantic {pk['pydantic']}, passlib (pbkdf2_sha256)"],
            ["Database", f"SQLite through SQLAlchemy {pk['sqlalchemy']}"],
            ["Front end", "React 19, Vite, React Router, Recharts, Framer Motion"],
            ["Testing", "pytest, an end-to-end smoke script, a Playwright responsive check"],
            ["Run", f"Python {F.ENV['python']}, Node {F.ENV['node']}; backend port 8407, front end port 5407"]]
    K.table(s, 0.6, 1.5, [2.6, 9.53], rows, font_size=15, row_h=0.64, first_bold=True)
    notes[13] = "Everything is open source and runs on one laptop."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component (objective)", "Status", "Evidence"],
            ["Learner profiles (1)", "Done", "profiles table, profile page"],
            ["Course catalogue (2)", "Done", "24 courses with topic, level, prerequisites, outcomes"],
            ["Content-based matching (4)", "Done", "TF-IDF similarity plus skill, topic, goal terms"],
            ["Hybrid ranking and learning path (5)", "Done", "8-term score, staged path, reasons"],
            ["Evaluation (6)", "Partial", "AUC/F1, policy evaluation, 10-persona check; no user study"],
            ["Collaborative filtering (3)", "Not implemented", "no real interaction log across learners"],
            ["Actor-Critic RL agent (base paper)", "Not implemented", "out of scope; uplift and OPE only"]]
    K.table(s, 0.6, 1.5, [4.5, 1.8, 5.83], rows, font_size=14, row_h=0.62)
    notes[14] = "Objective-by-objective status. The two gaps are cross-learner collaborative filtering and the reinforcement-learning agent."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results (synthetic data)")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.f3(LR["roc_auc"]), "test AUC, logistic regression", K.BLUE), (F.f3(LR["f1"]), "test F1 (2,640 rows)", K.GREEN),
                                   (F.f2(R["hybrid (shipped)"]["p@3"]), "persona P@3, hybrid", K.ORANGE), (F.f2(R["popularity (rating only)"]["p@3"]), "persona P@3, popularity", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=28)
    names = ["Popularity", "Content-only", "Hybrid"]
    keys = ["popularity (rating only)", "content-only (TF-IDF)", "hybrid (shipped)"]
    K.bar_chart(s, 0.6, 2.9, 7.4, 3.95, names, [("P@1", [R[k]["p@1"] for k in keys]), ("P@3", [R[k]["p@3"] for k in keys]), ("P@5", [R[k]["p@5"] for k in keys])],
                colors=[K.GREEN, K.BLUE, K.ORANGE], number_format="0.00", font_size=12, max_value=1.2)
    K.card(s, 8.3, 2.95, 4.43, 3.75, "Reading", f"10 author-written personas over 24 courses: the hybrid beats popularity clearly, but not content-only (P@3 {R['hybrid (shipped)']['p@3']:.2f} vs {R['content-only (TF-IDF)']['p@3']:.2f}). Test AUC is modest because the synthetic features carry little signal.", K.BLUE, "i", body_size=14)
    notes[15] = ("First measured numbers. The persona check is a sanity test with relevance defined as category membership, fixed before ranking; it is not a user study. "
                 "Offline policy evaluation gave SNIPS %.3f with an effective sample size of %.1f, so it is not evidence of a gain." % (P["snips"], P["effective_sample_size"]))

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, F.shot("08_recommendations.png"), 0.6, 1.3, 8.0, 5.0, border=True)
    K.text(s, 0.6, 6.4, 8.0, 0.4, "Ranked recommendations: match %, success estimate, reason", size=12, color=K.TXT, align="c", italic=True)
    K.picture(s, F.shot("07_dashboard.png"), 8.85, 1.3, 3.9, 2.4, border=True)
    K.text(s, 8.85, 3.74, 3.9, 0.4, "Dashboard after 12 recorded events", size=12, color=K.TXT, align="c", italic=True)
    K.picture(s, F.shot("09_learning_path.png"), 8.85, 4.2, 3.9, 2.4, border=True)
    K.text(s, 8.85, 6.64, 3.9, 0.4, "Staged learning path with next action", size=12, color=K.TXT, align="c", italic=True)
    notes[16] = "Real screenshots from the running application: one registered learner with a filled profile and 12 logged events."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{py['passed']} / {py['collected']}", "pytest tests passed", K.GREEN), (f"{sm['passed']} / {sm['checks']}", "end-to-end smoke checks", K.BLUE),
                                   (f"{rec8['mean_ms']:.0f} ms", "mean time, 8 recommendations", K.ORANGE), ("360-1440 px", "light and dark, no overflow", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["Estimated action benefits change sign after 6 events (best action quiz becomes homepage)", "Presented as an estimate, not a causal claim; documented as a limitation"],
            ["The suggested action is the same on every card of one learner", "Kept (it depends on learner state only); stated in the report"],
            [f"Offline policy evaluation: effective sample size {P['effective_sample_size']:.1f} of {P['test_samples']:,}", "Reported as weak evidence, not as a gain"]]
    K.table(s, 0.6, 3.1, [6.0, 6.13], rows, font_size=14, row_h=0.8)
    notes[17] = "The tests run against the real model and a throw-away database. The latency is a mean over 30 requests on 127.0.0.1."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    ce = F.CEIL
    rows = [["Challenge", "Corrective action"],
            ["Real OULAD was not used", "Documented generator as the data source; no external-validity claim"],
            ["Weak predictive signal, test AUC about 0.60", f"Ceiling check: with the hidden assessment score AUC reaches {ce['with_assess_score']['logistic_regression']['test_auc']:.2f}, so the limit is the generated label"],
            ["No real interaction log across learners", "No collaborative filtering; behaviour term is per learner"],
            ["Small hand-written catalogue (24 courses)", "Evaluated with personas and stated as a sanity check"],
            ["Ranking recomputed on every request", "Acceptable at this size (about %.0f ms); caching listed as future work" % rec8["mean_ms"]]]
    K.table(s, 0.6, 1.5, [4.6, 7.53], rows, font_size=14, row_h=0.8)
    notes[18] = "Each challenge is reported with what we did about it, and gaps that remain are stated."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Evaluate", "Six-seed study, confusion matrices, ablation of the eight terms, fairness by group.", K.BLUE, "1"),
        ("Compare", "Set the results against the base paper, stating where data and method differ.", K.GREEN, "2"),
        ("Document", "Final report, paper and deck with every figure regenerated from JSON.", K.ORANGE, "3"),
        ("Extend (future)", "Real OULAD data, collaborative filtering, a reinforcement-learning agent, a user study.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.1, 1.6, 2.9, 3.6, t, b_, col, gl, body_size=16)
    notes[19] = "Plan to the final review. The extensions on the right are outside this submission."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why synthetic data; why the hybrid does not beat content-only on the persona check; what the estimated action benefit means."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.scrub_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
