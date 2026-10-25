"""Appendices of the full report: A important code, B installation and user guide, C additional screens."""

import glob
import os

from . import facts as F
from .blocks import B, CODE, FIG, FIGPAIR, H1, H2, N, P, TAB
from .ch9_10 import excerpt, func_src


def _file(rel):
    return open(os.path.join(F.CODE, rel), encoding="utf8").read().strip()


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the code base at build time, so they are exactly what runs. Only the most important parts are shown; the complete source is in `8.ProjectCode`."),
        H2("A.1 Data generation (`generate_data.py`)"),
        P("The label noise function and the diabetes generator; the heart, liver and kidney generators follow the same pattern with their own risk scores."),
        CODE(func_src("generate_data.py", "add_noise_labels") + "\n\n" + func_src("generate_data.py", "generate_diabetes"), 7.5),
        H2("A.2 Training and model selection (`train_models.py`)"),
        CODE("# (imports, the DISEASES feature lists and the output folder are omitted)\n" + _file("train_models.py")[_file("train_models.py").index("MODEL_BUILDERS"):], 7.5),
        H2("A.3 Model loading and the Flask prediction handler (`app.py`)"),
        CODE(excerpt("app.py", "def load_bundle", "BUNDLES = ") + "\n\n" + func_src("app.py", "handle_prediction"), 7.5),
        H2("A.4 FastAPI service (`backend/main.py`)"),
        P("The routes that return the disease list, the sample record, the prediction, the training report and the dataset summary."),
        CODE("\n\n".join(func_src("backend/main.py", n) for n in ("diseases", "sample", "predict", "report", "datasets")), 7.5),
        H2("A.5 Form validation and submission (`frontend/src/pages/Predict.jsx`)"),
        CODE(excerpt("frontend/src/pages/Predict.jsx", "function validate(", "}", exact_end=True) + "\n\n" + excerpt("frontend/src/pages/Predict.jsx", "  const submit = async", "  const loadSample", None).split("  const loadSample")[0].rstrip(), 7.5),
        H2("A.6 Real-data recoding and metrics (`scripts/real_data_check.py`)"),
        P("How the real records are mapped to the project's coding before the shipped models are applied, and the metric helper used by the supplementary check."),
        CODE(func_src("scripts/real_data_check.py", "recode_for_shipped") + "\n\n" + func_src("scripts/real_data_check.py", "mets"), 7.5),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Prerequisites"),
        B("Windows 10 or 11 (the project was built and measured on Windows 11); Python 3.11 with `pip` (3.9 or later is accepted by the README); Node.js 18 or later with `npm` (Node 24 was used); a current browser (Chrome was used for all screens).",
          "About 1 GB of free disk space for the Python environment and the `frontend/node_modules` folder, and about 500 MB of free memory while the app runs.",
          "Internet access for the first run only, to install packages. The trained models and the data are already in the project folder."),
        H2("B.2 One-command start"),
        P("Open the folder `8.ProjectCode` and double-click `run.bat`, or run it from a terminal. It creates the `venv` environment and installs `requirements.txt` on the first run (the pinned scikit-learn 1.8.0 is required because the models were saved with that version), "
          "installs the frontend packages, starts the API and the web application in two windows, and opens the browser."),
        CODE("cd 8.ProjectCode\nrun.bat\n\n:: API:        http://127.0.0.1:8303   (interactive docs at /docs)\n:: Web app:    http://127.0.0.1:5303\n:: Original Flask pages (optional):  venv\\Scripts\\python app.py   ->  http://127.0.0.1:5000", 8.5),
        P("The ports are read from `.env` (`BACKEND_PORT=8303`, `FRONTEND_PORT=5303`, `VITE_API_URL=http://127.0.0.1:8303`). The API accepts browser requests only from `localhost:5303` and `127.0.0.1:5303`. A manual start is:"),
        CODE("python -m venv venv\nvenv\\Scripts\\pip install -r requirements.txt\nvenv\\Scripts\\python -m uvicorn backend.main:api --port 8303\n\ncd frontend\nnpm install\nnpm run dev          # http://127.0.0.1:5303\nnpm run build        # production build into frontend/dist", 8.5),
        H2("B.3 First five minutes"),
        N("Open http://127.0.0.1:5303 and press **Open app** (there is no sign-in).",
          "On the **Overview** page read the four conditions, the number of models trained and the test accuracy of the selected model of each condition.",
          "Choose a condition in the left menu, for example **Diabetes**. The form shows eight inputs with an example value and the range seen in the training data.",
          "Press **Positive sample** or **Negative sample** to fill the form with a real row of the training CSV, or type your own values. Every field is required; a value outside the training range shows a warning but is still accepted.",
          "Press **Predict risk**. The result card shows Positive (High Risk) or Negative (Low Risk), the model's confidence, the model used and its test accuracy. The label of a sample is not a promise: the model may disagree with it.",
          "Open **Models** to compare the four algorithms by accuracy, precision, recall and F1 (sortable table), and **Datasets** to see the size and class balance of each CSV and the warning that the data are synthetic.",
          "Use the sun icon at the top right to switch between the dark and light themes."),
        H2("B.4 The pages"),
        TAB("Pages of the web application", ["Page", "Address", "What it does"],
            [["Landing", "`/`", "Introduction, how it works, the conditions and headline numbers"],
             ["Overview", "`/app`", "Four conditions, models trained, best accuracy, accuracy chart, links to the forms"],
             ["Predict", "`/app/predict/diabetes` (also `heart`, `liver`, `kidney`)", "Input form, sample buttons, validation, result card"],
             ["Models", "`/app/models`", "Metric bars and a sortable score table for the four algorithms of each condition"],
             ["Datasets", "`/app/data`", "Rows, class balance and feature list of the four CSV files; synthetic-data warning"],
             ["About", "`/app/about`", "What the project does, tech stack and medical disclaimer"],
             ["Not found", "any other address", "A message with a link back to the application"]],
            widths=[1.0, 2.5, 2.5], size=9.5),
        H2("B.5 Calling the API directly"),
        CODE("curl http://127.0.0.1:8303/api/diseases\ncurl \"http://127.0.0.1:8303/api/diseases/diabetes/sample?outcome=1\"\ncurl -X POST http://127.0.0.1:8303/api/predict/diabetes ^\n     -H \"Content-Type: application/json\" ^\n     -d \"{\\\"values\\\": {\\\"Pregnancies\\\": 2, \\\"Glucose\\\": 128.9, \\\"BloodPressure\\\": 71.8, \\\"SkinThickness\\\": 32.4, \\\"Insulin\\\": 103.3, \\\"BMI\\\": 30.2, \\\"DiabetesPedigreeFunction\\\": 0.93, \\\"Age\\\": 54}}\"", 8),
        H2("B.6 Reproducing the numbers in this report"),
        CODE("venv\\Scripts\\python generate_data.py              :: regenerate data/*.csv (seed 42)\nvenv\\Scripts\\python train_models.py               :: retrain, rewrite models/*.pkl and training_report.json\nvenv\\Scripts\\python scripts\\run_experiments.py     :: ROC-AUC, CV, ten splits, thresholds, importance -> docs/experiments/results.json\nvenv\\Scripts\\python scripts\\real_data_check.py     :: real-data check -> docs/experiments/real_data_results.json\nvenv\\Scripts\\python scripts\\api_tests.py           :: 41 API checks and latency (API must be running)\nvenv\\Scripts\\python scripts\\smoke_test.py          :: 27-check smoke test (API must be running)\npython scripts\\make_figures.py                      :: charts -> docs/figures\npython scripts\\capture_screens.py                   :: screens 01-12 (app must be running)\npython scripts\\capture_extra.py                     :: screens 13-19", 8),
        P("Re-running `generate_data.py` and `train_models.py` overwrites the shipped data and models; because the generator uses a fixed seed the files should be reproduced, but check the new `training_report.json` before replacing models that a running service has loaded."),
        H2("B.7 Troubleshooting"),
        TAB("Common problems", ["Problem", "What to do"],
            [["Prediction fails with an error about `predict_proba` or a pickle", "The environment has a different scikit-learn version; install the pinned `requirements.txt` (scikit-learn 1.8.0) in a fresh `venv`"],
             ["The web page says it cannot reach the prediction API", "Start the API (`run.bat` starts both) and check that port 8303 is free and that `.env` matches"],
             ["A port is already in use", "Change `BACKEND_PORT` and `FRONTEND_PORT` in `.env` (and `VITE_API_URL`) and restart; keep the web port at 5303 or add it to the API's CORS list"],
             ["`npm install` fails", "Check the Node.js version (18 or later) and the internet connection; delete `frontend/node_modules` and retry"],
             ["Requests take about two seconds each", "Use `127.0.0.1` instead of `localhost` (IPv6 name resolution on some Windows machines)"],
             ["The result disagrees with the sample's label", "Expected for some rows: the label contains 8% deliberate noise and the model is not perfect (see the failure case in Chapter 8)"]],
            widths=[2.4, 3.6], size=9.5),
    ]


SHOT_DESC = {
    "01_landing-dark": "Landing page, dark theme", "02_landing-light": "Landing page, light theme", "03_landing-how-it-works": "Landing page, how-it-works section",
    "04_overview": "Overview page", "05_predict-diabetes": "Diabetes, positive sample", "06_predict-heart": "Heart disease, positive sample", "07_predict-liver": "Liver disease, positive sample",
    "08_predict-kidney": "Kidney disease, positive sample", "09_models": "Models page", "10_datasets": "Datasets page", "11_about": "About page", "12_not-found": "Not-found page",
    "13_predict-diabetes-low-risk": "Diabetes, negative sample", "14_predict-heart-low-risk": "Heart disease, negative sample", "15_predict-liver-low-risk": "Liver disease, negative sample",
    "16_predict-kidney-low-risk": "Kidney disease, negative sample", "17_validation-error": "Validation errors on an empty form", "18_out-of-range-warning": "Out-of-range warning",
    "19_predict-heart-mobile": "Phone layout (390 x 844)", "20_predict-heart-false-positive": "Failure case: false positive",
}
IN_CH8 = {"04_overview", "05_predict-diabetes", "06_predict-heart", "07_predict-liver", "08_predict-kidney", "09_models", "10_datasets", "13_predict-diabetes-low-risk",
          "14_predict-heart-low-risk", "15_predict-liver-low-risk", "16_predict-kidney-low-risk", "17_validation-error", "18_out-of-range-warning", "19_predict-heart-mobile",
          "20_predict-heart-false-positive"}


def screens_blocks():
    s = F.shot
    rows = []
    for path in sorted(glob.glob(os.path.join(F.SHOTS, "*.png"))):
        k = os.path.splitext(os.path.basename(path))[0]
        rows.append([f"`{k}.png`", SHOT_DESC.get(k, ""), "Chapter 8" if k in IN_CH8 else "Appendix C"])
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These screens complete the set in Chapter 8: the landing page in both themes and its how-it-works section, the About page with the medical disclaimer, and the not-found page. "
          "All are real captures of the running application at 1440 x 900, taken with `scripts/capture_screens.py`."),
        FIGPAIR((s("01_landing-dark.png"), "Landing page (dark theme)"), (s("02_landing-light.png"), "Landing page (light theme)")),
        FIGPAIR((s("03_landing-how-it-works.png"), "Landing page, how-it-works section: the F1-score of the four algorithms for the diabetes example, with SVM marked as the selected model"), (s("11_about.png"), "About page: what the system does, the tech stack and the medical disclaimer, which states that the training data are synthetically generated")),
        FIG(s("12_not-found.png"), "Not-found page shown for an address that does not exist", 3.6),
    ]
