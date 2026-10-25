"""Chapter 6: Methodology and software implementation."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB


def c(key):
    """Citation marker for a reference key (resolved at build time from refs.NUM)."""
    from .refs import NUM

    return f"[{NUM[key]}]"


X = F.X
TP = X["diabetes"]["train_rows"]
TE = X["diabetes"]["test_rows"]

RULES = [
    ["Diabetes", "0.04 (glucose - 120) + 0.06 (BMI - 30) + 0.02 (age - 40) + 1.5 x pedigree + 0.03 (blood pressure - 72) - 1.4",
     "pregnancies, skin thickness, insulin"],
    ["Heart disease", "0.035 (age - 50) + 0.9 sex + 0.5 cp + 0.02 (trestbps - 130) + 0.01 (chol - 240) + 0.8 exang + 0.5 oldpeak + 0.6 ca - 0.02 (thalach - 150) - 1.9",
     "fbs, restecg, slope, thal"],
    ["Liver disease", "0.35 total bilirubin + 0.02 (alk. phosphatase - 290) + 0.015 (ALT - 45) + 0.01 (AST - 50) - 0.8 albumin + 0.015 (age - 45) - 0.3",
     "gender, direct bilirubin, total protein, A/G ratio"],
    ["Kidney disease", "0.02 (age - 45) + 0.02 (BP - 76) - 40 (specific gravity - 1.015) + 0.6 albumin + 0.35 sugar + 0.01 (glucose - 148) + 0.02 (urea - 45) + 0.6 (creatinine - 1.5) - 0.35 (haemoglobin - 12.5) - 1.2",
     "sodium, potassium, packed cell volume"],
]

DISTRIBUTIONS = [
    ["Diabetes", "age uniform integer 18-79; pregnancies uniform integer 0-9; glucose N(120, 30) clipped to 60-250; blood pressure N(72, 12) to 40-130; skin thickness N(20, 10) to 0-60; insulin N(80, 60) to 0-400; BMI N(30, 7) to 15-55; pedigree N(0.47, 0.3) to 0.05-2.5"],
    ["Heart disease", "age 29-79; sex, cp (0-3), restecg (0-2), slope (0-2), ca (0-3), thal (0-2) uniform integers; trestbps N(131, 17) to 90-200; chol N(246, 51) to 120-450; thalach N(150, 23) to 70-210; fbs Bernoulli(0.15); exang Bernoulli(0.33); oldpeak exponential(1) to 0-6"],
    ["Liver disease", "age 18-84; gender uniform 0/1; total bilirubin exponential(1.5) to 0.1-20; direct bilirubin = total x U(0.2, 0.6); alk. phosphatase N(290, 150) to 60-1200; ALT exponential(45) to 5-500; AST exponential(50) to 5-500; total protein N(6.5, 1) to 3-9; albumin N(3.2, 0.8) to 1-5.5; A/G ratio = albumin / (protein - albumin + 0.1) to 0.2-3"],
    ["Kidney disease", "age 2-89; blood pressure N(76, 13) to 50-180; specific gravity one of 1.005 ... 1.025; albumin and sugar uniform integers 0-4; random glucose N(148, 70) to 50-490; urea exponential(45) to 10-300; creatinine exponential(1.5) to 0.3-15; sodium N(137, 8) to 110-160; potassium N(4.4, 1) to 2.5-8; haemoglobin N(12.5, 2.5) to 3-18; packed cell volume N(38, 8) to 15-55"],
]

HYPER = [
    ["Logistic Regression", "`LogisticRegression(max_iter=1000, random_state=42)`", "L2 penalty, C = 1, lbfgs solver (library defaults)"],
    ["Decision Tree", "`DecisionTreeClassifier(max_depth=6, random_state=42)`", "Gini impurity, no pruning other than the depth limit"],
    ["Random Forest", "`RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42)`", "Bootstrap samples, sqrt(p) features tried per split (library default)"],
    ["SVM", "`SVC(kernel=\"rbf\", C=1.0, probability=True, random_state=42)`", "gamma = \"scale\"; probabilities by Platt scaling (internal 5-fold cross-validation)"],
]


def methodology_blocks():
    tpos = ", ".join(str(X[d]["test_positive"]) + " for " + F.NAME[d].lower() for d in F.DISEASES)
    fit_lo = min(v["fit_s"] for d in F.DISEASES for v in X[d]["timing"].values()) * 1000
    fit_hi = max(v["fit_s"] for d in F.DISEASES for v in X[d]["timing"].values())
    return [
        H2("6.1 Overview of the Methodology"),
        P("The method is a supervised-learning pipeline repeated independently for four conditions. The first seven steps run once, offline, when the models are built; the last four run for every prediction request."),
        N("**Generate the data.** `generate_data.py` writes four CSV files of 2,000 rows each from the rules of Section 6.2.",
          "**Read and split.** For each disease the CSV is read, the feature columns and the target are separated, and a stratified 80/20 split with `random_state=42` gives 1,600 training and 400 test rows.",
          "**Scale.** A `StandardScaler` is fitted on the training rows only and applied to training and test rows.",
          "**Train.** Logistic Regression, Decision Tree, Random Forest and SVM are fitted with the settings of Section 6.6.",
          "**Evaluate.** Accuracy, precision, recall and F1-score are computed on the 400 test rows.",
          "**Select.** The model with the highest F1 is chosen for the disease.",
          "**Save.** The chosen model, the scaler and the feature list are written with `joblib`, and the scores of all 16 models are written to `training_report.json`.",
          "**Receive a record.** At run time the user enters, or loads, one value for each feature of one disease; the form checks that every field is present and numeric.",
          "**Validate.** The API checks the disease key, converts every value to a finite number in the saved feature order and answers 422 or 404 on failure.",
          "**Scale and predict.** The saved scaler transforms the vector; the saved model gives the class and the class probabilities.",
          "**Report.** The class becomes \"Positive (High Risk)\" or \"Negative (Low Risk)\", the confidence is the larger class probability, and the model name and its hold-out accuracy are returned with it."),
        P("Two things are deliberately absent. The pipeline has no data-cleaning step (the generated data contains no missing values, duplicates or invalid entries, and no imputation or outlier code was written), "
          "and it has no explanation step: the application reports a class and a confidence, not the parameters that produced them. Chapter 8 measures what these omissions mean."),
        H2("6.2 Data: Four Synthetic Datasets"),
        P(f"The four datasets are not clinical records. The original build environment had no access to the public benchmark data, so `generate_data.py` creates data with medically plausible ranges. "
          f"Each dataset has {F.N_ROWS:,} rows (8,000 in total, numpy seed 42), no missing cells and no duplicate rows (checked). The features are drawn independently from the distributions below; "
          "the table gives the sampling of each disease."),
        TAB("Sampling of the features (generate_data.py)", ["Disease", "Feature distributions"], DISTRIBUTIONS, widths=[1.1, 4.9], size=8.5),
        P("The label is then built in three steps. First a **linear risk score** is computed from some of the features; second the score is passed through the logistic function and the label is 1 if the probability exceeds 0.5 "
          "(that is, if the score is positive); third **8% of the labels are flipped at random** (`add_noise_labels(noise=0.08)`)."),
        EQ("risk = sum_j w_j (x_j - m_j) + b ;   p = 1 / (1 + exp(-risk)) ;   y = 1 if p > 0.5 else 0 ;   then y is flipped with probability 0.08"),
        TAB("Risk score of each disease (the label rule)", ["Disease", "Risk score", "Features with no weight"], RULES, widths=[1.0, 3.9, 1.1], size=8.5),
        P(f"The positive rate follows from the rule and the distributions: diabetes {F.pct(X['diabetes']['positive'] / F.N_ROWS)}, heart disease {F.pct(X['heart']['positive'] / F.N_ROWS)}, "
          f"liver disease {F.pct(X['liver']['positive'] / F.N_ROWS)} and kidney disease {F.pct(X['kidney']['positive'] / F.N_ROWS)}. Three consequences matter for everything that follows."),
        B("**The label is a known linear function of the features plus noise.** A linear model is therefore the correct model family, and the accuracy that any classifier can reach on fresh draws is limited to about 92% (one minus the flip rate). "
          "A hold-out accuracy of 88-92% means the pipeline recovers the rule almost as well as is possible; it does not say how well the pipeline would detect disease in patients.",
          "**Some features carry no information.** Pregnancies, skin thickness and insulin (diabetes), fasting blood sugar, resting ECG, slope and thal (heart), and sodium, potassium and packed cell volume (kidney) have zero weight in the rule, "
          "so any model that uses them is fitting noise.",
          "**The features are independent.** Real clinical variables are correlated (glucose with BMI, creatinine with urea); here they are not, which removes one of the main difficulties of real data."),
        P(f"Because these data are not a benchmark, a separate supplementary check (`scripts/real_data_check.py`) was run on public datasets with the same schemas: the Pima Indians Diabetes data {c('pima')}, the UCI Cleveland heart-disease data {c('cleveland')}, "
          f"the Indian Liver Patient Dataset {c('ilpd')} and the UCI chronic kidney disease data {c('ckd')}. That check is not part of the application and is reported in Chapter 8."),
        H2("6.3 Preprocessing"),
        P("Preprocessing is a single step: **standardisation**. For every feature j the scaler stores the mean and standard deviation of the 1,600 training rows and maps x to z = (x - mean_j) / sd_j. "
          "The scaler is fitted on the training rows only and then applied unchanged to the test rows and, at run time, to the vector entered by the user, so no test information reaches the models and training and serving use the same transformation. "
          "The scaler matters for Logistic Regression and the SVM, whose solutions depend on feature scale; trees are unaffected."),
        P("Several steps that the project objectives mention were **not implemented**, and the documents say so plainly: there is no imputation (no value is ever missing in the synthetic data; the real-data check imputes with the median, but the application does not), "
          "no outlier detection or capping, no feature selection, no class weighting or resampling (such as SMOTE " + c("smote") + "), and no encoding of categorical variables (the categorical inputs are already coded as small integers by the generator)."),
        H2("6.4 Choice of Algorithms and Why"),
        P("The four algorithms are the ones the project objectives name. They cover four different ways of drawing a decision boundary, which is why they are a reasonable comparison on tabular data:"),
        TAB("The four algorithms and the reason each is included", ["Algorithm", "Decision boundary", "Why it is in the comparison", "Known weakness"],
            [["Logistic Regression", "A single linear boundary in the scaled feature space", "The simplest probabilistic baseline; fast, stable and easy to inspect through its coefficients; correct when the label is linear in the features", "Cannot capture interactions or non-linear effects unless they are added by hand"],
             ["Decision Tree", "Axis-aligned rectangles from recursive splits", "Rule-like and easy to explain; needs no scaling; handles mixed feature types", "Unstable and prone to over-fitting; a depth limit is essential"],
             ["Random Forest", "Average of many decorrelated trees " + c("rf"), "Usually the strongest default on tabular data; reduces the variance of a single tree; gives feature importances", "Less smooth than a linear model; can fit label noise when trees are deep"],
             ["SVM (RBF)", "A maximum-margin boundary in a kernel feature space " + c("svm"), "Flexible non-linear boundary with few parameters; strong on small and medium data", "Sensitive to C and gamma; probabilities need an extra calibration step"]],
            widths=[1.2, 1.5, 1.9, 1.4], size=8.5),
        P("The project introduction expects ensemble methods to outperform single classifiers on medical tables, and the base paper " + c("base") + " found Random Forest and CatBoost to be its best classifiers on thyroid data. "
          "This project's measurements do not confirm that expectation on its own data: because the labels are linear plus noise, Logistic Regression is as good as or better than Random Forest for all four diseases, and the Random Forest over-fits the noisy labels (Chapter 8). "
          "That result is a property of the synthetic data and should not be generalised to clinical data, where the real-data check puts Random Forest and Logistic Regression close together."),
        H2("6.5 Mathematical Formulation"),
        H3("6.5.1 Logistic Regression"),
        P("Given a scaled feature vector x, the model estimates the probability of the positive class with the logistic (sigmoid) function of a linear score. Training minimises the L2-penalised log-loss over the n training rows (scikit-learn default, C = 1):"),
        EQ("p(y = 1 | x) = sigma(w.x + b) = 1 / (1 + exp(-(w.x + b)))"),
        EQ("min over (w, b) of  (1/2) ||w||^2 + C * sum_i [ -y_i log p_i - (1 - y_i) log(1 - p_i) ]"),
        P("The predicted class is 1 when p exceeds 0.5, that is when w.x + b is positive. The coefficients w, measured on standardised features, indicate which inputs raise the risk and by how much."),
        H3("6.5.2 Decision Tree"),
        P("A tree chooses at each node the feature and threshold that minimise the weighted Gini impurity of the two child nodes, where for a node with class proportions p_k:"),
        EQ("G = 1 - sum_k p_k^2"),
        P("Splitting stops at depth 6 (`max_depth=6`) or when a node is pure. The predicted probability of a leaf is the share of training rows of the positive class in it."),
        H3("6.5.3 Random Forest"),
        P("A forest grows B = 200 trees, each of depth at most 8, on bootstrap samples of the training rows, trying a random subset of about sqrt(p) features at every split. The prediction is the average of the trees' class probabilities:"),
        EQ("p(y = 1 | x) = (1 / B) * sum_{b = 1..B} p_b(y = 1 | x)"),
        H3("6.5.4 Support Vector Machine"),
        P("The soft-margin SVM with the radial basis function kernel solves the dual problem below, with C = 1 and gamma = 1 / (p * Var(X)) (`gamma=\"scale\"`). The decision function is a weighted sum of kernel values at the support vectors:"),
        EQ("K(x, x') = exp(-gamma ||x - x'||^2) ;   f(x) = sum_i alpha_i y_i K(x_i, x) + b ;   0 <= alpha_i <= C"),
        P("With `probability=True` scikit-learn fits a sigmoid (Platt scaling) to the decision values by internal five-fold cross-validation to obtain class probabilities. "
          "Because that calibration is fitted separately from the decision function, the class given by `predict` can occasionally differ from the class with the larger probability."),
        H3("6.5.5 Evaluation metrics and the selection rule"),
        P("With TP, FP, TN and FN counted on the 400 test rows (the positive class is \"high risk\"):"),
        EQ("accuracy = (TP + TN) / (TP + TN + FP + FN) ;   precision = TP / (TP + FP) ;   recall = TP / (TP + FN)"),
        EQ("F1 = 2 * precision * recall / (precision + recall)"),
        P("ROC-AUC is the probability that a randomly chosen positive row receives a higher score than a randomly chosen negative row; it needs no threshold. "
          "The training script computes accuracy, precision, recall and F1 only; ROC-AUC was added afterwards in `scripts/run_experiments.py`. The model served for disease d is the one with the largest F1 on the test rows:"),
        EQ("m*(d) = argmax over m in {LR, DT, RF, SVM} of F1_m(d) on the test set"),
        P("F1 is used instead of accuracy because it penalises both missed cases and false alarms and is not inflated by the majority class. Selecting and reporting on the same test rows gives a slightly optimistic score for the winner "
          + c("varma") + "; the extra analyses of Chapter 8 (five-fold cross-validation and ten random splits) are the check on that."),
        H3("6.5.6 Confidence, noise ceiling and permutation importance"),
        P("The confidence shown to the user is the larger of the two class probabilities, so it lies between 50% and 100% and says how sure the model is of the class it chose; it is not the probability of disease and the models were not calibrated. "
          "With a flip rate of 0.08 the best achievable expected accuracy on fresh draws of the synthetic data is 1 - 0.08 = 0.92. Finally, the offline importance analysis shuffles one feature at a time and measures the loss of accuracy:"),
        EQ("PI_j = acc(test) - (1 / R) * sum_{r = 1..R} acc(test with column j shuffled in repetition r) ,   R = 20"),
        H2("6.6 Model Architecture and Training Configuration"),
        TAB("Hyper-parameters exactly as used in train_models.py", ["Algorithm", "Constructor", "Remaining settings"], HYPER, widths=[1.3, 3.0, 1.7], size=9),
        P(f"All settings are fixed in the source; no grid search, random search or cross-validation was used to tune them. The training set has {TP:,} rows and the test set {TE} rows for every disease (stratified, `random_state=42`); "
          f"the numbers of positive test rows are {tpos}. "
          f"Fitting a single model takes between {fit_lo:.0f} ms and {fit_hi:.2f} s on the project machine (an Intel Core i5-12500 CPU; no GPU is needed), so the 16 models are trained in a few seconds."),
        TAB("Feature counts and the model that is served", ["Disease", "Inputs", "Selected model", "Selection rule result (test F1)"],
            [[F.NAME[d], str(X[d]["n_features"]), F.BEST[d], f"{F.HO[d][F.BEST[d]]['f1']:.4f}"] for d in F.DISEASES], widths=[1.6, 0.9, 1.8, 1.7], align=["l", "c", "l", "c"], size=10),
        H2("6.7 Evaluation Protocol"),
        P("Three layers of evidence are used, each answering a different question. (1) The **hold-out test** of `train_models.py` is the number the application shows. "
          "(2) **Stratified five-fold cross-validation** and **ten random 80/20 splits** (seeds 0 to 9), run by `scripts/run_experiments.py` with the scaler refitted inside every fold, ask whether the choice of model depends on the particular split. "
          "(3) A **decision-threshold sweep** (0.20 to 0.80), **permutation importance**, **hyper-parameter sensitivity** and a **train-versus-test comparison** characterise the selected models. "
          "The extra script also checks that its re-computation reproduces `training_report.json` exactly, which it does for all 16 model-and-disease cells and for the saved pickles."),
        P("The supplementary real-data check uses the same four algorithms and settings with a median imputer in front of the scaler and three repetitions of five-fold cross-validation, and in addition applies the saved, synthetic-trained models to the real records. "
          "It is described as supplementary because the datasets, their coding and their size differ from those of the application."),
    ]


def application_blocks():
    A = F.API
    lat = A["latency"]["POST /api/predict/diabetes"]
    return [
        H2("6.8 Application Architecture"),
        P("The application has three layers that share one set of trained models. The **model layer** is the offline script `train_models.py` and the files it writes in `models/`. The **service layer** is `app.py`, which loads those files once at import time into `BUNDLES` "
          "(a dictionary from disease key to the tuple model, scaler, features) and defines `FIELD_META`, and `backend/main.py`, a FastAPI application that imports `app.py` and adds the JSON routes. The **presentation layer** is the React application in `frontend/`. "
          "Because `backend/main.py` imports the Flask module instead of copying its objects, the API and the original Flask pages use the identical models and the identical arithmetic; importing `app.py` does not start the Flask server."),
        P("The React application is a single-page application built with Vite. `src/App.jsx` declares the routes (the landing page, then `/app` with an overview, `predict/:disease`, `models`, `data`, `about` and a not-found page; all but the landing page are loaded lazily). "
          "`src/lib/api.js` is the only place that talks to the network: it prefixes every path with the API address (`VITE_API_URL`, default `http://127.0.0.1:8303`), turns a failed fetch into the message \"Cannot reach the prediction API\", and turns a non-200 answer into an error carrying the `detail` text of the API. "
          "`Predict.jsx` is one component for all four diseases: it asks `/api/diseases/{d}` for the fields, renders a number input or a drop-down for each, validates that every field is filled with a number, posts `{\"values\": {...}}` and shows the answer. "
          "Page data are loaded with a small `useAsync` hook, and the connection badge uses `useHealth`, which polls `/api/health` every 30 seconds."),
        H2("6.9 API Design with Real Requests and Responses"),
        P("The seven routes are listed in Chapter 5. The following exchanges were captured from the running service on `127.0.0.1:8303`. A prediction request carries one value for each feature, keyed by the feature name:"),
        CODE("""POST /api/predict/diabetes
{"values": {"Pregnancies": 2, "Glucose": 128.9, "BloodPressure": 71.8, "SkinThickness": 32.4,
            "Insulin": 103.3, "BMI": 30.2, "DiabetesPedigreeFunction": 0.93, "Age": 54}}

200 OK
{"disease": "diabetes", "title": "Diabetes Risk Prediction", "positive": true,
 "result": "Positive (High Risk)", "probability": 90.71, "model": "SVM", "accuracy": 0.895}""", 8.5),
        P("A request with a value that is not a number is refused before the model is called; the message names the labels of the fields that failed. Here only `Glucose` was sent (with the text \"abc\"), so all eight labels are listed:"),
        CODE("""POST /api/predict/diabetes   {"values": {"Glucose": "abc"}}

422 Unprocessable Entity
{"detail": "Please enter a valid number for: Number of Pregnancies, Glucose Level (mg/dL),
            Blood Pressure (mm Hg), Skin Thickness (mm), Insulin Level (mu U/ml), BMI,
            Diabetes Pedigree Function, Age."}""", 8.5),
        P("The sample route returns a real row of the CSV and its label, which the interface uses to fill the form:"),
        CODE("""GET /api/diseases/kidney/sample?outcome=1

200 OK
{"values": {"age": 49.0, "blood_pressure": 89.7, "specific_gravity": 1.005, "albumin": 2.0, "sugar": 2.0,
            "blood_glucose_random": 151.5, "blood_urea": 64.5, "serum_creatinine": 0.84, "sodium": 142.6,
            "potassium": 3.48, "hemoglobin": 10.74, "packed_cell_volume": 31.5},
 "label": 1}""", 8.5),
        P("`GET /api/diseases/{d}` returns the data the form needs: for each field its name, label, placeholder, input type, minimum, maximum and median in the CSV, and the options of a categorical field "
          "(for example `{\"value\": 1, \"label\": \"Male\"}`), together with the metrics of the best model and the four algorithms' scores. `GET /api/datasets` returns, for every disease, the row count, the positive and negative counts, the target column, the feature list and `\"synthetic\": true`, "
          "which the Datasets page turns into its warning banner."),
        P(f"On the project machine a prediction request takes a median of {lat['p50_ms']:.1f} ms and a 95th percentile of {lat['p95_ms']:.1f} ms (200 calls on 127.0.0.1); Chapter 7 gives the measurements and their caveats."),
        H2("6.10 Security and Error Handling"),
        P("The application is built as a local demonstration, and its security posture is correspondingly limited. The facts are:"),
        B("**No authentication and no stored data.** Every route is open; no patient value is written to disk or to a log by the application, and the result exists only in the response.",
          "**Input validation.** The pydantic model `PredictBody` requires a JSON object `values`; each value is converted with `float()`, and a missing key, `null`, an empty string, text, `nan` or infinity is reported with HTTP 422 and a readable message. "
          "Unknown extra keys are ignored. Physiologically impossible numbers (a glucose of 100,000 mg/dL or an age of -5) are **accepted**, because there is no range check in the API; the interface only warns when a value lies outside the training range of the feature.",
          "**Error codes.** 404 for an unknown disease key (also for the detail and sample routes), 422 for invalid input or malformed JSON, 405 for a wrong method, 404 for an unknown route. The React client shows the `detail` text; if the API cannot be reached it says so.",
          "**CORS.** Only `http://localhost:5303` and `http://127.0.0.1:5303` may call the API from a browser.",
          "**Model files.** `joblib.load` is used on the files in `models/`; these must come only from `train_models.py` because pickle files can execute code when loaded.",
          "**Flask development server.** `app.py` runs with `debug=True` on all interfaces when started directly. This is for local use only."),
        P("What is missing, and would be required before any real use, is authentication and authorisation, transport security (HTTPS), rate limiting, audit logging, range validation of clinical values, and a data-protection review."),
        H2("6.11 Installation and Execution"),
        P("The project needs Python 3.11 or newer and Node.js (the project was built with Python 3.11.9 and Node 24). The trained models were saved with scikit-learn 1.8.0, so the pinned `requirements.txt` must be used: "
          "an older scikit-learn fails on `predict_proba` when it unpickles the models."),
        TAB("Pinned Python packages (requirements.txt)", ["Package", "Version", "Used for"],
            [["scikit-learn", "1.8.0", "Models, scaler, metrics"], ["pandas", "3.0.2", "Reading the CSVs in the API"], ["numpy", "2.4.4", "Arrays, data generation"],
             ["joblib", "1.5.3", "Saving and loading the models"], ["Flask", "3.1.3", "The original web pages and the shared `app.py`"],
             ["fastapi", "0.110.0", "The JSON API"], ["uvicorn", "0.29.0", "The ASGI server"]],
            widths=[1.5, 1.0, 3.5], size=10),
        P("On Windows the whole application starts with one command:"),
        CODE("""run.bat          # creates venv\\ and installs requirements.txt on first run, installs frontend\\node_modules,
                 # starts  venv\\Scripts\\python -m uvicorn backend.main:api --port 8303
                 # and     cd frontend && npm run dev   (http://127.0.0.1:5303), then opens the browser""", 8.5),
        P("The ports come from `.env` (`BACKEND_PORT=8303`, `FRONTEND_PORT=5303`, `VITE_API_URL=http://127.0.0.1:8303`; `.env.example` is the template). To retrain from scratch:"),
        CODE("""venv\\Scripts\\python generate_data.py     # writes data/*.csv  (numpy seed 42)
venv\\Scripts\\python train_models.py      # writes models/*.pkl and models/training_report.json
venv\\Scripts\\python -m uvicorn backend.main:api --port 8303
venv\\Scripts\\python scripts\\smoke_test.py   # 27 checks against the running API
venv\\Scripts\\python app.py                # optional: the original Flask pages on http://127.0.0.1:5000""", 8.5),
        P("Appendix B gives the full installation and user guide."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
