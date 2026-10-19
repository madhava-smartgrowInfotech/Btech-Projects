"""Chapters 3 (feasibility) and 4 (requirements and analysis)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

FUNCTIONAL = [
    ["FR1", "Sign in with the demo account (email and password) and sign out.", "Must"],
    ["FR2", "Upload a chest X-ray by file picker or drag and drop; accept PNG, JPG and JPEG up to 8 MB.", "Must"],
    ["FR3", "Validate the upload and explain the failure: no file, empty name, unsupported type, too large, unreadable image.", "Must"],
    ["FR4", "Show a preview of the chosen image before it is analysed.", "Should"],
    ["FR5", "Preprocess the image and classify it as Normal, Bacterial Pneumonia or Viral Pneumonia with a probability for each class.", "Must"],
    ["FR6", "Generate a Grad-CAM heatmap overlay for the predicted class.", "Must"],
    ["FR7", "Display the result: class badge, confidence, three probability bars, original and heatmap side by side, and a blend control.", "Must"],
    ["FR8", "Store every result (record plus the original and heatmap images) and make it viewable later.", "Must"],
    ["FR9", "List past scans with thumbnail, file name, prediction, confidence and date; search, filter by class, sort and paginate.", "Should"],
    ["FR10", "Export the history as CSV.", "Could"],
    ["FR11", "Delete a stored scan together with its two image files, after confirmation.", "Could"],
    ["FR12", "Show dashboard statistics: totals, class distribution, average confidence, recent scans, scans per day.", "Should"],
    ["FR13", "Print a result report and download the heatmap image.", "Could"],
    ["FR14", "Warn on the detect and result screens when no trained model is loaded (Demo Mode).", "Must"],
    ["FR15", "Handle an unknown result id with a clear not-found state.", "Must"],
    ["FR16", "Explain the five-step pipeline and show the project abstract and technology on an About page.", "Should"],
    ["FR17", "Show the clinical disclaimer on every screen.", "Must"],
    ["FR18", "Offer light and dark themes and remember the choice.", "Could"],
]

NONFUNCTIONAL = [
    ["Usability", "Every screen usable by keyboard alone; layout works from 360 px to 1440 px; light and dark themes; reduced-motion respected.", "scripts/verify_ui.py (6 viewport and theme combinations, focus, dialogs)"],
    ["Performance", "One analysis completes in a few seconds on a CPU-only desktop.", "Section 7.7: measured per-stage and end-to-end latency"],
    ["Reliability", "A failed upload never leaves a half-stored scan; errors are returned as JSON with a readable message.", "tests/test_api.py (corrupt, oversize, unsupported)"],
    ["Security", "Signed HttpOnly cookie, 401 for protected routes, no path traversal, parameterised SQL, upload size and type limits.", "tests/test_api.py, tests/test_auth_tokens.py"],
    ["Portability", "Runs on Windows 10/11 with Python 3.10 or 3.11 and Node.js 18+; one script starts everything.", "run.bat, docs/03_HOW_TO_RUN.md"],
    ["Maintainability", "Model code, API layer, database layer and front end are separate; behaviour is covered by automated tests.", "73 pytest tests, 25 smoke-test checks"],
    ["Privacy", "Images and records stay on the local machine; the new interface loads fonts and scripts from its own bundle and makes no third-party calls.", "Code review of frontend/index.html and src"],
    ["Honesty of output", "The interface must state when the model is untrained and must show a medical disclaimer.", "Demo-mode badge and alerts; footer text"],
]


def blocks():
    ch3 = [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical feasibility"),
        P("Every component of the system is available as free, mature open-source software, and the whole stack ran on one ordinary desktop. "
          f"TensorFlow/Keras {n(19)} provides the network, OpenCV {n(35)} the image operations and CLAHE {n(11)}, FastAPI {n(34)} and Flask {n(36)} the "
          "web layers, SQLite the database and React with Vite the front end. The model is deliberately small (about 0.59 million parameters), so "
          "it can be trained and served without a GPU. The only technical risks identified were (i) the absence of a trained model in the original "
          "repository, which was removed by training one on the public dataset, and (ii) the Grad-CAM implementation, which works for the project's "
          "own CNN but cannot reach inside the nested backbones of the transfer-learning builder; the deployed model therefore uses the custom CNN "
          "(Section 6.6)."),
        H2("3.2 Economic feasibility"),
        P("No licence, cloud service or special hardware was purchased. The dataset is public (CC BY 4.0) and the frameworks are open source. Training "
          "used a desktop that already existed. The recurring cost of running the system is the electricity of one computer; there is no per-scan fee. "
          "A clinical deployment would add costs that are outside this project: regulatory approval, clinical validation, integration with hospital "
          "systems and security hardening."),
        TAB("Cost view", ["Item", "Cost to the project", "Remark"], [
            ["Software, frameworks, libraries", "None", "Open-source licences"],
            ["Dataset", "None", "Kermany et al., CC BY 4.0 [3], [4]"],
            ["Training hardware", "None additional", "Existing desktop, CPU only"],
            ["Hosting", "None", "Runs locally on ports 8312 (API) and 5312 (UI)"],
            ["Clinical validation, certification", "Not budgeted", "Out of scope (Section 1.6)"],
        ], widths=[2.4, 1.6, 2.4]),
        H2("3.3 Operational feasibility"),
        P("The interface was designed so that a non-specialist can use it without training: one primary action on the detect screen, a plain-language result, "
          "a visible disclaimer and explicit empty, loading and error states. Start-up is a single script (`run.bat`) that creates the Python environment, "
          "installs dependencies and opens the browser. Operation requires no database administration, because the SQLite file is created on first run. "
          "Operational limits are that the demo account is shared and that scans are stored on the local disk without backup."),
        H2("3.4 Schedule feasibility"),
        P("The work divides into phases with clear dependencies: (1) data acquisition and checking, (2) preprocessing and model definition, (3) training and "
          "evaluation, (4) API layer, (5) user interface, (6) testing and (7) documentation. Phases 4 and 5 depend only on the interface of the model code, so "
          "they proceeded while training ran. The decisive schedule fact is the cost of an experiment: one epoch of the custom CNN takes about four minutes "
          "on the CPU used, so a full training run is a few hours and only a handful of experiments could be afforded (Chapter 8). The project proposal also "
          "listed U-Net segmentation, which would have needed pixel-level lung masks and a second training phase; that scope did not fit and is deferred."),
        H2("3.5 Legal and ethical considerations"),
        P("The training data are anonymised paediatric radiographs released for research under CC BY 4.0. The system stores uploaded images locally and "
          "sends nothing to third parties. Because medical decisions are involved, the interface repeats on every page that the output is a screening aid and "
          "not a diagnosis, and the demo-mode alert warns when predictions come from an untrained network."),
        H2("3.6 Advantages and constraints"),
        B("**Advantages:** open and inspectable code; no GPU required; small model; end-to-end path with explanation; reproducible by one script; extensive automated tests.",
          "**Constraints:** CPU-only training limits experimentation; single-source paediatric data; no external validation; U-Net segmentation absent; demonstration-level authentication."),
    ]

    ch4 = [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing system and its limitations"),
        P("In current clinical practice a clinician or radiologist reads each chest radiograph by eye. Research code that classifies radiographs exists "
          f"{n(1, 5, 6)} but is distributed as notebooks or scripts. The project started from a Flask prototype with upload, prediction, Grad-CAM and history pages "
          "(`app.py`, `templates/`) that ran in Demo Mode, because no trained weights were shipped."),
        B("**Manual reading:** slow when staff are scarce, tiring, and variable between readers.",
          "**Accuracy-only research models:** report a label or a score with no visual justification and no record of past cases.",
          "**The original prototype:** no login, no dashboard, no search or export, no deletion, no automated tests, and no trained model, so its predictions were meaningless.",
          "**Segmentation and uncertainty** are discussed in the literature but not available in any ready-to-run form."),
        H2("4.2 Proposed system and its advantages"),
        P("The proposed system keeps the original Flask code untouched and adds a FastAPI service and a React interface over the same model, Grad-CAM and "
          "database modules, trains a real model on public data, and adds a demo login, dashboard, history tools and tests."),
        B("A trained three-class classifier instead of an untrained demonstration network.",
          "A Grad-CAM overlay and three probabilities for every scan, so each prediction can be checked against the image.",
          "A persistent history with search, filter, sort, export and deletion, and a dashboard summarising it.",
          "Clear validation messages and honest states (Demo Mode banner, loading, empty, error, not found).",
          "A reproducible training script and test suite so the numbers in this report can be regenerated."),
        H2("4.3 Functional requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Priority"], FUNCTIONAL, widths=[0.5, 4.8, 0.8], align=["c", "l", "c"]),
        H2("4.4 Non-functional requirements"),
        TAB("Non-functional requirements and how each is verified", ["Quality", "Requirement", "Evidence"], NONFUNCTIONAL, widths=[1.1, 3.2, 2.0], size=9.5),
        H2("4.5 Hardware requirements"),
        TAB("Hardware", ["Item", "Used for development and measurement", "Minimum suggested"], [
            ["Processor", "12th Gen Intel Core i5-12500", "Any recent 4-core x86-64 CPU"],
            ["Memory", "15.7 GB RAM", "8 GB (16 GB for training)"],
            ["Graphics", "None used (CPU only)", "Not required"],
            ["Storage", "About 2 GB for the Python environment, 1.2 GB for the training dataset", "5 GB free"],
            ["Display", "1440 x 900 reference; layout verified from 360 px", "Any modern browser"],
        ], widths=[1.3, 3.0, 2.0]),
        H2("4.6 Software requirements"),
        TAB("Software", ["Layer", "Software"], [
            ["Operating system", "Windows 11 Pro (development); Windows 10/11 supported by `run.bat`"],
            ["Language and runtime", "Python 3.11 (3.10 or 3.11 supported), Node.js 18 or newer"],
            ["Deep learning", "TensorFlow / Keras, NumPy, scikit-learn, matplotlib"],
            ["Image processing", "OpenCV (headless), Pillow"],
            ["Web back end", "FastAPI with Uvicorn, python-multipart, python-dotenv; Flask (original UI)"],
            ["Database", "SQLite (Python standard library)"],
            ["Front end", "React 19, Vite, React Router, Framer Motion, GSAP, Recharts, lucide-react, the Neo Brutal Grid design kit"],
            ["Testing", "pytest, FastAPI TestClient, Playwright (user-interface checks)"],
        ], widths=[1.6, 4.7]),
        H2("4.7 User roles"),
        TAB("Roles", ["Role", "Description", "Access"], [
            ["User (clinician or student)", "Signs in with the demo account, uploads scans, reviews results and history", "All screens of the web application"],
            ["Developer", "Trains and exports a model, runs tests, starts the servers", "Command line (`scripts/`, `run.bat`)"],
        ], widths=[1.7, 3.0, 1.6]),
        H2("4.8 Constraints"),
        B("The model can only be as good as its training data: one paediatric source with file-name-derived pathogen labels.",
          "Inputs are limited to PNG or JPEG files of at most 8 MB.",
          "The system is a research prototype and must not be used for clinical decisions.",
          "One shared demo account; there is no user registration."),
    ]
    return ch3 + ch4
