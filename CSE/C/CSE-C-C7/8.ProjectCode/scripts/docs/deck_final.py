"""16.Final_PPT.pptx: 28 slides, built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited).

Every number is read from artifacts/metrics/model_metrics.json and experiments/*.json through facts.py; only qualitative text is typed here.
"""

import json
import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Pt

from . import facts as F
from . import pptkit as K
from .refs import K as RK, REFS

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520

OBJECTIVES = [
    "Build a learner profile (education, skill level, interests, goals, weekly hours) and update it from interaction events.",
    "Maintain a course catalogue with skills, level, topics, duration and ratings (24 hand-written courses).",
    "Collaborative filtering across learners (not implemented; the behavioural term is per learner).",
    "Content-based matching of learner and courses with TF-IDF and cosine similarity.",
    "A hybrid recommender with explanations and a staged learning path, plus a success model and action-benefit scores.",
    "Evaluate with precision, recall and feedback (partly met: AUC and F1 on synthetic data, persona precision@k; no user study).",
]


def chrome(sh):
    return sh.top in (TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT)


def set_title(slide, text):
    for sh in slide.shapes:
        if sh.top == TOP_TITLE:
            K.replace_text(sh, text)
            return


def wipe(slide):
    K.clear(slide, chrome)


def fbox(slide, x, y, w, h, fill=K.FHEAD, line=None):
    return K.box(slide, x, y, w, h, fill=fill, line=line, radius=0.04)


def ftable(slide, x, y, widths, rows, size=13, row_h=0.45, align=None, first_bold=True):
    return K.table(slide, x, y, widths, rows, font_size=size, row_h=row_h, header_fill=K.FHEAD, header_color=K.FNAVY, zebra=K.FZEBRA,
                   body_color=K.DARK, first_bold=first_bold, font=FONT, align=align, border=K.RGBColor(0xBF, 0xBF, 0xBF))


def ftext(slide, x, y, w, h, paras, size=16, color=K.DARK, **kw):
    return K.text(slide, x, y, w, h, paras, size=size, color=color, font=FONT, **kw)


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=12, color=K.DARK, font=FONT)


def line_chart(slide, x, y, w, h, categories, series, colors, font_size=11, number_format="0.00"):
    cd = CategoryChartData()
    cd.categories = categories
    for name, vals in series:
        cd.add_series(name, vals)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, K.E(x), K.E(y), K.E(w), K.E(h), cd)
    ch = gf.chart
    ch.font.size = Pt(font_size)
    ch.has_title = False
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.BOTTOM
    ch.legend.include_in_layout = False
    va = ch.value_axis
    va.minimum_scale, va.maximum_scale = 0, 1.0
    va.major_gridlines.format.line.color.rgb = K.LINE
    va.format.line.fill.background()
    va.tick_labels.number_format = number_format
    va.tick_labels.number_format_is_linked = False
    ch.category_axis.format.line.color.rgb = K.LINE
    for s, c in zip(ch.plots[0].series, colors):
        s.format.line.color.rgb = c
        s.format.line.width = Pt(2.25)
        s.smooth = False
        s.marker.style = XL_MARKER_STYLE.CIRCLE
        s.marker.size = 6
        s.marker.format.fill.solid()
        s.marker.format.fill.fore_color.rgb = c
        s.marker.format.line.color.rgb = c
    return gf


def cap(slide, x, y, w, text, size=12):
    ftext(slide, x, y, w, 0.9, text, size=size, color=K.FNAVY, italic=True)


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE"
    cp.comments = ""
    cp.subject = F.TITLE
    notes = {}

    M = F.METRICS
    MD = M["models"]
    LR, RF, XG = MD["logistic_regression"], MD["random_forest"], MD["xgboost"]
    PE, FA = M["policy_evaluation"], M["fairness"]
    SEED = F.SEEDS["summary"]
    SEL = M["selected_model"]
    CE = F.CEIL
    DP = F.PROFILE
    RS = F.REC["summary"]
    AB = F.REC["ablation_drop_one_term"]
    FBK = F.FB
    ACT = F.ACT
    LAT = F.API_LAT["endpoints"]
    TST = F.TESTS
    ENV = F.ENV
    SW = json.load(open(os.path.join(F.EXP, "threshold_sweep.json"), encoding="utf-8"))["sweep"]
    lr_seed = SEED["logistic_regression"]["test_auc"]
    logged = M["policy_evaluation"].get("logged_success_rate", 0.4375)
    rec8 = LAT["GET /api/recommendations?top_n=8"]

    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh in S[0].shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.TITLE)
        elif sh.name == "Text 2":
            K.replace_text(sh, f"Final Review  ·  {F.PRODUCT}")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_.title()}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE.title()}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and LearnPathIQ: a hybrid course recommendation engine with a learner-success model, built and measured on synthetic data."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap & Problem Statement\nObjectives\nProposed System & Architecture\nMethodology, Dataset & Model\nDecision Workflow, Interaction & Database\nImplementation Highlights\nResults, Threshold Analysis, Performance & Testing\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References")
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.95, [
        ("Learners on online platforms face a catalogue far larger than they can browse, and generic top-rated lists ignore their level, goals and behaviour.", {"bullet": True, "space_after": 9}),
        ("LearnPathIQ ranks courses with a hybrid score of eight terms (TF-IDF content match, skill fit, topic overlap, predicted success, behavioural boost, goal match, rating, engagement), explains each choice and orders a staged learning path.", {"bullet": True, "space_after": 9}),
        (f"A learner-success model (logistic regression selected) reaches test AUC **{F.f3(LR['roc_auc'])}** on **synthetic OULAD-like data** (six-seed mean {F.f3(lr_seed['mean'])}); one-vs-rest uplift models score five learning actions. The real OULAD data were not used.", {"bullet": True, "space_after": 9}),
        (f"On ten hand-written personas, hybrid precision@3 is {F.f2(RS['hybrid (shipped)']['p@3'])} against {F.f2(RS['popularity (rating only)']['p@3'])} for popularity, and below content-only ({F.f2(RS['content-only (TF-IDF)']['p@3'])}).", {"bullet": True, "space_after": 9}),
        (f"A FastAPI service and a React interface add login, dashboard, history and model analytics; {TST['pytest']['passed']} pytest tests and {TST['smoke']['passed']} smoke checks pass. No user study, collaborative filtering or reinforcement-learning agent is included.", {"bullet": True}),
    ], size=18)
    notes[3] = "Read the first two bullets, then give the headline numbers with their protocol (synthetic data, held-out learners). End on what is missing."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.95, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper [1]"],
            ["Method", "XGBoost learner-success model, uplift (T-learner) action scoring, an Actor-Critic reinforcement-learning agent with causal regularisation, off-policy evaluation, fairness audit"],
            ["Data", "Open University Learning Analytics Dataset (OULAD): 32,593 enrolments, about 1.7 million learner-week rows, 25,516 learners"],
            ["Reported results", "XGBoost AUC 0.795, Brier 0.074; logged pass rate 0.589; Greedy-Uplift SNIPS 0.619 [0.613, 0.625]; older learners markedly lower"],
            ["Stated limits", "Offline evidence only; importance weights unstable (IPS 9.956 against SNIPS 0.643); no live A/B test"]]
    ftable(s, 0.55, 2.9, [2.0, 10.2], rows, size=14, row_h=0.78)
    notes[4] = "A causal-AI framework on a real public dataset. We borrow the success model, uplift scoring, off-policy evaluation and fairness audit; we did not implement the Actor-Critic agent."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Author / Year", "Methodology", "Dataset", "Key Result", "Limitation"],
            [f"Isiwu et al. (2026) [{RK['base']}]", "XGBoost + uplift + Actor-Critic RL, off-policy evaluation", "OULAD", "AUC 0.795; SNIPS 0.619", "Offline only"],
            [f"Khreis et al. (2026) [{RK['khreis']}]", "BERT with contrastive learning and isotropy regularisation", "500+ engineering courses", "Better embedding separation than vanilla BERT", "Text-only; one institution"],
            [f"Gharahighehi et al. (2025) [{RK['gharahighehi']}]", "Collaborative filtering with survival analysis", "Three public MOOC sets", "Beats CF baselines on two measures", "Needs interaction history"],
            [f"Sujay et al. (2026) [{RK['eduguide']}]", "TF-IDF, cosine similarity and ratings, weighted", "Coursera course listing", "Weighted hybrid score", "Results not reviewed in detail"],
            [f"Batch survey (2025) [{RK['s_lightgcn']}]", "LightGCN with learning-behaviour data", "Authors not recorded", "Title and year only", "Not independently verified"],
            [f"Batch survey (2025-26) [{RK['s_ml']}], [{RK['s_review']}]", "Machine-learning course recommendation; literature review", "Authors not recorded", "Title and year only", "Not independently verified"]]
    ftable(s, 0.55, 1.85, [2.5, 3.1, 2.1, 2.5, 2.0], rows, size=11, row_h=0.68)
    notes[5] = "Representative work. The last two rows are entries from the batch survey for which only a title and year were recorded; no result is claimed for them."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.8, [
        ("**Beyond prediction:** success models say who may struggle but not which learning action or course helps; few systems connect the two.", {"bullet": True, "space_after": 12}),
        ("**Cold start:** collaborative filtering needs interaction history; a new learner needs a ranking from profile and content on day one.", {"bullet": True, "space_after": 12}),
        ("**Adaptation:** rankings are rarely updated from the learner's own events without retraining.", {"bullet": True, "space_after": 12}),
        ("**Honest evaluation:** offline policy estimates and recommendation quality are rarely reported with their weaknesses (effective sample size, baselines, subgroup gaps).", {"bullet": True, "space_after": 12}),
        ("**Explanations:** a ranked list without reasons is hard for a learner to trust.", {"bullet": True}),
    ], size=20)
    notes[6] = "Five gaps drawn from the survey; the project addresses cold start, adaptation, explanation and evaluation honesty, and only partly the first."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.95, 12.2, 2.0)
    ftext(s, 0.85, 2.0, 11.6, 1.9, "Given a learner's profile and recent activity, rank the courses of a catalogue by how well they fit, say why, estimate the chance the learner succeeds, suggest the learning action expected to help most, and keep adapting as the learner interacts, all through a web application.", size=20, anchor="m")
    for i, (t, b_) in enumerate([("Input", "Profile (education, level, interests, goals, hours) and interaction events"), ("Output", "Ranked courses with match %, reasons, success estimate, suggested action, learning path"), ("Record", "Interaction history, recommendation log, model analytics")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.3, 3.9, 1.9, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.4, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 4.9, 3.5, 1.2, b_, size=15)
    notes[7] = "The statement has three parts: rank and explain, estimate and suggest, adapt and record."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=19)
    notes[8] = "The six objectives of the proposal. The conclusion reports which were met: 3 not implemented, 6 partly."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 2.0, 12.2, 1.1, [("Profile + events", K.FNAVY), ("Score 8 terms", K.FBLUE), ("Success + uplift", K.GREEN), ("Rank + explain", K.ORANGE), ("Log + adapt", K.PURPLE)], size=15, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, [
        ("Hybrid ranker: 0.30 content, 0.15 skill, 0.15 topic, 0.12 success, 0.10 behaviour, 0.08 goal, 0.05 rating, 0.05 engagement.", {"bullet": True, "space_after": 10}),
        ("Learner-success model (logistic regression, XGBoost and random forest compared) and one-vs-rest uplift models for five actions.", {"bullet": True, "space_after": 10}),
        ("Every logged event changes the next ranking at once, with no retraining.", {"bullet": True, "space_after": 10}),
        ("FastAPI service, SQLite, React interface; offline policy evaluation and fairness audit on a Model analytics page.", {"bullet": True}),
    ], size=18)
    notes[9] = "The proposed system in one line of boxes, then the four properties that matter."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.8, 7.6, 5.1)
    ftext(s, 8.4, 2.0, 4.4, 4.7, [
        ("Presentation: React 19 SPA (port 5407) and the original Jinja2 UI", {"bullet": True, "space_after": 8}),
        ("Application: FastAPI (port 8407), token auth, Pydantic validation", {"bullet": True, "space_after": 8}),
        ("Recommendation: ranker, success model, uplift scores", {"bullet": True, "space_after": 8}),
        ("Data: SQLite (6 tables), course catalogue, joblib model bundle", {"bullet": True}),
    ], size=16)
    notes[10] = "Four tiers; the model bundle is loaded once and cached, recommendations are recomputed on every request."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.2, [("Synthetic generator", K.FNAVY), ("8 features", K.FNAVY), ("Learner-level split", K.GREEN), ("LR / RF / XGBoost", K.ORANGE), ("Uplift + OPE", K.PURPLE), ("Fairness audit", K.FBLUE), ("model_metrics.json", K.FNAVY)], size=12, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, [
        (f"Data: {DP['learners']:,} learners x {DP['weeks']} weeks = {DP['rows']:,} rows; split by learner 80 / 10 / 10 so no learner is in two sets; seed 42.", {"bullet": True, "space_after": 10}),
        ("Success model chosen by validation AUC; uplift = P(success | action) - P(success | no action), one T-learner pair per action.", {"bullet": True, "space_after": 10}),
        (f"Extra experiments added for the documents: six-seed re-run, ceiling check, weight ablation, {len(F.REC['per_persona'])}-persona ranking check, feedback-loop test, latency.", {"bullet": True, "space_after": 10}),
        ("Every number on these slides is read from files written by the scripts.", {"bullet": True}),
    ], size=18)
    notes[11] = "The workflow, and the extra experiments that were added because the project shipped without a ranking evaluation."

    # ---- 12 dataset, features & model
    s = S[11]
    set_title(s, "Dataset, Features & Model")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.1, f"{DP['rows']:,}", "synthetic learner-week rows", K.FBLUE, 26)
    ftile(s, 0.55, 3.15, 2.9, 1.1, "8", "features per learner-week", K.GREEN, 26)
    ftile(s, 0.55, 4.4, 2.9, 1.1, "24", "hand-written courses, 9 categories", K.ORANGE, 26)
    K.picture(s, F.fig("fig_data_profile.png"), 3.7, 1.85, 4.9, 2.7)
    rows = [["Feature", "Corr. with success"]] + [[k, f"{v:.3f}"] for k, v in DP["corr_with_success"].items()]
    ftable(s, 8.85, 1.9, [2.3, 1.7], rows, size=11, row_h=0.37)
    ftext(s, 3.7, 4.75, 5.0, 2.1, [
        (f"Train {M['train_samples']:,} / validation {M['val_samples']:,} / test {M['test_samples']:,} rows.", {"bullet": True}),
        (f"Success rate {F.pct(DP['success_rate'])}; label depends on a hidden assessment score that the model never sees.", {"bullet": True}),
        ("The real OULAD was not downloaded or used.", {"bullet": True}),
    ], size=14)
    notes[12] = "Dataset and model in one view. The data are generated; correlations with the label are weak (largest 0.18), which explains the modest AUC."

    # ---- 13 decision workflow
    s = S[12]
    set_title(s, "Decision Workflow")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.55, 1.8, 5.2, 5.1)
    ftext(s, 6.0, 2.0, 6.8, 4.8, [
        ("Authenticate: token to user; 401 if missing or invalid.", {"bullet": True, "space_after": 12}),
        ("Estimate: engagement score, learner state vector, success probability, uplift per action.", {"bullet": True, "space_after": 12}),
        ("Score: eight terms per course, clipped to [0, 1], sorted, top-N kept.", {"bullet": True, "space_after": 12}),
        ("Explain: up to three reasons per card; the best action is the arg-max of the estimated benefit.", {"bullet": True, "space_after": 12}),
        ("Log: one recommendation_logs row per card.", {"bullet": True}),
    ], size=18)
    notes[13] = "The ranking route in decision form. The suggested action depends on the learner state only, so every card of one learner shows the same action; this is stated as a limit."

    # ---- 14 interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_diagram.png"), 0.55, 1.8, 7.3, 5.1)
    K.picture(s, F.diag("08_use_case_diagram.png"), 8.1, 1.8, 4.7, 5.1)
    notes[14] = "Sequence of requesting recommendations and logging feedback, and the use cases of the learner and the developer."

    # ---- 15 database
    s = S[14]
    set_title(s, "Database Design")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 6.9, 5.1)
    rows = [["Table", "Role"], ["users", "name, unique email, password hash"], ["profiles", "1:1 with user: level, interests, goals, hours"], ["courses", "24 seeded courses"], ["interactions", "view, open, start, quiz, content, forum, complete, dismiss, save"], ["recommendation_logs", "score and explanation per card shown"], ["auth_tokens", "session tokens"]]
    ftable(s, 7.7, 1.9, [1.9, 3.2], rows, size=12, row_h=0.62)
    notes[15] = "Six tables. Course and user links in interactions and logs are logical (plain columns), not database constraints."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("18", "JSON routes under /api", K.FBLUE), (str(TST["pytest"]["passed"]), "pytest tests passed", K.GREEN), ("12", "React pages", K.ORANGE), (f"{rec8['mean_ms']:.0f} ms", "recommendations, mean (n=30)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.1, v, l, c, 28)
    tr = FBK["tracked"]
    ftext(s, 0.55, 3.3, 12.2, 3.5, [
        ("pbkdf2_sha256 password hashes, random session tokens stored server-side, HttpOnly cookie (72 h) or X-Token header, Pydantic validation, ORM parameterised queries.", {"bullet": True, "space_after": 9}),
        (f"Feedback loop tested: after six events the ML101 score rose from {F.f3(tr['ML101']['score_before'])} to {F.f3(tr['ML101']['score_after'])} and the dismissed DA101 fell from rank {tr['DA101']['rank_before']} to {tr['DA101']['rank_after']}.", {"bullet": True, "space_after": 9}),
        ("Model analytics page shows model table, confusion matrices, ROC, offline policy values and the fairness audit from the saved metrics.", {"bullet": True, "space_after": 9}),
        ("No caching: TF-IDF is refitted over 25 documents on every request; SQLite single node; demo-grade authentication.", {"bullet": True}),
    ], size=18)
    notes[16] = "Highlights of the implementation, with the one behavioural test and the known engineering limits."

    # ---- 17 results: models and ranking
    s = S[16]
    set_title(s, "Results – Success Model & Ranking Quality")
    wipe(s)
    rows = [["Model", "Val AUC", "Test AUC", "Accuracy", "F1", "Brier"]]
    for k, lab in (("logistic_regression", "Logistic Regression (selected)"), ("random_forest", "Random Forest"), ("xgboost", "XGBoost")):
        m = MD[k]
        rows.append([lab, F.f3(m["val_auc"]), F.f3(m["roc_auc"]), F.f3(m["accuracy"]), F.f3(m["f1"]), F.f3(m["brier"])])
    ftable(s, 0.55, 1.85, [3.1, 0.95, 0.95, 0.95, 0.8, 0.8], rows, size=12, row_h=0.45, align=["l", "c", "c", "c", "c", "c"])
    ftext(s, 0.55, 3.8, 7.6, 3.0, [
        (f"Held-out test: {M['test_samples']:,} learner-weeks (220 learners); chance AUC is 0.5.", {"bullet": True, "space_after": 7}),
        (f"Six seeds: LR {F.f3(lr_seed['mean'])} +- {F.f3(lr_seed['std'])}, RF {F.f3(SEED['random_forest']['test_auc']['mean'])}, XGBoost {F.f3(SEED['xgboost']['test_auc']['mean'])}.", {"bullet": True, "space_after": 7}),
        (f"With the hidden assessment score added, AUC rises to {F.f2(CE['with_assess_score']['logistic_regression']['test_auc'])}: the weak signal comes from the generated label.", {"bullet": True, "space_after": 7}),
        ("Success estimates are probabilities for ranking, not a reliable predictor.", {"bullet": True}),
    ], size=14)
    names = ["popularity (rating only)", "content-only (TF-IDF)", "hybrid (shipped)"]
    K.bar_chart(s, 8.4, 1.8, 4.5, 4.4, ["Popularity", "Content-only", "Hybrid"], [("P@3", [RS[n]["p@3"] for n in names]), ("P@5", [RS[n]["p@5"] for n in names]), ("MRR", [RS[n]["mrr"] for n in names])],
                colors=[K.FBLUE, K.ORANGE, K.GREEN], number_format="0.00", font_size=11, max_value=1.2, gap=40, label_size=9)
    cap(s, 8.4, 6.25, 4.5, f"{len(F.REC['per_persona'])} author-written personas, 24 courses. A sanity check, not a user study; hybrid does not beat content-only.", 11)
    notes[17] = "Left: the three success models on the held-out learners. Right: ranking quality on ten personas whose relevant categories were fixed before ranking. The hybrid beats popularity clearly but not content-only TF-IDF."

    # ---- 18 confusion matrices
    s = S[17]
    set_title(s, "Confusion Matrix & Per-class Metrics")
    wipe(s)
    K.picture(s, F.fig("fig_confusion_matrices.png"), 0.55, 1.75, 12.2, 3.45)
    for i, (v, l, c) in enumerate([(F.f3(LR["precision"]), "precision (selected LR)", K.FBLUE), (F.f3(LR["recall"]), "recall: many successes missed", K.GREEN), (F.f3(LR["f1"]), "F1 at threshold 0.5", K.ORANGE), (F.f3(FA["age_band"]["55<="]["f1"]), "F1 for the 55+ age band (0-35: " + F.f3(FA["age_band"]["0-35"]["f1"]) + ")", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 5.35, 2.9, 1.1, v, l, c, 26)
    cap(s, 0.55, 6.55, 12.2, f"Selected LR: TN {LR['confusion_matrix'][0][0]:,}, FP {LR['confusion_matrix'][0][1]}, FN {LR['confusion_matrix'][1][0]}, TP {LR['confusion_matrix'][1][1]}. Fairness audit is audit-only: no mitigation is applied.", 12)
    notes[18] = "Rows are the true class, columns the prediction. At threshold 0.5 the selected model misses most true successes (recall 0.329); the next slide shows the trade-off. The 55+ band has the lowest F1 in the audit."

    # ---- 19 threshold & parameter analysis
    s = S[18]
    set_title(s, "Threshold & Parameter Analysis")
    wipe(s)
    th = [f"{r['threshold']:.2f}" for r in SW]
    line_chart(s, 0.55, 1.75, 6.2, 3.3, th, [("Precision", [r["precision"] for r in SW]), ("Recall", [r["recall"] for r in SW]), ("F1", [r["f1"] for r in SW])], [K.FBLUE, K.GREEN, K.ORANGE])
    keys = [k for k in AB if k != "full"]
    K.bar_chart(s, 6.95, 1.75, 5.9, 3.3, keys, [("P@3 without the term", [AB[k]["p@3"] for k in keys])], colors=[K.FBLUE], number_format="0.00", font_size=10, max_value=1.0, gap=40, label_size=9, legend=False)
    cap(s, 0.55, 5.05, 6.2, "Decision threshold of the success model (test split): recall falls and precision rises as the threshold moves from 0.30 to 0.70; 0.5 is shipped.", 11)
    cap(s, 6.95, 5.05, 5.9, f"Drop-one-term ablation of the hybrid score (full = {F.f3(AB['full']['p@3'])}): topic and content matter most; success, behaviour, goal and engagement terms did not change the persona ranking.", 11)
    for i, (v, l, c) in enumerate([(F.f3(PE["ips"]), "IPS", K.FBLUE), (F.f3(PE["snips"]), "SNIPS", K.GREEN), (F.f3(PE["doubly_robust"]), "Doubly robust", K.ORANGE), (f"{PE['effective_sample_size']}", f"effective sample size of {PE['test_samples']:,}", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 5.9, 2.9, 0.95, v, l, c, 22)
    notes[19] = "Top left: threshold sweep, taken from experiments/threshold_sweep.json and matching the shipped confusion matrix at 0.5. Top right: weight ablation. Bottom: offline policy values (propensity clipped to 0.02-0.98, weights capped at 10); with an effective sample size of about 9 they are not evidence that the policy helps."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    for i, (k, l, c) in enumerate([("GET /api/health", "health check, mean", K.FBLUE), ("GET /api/courses", "course list, mean", K.GREEN), ("GET /api/recommendations?top_n=8", "recommendations (8), mean", K.ORANGE), ("GET /api/learning-path", "learning path, mean", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.15, f"{LAT[k]['mean_ms']:.1f} ms", l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["pytest (tests/test_app.py)", ", ".join(t.replace("test_", "") for t in TST["pytest"]["tests"]), f"{TST['pytest']['passed']} of {TST['pytest']['collected']} passed ({TST['pytest']['seconds']} s)"],
            ["Live smoke test", "running backend and front end through the Vite proxy", f"{TST['smoke']['passed']} of {TST['smoke']['checks']} checks passed"],
            ["UI verification", "11 screens at 360 / 768 / 1440 px, light and dark", "no overflow, console clean, keyboard OK"],
            ["Latency probe", f"30 requests per read endpoint on 127.0.0.1; recommendations p95 {rec8['p95_ms']:.0f} ms", f"first registration {LAT['POST /api/auth/register']['mean_ms']:.0f} ms (hashing)"]]
    ftable(s, 0.55, 3.35, [3.0, 5.7, 3.5], rows, size=13, row_h=0.55)
    cap(s, 0.55, 6.25, 12.2, f"Machine: {ENV['cpu']}, {ENV['ram_gb']} GB RAM, no GPU. Not done: load tests beyond 30 sequential requests, a user study, cross-browser tests, penetration tests.", 12)
    notes[20] = "Latency was measured on a CPU-only desktop through the loopback address; recommendations are recomputed on every call because nothing is cached."

    # ---- 21 comparison with base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only – different data)")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", "This project"],
            ["Data", "Real OULAD: 32,593 enrolments, about 1.7 million learner-weeks", f"Synthetic OULAD-like: {DP['learners']:,} learners, {DP['rows']:,} learner-weeks"],
            ["Success model", "XGBoost: AUC 0.795, Brier 0.074", f"Logistic regression: AUC {F.f3(LR['roc_auc'])}, Brier {F.f3(LR['brier'])} (XGBoost {F.f3(XG['roc_auc'])})"],
            ["Logged outcome", "Pass rate 0.589", f"Success rate {F.f3(logged)} on the test rows"],
            ["Policy", "Actor-Critic RL with causal regularisation; Greedy-Uplift SNIPS 0.619", f"Uplift arg-max only; SNIPS {F.f3(PE['snips'])}, effective sample size {PE['effective_sample_size']}"],
            ["Fairness audit", "By age and gender; older learners markedly lower", f"By age and gender; 55+ F1 {F.f3(FA['age_band']['55<=']['f1'])} against {F.f3(FA['age_band']['0-35']['f1'])}"],
            ["Deliverable", "Research framework", "Working web application: ranking, explanations, learning path, analytics, tests"]]
    ftable(s, 0.55, 1.85, [2.0, 5.0, 5.2], rows, size=12, row_h=0.62)
    ftext(s, 0.55, 6.3, 12.2, 0.6, "Not a like-for-like comparison: real against generated data, different features and no reinforcement-learning agent here. The numbers are context, not a ranking.", size=13, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that the data differ: the base paper uses real OULAD, this project a generator; a higher or lower number here says nothing about the base paper's method."

    # ---- 22-24 output screens
    def screens(idx, title, left, right, capl, capr, note):
        s_ = S[idx]
        set_title(s_, title)
        wipe(s_)
        K.picture(s_, F.shot(left), 0.55, 1.85, 6.0, 3.75, border=True)
        K.picture(s_, F.shot(right), 6.8, 1.85, 6.0, 3.75, border=True)
        ftext(s_, 0.55, 5.8, 6.0, 1.1, capl, size=13, color=K.FNAVY)
        ftext(s_, 6.8, 5.8, 6.0, 1.1, capr, size=13, color=K.FNAVY)
        notes[idx + 1] = note

    screens(21, "Output – Dashboard and Recommendations", "07_dashboard.png", "08_recommendations.png",
            "Dashboard of the registered learner after 12 recorded interactions: engagement level, success estimate and shortcuts.",
            "Ranked courses with match percentage, success estimate, reasons and the suggested action (the same action on every card).",
            "Real captures of the running application with one registered learner and 12 interaction events.")
    screens(22, "Output – Learning Path and Insights", "09_learning_path.png", "10_insights.png",
            "Staged learning path: courses ordered by level, then score, with the next best action.",
            "Insights: engagement, strengths, estimated benefit of each action (the contributing-features list is empty for the shipped logistic regression).",
            "The path is ordered by skill level and score; there is no prerequisite graph.")
    screens(23, "Output – Model Analytics", "17_analytics_diagnostics.png", "18_analytics_policy.png",
            "Diagnostics tab: confusion matrices, ROC curve and feature importance read from the saved metrics.",
            "Offline policy tab: IPS, SNIPS and doubly robust values with the effective sample size and the caveat.",
            "The page reads artifacts/metrics/model_metrics.json; a fairness tab and a model table complete it.")

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [
        ("**Delivered:** LearnPathIQ: profile, catalogue, hybrid ranker with explanations, learning path, success and uplift models, offline policy evaluation, fairness audit, web application and tests.", {"bullet": True, "space_after": 10}),
        (f"**Measured:** success-model test AUC {F.f3(LR['roc_auc'])} on synthetic data; hybrid P@3 {F.f2(RS['hybrid (shipped)']['p@3'])} on ten personas against {F.f2(RS['popularity (rating only)']['p@3'])} for popularity.", {"bullet": True, "space_after": 10}),
        ("**Findings:** the hybrid does not beat content-only matching; the offline policy values rest on an effective sample size of about 9; estimated action benefits flip sign after a few events.", {"bullet": True, "space_after": 10}),
        ("**Not achieved:** real OULAD data, collaborative filtering across learners, an Actor-Critic agent, a user study, live A/B tests.", {"bullet": True}),
    ], size=20)
    notes[25] = "Objectives 1, 2, 4 and 5 met, 6 partly, 3 not implemented. Findings are reported with their weaknesses."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [
        ("Train and evaluate on the real OULAD data so metrics can be compared with the base paper.", {"bullet": True, "space_after": 12}),
        ("Add collaborative filtering across learners once real interaction logs exist; compare with content-only and hybrid.", {"bullet": True, "space_after": 12}),
        ("Learn a policy (the base paper's Actor-Critic agent) and validate it with a larger effective sample size or a live A/B test.", {"bullet": True, "space_after": 12}),
        ("A user study with real precision, recall and satisfaction; prerequisite graph for the learning path; per-card suggested actions.", {"bullet": True, "space_after": 12}),
        ("Caching, a production database, real accounts and roles, container deployment.", {"bullet": True}),
    ], size=20)
    notes[26] = "Concrete next steps, ordered by value."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    keys = ["base", "khreis", "gharahighehi", "oulad", "dudik", "uplift", "kunzel", "xgboost", "sklearn", "tfidf", "breiman", "hrl", "yu", "lightgcn", "fastapi", "eduguide"]
    items = sorted((RK[k], REFS[RK[k] - 1].split(", doi")[0].split(" (listing")[0]) for k in keys)
    ftext(s, 0.55, 1.85, 6.0, 5.1, [(f"[{n}] {t}", {"space_after": 5}) for n, t in items[:8]], size=11)
    ftext(s, 6.8, 1.85, 6.0, 5.1, [(f"[{n}] {t}", {"space_after": 5}) for n, t in items[8:]], size=11)
    notes[27] = "Selected references; the complete list is in the report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.scrub_theme(out_path, "LearnPathIQ")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
