"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, prepare, scan_deck, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    X, DS, PERF, REC = F.R, F.DS, F.PERF, F.REC

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: calibrated XGBoost with kNN refinement behind a FastAPI service and a React interface",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how the system is designed and built: the data and model, what is implemented, the first measured results and the open items."

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
        ("Problem", "Placement cells hold student records but do no prediction: students get no early signal, shortlisting is manual, and nobody tells a student which skill or which company to aim for.", K.ORANGE, "!"),
        ("Proposed system", "For a student, company and role: build 24 features, estimate the placement probability with calibrated XGBoost (kNN refines borderline cases), explain the gaps, and recommend higher-probability company-role pairs.", K.BLUE, "i"),
        ("Base papers", "Declared base [1] predicts placement with LR, RF and boosting but reports no numbers. The method we adapt is the hybrid XGBoost + kNN framework of [2], built for admissions on real data.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.7, t, b_, col, gl, body_size=17)
    notes[3] = "One-minute recap of Review 1: the placement-cell gap, our adaptation of the hybrid model, and how the two base papers relate."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.6, 5.5)
    K.text(s, 8.5, 1.5, 4.2, 5.2, [
        ("**Layers**", {"space_after": 8}),
        ("Presentation: React 19 app (port 5405) and the original Flask pages (port 5000).", {"bullet": True}),
        ("Application: FastAPI (port 8405), 9 endpoints, Pydantic validation, CORS for the front end only.", {"bullet": True}),
        ("Core: src/ modules (features, training, prediction, recommendation) shared by both interfaces.", {"bullet": True}),
        ("Storage: CSV data and pickled models; no SQL database.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "The FastAPI layer imports the original src.recommend functions, so Flask and React use exactly the same models."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Generate 3,000 students", K.NAVY), ("24 features", K.NAVY), ("70/15/15 split", K.GREEN), ("6 baselines", K.PURPLE),
                                      ("Platt calibration", K.ORANGE), ("kNN / SVM residual", K.BLUE), ("Models + metrics.json", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One feature function", "Training, the API and the recommender all call the same build_features, so there is no train/serve mismatch."),
                                 ("Stratified split", f"Placed ratio kept in every part: {F.TRAIN_N:,} train / {F.VAL_N} validation / {F.TEST_N} test, seed 42; test used once."),
                                 ("Reproducible", "src/ scripts regenerate data, models and plots; scripts/run_experiments.py adds the extra measurements.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 2.9)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.85, 3.4, 2.0, b_, size=17, color=K.TXT)
    notes[5] = "The training scripts are three commands. The experiments script re-derives confusion matrices, a five-seed study and a label-free hybrid check."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset (synthetic)")
    wipe(s)
    for i, (v, l, c) in enumerate([("3,000", "synthetic students, 19 columns", K.BLUE), ("30", "companies: 7 Tier-1, 15 Tier-2, 8 Tier-3", K.GREEN),
                                   (F.pct(DS["placed_rate"]), "placed (1,791 / 3,000)", K.ORANGE), ("2,100 / 450 / 450", "train / validation / test", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=19 if i == 3 else 28, lsize=12)
    bt = DS["by_tier"]
    K.bar_chart(s, 0.6, 2.95, 5.6, 3.9, ["Tier 1 (324)", "Tier 2 (1,320)", "Tier 3 (1,356)"], [("Placed rate by target tier", [bt["1"]["mean"], bt["2"]["mean"], bt["3"]["mean"]])],
                colors=[K.BLUE], number_format="0.0%", font_size=12, max_value=1.0)
    K.text(s, 6.5, 3.0, 6.2, 3.9, [
        ("**No real student data.** Records come from src/generate_dataset.py (seed 42): scores follow CGPA with noise; the label is drawn from a logistic score of cutoff gaps, internships, projects, backlogs and tier.", {"bullet": True, "size": 14}),
        ("The 30-company table (cutoffs, packages 4.0 to 28.0 LPA, hiring rates) is invented but plausible.", {"bullet": True, "size": 14}),
        ("No missing values; classes 59.7 / 40.3, so no resampling was applied.", {"bullet": True, "size": 14}),
        ("Because the labels follow a logistic rule, even Logistic Regression scores well; results are not claims about real placements.", {"bullet": True, "size": 14}),
    ], size=14, color=K.INK)
    notes[6] = "Be upfront: the dataset is synthetic because real placement records are private. Placed rate by tier is strongly structured (9.6%, 49.5%, 81.6%), which is how the generator was built."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing and features")
    wipe(s)
    K.picture(s, F.diag("11_training_pipeline.png"), 0.6, 1.4, 6.6, 3.6)
    K.text(s, 7.5, 1.45, 5.2, 5.3, [
        ("1  Frequency-encode 5 categoricals (branch, company, role, degree, student type)", {}),
        ("2  Z-score 13 numeric columns", {}),
        ("3  Add 6 engineered columns: skill index, company hiring rate, CGPA x tier, CGPA / aptitude / technical gap to the company's cutoffs", {}),
        ("= 24 features. Maps and scaler are fitted on the training split only and saved in preprocess.pkl.", {"italic": True, "size": 14, "color": K.TXT}),
    ], size=16, color=K.INK, space_after=9)
    K.text(s, 0.6, 5.25, 6.6, 1.5, "Gap features carry the placement logic: SHAP ranks CGPA gap, backlogs, technical gap, aptitude gap and CGPA x tier highest.", size=14, color=K.TXT)
    notes[7] = "Frequency encoding avoids sparse one-hot columns for company and role. The gap features compare the student against the chosen company's cutoffs."

    # ---- 8 model architecture
    s = S[7]
    set_title(s, "Model design")
    wipe(s)
    rows = [["Component", "Configuration"], ["Baselines", "Logistic Regression, Decision Tree, Random Forest (200), SVM (RBF), kNN (k = 9)"],
            ["XGBoost", "100 trees, depth 8, learning rate 0.1, subsample 0.8, colsample 0.8, L1 0.1, L2 1.0"],
            ["Calibration", "Platt scaling: CalibratedClassifierCV(sigmoid, cv = 3)"],
            ["Residual set R", "calibrated prediction wrong OR probability in [0.4, 0.6] (base paper Eq. 1)"],
            ["Local models", "kNN (k = 9) and SVM (RBF) fitted on all training rows, applied to R only"],
            ["Serving rule", "p = XGBoost; if 0.4 <= p <= 0.6 then p = 0.5 p + 0.5 kNN; ready if p >= 0.5"]]
    K.table(s, 0.6, 1.4, [2.3, 6.6], rows, font_size=13, row_h=0.72, first_bold=True)
    K.tile(s, 9.9, 1.4, 2.83, 1.45, "24", "input features", K.BLUE, vsize=26)
    K.tile(s, 9.9, 3.0, 2.83, 1.45, "1.49 MB", "calibrated XGBoost file", K.GREEN, vsize=24)
    K.tile(s, 9.9, 4.6, 2.83, 1.45, "CPU only", "about 3 s to retrain", K.ORANGE, vsize=24)
    notes[8] = "The residual set in the paper uses the true labels. The served model cannot, so predict_for refines only the borderline band; the label-free effect is measured later."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Split", "stratified 70 / 15 / 15, seed 42 (2,100 / 450 / 450)"],
            ["Cross-validation", f"9-fold on the training split for XGBoost: accuracy {F.CV9:.4f}"],
            ["Calibration quality", f"Brier score {F.BRIER:.4f} after Platt scaling (raw XGBoost {F.CAL['brier_raw_xgb']:.4f})"],
            ["Residual rate", f"{F.pct(F.RESIDUAL_RATE)} of test rows with the label-based rule; {F.pct(F.EXP['seed42']['borderline_rate'])} borderline only"],
            ["Hardware", f"{F.ENV['cpu']}, {F.ENV['ram']}, no GPU; Python {F.ENV['python']}, scikit-learn {F.ENV['sklearn']}, XGBoost {F.ENV['xgboost']}"]]
    K.table(s, 0.6, 1.4, [3.0, 9.13], rows, font_size=14, row_h=0.55, first_bold=True)
    K.picture(s, F.fig("calibration.png"), 0.6, 4.85, 3.0, 2.05)
    K.text(s, 3.9, 4.95, 8.8, 1.9, "Platt scaling improves Brier only slightly (0.1379 to 0.1352) and Logistic Regression is better calibrated (0.1180): calibration is needed for ranking recommendations, but it is not a large gain here. Mean predicted probability on test is 0.592 against an observed rate of 0.596.", size=14, color=K.TXT)
    notes[9] = "All hyper-parameters are the base paper's. We did not tune them further."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 5.2, 5.6)
    K.text(s, 6.2, 1.5, 6.5, 5.3, [
        ("**Calibrated probability.** XGBoost output after Platt scaling.", {"bullet": True, "space_after": 10}),
        ("**Borderline refinement.** If p is between 0.4 and 0.6, blend with the kNN probability (0.5 / 0.5).", {"bullet": True, "space_after": 10}),
        ("**Decision.** Placement ready if p >= 0.5, otherwise needs improvement with skill-gap tips.", {"bullet": True, "space_after": 10}),
        ("**Tips.** Rules on the company cutoffs: CGPA, aptitude, technical, internship.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[10] = "This is predict_for in src/recommend.py. The recommendation algorithm calls it for every feasible company and role."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 6.2, 5.6)
    rows = [["Module", "Role"], ["generate_dataset.py", "synthetic students, 30 companies"], ["preprocess.py", "encode, scale, gap features"], ["hybrid_model.py", "train, calibrate, hybrid, plots"],
            ["recommend.py", "predict_for, recommend"], ["backend/main.py", "9 FastAPI routes"], ["app.py + templates/", "original Flask pages"], ["frontend/src", "React pages and charts"]]
    K.table(s, 7.1, 1.5, [2.6, 3.03], rows, font_size=12, row_h=0.55)
    notes[11] = "Level-1 data flow. The src/ modules are the original code; the backend and the React front end are the new layers."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.0, 5.1)
    K.picture(s, F.diag("06_class_diagram.png"), 6.8, 1.35, 5.9, 5.1)
    K.text(s, 0.6, 6.55, 12.13, 0.4, "There is no SQL database: students and companies are CSV files, models are pickles and metrics are JSON. The ER diagram shows these stores; the class diagram shows the Pydantic models and the modules.", size=12, color=K.TXT, align="c", italic=True)
    notes[12] = "The batch description mentions MySQL; the implementation uses files. The ER diagram models the logical entities."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    E = F.ENV
    rows = [["Layer", "Technology"], ["Machine learning", f"scikit-learn {E['sklearn']}, XGBoost {E['xgboost']}, SHAP {E['shap']}, pandas {E['pandas']}, NumPy {E['numpy']}"],
            ["Plots", "matplotlib (PCA, probability histogram, SHAP bars)"], ["API", f"FastAPI {E['fastapi']}, Uvicorn {E['uvicorn']}, Pydantic {E['pydantic']} (port 8405)"],
            ["Original UI", f"Flask {E['flask']}, Jinja templates (port 5000)"],
            ["Front end", f"React {E['react']}, Vite {E['vite']}, Tailwind {E['tailwind']}, Recharts, three.js, framer-motion (port 5405)"],
            ["Testing", "46 scripted checks, smoke test, Playwright for screenshots"]]
    K.table(s, 0.6, 1.5, [3.0, 9.13], rows, font_size=15, row_h=0.62, first_bold=True)
    notes[13] = f"Python {E['python']} on Windows 11. run.bat creates the virtual environment, installs packages, trains if needed and starts both servers."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Dataset generator, features, training, calibration, hybrid", "Done", "src/, models/metrics.json"],
            ["Prediction with skill-gap tips; company-role recommendation", "Done", "src/recommend.py, 46 checks pass"],
            ["FastAPI service (9 endpoints)", "Done", "smoke test 15 / 15"],
            ["React interface (6 pages, command palette)", "Done", "10 screenshots"],
            ["Officer dashboard and recruiter shortlist", "Done", "metrics, SHAP, PCA, 1,394-match filter"],
            ["Real placement data, login, database, PDF / e-mail reports", "Not done", "stated limitations"],
            ["Recommendation speed", "Weak", "3 to 8 s per request (pickles reloaded)"]]
    K.table(s, 0.6, 1.5, [5.6, 1.4, 5.13], rows, font_size=14, row_h=0.62)
    notes[14] = "State of the code base. The honest gaps: no real data, no authentication or database, slow recommendations."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: held-out test split")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{X['xgb_calibrated']['accuracy']:.4f}", "XGBoost + Platt accuracy", K.BLUE), (f"{X['hybrid_xgb_knn']['accuracy']:.4f}", "hybrid, true labels used", K.ORANGE),
                                   (f"{X['hybrid_knn_labelfree']['accuracy']:.4f}", "hybrid, label-free", K.GREEN), (f"{X['logreg']['roc_auc']:.4f}", "Logistic Regression AUC (best)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=28)
    K.picture(s, F.fig("model_comparison.png"), 0.6, 2.95, 7.6, 3.9)
    K.card(s, 8.5, 2.95, 4.23, 3.8, "Reading", "450 test students, seed 42. The hybrid's 0.84 relies on the true labels to choose the refined rows; without them it is 0.8089 vs 0.8067 for XGBoost + Platt: one student. Logistic Regression has the highest AUC (0.9106).", K.BLUE, "i", body_size=14)
    notes[15] = "Numbers are models/metrics.json for the shipped pickles (reproduced exactly) plus the label-free variant measured by scripts/run_experiments.py."

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, F.shot("02_predict.png"), 0.6, 1.3, 7.4, 4.65, border=True)
    K.picture(s, F.shot("03_recommend.png"), 8.3, 1.3, 4.43, 2.77, border=True)
    K.picture(s, F.shot("04_dashboard.png"), 8.3, 4.2, 4.43, 2.77, border=True)
    K.text(s, 0.6, 6.05, 7.4, 0.9, "Eligibility: Microsoft SDE for a CGPA 8.4 student, 22.2% (technical 79 below the 82 cutoff). Right: recommendations (base 10.8% at Google) and the officer dashboard. Real application, 3,000-student dataset.", size=12, color=K.TXT)
    notes[16] = "Real screenshots from the running application captured with Playwright; nothing is mocked."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.TEST_SUMMARY['passed']} / {F.TEST_SUMMARY['total']}", "scripted checks passed", K.GREEN), (f"{F.SMOKE_TOTAL} / {F.SMOKE_TOTAL}", "smoke-test checks", K.BLUE),
                                   (f"{PERF['POST /api/predict']['mean_ms']:.0f} ms", "mean POST /api/predict", K.ORANGE), (f"{PERF['POST /api/recommend']['mean_ms'] / 1000:.1f} s", "mean POST /api/recommend", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["The hybrid's gain depends on the true labels; the label-free rule gains one student of 450", "Report both; recommend the label-free number as the deployable one"],
            ["Unknown branch or role values are accepted (frequency 0)", "Documented as a validation gap"],
            ["Role-only list is empty when the target company fails the feasibility filter", "Documented; hybrid and company-only lists still work"]]
    K.table(s, 0.6, 3.05, [6.0, 6.13], rows, font_size=14, row_h=0.8)
    notes[17] = "46 checks: 10 unit, 8 integration, 6 functional, 13 validation, 9 security. Timings on 127.0.0.1."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No real placement records are available", "Synthetic generator with a stated logistic rule; limitation reported"],
            ["The paper's residual rule uses true labels", "Added a label-free variant and a five-seed study"],
            ["The pickled company table needs pyarrow with pandas 3", "pyarrow added to requirements.txt"],
            ["Recommendation reloads four pickle files for every call", "Measured 3 to 8 s; caching listed as future work"],
            ["Python clients to localhost add about 2 s here", "Latency measured on 127.0.0.1"]]
    K.table(s, 0.6, 1.5, [5.6, 6.53], rows, font_size=15, row_h=0.85)
    notes[18] = "Each challenge led to a concrete change in the code base or in how results are reported."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Evaluate", "Re-run on real, anonymised placement records if the cell can share them; keep the split free of leakage.", K.BLUE, "1"),
        ("Speed up", "Cache the model files once per process so a recommendation takes well under a second.", K.GREEN, "2"),
        ("Harden", "Validate categories, add login and roles, store data in a database.", K.ORANGE, "3"),
        ("Extend", "Batch CSV prediction, PDF reports and per-student SHAP explanations.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.1, 1.6, 2.9, 4.4, t, b_, col, gl, body_size=16)
    notes[19] = "Plan to the final review and beyond; the first item depends on data access."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why synthetic data; why the hybrid gain disappears without labels; how recommendations are validated (they are not, yet)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "Placement")
    return out_path


if __name__ == "__main__":
    p = build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx"))
    print(p, scan_deck(p))
