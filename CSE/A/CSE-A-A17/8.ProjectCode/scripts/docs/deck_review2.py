"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers are defined here. All numbers come from facts.py (experiments/**/metrics.json).
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
    cp.keywords = "fashion demand forecasting, XGBoost, domain adaptation, H&M, covariate shift"
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
            K.replace_text(sh, F.TITLE, 28)
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
        out = os.path.join(tempfile.gettempdir(), f"a17_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    K.picture(slide, F.shot(name), x, y, w, h - 0.5, border=True)
    K.text(slide, x, y + h - 0.45, w, 0.45, caption, size=11, color=K.TXT, align="c", italic=True)


def src_lines():
    root = F.CODE
    out = {}
    for rel in ("src/data_loader.py", "src/preprocessing.py", "src/demand_forecasting.py", "src/feature_engineering.py", "src/baseline_models.py",
                "src/xgboost_model.py", "src/domain_adaptation.py", "src/evaluation.py", "src/gemini_helper.py", "backend/main.py", "backend/state.py", "backend/gemini_api.py"):
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            out[rel] = sum(1 for _ in f)
    return out


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    fc, M = F.FC, F.FC["models"]
    xs = fc["xgboost_seed_stats"]
    dsum = F.DOM["summary"]
    p_on, p_st = F.pair("Online"), F.pair("Store ->")
    p_kn = F.pair("Knitwear")
    rec = F.REC["results"]
    sp = fc["split"]
    ds = F.DS
    lines = src_lines()
    ST = F.API["stages_seconds"]
    LAT = F.API["latency_ms"]
    dup = ds["raw_rows"] - ds["clean_rows"]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: XGBoost demand forecasting with importance-weighted domain adaptation on H&M retail data",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how TrendCast is designed and built, what is implemented, the first measured results on a real subset of the H&M data, and the open items. "
                "Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
               ("05", "Data flow, modules, UML"), ("06", "Technology stack"), ("07", "Implementation progress"), ("08", "Preliminary results"),
               ("09", "Output screens"), ("10", "Testing"), ("11", "Challenges"), ("12", "Next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "A forecasting model trained in one retail context loses accuracy in another whose data distribution differs. Fashion adds short product life, seasonality and trends that move inside a season, and planners distrust forecasts they cannot explain.", K.ORANGE, "!"),
        ("Proposed system", "TrendCast cleans retail transactions, builds daily demand per article, forecasts it with XGBoost, moves a model from a source domain to a shifted target with importance weights, and shows the result in a gated web console with an optional AI explanation.", K.BLUE, "i"),
        ("Base paper link " + F.BASE_SHORT.split(" (")[0], "The base paper pairs LightGBM with four explainability levels on UCI Online Retail II (RMSE 33.71, R2 0.243). We keep gradient boosting and the leakage-safe lag features, and add domain adaptation. Different data: only relative findings are comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.9, t, b_, col, gl, body_size=17)
    notes[3] = ("Recap of Review 1. The base paper stops at one market and one-day-ahead forecasts; our gap is moving a gradient-boosted model across domains and testing that honestly.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.3, 5.7)
    K.text(s, 8.15, 1.45, 4.6, 5.4, [
        ("**Layered, no database**", {"space_after": 8}),
        (f"Console: React 19 + Vite on port {F.WEB_PORT}, 13 pages; the original Streamlit app (11 pages) still runs on the same code.", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}, 22 routes under /api; downstream routes answer 409 until the earlier step is done.", {"bullet": True}),
        ("Pipeline: src/ modules for loading, cleaning, daily demand, features, baselines, XGBoost, domain adaptation and metrics.", {"bullet": True}),
        ("State: one process-wide dictionary with a lock; only the trained models are saved (models/*.joblib).", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "The routes live in backend/main.py (626 lines) and call src/ functions; no pipeline logic was rewritten in the API layer."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: clean, aggregate, forecast, adapt, evaluate")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.5, 5.0)
    for i, (t, b_) in enumerate([("Prepare", "Validate and clean the CSVs, join articles, count units per article per day, fill idle days with zero, add shifted lag and rolling features."),
                                 ("Forecast", "Split by date (80/20), compare the moving average with XGBoost, optionally tune with time-ordered cross-validation."),
                                 ("Adapt and judge", "Train on a source domain, test on the later half of a target domain, re-weight source rows by p/(1-p), report before and after as measured.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.35, y, 4.38, 1.65)
        K.text(s, 8.5, y + 0.07, 4.1, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.5, y + 0.42, 4.1, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.5, 0.45, "High-level workflow as implemented in the API.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "Every step is gated in the console. The domain step uses the same feature table and the same XGBoost defaults as the main model."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset: a real subset of H&M retail transactions")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{ds['raw_rows']:,}", "transaction rows read (2018-09-20 to 2019-01-04)", K.ORANGE),
                                   (f"{ds['articles']}", "best-selling articles of the first shard", K.BLUE),
                                   (f"{ds['feature_rows']:,}", "article-day rows after filling idle days", K.GREEN),
                                   (f"{ds['customers']:,}", "customers in the subset", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["", "Real subset (all reported results)", "Synthetic sample (smoke tests only)"],
            ["Source", "H&M Personalized Fashion Recommendations (Kaggle data, Hugging Face parquet mirror); first of 7 transaction shards", "scripts/make_sample_data.py, H&M schema"],
            ["Size", f"{ds['raw_rows']:,} rows; channel 1 {ds['channel_rows_raw']['1']:,}, channel 2 {ds['channel_rows_raw']['2']:,} after cleaning", "70,974 rows, 90 articles, 4,000 customers"],
            ["Target", f"units sold per article per day (mean 19.46, median 14, max 566; {ds['zero_demand_share_pct']:.1f} % zero days)", "same definition"],
            ["Split", f"chronological: train {sp['train_start'][:10]} to {sp['train_end'][:10]} ({sp['train_rows']} rows), test {sp['test_start'][:10]} to {sp['test_end'][:10]} ({sp['test_rows']} rows)", "not used for metrics"],
            ["Limits", "107 days only; test window holds the Christmas peak and January; no earlier year; not redistributed", "simulated, not real sales"]]
    K.table(s, 0.6, 2.95, [1.2, 6.5, 4.43], rows, font_size=12, row_h=0.62, first_bold=True)
    notes[6] = ("The shipped sample is synthetic, so the real subset was built from the public H&M files. Licence: Kaggle competition terms, academic use; the files are not redistributed. "
                "Channels 1 and 2 are only codes in the data.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing and feature construction")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Parse dates, drop bad rows", K.NAVY), ("Join articles", K.PURPLE), ("Units per article-day", K.PURPLE),
                                       ("Fill idle days with 0", K.GREEN), ("Shifted lags and rolls", K.GREEN), ("31 model inputs", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([(f"{dup:,}", f"exact-duplicate rows dropped ({dup / ds['raw_rows'] * 100:.1f} % of the subset); repeat purchases look like duplicates, so demand is understated", K.ORANGE),
                                   ("31", "inputs: price, channel, 6 encoded attributes, 14 calendar, 9 lag and rolling", K.BLUE)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=11.5)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        ("Lags 1, 7, 14, 28 and rolling mean 7, 14, 28 and std 7, 28 are computed on values shifted by one day, so a day never sees its own demand.", {"bullet": True}),
        ("Month and weekday get sine and cosine encodings; product attributes are label-encoded, not one-hot.", {"bullet": True}),
        (f"Idle days between an article's first and last sale become demand 0: {ds['feature_rows'] - ds['daily_rows']} rows added, {ds['zero_demand_share_pct']:.2f} % of the table.", {"bullet": True}),
        ("Known limit: price and channel are the target day's own mean price and most frequent channel, so they are planned inputs at best.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "Leakage guards: shifted lag and rolling features, chronological split, TimeSeriesSplit for tuning, domain column excluded from the domain classifier."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model architecture")
    wipe(s)
    K.picture(s, trim(F.diag("12_model_architecture.png"), "12"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**Main model**: one XGBoost regressor (300 trees, depth 8, learning rate 0.05) on the 31 inputs.", {"bullet": True, "space_after": 8}),
        ("**Baseline in the product**: mean of the article's last 7 days.", {"bullet": True, "space_after": 8}),
        ("**Weighted variant**: the same XGBoost with a per-row sample weight from the domain classifier.", {"bullet": True, "space_after": 8}),
        ("Offline comparison models: random forest, LightGBM, naive lag-1.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=14, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "Feature groups feeding one XGBoost regressor, with the baselines.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "XGBoost was chosen because it handles mixed numeric and encoded features, is fast on CPU and accepts sample weights, which the adaptation step needs."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training and evaluation configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Split", f"chronological 80/20 by date; train {sp['train_rows']} rows, test {sp['test_rows']} rows; domain tests hold out the later 50 % of target dates"],
            ["XGBoost", f"300 trees, depth 8, learning rate 0.05, subsample 0.8, colsample 0.8, seed 42; fit {fc['xgboost_fit_seconds_mean']:.1f} s on CPU; seeds 42 to 46 for stability"],
            ["Tuning", f"RandomizedSearchCV, 10 iterations x 3 time-ordered folds; {fc['tuning_seconds']:.0f} s; best: depth {fc['tuned_best_params']['max_depth']}, {fc['tuned_best_params']['n_estimators']} trees, learning rate {fc['tuned_best_params']['learning_rate']}"],
            ["Baselines", "moving average (7 d, in the product); random forest 200 trees, LightGBM 300 trees, naive lag-1 and lag-7 (offline)"],
            ["Domain adaptation", "logistic regression (1000 iterations) separates source from target; weight = p/(1-p), clipped at 20; weighted XGBoost"],
            ["Metrics", "RMSE, MAE, MAPE with zero-demand rows excluded, R2; WAPE added offline"],
            ["Machine", "Intel Core i5-12500, 15.7 GB RAM, no GPU; Python 3.11.9, XGBoost 2.0.3, scikit-learn 1.5.0"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=13, row_h=0.66, first_bold=True)
    notes[9] = "All numbers in later slides use exactly this configuration. Tuning is time-ordered so it never trains on the future."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: importance-weighted domain adaptation")
    wipe(s)
    K.picture(s, trim(F.diag("11_flowchart_domain_adaptation.png"), "11"), 0.6, 1.3, 6.6, 5.7)
    K.text(s, 7.5, 1.45, 5.25, 5.5, [
        ("**Weight rule**: w = p / (1 - p), where p is the domain classifier's probability that a source row looks like target; clipped at 20.", {"bullet": True, "space_after": 9}),
        ("**Gating**: both domains need rows, source and target must differ, and the target must have enough dates to hold out a test half; otherwise the API answers 400.", {"bullet": True, "space_after": 9}),
        ("**Report as measured**: RMSE, MAE, MAPE and R2 before and after; a worse result is shown as worse.", {"bullet": True, "space_after": 9}),
        ("**Our checks**: shuffled weights, pooled source plus target-train, a target-only model, weights rescaled to mean 1, and a time-clean source that stops before the target test dates.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[10] = "The classifier excludes the domain column, otherwise it could read the label directly. The extra checks are offline in scripts/run_experiments.py."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 6.4, 5.2)
    K.text(s, 0.6, 6.55, 6.4, 0.4, "DFD level 1: seven processes and the data stores.", size=12, color=K.TXT, align="c", italic=True)
    mods = [["Module", "Lines", "Role"],
            ["data_loader.py", lines["src/data_loader.py"], "column validation"],
            ["preprocessing.py", lines["src/preprocessing.py"], "clean, merge, quality report"],
            ["demand_forecasting.py", lines["src/demand_forecasting.py"], "daily demand, idle-day fill"],
            ["feature_engineering.py", lines["src/feature_engineering.py"], "calendar, lag, rolling, encoding"],
            ["baseline_models.py", lines["src/baseline_models.py"], "date split, moving average"],
            ["xgboost_model.py", lines["src/xgboost_model.py"], "train, tune, importance"],
            ["domain_adaptation.py", lines["src/domain_adaptation.py"], "classifier, weights"],
            ["evaluation.py", lines["src/evaluation.py"], "metrics, before/after"],
            ["backend/main.py", lines["backend/main.py"], "22 API routes"]]
    K.table(s, 7.25, 1.45, [2.35, 0.7, 2.43], mods, font_size=11.5, row_h=0.5, first_bold=True, align=["l", "r", "l"])
    notes[11] = "Module sizes counted from the files. The API layer is thin: it validates, takes the lock, calls src/ and shapes the JSON."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 0.6, 1.3, 8.3, 4.9)
    K.text(s, 0.6, 6.25, 8.3, 0.4, "UML class diagram: API, request models, state and src/ modules.", size=12, color=K.TXT, align="c", italic=True)
    K.box(s, 9.15, 1.4, 3.58, 5.2)
    K.text(s, 9.35, 1.55, 3.2, 5.0, [
        ("**Logical entities (no database)**", {"space_after": 8}),
        ("Transaction, Article and Customer tables are joined on article_id and customer_id.", {"bullet": True}),
        ("Transactions are counted per date and article into DailyDemand, which becomes one FeatureRow per article-day.", {"bullet": True}),
        ("A training run writes a ModelFile; a domain run writes an adapted ModelFile and a DomainRun record; a Forecast is dated rows for one article.", {"bullet": True}),
        ("Only models/*.joblib survive a restart; the logical ER diagram is in the report.", {"bullet": True, "italic": True}),
    ], size=12.5, color=K.INK, space_after=6)
    K.text(s, 0.6, 6.65, 8.3, 0.4, "Tables live in memory per process; models/baseline_xgboost.joblib, adapted_xgboost.joblib and feature_info.joblib persist.", size=11.5, color=K.TXT, align="c")
    notes[12] = "A database was not needed for a single-user tool. The ER diagram is logical: the relations are shared columns between pandas tables."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    stack = [("Python 3.11.9", "pandas 2.2.1, NumPy 1.26.4", K.BLUE), ("XGBoost 2.0.3", "main model; scikit-learn 1.5.0 for baselines, tuning, metrics", K.ORANGE),
             ("FastAPI 0.143.3", "22 routes; uvicorn; pydantic request models", K.GREEN), ("React 19 + Vite 8", "13 pages, Recharts charts", K.PURPLE),
             ("Streamlit 1.66.0", "original 11-page interface, kept", K.BLUE), ("LightGBM 4.7.0", "offline baseline only", K.ORANGE),
             ("pytest, Playwright", "39 tests; screenshots from the real UI", K.GREEN), ("Gemini REST (optional)", "AI Insights; aggregated numbers only", K.PURPLE)]
    for i, (t, b_, col) in enumerate(stack):
        r, c = divmod(i, 4)
        x, y = 0.6 + c * 3.09, 1.5 + r * 2.5
        K.box(s, x, y, 2.85, 2.25)
        K.circle(s, x + 0.22, y + 0.22, 0.5, col, str(i + 1), 16)
        K.text(s, x + 0.22, y + 0.9, 2.45, 0.45, t, size=16, color=K.INK, bold=True)
        K.text(s, x + 0.22, y + 1.35, 2.45, 0.85, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Everything runs on CPU on a single machine; there is no GPU, cloud service or database requirement.", size=13, color=K.TXT, italic=True)
    notes[13] = "Versions are those installed on the measuring machine."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Data pipeline and features", "Done", f"31 inputs, shifted lags, {ds['feature_rows']:,} rows built in {ST['build features']:.1f} s"],
            ["Baseline, XGBoost, tuning", "Done", f"XGBoost RMSE {xs['RMSE']['mean']:.2f} vs moving average {M[F.MA]['RMSE']:.2f}"],
            ["Domain adaptation", "Done, mixed result", f"helped {dsum['pairs_where_adaptation_helped']} of {dsum['pairs_total']} source-target pairs"],
            ["Evaluation and importance", "Done", "gain importance in the app; SHAP only offline"],
            ["Recursive 7 / 14 / 30-day forecast", "Done, weak", f"error {rec['xgb_app']['by_band'][0]['WAPE (%)']:.0f} % over days 1-7, {rec['xgb_app']['by_band'][2]['WAPE (%)']:.0f} % over days 15-30 (WAPE)"],
            ["FastAPI and React console", "Done", "22 routes, 13 pages, gated by 409 messages"],
            ["AI Insights (Gemini)", "Built", "external service returned 503 and timeouts when we captured it"],
            ["Not implemented", "Open", "cold-start mode, inventory impact and SHAP inside the app"]]
    K.table(s, 0.6, 1.45, [3.9, 2.2, 6.03], rows, font_size=13, row_h=0.6, first_bold=True)
    notes[14] = "Honest status: the pipeline and console are complete; two items are open (cold start, in-app inventory impact) and the long-horizon forecast is weak."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results on real H&M data")
    wipe(s)
    order = [("Naive lag-1", M["Naive (lag 1)"]["RMSE"]), ("Rolling mean 7", M["Rolling mean 7 (shifted)"]["RMSE"]), ("LightGBM", M["LightGBM"]["RMSE"]),
             ("XGBoost tuned", M[F.XGB_T]["RMSE"]), ("XGBoost default", xs["RMSE"]["mean"]), ("Moving average", M[F.MA]["RMSE"]), ("Random forest", M["Random forest"]["RMSE"])]
    K.bar_chart(s, 0.6, 1.35, 6.1, 3.7, [o[0] for o in order], [("RMSE (units per article-day)", [round(o[1], 2) for o in order])], colors=[K.BLUE], number_format="0.00", font_size=10, max_value=15)
    K.text(s, 0.6, 5.05, 6.1, 0.35, "Test RMSE, 2018-12-14 to 2019-01-04; lower is better (XGBoost = mean of 5 seeds).", size=11, color=K.TXT, align="c", italic=True)
    drows = [["Source -> target", "RMSE before", "RMSE after", "Change"]]
    for p in F.DOM["pairs"]:
        e = p["app"]
        drows.append([p["label"].split(" (")[0], f"{e['before']['RMSE']['mean']:.2f}", f"{e['adapted']['RMSE']['mean']:.2f}", f"{e['rmse_improvement_pct_mean']:+.1f} %"])
    K.table(s, 6.95, 1.4, [2.55, 1.05, 1.05, 1.13], drows, font_size=11, row_h=0.4, first_bold=True, align=["l", "r", "r", "r"])
    K.text(s, 0.6, 5.5, 12.13, 1.6, [
        (f"XGBoost beats the moving-average baseline ({xs['RMSE']['mean']:.2f} vs {M[F.MA]['RMSE']:.2f}) but not repeating yesterday ({M['Naive (lag 1)']['RMSE']:.2f}); lag and rolling features carry the model.", {"bullet": True}),
        (f"Domain adaptation as shipped: {dsum['pairs_where_adaptation_helped']} of {dsum['pairs_total']} pairs improved, mean {dsum['mean_rmse_improvement_pct']:+.1f} %; the one clear gain ({p_on['app']['rmse_improvement_pct_mean']:+.1f} %) falls to {p_on['time_clean']['rmse_improvement_pct_mean']:+.1f} % when source rows may not overlap the target test dates.", {"bullet": True}),
        (f"Department pairs collapse (e.g. {p_kn['label'].split(' (')[0]} {p_kn['app']['rmse_improvement_pct_mean']:+.0f} %): weights near 1e-5 stop XGBoost splitting; rescaling to mean 1 gives {p_kn['app']['normalised_improvement_pct_mean']:+.1f} %.", {"bullet": True}),
    ], size=13, color=K.INK, space_after=5)
    notes[15] = "Results are reported as measured, including the negative ones. Pair labels use store/online only as our convention; the data code the channels 1 and 2."

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shot_box(s, "12_training.png", 0.6, 1.4, 3.95, 3.5, "Model training: XGBoost test metrics on the real subset")
    shot_box(s, "16_domain-before-after.png", 4.69, 1.4, 3.95, 3.5, "Domain adaptation: before and after cards, channel 1 to channel 2")
    shot_box(s, "19_forecast.png", 8.78, 1.4, 3.95, 3.5, "Demand forecast: history and 14-day forecast for one article")
    shot_box(s, "07_explore.png", 0.6, 4.95, 3.95, 2.1, "Data exploration")
    shot_box(s, "18_evaluation-importance.png", 4.69, 4.95, 3.95, 2.1, "Feature importance, top 20")
    shot_box(s, "21_insights.png", 8.78, 4.95, 3.95, 2.1, "AI Insights: Gemini returned 503, shown as an error")
    notes[16] = "All screens are captures of the running application with the real H&M subset loaded. The AI Insights capture shows the real service error."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests pass ({F.PYTEST_UNIT} unit, {F.PYTEST_API} API)", K.GREEN),
                                   (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "end-to-end smoke checks on a live backend", K.BLUE),
                                   ("25", "browser screenshots; 3 problems, all the Gemini call (502)", K.ORANGE),
                                   (f"{LAT['POST /api/forecast (30 d)']['median']:.0f} ms", "median 30-day forecast request", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Stage (real subset, 684k rows)", "Seconds"], ["Upload, clean, merge", f"{ST['upload+clean+merge (684k rows)']:.1f}"], ["Build features", f"{ST['build features']:.1f}"],
            ["Train XGBoost (default)", f"{ST['train XGBoost (default)']:.1f}"], ["Train XGBoost (tuned)", f"{ST['train XGBoost (tuned)']:.1f}"], ["Domain adaptation run", f"{ST['domain adaptation run']:.1f}"]]
    K.table(s, 0.6, 3.0, [3.6, 1.2], rows, font_size=12.5, row_h=0.46, first_bold=True, align=["l", "r"])
    K.text(s, 6.0, 3.0, 6.73, 3.9, [
        ("**What the tests cover**: cleaning rules, aggregation, no-leakage lag features, date split, metrics, weights, and all API gates and errors.", {"bullet": True, "space_after": 8}),
        ("**Edge cases checked**: wrong columns, empty file, same source and target, bad horizon, article with too little history, new upload resets later steps.", {"bullet": True, "space_after": 8}),
        ("**Not done**: user study, load test, security audit, browsers other than Chrome. There is no sign-in by design.", {"bullet": True, "space_after": 8}),
        ("Timings are from a busy machine; treat them as upper bounds.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=13.5, color=K.INK)
    notes[17] = "Unit and API tests use small synthetic frames; the experiments use the real subset."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "What we found", "Action"],
            ["Shipped data is synthetic", "A metric on it would say nothing about fashion retail", "Built a real subset from the public H&M files"],
            ["Adaptation gain not robust", f"{p_on['app']['rmse_improvement_pct_mean']:+.1f} % on one pair becomes {p_on['time_clean']['rmse_improvement_pct_mean']:+.1f} % without time overlap", "Added shuffled, pooled, target-only and time-clean controls"],
            ["Weights collapse", "Perfectly separable domains give weights near 1e-5", "Diagnosed; mean-1 rescaling fixes it offline"],
            ["Weak long forecasts", f"Recursive error reaches {rec['xgb_app']['by_band'][2]['WAPE (%)']:.0f} % (WAPE) over days 15-30", "Reported; direct multi-horizon models planned"],
            ["Duplicates removed", f"{dup / ds['raw_rows'] * 100:.1f} % of rows dropped as exact duplicates", "Documented; repeat-purchase handling is future work"],
            ["LightGBM crash", "Importing it after pandas crashed on this machine", "Import it first in the experiment script"],
            ["Gemini unavailable", "503 and timeouts during capture", "Kept optional; the screen shows the clear error"]]
    K.table(s, 0.6, 1.4, [2.9, 4.9, 4.33], rows, font_size=12.5, row_h=0.68, first_bold=True)
    notes[18] = "Each challenge is a measured finding, not a guess; the evidence is in docs/REPORT_FACTS.md."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Fix and re-measure", "Normalise the importance weights, make the time-clean protocol the default, refresh all calendar features in the recursive forecast, and re-run the six pairs.", K.ORANGE, "1"),
        ("Extend the product", "Add a cold-start mode for unseen articles, SHAP and inventory impact (under- and over-stock units) in the console, and more months of H&M data.", K.BLUE, "2"),
        ("Deliver", "Finish the final report and IEEE paper from the measured results, rehearse the final demo, and keep every number tied to the metrics files.", K.GREEN, "3"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 3.9, t, b_, col, gl, body_size=17)
    notes[19] = "The open items are the ones identified by the measurements, in priority order."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Close the review and invite questions."

    for i, t in notes.items():
        K.set_notes(S[i - 1], t)
    prs.save(out_path)
    K.rename_theme(out_path, "TrendCast")
    return out_path


def main():
    build(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
