"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a=None, b=None):
    return F.src(rel, a, b)


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("Excerpts from the repository (`8.ProjectCode`) in the state in which the results of this report were measured; the complete files are in `backend/`, `agrivision/` and `scripts/`."),
        H2("A.1 Bearer token and current user (`backend/main.py`)"),
        CODE(src("backend/main.py", 94, 110) + "\n\n" + src("backend/main.py", 123, 130), 7.5),
        H2("A.2 Detection endpoint (`backend/main.py`)"),
        CODE(src("backend/main.py", 306, 340), 7),
        H2("A.3 Feature extraction (`agrivision/inference.py`)"),
        CODE(src("agrivision/inference.py", 87, 100), 7.5),
        H2("A.4 Scoring, ranking and confidence (`agrivision/inference.py`)"),
        CODE(src("agrivision/inference.py", 108, 145), 7),
        H2("A.5 Compact CNN (`agrivision/train.py`)"),
        CODE(src("agrivision/train.py", 25, 52), 7.5),
        H2("A.6 Evaluation metrics (`scripts/run_experiments.py`)"),
        CODE(src("scripts/run_experiments.py", 62, 95), 7),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements and start"),
        B(f"A Windows PC (measurements in this report: {F.HARDWARE}). Python 3.10 or newer on the PATH, Node.js 20 or newer, a current Chrome or Edge and internet for the first installation.",
          "Double-click `run.bat` in `8.ProjectCode`. It (1) checks Python and Node.js, (2) creates `.venv`, or rebuilds one copied from another PC, and installs `backend/requirements.txt` (FastAPI, uvicorn, python-multipart, Flask, Pillow, NumPy, reportlab), "
          "(3) runs `npm install` in `frontend/` when `node_modules` is missing, (4) starts the API on port 8416 with `PYTHONHASHSEED=0` and waits for `/api/health`, (5) starts the web application on port 5416 and opens `http://localhost:5416`. "
          "Two minimised windows hold the servers; close them to stop. Ports are read from `.env` (`BACKEND_PORT`, `FRONTEND_PORT`).",
          "Sign in with the demo account `demo@agrivision.ai` / `demo1234`, or register. The interactive API documentation is at `http://127.0.0.1:8416/docs`.",
          "The original Flask pages can be started separately with `cd agrivision && python app.py` (port 5000); they share the database and the uploads."),
        CODE(".venv\\Scripts\\python -m uvicorn backend.main:app --port 8416      # backend by hand (set PYTHONHASHSEED=0)\ncd frontend && npm install && npm run dev    # frontend by hand (npm run build for the production bundle)", 7.5),
        H2("B.2 Using the screens"),
        N("**Disease guide** (`/encyclopedia`, no sign-in): search the 38 classes; open one for symptoms, lifecycle, severity, three treatments and prevention.",
          "**Detect** (`/detect`): choose the crop (or 'general'), drop or select a leaf photograph (JPG, PNG, JPEG, WEBP up to 10 MB) or use the camera, press 'Diagnose now'. A crop with fewer than three candidate classes (blueberry, cherry, orange, peach, bell pepper, raspberry, soybean, squash, strawberry) currently fails with 'could not be read as an image'; use 'general' instead.",
          "**Result** (`/result/<id>`): read the class, severity, the heuristic score and top-3 list, symptoms and treatments; export the scan as CSV or PDF, print it or share the link. Treat the answer as a first screen only.",
          "**History** (`/history`): search by disease or crop, filter all, diseased or healthy, open or delete a scan, export all scans as CSV.",
          "**Dashboard** and **Analytics**: totals, healthy and high-severity counts, disease rate, recent scans, distribution of diseases, severity and a timeline.",
          "**Profile** (`/profile`): name, region, language (English, Hindi, Marathi) and preferred crops; the language also switches from the top bar. The theme button changes between light and dark."),
        H2("B.3 Experiments, checks and troubleshooting"),
        CODE("python scripts/run_experiments.py data                     # cache the PlantDoc photographs at 224 px\nset PYTHONHASHSEED=0 && python scripts/run_experiments.py heuristic\npython scripts/run_experiments.py cnn --seed 42 [--protocol shipped]\npython scripts/run_experiments.py mobilenet --seed 42\npython scripts/run_experiments.py baseline  &&  python scripts/run_experiments.py aggregate\npython scripts/smoke_test.py ; python scripts/edge_tests.py ; python scripts/measure_api.py ; python scripts/make_report_facts.py", 7.5),
        P(f"`smoke_test.py` runs {F.N_SMOKE} API checks, `edge_tests.py` runs {F.N_EDGE} unit and API checks and `measure_api.py` times the API; each starts its own server on a spare port with a throw-away database. "
          "TensorFlow must be imported before scikit-learn in the same process on this machine, so each training command is its own process. To use a trained network, copy `plantdoc_cnn.h5` and `labels.json` to `agrivision/models/` and restart the API: "
          "`/api/health` then reports `trained_model: true`."),
        TAB("Common problems", ["Symptom", "Cause and remedy"],
            [["'API offline' chip, blank lists", "Backend not running: start it with `run.bat` and refresh"],
             ["Port already in use", "Change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` and restart"],
             ["HTTP 400 'could not be read as an image' for a valid photograph", "The chosen crop has fewer than three candidate classes (defect D1): choose 'general'"],
             ["HTTP 413", "The photograph is larger than 10 MB: use a smaller one"],
             ["HTTP 401 after a week", "The token expired (7 days): sign in again"],
             ["Different answers for the same photograph after a restart", "Start the backend with `PYTHONHASHSEED=0`, as `run.bat` does"],
             ["TensorFlow 'DLL initialization failed'", "Import TensorFlow before scikit-learn or FastAPI in that process"],
             ["Plain fonts", "The font stylesheet loads without blocking; offline the system fonts are used"]],
            widths=[2.6, 3.9], align=["l", "l"], size=9),
    ]


def screens_blocks():
    s = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The remaining screens of the application, captured at 1440 x 900 pixels with real data: the demo farmer's account holds scans of PlantDoc test photographs, uploaded through the API for the capture and removed afterwards. "
          "The engine behind every result is the heuristic."),
        PAIR([(s("01_landing_dark.png"), "Landing page, dark theme."), (s("01_landing_light.png"), "Landing page, light theme.")], 2.8),
        PAIR([(s("02_landing_how_it_works.png"), "Landing page: how it works."), (s("03_register.png"), "Register page.")], 2.8),
        PAIR([(s("06_login.png"), "Login page with the demo-account hint."), (s("04_encyclopedia.png"), "Disease guide listing the 38 classes.")], 2.8),
        PAIR([(s("05_disease_detail.png"), "Disease detail card (tomato late blight)."), (s("12_profile.png"), "Profile page: language and preferred crops.")], 2.8),
        PAIR([(s("14_dashboard_light.png"), "Dashboard in the light theme."), (s("17_dashboard_hindi.png"), "Dashboard with the Hindi interface; body text is still English.")], 2.8),
    ]
