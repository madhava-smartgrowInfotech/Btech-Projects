"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .ch9_10 import src


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) at the state in which the results of this report were measured. Docstrings are kept; nothing is shortened inside a listing."),
        H2("A.1 Segmentation and normalisation (`sign_language_app/preprocessing.py`)"),
        CODE(src("sign_language_app/preprocessing.py", 47, 102), 8),
        H2("A.2 The network (`sign_language_app/model.py`)"),
        CODE(src("sign_language_app/model.py", 18, 50), 8),
        H2("A.3 The recogniser (`sign_language_app/recognizer.py`)"),
        CODE(src("sign_language_app/recognizer.py", 16, 86), 8),
        H2("A.4 Training core (`sign_language_app/train.py`)"),
        CODE(src("sign_language_app/train.py", 37, 92), 8),
        H2("A.5 Recognition and collection endpoints (`backend/main.py`)"),
        CODE(src("backend/main.py", 195, 225), 8),
        CODE(src("backend/main.py", 230, 267), 8),
        H2("A.6 Browser camera (`frontend/src/lib/camera.ts`, frame grab)"),
        CODE(src("frontend/src/lib/camera.ts", 65, 91), 8),
        H2("A.7 Unit tests of the decision logic (`tests/test_recognizer.py`)"),
        CODE(src("tests/test_recognizer.py", 1, 52), 8),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows PC with a webcam and speakers (the build machine was an Intel Core i5-12500 with 15.7 GB RAM and no GPU; these are the machine's figures, not stated minimums).",
          "Python 3.10 or 3.11 on the PATH and Node.js 18 or newer.",
          "Chrome or Edge, opened on `http://localhost`: browsers allow webcam access only on `localhost` or HTTPS.",
          "An internet connection for the first installation (TensorFlow 2.15.0 and the frontend packages are large)."),
        H2("B.2 Installation and start"),
        N("Open the project folder `8.ProjectCode` and double-click `run.bat`. It creates `.venv`, runs `pip install -r requirements.txt`, installs the frontend packages and starts both servers.",
          "The browser opens `http://localhost:5316`; the API runs in its own window on port 8316 (documentation at `http://127.0.0.1:8316/docs`). The first request waits a few seconds while TensorFlow loads.",
          "To stop, press Ctrl+C in the web window and close the API window. Ports are set in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`)."),
        P("Manual start: create a virtual environment, `pip install -r requirements.txt`, then `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8316` in one terminal and `cd frontend && npm install && npm run dev` in another. "
          "The original desktop application starts with `python run.py`."),
        H2("B.3 Preparing data and a model"),
        N("**Use a public dataset.** Copy an evenly spaced subset of the Kaggle ASL Alphabet images into `data/<CLASS>/` with `python scripts/prepare_data.py [archive_dir] [per_class]` (default 250 per class), or",
          "**Collect your own.** Open *Collect data*, start the camera, pick a letter, place the hand inside the cyan box and press Capture (one image) or Burst (several). 150 to 250 images per class is a good target; vary the hand position a little.",
          "Open *Train model*. At least two classes need images. Choose epochs, batch size and learning rate (defaults 25, 32 and 0.001), press Start and watch the charts. The model, labels, history, report and confusion matrix are saved in `models/`."),
        H2("B.4 Using the screens"),
        TAB("User guide", ["Screen", "How to use it"],
            [["Dashboard", "Check that a model is ready, how many images each class has and the last test accuracy."],
             ["Recognize", "Press Start camera (allow the camera in the address bar). Show a letter inside the box and hold it for about a second: it is typed into the sentence. Use Space, Back and Clear to edit and Speak sentence to hear it. A plain background and even light give the cleanest mask."],
             ["Collect data", "Capture images for a class; the strip below shows recent captures."],
             ["Train model", "Set the hyper-parameters and start; Stop ends a run early; the best weights are kept."],
             ["Model performance", "Per-class precision, recall and F1, the confusion matrix and the training curves of the saved model."],
             ["About", "The project abstract, the pipeline steps and the base paper."]],
            widths=[1.4, 5.2], align=["l", "l"], size=10),
        H2("B.5 Running the tests"),
        CODE("""python -m pytest tests                    # 52 tests, about 4 seconds
python scripts/smoke_test.py              # 26 live API checks in a temporary copy (port 8399)
python scripts/measure_metrics.py         # re-measure accuracy, threshold curve, robustness, latency
python scripts/verify_docs.py             # check the submission documents""", 9),
        H2("B.6 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Fix"],
            [["\"Can't reach the SignSpeak server\"", "The API window is not running or is still loading TensorFlow; wait about 20 seconds or run `run.bat` again."],
             ["Camera permission message", "Allow the camera in the address bar; close other programs that use the webcam."],
             ["Port already in use", "`netstat -ano | findstr :5316`, then `taskkill /PID <pid> /F`."],
             ["\"No trained model\" on Recognize", "Train one first on the Train model screen."],
             ["Speak does nothing", "The server voice plays on this PC's speakers; if it fails, the browser voice is used."],
             ["Letters are typed wrongly", "Use a plain background and even light, keep the hand upright and inside the box, and hold the sign steady."]],
            widths=[2.2, 4.4], align=["l", "l"], size=10),
    ]


def screens_blocks():
    s = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These captures complement Chapter 8: the light theme and the phone-width layout (390x844 px) of real screens with the trained model and the 7,250-image dataset loaded."),
        FIG(s("02_landing_light.png"), "Landing page, light theme.", F.shot_w(s("02_landing_light.png"), 5.6, 3.9)),
        FIG(s("09_dashboard_light.png"), "Dashboard, light theme.", F.shot_w(s("09_dashboard_light.png"), 5.6, 3.9)),
        FIG(s("10_model_light.png"), "Model performance screen, light theme.", F.shot_w(s("10_model_light.png"), 5.6, 3.9)),
        PAIR([(s("11_mobile_dashboard.png"), "Dashboard at phone width (390x844)."), (s("12_mobile_recognize.png"), "Recognize screen at phone width (390x844).")], 2.4),
        P("At phone width the navigation collapses into a drawer and the cards stack in one column; no content is cut off and the text stays readable. The browser walk checked every screen at 360, 768 and 1440 px."),
    ]
