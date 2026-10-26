"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""
import os

from . import facts as F
from .blocks import B, CODE, H1, H2, N, P, PAIR, TAB, FIG


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


CRY = "backend/app/services/crypto.py"
LSB = "backend/app/services/lsb.py"
PIPE = "backend/app/services/pipeline.py"
MET = "backend/app/services/metrics.py"
ROB = "backend/app/services/robustness.py"
DB = "backend/app/db.py"
KEYS = "backend/app/routes/keys.py"


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` in the state in which the results were measured (whole statements; the full files are in the repository). "
          "Chapter 6 explains the design; Chapter 5 gives the database and API."),
        H2("A.1 Hybrid encryption: building and opening the bundle (`crypto.py`)"),
        CODE(src(CRY, 87, 101) + "\n\n" + src(CRY, 104, 128), 7.5),
        H2("A.2 LSB embedding and extraction (`lsb.py`)"),
        CODE(src(LSB, 24, 32) + "\n\n" + src(LSB, 35, 55), 7.5),
        H2("A.3 Send and receive pipeline (`pipeline.py`)"),
        CODE(src(PIPE, 13, 30) + "\n    ...\n" + src(PIPE, 47, 55), 7.5),
        H2("A.4 Imperceptibility measures (`metrics.py`)"),
        CODE(src(MET, 5, 21), 7.5),
        H2("A.5 Robustness attack runner (`robustness.py`)"),
        CODE(src(ROB, 76, 106), 7.5),
        H2("A.6 Database models (`db.py`)"),
        CODE(src(DB, 21, 51), 7.5),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB(f"Requirements to run {F.PRODUCT}", ["Item", "Requirement"],
            [["Operating system", "Windows 10 or 11 (the launchers `setup.bat` and `run.bat` are for Windows; the commands in B.3 work elsewhere)"],
             ["Python", "3.11 or newer (tested with 3.11.9) with *Add to PATH* ticked"],
             ["Node.js", "LTS release for the React console (tested with 24.19)"],
             ["Memory and disk", "A few hundred MB for the Python packages and `node_modules`; any laptop is sufficient"],
             ["Network", "Needed only for the first install of packages; the application runs offline afterwards"],
             ["GPU, API keys, datasets", "None needed: there is no model and no external service"]],
            widths=[1.5, 5.0], align=["l", "l"], size=10),
        H2("B.2 One-click start"),
        N("Open the folder `8.ProjectCode` and run **`setup.bat`** once. It copies `.env.example` to `.env` if needed, creates `venv`, installs `backend\\requirements.txt`, regenerates the sample covers if `data\\covers` is missing and runs `npm install` in `frontend`.",
          "Open `.env` and replace `JWT_SECRET` with a random string of at least 16 characters (the backend refuses to start with a shorter one).",
          f"Run **`run.bat`**. Two windows open (backend on port {F.API_PORT}, frontend on port {F.WEB_PORT}) and the browser opens http://localhost:{F.WEB_PORT}.",
          f"Sign in with the demo account `{F.DEMO_USER}` / `{F.DEMO_PASSWORD}` (created automatically on the first start), or choose *Create account*.",
          "To stop, close the two windows."),
        H2("B.3 Starting by hand and running the checks"),
        CODE("python -m venv venv\n"
             "venv\\Scripts\\python -m pip install -r backend\\requirements.txt\n"
             f"cd backend && ..\\venv\\Scripts\\python -m uvicorn app.main:app --host 127.0.0.1 --port {F.API_PORT}     # API\n\n"
             "cd frontend && npm install && npm run dev                                          # console\n\n"
             f"venv\\Scripts\\python scripts\\smoke_test.py          # 21 end-to-end checks against the running API\n"
             f"venv\\Scripts\\python -m pytest -q                    # {F.PYTEST_PASSED} unit and API tests (scratch database)\n"
             "venv\\Scripts\\python ml\\eval.py                      # experiments/eval/metrics.json and summary.md\n"
             "venv\\Scripts\\python scripts\\run_experiments.py      # experiments/extra/metrics.json (about 1.5 minutes)\n"
             "venv\\Scripts\\python scripts\\measure_api.py          # API latency (API running)\n"
             "cd frontend && npm run build                         # production build of the console", 8),
        H2("B.4 Settings (`.env`)"),
        TAB("Settings that matter", ["Name", "Meaning", "Default"],
            [["BACKEND_PORT", "Port of the FastAPI server", str(F.API_PORT)],
             ["FRONTEND_PORT", "Port of the Vite development server", str(F.WEB_PORT)],
             ["DATABASE_URL", "SQLAlchemy URL of the SQLite file", "sqlite:///./data/app.db"],
             ["JWT_SECRET", "Key that signs the sign-in tokens; at least 16 characters", "placeholder, must be replaced"]],
            widths=[1.6, 3.4, 1.5], align=["l", "l", "l"], size=10),
        H2("B.5 Using the application"),
        N("**Keys.** Generate a keypair (RSA 2048, 3072 recommended, or 4096). Download the public key and give it to anyone who should send you something. To send to someone else, import their public key as a *public only* entry.",
          "**Send.** Choose the receiver's key, a file (a sample or an upload) and a cover image. The capacity bar shows an estimate. Press *Encrypt and hide*, then *Download PNG*. Send the PNG as a file; do not paste it into an application that recompresses pictures.",
          "**Analysis.** Open the message to see PSNR (above 50 dB is invisible), SSIM, MSE, the share of values changed, histograms and bit planes.",
          "**Receive.** Choose your own keypair and the stego image (one you sent, or an upload). The restored file and two matching SHA-256 values appear; download the file.",
          "**Robustness.** Select a sent message and run the tests. The page lists which attacks leave the payload intact and which destroy it. The benchmark measures quality and speed on every sample cover.",
          "**Operation log.** Review every operation with sizes, timings and metrics. Keys, passwords and file contents are never recorded."),
        H2("B.6 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and fix"],
            [["Port already in use", "Another program holds 8315 or 5315; close it or change the ports in `.env`"],
             ["Blank page or 502 from the console", "The backend window did not start; read its output (often a short `JWT_SECRET`)"],
             ["\"This cover holds only N bytes\"", "Choose a larger cover image or a smaller file"],
             ["Recipient cannot open the image", "The image was re-encoded by a messaging app or e-mail client; send it as a file or inside an archive"],
             ["\"RSA unwrap failed\"", "The selected key is not the one the message was sent to; choose the receiver's keypair"],
             ["Send page shows an error for a new account", "The account has no keys yet: open Keys, generate a keypair, then return to Send"]],
            widths=[2.2, 4.3], align=["l", "l"], size=10),
    ]


def screens_blocks():
    SH = F.shot
    inv = [["01_landing", "Landing page: headline and the measured-results tiles"], ["02_landing_features", "Landing page: how it works and features"],
           ["03_login", "Sign in and create account"], ["04_keys", "Keys (Chapter 8)"], ["05_send_form", "Send before the run (Chapter 8)"],
           ["06_send_result", "Send result (Chapter 8)"], ["07_send_capacity_blocked", "Send blocked by the capacity check (Chapter 8)"],
           ["08_analysis", "Analysis, imperceptibility measures (Chapter 8)"], ["09_analysis_histograms", "Analysis, histograms (Chapter 8)"],
           ["10_analysis_bitplanes", "Analysis, bit planes (Chapter 8)"], ["11_receive_result", "Receive, restored file (Chapter 8)"],
           ["12_receive_wrong_key", "Receive with the wrong key (Chapter 8)"], ["13_robustness_results", "Robustness, nine attacks (Chapter 8)"],
           ["14_robustness_detail", "Robustness, error-rate chart (Chapter 8)"], ["15_capacity_table", "Capacity per cover (Chapter 8)"],
           ["16_benchmark", "Benchmark rows (Chapter 8)"], ["17_log", "Operation log (Chapter 8)"], ["18_log_detail", "Log detail of one send (Chapter 8)"]]
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("Chapter 8 shows the working screens from Keys to the Operation log. The captures below complete the set: the public landing page and the sign-in page. All 18 captures were taken at 1440 x 900 from the running application with real data."),
        PAIR([(SH("01_landing.png"), "Additional screen: landing page, headline and the measured-results tiles."),
              (SH("02_landing_features.png"), "Additional screen: landing page, how it works and features.")], 2.95),
        P("The landing page is public. Its tiles repeat the headline results of the evaluation (22 round trips, mean PSNR 61.7 dB, mean SSIM 0.9990, 3.0 bits per pixel, 86 ms median unwrap and decrypt) and are labelled as measured in this repository."),
        FIG(SH("03_login.png"), "Additional screen: sign in and create account, with the demo credentials pre-filled.", F.shot_w(SH("03_login.png"), 4.6, 3.0)),
        P("The sign-in page offers the demo account and registration. The password is limited to 72 bytes because bcrypt ignores anything longer."),
        P("All 18 screens were captured in one session by `scripts/capture_screens.py` (1440 x 900, real data, fresh database); the files are in `docs/screenshots/`."),
    ]
