"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers are defined here. All numbers come from facts.py (experiments/metrics.json, api_latency.json).
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"
OUT = os.path.join(F.BATCH, "13.Review_2_PPT.pptx")


# ------------------------------------------------------------------ helpers
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
    cp.keywords = "personal finance, expense categorisation, TF-IDF, spending forecast, health score, FastAPI, React"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=4):
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
            K.replace_text(sh, F.TITLE, 30)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag):
    """Copy of a diagram with its white margins removed (written to the temp folder, source untouched)."""
    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"c11_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    K.picture(slide, F.shot(name), x, y, w, h - 0.5, border=True)
    K.text(slide, x, y + h - 0.45, w, 0.45, caption, size=11, color=K.TXT, align="c", italic=True)


def line_counts():
    """Lines of code per module group, counted from the files."""
    groups = {"backend": ["backend/main.py", "backend/demo_seed.py"],
              "services": ["services/ai_service.py", "services/analytics_service.py", "services/budget_service.py", "services/data_import_service.py",
                           "services/goal_service.py", "services/investment_service.py", "services/report_service.py", "services/transaction_service.py"],
              "ml": ["ml/expense_classifier.py", "ml/spending_prediction.py", "ml/financial_health.py"],
              "database": ["database/database.py", "database/models.py"],
              "auth": ["auth/authentication.py", "utils/security.py", "utils/validators.py"],
              "tests": ["tests/conftest.py", "tests/test_auth.py", "tests/test_budget.py", "tests/test_financial_health.py", "tests/test_ml.py", "tests/test_transactions.py"],
              "scripts": ["scripts/run_experiments.py", "scripts/smoke_test.py", "scripts/measure_api.py", "scripts/probe_data.py"]}
    out = {}
    for g, files in groups.items():
        n = 0
        for rel in files:
            with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
                n += sum(1 for _ in f)
        out[g] = n
    return out


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    lc = line_counts()
    cl = F.CLS
    bt = F.FC["demo_backtest"]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: categorise, forecast, score and advise from a user's own transactions",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how FINJARVIS is designed and built, what is implemented, the first measured results from our own experiments and tests, and the open items. "
                "Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and data"), ("03", "Import and preprocessing"), ("04", "Models and configuration"),
               ("05", "Decision logic and data flow"), ("06", "Database, UML, technology"), ("07", "Implementation progress"), ("08", "Preliminary results"),
               ("09", "Output screens"), ("10", "Testing"), ("11", "Challenges"), ("12", "Next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Manual expense recording is tedious and abandoned. Apps report past spending but do not forecast. Generic advice ignores the person's own income and commitments.", K.ORANGE, "!"),
        ("Proposed system", "FINJARVIS: users record or import transactions; a TF-IDF and logistic-regression model labels them; a linear trend forecasts next month; six weighted components give a 0-100 health score; an assistant answers from the user's own data.", K.BLUE, "i"),
        ("Base paper and scope", "Kharat et al. [1] combine BERT, Q-learning, LSTM and Isolation Forest. We built simpler, inspectable modules. Not built: anomaly detection, reinforcement-learning budgets, LSTM/ARIMA, loan tracker, scheduler. Flask and MySQL became FastAPI and SQLite.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.6, t, b_, col, gl, body_size=17)
    notes[3] = ("Recap of Review 1. The base paper's four-model design is the reference; our build is deliberately simpler, and the gaps are stated openly at this point so that results are read correctly.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.3, 5.7)
    K.text(s, 8.15, 1.45, 4.6, 5.4, [
        ("**Layered, one database file**", {"space_after": 8}),
        (f"Dashboard: React 18 + Vite on port {F.WEB_PORT}, Tailwind, Recharts, TanStack Query; {F.N_PAGES} pages.", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}, {F.N_ROUTES} routes in backend/main.py with a bearer-token dependency.", {"bullet": True}),
        ("Services: transactions, budgets, goals, investments, analytics, assistant, reports, import.", {"bullet": True}),
        ("ML modules: expense classifier, spending prediction, financial health.", {"bullet": True}),
        ("Storage: SQLAlchemy over SQLite (finjarvis.db, 6 tables). The original Streamlit UI still uses the same code.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[4] = f"backend/main.py is {lc['backend']} lines including the seed module; the routes call the same service functions the Streamlit pages call and keep no business rules of their own."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: record, categorise, analyse, advise")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.5, 5.0)
    for i, (t, b_) in enumerate([("Record", "Manual entry or CSV/Excel import with preview; bad rows are skipped with a message. Auto-detect labels a description with the classifier."),
                                 ("Analyse", "Monthly totals feed a linear-trend forecast; income, expenses, budgets, goals and holdings feed the health score."),
                                 ("Advise", "Budget alerts at 75, 90 and 100 % (checked when the dashboard or notifications are opened); rule-routed answers from the user's data; PDF, Excel and CSV reports.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.35, y, 4.38, 1.65)
        K.text(s, 8.5, y + 0.07, 4.1, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.5, y + 0.42, 4.1, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.5, 0.45, "High-level workflow as implemented in the API.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "Every step shown is implemented in services/ and ml/; the workflow diagram mirrors the routes."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Data: a 51-example seed list; no public corpus")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{cl['seed_examples']}", f"training descriptions in {cl['seed_categories']} categories (3 to 6 each)", K.ORANGE),
                                   (f"{cl['probe_examples']}", "team-written probe descriptions, 3 tiers of 66, never used for training", K.BLUE),
                                   (f"{cl['sample_csv_rows']}", "rows in the bundled sample CSV (fictional, Jun-Aug 2026)", K.GREEN),
                                   (f"{F.FC['demo_backtest']['demo_transactions']}", "transactions in the demo account (6 months, synthetic)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=11.5)
    rows = [["", "Seed list (ml/expense_classifier.py)", "Probe set (scripts/probe_data.py)"],
            ["Origin", "51 short English, Indian-merchant style phrases written by the project", "198 descriptions written by the team before scoring"],
            ["Tiers", "Food 6, Transport 6, Entertainment 6, Bills 5, Shopping 5, Education 5, Healthcare 5, Travel 4, Rent 3, Investments 3, Salary 3",
             "A seed-like wording; B upper-case UPI/POS/NEFT narrations with a seed keyword; C unseen merchants and phrases"],
            ["Use", "the only data the shipped model is trained on (no train/test split exists in the app)", "evaluation only; not an independent benchmark"],
            ["Licence", "own work; the demo data is fictional and contains no real personal data", "own work"]]
    K.table(s, 0.6, 2.95, [1.2, 5.6, 5.33], rows, font_size=12, row_h=0.76, first_bold=True)
    notes[6] = ("There is no public training corpus: the categoriser learns from a 51-example list. Evaluation uses a probe set the team wrote, so the numbers describe this system and are not an independent benchmark.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Import and data preparation")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Read CSV / Excel", K.NAVY), ("Check 5 columns", K.PURPLE), ("Parse date and amount", K.PURPLE),
                                       ("Skip bad rows", K.PURPLE), ("Blank category: classifier", K.GREEN), ("Commit rows", K.ORANGE)], size=12, gap=0.22)
    im = F.IMP
    for i, (v, l, c) in enumerate([(f"{im['rows_skipped']} / {im['injected_bad_total']}", "injected bad rows skipped (bad dates, negative or non-numeric amounts, blank descriptions) in a 1,000-row test file", K.ORANGE),
                                   (f"{im['rows_per_second_commit']:.1f} rows/s", f"commit speed: {im['rows_imported']} rows in {im['commit_s']:.1f} s, one database session per row", K.BLUE)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=11.5)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        ("Required columns: date, description, amount, category, type; each skipped row gets a 'Row n' warning, so the user sees what was dropped.", {"bullet": True}),
        ("Unknown type becomes an expense; a blank category is labelled by the classifier (all 916 imported rows were auto-labelled in the test).", {"bullet": True}),
        ("Sign-up rules: username 3-30 characters, password 8+ with upper, lower, digit and special character; passwords are stored as bcrypt hashes.", {"bullet": True}),
        ("Text is lower-cased and split into word 1-2-grams by TF-IDF; there is no other cleaning, stop-word removal or SMOTE.", {"bullet": True}),
        ("Known gap: import is slow because every row is committed in its own database session.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=8)
    notes[7] = "The preprocessing is validation and light text normalisation; the base paper's SMOTE balancing and 50 categories are not used here."

    # ---- 8 model
    s = S[7]
    set_title(s, "Models: categoriser, forecast and health score")
    wipe(s)
    K.picture(s, trim(F.diag("11_categoriser_pipeline.png"), "11"), 0.6, 1.25, 6.0, 3.85)
    K.picture(s, trim(F.diag("12_health_score_model.png"), "12"), 6.75, 1.25, 6.0, 3.85)
    for i, t in enumerate([
        "**Categoriser**: TfidfVectorizer (word 1-2-grams) then LogisticRegression; a keyword table is used only if the model cannot load; the model never outputs 'Other'. A correction retrains it on the seed plus the user's history.",
        "**Forecast**: least-squares line over monthly expense totals, clipped at 0; needs 3 months; trend label 'increasing' if the slope is above 1, 'decreasing' below -1.",
        "**Health score**: sum of six weighted components (0.30, 0.20, 0.15, 0.15, 0.10, 0.10) clipped to 0-100, mapped to five rating bands with the weakest area named.",
    ]):
        K.box(s, 0.6 + i * 4.14, 5.3, 3.85, 1.75)
        K.text(s, 0.78 + i * 4.14, 5.38, 3.5, 1.6, t, size=11.5, color=K.INK)
    notes[8] = "All three are small, explainable models; each decision can be traced to a word weight, a slope or a component score."

    # ---- 9 configuration
    s = S[8]
    set_title(s, "Model and experiment configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Categoriser", f"TfidfVectorizer(ngram_range=(1,2), min_df=1) + LogisticRegression(max_iter=1000, C=1); {cl['seed_examples']} seed examples; retrain {cl['retrain_ms_seed_only']} ms; predict {cl['predict_ms_per_description']} ms"],
            ["Forecast", "numpy.polyfit degree 1 over monthly expense totals; MIN_MONTHS_REQUIRED = 3; recent average = mean of the last 3 months"],
            ["Health score", "weights: savings rate 0.30, expense ratio 0.20, budget adherence 0.15, emergency fund 0.15, diversification 0.10, goal progress 0.10; bands 90 / 75 / 60 / 40"],
            ["Budget alerts", "75 %, 90 % and 100 % of a monthly category budget; checked when GET /api/dashboard or /api/notifications is read (no timer); one notification per identical message"],
            ["Evaluation", "198-description probe set; leave-one-out on the seed; rolling-origin backtest on 6 months; 2,000-user synthetic simulation per setting"],
            ["Tests", f"pytest ({F.PYTEST_TOTAL} tests) and a {F.SMOKE_TOTAL}-check smoke test on a throw-away database"],
            ["Machine", "Intel Core i5-12500 (6 cores), 15.7 GB RAM, Windows 11, Python 3.11.9, scikit-learn 1.9.1, no GPU"]]
    K.table(s, 0.6, 1.45, [2.0, 10.13], rows, font_size=12.5, row_h=0.66, first_bold=True)
    notes[9] = "There is no training run in the deep-learning sense: the classifier fits in milliseconds. The configuration is what the code uses."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: categorise a transaction, check alerts")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_algorithm.png"), "10"), 0.6, 1.3, 6.6, 5.7)
    K.text(s, 7.5, 1.45, 5.25, 5.5, [
        ("**Categorise**: Auto-detect uses the model's label; a manual category that differs from the prediction triggers a retrain.", {"bullet": True, "space_after": 9}),
        ("**Budget check**: when the dashboard or notification list is opened, spend / budget >= 75, 90 or 100 % writes a notification (not on save, not on a timer).", {"bullet": True, "space_after": 9}),
        ("**Assistant routing**: can-I-save, reduce-expenses, health, where-spending, category-spend, optional LLM, fixed help text.", {"bullet": True, "space_after": 9}),
        ("**Limit**: unseen text gives a zero vector, so the label comes from the intercepts (mostly Transport); no confidence threshold is applied.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[10] = "The limit on this slide is a measured finding: 48 of the 56 probe errors were predicted as Transport."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 6.4, 5.2)
    K.text(s, 0.6, 6.55, 6.4, 0.4, "DFD level 1: the main processes and the data stores.", size=12, color=K.TXT, align="c", italic=True)
    mods = [["Module group", "Lines", "Role"],
            ["backend/", lc["backend"], f"{F.N_ROUTES} routes, demo seed"],
            ["services/", lc["services"], "business logic, import, reports"],
            ["ml/", lc["ml"], "classifier, forecast, health"],
            ["database/", lc["database"], "6 SQLAlchemy tables"],
            ["auth, utils/", lc["auth"], "bcrypt, tokens, validators"],
            ["tests/", lc["tests"], f"{F.PYTEST_TOTAL} pytest tests"],
            ["scripts/ (measurement)", lc["scripts"], "experiments, probes, smoke test"]]
    K.table(s, 7.2, 1.45, [2.6, 0.75, 2.18], mods, font_size=11, row_h=0.55, first_bold=True, align=["l", "r", "l"])
    notes[11] = "Line counts are taken from the files. The API layer is thin: it validates, calls a service and shapes the JSON."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 0.6, 1.3, 6.4, 4.9)
    K.text(s, 0.6, 6.25, 6.4, 0.4, "UML class diagram: entities, services and ML modules.", size=12, color=K.TXT, align="c", italic=True)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 7.2, 1.3, 5.55, 4.9)
    K.text(s, 7.2, 6.25, 5.55, 0.4, "ER diagram of the SQLite database (finjarvis.db).", size=12, color=K.TXT, align="c", italic=True)
    K.text(s, 0.6, 6.65, 12.13, 0.4, "users 1-N transactions, budgets, financial_goals, investments and notifications; every child row carries user_id and is deleted with the user.", size=11.5, color=K.TXT, align="c")
    notes[12] = "All queries filter by user_id, which is what keeps one user's data away from another; the smoke test checks this with a second account."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    stack = [("Python 3.11.9", "backend language; scikit-learn 1.9.1, pandas 3.0, numpy 2.4", K.BLUE), ("FastAPI 0.159", "33 routes; uvicorn 0.54; pydantic 2.14", K.ORANGE),
             ("SQLAlchemy 2.1", "6 tables on SQLite; one file, no server", K.GREEN), ("passlib + bcrypt 4.0.1", "bcrypt pinned (bcrypt 5 breaks passlib); HMAC-signed tokens", K.PURPLE),
             ("ReportLab, OpenPyXL", "PDF and Excel reports; CSV from pandas", K.BLUE), ("React 18 + Vite 8", "TypeScript, Tailwind v4, Recharts, TanStack Query", K.ORANGE),
             ("pytest, Playwright", f"{F.PYTEST_TOTAL} tests; screenshots from the real UI", K.GREEN), ("Optional extras", "Anthropic LLM answers and yfinance live prices; not used in any measurement", K.PURPLE)]
    for i, (t, b_, col) in enumerate(stack):
        r, c = divmod(i, 4)
        x, y = 0.6 + c * 3.09, 1.5 + r * 2.5
        K.box(s, x, y, 2.85, 2.25)
        K.circle(s, x + 0.22, y + 0.22, 0.5, col, str(i + 1), 16)
        K.text(s, x + 0.22, y + 0.9, 2.45, 0.45, t, size=15, color=K.INK, bold=True)
        K.text(s, x + 0.22, y + 1.35, 2.45, 0.85, b_, size=12, color=K.TXT)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Everything runs on one machine on CPU; no external service is needed for any measured feature.", size=13, color=K.TXT, italic=True)
    notes[13] = "Versions are those installed in the project's virtual environment on the measuring machine."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Accounts, import, manual entry", "Done", "bcrypt, signed tokens, user scoping; import skips 84 of 84 bad rows"],
            ["Expense categoriser", "Done, simple", f"TF-IDF + LR: {cl['tfidf_lr']['accuracy'] * 100:.1f} % on probe set, {cl['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants"],
            ["Forecast and health score", "Done, simple", "linear trend (3-month minimum); 6-component score; sensitivity tested on 5,000 profiles"],
            ["Budgets, goals, investments, alerts", "Done", "alerts at 75/90/100 %; 6 asset types; optional live prices"],
            ["Assistant and reports", "Done, rule layer", "14 of 20 answerable questions handled; PDF, Excel, CSV downloads"],
            ["React dashboard", "Done", f"{F.N_PAGES} pages; 19 captured screens on the demo account"],
            ["Anomaly detection, RL budgeting, LSTM", "Not built", "objective 4 and base-paper modules; not attempted"],
            ["Loan tracker, scheduled digests", "Not built", "named in the abstract; no table, route or job exists"]]
    K.table(s, 0.6, 1.45, [3.9, 1.8, 6.43], rows, font_size=12.5, row_h=0.6, first_bold=True)
    notes[14] = "Honest status: the core flow is complete in simple form; one objective (anomaly detection) and two abstract features (loan tracker, scheduler) are not built."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: categoriser and forecast")
    wipe(s)
    t1, t2 = cl["tfidf_lr"]["accuracy_by_tier"], cl["keyword_table"]["accuracy_by_tier"]
    K.bar_chart(s, 0.6, 1.35, 6.3, 3.5, ["A seed-like", "B statement strings", "C unseen merchants"],
                [("TF-IDF + LR (shipped)", [round(t1[k] * 100, 1) for k in "ABC"]), ("Keyword table", [round(t2[k] * 100, 1) for k in "ABC"])],
                colors=[K.BLUE, K.ORANGE], number_format="0.0", font_size=10, max_value=125)
    K.text(s, 0.6, 4.85, 6.3, 0.5, f"Accuracy (%) per probe tier; overall {cl['tfidf_lr']['accuracy'] * 100:.1f} % (142 of 198), macro-F1 = {cl['tfidf_lr']['macro_f1']:.3f}.", size=11, color=K.TXT, align="c", italic=True)
    mp = bt["mape_pct"]
    frows = [["Forecast method (3 test points)", "MAE (INR)", "MAPE %"]]
    for lab, k in [("Linear trend (app)", "linear_trend (app)"), ("Mean of all history", "mean_of_all"), ("Mean of last 3", "mean_of_last_3"), ("Last value", "last_value")]:
        frows.append([lab, f"{bt['mae'][k]:,.0f}", f"{mp[k]:.1f}"])
    K.table(s, 7.2, 1.4, [3.3, 1.2, 1.03], frows, font_size=11.5, row_h=0.46, first_bold=True, align=["l", "r", "r"])
    K.text(s, 7.2, 3.85, 5.53, 1.0, f"Demo account, one-step-ahead backtest of months 4-6; app forecast for November: INR {bt['app_prediction_for_next_month']['predicted_next_month_expense']:,.0f}.", size=11, color=K.TXT, italic=True)
    K.text(s, 0.6, 5.4, 12.13, 1.7, [
        (f"The model is perfect on seed-like text and near-perfect on statement strings, but only {t1['C'] * 100:.1f} % on unseen merchants; {cl['errors_predicted_as_transport']} of {len(cl['errors'])} errors are predicted as Transport.", {"bullet": True}),
        (f"Leave-one-out on the 51 seed pairs is {cl['loo_cv_accuracy_on_seed'] * 100:.1f} %: the seed list is tiny and non-redundant. One correction fixes a repeat merchant (18.2 % to 100 %) but barely helps new ones.", {"bullet": True}),
        ("The linear trend is not better than a plain mean on this short history (MAPE 28.4 % vs 21.4 %); a synthetic simulation shows it needs about 7 or more months.", {"bullet": True}),
        ("Probe set and demo data are ours, not independent; the base paper's 92.3 % BERT accuracy is on different data and is not comparable.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=12.5, color=K.INK, space_after=4)
    notes[15] = "Numbers are from experiments/metrics.json. The headline 71.7 % hides the split between known wording and unseen merchants, which is why the tiers are shown."

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shot_box(s, "05_dashboard.png", 0.6, 1.3, 3.95, 2.9, "Dashboard: balance, savings, health score 90")
    shot_box(s, "09_transactions-import.png", 4.69, 1.3, 3.95, 2.9, "CSV/Excel import with preview and auto-categories")
    shot_box(s, "11_analytics-prediction.png", 8.78, 1.3, 3.95, 2.9, "Spending prediction: next month INR 39,471")
    shot_box(s, "12_budgets.png", 0.6, 4.25, 3.95, 2.9, "Budgets with usage and alerts")
    shot_box(s, "15_assistant.png", 4.69, 4.25, 3.95, 2.9, "AI assistant answering from the user's data")
    shot_box(s, "16_reports.png", 8.78, 4.25, 3.95, 2.9, "Reports: PDF, Excel and CSV downloads")
    notes[16] = "All screens are captures of the running application on the fictional demo account (68 transactions); nothing is mocked."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests pass (auth 9, budget 6, health 6, ML 9, transactions 8)", K.GREEN),
                                   (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "end-to-end smoke checks on a throw-away database", K.BLUE),
                                   (f"{F.AS['unanswerable_correctly_declined']} / {F.AS['not_answerable']}", "off-topic assistant questions correctly declined", K.PURPLE),
                                   (f"{F.AS['answerable_handled_by_analytics']} / {F.AS['answerable']}", "answerable questions handled from the data", K.ORANGE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Check", "Result"],
            ["Weak password / wrong password", "rejected"],
            ["Tampered token", "rejected (401)"],
            ["Protected route without token", "401"],
            ["Second user sees first user's data", "no (scoped by user_id)"],
            ["Duplicate e-mail on profile", "rejected"],
            ["Bad analytics date range", "rejected"],
            ["Food total vs direct SUM", f"INR {F.AS['numeric_check_food_truth']:,.0f}, identical"]]
    K.table(s, 0.6, 2.95, [3.9, 2.4], rows, font_size=13, row_h=0.5, first_bold=True)
    K.text(s, 7.2, 2.95, 5.53, 4.0, [
        ("**What the tests cover**: sign-up and login rules, budgets and alerts, the health score, classifier and forecast, add / edit / delete / filter of transactions, import, reports, profile.", {"bullet": True, "space_after": 8}),
        ("**Found by measurement**: unseen merchants mislabelled, six assistant questions missed (e.g. 'biggest expense'), one quirk: 'overspending on shopping?' returns a total, not a budget comparison.", {"bullet": True, "space_after": 8}),
        ("**Not done**: browser-level automated UI tests, concurrency, security scan, LLM layer, live price refresh.", {"bullet": True}),
    ], size=14.5, color=K.INK)
    notes[17] = "Tests and checks are real runs on 2026-10-22. The assistant questions were written by the team; the numbers describe the rule layer only."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "What we found", "Action"],
            ["No labelled data", "Only 51 seed phrases; no public corpus used", "Wrote a 198-item probe set and reported tiers, not one headline number"],
            ["Unseen merchants", f"Tier C accuracy {t1['C'] * 100:.1f} %; errors collapse to Transport", "Measured; confidence abstention shown offline (not in app); corrections retrain"],
            ["Short history", "Trend no better than a mean below ~7 months", "Reported; minimum of 3 months is too low for this method"],
            ["Assistant coverage", "6 of 20 answerable questions fall to help text", "Listed the misses; LLM layer is optional and untested"],
            ["Shared model file", "One ml/expense_model.pkl serves all users: a correction by one user retrains it for everyone", "Documented as a design weakness; per-user models are future work"],
            ["Slow import", f"{F.IMP['rows_per_second_commit']:.1f} rows/s, one session per row", "Documented; batch the commit"],
            ["Library versions", "bcrypt 5 breaks passlib; pickle made with sklearn 1.5.0", "Pinned bcrypt 4.0.1; retrain the model to remove the warning"],
            ["Abstract vs build", "Flask + MySQL, loans, scheduler, anomaly detection in the abstract", "FastAPI + SQLite; the gaps are reported, not hidden"]]
    K.table(s, 0.6, 1.35, [2.4, 4.9, 4.83], rows, font_size=12, row_h=0.62, first_bold=True)
    notes[18] = "Each challenge is a measured finding; the evidence is in docs/REPORT_FACTS.md."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Improve", "Add a confidence threshold so unsure labels ask the user, grow the seed list from real corrections, and raise the forecast minimum or blend with a recent mean.", K.ORANGE, "1"),
        ("Complete", "Decide with the guide whether to add a simple anomaly rule (z-score on category amounts) and a loan tracker; widen assistant intents; set a real secret key.", K.BLUE, "2"),
        ("Deliver", "Finish the final report, IEEE paper and presentation from the measured results, and keep every number tied to the metrics files.", K.GREEN, "3"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 3.6, t, b_, col, gl, body_size=18)
    notes[19] = "The open items are those identified by our own measurements, in priority order."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Close the review and invite questions."

    for i, t in notes.items():
        K.set_notes(S[i - 1], t)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


def main():
    build(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
