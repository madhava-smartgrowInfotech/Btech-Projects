"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (letterhead, rule, title and footer chrome inherited)."""

import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .refs import N, REFS, _IDX

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520


def chrome(sh):
    return sh.top in (TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT)


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if sh.top == TOP_TITLE:
            K.replace_text(sh, text, size)
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


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26, lsize=12):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=lsize, color=K.DARK, font=FONT)


CROPS = os.path.join(tempfile.gettempdir(), "a17_deck_crops")


def crop_shot(name, box=(256, 56, 1440, 900)):
    """Real screenshot with the sidebar cropped away (left, top, right, bottom in pixels) so the content is larger on the slide."""
    from PIL import Image

    os.makedirs(CROPS, exist_ok=True)
    out = os.path.join(CROPS, f"{os.path.splitext(name)[0]}_crop.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def clean_ref(s):
    return " ".join(s.replace("*", "").split())


def bl(items, space=8):
    return [(t, {"bullet": True, "space_after": space}) for t in items]


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.last_modified_by = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.subject = F.PRODUCT
    cp.keywords = "fashion demand forecasting, XGBoost, domain adaptation, importance weighting, H&M"
    notes = {}

    FC, DOM, REC, EX, INV, COLD, API, DS = F.FC, F.DOM, F.REC, F.EX, F.INV, F.COLD, F.API, F.DS
    M = FC["models"]
    xs = FC["xgboost_seed_stats"]
    sm = DOM["summary"]
    pairs = DOM["pairs"]
    chan21, chan12 = F.pair("Online"), F.pair("Store")
    abl = FC["ablation"]
    rec = REC["results"]
    st, lat = API["stages_seconds"], API["latency_ms"]
    bt = FC["rolling_origin"]
    inv_x, inv_m = INV["XGBoost"], INV["Moving average (7d)"]

    for sl in S:  # footers on every slide except the title
        for sh_ in sl.shapes:
            if sh_.top == TOP_FOOT and sh_.has_text_frame and "Final Review" in sh_.text_frame.text:
                K.replace_text(sh_, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh_ in S[0].shapes:
        if sh_.name == "Text 1":
            K.replace_text(sh_, F.FULL_TITLE, 28)
        elif sh_.name == "Text 2":
            K.replace_text(sh_, f"Final Review  ·  {F.PRODUCT}")
        elif sh_.name == "Text 3":
            K.replace_text(sh_, f"Team Details : Batch {F.BATCH_NO}")
        elif sh_.name == "Text 4":
            K.replace_text(sh_, "\n".join(f"{r_}   {n_}" for n_, r_ in F.STUDENTS_UPPER))
        elif sh_.name == "Text 5":
            K.replace_text(sh_, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh_.name == "Text 6":
            K.replace_text(sh_, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and TrendCast: fashion demand forecasting with XGBoost and importance-weighted domain adaptation, measured on real H&M data."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh_ in s.shapes:
        if sh_.name == "Text 4":
            K.replace_text(sh_, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Data & Domain-Adaptation Workflow\nInteraction & Data Design\nImplementation, Performance & Testing\nResults: Models, Errors, Parameter Analysis, Domain Adaptation\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.8, 12.2, 5.1, bl([
        "Fashion demand shifts with season, price and channel, and a model trained in one retail context loses accuracy in another. TrendCast turns H&M-style transactions into daily units per article, forecasts them with XGBoost and adds importance-weighted domain adaptation, in a FastAPI + React product.",
        f"Measured on a real subset of the H&M data ({DS['clean_rows']:,} cleaned rows, {DS['articles']} best-selling articles, 107 days): XGBoost reaches RMSE {M[F.XGB]['RMSE']:.2f} (R\u00b2 {M[F.XGB]['R2']:.2f}) against {M[F.MA]['RMSE']:.2f} for the product's moving average, but not against the one-line 'repeat yesterday' forecast ({M['Naive (lag 1)']['RMSE']:.2f}).",
        f"Domain adaptation as built helps on {sm['pairs_where_adaptation_helped']} of {sm['pairs_total']} source-target pairs (mean RMSE change {sm['mean_rmse_improvement_pct']:+.1f}%). The one clear gain ({chan21['app']['rmse_improvement_pct_mean']:+.1f}%) disappears when source rows may not overlap the target test dates.",
        f"The 7/14/30-day recursive forecast is worse than a flat 7-day mean (WAPE {rec['xgb_app']['by_band'][0]['WAPE (%)']:.0f}% on days 1-7, {rec['xgb_app']['by_band'][2]['WAPE (%)']:.0f}% on days 15-30).",
        f"{F.PYTEST_PASSED} pytest tests and {F.SMOKE_PASSED} smoke checks pass; 25 real screenshots. Not shown: inventory savings, new-store transfer, cold-start in the product.",
    ], 9), size=17)
    notes[3] = "Give the product, then the honest result: the pipeline works, the model beats the app's baseline, domain adaptation is not reliably better, and multi-day forecasts are weak."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 0.8, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper: explainable retail demand forecasting, hybrid LightGBM-SHAP framework"],
            ["Data", "UCI Online Retail II: 1.07 million transactions, 4,631 SKUs; daily SKU demand, one-day-ahead; products kept with >= 1,000 units and >= 150 active days"],
            ["Model", "LightGBM with Optuna tuning (30 trials, 3-fold TimeSeriesSplit) on 41 engineered features (temporal, lag, rolling, ...); strictly backward-looking features"],
            ["Explainability", "Four levels: permutation importance, partial dependence, SHAP (instance level) and ICE curves for heterogeneity between products"],
            ["Reported", "RMSE 33.71, R\u00b2 0.243, MASE 0.799 vs six baselines (naive lag-1, 7-day moving average, linear, random forest, XGBoost 33.89, CatBoost 33.83); rolling statistics the dominant group"],
            ["Stated limits", "One dataset (UK wholesaler); assumes stationary relationships; no promotions or holidays as inputs; one-day horizon; SHAP cost at scale; no domain shift handling"]]
    ftable(s, 0.55, 2.6, [1.7, 10.5], rows, size=12, row_h=0.7)
    notes[4] = "Mishra et al., IEEE Access 2026. TrendCast keeps its ideas of backward-looking features, a gradient-boosted learner and explanation, and adds the missing piece the authors name as a limit: moving a model to a differently distributed context."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Work", "Year", "Approach", "Finding / limitation"],
            [f"Mishra et al. {N('base')} (base)", "2026", "LightGBM + SHAP/ICE explanations; 41 features", "RMSE 33.71, R\u00b2 0.243 on UCI data; one market, no domain shift"],
            [f"Chen & Guestrin {N('xgb')}", "2016", "XGBoost: regularised tree boosting, weighted rows", "Default tabular learner; assumes one data distribution"],
            [f"Makridakis et al. {N('m5')}", "2022", "M5 retail competition (as summarised in the base paper)", "Boosted trees with hand-built features matched deep learning"],
            [f"Shimodaira {N('shim')}; Bickel et al. {N('bickel')}", "2000; 2009", "Importance weighting for covariate shift; weights from a logistic classifier", "The method TrendCast implements; weights can be extreme"],
            [f"Ben-David et al. {N('bendavid')}", "2010", "Target error bounded by source error plus domain divergence", "Unrelated domains transfer badly; bound is loose"],
            [f"Thomassey {N('thom')}", "2010", "Clothing sales forecasting: fuzzy, neural, data mining", "Volatile, seasonal, short-lived items; pre-boosting era"],
            [f"Ekambaram et al. {N('ekam')}", "2020", "Multi-modal attention model for new fashion products", "Needs images and a large product history"],
            [f"Skenderi et al. {N('skend')}; Zhou et al. {N('cdlf')}", "2021; 2026", "Image + Google Trends sales; diffusion for new-product life cycles", "Cold-start work; not weighted transfer of a tabular model"],
            [f"Batch survey {N('s2')}-{N('s5')}", "2026", "Four inventory / forecasting titles", "Titles only; could not be verified online, no result quoted"]]
    ftable(s, 0.55, 1.8, [3.3, 1.0, 4.2, 3.7], rows, size=11, row_h=0.5, align=["l", "c", "l", "l"])
    notes[5] = "Only facts checked against the papers or their abstract pages are used. The four batch-survey titles could not be located online, so nothing is claimed from them."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(g, {"bullet": True, "space_after": 14}) for g in [
        "The base paper's own limitation: one dataset, one market, stationary assumption - no handling of a shifted target context.",
        "Fashion new-item models (Ekambaram, Skenderi, Zhou) need images, external signals or a large product history; a plain tabular model is not covered.",
        "Importance weighting for covariate shift is well established in theory (Shimodaira, Bickel) but is rarely shown inside a retail demand pipeline.",
        "Reported adaptation gains are seldom checked against controls (time-clean split, shuffled weights, pooling the data), so gains may come from leakage.",
        "Forecasts without a clear explanation of drivers are not trusted by planners (base paper); a deployed tool also needs honest multi-day accuracy."]], size=19)
    notes[6] = "Five gaps. TrendCast builds the adaptation workflow and then tests it against controls instead of only reporting the best pair."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.85, 12.2, 2.6)
    ftext(s, 0.85, 1.9, 11.6, 2.5, [
        "Forecasting models trained on one market lose accuracy when applied to another.",
        "New products have no sales history, so conventional forecasting cannot cover them.",
        "Fashion trends shift within a season, invalidating models trained on older data.",
        "Forecasts delivered without explanation are not trusted by inventory planners.",
        "Need: a demand forecasting system that adapts across markets and categories and explains the drivers behind each forecast."], size=16, anchor="m", bullets=True)
    for i, (t, b_) in enumerate([("Input", "Transactions, articles and optional customers CSVs; split, tuning and domain choices"),
                                 ("Output", "Data-quality report, model metrics, domain-shift report, feature importance, 7/14/30-day forecast"),
                                 ("Record", "Experiment metrics (JSON), 39 tests, 25 screenshots of the running console")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.7, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.8, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 5.3, 3.5, 1.0, b_, size=14)
    notes[7] = "Four problem points from the batch statement, then input, output and record."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate([
        "Collect historical fashion retail sales data and engineer seasonal, pricing and category features.",
        "Train gradient-boosting models such as XGBoost to forecast demand at product and category level.",
        "Apply domain adaptation to transfer the model across markets and product categories.",
        "Compare adapted and non-adapted models on a target market with a different data distribution.",
        "Explain forecast drivers so planners understand why demand is predicted to move.",
        "Evaluate using MAE, RMSE and MAPE, and translate error into inventory impact."], 1)], size=22)
    notes[8] = "The six objectives from the batch document. The conclusion slide gives the status of each."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 0.4, "Forecasting pipeline", size=15, color=K.FNAVY, bold=True)
    K.flow(s, 0.55, 2.15, 12.2, 0.85, [("Upload CSVs", K.FNAVY), ("Clean + merge", K.FBLUE), ("Daily demand", K.GREEN), ("31 features", K.ORANGE), ("Split by date", K.PURPLE), ("XGBoost", K.FNAVY)], size=13, gap=0.3, font=FONT)
    ftext(s, 0.55, 3.2, 12.2, 0.4, "Domain adaptation (source domain -> shifted target domain)", size=15, color=K.FNAVY, bold=True)
    K.flow(s, 0.55, 3.6, 12.2, 0.85, [("Source-only model", K.FNAVY), ("Domain classifier", K.FBLUE), ("Weights p/(1-p)", K.GREEN), ("Weighted XGBoost", K.ORANGE), ("Before vs after", K.PURPLE), ("Forecast + explain", K.FNAVY)], size=13, gap=0.3, font=FONT)
    ftext(s, 0.55, 4.8, 12.2, 2.1, bl([
        "Every step is gated: a page refuses to run until the earlier step has produced its output (HTTP 409 with a plain-language message).",
        "Leakage guards: lags and rolling statistics are shifted, the split is by date, tuning uses TimeSeriesSplit, MAPE skips zero-demand rows.",
        "The same src/ package serves the original 11-page Streamlit app and the new 13-page React console; Gemini explanations are optional and see only aggregates.",
    ], 7), size=16)
    notes[9] = "The proposed system as two chains. The adaptation chain is the project's addition to a standard boosted-tree forecaster."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.8, 7.2, 5.1)
    ftext(s, 7.95, 1.95, 4.9, 4.9, bl([
        f"Console: React 19 + Vite, port {F.WEB_PORT}; 13 pages",
        f"API: FastAPI, port {F.API_PORT}; 22 routes, no sign-in (single-user tool)",
        "Pipeline: src/ package (loading, cleaning, daily demand, features, XGBoost, adaptation, evaluation)",
        "State: one process-wide dictionary behind a lock; no database; trained models saved as joblib files",
        "Optional: Gemini REST call with aggregated numbers only",
    ], 8), size=15)
    notes[10] = "Four tiers. No database: uploaded tables and results live in memory; only models are written to disk."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.picture(s, F.diag("02_high_level_workflow.png"), 0.55, 1.8, 7.3, 4.9)
    ftext(s, 8.1, 1.9, 4.7, 5.0, bl([
        "Target: units sold per article per day (rows of the cleaned transaction table).",
        "Features: price, channel, 6 encoded attributes, 14 calendar, 9 lag / rolling (shifted by one day).",
        "Split: first 80% of the dates train, last 20% test; no random split.",
        "Models: 7-day moving average baseline; XGBoost (300 trees, depth 8) with optional tuning.",
        "Adaptation: logistic domain classifier, weight p/(1-p) clipped at 20, weighted XGBoost.",
    ], 8), size=14)
    notes[11] = "Method in one picture: ingest, aggregate, engineer, split, train, adapt, evaluate, forecast."

    # ---- 12 dataset, features & model
    s = S[11]
    set_title(s, "Dataset, Features & Model")
    wipe(s)
    ftile(s, 0.55, 1.8, 2.1, 1.0, f"{DS['raw_rows']:,}", "real H&M rows, 300 articles", K.FBLUE, 22, 11)
    ftile(s, 2.8, 1.8, 2.1, 1.0, f"{DS['feature_rows']:,}", "article-days x 31 inputs", K.GREEN, 22, 11)
    ftile(s, 5.05, 1.8, 2.1, 1.0, "107 days", "2018-09-20 to 2019-01-04", K.ORANGE, 22, 10)
    rows = [["Item", "Detail"],
            ["Source", f"H&M Personalized Fashion Recommendations {N('hm')}; first shard, 300 best sellers"],
            ["Cleaning", f"{DS['raw_rows'] - DS['clean_rows']:,} exact-duplicate rows dropped (11.6%)"],
            ["Split", f"train {FC['split']['train_rows']} rows to {FC['split']['train_end'][:10]}; test {FC['split']['test_rows']} rows"],
            ["Zero-demand rows", f"{DS['zero_demand_share_pct']:.2f}% after gap filling"],
            ["Test window", "Christmas peak and January sales"],
            ["Not in the data", "promotions, regions, fabric, prices of competitors"]]
    ftable(s, 0.55, 3.0, [1.7, 5.45], rows, size=11, row_h=0.46)
    K.picture(s, F.diag("12_model_architecture.png"), 7.5, 1.8, 5.35, 4.2)
    ftext(s, 7.5, 6.1, 5.35, 0.8, "Models: moving average, random forest, LightGBM (baselines), XGBoost default and tuned. Synthetic sample data are used only for smoke tests.", size=12, color=K.FNAVY, italic=True)
    notes[12] = "A real 107-day slice of H&M. The test window is the hardest part of the year to forecast and the training window holds no earlier year."

    # ---- 13 domain-adaptation workflow
    s = S[12]
    set_title(s, "Domain-Adaptation Workflow")
    wipe(s)
    K.picture(s, F.diag("11_flowchart_domain_adaptation.png"), 0.55, 1.75, 12.2, 3.35)
    ftext(s, 0.55, 5.2, 6.0, 1.8, bl([
        "Choose a domain column (channel, product group, department) with a source and a target value; hold out the later half of the target dates.",
        "Source-only XGBoost gives the 'before' metrics on the held-out target rows.",
    ], 6), size=13)
    ftext(s, 6.8, 5.2, 6.0, 1.8, bl([
        "Domain classifier (logistic regression, domain column excluded): accuracy shows how different the domains are.",
        "Weight w = p/(1-p), clipped at 20; weighted XGBoost gives the 'after' metrics, reported as measured.",
    ], 6), size=13)
    notes[13] = "The core algorithm of the project: implemented in src/domain_adaptation.py and the /api/domain/run route."

    # ---- 14 interaction
    s = S[13]
    set_title(s, "User - System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_flow.png"), 0.55, 1.8, 6.4, 5.1)
    K.picture(s, F.diag("08_use_case.png"), 7.1, 1.8, 5.7, 5.1)
    notes[14] = "Sequence of the domain-adaptation run and the use cases of the analyst."

    # ---- 15 data design
    s = S[14]
    set_title(s, "Data Design (no database)")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 6.7, 4.6)
    rows = [["Store", "Content"], ["transactions / articles / customers", "uploaded CSVs, cleaned, in memory"], ["daily demand", "one row per article-day"],
            ["feature table", "31 model inputs + target"], ["results dictionary", "metrics of the models trained"], ["models/*.joblib", "baseline, adapted XGBoost, feature list"],
            [".env", "ports, Gemini key (git-ignored)"]]
    ftable(s, 7.5, 1.9, [2.6, 2.7], rows, size=11, row_h=0.5)
    ftext(s, 0.55, 6.45, 12.2, 0.5, "No foreign keys and no persistence of data: only the model files survive a restart.", size=13, color=K.FNAVY, italic=True)
    notes[15] = "TrendCast has no database. The ER diagram shows logical entities."

    # ---- 16 implementation, performance & testing
    s = S[15]
    set_title(s, "Implementation, Performance & Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([("22", "API routes", K.FBLUE), (f"{F.PYTEST_PASSED} + {F.SMOKE_PASSED}", "pytest tests + smoke checks, all pass", K.GREEN), ("13", "React pages, 25 real screenshots", K.ORANGE), (f"{lat['POST /api/forecast (30 d)']['median']:.0f} ms", "median 30-day forecast request", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 26)
    rows = [["Stage (real subset, 684k rows)", "Seconds"], ["Upload + clean + merge", f"{st['upload+clean+merge (684k rows)']:.1f}"], ["Build features", f"{st['build features']:.1f}"],
            ["Train XGBoost (default)", f"{st['train XGBoost (default)']:.1f}"], ["Train XGBoost (tuned, 10 x 3)", f"{st['train XGBoost (tuned)']:.1f}"], ["Domain adaptation run", f"{st['domain adaptation run']:.1f}"]]
    ftable(s, 0.55, 3.2, [3.6, 1.2], rows, size=12, row_h=0.42, align=["l", "r"])
    ftext(s, 6.0, 3.2, 6.8, 3.7, bl([
        f"{F.PYTEST_UNIT} unit tests (cleaning, leakage-free lags, split, metrics, weights) and {F.PYTEST_API} API tests (gating, validation, full flow).",
        "Smoke test: 26 live checks incl. bad file -> 400, same source/target -> 400, bad horizon -> 400.",
        "Browser walk-through: 25 screens; only console problems were Gemini 502s.",
        "Measured on an i5-12500, 15.7 GB, no GPU, other jobs running.",
        "Not tested: load, many users, Chrome-only, full-size H&M.",
    ], 7), size=14)
    notes[16] = "Implementation facts and the testing that was actually run, with its limits."

    # ---- 17 results: model performance
    s = S[16]
    set_title(s, "Results - Model Performance (chronological 80/20 split)")
    wipe(s)
    order = [("Moving average (7d)", "Moving average (app baseline)"), ("Naive (lag 1)", "Naive: repeat yesterday"), ("Rolling mean 7 (shifted)", "Rolling mean 7"), ("Random forest", "Random forest"),
             ("LightGBM", "LightGBM"), (F.XGB, "XGBoost default (5 seeds)"), (F.XGB_T, "XGBoost tuned")]
    rows = [["Model", "RMSE", "MAE", "R\u00b2"]] + [[lab, f"{M[k]['RMSE']:.2f}", f"{M[k]['MAE']:.2f}", f"{M[k]['R2']:.3f}"] for k, lab in order]
    ftable(s, 0.55, 1.85, [3.2, 0.9, 0.9, 0.9], rows, size=12, row_h=0.42, align=["l", "r", "r", "r"])
    ftext(s, 0.55, 5.35, 5.9, 1.6, bl([
        f"XGBoost default: RMSE {xs['RMSE']['mean']:.2f} \u00b1 {xs['RMSE']['std']:.2f} over 5 seeds; fits in {FC['xgboost_fit_seconds_mean']:.1f} s.",
        "Beats the app's moving average, does NOT beat repeating yesterday.",
    ], 6), size=13)
    K.picture(s, F.fig("f01_model_comparison.png"), 6.7, 1.8, 6.1, 4.5)
    ftext(s, 6.7, 6.4, 6.1, 0.5, f"Test: {FC['split']['test_start'][:10]} to {FC['split']['test_end'][:10]}, {FC['split']['test_rows']} rows; MAPE on non-zero rows is {M[F.XGB]['MAPE (%)']:.0f}% (low-volume days).", size=11, color=K.FNAVY, italic=True)
    notes[17] = "Be explicit: on this window a one-line naive forecast is better than the boosted tree. Rolling-origin backtests show XGBoost beats the moving average in all three folds and beats lag-1 in one."

    # ---- 18 predicted vs actual and inventory units
    s = S[17]
    set_title(s, "Error Breakdown - Predicted vs Actual and Inventory Units")
    wipe(s)
    K.picture(s, F.fig("f03_test_daily_series.png"), 0.45, 1.75, 6.4, 3.6)
    K.picture(s, F.fig("f09_inventory_units.png"), 6.95, 1.75, 5.9, 3.6)
    rows = [["Forecast", "Total bias", "Under-forecast (lost sales)", "Over-forecast (excess)", "WAPE"],
            ["XGBoost", f"{inv_x['bias_pct']:+.1f}%", f"{inv_x['understock_pct_of_demand']:.1f}% of demand", f"{inv_x['overstock_pct_of_demand']:.1f}%", f"{inv_x['wape_pct']:.1f}%"],
            ["Moving average (7d)", f"{inv_m['bias_pct']:+.1f}%", f"{inv_m['understock_pct_of_demand']:.1f}%", f"{inv_m['overstock_pct_of_demand']:.1f}%", f"{inv_m['wape_pct']:.1f}%"]]
    ftable(s, 0.55, 5.45, [2.6, 1.5, 3.2, 2.7, 1.5], rows, size=12, row_h=0.4, align=["l", "r", "r", "r", "r"])
    ftext(s, 0.55, 6.7, 12.2, 0.3, f"{INV['actual_units']:,.0f} units sold in the test window. Units are offline measurements; the app itself shows no inventory view. XGBoost over-forecasts the window overall.", size=11, color=K.FNAVY, italic=True)
    notes[18] = "Confusion-matrix equivalent for a regression task: predicted vs actual daily totals and the split of error into lost-sales and excess units."

    # ---- 19 parameter analysis
    s = S[18]
    set_title(s, "Parameter Analysis - Features, Tuning and Horizon")
    wipe(s)
    K.picture(s, F.fig("f02_ablation.png"), 0.45, 1.75, 6.4, 3.65)
    K.picture(s, F.fig("f04_recursive_horizon.png"), 6.95, 1.75, 5.9, 3.65)
    ftext(s, 0.55, 5.55, 12.2, 1.4, bl([
        f"Feature groups: lag / rolling only gives RMSE {abl['lag / rolling only']['RMSE']:.2f} (R\u00b2 {abl['lag / rolling only']['R2']:.2f}), better than all 31 features ({abl['all features (as shipped)']['RMSE']:.2f}); without lag / rolling R\u00b2 is {abl['no lag / rolling']['R2']:.2f}. Absolute-time features cannot extrapolate past the training dates.",
        f"Tuning (RandomizedSearchCV, 10 iterations x 3 TimeSeriesSplit, {FC['tuning_seconds']:.0f} s): RMSE {M[F.XGB]['RMSE']:.2f} -> {M[F.XGB_T]['RMSE']:.2f}; best depth {FC['tuned_best_params']['max_depth']}, learning rate {FC['tuned_best_params']['learning_rate']}.",
        f"Recursive forecast WAPE by horizon: {rec['xgb_app']['by_band'][0]['WAPE (%)']:.0f}% / {rec['xgb_app']['by_band'][1]['WAPE (%)']:.0f}% / {rec['xgb_app']['by_band'][2]['WAPE (%)']:.0f}% (days 1-7 / 8-14 / 15-30) against {rec['flat_ma7']['by_band'][0]['WAPE (%)']:.0f}% / {rec['flat_ma7']['by_band'][1]['WAPE (%)']:.0f}% / {rec['flat_ma7']['by_band'][2]['WAPE (%)']:.0f}% for a flat 7-day mean.",
    ], 5), size=12)
    notes[19] = "Parameter analysis: which inputs matter, what tuning buys, and how fast the multi-day forecast degrades. The app's loop also freezes four calendar features; refreshing them did not help."

    # ---- 20 domain adaptation results
    s = S[19]
    set_title(s, "Results - Domain Adaptation (6 pairs x 5 seeds)")
    wipe(s)
    K.picture(s, F.fig("f05_domain_pairs.png"), 0.45, 1.75, 6.3, 3.9)
    names = ["Channel 2 -> 1", "Channel 1 -> 2", "Upper -> Lower body", "Lower -> Upper body", "Knitwear -> Trouser", "Jersey Basic -> Blouse"]
    assert len(pairs) == 6
    rows = [["Pair", "RMSE before", "adapted", "change", "pooled"]]
    for nm, p in zip(names, pairs):
        e = p["app"]
        rows.append([nm, f"{e['before']['RMSE']['mean']:.2f}", f"{e['adapted']['RMSE']['mean']:.2f}", f"{e['rmse_improvement_pct_mean']:+.1f}%", f"{e['pooled_unweighted']['RMSE']['mean']:.2f}"])
    ftable(s, 6.95, 1.8, [2.3, 1.0, 0.9, 0.9, 0.8], rows, size=11, row_h=0.42, align=["l", "r", "r", "r", "r"])
    ftext(s, 6.95, 4.85, 5.9, 0.9, f"Mean change {sm['mean_rmse_improvement_pct']:+.1f}% as built; {sm['normalised_mean_rmse_improvement_pct']:+.1f}% with mean-1 weights; {sm['time_clean_mean_rmse_improvement_pct']:+.1f}% time-clean. 'pooled' = source + early target rows, no weights.", size=11, color=K.FNAVY, italic=True)
    ftext(s, 0.55, 5.75, 12.2, 1.25, bl([
        f"Helped on {sm['pairs_where_adaptation_helped']} of {sm['pairs_total']}. The channel 2 -> 1 gain ({chan21['app']['rmse_improvement_pct_mean']:+.1f}%) turns into {chan21['time_clean']['rmse_improvement_pct_mean']:+.1f}% when source rows are limited to dates before the target test window.",
        "When the domain classifier separates domains perfectly (department pairs, accuracy 100%), weights are about 1e-5 and XGBoost stops splitting (R\u00b2 about 0); rescaling to mean 1 removes the collapse.",
        "Unweighted pooling beats weighted adaptation on 5 of 6 pairs.",
    ], 4), size=12)
    notes[20] = "The central finding. Domain adaptation as implemented is not reliably better; the controls explain why."

    # ---- 21 comparison with base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only - different datasets)")
    wipe(s)
    rows = [["Aspect", "Base paper (LightGBM-SHAP)", "TrendCast (XGBoost + adaptation)"],
            ["Data", "UCI Online Retail II, 1.07 M transactions, 4,631 SKUs", f"H&M subset, {DS['clean_rows']:,} rows, {DS['articles']} articles, 107 days"],
            ["Task", "One-day-ahead SKU demand", "One-day-ahead evaluation plus 7/14/30-day recursive forecast"],
            ["Best model", "LightGBM, RMSE 33.71, R\u00b2 0.243", f"XGBoost RMSE {M[F.XGB]['RMSE']:.2f} (R\u00b2 {M[F.XGB]['R2']:.2f}); tuned {M[F.XGB_T]['RMSE']:.2f}"],
            ["Vs 7-day moving average", "2.86 RMSE better (about 7.8%)", f"{M[F.MA]['RMSE'] - M[F.XGB]['RMSE']:.2f} RMSE better (about {(M[F.MA]['RMSE'] - M[F.XGB]['RMSE']) / M[F.MA]['RMSE'] * 100:.0f}%)"],
            ["Vs naive lag-1", "14.06 RMSE better (about 29%)", f"lag-1 is {M[F.XGB]['RMSE'] - M['Naive (lag 1)']['RMSE']:.2f} RMSE better than XGBoost"],
            ["Dominant features", "Rolling statistics (R\u00b2 -0.064 when removed)", f"Lag / rolling (R\u00b2 {abl['no lag / rolling']['R2']:.2f} when removed)"],
            ["Explainability", "PFI, PDP, SHAP, ICE", f"Gain importance in app; TreeSHAP offline (rank agreement {EX['spearman_rank_corr_shap_vs_gain']:.2f})"],
            ["Domain shift", "Not addressed (stated limit)", f"Implemented; helps {sm['pairs_where_adaptation_helped']} of {sm['pairs_total']} pairs"]]
    ftable(s, 0.55, 1.8, [2.4, 4.8, 5.0], rows, size=12, row_h=0.5)
    ftext(s, 0.55, 6.4, 12.2, 0.55, "RMSE values sit on different scales (different units sold per SKU-day), so only relative findings are compared: boosted trees beat the moving average, and lag / rolling features dominate in both studies.", size=12, color=K.FNAVY, italic=True)
    notes[21] = "Say plainly that the datasets differ. Agreement: boosting beats the moving average and rolling/lag features dominate. Difference: the naive lag-1 forecast is much stronger on our short, dense window."

    # ---- 22-24 output screens
    def two_shots(slide, title, a, b, cap_a, cap_b):
        set_title(slide, title)
        wipe(slide)
        K.picture(slide, crop_shot(a), 0.45, 1.75, 6.0, 3.75, border=True)
        K.picture(slide, crop_shot(b), 6.85, 1.75, 6.0, 3.75, border=True)
        ftext(slide, 0.45, 5.65, 6.0, 1.0, cap_a, size=13, color=K.FNAVY, bold=True)
        ftext(slide, 6.85, 5.65, 6.0, 1.0, cap_b, size=13, color=K.FNAVY, bold=True)

    two_shots(S[21], "Output - Data Upload and Exploration", "06_upload-quality-report.png", "07_explore.png",
              f"Data-quality report on the real subset: {DS['clean_rows']:,} transactions, 276,168 customers, 300 products, 79,214 rows removed",
              f"Explore demand: {DS['clean_rows']:,} units, 30,481 product-days, 107 days; daily totals show the two demand peaks")
    notes[22] = "Real H&M subset loaded in the running console."
    two_shots(S[22], "Output - Model Training and Domain Adaptation", "13_training-comparison.png", "16_domain-before-after.png",
              "Training page: XGBoost (RMSE 11.065, R\u00b2 0.337) against the moving average (RMSE 12.891, R\u00b2 0.101)",
              "Domain adaptation channel 1 -> 2: RMSE 18.983 -> 18.989; the page shows the change as 'worse', unedited")
    notes[23] = "The domain screen shows an honest zero-effect result on the default pair."
    two_shots(S[23], "Output - Evaluation and Forecast", "18_evaluation-importance.png", "20_forecast-table.png",
              "Evaluation: before/after table and gain-based feature importance (top: is_month_end, lag_1, day_of_year)",
              "Forecast: history and 14-day forecast with the forecast table for one article")
    notes[24] = "Evaluation and forecast pages. The AI Insights page showed Gemini 503 / timeouts during capture and is not used here."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 1.0, "TrendCast is a working, tested forecasting product on real H&M data whose honest measurements show where the method helps and where it does not.", size=17, color=K.FNAVY, bold=True)
    rows = [["#", "Objective", "Outcome"],
            ["1", "Real data, seasonal / price / category features", f"Met: H&M subset, 31 inputs, shifted lags, date split; no promotions in the data"],
            ["2", "XGBoost at product and category level", "Met at article level; no separate category model"],
            ["3", "Domain adaptation across markets / categories", "Implemented for channel, group, department; markets = 2 channels"],
            ["4", "Compare adapted vs non-adapted", f"Done: helps {sm['pairs_where_adaptation_helped']}/{sm['pairs_total']}, mean {sm['mean_rmse_improvement_pct']:+.1f}%; not reliable"],
            ["5", "Explain forecast drivers", "Partly: gain importance in app, TreeSHAP offline only"],
            ["6", "MAE / RMSE / MAPE and inventory impact", "Metrics met; inventory units offline only, no cost savings shown"]]
    ftable(s, 0.55, 2.55, [0.5, 4.5, 7.2], rows, size=12, row_h=0.5, align=["c", "l", "l"])
    ftext(s, 0.55, 6.15, 12.2, 0.8, "Key findings: boosted trees beat the moving average but not repeat-yesterday; lag / rolling features carry the model; weights must be normalised; adaptation needs time-clean testing.", size=13, color=K.FNAVY, italic=True)
    notes[25] = "Be explicit about which objectives were met, partly met or not met. The abstract's claim of fewer shortages and less overstock is not demonstrated."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Limitations & Future Scope")
    wipe(s)
    fbox(s, 0.55, 1.8, 6.0, 4.5, fill=K.FZEBRA)
    ftext(s, 0.75, 1.9, 5.6, 0.4, "Known limitations", size=17, color=K.FNAVY, bold=True)
    ftext(s, 0.75, 2.4, 5.6, 4.4, bl([
        "107 days, 300 best-selling articles, one data shard; no multi-year seasonality",
        "Cleaning drops 11.6% duplicate rows that are real repeat purchases",
        "Target-day price and channel are inputs; frozen in recursive forecasts",
        "Source rows overlap the target test dates; weights not normalised",
        "No cold-start mode; SHAP and inventory impact offline only",
        "Gemini AI Insights unavailable during capture (503 / timeout)",
        "Single user, no authentication, no load test",
    ], 6), size=14)
    fbox(s, 6.8, 1.8, 6.0, 4.5, fill=K.FHEAD)
    ftext(s, 7.0, 1.9, 5.6, 0.4, "Future scope", size=17, color=K.FNAVY, bold=True)
    ftext(s, 7.0, 2.4, 5.6, 4.4, bl([
        "Normalise weights; make the time-clean protocol the default",
        "Add a cold-start mode from product attributes (R\u00b2 0.27 offline)",
        "Keep rolling-origin backtests and a lag-1 baseline in the app",
        "Direct multi-horizon or probabilistic forecasts",
        "SHAP in the app; inventory cost simulation",
        "Full H&M data, promotions and regions; CORAL / adversarial adaptation",
        "Authentication, persistence, multi-user roles",
    ], 6), size=14)
    notes[26] = "Limitations first, then concrete next steps drawn from the measured defects."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    keys = ["base", "xgb", "lgbm", "shap", "treeshap", "m5", "shim", "bickel", "sugi", "bendavid", "thom", "ekam", "skend", "cdlf", "hm", "sk"]
    short_ = [f"[{_IDX[k]}] {clean_ref(REFS[_IDX[k] - 1])}" for k in keys]
    short_ = [t if len(t) < 330 else t[:327] + "..." for t in short_]
    ftext(s, 0.55, 1.75, 6.0, 5.2, [(t, {"space_after": 4}) for t in short_[:8]], size=10)
    ftext(s, 6.8, 1.75, 6.0, 5.2, [(t, {"space_after": 4}) for t in short_[8:]] + [(f"The full numbered list of {len(REFS)} references, including the batch survey titles {N('s2')}-{N('s5')}, is in the report.", {"italic": True})], size=10)
    notes[27] = "Selected references; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh_ in S[27].shapes:
        if sh_.name == "Text 2":
            K.replace_text(sh_, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "TrendCast")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
