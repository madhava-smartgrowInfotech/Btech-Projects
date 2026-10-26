"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\Abstracts\\Templates\\Review_1_PPT.pptx."""

import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K
from .refs import N, REFS, _IDX

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "personal finance, expense categorisation, spending forecast, budgeting, FastAPI, React"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 34)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 20)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"Guide: {F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


# Problem statement and objectives are taken from 6.OBJECTIVES&PROBLEM STATEMENT.docx
PROBLEM_STATEMENT = [
    "Manual expense recording is tedious and is quickly abandoned by users",
    "Existing applications report past spending but do not forecast what is coming",
    "Generic budgeting advice ignores individual income patterns and commitments",
    "Unusual transactions go unnoticed until the statement is reviewed much later",
    "Need: a personal finance platform that categorises spending automatically, forecasts future expenditure, and gives advice grounded in the user's own data",
]
OBJECTIVES = [
    "Build secure user accounts with transaction import and manual entry",
    "Categorise expenses automatically from transaction descriptions using text classification",
    "Forecast upcoming expenses and savings using time-series models over spending history",
    "Detect anomalous transactions that deviate from a user's established pattern",
    "Generate personalised budget recommendations and alerts on threshold breaches",
    "Visualise spending, category breakdown and forecasts on an interactive dashboard",
]

# [work, year, approach, reported result / limitation]  (only what the papers state)
LIT_ROWS = [
    [f"Kharat et al. {N('base')} (base paper)", "2025", "BERT categoriser (50 classes), Q-learning budgets, LSTM savings forecast, Isolation Forest anomalies; Streamlit",
     "BERT accuracy 92.3 %; LSTM R2 0.63; anomaly F1 94 %. Own synthetic/private data, 80/20 splits; not released"],
    [f"To {N('to')}", "2026", "Goal-directed design and gamification for a youth finance app; interviews, survey, usability tests",
     "Design study with small user samples; no categorisation or forecasting model"],
    [f"Theerthala {N('theerthala')}", "2025", "Behavioural-finance data generation to fine-tune an 8B LLM advisor (19k samples)",
     "Comparable to 14-32B models at about 80 % lower cost; judged by an LLM jury; no transaction pipeline"],
    [f"Dilip and Janaki {N('finsense')}", "2026", "XGBoost + LSTM hybrid for expense prediction with SHAP explanations",
     "Lists RMSE, MAE, MAPE, R2 as metrics but gives no numeric results in the text read"],
    [f"Abiya et al. {N('leak')}", "2026", "Isolation Forest and K-Means on synthetic transactions to find leakage and subscriptions",
     "Reported better than rule-based budgeting; no metrics in the abstract; synthetic data"],
    [f"Batch survey {N('s2')}, {N('s3')}", "2025-26", "AI budget planning and expense prediction; AI platform for tracking and budget automation (titles only)",
     "Full texts not located or read; no figures quoted"],
    [f"Devlin et al. {N('bert')}; Araci {N('finbert')}", "2019", "BERT and its financial variant FinBERT: transfer learning for text classification",
     "Needs labelled data and heavy compute (as the base paper itself notes)"],
    [f"Liu et al. {N('iforest')}", "2008", "Isolation Forest: unsupervised anomaly detection by random partitioning", "Contamination rate must be chosen; many false alarms if mis-set"],
    [f"Salton and Buckley {N('tfidf')}", "1988", "TF-IDF term weighting for text retrieval and classification", "Bag of words: no context, unseen words carry no signal"],
    [f"Makridakis et al. {N('makri')}", "2018", "Compares statistical and machine-learning forecasters on many series", "Simple statistical methods are hard to beat on short, noisy series"],
]

GAPS = [
    f"The base paper's four-model design (BERT, Q-learning, LSTM, Isolation Forest) is evaluated on its own synthetic or private data with no released application {N('base')}",
    f"Related 2026 systems report no numeric results, or test only on synthetic data {N('finsense', 'leak')}",
    f"Design studies cover engagement and literacy but not automated categorisation or forecasting {N('to')}",
    "An affordable, open web platform that combines import, categorisation, forecasting, budget alerts and a dashboard is not reported (the batch survey gap)",
    "Few works say how a simple categoriser or trend model behaves on inputs it has not seen; this project measures that and states the failures",
]

ABSTRACT_POINTS = [
    ("The problem", "Digital transactions, several income sources, recurring bills and investments make personal finance hard to track. Existing apps lack intelligent recommendations, customisation and affordability.", K.ORANGE, "!"),
    ("Our idea", "A customisable, open web platform that tracks expenses, manages budgets and goals, and uses simple machine learning to categorise spending, forecast the next month and answer questions from the user's own data.", K.BLUE, "i"),
    ("The deliverable", "FINJARVIS: a secure web application with a React dashboard and FastAPI service. The abstract proposed Flask and MySQL; the delivered build uses FastAPI and SQLite.", K.GREEN, "✓"),
]


def pic_or_note(s, name, x, y, w, h):
    p = F.diag(name)
    if os.path.exists(p):
        K.picture(s, p, x, y, w, h)
        return True
    print("WARNING: missing", p)
    return False


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]

    # 1 title
    title_slide(S[0], "Track, categorise, forecast and advise from your own transactions", "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the title. One sentence: FINJARVIS lets a person record or import transactions, labels them automatically, forecasts next month's spending, "
                "scores financial health and answers questions from their own data.")

    # 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey and evidence"), ("04", "Existing system and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. The review covers why the problem matters and what is missing in current work, then the approach, the architecture and the objectives against what was built."

    # 3 abstract
    s = S[2]
    set_title(s, "Abstract: an AI-assisted personal finance manager")
    wipe(s)
    W, H = 3.85, 5.0
    for i, (t, body, col, gl) in enumerate(ABSTRACT_POINTS):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=20)
    K.text(s, 0.6, 6.6, 12.13, 0.5, "Keywords: personal finance automation, expense forecasting, AI in financial planning, linear regression, smart alerts, data visualisation, budgeting assistance.", size=12, color=K.TXT, italic=True)
    notes[3] = "Three points from the project abstract: the personal finance problem, the customisable AI platform, and what was delivered (with the framework change from Flask and MySQL stated openly)."

    # 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.35, 12.13, 1.2, fill=K.CARD)
    K.text(s, 0.82, 1.4, 11.7, 1.1, F.BASE_PAPER, size=13, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", "Four modules in one Streamlit assistant: BERT expense categorisation (16 to 50 classes, SMOTE), Q-learning budget recommendation, LSTM savings forecasting and Isolation Forest anomaly detection.", K.BLUE, "M"),
        ("Reported results", "BERT accuracy 92.3 %, F1 91.1 % (80/20 split). LSTM RMSE 137.2, MAE 89.5, R2 0.63 on a synthetic savings series. Isolation Forest precision 93 %, recall 94 %. Data is synthetic or private.", K.GREEN, "R"),
        ("What FINJARVIS takes and adds", "Takes the idea of one assistant for categorisation, budgeting and forecasting. Implements simple, inspectable versions (TF-IDF + logistic regression, linear trend, rule-based advice) as a runnable web platform and measures where they fail.", K.ORANGE, "A"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 3.15, t, b_, col, gl, body_size=13.5)
    K.box(s, 0.6, 6.05, 12.13, 0.8, fill=K.CARD)
    K.text(s, 0.82, 6.05, 11.7, 0.8, f"Not implemented here: BERT, reinforcement learning, LSTM and Isolation Forest. The registered base paper is compared with the project's simpler modules in the final review; datasets differ, so its numbers are not put on one scale with ours.",
           size=12, color=K.INK, anchor="m")
    notes[4] = ("The batch registered the IJRASET paper. Its four modules are the reference design. Our build deliberately uses simpler, explainable models, and that difference is stated now so no one expects BERT or LSTM results later.")

    # 5 literature table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Year", "Approach", "Reported result / limitation"]] + LIT_ROWS
    K.table(s, 0.6, 1.2, [2.55, 0.75, 4.55, 4.28], rows, font_size=10, row_h=0.5, header_size=11, align=["l", "c", "l", "l"])
    notes[5] = ("Details are only what the papers themselves state. Two batch-survey titles could not be located online or read in full, so no results are quoted from them. The last three rows are standard method papers used as background.")

    # 6 supporting evidence
    s = S[5]
    set_title(s, "Supporting evidence from the base paper")
    wipe(s)
    cats = ["BERT accuracy", "BERT F1", "IForest precision", "IForest recall", "IForest F1"]
    K.bar_chart(s, 0.6, 1.4, 6.6, 4.9, cats, [("Reported score (%)", [92.3, 91.1, 93.0, 94.0, 94.0])], colors=[K.BLUE], number_format="0.0", font_size=11, max_value=110, legend=False)
    K.text(s, 0.6, 6.35, 6.6, 0.7, f"Base paper {N('base')}: reported scores on its own (synthetic or private) data; not reproduced or comparable with this project's data.",
           size=11, color=K.TXT, italic=True)
    K.text(s, 7.5, 1.45, 5.25, 5.0, [
        ("**What the literature shows**", {"space_after": 8}),
        (f"A fine-tuned BERT can separate 50 expense categories on its own data {N('base')}.", {"bullet": True, "space_after": 8}),
        (f"Savings forecasting by LSTM reached only R2 0.63, which the paper itself calls a challenge {N('base')}.", {"bullet": True, "space_after": 8}),
        (f"Simple statistical forecasters are hard to beat on short, noisy series {N('makri')}.", {"bullet": True, "space_after": 8}),
        ("Caveat: the base paper's data is not public, so its numbers cannot be checked or reused. This project reports only its own measurements.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[6] = "This is published evidence on different data. We use it to show what the full multi-model design reports, not as a target we claim to match."

    # 7 existing system
    s = S[6]
    set_title(s, "Existing system and current practice")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.1, [("Note every spend by hand", K.NAVY), ("Choose a category yourself", K.NAVY), ("Review a past-only report", K.NAVY), ("Apply generic budget advice", K.NAVY), ("Spot odd charges late", K.NAVY)], size=14, gap=0.45)
    K.card(s, 0.6, 2.95, 5.95, 3.8, "For the user",
           "Manual expense recording is tedious and is abandoned within weeks.\nApps show what was spent but not what is coming.\nAdvice ignores the person's own income and commitments.", K.BLUE, "1", body_size=17)
    K.card(s, 6.78, 2.95, 5.95, 3.8, "In current tools",
           "Rule-based keyword matching lacks context.\nStatic budgets do not adapt to behaviour.\nCommercial finance apps can be costly and hard to customise.", K.ORANGE, "2", body_size=17)
    notes[7] = "Current practice, from the project introduction, problem statement and the base paper's description of traditional tools."

    # 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    heads = ["Manual entry", "Backward-looking", "One-size-fits-all advice", "Late discovery of anomalies"]
    bodies = [
        "Recording every transaction by hand is tedious; most users stop within weeks and the data becomes incomplete.",
        "Reports describe past spending. Nothing tells the user what next month is likely to cost.",
        "Generic budgeting tips ignore individual income patterns, commitments and savings goals.",
        "Unusual transactions are noticed only when the statement is reviewed much later.",
    ]
    for i in range(4):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.45 + r * 2.35, 5.95, 2.15, heads[i], bodies[i], C[i], str(i + 1), body_size=16)
    K.box(s, 0.6, 6.25, 12.13, 0.75, fill=K.CARD)
    K.text(s, 0.85, 6.25, 11.7, 0.75, f"Research adds: heavy models on private data {N('base')}, design studies without prediction {N('to')}, and evaluations on synthetic data only {N('leak')}.", size=14, color=K.INK, anchor="m")
    notes[8] = "The four limitations are the batch problem statement; the last line is what the recent papers leave open."

    # 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    for i, g in enumerate(GAPS):
        y = 1.3 + i * 1.12
        K.circle(s, 0.6, y + 0.1, 0.62, C[i % 4], str(i + 1), 18)
        K.text(s, 1.55, y, 11.15, 1.0, g, size=15.5, color=K.INK, anchor="m")
    notes[9] = ("Gap 4 is the survey conclusion of the batch: delivering the multi-model idea as an affordable, customisable web platform. "
                "The others come from reading the base paper and the recent papers.")

    # 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 3.1, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.85, [(p, {"bullet": True, "space_after": 8}) for p in PROBLEM_STATEMENT], size=18, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "Registration details, manually entered or imported CSV/Excel transactions, budgets, goals and holdings"),
                                 ("Output", "Category per transaction, next-month forecast, 0-100 health score, budget alerts, answers and reports"),
                                 ("Measures", "Categoriser accuracy, forecast error, correctness of answers, tests passed and response time")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.8, 3.85, 1.95)
        K.text(s, x + 0.25, 4.9, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.35, 3.4, 1.35, b_, size=13, color=K.TXT)
    notes[10] = "Read the statement slowly. The need is a platform that categorises automatically, forecasts, and gives advice grounded in the user's own data."

    # 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 4.9, [(f"{i}.  {o}", {"space_after": 14}) for i, o in enumerate(OBJECTIVES, 1)], size=23, color=K.INK)
    K.text(s, 0.6, 6.35, 12.13, 0.7, "The next slides and the final report state which objectives were met, partly met or not met, with measurements.",
           size=13, color=K.TXT, italic=True)
    notes[11] = "The six objectives from the proposal. Objective 4 (anomaly detection) was not built; that is stated openly on the expected-outcomes slide."

    # 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Record and import", "Add, edit and search transactions, or import a CSV/Excel file with a preview; bad rows are skipped with a message. Every record belongs to one user.", K.BLUE, "1"),
        ("Categorise", "TF-IDF word 1-2-grams and logistic regression label each description; a keyword table is the fallback. A user's correction retrains the model.", K.GREEN, "2"),
        ("Forecast and score", "A least-squares trend over monthly totals predicts next month; six weighted components give an explainable 0-100 health score.", K.ORANGE, "3"),
        ("Advise and report", "Budget alerts at 75, 90 and 100 % (checked when the dashboard is opened), goals, a rule-routed assistant answering from the user's data, and PDF, Excel and CSV reports.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.7, t, b_, col, gl, body_size=16)
    K.box(s, 0.6, 5.35, 12.13, 1.4)
    K.circle(s, 0.85, 5.65, 0.7, K.NAVY, "UI", 16)
    K.text(s, 1.8, 5.5, 10.7, 0.45, "FastAPI service + React dashboard + SQLite database", size=16, color=K.INK, bold=True)
    K.text(s, 1.8, 5.95, 10.7, 0.75, f"{F.N_ROUTES} API routes, {F.N_TABLES} tables, signed bearer tokens and bcrypt-hashed passwords. Simple, explainable models were chosen on purpose; where they are weak, the project measures and reports it.", size=14, color=K.TXT)
    notes[12] = "Four stages and the stack. The models are deliberately simple; the anomaly detector, reinforcement-learning budgeting and LSTM of the base paper are not part of the build."

    # 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    pic_or_note(s, "01_system_architecture.png", 0.6, 1.2, 7.6, 5.9)
    K.text(s, 8.4, 1.5, 4.35, 5.2, [
        ("**Layers**", {"space_after": 8}),
        (f"React dashboard on port {F.WEB_PORT}.", {"bullet": True}),
        (f"FastAPI on port {F.API_PORT}: {F.N_ROUTES} routes, bearer-token guard.", {"bullet": True}),
        ("Service layer: transactions, budgets, goals, investments, analytics, assistant, reports, import.", {"bullet": True}),
        ("ML modules: expense classifier, spending prediction, financial health.", {"bullet": True}),
        ("SQLAlchemy over one SQLite file with six tables.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[13] = "Follow the diagram top to bottom: the dashboard calls the API, the API calls the services, the services use the ML modules and the database."

    # 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes: objectives against what was built")
    wipe(s)
    rows = [["Objective", "What was built", "Status"],
            ["1  Accounts, import and manual entry", "Sign-up and login, bcrypt, signed tokens, CSV/Excel import with preview", "Met"],
            ["2  Automatic categorisation", "TF-IDF + logistic regression on a 51-example seed list (not BERT)", "Met, simple form"],
            ["3  Time-series forecast", "Linear trend over monthly expense totals; no ARIMA or LSTM; expenses only", "Partly met"],
            ["4  Anomaly detection", "Not built; only the largest expense in a window is shown", "Not met"],
            ["5  Budget advice and alerts", "User-set budgets, alerts at 75/90/100 %, rule-based advice (no reinforcement learning)", "Partly met"],
            ["6  Interactive dashboard", f"{F.N_PAGES} React pages with charts, health score and forecast", "Met"]]
    K.table(s, 0.6, 1.4, [3.5, 6.9, 1.73], rows, font_size=14, row_h=0.64, first_bold=True)
    K.text(s, 0.6, 6.0, 12.13, 1.0, "Also stated now: no loan tracker and no scheduler were built, and the abstract's Flask and MySQL became FastAPI and SQLite. "
           "Measured results (accuracy, forecast error, tests, latency) follow in Review 2 and the final review.", size=14, color=K.TXT, italic=True)
    notes[14] = ("This is the problem-identification review, but the product already exists, so the slide compares each objective with what was built. Anomaly detection was not built and is reported as a gap.")

    # 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    keys = ["base", "to", "theerthala", "finsense", "leak", "s2", "s3", "bert", "finbert", "iforest", "tfidf", "makri", "sklearn"]
    keys = sorted(keys, key=lambda k: _IDX[k])
    items = [(f"[{_IDX[k]}] {REFS[_IDX[k] - 1]}", {"space_after": 4}) for k in keys]
    half = (len(items) + 1) // 2
    K.text(s, 0.6, 1.25, 6.0, 5.8, items[:half], size=12, color=K.INK)
    K.text(s, 6.75, 1.25, 6.0, 5.8, items[half:], size=12, color=K.INK)
    notes[15] = "Selected references; the complete numbered list is in the project report."

    # 16 thank you
    thank_you(S[15])
    notes[16] = ("Likely questions: why simple models instead of BERT and LSTM (small data, explainability, measured on the demo); what was not built (anomaly detection, reinforcement learning, loan tracker); "
                 "why FastAPI and SQLite instead of Flask and MySQL.")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
