"""Chapter 3 (feasibility study) and Chapter 4 (system requirements and analysis)."""

import csv
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB


def _c(*keys):
    from .refs import NUM

    return "[" + ", ".join(str(NUM[k]) for k in keys) + "]"


def _fit_total_s():
    return sum(F.X[d]["timing"][m]["fit_s"] for d in F.DISEASES for m in F.MODEL_ORDER)


def _lat(key):
    return F.API["latency"][key]


def feasibility_blocks():
    X = F.X
    fit_total = _fit_total_s()
    p_d, p_h = _lat("POST /api/predict/diabetes"), _lat("POST /api/predict/heart")
    conc = _lat("POST /api/predict/diabetes (4 concurrent clients)")
    row_ms = max(X[d]["timing"][m]["predict_ms_per_row"] for d in F.DISEASES for m in F.MODEL_ORDER)
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the proposed system can be built and used with the resources at hand. The aspects below are assessed with measurements from this project wherever a measurement exists "
          "and are described qualitatively where one does not; no monetary figure is invented."),
        H2("3.1 Technical Feasibility"),
        P("Every component is available as free, open-source software and runs on an ordinary desktop. The measurements in the table below were taken on a single machine without a graphics processor "
          "(Intel Core i5-12500, 12 threads, 16 GB RAM, Windows 11, Python 3.11.9, scikit-learn 1.8.0)."),
        TAB("Technical feasibility: measured evidence", ["Question", "Measurement"],
            [["Can all 16 models be trained on a desktop CPU?",
              f"Yes. Fitting all 16 (four algorithms for each of four conditions, 1,600 training rows each) took {fit_total:.1f} s in total in the experiment script; the largest single fit was a Random Forest of about 0.6 s"],
             ["Is single-record inference fast?", f"Yes. In-process prediction takes at most {row_ms:.3f} ms per row for any of the 16 models (batch of 400 rows)"],
             ["Is the API fast enough for a web interface?",
              f"Yes. Over 127.0.0.1 a prediction request had a median of {p_d['p50_ms']:.1f} ms (diabetes) and {p_h['p50_ms']:.1f} ms (heart), 95th percentile about {p_d['p95_ms']:.0f} ms; four concurrent clients sustained {conc['throughput_rps']:.0f} requests per second. "
              "These timings were taken while the PC was under memory pressure and Windows timer resolution (about 15.6 ms) quantises single calls, so they are upper bounds"],
             ["Is the software stack mature?", "Python 3.11, scikit-learn, pandas, NumPy, Flask, FastAPI, React 19 and Vite 8 are widely used and documented"],
             ["Can the system be tested?", f"Yes. A {F.SMOKE_CHECKS}-line smoke test and a {F.API_CHECKS[1]}-check API test script exist and passed ({F.API_CHECKS[0]} of {F.API_CHECKS[1]}); there is no pytest suite or frontend unit test"]],
            widths=[2.2, 3.8], size=10),
        P("The only technical difficulty met during the work was environmental: the saved models were written with scikit-learn 1.8.0 and fail on an older release when `predict_proba` is called, so `requirements.txt` pins the version."),
        H2("3.2 Economic Feasibility"),
        P("The software cost is zero: no commercial licence, cloud service or paid API is used, and every prediction is made by a small local model. The only hardware needed is a computer that can run Python and a web browser; "
          "the development machine was an ordinary desktop. Operating cost is limited to the time of the person who uses the application."),
        P("The benefit side, in a real deployment, would be earlier detection and fewer unnecessary specialist referrals. This project has no clinical, cost or referral data, so it does **not** estimate any monetary saving "
          "and makes no claim about health outcomes. Whether a screening tool of this kind is worth deploying depends on its performance on real patients, which this project could measure only partly (the supplementary check in Chapter 8), "
          "and on the cost of follow-up for false alarms, which is clinic-specific."),
        H2("3.3 Operational Feasibility"),
        B("**Usability.** The interface needs no programming. A user picks a condition, fills a form whose labels carry units and an example value, and presses one button; empty or non-numeric fields are marked \"Required.\" or \"Enter a number.\", and a value outside the training range of that field is flagged with a warning.",
          "**Skills.** A person who can read a laboratory report can use every page. The result is a risk class and a percentage, with a standing notice that it is not a diagnosis.",
          "**Deployment.** One script (`run.bat`) creates the virtual environment, installs the pinned packages and starts the API (port 8303) and the web interface (port 5303). The original Flask pages start with one command on port 5000.",
          "**Data handling.** Nothing is stored: values typed into the form are sent to the API, scored and discarded. The models and the training data are plain files in the project folder."),
        H2("3.4 Schedule Feasibility"),
        P("The work was organised in phases that depend on one another. The table lists them in order; calendar dates are not given because the batch records do not include a dated plan."),
        TAB("Project phases", ["Phase", "Activity", "Output"],
            [["1", "Problem definition, base paper study, literature survey", "Abstract, objectives, survey"],
             ["2", "Data generation and a common preprocessing step", "Four CSV files, scaler per condition"],
             ["3", "Training and comparison of four algorithms per condition", "16 models, `training_report.json`, saved best models"],
             ["4", "Flask prediction pages", "Original working application"],
             ["5", "FastAPI layer and React interface", "Seven API routes, landing, overview, prediction, models, datasets and about pages"],
             ["6", "Testing, extra experiments, real-data check and documentation", "API tests, metrics, screens, report, decks, paper"]],
            widths=[0.7, 3.4, 1.9], align=["c", "l", "l"], size=10),
        H2("3.5 Legal, Ethical and Data-Protection Feasibility"),
        P("The data used in this project are synthetic and contain no personal information, so no consent or anonymisation was needed. The real public data sets used in the supplementary check "
          f"(Pima diabetes {_c('pima')}, UCI Cleveland {_c('cleveland')}, ILPD {_c('ilpd')} and chronic kidney disease {_c('ckd')}) are published for research use; the UCI sets are distributed under the CC BY 4.0 licence. "
          "In real use, patient values are personal health data: processing them needs a lawful basis, access control and retention limits under the rules that apply to the health provider. "
          "The application stores nothing, but it has no authentication, so it must not be exposed to real patients in its present form."),
        P("There is also an ethical point about the output. A risk class is a ranking produced by a model trained on synthetic data and can be wrong; the application therefore carries the notice "
          "\"Machine-learning estimate for education and demonstration only. It is not a medical diagnosis; consult a qualified healthcare provider.\" on every result."),
        H2("3.6 Risk Analysis"),
        TAB("Project risks and mitigation", ["Risk", "Effect", "Mitigation in this project"],
            [["No real patient data in the shipped pipeline", "Reported accuracy is not clinical accuracy", "Synthetic data declared in the README, on the Datasets page and in every document; a supplementary real-data check measures the gap"],
             ["Label noise and a known generating rule", "Accuracy is capped near 92% and favours linear models", "The ceiling is stated; Logistic Regression is reported as best where it is, instead of promoting ensembles"],
             ["Selection on the test set and one split", "Optimistic metrics; diabetes model (SVM) not supported by cross-validation", "5-fold cross-validation and ten random splits reported beside the headline figures"],
             ["Models do not transfer to real records", "Liver accuracy 54.0% is below the 71.4% majority baseline on real ILPD data", "Reported plainly; the application carries a not-a-diagnosis notice"],
             ["No range validation in the API", "Impossible values (for example glucose 100,000) are scored", "UI warns outside the training range; listed as a limitation and as future work"],
             ["Library version differences", "Saved models fail on older scikit-learn", "Versions pinned in `requirements.txt`; stated in the how-to-run guide"],
             ["No authentication or persistence", "Unsuitable for real patient data", "Documented limitation; nothing is stored"]],
            widths=[1.6, 1.8, 2.6], size=9.5),
        H2("3.7 Advantages and Constraints"),
        P("The feasibility findings can be summarised as a list of what the design gains and what it has to live with."),
        B("**Advantages.** No licence or cloud cost; a complete training run takes seconds on a desktop CPU, so models can be regenerated at will; one interface covers four conditions; the code is small enough (a few hundred lines of Python for training and API) for a student team to read in full; "
          "every number in the documents is produced by a script and can be reproduced.",
          "**Constraints.** The shipped models depend on one scikit-learn version; the data are synthetic; the interface and API trust the user to enter values in the right units; there is no authentication, persistence or audit log; "
          "and the evaluation is limited to a single hold-out split plus the extra experiments described in Chapter 8, with no clinical validation."),
        P("None of the constraints prevents the system from being built or demonstrated; each of them would have to be removed before any use with patients, and Chapter 10 lists the steps."),
        H2("3.8 Conclusion of the Feasibility Study"),
        P("The system is technically feasible (measured), feasible in terms of cost (no licences, ordinary hardware) and operationally feasible for a non-programmer. "
          "It is acceptable from a legal and ethical point of view only as a demonstration on synthetic or properly governed data. Its main risk is not the build but the evidence: the headline metrics come from synthetic data, "
          "and must be re-measured on real, clinically validated data before any decision about patients rests on them."),
    ]


# labels as shown on the forms (app.py FIELD_META) -> used in the data-requirements tables
LABELS = {
    "diabetes": [("Pregnancies", "Number of pregnancies"), ("Glucose", "Glucose level (mg/dL)"), ("BloodPressure", "Blood pressure (mm Hg)"), ("SkinThickness", "Skin thickness (mm)"),
                 ("Insulin", "Insulin level (mu U/ml)"), ("BMI", "Body mass index"), ("DiabetesPedigreeFunction", "Diabetes pedigree function"), ("Age", "Age in years")],
    "heart": [("age", "Age in years"), ("sex", "Sex (1 = male, 0 = female)"), ("cp", "Chest pain type (0-3)"), ("trestbps", "Resting blood pressure (mm Hg)"), ("chol", "Serum cholesterol (mg/dl)"),
              ("fbs", "Fasting blood sugar > 120 mg/dl (1 = yes)"), ("restecg", "Resting ECG result (0-2)"), ("thalach", "Maximum heart rate achieved"), ("exang", "Exercise-induced angina (1 = yes)"),
              ("oldpeak", "ST depression"), ("slope", "Slope of the ST segment (0-2)"), ("ca", "Number of major vessels (0-3)"), ("thal", "Thalassaemia code (0-2)")],
    "liver": [("Age", "Age in years"), ("Gender", "Gender (1 = male, 0 = female)"), ("Total_Bilirubin", "Total bilirubin"), ("Direct_Bilirubin", "Direct bilirubin"),
              ("Alkaline_Phosphotase", "Alkaline phosphatase"), ("Alamine_Aminotransferase", "Alanine aminotransferase (ALT)"), ("Aspartate_Aminotransferase", "Aspartate aminotransferase (AST)"),
              ("Total_Protiens", "Total proteins"), ("Albumin", "Albumin"), ("Albumin_and_Globulin_Ratio", "Albumin and globulin ratio")],
    "kidney": [("age", "Age in years"), ("blood_pressure", "Blood pressure (mm Hg)"), ("specific_gravity", "Urine specific gravity"), ("albumin", "Albumin in urine (0-4)"), ("sugar", "Sugar in urine (0-4)"),
               ("blood_glucose_random", "Random blood glucose"), ("blood_urea", "Blood urea"), ("serum_creatinine", "Serum creatinine"), ("sodium", "Sodium"), ("potassium", "Potassium"),
               ("hemoglobin", "Haemoglobin"), ("packed_cell_volume", "Packed cell volume")],
}


def _ranges(d):
    """min / max of every column of data/<d>.csv (read at build time)."""
    path = os.path.join(F.CODE, "data", f"{d}.csv")
    cols, lo, hi = None, {}, {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                x = float(v)
                lo[k] = x if k not in lo else min(lo[k], x)
                hi[k] = x if k not in hi else max(hi[k], x)
    return lo, hi


def _g(x):
    return str(int(x)) if float(x).is_integer() else f"{x:.2f}".rstrip("0").rstrip(".")


def analysis_blocks():
    X = F.X
    data_rows = []
    for d in F.DISEASES:
        lo, hi = _ranges(d)
        for i, (k, lab) in enumerate(LABELS[d]):
            data_rows.append([F.NAME[d] if i == 0 else "", f"`{k}`", lab, f"{_g(lo[k])} to {_g(hi[k])}"])
    p_d = _lat("POST /api/predict/diabetes")
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System and its Limitations"),
        P("In current practice a person's risk for these conditions is assessed in one of three ways. The first is clinical: a clinician reads laboratory values against reference ranges and decides what to do. "
          "This is the reference standard, but it needs a clinician for every report, and in the project's problem statement (Section 1.3) rural and semi-urban health centres often lack one. "
          "The second is a printed or online risk calculator for a single condition, which asks for a handful of values and returns a score. The third is a research prototype of a machine-learning model, "
          f"typically for one disease and one data set, as the surveyed papers show (Chapter 2, {_c('base')}, {_c('bangla')})."),
        TAB("Limitations of the existing approaches", ["Approach", "Limitation"],
            [["Manual reading of reports", "Depends on specialist availability; combinations of mildly abnormal values are easy to miss; no consistent, repeatable score"],
             ["Single-condition calculators and prototypes", "One tool per disease, each with its own inputs and interface; none reusable across conditions"],
             ["Published ML studies", "Usually one disease, one data set and a results table; rarely packaged as an application a non-programmer can run"],
             ["Opaque scores", "A class or percentage without the reasons behind it gives the user nothing to check against clinical judgement"]],
            widths=[2.0, 4.0], size=10),
        H2("4.2 Proposed System and its Advantages"),
        P(f"The proposed system, the {F.PRODUCT}, replaces the separate tools with one application. It holds a trained model for each of four conditions, applies the same preprocessing and evaluation to all of them, "
          "and serves them through one API and one interface. The architecture is described in Chapter 5 and the methodology in Chapter 6."),
        TAB("Existing approaches compared with the proposed system", ["Aspect", "Existing", "Proposed"],
            [["Conditions covered", "One per tool", "Four (diabetes, heart, liver, kidney) in one application"],
             ["Algorithms", "Usually one chosen in advance", "Logistic Regression, Decision Tree, Random Forest and SVM compared for every condition; best by F1 served"],
             ["Inputs", "Different for every tool", "Routine laboratory and examination values (8, 13, 10 and 12 fields), with units, examples and training ranges shown"],
             ["Output", "A score or a label", "Risk class, confidence, model used, that model's hold-out accuracy, and a not-a-diagnosis notice"],
             ["Reproducibility", "Rarely scripted", "Scripts regenerate the data, models, metrics, diagrams and screens"],
             ["Transparency about data", "Often not stated", "Datasets page and README state that the data are synthetic"]],
            widths=[1.5, 1.8, 2.7], size=9.5),
        P("The advantages are therefore convenience (one place for four conditions), comparability (the same protocol everywhere), speed (a prediction returns in tens of milliseconds) and honesty about what the numbers mean. "
          "It is not an advantage in clinical accuracy: that has not been established."),
        H2("4.3 Functional Requirements"),
        P("The functional requirements were derived from the objectives (Section 1.4) and from the way a user of a screening tool works. Each requirement is implemented by a page of the interface and one or more API routes."),
        TAB("Functional requirements", ["ID", "Requirement", "Implemented by"],
            [["FR1", "Let the user choose one of four conditions", "Prediction page tabs; `/app/predict/:disease`"],
             ["FR2", "Show a form with the clinical fields of the chosen condition, with labels, units, example values and training ranges", "`GET /api/diseases/{d}`"],
             ["FR3", "Pre-fill the form with a real record of the data set, positive or negative", "\"Positive sample\" and \"Negative sample\" buttons; `GET /api/diseases/{d}/sample`"],
             ["FR4", "Validate the input: required, numeric, with a warning outside the training range", "Form validation in `Predict.jsx`; HTTP 422 with a message from `POST /api/predict/{d}`"],
             ["FR5", "Predict the risk class and show the confidence, the model used and its hold-out accuracy", "`POST /api/predict/{d}`; result card"],
             ["FR6", "Show a not-a-diagnosis notice with every result", "Result card text"],
             ["FR7", "Compare the four algorithms for each condition on accuracy, precision, recall and F1, and mark the selected one", "Models page; `GET /api/diseases/{d}`, `GET /api/report`"],
             ["FR8", "Show the datasets: rows, class balance, feature list and the synthetic-data warning", "Datasets page; `GET /api/datasets`"],
             ["FR9", "Report an unknown condition with HTTP 404 and an unknown route with a not-found page", "`_check()` in `backend/main.py`; 404 page"],
             ["FR10", "Regenerate the data and retrain the models from scripts", "`generate_data.py`, `train_models.py`"],
             ["FR11", "Keep the original Flask prediction pages working on the same saved models", "`app.py`"]],
            widths=[0.5, 3.4, 2.1], align=["c", "l", "l"], size=9.5),
        P("Features that the abstract or the objectives mention but that are **not** implemented are deliberately absent from this table: per-prediction explanations (objective 6), health recommendations, "
          "imputation of missing values, feature selection and user accounts. They are listed as limitations in Chapter 9 and as future work in Chapter 10."),
        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and how they are met", ["Quality", "Requirement", "Evidence"],
            [["Performance", "Interactive response on a desktop", f"Prediction requests had a median of {p_d['p50_ms']:.1f} ms over 127.0.0.1 and a 95th percentile of about {p_d['p95_ms']:.0f} ms (upper bounds; see Chapter 7)"],
             ["Usability", "Usable without programming; clear errors", "Labelled fields with units and examples, \"Required.\" / \"Enter a number.\" messages, out-of-range warning, dark and light themes, layout checked at 1440 px and 390 px"],
             ["Reliability", "Invalid input never crashes the service", f"Missing, non-numeric, NaN, infinite and null values return HTTP 422; unknown disease 404; {F.API_CHECKS[0]} of {F.API_CHECKS[1]} API checks passed"],
             ["Security", "Basic protection of the service", "CORS limited to `localhost:5303` and `127.0.0.1:5303`; no data stored. There is no authentication, so the service is not suitable for real patient data"],
             ["Portability", "Runs on Windows and any system with Python 3.11", "`requirements.txt` with pinned versions; `run.bat`; no GPU or external service"],
             ["Maintainability", "Prediction logic separate from the interface", "`backend/main.py` imports the models and field metadata from `app.py` instead of copying them; training is a separate script"],
             ["Reproducibility", "Same numbers on re-run", "Fixed seed 42 in data generation, split and models; experiment scripts write JSON files that the documents read"]],
            widths=[1.1, 2.0, 2.9], size=9.5),
        H2("4.5 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum (estimate)", "Used in this project"],
            [["Processor", "Dual-core 2 GHz", "Intel Core i5-12500 (6 cores, 12 threads)"],
             ["Memory", "4 GB", "16 GB"],
             ["Storage", "1 GB free (Python environment, node packages, data, models)", "SSD"],
             ["Graphics", "Not required", "Not used (CPU only; the landing page uses a WebGL scene in the browser)"],
             ["Display", "1280 x 720", "1440 x 900 used for screenshots; a 390 x 844 phone layout was also checked"]],
            widths=[1.3, 2.4, 2.3], size=10),
        P("The minimum column is a conservative estimate for 2,000-row data sets and was not tested on smaller machines."),
        H2("4.6 Software Requirements"),
        TAB("Software", ["Component", "Version / note"],
            [["Operating system", "Windows 11 (`run.bat`); the Python parts are not Windows-specific"],
             ["Python", "3.11.9"],
             ["scikit-learn", "1.8.0 (pinned; models were saved with it)"],
             ["pandas / NumPy / joblib", "3.0.2 / 2.4.4 / 1.5.3 (pinned in `requirements.txt`)"],
             ["Flask", "3.1.3: original prediction pages, field metadata and model loading in `app.py`"],
             ["FastAPI / uvicorn", "0.110.0 / 0.29.0: JSON API on port 8303"],
             ["Node.js", "24.19.0, for the web interface"],
             ["React, Vite, React Router, Recharts", "React 19, Vite 8, React Router 7, Recharts 3 (declared ranges in `package.json`); interface on port 5303"],
             ["Other front-end libraries", "three.js and react-three-fiber (landing scene), framer-motion, GSAP, Lenis, lucide-react"],
             ["Playwright", "Used only to capture the screenshots in this report"]],
            widths=[2.2, 3.8], size=10),
        H2("4.7 Data Requirements"),
        P("The system expects, for each condition, one value for every field in the table below. The training data are the four CSV files generated by `generate_data.py`; each row also carries the target column "
          "(1 = high risk, 0 = low risk). The ranges are the minimum and maximum of the generated data and are the ranges the form uses for its warning."),
        TAB("Input fields and training ranges (read from `data/*.csv`)", ["Condition", "Field", "Meaning", "Training range"], data_rows, widths=[1.1, 1.9, 2.2, 0.8], align=["l", "l", "l", "c"], size=8.5),
        P(f"Each file has {F.N_ROWS:,} rows, no missing values and no duplicate rows. The target is the column `Outcome` (diabetes), `target` (heart), `Dataset` (liver) or `classification` (kidney)."),
        H2("4.8 Analysis of the Data"),
        P("The class balance differs by condition, which matters for the choice of metric. In the heart data 73.1% of the records are high risk, so a classifier that always answered \"high risk\" would be 73.1% accurate "
          "and have perfect recall; in the liver data only 28.1% are high risk, so one that always answered \"low risk\" would be 72.0% accurate and find nobody. Accuracy alone is therefore not used to choose a model, "
          "and the selection rule of the training script is F1-score."),
        TAB("Class balance of the four data sets", ["Condition", "High risk (1)", "Low risk (0)", "Share high risk", "Majority-class accuracy"],
            [[F.NAME[d], X[d]["positive"], X[d]["negative"], F.pct(X[d]["positive"] / X[d]["rows"]), F.pct(max(X[d]["positive"], X[d]["negative"]) / X[d]["rows"])] for d in F.DISEASES],
            widths=[1.5, 1.2, 1.2, 1.1, 1.0], align=["l", "c", "c", "c", "c"], size=10),
        P("Because the labels were produced from a linear risk rule with 8% of them flipped at random, the most important property of the data is its noise ceiling: no model can score much above 92% accuracy on fresh data of this kind. "
          "The hold-out accuracies in Chapter 8 should be read against that ceiling."),
        H2("4.9 User Roles, Use Cases and Constraints"),
        P("There is a single role, the **user**, who may be a student, a health worker or a clinician exploring the tool. There are no accounts or permissions. "
          "A second, offline role, the **developer**, regenerates the data and retrains the models from the command line. The use-case diagram in Chapter 5 shows both."),
        TAB("Main use cases", ["Use case", "Precondition", "Main flow", "Result"],
            [["Predict risk", "API running", "Choose a condition, fill the form (or load a sample), press Predict risk", "Risk class, confidence, model and its accuracy"],
             ["Load a real record", "API running", "Press Positive sample or Negative sample", "Form filled from a random row of the data set"],
             ["Compare models", "API running", "Open the Models page, choose a condition", "Metric bars and a sortable table for four algorithms"],
             ["Inspect data sets", "API running", "Open the Datasets page", "Rows, class balance, features and the synthetic-data notice"],
             ["Retrain models", "Command line", "Run `generate_data.py` then `train_models.py`", "New CSV files, models and training report"]],
            widths=[1.4, 1.1, 2.0, 1.5], size=9),
        P("**Constraints.**"),
        B("The system is a demonstration; it is not clinically validated and must not be used to make decisions about real patients.",
          "One record is scored at a time and for one condition at a time; there is no batch scoring and no combined four-condition result for a single patient.",
          "The training data are synthetic, and the feature coding (for example chest pain type 0-3, thalassaemia code 0-2) follows the generator, not any particular clinical data set.",
          "All inputs are required; missing values are rejected, not imputed.",
          "Only scikit-learn models are used; there are no deep-learning or gradient-boosting libraries, and no hyper-parameter search."),
    ]
