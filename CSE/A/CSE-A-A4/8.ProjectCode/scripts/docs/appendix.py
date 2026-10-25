"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .ch9_10 import src


def code_blocks():
    if F.REPORT:
        return _code_report()
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured. Comments are kept as written; ranges are whole statements."),
        H2("A.1 Preprocessing pipeline (`backend/preprocessing.py`)"),
        CODE(src("backend/preprocessing.py", 71, 77), 7.5),
        CODE(src("backend/preprocessing.py", 110, 149), 7.5),
        H2("A.2 Persistent contrastive divergence step and prediction (`backend/rbm_classifier.py`)"),
        CODE(src("backend/rbm_classifier.py", 82, 107), 7.5),
        CODE(src("backend/rbm_classifier.py", 148, 175), 7.5),
        H2("A.3 Simplified annealing sampler (`backend/samplers.py`)"),
        CODE(src("backend/samplers.py", 41, 66), 7.5),
        H2("A.4 Learning-rate schedules (`backend/train.py`)"),
        CODE(src("backend/train.py", 16, 26), 7.5),
        H2("A.5 Ensemble decision and risk band (`backend/app.py`, route `predict_single`)"),
        CODE(src("backend/app.py", 359, 371), 7.5),
        H2("A.6 Scaling step that fails silently (`backend/app.py`, route `predict_batch`)"),
        CODE(src("backend/app.py", 416, 423), 7.5),
        H2("A.7 Evaluation helper (`backend/evaluation.py`)"),
        CODE(src("backend/evaluation.py", 4, 20), 7.5),
    ]


def guide_blocks():
    if F.REPORT:
        return _guide_report()
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11 (the project was built and measured on Windows 11); Linux and macOS should also work with the manual commands below.",
          "Python 3.11 (the version used here); packages in `requirements.txt`: Flask 3.1.0, Flask-Cors 5.0.0, NumPy 1.26.4, pandas 2.2.2, scikit-learn 1.5.0, SciPy 1.13.0, imbalanced-learn 0.12.4, Matplotlib, Seaborn, joblib and openpyxl.",
          "Node.js 18 or newer with npm, to run the React front end (the frontend folder holds a Vite project).",
          "A current browser. About 4 GB of free memory is plenty; no GPU and no internet connection are needed after installation."),
        H2("B.2 Installation"),
        N("Open the folder `8.ProjectCode` in a terminal.",
          "Optional but recommended: `python -m venv venv`, then activate it (`venv\\Scripts\\activate` on Windows).",
          "Install the Python packages: `pip install -r requirements.txt`.",
          "Install the front-end packages once: `cd frontend`, `npm install`, `cd ..` (`run.bat` does this automatically when `frontend\\node_modules` is missing).",
          "Check that the folders `data` (with `creditcard_synthetic.csv`, 39,000 rows) and `models` (three `grbmc_*.pkl`, three `history_*.json`, `pipeline.pkl`) exist. If they do not, run `python backend/synthetic_data.py` and then `python seed_models.py`, which trains the three models on an 8,000-row sample in under a minute."),
        H2("B.3 Starting the application"),
        TAB("Ways to start SecurePay AI", ["Method", "Command", "What it does"],
            [["Double-click", "`run.bat`", "Installs the Python packages, installs the front-end packages if needed, opens one window for the Flask API and one for the Vite server, then opens the browser"],
             ["PowerShell", "`.\\run.ps1`", "Same steps from PowerShell"],
             ["Manual", "`python backend/app.py` and, in `frontend`, `npm run dev -- --host 127.0.0.1`", "Start the two servers yourself, for example to see their logs"]],
            widths=[1.2, 2.4, 2.7], align=["l", "l", "l"], size=10),
        P(f"The API listens on port {F.API_PORT} and the React interface on port {F.WEB_PORT}; both can be changed with `BACKEND_PORT` and `FRONTEND_PORT` in the `.env` file, which `run.bat`, `run.ps1` and the Vite configuration all read. Open `http://127.0.0.1:{F.WEB_PORT}`. "
          f"The older single-page Flask interface is still served by the API at `http://127.0.0.1:{F.API_PORT}/`. Keep both windows open while you use the application and press Ctrl+C in each to stop it."),
        H2("B.4 Using the screens"),
        H3("Landing page"),
        P("The landing page explains the four steps (describe the payment, prepare the features, three models vote, get a decision band) and links to every screen. It states that the models are trained on a synthetic dataset and are not for production payments."),
        H3("Dashboard"),
        P("Four tiles show the number of transactions, the fraud-labelled count, the best F1 score recorded in the training history and the number of models loaded. Below them a bar chart shows the fraud rate by merchant category and another shows each model's F1 at its best epoch. "
          "The best-epoch value is chosen on the test split, so it is higher than the final-epoch figures used in this report. Further down, a table shows the first rows of the dataset with their labels and a card summarises what fraud looks like in the data. The status chip at the top shows whether the API is reachable."),
        H3("Verify transaction"),
        N("Open **Verify transaction**. Choose an example (an everyday grocery purchase or a large online purchase abroad) or fill the form: amount, merchant category, channel, card present, country match, transaction time in seconds, and three advanced signals V3, V14 and V17. All other anonymised features take the dataset average.",
          "Choose Ensemble or one model (PCD, SAS, QS) and press **Run fraud check**.",
          "Read the result: a verdict (fraud above 50 %), the risk score on a bar with bands at 40 % and 70 %, a recommended action (approve, challenge with 3-D Secure, decline and alert) and the probability from each model."),
        P("Note: the single check scales its input correctly, but the bulk screen does not (Chapter 8), so a bulk file is flagged far too often."),
        H3("Bulk verification"),
        N("Open **Bulk verification** and drop a CSV with the columns Amount, Time, Merchant_Category, Transaction_Type, Card_Present, Country_Match and V1 to V22. **Try the sample file** uses the 20 labelled rows in `data/sample_batch.csv`; **Download sample** saves it.",
          "Press **Upload and analyse**. The page shows the number of transactions, how many were flagged and approved, accuracy, precision, recall, F1 and ROC-AUC when the file has a `Class` column, a confusion matrix and a preview of the first ten rows.",
          "Download the full result as CSV; it adds `Predicted_Class`, `Fraud_Probability` and `Risk` to every row."),
        H3("Analytics"),
        P("Four tabs summarise the whole file: **Where** (fraud rate by merchant category and channel), **When** (fraud rate by hour of day), **How much** (amount distribution and a summary of fraud and legitimate amounts) and **Card signals** (fraud rate with and without the physical card and with matching and mismatching country)."),
        H3("Model comparison"),
        P("Four tabs describe the models: **Comparison** (metrics at each model's best epoch, a model table with the paper's training time beside the time measured here), **Training curves** (per-epoch F1, accuracy, precision, recall or loss), **Features** (random-forest importance and the shape of the pipeline) and **QUBO matrix** (a heat-map of the model's energy function for PCD, SAS or QS). The button **Retrain in the lab** opens the lab."),
        H3("Model lab"),
        P("The lab regenerates the dataset (500 to 50,000 rows per class), rebuilds the preprocessing pipeline (manual undersampling, SMOTE or Tomek links, 5 to 30 features) and retrains any of the three models (1 to 50 epochs, 10 to 300 hidden units). "
          "Each action asks for confirmation. Training overwrites the files in `models` and replaces the in-memory pipeline, so copy that folder first if you want to keep the shipped models."),
        H2("B.5 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause", "Fix"],
            [["The dashboard says it cannot reach the API server", "The Flask window is not running or uses another port", f"Run `python backend/app.py` in `8.ProjectCode`; check `http://127.0.0.1:{F.API_PORT}/api/health`"],
             ["Port already in use", "An old server is still running", "Close the old window or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`"],
             ["`ModuleNotFoundError: flask_cors` or similar", "Packages are not installed", "Run `pip install -r requirements.txt`"],
             ["`models/pipeline.pkl` fails to unpickle (an error about `StringDtype`)", "The pickle was written with a newer pandas than the one installed", "No action: the API catches the error and rebuilds the same pipeline from the CSV at start-up"],
             ["Bulk upload says no columns to parse", "The file is empty or not a CSV", "Use the sample file as a template"],
             ["Every row in a bulk file is flagged", "The scaling defect described in Chapter 8 (inputs are not scaled)", "Known limitation of this build; see the limitations chapter"],
             ["Model views are empty", "No history files in `models`", "Run `python seed_models.py` or train in the lab"]],
            widths=[2.0, 2.2, 2.1], align=["l", "l", "l"], size=9.5),
        H2("B.6 Reproducing the measurements"),
        P("With the API running, `python scripts/smoke_test.py http://127.0.0.1:8304` runs the read-only API checks; `python scripts/measure_latency.py` writes `experiments/latency.json`; `python scripts/run_experiments.py` regenerates `experiments/metrics.json` (it needs `xgboost` and `imbalanced-learn`, and takes several minutes); "
          "`python scripts/make_report_facts.py` writes `docs/REPORT_FACTS.md`."),
    ]


def screens_blocks():
    s = F.shot
    if F.REPORT:
        return _screens_report(s)
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These screens complement the output screens of Chapter 8. All were captured at 1440 x 900 (mobile at 360 x 780) from the running application with the full dataset and the three trained models loaded."),
        H2("C.1 Landing page (dark theme)"),
        FIG(s("02_landing-dark.png"), "The landing page in the dark theme: hero with the best-epoch F1, a four-step explanation, the six screens and a note that the models are trained on synthetic data.", F.shot_w(s("02_landing-dark.png"), 5.6, 6.4)),
        H2("C.2 Analytics: time, amount and card signals"),
        FIG(s("07_analytics-when.png"), "Analytics, When tab: the fraud rate is close to 50 % in every hour of the day, because the generator draws timestamps uniformly and independently of the label.", 5.4),
        FIG(s("08_analytics-how-much.png"), "Analytics, How much tab: amount bands split by label; most fraud falls above $250. The summary lists mean and median amounts for each class and the largest transaction.", 5.4),
        FIG(s("09_analytics-card-signals.png"), "Analytics, Card signals tab: the fraud rate is much higher when the card is not present and when the purchase country differs from the card's.", 5.4),
        H2("C.3 Feature importance"),
        FIG(s("12_models-features.png"), "Model comparison, Features tab: random-forest importance of the one-hot features, with the 18 selected features highlighted, and the pipeline in numbers (6,400 training rows, 1,600 test rows, no correlated columns dropped).", 5.4),
        H2("C.3a Model lab after a real retraining run"),
        P("The Model lab retrains the three models on the current pipeline. To obtain this capture the three models were retrained through the page itself with its default settings (10 epochs, 65 hidden units; the classical model widens to 200), and the original model files were restored afterwards, so the figures in the rest of this report are unaffected. This particular run is a good illustration of the instability measured in Chapter 8: the classical model ended with every test transaction predicted legitimate, while the annealing and quantum-inspired models reached F1 of about 92 % and 87 %."),
        FIG(s("20b_lab-trained-results.png"), "Model lab after a retraining run: per-model metric tiles and confusion matrices. The classical (PCD) model predicts every test row as legitimate (recall 0 %), while SAS and QS find most fraud.", 5.0),
        H2("C.4 Dark theme"),
        PAIR([(s("15_dashboard-dark.png"), "Dashboard in the dark theme."), (s("16_verify-dark.png"), "Verify screen in the dark theme after a check of a large online purchase: ensemble probability 68.4 % (medium, challenge with 3-D Secure), with the per-model probabilities.")], 3.1),
        H2("C.5 Error state and mobile layout"),
        FIG(s("21_dashboard-offline.png"), "Dashboard when the API is not running: the status chip reads API offline and the page explains how to start the server and offers Try again.", 5.0),
        FIG(s("22_bulk-error.png"), "Bulk verification with an empty file: the upload fails with a readable message instead of a crash, and the required columns are listed.", 5.0),
        PAIR([(s("17_mobile-dashboard.png"), "Dashboard on a 360-pixel-wide screen."), (s("18_mobile-verify.png"), "Verify screen on a phone, with the two example buttons."), (s("19_mobile-bulk.png"), "Bulk screen on a phone with the three-step progress list.")], 1.7),
    ]


# ----------------------------------------------------------------------------- compact report variants
def _code_report():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured."),
        H2("A.1 Preprocessing pipeline (`backend/preprocessing.py`)"),
        CODE(src("backend/preprocessing.py", 110, 149), 7),
        H2("A.2 Prediction by free energy (`backend/rbm_classifier.py`)"),
        CODE(src("backend/rbm_classifier.py", 148, 175), 7),
        H2("A.3 Simplified annealing sampler (`backend/samplers.py`)"),
        CODE(src("backend/samplers.py", 41, 66), 7),
        H2("A.4 Ensemble decision and risk band (`predict_single`) and the scaling step that fails silently (`predict_batch`)"),
        CODE(src("backend/app.py", 359, 371), 7),
        CODE(src("backend/app.py", 416, 423), 7),
    ]


def _guide_report():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements and installation"),
        P("Windows 10 or 11 (also expected to work on Linux and macOS), Python 3.11 with the packages in `requirements.txt` (Flask 3.1.0, Flask-Cors 5.0.0, NumPy 1.26.4, pandas 2.2.2, scikit-learn 1.5.0, imbalanced-learn 0.12.4 and others), "
          "and Node.js 18 or newer with npm for the Vite front end. About 4 GB of memory is enough; no GPU or internet connection is needed after installation."),
        N("Open `8.ProjectCode` in a terminal and optionally create a virtual environment (`python -m venv venv`).",
          "Install the Python packages with `pip install -r requirements.txt` and the front-end packages once with `cd frontend`, `npm install` (`run.bat` does this when `frontend\\node_modules` is missing).",
          "Check that `data/creditcard_synthetic.csv` (39,000 rows) and the files in `models/` exist; if not, run `python backend/synthetic_data.py` and `python seed_models.py`."),
        H2("B.2 Starting the application"),
        P(f"Double-click `run.bat` (or run `.\\run.ps1`): it installs the packages, starts the Flask API on port {F.API_PORT} and the Vite server on port {F.WEB_PORT}, and opens the browser at `http://127.0.0.1:{F.WEB_PORT}`. "
          "To start them by hand, run `python backend/app.py` and, in `frontend`, `npm run dev -- --host 127.0.0.1`. The ports can be changed in `.env`. Keep both windows open and press Ctrl+C in each to stop."),
        H2("B.3 Using the screens"),
        B("**Dashboard:** tiles for transactions, fraud-labelled rows, best recorded F1 (chosen on the test split, so higher than the final-epoch figures in this report) and models loaded; bar charts of fraud rate by merchant category and F1 by model; the first dataset rows.",
          "**Verify transaction:** pick an example or fill amount, merchant, channel, card present, country match, time and the signals V3, V14, V17; choose Ensemble or one model and press **Run fraud check**. The result shows the verdict, a risk bar with bands at 40 % and 70 %, the recommended action and each model's probability. The single check scales its input correctly.",
          "**Bulk verification:** drop a CSV with the 28 feature columns (or **Try the sample file**), press **Upload and analyse**, read the counts, the metrics when a `Class` column is present and the preview, and download the result CSV. In this build the bulk route skips scaling (Chapter 8).",
          "**Analytics:** four tabs (Where, When, How much, Card signals) over the whole file.",
          "**Model comparison:** metrics at each model's best epoch, training curves, feature importance and the QUBO matrix heat-map; **Retrain in the lab** opens the lab.",
          "**Model lab:** regenerate the dataset, rebuild the pipeline (manual undersampling, SMOTE or Tomek links, 5 to 30 features) and retrain any of the three models. Training overwrites the files in `models/`, so copy that folder first."),
        H2("B.4 Troubleshooting and reproducing the measurements"),
        TAB("Common problems", ["Symptom", "Fix"],
            [["Dashboard cannot reach the API", f"Run `python backend/app.py`; check `http://127.0.0.1:{F.API_PORT}/api/health`"],
             ["Port already in use", "Close the old window or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`"],
             ["`ModuleNotFoundError`", "Run `pip install -r requirements.txt`"],
             ["`pipeline.pkl` fails to unpickle (`StringDtype`)", "No action: the API rebuilds the same pipeline from the CSV at start-up"],
             ["Every row in a bulk file is flagged", "Known scaling defect of the bulk route (Chapter 8)"]],
            widths=[2.6, 3.7], align=["l", "l"], size=9),
        P("With the API running, `python scripts/smoke_test.py`, `python scripts/measure_latency.py`, `python scripts/run_experiments.py` and `python scripts/make_report_facts.py` regenerate the checks, latency, metrics and facts file used in this report."),
    ]


def _screens_report(s):
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These screens complement the output screens of Chapter 8; all were captured from the running application with the full dataset and the three trained models loaded (1440 x 900; mobile 360 x 780)."),
        H2("C.1 Landing page, dark theme and dashboard"),
        PAIR([(s("02_landing-dark.png"), "Landing page, dark theme."), (s("15_dashboard-dark.png"), "Dashboard, dark theme.")], 2.6),
        H2("C.2 Analytics: time, amount and card signals"),
        PAIR([(s("07_analytics-when.png"), "When: fraud rate by hour."), (s("08_analytics-how-much.png"), "How much: amount bands."), (s("09_analytics-card-signals.png"), "Card signals.")], 2.0),
        H2("C.3 Feature importance and dark verify screen"),
        PAIR([(s("12_models-features.png"), "Features: importance of the 18 selected inputs."), (s("16_verify-dark.png"), "Verify, dark theme: 68.4 % (medium).")], 2.6),
        H2("C.4 Model lab after a real retraining run"),
        P("The three models were retrained through the lab with its default settings (10 epochs) and the original model files were restored afterwards. The classical model ended predicting every row legitimate, the other two reached F1 of about 92 % and 87 %: the instability measured in Chapter 8."),
        FIG(s("20b_lab-trained-results.png"), "Model lab after retraining: metric tiles and confusion matrices; PCD predicts every row legitimate.", 3.0),
        H2("C.5 Error states and mobile layout"),
        PAIR([(s("21_dashboard-offline.png"), "Dashboard with the API stopped."), (s("22_bulk-error.png"), "Bulk upload of an empty file.")], 2.6),
        PAIR([(s("17_mobile-dashboard.png"), "Mobile dashboard."), (s("18_mobile-verify.png"), "Mobile verify."), (s("19_mobile-bulk.png"), "Mobile bulk.")], 1.6),
    ]
