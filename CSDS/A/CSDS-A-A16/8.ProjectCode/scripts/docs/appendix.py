"""Appendices A (important code), B (installation and user guide) and C (additional screens) for Mosaic."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


ML = "backend/app/ml/"
INF = ML + "inference.py"
CNN = ML + "classifier_model.py"
GAN = ML + "gan_model.py"
SYN = ML + "synthesize_compound.py"
FIN = ML + "train_final_classifier.py"
TGAN = ML + "train_gan.py"
ANA = "backend/app/routers/analyze.py"
SEC = "backend/app/security.py"


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode/backend/app` in the state in which the results were measured (whole statements; the full files are in the repository)."),
        H2("A.1 Face crop to scores: preprocessing and `analyze_image_bytes()` (`ml/inference.py`)"),
        CODE(src(INF, 40, 81), 7.5),
        H2("A.2 The conditional generator (`ml/gan_model.py`)"),
        CODE(src(GAN, 4, 26), 7.5),
        H2("A.3 Synthesising compound-emotion faces (`ml/synthesize_compound.py`)"),
        CODE(src(SYN, 23, 46), 7.5),
        H2("A.4 Training the 18-output classifier (`ml/train_final_classifier.py`)"),
        CODE(src(FIN, 29, 33) + "\n    ...\n" + src(FIN, 56, 78), 7.5),
        H2("A.5 The analysis endpoint (`routers/analyze.py`)"),
        CODE(src(ANA, 28, 68), 7.5),
        H2("A.6 Password hashing and tokens (`security.py`)"),
        CODE(src(SEC, 8, 30), 7.5),
    ]


def guide_blocks():
    a, w = F.API_DEFAULT_PORT, F.WEB_PORT
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        P("A Windows 10 or 11 PC (or a recent Linux), Python 3.10 or newer, Node.js with npm, and a current browser. No GPU is needed: the three training stages take 30 to 60 minutes on a CPU, and a request takes a few tens of milliseconds. "
          "About 1 GB of disk space is enough for the packages, the FER2013 pickles (58 MB) and the checkpoints (11 MB). "
          "The repository has no `run.bat` or `setup.bat` and no `.env.example`; the steps below are those of `README.md`, with the corrections found while documenting the project."),
        H2("B.2 Backend set-up"),
        CODE("cd backend\npython -m venv .venv\n.\\.venv\\Scripts\\activate        # Windows\npip install -r requirements.txt", 8.5),
        P("**Keep `bcrypt==4.0.1`.** Version 5 of `bcrypt` is incompatible with `passlib 1.7.4`: registration then fails with a server error, and the automated tests fail at `hash_password`. "
          "The `requirements.txt` pin avoids this; if you reuse a Python installation that already has a newer `bcrypt`, install `bcrypt==4.0.1` into the virtual environment. "
          "A virtual environment copied from another computer (for example one built for a different Python version) will not work; create a new one."),
        H2("B.3 Training the models (one time)"),
        P("Place `train.pt` and `test.pt` (the FER2013 pickles from the `Jeneral/fer-2013` mirror) in `backend/data/`, then run:"),
        CODE("python -m app.ml.run_pipeline", 8.5),
        P("The pipeline trains the backbone, the cEmoGAN and the final classifier and writes `stage1_backbone.pt`, `generator.pt`, `classifier_final.pt` and `training_log.txt` to `backend/checkpoints/`. "
          "The three stages can also be run one at a time with `python -m app.ml.train_classifier_stage1`, `python -m app.ml.train_gan` and `python -m app.ml.train_final_classifier`. "
          "Without `classifier_final.pt` the API starts, but `/api/health` reports `model_loaded: false` and any request that contains a face fails with HTTP 500."),
        H2("B.4 Starting the API"),
        CODE(f"uvicorn app.main:app --reload --port {a}", 8.5),
        P(f"Interactive documentation is at `http://localhost:{a}/docs`. The CORS list admits only the console origins `http://localhost:{w}` and `http://127.0.0.1:{w}`. "
          "Set the environment variable `MOSAIC_SECRET_KEY` to a long random value before any use beyond a demonstration."),
        H2("B.5 Starting the console"),
        CODE("cd frontend\nnpm install\nnpm run dev                       # http://localhost:3000\n\n# production build (what the screenshots in this report use)\nnpm run build\nnpm start -- -p 3000", 8.5),
        P(f"The console finds the API through `NEXT_PUBLIC_API_URL` (default `http://localhost:{a}/api`, set in `frontend/.env.local`). The variable is fixed at build time; after changing it, restart `npm run dev` or rebuild. "
          "If port 8000 is already used by another program, start the API on another port and set the variable to match, for example `NEXT_PUBLIC_API_URL=http://localhost:8116/api`."),
        H2("B.6 Using Mosaic"),
        N("Open the console. The landing page introduces the product; choose **Get started**.",
          "Create an account with a name, an e-mail address and a password of at least six characters, or log in. You are taken to **Analyze a face**.",
          "On the **Upload** tab drop an image or click to browse; on the **Webcam** tab allow the camera and capture a frame. The image is sent to the service at once.",
          "Read the result: the dominant emotion and its confidence; a bar chart of the seven basic emotions; and the six highest of the eleven compound emotions.",
          "If the message *No face was detected in that image* appears, use a clearer, front-facing and larger photograph: very small faces are not found by the detector.",
          "Open **History** in the side bar for the saved analyses, most recent first, with the dominant emotion, time and confidence. Hover a row and use the bin icon to delete it.",
          "Use **Log out** at the bottom of the side bar to end the session."),
        H2("B.7 Running the automated tests"),
        CODE("cd backend\npython -m pytest tests -q", 8.5),
        P("The suite uses a temporary SQLite database. API tests that need a face are skipped when `data/test.pt` is absent, and model-dependent tests are skipped when `classifier_final.pt` has not been trained."),
        H2("B.8 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and remedy"],
            [["Registration or login returns HTTP 500", "`bcrypt` 5 with `passlib`: install `bcrypt==4.0.1`"],
             ["`/api/health` shows `model_loaded: false`", "`classifier_final.pt` is missing: run `python -m app.ml.run_pipeline` (or the final stage) and restart the API"],
             ["Port 8000 is already in use", "start uvicorn on another port and rebuild or restart the console with `NEXT_PUBLIC_API_URL` set to it"],
             ["The console loads but every call fails", "the API is not running, or the console origin is not in the CORS list (`localhost:3000` or `127.0.0.1:3000`)"],
             ["Reloading the page with F5 sends you to the log-in page", "known behaviour of the route guard: navigate with the side-bar links instead of reloading, and log in again if needed"],
             ["The analysed face shows a broken thumbnail", "known defect: the console requests the relative thumbnail path from its own origin; the image itself is at `/api/media/thumbs/<id>.jpg` on the API"],
             ["A small FER2013 image reports no face", "the Haar detector needs a face of at least 40 pixels and prefers more; enlarge the image (two to three times) before uploading"],
             ["Uploading a non-image file shows 'Analysis failed'", "the API returns HTTP 500 for undecodable files; upload JPEG or PNG"],
             ["`InconsistentVersionWarning` or `torch.load` FutureWarning in the log", "informational: the checkpoints are loaded with the default `weights_only` setting of the installed PyTorch"]],
            widths=[2.5, 4.0], align=["l", "l"], size=9.5),
    ]


def screens_blocks():
    SH = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These captures complete the set of screens of Chapter 8. All were taken at 1440 by 900 pixels from the running application (production build of the console, API on port 8116) with an account registered through the registration page. "
          "The faces are real FER2013 test images enlarged five times onto a grey canvas, or, where stated, faces produced by the cEmoGAN generator."),
        PAIR([(SH("01_landing_hero.png"), "Landing page: hero with the animated particle canvas and the call to action."),
              (SH("02_landing_features.png"), "Landing page: the four product features (compound states, multi-label scores, generative augmentation, history).")], 3.0),
        P("The landing page presents the product claim, *See every emotion, not just one*. The feature cards describe compound emotions, simultaneous scores across basic and compound categories, generative augmentation during training and a saved history. "
          "The text is marketing copy of the product; Chapter 8 states what the measurements show about the compound categories."),
        PAIR([(SH("03_landing_how_it_works.png"), "Landing page: the three steps and the ribbon of compound-emotion names."),
              (SH("04_login.png"), "Log-in page: e-mail and password fields.")], 3.0),
        P("The three steps are capture a face, run the model (an 18-way multi-label classifier that scores 7 basic and 11 compound emotions in a single pass) and read the breakdown. The log-in page asks for an e-mail address and a password and links to registration."),
        PAIR([(SH("05_register.png"), "Registration page before input."),
              (SH("06_register_filled.png"), "Registration page filled in with the demonstration account (the password field is masked).")], 3.0),
        P("Registration needs a name, an e-mail address and a password of at least six characters. After a successful registration the service returns a token and the console opens the analysis page."),
        PAIR([(SH("07_analyze_empty.png"), "Analysis page before any image: upload area and the placeholder results panel."),
              (SH("19_webcam_tab.png"), "Analysis page re-opened from the side bar; the Webcam tab was not exercised in this run, the image shows the Upload tab.")], 3.0),
        P("The left panel offers Upload and Webcam tabs and a drop zone; the right panel reads *Your results will appear here*. The side bar shows the signed-in user and the Log out button. "
          "The webcam path was not tested because the capture was made with an automated browser; only the file-upload path was exercised."),
        PAIR([(SH("10_result_sad.png"), "Result for a real FER2013 face labelled sad: dominant emotion Sad."),
              (SH("11_result_fear.png"), "Result for a real FER2013 face labelled fear: dominant emotion Fear.")], 3.0),
        P("In both captures the dominant basic emotion agrees with the dataset label and all compound bars stay at about 0 to 1 %. "
          "The small image to the left of the dominant emotion is the face thumbnail returned by the API; it renders as a broken image in the console (known defect)."),
        PAIR([(SH("13_result_surprise_misread.png"), "Result for a real FER2013 face labelled surprise, read as Fear."),
              (SH("15_result_gan_angrily_disgusted.png"), "Result for a cEmoGAN-generated face conditioned on angrily disgusted: dominant Angry, compound bars about 1 %.")], 3.0),
        P("The first capture is a misclassification: a face labelled surprise is scored Fear (52 %) with Surprise second, in line with the confusion between these two classes reported in Chapter 8. "
          "The second is generator output, not a real photograph; the classifier reads it as Angry and gives each compound class only about 1 %, so even a synthetic compound face does not make a compound emotion dominant."),
    ]
