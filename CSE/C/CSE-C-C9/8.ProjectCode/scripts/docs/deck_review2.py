"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from . import shared as SH
from .deck_review1 import agenda, is_ph, prepare, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def shot_row(s, items, x0=0.6, y0=1.3, w=3.95, h=2.47, gx=0.14, cols=3, rows_gap=0.3):
    """Grid of captioned screenshots. items: [(file, caption)]"""
    for i, (name, cap) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + 0.28 + rows_gap)
        K.picture(s, F.shot(name), x, y, w, h, border=True)
        K.text(s, x, y + h + 0.04, w, 0.25, cap, size=11, color=K.TXT, align="c", italic=True)


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    M = F.METRICS
    C = F.CM[F.BEST]
    MEAS = F.MEAS
    lat = MEAS["api_latency_ms_127_0_0_1"]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: a trained XGBoost profile classifier with SHAP explanations, a Holt-Winters forecast, a Flask API and a React interface",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how the system is designed and built: the data and model, what has been implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
               ("05", "Data flow, data model and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Financial assessment uses few parameters and a static score; non-linear demographic effects are missed, the future is not considered and the result cannot be explained.", K.ORANGE, "!"),
        ("Proposed system", "Twelve validated inputs become engineered features; an XGBoost model gives a strength score, profile and risk band; SHAP explains it; Holt-Winters adds a 12-month outlook; a what-if screen compares scenarios.", K.BLUE, "i"),
        ("Base paper link", "Reuses the explainable-ML framework of the Korean hospital study (feature engineering, four model families, SHAP) for individuals. Group K-Fold, temporal validation and counterfactual analysis do not apply to one-row-per-person data.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.7, t, b_, col, gl, body_size=16)
    notes[3] = "One-minute recap of Review 1: the base paper is about organisations; we apply the same framework to individuals and deliver it as a tested application."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.8, 5.5)
    K.text(s, 8.7, 1.5, 4.05, 5.2, [
        ("**Four tiers**", {"space_after": 8}),
        ("Presentation: React single-page app on port 5409; original Jinja pages on 8409.", {"bullet": True}),
        ("Application: Flask on port 8409, routes, JSON API, validation.", {"bullet": True}),
        ("Model and service tier: predictor, SHAP, what-if, forecast loader.", {"bullet": True}),
        ("Data: pickled pipelines, JSON artifacts, UCI Adult CSV files.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=9)
    notes[4] = "Four tiers. The online path only loads what scripts/train.py wrote offline."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.35, [("UCI Adult data", K.NAVY), ("Clean + 12 derived features", K.PURPLE), ("Stratified 80/20 split", K.GREEN), ("Pipeline x4 models", K.ORANGE),
                                      ("5-fold CV + test", K.BLUE), ("Select by ROC-AUC", K.NAVY), ("SHAP + forecast + JSON", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("Leakage-safe", "Imputation, one-hot encoding and scaling sit inside each scikit-learn Pipeline, so they are fitted on training folds only."),
                                 ("Stratified, one row per person", "A stratified 80/20 split and 5-fold CV preserve the 24 % positive share; no entity-grouped or temporal split applies to this data."),
                                 ("Reproducible", "Seed 42 everywhere; train.py writes metrics, validation, SHAP, forecast and plots to JSON/PNG, re-derived by report_metrics.py.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.3, 3.85, 3.2)
        K.text(s, x + 0.25, 3.45, 3.4, 0.5, t, size=17, color=K.INK, bold=True)
        K.text(s, x + 0.25, 4.05, 3.4, 2.3, b_, size=15, color=K.TXT)
    notes[5] = "The training script is one command and writes every number to disk. Preprocessing lives in the pipelines used at prediction time too."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.N_ROWS:,}", "records, UCI Adult / Census Income", K.BLUE), ("15", "raw columns (14 inputs + income)", K.GREEN),
                                   (f"{F.N_TRAIN:,} / {F.N_TEST:,}", "stratified train / test split", K.ORANGE), (F.pct(F.RM["positive_rate_all"]), "earn more than 50K (positive class)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    K.bar_chart(s, 0.6, 2.95, 6.3, 3.9, ["<=50K", ">50K"], [("Test split", [F.TEST_NEG, F.TEST_POS])], colors=[K.BLUE], number_format="#,##0", font_size=12, legend=False)
    mc = F.RM["missing_cells_raw"]
    K.text(s, 7.2, 3.0, 5.5, 3.8, [
        ("Public data (UCI, Kohavi 1996), 32,561 + 16,281 rows; target income above 50K is used as a financial-profile signal, not a credit label.", {"bullet": True}),
        (f"Missing values marked '?': workclass {mc['workclass']:,}, occupation {mc['occupation']:,}, native-country {mc['native-country']:,}.", {"bullet": True}),
        ("The data are 1994 US census records and have no time dimension, so forecasting uses a separate, documented synthetic index.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=8)
    notes[6] = "UCI Adult: one row per person, so a stratified split does not leak individuals. Income is a proxy, which is stated as a limit throughout."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing and feature engineering")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 0.95, [("'?' to missing", K.NAVY), ("Median / 'Unknown' impute", K.BLUE), ("12 derived features", K.PURPLE), ("One-hot encode", K.GREEN), ("Scale (LR only)", K.ORANGE)], size=13, gap=0.25)
    rows = [["Derived feature", "Rule"],
            ["net-capital, capital-intensity", "gains minus losses; gains plus losses"],
            ["log-capital-gain / -loss", "log(1 + value), for the linear model"],
            ["hours-band", "Part-time <30, Full-time 30-40, Extended 41-60, Very-long"],
            ["age-band, education-tier", "5 age bands; Secondary, Higher-secondary, Tertiary"],
            ["region, employment-stability", "from native country; from workclass and hours"],
            ["has-capital-gain / -loss, capital-position", "flags; Net-loss, No-capital, Moderate-gain, High-gain"]]
    K.table(s, 0.6, 2.7, [4.0, 5.0], rows, font_size=12, row_h=0.55)
    K.card(s, 9.85, 2.7, 2.88, 3.85, "Feature set", "10 numeric and 16 categorical features feed the ColumnTransformer. The census weight fnlwgt has no meaning for a new user and is imputed with the training median.", K.BLUE, "26", body_size=13, title_size=15)
    notes[7] = "Every derived column is computed from the raw fields only; the same function runs at training and at prediction time."

    # ---- 8 model
    s = S[7]
    set_title(s, "Models compared")
    wipe(s)
    rows = [["Model", "Configuration", "Role"],
            ["Logistic Regression", "C = 1.0, max_iter 2000, standardised numerics", "Interpretable linear baseline"],
            ["Random Forest", "300 trees, unlimited depth", "Bagged-tree comparator"],
            ["Gradient Boosting", "scikit-learn defaults, random_state 42", "Boosted-tree comparator"],
            ["XGBoost", "400 trees, depth 6, learning rate 0.05, subsample 0.9, colsample 0.9, lambda 1", "Selected: best ROC-AUC"]]
    K.table(s, 0.6, 1.5, [2.6, 6.2, 3.33], rows, font_size=14, row_h=0.7, first_bold=True)
    K.tile(s, 0.6, 5.2, 3.85, 1.4, "No tuning", "hyperparameters fixed in advance, as in the base paper", K.BLUE, vsize=24)
    K.tile(s, 4.64, 5.2, 3.85, 1.4, "No rebalancing", "24 % positive class kept as is; threshold analysis instead", K.GREEN, vsize=24)
    K.tile(s, 8.68, 5.2, 4.05, 1.4, "Tree models", "chosen for non-linearity and exact TreeSHAP", K.ORANGE, vsize=24)
    notes[8] = "Four model families like the base paper (minus its MLP). Hyperparameters were set once, not searched; selection is by ROC-AUC. The 24 % share is noted as a mild imbalance."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training and evaluation configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Split / seed", f"stratified 80/20 on the target, random_state 42: train {F.N_TRAIN:,}, test {F.N_TEST:,}"],
            ["Cross-validation", "5-fold stratified, shuffled, scored by ROC-AUC on the training split"],
            ["Primary metric / threshold", "ROC-AUC for selection; accuracy, precision, recall, F1 at probability 0.5"],
            ["SHAP", "TreeExplainer (tree_path_dependent) on a 500-row sample for global importance; live per request"],
            ["Forecast", "Holt-Winters, additive trend and seasonality (12), 12-month horizon, 95% band from residual sd"],
            ["Hardware", f"{MEAS['environment']['cpu']}, {MEAS['environment']['ram_gb']} GB RAM, CPU only; Python {MEAS['environment']['python']}"]]
    K.table(s, 0.6, 1.5, [3.2, 8.93], rows, font_size=14, row_h=0.72, first_bold=True)
    notes[9] = "The whole evaluation protocol on one slide. Selection on the test AUC with no separate validation set is noted as a limitation; the CV ranking agrees."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 5.3, 5.55)
    K.text(s, 6.3, 1.5, 6.4, 3.0, [
        ("**Validate first.** All 12 fields present, in the allowed set and range; otherwise HTTP 400 with messages and no model call.", {"bullet": True, "space_after": 9}),
        ("**Score.** p = P(income > 50K) from the Pipeline, shown as the financial-strength score.", {"bullet": True, "space_after": 9}),
        ("**Explain.** Live SHAP: top five strengthening and weakening factors, in plain language.", {"bullet": True}),
    ], size=15, color=K.INK)
    rows = [["Score p", "Profile", "Risk band"], ["p >= 0.60", "Established", "Low"], ["0.35 <= p < 0.60", "Developing", "Moderate"], ["p < 0.35", "Emerging", "High"]]
    K.table(s, 6.3, 4.65, [2.4, 2.0, 2.0], rows, font_size=14, row_h=0.5, align=["l", "c", "c"])
    notes[10] = "Band cut-offs are fixed in profile_from_proba. On the test split they give Emerging 7.2 %, Developing 44.0 % and Established 85.2 % actual income-above-50K rates."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 7.2, 5.55)
    rows = [["Module", "Role"], ["app/routes.py, api.py", "pages and JSON routes"], ["app/utils/validation.py", "input checks"], ["app/services/predictor.py", "predict, SHAP, insights"],
            ["app/services/whatif.py", "baseline vs scenario"], ["scripts/feature_engineering.py", "cleaning, features, encoder"], ["scripts/train.py, forecast.py", "offline training"], ["frontend/src", "React screens"]]
    K.table(s, 8.1, 1.5, [2.65, 1.98], rows, font_size=11, row_h=0.5)
    notes[11] = "Level-1 data flow: six processes, one of them offline. Levels 0 and 2 are in the report."

    # ---- 12 data model and UML
    s = S[11]
    set_title(s, "Data model and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.0, 4.8)
    K.picture(s, F.diag("06_uml_class_diagram.png"), 6.8, 1.35, 5.9, 4.8)
    K.text(s, 0.6, 6.25, 12.13, 0.7, "No relational database: trained pipelines are .pkl files, evaluation output is JSON, the what-if baseline is kept in browser session storage and nothing about a person is stored. The UML draws modules as classes because the code is function-oriented.", size=12, color=K.TXT, align="c", italic=True)
    notes[12] = "The batch brief mentions MySQL; the delivered system deliberately stores no personal data, so there is no RDBMS. Requests and responses are the entities."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    e = MEAS["environment"]
    rows = [["Layer", "Technology"],
            ["Data and ML", f"pandas, NumPy, scikit-learn {e['scikit-learn']}, XGBoost {e['xgboost']}, statsmodels {e['statsmodels']}"],
            ["Explainability", f"SHAP {e['shap']} (TreeExplainer), matplotlib"],
            ["API", f"Flask {e['flask']} (JSON API and original Jinja pages), joblib model loading"],
            ["Front end", "React 19, Vite, React Router, Recharts, Framer Motion"],
            ["Testing", "pytest, Flask test client, scripts/smoke_test.py, Playwright screen capture"],
            ["Run", "run.bat creates the venv, trains if needed, builds the front end; API 8409, front end 5409"]]
    K.table(s, 0.6, 1.5, [2.6, 9.53], rows, font_size=15, row_h=0.7, first_bold=True)
    notes[13] = "All open source and local; no external service is called at run time."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Cleaning, 12 derived features, encoders", "Done", "scripts/feature_engineering.py, 2 tests"],
            ["Four-model training, CV, selection", "Done", "scripts/train.py, artifacts/*.json"],
            ["SHAP global and live local explanations", "Done", "predictor.py, shap_global.json"],
            ["Holt-Winters 12-month forecast", "Done (synthetic data)", "forecast.json, 12 points + 95% band"],
            ["Flask API (16 routes), validation, what-if", "Done", "7 API/page tests, smoke test 35/35"],
            ["React interface (11 pages), sample login", "Done", "19 real screenshots"],
            ["Real macro indicators, database, fairness audit", "Not implemented", "listed as future work"]]
    K.table(s, 0.6, 1.5, [4.9, 2.4, 4.83], rows, font_size=14, row_h=0.65)
    notes[14] = "State of the code base. The honest gaps are real macroeconomic data, persistence and a fairness audit."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: held-out test split")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.pct(M["accuracy"]), "accuracy", K.BLUE), (F.f3(M["roc_auc"]), "ROC-AUC", K.GREEN), (F.f3(M["f1"]), "F1 (threshold 0.5)", K.ORANGE), (F.f3(M["cv_roc_auc_mean"]), f"5-fold CV AUC (sd {M['cv_roc_auc_std']:.4f})", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=28)
    cats = [F.MODEL_LABEL[m] for m in F.MODELS]
    K.bar_chart(s, 0.6, 2.9, 7.6, 3.95, cats, [("ROC-AUC", [F.COMPARE[m]["roc_auc"] for m in F.MODELS]), ("F1", [F.COMPARE[m]["f1"] for m in F.MODELS])],
                colors=[K.BLUE, K.GREEN], number_format="0.000", font_size=12, max_value=1.1)
    K.card(s, 8.5, 2.95, 4.23, 3.75, "Reading", f"XGBoost leads on every headline metric. n = {F.N_TEST:,} test records; at 0.5 recall is {F.pct(M['recall'])} and precision {F.pct(M['precision'])}. Protocol and caveats (income is not credit, test-set selection) are on the next slides.", K.BLUE, "i", body_size=14)
    notes[15] = "First measured numbers, all from artifacts/metrics.json and model_comparison.json. The final review adds confusion matrices, the threshold sweep and calibration."

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shot_row(s, [("04_dashboard.png", "Dashboard"), ("05_assessment.png", "Assessment form"), ("14_result-established.png", "Result with SHAP drivers"),
                 ("07_explainability.png", "Explainability"), ("08_forecast.png", "12-month forecast"), ("09_whatif.png", "What-if comparison")], y0=1.25, rows_gap=0.12)
    notes[16] = "Real screenshots from the running application with the trained model and live predictions."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(str(MEAS["pytest"]["passed"]), "pytest tests passed", K.GREEN), (f"{MEAS['smoke_test']['passed']}/{MEAS['smoke_test']['total']}", "live smoke-test checks", K.BLUE),
                                   (f"{lat['POST /api/predict']['median']:.0f} ms", "median POST /api/predict", K.ORANGE), (f"{lat['POST /api/whatif']['median']:.0f} ms", "median POST /api/whatif", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["Saved pipelines were written by an older scikit-learn / XGBoost and warn on load", "Metrics were re-derived from the loaded models and match exactly; versions are documented"],
            ["Invalid input (age 7, -5) reaches the API", "Server-side validation returns HTTP 400 with a message; the form shows it (screen 13)"],
            ["Large what-if changes move the score by about 98 points", "Result is labelled a model simulation, not a causal prediction"]]
    K.table(s, 0.6, 3.1, [5.6, 6.53], rows, font_size=13, row_h=0.85)
    notes[17] = "The suite runs offline against the real model. Latency was measured on 127.0.0.1 with 40 calls each, CPU only."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["Census data has no time dimension, so it cannot forecast", "Separate monthly index, documented as synthetic, modelled with Holt-Winters"],
            ["Income is a proxy, not creditworthiness", "Profile and risk band wording; limit stated on every analysis screen"],
            [f"Positive class is {F.pct(F.RM['positive_rate_all'])}; recall {F.pct(M['recall'])} at 0.5", "Threshold analysis shows the precision-recall trade-off"],
            ["Sex, race and marital status are inputs and influential", "Disclosed as a fairness limitation; audit listed as future work"],
            ["Docker files cover only the Flask pages", "Documented; run.bat starts both servers locally"]]
    K.table(s, 0.6, 1.5, [5.6, 6.53], rows, font_size=14, row_h=0.8)
    notes[18] = "Each challenge was met by a concrete change or an explicit statement of the limit."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Evaluate", "Confusion matrices, threshold sweep, calibration and observed rates per profile band on the test split.", K.BLUE, "1"),
        ("Compare", "Set the results against the base paper, stating where data and protocol differ.", K.GREEN, "2"),
        ("Document", "Final report, paper and deck with every figure regenerated from JSON.", K.ORANGE, "3"),
        ("Extend (future)", "Real macro indicators, fairness audit, persistence, tuning and external validation.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.1, 1.6, 2.9, 4.4, t, b_, col, gl, body_size=15)
    notes[19] = "Plan to the final review. The extensions at the right are out of scope for this submission."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why XGBoost; why a synthetic forecast; why income as the target; what about fairness."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.scrub_theme(out_path)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
