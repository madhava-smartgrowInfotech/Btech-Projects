"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, prepare, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    lr, rf, dt = F.LR, F.RF, F.DT
    ds, sp = F.DS, F.SP
    lat = F.LAT
    api = (F.API or {}).get("repeated_ms", {})

    # ---- 1 title
    title_slide(S[0], "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS",
                "Design, methodology and progress: five classifiers compared, risk bands, drivers and retention actions in a web application")
    notes[1] = "This review shows how the system is designed and built: data, model, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and models"), ("04", "Training and decision logic"),
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
        ("Problem", "Churn is noticed after the customer has gone, offers are uniform, scores come without reasons and imbalanced data hides the churn class.", K.ORANGE, "!"),
        ("Proposed system", "Clean and encode the data, compare five classifiers, pick the best on F1, then show risk bands, drivers, what-if and rule-based retention actions.", K.BLUE, "i"),
        ("Base paper link", "Takes the motivation (explain churn, tie it to retention) from the base paper; does not reproduce its perturbation explainer, LIME or XGBoost/LightGBM/CatBoost models.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.6, t, b_, col, gl, body_size=18)
    notes[3] = "One-minute recap of Review 1. We deliver the application and measure it honestly; the base paper is a research framework on the real Telco data."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 6.6, 5.5)
    K.text(s, 7.5, 1.5, 5.2, 5.2, [
        ("**Presentation:** React 19 + Vite SPA \"ChurnIQ\" (port 5314) and the original Streamlit app.", {"bullet": True, "space_after": 8}),
        ("**Application:** FastAPI (port 8314): 31 route handlers, HMAC-signed bearer token, in-memory AppState.", {"bullet": True, "space_after": 8}),
        ("**Core:** 12 pure-Python modules in src/, shared by both front ends and untouched by the API layer.", {"bullet": True, "space_after": 8}),
        ("**Data and state:** CSV, joblib model files, session state in memory. No SQL database.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[4] = "Four tiers. The FastAPI layer imports the src/ modules, so no model code was rewritten for the web interface."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.35, [("Load CSV", K.NAVY), ("Profile + clean", K.NAVY), ("Split 80/20", K.PURPLE), ("Fit preprocessor", K.GREEN),
                                      ("Balance + train", K.ORANGE), ("Evaluate + select", K.BLUE), ("Save + score", K.NAVY)], size=14, gap=0.22)
    for i, (t, b_) in enumerate([("No leakage", "Imputer, scaler and encoder are fitted on the training split only; SMOTE touches only the transformed training split."),
                                 ("Selection on F1", "The best model is chosen on F1 by default, never on accuracy alone; the metric is user-selectable."),
                                 ("Reproducible", "Seed 42; one script writes every metric to JSON; the same functions serve the app and the experiments.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.3, 3.85, 3.2)
        K.text(s, x + 0.25, 3.45, 3.4, 0.5, t, size=19, color=K.INK, bold=True)
        K.text(s, x + 0.25, 4.05, 3.4, 2.3, b_, size=18, color=K.TXT)
    notes[5] = "The workflow is exactly what the Model Training page runs. Leakage is avoided by fitting every transformer on the training split only."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{ds['rows']:,}", "customers, 21 columns", K.BLUE), ("19", "features: 4 numeric, 15 categorical", K.GREEN), (f"{ds['churn_rate_pct']}%", "churn rate (264 churned, 736 retained)", K.ORANGE), ("Synthetic", "generated by src/sample_data.py, seed 42", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.08, 1.45, 2.88, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("class_balance.png"), 0.6, 2.95, 5.4, 3.9)
    K.text(s, 6.3, 3.0, 6.4, 3.9, [
        ("Same column schema as the public Telco data (customerID, tenure, Contract, MonthlyCharges, Churn ...), but the rows are **generated**: churn comes from a latent logistic score plus noise.", {"bullet": True, "space_after": 8}),
        ("No real operator data were available, so no claim is made about real-world accuracy.", {"bullet": True, "space_after": 8}),
        (f"Stratified 80/20 split: {sp['train_rows']} training and {sp['test_rows']} test rows, **{sp['test_churners']} churners in the test set**; 0 duplicates, 0 missing cells.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[6] = "Be explicit that the data are synthetic, generated with the Telco schema. The base paper uses the real 7,043-row Telco data; the two are not comparable."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing")
    wipe(s)
    rows = [["Step", "What the code does"],
            ["Detect", "target (Churn) and ID (customerID) columns; blank TotalCharges coerced to numbers"],
            ["Clean", "drop exact duplicates; report missing cells"],
            ["Numeric", "median imputation, then StandardScaler (4 columns)"],
            ["Categorical", "most-frequent imputation, then OneHotEncoder(handle_unknown=ignore): 15 columns"],
            ["Result", f"{sp['encoded_feature_count']} model inputs; unseen categories at scoring time are ignored, not fatal"]]
    K.table(s, 0.6, 1.45, [1.5, 5.4], rows, font_size=14, row_h=0.8, first_bold=True)
    K.picture(s, F.fig("churn_by_segment.png"), 7.8, 1.4, 5.0, 3.4)
    K.text(s, 7.8, 4.95, 5.0, 1.8, "Churn rate by contract, tenure, internet service and payment method (all 1,000 rows): month-to-month 34.1% against 12.5% on a two-year contract.", size=13, color=K.TXT, italic=True)
    notes[7] = "Preprocessing is one scikit-learn ColumnTransformer, fitted on the training split. The figure is the exploratory view the Explore page shows."

    # ---- 8 models
    s = S[7]
    set_title(s, "Models compared")
    wipe(s)
    rows = [["Model", "Settings (from src/train_models.py)", "Imbalance handling"],
            ["Logistic Regression", "max_iter 2000", "class_weight balanced"],
            ["Decision Tree", "max_depth 8, min_samples_leaf 10", "class_weight balanced"],
            ["Random Forest", "300 trees, max_depth 12, min_samples_leaf 5", "class_weight balanced"],
            ["Gradient Boosting (optional)", "200 trees, depth 3, learning rate 0.08", "no class_weight option"],
            ["Hist Gradient Boosting (optional)", "max_depth 6, learning rate 0.08", "no class_weight option"]]
    K.table(s, 0.6, 1.5, [3.9, 5.2, 3.03], rows, font_size=15, row_h=0.66, first_bold=True)
    K.text(s, 0.6, 5.7, 12.13, 1.0, "Logistic Regression, Decision Tree and Random Forest are the required three. The two boosted models are optional; because they take no class_weight, \"class weights\" does not rebalance them, and the app says so.", size=15, color=K.TXT, italic=True)
    notes[8] = "Five scikit-learn models behind one registry. Selecting the model on F1 is the default; recall, precision, accuracy and ROC-AUC can be chosen instead."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Split", "stratified, test size 20% (adjustable 10-40%), random_state 42"],
            ["Imbalance", "class_weight=balanced (default) | SMOTE on the training split only | none"],
            ["Selection metric", "F1-score (default); accuracy, precision, recall, ROC-AUC selectable"],
            ["Risk bands", "Low < 30, Medium 30-60, High 60-80, Critical >= 80; editable, validated on the server"],
            ["Batch cut-off", "predicted churn when probability >= 50%"],
            ["Hardware", f"Intel Core i5-12500, CPU only; all five models train in {F.M['app_default_split']['class_weight']['wall_seconds']} s"]]
    K.table(s, 0.6, 1.5, [3.0, 9.13], rows, font_size=16, row_h=0.7, first_bold=True)
    notes[9] = "These are the defaults of the Model Training page. The measured run uses exactly these settings."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 4.1, 5.6)
    K.text(s, 5.0, 1.5, 7.7, 5.3, [
        ("**Validate.** Two classes, enough rows and a target column; otherwise HTTP 422 and nothing is trained.", {"bullet": True, "space_after": 10}),
        ("**Decide.** Probability = predict_proba x 100; the band follows the editable 30 / 60 / 80 thresholds.", {"bullet": True, "space_after": 10}),
        ("**Explain.** Local: coefficient x value (top 5 up, top 5 down). Global: built-in and permutation importance. SHAP is optional and not installed here.", {"bullet": True, "space_after": 10}),
        ("**Act.** Ten IF/THEN rules (contract, tech support, security, charges, e-check, tenure, fibre ...) fire at probability >= 60 or Critical band; two fallbacks cover lower risk.", {"bullet": True, "space_after": 10}),
        ("**Caution.** Scores are rankings, not calibrated probabilities.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[10] = "The rule engine is a set of heuristics written by the team; its business effect has not been measured."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 6.2, 5.5)
    rows = [["Module", "Role"], ["data_loader, eda", "profile, target / ID, EDA charts"], ["preprocessing", "clean, ColumnTransformer, split, SMOTE"], ["train_models, evaluation", "registry, metrics, best model"],
            ["explainability", "importance, local drivers"], ["risk_segmentation, prediction", "bands, scores, batch"], ["retention_engine", "10 rules + 2 fallbacks"], ["persistence", "joblib save / load"]]
    K.table(s, 7.1, 1.4, [2.7, 2.93], rows, font_size=12, row_h=0.6)
    notes[11] = "Level-1 data flow: six processes. Level 0 and level 2 are in the report."

    # ---- 12 data model and UML
    s = S[11]
    set_title(s, "Data model and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 5.8, 4.9)
    K.picture(s, F.diag("06_uml_class_diagram.png"), 6.7, 1.35, 6.0, 4.9)
    K.text(s, 0.6, 6.35, 12.13, 0.6, "There is no SQL database: the ER diagram is the logical data model (CSV, joblib files, in-memory state). The code is function-oriented, so the UML draws modules as classes (full-size diagrams are in the report).", size=13, color=K.TXT, align="c", italic=True)
    notes[12] = "State plainly that there is no database. The logical model shows the entities the code handles; the UML draws modules as classes."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Machine learning", "scikit-learn 1.9.1, imbalanced-learn (SMOTE), pandas 3.0.6, numpy 2.4.6, joblib"],
            ["Explainability", "built-in importance, permutation importance, coefficient x value; SHAP optional (not installed)"],
            ["API", "FastAPI 0.143.3, uvicorn; HMAC-SHA256 bearer token (standard library)"],
            ["Original UI", "Streamlit app (13 pages) over the same core, port 8501"],
            ["Front end", "React 19, Vite 8, React Router, Recharts, Framer Motion (kit V4)"],
            ["Testing", "pytest (44 tests), a 63-check API smoke test, Playwright for screenshots"],
            ["Run", "run.bat creates the virtual environment and starts ports 8314 / 5314 (Python 3.11.9, Windows)"]]
    K.table(s, 0.6, 1.5, [2.8, 9.33], rows, font_size=14, row_h=0.65, first_bold=True)
    notes[13] = "Everything is open source and runs on one machine; run.bat starts the stack."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Data load, profile, EDA, preprocessing", "Done", "src/, 44 pytest tests"],
            ["Five-model training, evaluation, selection", "Done", "scripts/run_experiments.py, metrics.json"],
            ["Risk bands, Customer 360, what-if, retention rules", "Done", "smoke test, 16 screenshots"],
            ["Batch scoring and drift monitoring", "Done", "smoke test (63 checks)"],
            ["FastAPI layer and React interface", "Done", "31 routes, 16 page components"],
            ["SHAP explanations", "Code path only", "shap not installed: fallbacks used, SHAP unmeasured"],
            ["LIME, perturbation explainer, boosted libraries, database", "Not implemented", "out of scope; listed as limits"]]
    K.table(s, 0.6, 1.5, [5.2, 1.9, 5.03], rows, font_size=14, row_h=0.62)
    notes[14] = "State of the code base. The gaps are SHAP (present but unexercised) and the base paper's own explainer."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: 200-row test split")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{lr['f1_score']:.3f}", "F1, Logistic Regression (best)", K.BLUE), (f"{lr['roc_auc']:.3f}", "ROC-AUC, Logistic Regression", K.GREEN),
                                   (f"{lr['recall']:.3f}", "recall: 35 of 53 churners found", K.ORANGE), (f"{lr['precision']:.3f}", "precision (56 false alarms)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.08, 1.45, 2.88, 1.25, v, l, c, vsize=28)
    names = F.MODEL_ORDER
    K.bar_chart(s, 0.6, 2.9, 7.6, 3.95, [F.SHORT[n] for n in names],
                [("Recall", [F.CW[n]["recall"] for n in names]), ("F1", [F.CW[n]["f1_score"] for n in names]), ("ROC-AUC", [F.CW[n]["roc_auc"] for n in names])],
                colors=[K.ORANGE, K.BLUE, K.GREEN], number_format="0.00", font_size=11, max_value=1.0)
    K.card(s, 8.5, 2.95, 4.23, 3.75, "Reading", "80/20 split, seed 42, class weights; 53 churners in the test set, so results move by 0.03-0.10 between splits (see stability). ROC-AUC about 0.72 is moderate, and the data are synthetic.", K.BLUE, "i", body_size=14)
    notes[15] = ("First measured numbers: Logistic Regression F1 0.486, ROC-AUC 0.722, recall 0.660, precision 0.385. Random Forest is within noise (F1 0.472). "
                 "Gradient boosting has the highest accuracy (0.745) but a recall of only 0.283, which is why selection is on F1.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shots = [("04_dashboard.png", "Dashboard"), ("09_risk.png", "Customer risk"), ("10_customer360.png", "Customer 360"),
             ("11_explain.png", "Explainable AI"), ("12_whatif.png", "What-if"), ("13_retention.png", "Retention actions")]
    for i, (f, cap) in enumerate(shots):
        r, c = divmod(i, 3)
        x, y = 0.6 + c * 4.14, 1.3 + r * 2.85
        K.picture(s, F.shot(f), x, y, 3.95, 2.45, border=True)
        K.text(s, x, y + 2.48, 3.95, 0.3, cap, size=12, color=K.TXT, align="c")
    notes[16] = "Real screenshots from the running ChurnIQ application with 1,000 sample customers and three trained models."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([("44", "pytest tests passed (venv and system Python)", K.GREEN), ("63", "live API smoke-test checks passed", K.BLUE), ("16", "screens captured, console clean", K.ORANGE), ("360-1440 px", "light and dark, no horizontal overflow", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.08, 1.45, 2.88, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["A 200-row test split with 53 churners gives noisy metrics", "Added 5-fold cross-validation and five random splits"],
            ["Accuracy looks fine without imbalance handling (0.745) while recall collapses (0.189)", "Selection on F1 and class weights by default"],
            ["Tests showed pandas 3 string columns slip past dtype == object checks", "Fixed in data_loader.py with a helper; regression tests added"]]
    K.table(s, 0.6, 3.1, [6.4, 5.73], rows, font_size=14, row_h=0.85)
    notes[17] = "The tests run offline with the real code. The observations drove three changes. No load test, penetration test or user study has been done."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No real operator data available", "Synthetic sample with the Telco schema; every document states it"],
            ["SHAP is not installed", "Built-in importance, permutation importance and coefficient x value; SHAP not claimed"],
            ["Random Forest differs between scikit-learn versions on 200 rows (accuracy 0.665 vs 0.720)", "Environment of record fixed (scikit-learn 1.9.1); both runs archived"],
            ["pandas 3 string dtype broke type detection", "Found by unit tests; fixed and covered by regression tests"],
            ["Requests via localhost take an extra ~2 s on Windows (IPv6 tried first)", "Measured against 127.0.0.1; documented as a quirk"],
            ["Tiny test set", "Cross-validation and seed spread reported beside the single split"]]
    K.table(s, 0.6, 1.5, [6.2, 5.93], rows, font_size=14, row_h=0.72)
    notes[18] = "Each challenge was met with a concrete change in code or in how results are reported."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Evaluate", "Finish the stability study, the imbalance comparison, threshold and calibration analysis.", K.BLUE, "1"),
        ("Compare", "Set the results against the base paper, stating where data and protocol differ.", K.GREEN, "2"),
        ("Document", "Final report, paper and deck with every figure regenerated from JSON.", K.ORANGE, "3"),
        ("Extend (future)", "Real operator data, SHAP and perturbation explainers, calibration, measured campaign effect.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.08, 1.6, 2.88, 4.4, t, b_, col, gl, body_size=19)
    notes[19] = "Plan to the final review. The extensions at the right are out of scope for this submission."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why synthetic data; why Logistic Regression is best here; why no SHAP numbers; why no database."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
