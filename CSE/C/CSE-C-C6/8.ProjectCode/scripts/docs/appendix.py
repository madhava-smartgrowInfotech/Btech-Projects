"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

from . import facts as F
from .blocks import B, CODE, H1, H2, N, P, PAIR, TAB
from .ch9_10 import src


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("Excerpts from the repository (`8.ProjectCode`) in the state in which the results of this report were measured; the complete files are in `src/` and `backend/`."),
        H2("A.1 Text cleaning (`src/preprocessing.py`)"),
        CODE(src("src/preprocessing.py", 32, 43), 7.5),
        H2("A.2 Firefly fitness and main loop (`src/firefly.py`)"),
        CODE(src("src/firefly.py", 44, 59) + "\n        ...\n" + src("src/firefly.py", 75, 96), 7.5),
        H2("A.3 Pipeline: features, PCA and the final classifier (`src/pipeline.py`)"),
        CODE(src("src/pipeline.py", 37, 66) + "\n        ...\n" + src("src/pipeline.py", 91, 97), 7.5),
        H2("A.4 Prediction endpoint (`backend/main.py`)"),
        CODE(src("backend/main.py", 171, 195), 7.5),
        H2("A.5 Background retraining (`backend/main.py`)"),
        CODE(src("backend/main.py", 250, 272), 7.5),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements and start"),
        B(f"A Windows PC (measurements in this report: {F.HARDWARE}); no GPU. Python 3.11 or newer, Node.js 20 or newer, a current Chrome or Edge, and internet for the first installation.",
          "Double-click `run.bat` in `8.ProjectCode`: it checks Python and Node.js, creates or rebuilds `.venv`, installs `backend/requirements.txt` and the frontend packages and starts both servers. "
          "The browser opens `http://localhost:5406` (use localhost, not 127.0.0.1); the API runs on `http://127.0.0.1:8406` (`/docs`). Ports are set in `.env`. Close the two minimised windows to stop.",
          "The backend loads `models/msvm_model.pkl` (about 3 s); if it is missing, a small demo model is trained first (about a minute). To use the LIAR2 model, set `FAKENEWS_MODEL` to `models/liar2_msvm_model.pkl` (or a copy) before starting; "
          "it is produced by `scripts/run_experiments.py` from the LIAR2 files `train.csv`, `valid.csv`, `test.csv` (huggingface.co/datasets/chengxuphd/liar2) placed in `data/liar2/`."),
        CODE(".venv\\Scripts\\python -m uvicorn backend.main:app --port 8406      # by hand, backend\ncd frontend && npm install && npm run dev                          # by hand, frontend\n"
             "python train.py --csv data/my.csv ; python predict.py --text \"...\" ; streamlit run app.py   # CLI and Streamlit", 7.5),
        H2("B.2 Using the screens"),
        N("**Detect** (`/app`): enter an optional headline and the text (at least five words), press \"Detect fake news\" or Ctrl+Enter; read the verdict, confidence, probability chart and cue words.",
          "**Batch check** (`/app/batch`): drop a CSV (up to 25 MB, 20,000 rows), choose the text column, press \"Run batch detection\", inspect the table and download the results.",
          "**Model analytics** (`/app/analytics`): accuracy, macro-F1, feature reduction, confusion matrix, Firefly curve and baseline comparison of the loaded model, on its own hold-out.",
          "**Retrain** (`/app/retrain`): optionally attach a labelled CSV (text, optional title, label as REAL, PARTIALLY TRUE, FAKE, 0 to 2 or LIAR names), set fireflies (4 to 20), generations (3 to 30) and TF-IDF features (1,000 to 8,000), confirm and wait. **Retraining replaces the loaded model and its file**; keep a copy.",
          "**About** (`/app/about`): the pipeline, the meaning of the verdicts and the facts of the loaded model."),
        H2("B.3 Checks and troubleshooting"),
        P(f"`scripts/smoke_test.py` ({F.N_SMOKE} API checks), `scripts/unit_edge_tests.py` ({F.N_UNIT_LIB} library and {F.N_UNIT_API} API checks), `npm run build` (type check and build), `scripts/run_experiments.py`, `scripts/measure_api.py` and `scripts/capture_docs_screens.py` (screenshots, app running)."),
        TAB("Common problems", ["Symptom", "Cause and remedy"],
            [["\"Can't reach the detection API\" or a blank page", "Backend not running, or page opened on 127.0.0.1: run `run.bat`, open `http://localhost:5406`"],
             ["Pickle or scikit-learn error when loading the model", "The model was saved by scikit-learn 1.9: use the packages `run.bat` installs, or retrain"],
             ["HTTP 422 / 400 / 413 / 409", "Fewer than five words / unreadable or empty CSV or no label column / more than 20,000 rows or 25 MB / a retraining job is running"],
             ["Odd verdicts after retraining on true/false labels", "pandas reads a label column of only true/false as booleans (limitation L11): use REAL / FAKE or 0 / 2"],
             ["Port already in use", "Change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`"]],
            widths=[2.4, 4.3], align=["l", "l"], size=9),
    ]


def screens_blocks():
    s = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("Captured by the frontend build on the shipped demo model, trained on the synthetic template corpus: the interface is faithful, but confidences of 99 to 100 % and an accuracy of 100 % describe template-style data, not real news. "
          "Captures on the LIAR2 model are in Chapter 8; the last pair below adds the retraining confirmation (file 21) and the demo model's analytics charts."),
        PAIR([(s("01_landing_dark.png"), "Landing page, dark theme (demo model)."), (s("01_landing_light.png"), "Landing page, light theme; the demo card scores the clickbait example FAKE, 89.5 %.")], 2.8),
        PAIR([(s("02_landing_how_it_works.png"), "\"How it works\": step 2 of 4, compress with PCA."), (s("03_detect_result.png"), "Detect: clickbait example FAKE, 99.4 %, 2 ms.")], 2.8),
        PAIR([(s("04_batch_results.png"), "Batch check on six demo articles: two per class, 99 to 100 %."), (s("05_analytics.png"), "Analytics: accuracy 100 %, 596 to 57 features, PCA 136 components (95.2 %), 750 documents.")], 2.8),
        PAIR([(s("05b_analytics_charts.png"), "Analytics charts: perfect confusion matrix (50, 50, 50)."), (s("09_about.png"), "About screen of the demo model.")], 2.8),
        PAIR([(s("06_retrain.png"), "Retrain: a 60-row CSV, 10 fireflies, 6 generations."), (s("07_retrain_running.png"), "Retrain running: 60 rows, 10 x 6 evaluations.")], 2.8),
        PAIR([(s("08_retrain_done.png"), "Retrain finished: PCA 10 components, Firefly kept 3, 100 %, 10 s."), (s("21_liar2_retrain_running.png"), "LIAR2 retrain: the confirmation dialog \"Replace the current model?\" while the job starts.")], 2.8),
    ]
