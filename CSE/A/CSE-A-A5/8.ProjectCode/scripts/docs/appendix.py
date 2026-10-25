"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


def _code_report():
    sc = "cipherguard/crypto/secure_channel.py"
    tr = "cipherguard/ids/train.py"
    inf = "cipherguard/ids/inference.py"
    mn = "cipherguard/api/main.py"
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` in the state in which the results were measured (excerpts of whole statements; the full files are in the repository)."),
        H2("A.1 Key derivation and authenticated encryption (`secure_channel.py`)"),
        CODE(src(sc, 46, 54) + "\n\n" + src(sc, 70, 77) + "\n\n" + src(sc, 80, 80) + "\n        ...\n" + src(sc, 86, 93)
             + "\n\n" + src(sc, 104, 104) + "\n        ...\n" + src(sc, 114, 116), 7.5),
        H2("A.2 The 1D CNN, XGBoost and the stacking meta-model (`train.py`)"),
        CODE(src(tr, 72, 99), 7.5),
        CODE(src(tr, 292, 306) + "\n    ...\n" + src(tr, 348, 360), 7.5),
        H2("A.3 Scoring and severity (`inference.py`)"),
        CODE(src(inf, 139, 153) + "\n\n" + src(inf, 159, 171), 7.5),
        H2("A.4 The encrypt and decrypt routes (`main.py`)"),
        CODE(src(mn, 276, 292) + "\n    ...\n" + src(mn, 303, 304) + "\n    ...\n" + src(mn, 314, 335), 7.5),
    ]


def code_blocks():
    if F.REPORT:
        return _code_report()
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured. Docstrings and comments are kept as they are; "
          "each range is a whole statement or method."),
        H2("A.1 Key derivation (`cipherguard/crypto/secure_channel.py`)"),
        P("HKDF-SHA256 turns the ECDH shared secret into the 32-byte AES-256 key. No salt is used and the `info` string binds the key to this application."),
        CODE(src("cipherguard/crypto/secure_channel.py", 46, 54), 8),
        H2("A.2 Authenticated encryption and decryption"),
        P("`derive_session_key` performs the ECDH exchange and the HKDF step; `encrypt` draws a random 96-bit nonce, runs AES-GCM and separates the 16-byte tag from the ciphertext; "
          "`decrypt` re-joins them and lets AES-GCM raise an exception when the tag does not verify."),
        CODE(src("cipherguard/crypto/secure_channel.py", 70, 117), 8),
        H2("A.3 One-shot encryption to the cloud's public key"),
        CODE(src("cipherguard/crypto/secure_channel.py", 131, 148), 8),
        H2("A.4 The 1D CNN (`cipherguard/ids/train.py`)"),
        CODE(src("cipherguard/ids/train.py", 72, 99), 8),
        H2("A.5 XGBoost and the stacking meta-model"),
        P("The meta-model is fitted on the validation split's two probabilities and applied to the test split; the decision threshold is 0.5."),
        CODE(src("cipherguard/ids/train.py", 292, 306), 8),
        CODE(src("cipherguard/ids/train.py", 348, 360), 8),
        H2("A.6 Scoring and severity bands (`cipherguard/ids/inference.py`)"),
        CODE(src("cipherguard/ids/inference.py", 139, 175), 8),
        H2("A.7 The score route (`cipherguard/api/main.py`)"),
        CODE(src("cipherguard/api/main.py", 137, 168), 8),
        H2("A.8 The encrypt and decrypt routes"),
        P("The encrypt route keeps the derived key in a dictionary keyed by the ephemeral public key (a demonstration shortcut); when the key is not in the cache, the decrypt route "
          "performs the real ECDH exchange with the cloud's private key. A tag mismatch surfaces as HTTP 400."),
        CODE(src("cipherguard/api/main.py", 276, 335), 8),
    ]


def _guide_report():
    cry = F.CRY["machine"]
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements and start"),
        B(f"Windows 10 or 11, about 4 GB of free memory, Python 3.10 to 3.12 (measurements used Python {cry['python']}), Node.js 18 or newer, and a current browser; internet access for the first installation only.",
          f"Double-click `run.bat` in `8.ProjectCode`: it creates `.venv`, installs `requirements.txt`, trains the models only if `models/` is empty, installs the frontend packages and starts the API "
          f"(http://127.0.0.1:{F.API_PORT}) and the React console (http://127.0.0.1:{F.WEB_PORT}). Keep the window open while using the application."),
        CODE("pip install -r requirements.txt\n"
             f"python scripts/serve.py {F.API_PORT}           # API; imports torch first (WinError 1114 otherwise)\n"
             "cd frontend && npm install && npm run dev  # console on the port in .env", 8.5),
        H2("B.2 Real-trained bundle, tests and experiments"),
        P("To serve the models trained on the real UNSW-NB15 training set, set `CIPHERGUARD_MODELS_DIR=experiments/unsw_nb15/official/models` and "
          "`CIPHERGUARD_REPORTS_DIR=experiments/unsw_nb15/official/reports` before starting `scripts/serve.py`; uploading `data/samples/real_unsw_nb15_sample_120.csv` on the Live scoring screen then shows how many verdicts agree with its labels."),
        CODE("python -m pytest tests -v                  # 26 tests: crypto, engine, API\n"
             "python scripts/smoke_test.py                # 15 checks against the running API\n"
             "python scripts/run_experiments.py           # official partition, paper protocol, domain shift\n"
             "python scripts/benchmark_crypto.py          # crypto benchmark and tamper tests\n"
             "python scripts/measure_pipeline.py --api    # combined overhead, in process and over HTTP", 8.5),
        B("**Port in use:** `netstat -ano | findstr :8305`, stop the process or change `.env`.  **HTTP 503:** model files missing; run `python -m cipherguard.ids.train`.  "
          "**Decryption failed (400):** expected after the Tamper button."),
    ]


def guide_blocks():
    if F.REPORT:
        return _guide_report()
    return _guide_full()


def _guide_full():
    cry = F.CRY["machine"]
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11, 64-bit; about 4 GB of free memory and 1 GB of disk for the virtual environment, models and the React packages.",
          f"Python 3.10 to 3.12 (the measurements in this report used Python {cry['python']}), Node.js 18 or newer for the React console, and a current browser.",
          "Internet access for the first installation only (Python packages and npm packages). The synthetic demonstration data and the trained model files are part of the repository."),
        H2("B.2 Quick start with run.bat"),
        N("Open the project folder (`8.ProjectCode`) and double-click `run.bat`. The script finds Python, creates `.venv` if it is missing, installs `requirements.txt`, trains the "
          "models only if `models/` is empty, installs the frontend packages on the first run and starts both servers.",
          f"The API listens on http://127.0.0.1:{F.API_PORT} and the React console on http://127.0.0.1:{F.WEB_PORT}; the ports are set in `.env`. The browser opens on the console.",
          f"The original single-file dashboard is still served by the API at http://127.0.0.1:{F.API_PORT}, and the interactive API documentation at `/docs`.",
          "Keep the console window open while using the application; press Ctrl+C or close the window to stop."),
        H2("B.3 Manual start"),
        CODE("pip install -r requirements.txt\n"
             "python -m cipherguard.ids.train          # only if models/ is missing\n"
             f"python scripts/serve.py {F.API_PORT}           # API; imports torch first (see the note below)\n"
             "cd frontend\n"
             "npm install\n"
             "npm run dev                               # console on the port in .env", 8.5),
        P("`scripts/serve.py` exists because, on the Windows host used for the measurements, `import torch` failed with `WinError 1114` when numpy or pandas had been imported first. "
          "Starting the API through `serve.py`, or through `run.bat`'s own virtual environment with the pinned torch 2.2.0, avoids it; `tests/conftest.py` applies the same rule to the tests."),
        H2("B.4 Using the console"),
        TAB("Console screens and what to do on each", ["Screen", "Route", "What to do"],
            [["Landing", "/", "Read the live counters and run the API terminal, which calls the real endpoints."],
             ["Live scoring", "/app", "Fill the flow form or press Simulate normal / Simulate attack; drop a CSV (<= 10 MB, <= 10,000 rows) or press Use sample; read verdict, severity and the two model scores."],
             ["Secure transfer", "/app/secure", "Type text or choose a file (<= 5 MB), press Encrypt and transmit, then Decrypt and verify at cloud; press Tamper ciphertext to see the tag check fail."],
             ["Alerts", "/app/alerts", "Filter attacks by severity and clear the list."],
             ["Model performance", "/app/performance", "Read the held-out metrics, the confusion matrix and the data-mode banner of the bundle that is being served."]],
            widths=[1.3, 1.3, 3.7], align=["l", "l", "l"], size=10),
        H2("B.5 Serving the real-trained bundle"),
        P("The models trained on the real UNSW-NB15 training set are stored in `experiments/unsw_nb15/official/`. To make the API serve them, set two environment variables "
          "before starting it; the Model performance screen then shows the real held-out numbers and the banner names the data mode."),
        CODE("set CIPHERGUARD_MODELS_DIR=experiments\\unsw_nb15\\official\\models\n"
             "set CIPHERGUARD_REPORTS_DIR=experiments\\unsw_nb15\\official\\reports\n"
             f"python scripts\\serve.py {F.API_PORT}", 8.5),
        P("`data/samples/real_unsw_nb15_sample_120.csv` holds 60 normal and 60 attack flows from the official test set; uploading it on the Live scoring screen shows how many verdicts agree "
          "with the labels in the file."),
        H2("B.6 Tests, experiments and benchmarks"),
        CODE("python -m pytest tests -v                  # 26 tests: crypto, engine, API\n"
             "python scripts/smoke_test.py                # 15 checks against the running API\n"
             "python scripts/fetch_unsw_nb15.py           # official UNSW-NB15 train/test files (needs pyarrow<18)\n"
             "python scripts/run_experiments.py           # official partition, paper protocol, domain shift\n"
             "python scripts/benchmark_crypto.py          # SecureChannel vs AES-GCM vs RSA-OAEP hybrids, tamper tests\n"
             "python scripts/measure_pipeline.py --api    # combined overhead, in process and over HTTP\n"
             "python scripts/make_real_bundle.py          # bundle + 120-flow real sample for the API\n"
             "python scripts/capture_screens.py           # regenerate docs/screenshots", 8.5),
        H2("B.7 Troubleshooting"),
        B("**Port in use:** find the process with `netstat -ano | findstr :8305` and stop it, or change the port in `.env`.",
          "**HTTP 503 from the scoring routes:** the model files are missing; run `python -m cipherguard.ids.train`.",
          "**`WinError 1114` while importing torch:** import torch before numpy/pandas, or start through `scripts/serve.py`.",
          "**Parquet files cannot be read:** install `pyarrow<18` (a newer pyarrow requires NumPy 2).",
          "**Decryption failed (400):** expected after the Tamper button, or when the ephemeral public key does not belong to the envelope."),
    ]


def screens_blocks():
    shots = [
        ("01_landing-dark.png", "Landing page (dark theme): live counters and a terminal that calls the real API.", "The landing page shows the product name, the engine status and live numbers read from the running API."),
        ("02_landing-light.png", "Landing page (light theme).", "The same page in the light theme; the theme choice is remembered in the browser."),
        ("04_batch-scoring.png", "Batch CSV scoring of the bundled 120-row synthetic sample.", "A CSV is scored in one request; the panel shows rows scored, attacks and normal counts, the share flagged, agreement with the CSV label and a paged table with the two model scores."),
        ("05_session-charts.png", "Session charts: attack versus normal and the confidence distribution.", "Charts summarise everything scored in the current browser session."),
        ("07_secure-transfer-tampered.png", "Secure transfer: a flipped ciphertext byte is rejected.", "After pressing Tamper ciphertext the cloud's tag check fails and the API answers 400; the screen reports that decryption was rejected."),
        ("08_alerts.png", "Alerts screen populated by the batch.", "Each attack verdict is appended to the alert list with time, severity, confidence, key features and both model scores."),
    ]
    out = [H1("APPENDIX C: ADDITIONAL SCREENS"),
           P("These screens complete the set of real captures of the running application (1440 x 900, Chromium). The screens used in Chapter 8 are not repeated here. "
             "Screens 01 to 09 were taken with the shipped, synthetic-trained bundle.")]
    if F.REPORT:
        keep = [shots[2], shots[3], shots[4], shots[5]]
        out.append(P("The four screens below complete the set of real captures of the running application (1440 x 900, shipped synthetic-trained bundle); the screens used in Chapter 8 are not repeated."))
        for k in (0, 2):
            out.append(PAIR([(F.shot(keep[k][0]), keep[k][1]), (F.shot(keep[k + 1][0]), keep[k + 1][1])], 2.9))
        return out
    for i, (fn, cap, text) in enumerate(shots, 1):
        out.append(H2(f"C.{i} {cap.split(':')[0].rstrip('.')}"))
        out.append(P(text))
        out.append(FIG(F.shot(fn), cap, F.shot_w(F.shot(fn), 5.2, 3.6)))
    return out
