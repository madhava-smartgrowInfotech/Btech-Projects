"""Chapters 3 and 4: Feasibility Study; System Requirements and Analysis (VeriVision AI)."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def _feasibility():
    L = F.LATENCY
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the proposed system can be built and used with the resources at hand. This chapter answers that question for four aspects and sums up the "
          "advantages and constraints. Every statement about speed or resources is backed by a measurement taken on the development machine described in Section 4.5."),

        H2("3.1 Technical Feasibility"),
        P(f"The technical question is whether four CNN routes, a fusion rule, Grad-CAM and a robustness check can be trained and served on a computer without a GPU. The development machine has an Intel Core i5-12500 "
          f"(6 cores, 12 threads), 15.7 GB of RAM and no GPU. All four routes were fine-tuned on it: about 24 minutes for A1, 22 for A2, 13 for C and 53 for B (wall-clock times from file timestamps; the machine was shared with other jobs, "
          f"so these are upper bounds). Serving was equally feasible. With the models loaded once at start-up, a verdict from all four routes plus fusion takes a median of {L['predict_s']:.2f} s, and a full analysis including three Grad-CAM overlays and "
          f"three robustness variants takes {L['analyze_s']:.2f} s (median of 8 runs on a 32-pixel image; {L['analyze_photo_1024px']['median']:.2f} s for a 1,024-pixel photograph). "
          "The earlier estimate of 10 to 60 seconds in the project README turned out to be pessimistic."),
        P(f"The software stack is mature and open: PyTorch [{R['pytorch']}] and torchvision for the models, pytorch-grad-cam [{R['pytorch_grad_cam']}] for the explanations, scikit-learn [{R['sklearn']}] for the metrics, "
          f"Flask [{R['flask']}] for the server and React with Vite for the interface. The pinned versions are listed in `requirements.txt` and were installed and exercised together (Python 3.11.9, torch 2.14.1 CPU build). "
          "The technical risks were the CPU training time, which limited the training subset to 6,000 images, and the small image size of the data, which limits what the models can learn; both are reported as limitations."),

        H2("3.2 Economic Feasibility"),
        P("The system needs no paid component. Every library is open source, the pretrained weights are the freely distributed ImageNet weights shipped with torchvision, the datasets are public "
          "(CIFAKE through a Hugging Face copy; a second public image set for the cross-domain probe), and the whole project ran on an existing personal computer. There is no hosted service, no "
          "per-request fee and no GPU rental. The principal cost is therefore team time. No cost figures are given because none were recorded."),
        P("One licensing note matters for any wider use. The CIFAKE copy used here carries no licence field on its Hugging Face card, while the Kaggle original and other copies are tagged MIT; the second dataset used for the probe is tagged MIT."),

        H2("3.3 Operational Feasibility"),
        P(f"The operational question is whether a person who is not a developer can use the result. The interface has six pages (landing, sign-in, analysis, model insights, how it works and system status). "
          f"A user signs in with the demo account, drops in an image and, within a couple of seconds, sees the verdict with a confidence word, the votes of the four routes, the heat maps and the robustness check. "
          f"Upload limits are enforced (PNG, JPEG or WebP, up to {F.UPLOAD_LIMIT_MB} MB), errors are returned as plain messages, and a status page names any missing model file. "
          "The application runs locally with two commands, the uploaded image is held in memory and discarded after the reply, and nothing leaves the machine. "
          f"Automated checks give confidence that this works: {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} unit and API tests and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass. "
          "What operational feasibility does not cover is use by a real organisation: there is no user study, no multi-user account system and no hosted deployment."),

        H2("3.4 Schedule Feasibility"),
        P("The work followed the order of the pipeline. The table lists the phases, the output of each and the one duration that was measured; calendar dates are not given because they were not recorded."),
        TAB("Project phases and outputs", ["Phase", "Work", "Output", "Measured duration"], [
            ["1", "Study of the base paper, HEDGE and the empirical study; choice of the four-route design", "Design and parameters in `app/config.py`", "-"],
            ["2", "Application: Flask API, inference, fusion, Grad-CAM, robustness, React interface", "Running application on ports 8414 and 5414", "-"],
            ["3", "Real data preparation: class-balanced CIFAKE subset and cross-domain probe set", "6,000 / 1,200 / 2,000 images and 600 probe images", "-"],
            ["4", "Fine-tuning of the four routes on the CPU", "Four checkpoints and training histories", "A1 24 min, A2 22 min, B 53 min, C 13 min"],
            ["5", "Evaluation: held-out test, ablation, threshold sweep, calibration, robustness, probe", "`experiments/cifake/metrics.json`", "283 ms per image, all routes, batched"],
            ["6", "Testing and timing", f"{F.PYTEST_PASSED} unit tests, {F.SMOKE_PASSED} smoke checks, latency file", f"Unit tests {F.PYTEST_SECONDS:.0f} s"],
            ["7", "Screens, diagrams and documentation", "19 screenshots, 11 diagrams, 15 charts, this report", "-"],
        ], widths=[0.6, 2.5, 2.1, 1.1], align=["c", "l", "l", "l"], size=9.5),
        P("The schedule was feasible because the models are small. A larger backbone or the full 100,000-image training set would not have been, which is the main reason the training subset is only 6% of the available training images."),

        H2("3.5 Advantages and Constraints"),
        B("**Advantages.** No GPU or paid service; a response in about two seconds for a full analysis; four independent opinions with visible weights; explanation and stability check next to the verdict; images stay on the machine; "
          "every parameter in one configuration file; reproducible training and evaluation scripts.",
          "**Constraints.** CPU-only training limited the data to a 6,000-image subset and 3 to 5 epochs; the data are 32-pixel images from one generator; each route was trained once; the machine had to be shared; "
          "the base paper's face-specific method could not be reproduced within these resources and is not implemented."),
    ]


def _requirements():
    L = F.LATENCY
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter describes the situation the system is meant to improve, the system that was built, and the requirements it was built to meet, with the hardware, software and user roles involved."),

        H2("4.1 Existing System and its Limitations"),
        P("Today an image of doubtful origin is checked in one of four ways."),
        B(*lit.EXISTING_SYSTEM),
        P("These approaches have the following limitations."),
        B(*lit.LIMITATIONS_EXISTING),
        P(f"The research detectors discussed in Chapter 2 [{R['hedge']}], [{R['empirical']}] improve on manual inspection but typically return a score or a label, depend on large models and GPU hardware, and are seldom packaged so that an analyst can see the disagreement between models, the explanation and the stability of the answer together."),

        H2("4.2 Proposed System and its Advantages"),
        P("VeriVision AI is a local web application. The user uploads an image; the server validates it, runs four fine-tuned CNN routes, fuses their logits with two deterministic gating rules, "
          "and returns the verdict, the confidence word, the per-route votes, Grad-CAM overlays for three routes and a robustness consistency score. An insights page shows the stored evaluation of the models."),
        B(*lit.PROPOSED_APPROACH),
        P("Its advantages over the existing practice are: the combined output is available on one screen; the fusion is transparent and configurable; the explanation is generated for the class that was predicted; "
          "the stability check shows when a verdict depends on fragile cues; the tool runs offline on a CPU; and the evaluation is published inside the application, including the numbers that are unflattering."),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements and where they are met", ["ID", "Requirement", "Realised by"], [
            ["FR1", "The user shall sign in with a demo account and receive a time-limited token.", "`POST /api/auth/login` (signed token, 12 h)"],
            ["FR2", f"The user shall upload a PNG, JPEG or WebP image of at most {F.UPLOAD_LIMIT_MB} MB; invalid files shall be rejected with a clear error.", "`app/preprocessing.py`, 400 / 413 responses"],
            ["FR3", "The system shall classify the image as REAL or AI_GENERATED with a probability and a confidence word.", "`app/ensemble.py`, High / Moderate / Low"],
            ["FR4", "The system shall show the vote, confidence and weight of each of the four routes.", "`POST /api/analyze` branches"],
            ["FR5", "The system shall produce Grad-CAM overlays for the predicted class.", "`app/explainability.py` (routes A1, B, C)"],
            ["FR6", "The system shall re-test the image under JPEG, resize and blur and report a consistency k/n.", "`app/robustness.py`"],
            ["FR7", "The system shall show the stored evaluation of the models (metrics, confusion matrix).", "`GET /api/insights`, Insights page"],
            ["FR8", "The system shall report its health and the presence of each model file.", "`GET /health`, Status page"],
            ["FR9", "The system shall offer a JSON verdict endpoint that needs no token.", "`POST /api/predict`"],
            ["FR10", "The developer shall be able to prepare data, train, and evaluate the routes by script.", "`scripts/prepare_*.py`, `train_*.py`, `run_cifake_experiments.py`"],
        ], widths=[0.55, 3.7, 2.05], align=["c", "l", "l"], size=9.5),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements, targets and measured status", ["Quality", "Requirement", "Status"], [
            ["Performance", "A verdict within a few seconds on a CPU", f"Median {L['predict_s']:.2f} s (verdict) and {L['analyze_s']:.2f} s (full analysis), 8 runs each"],
            ["Reliability", "Clear errors for bad input or missing models", "JSON errors 400, 401, 413, 500, 503; Status page; error paths tested"],
            ["Security and privacy", "Authenticated analysis, upload checks, no external calls", "Signed bearer token; image decoded in memory; nothing stored or sent out"],
            ["Usability", "One screen for verdict, votes, heat map and robustness", "React interface, light and dark themes; 19 screens captured"],
            ["Maintainability", "All tunables in one place; automated tests", f"`app/config.py`; {F.PYTEST_PASSED} unit tests, {F.SMOKE_PASSED} smoke checks"],
            ["Portability", "Run on a plain Windows or Linux PC", "CPU build of PyTorch; Dockerfile and compose file supplied"],
            ["Accuracy", "Useful in-domain accuracy with measured limits", f"{F.pct(F.ENS['accuracy'])} on the held-out subset; chance on another source (Chapter 8)"],
        ], widths=[1.2, 2.5, 2.6], align=["l", "l", "l"], size=9.5),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware used and recommended", ["Item", "Used for development and all measurements", "Recommended minimum"], [
            ["Processor", "Intel Core i5-12500, 6 cores / 12 threads", "Any modern 4-core CPU"],
            ["Memory", "15.7 GB RAM", "8 GB for serving; 16 GB for training"],
            ["Graphics", "None (CPU inference and training)", "Not required"],
            ["Storage", "Four checkpoints 138 MB; `data` folder 720 MB", "2 GB free"],
            ["Network", "Not needed after installation", "Needed once to download weights and packages"],
        ], widths=[1.1, 3.0, 2.2], align=["l", "l", "l"], size=10),

        H2("4.6 Software Requirements"),
        TAB("Software stack", ["Component", "Version used", "Purpose"], [
            ["Operating system", "Windows 11", "Host"],
            ["Python", "3.11.9", "Backend, training, evaluation"],
            ["PyTorch / torchvision", "2.14.1 (CPU) / 0.29.1", "Models, training, inference"],
            ["pytorch-grad-cam", "1.5.7", "Grad-CAM overlays"],
            ["Flask", "3.1.3", "API and classic pages"],
            ["scikit-learn, NumPy, pandas, Pillow, OpenCV (headless)", "1.9.1, 2.4.6, 3.0.6, 13.0.0, 5.0.0.93", "Metrics, arrays, tables, image I/O, degradations"],
            ["Matplotlib, ReportLab", "3.11.2, 5.1.0", "Charts and the generated PDF report"],
            ["pytest", "9.1.1", "Automated tests"],
            ["Node.js, Vite, React", "Node 24; Vite 8, React 19", "Web interface"],
            ["Browser", "Chrome (tested)", "Interface"],
        ], widths=[2.4, 1.9, 2.0], align=["l", "l", "l"], size=10),

        H2("4.7 User Roles"),
        TAB("User roles", ["Role", "Description", "Permissions"], [
            ["Analyst (demo user)", "Anyone checking an image", "Sign in, upload, read verdict, votes, heat maps and robustness; read insights and status"],
            ["Developer", "Maintains the models and data", "Run the preparation, training and evaluation scripts; edit `app/config.py`"],
            ["API client", "Another program", "`POST /api/predict` for a JSON verdict (no token)"],
        ], widths=[1.5, 2.0, 2.8], align=["l", "l", "l"], size=10),
        P("There is a single demo account for local use; the product has no registration or database of users, so role separation is conceptual rather than enforced."),

        H2("4.8 Constraints"),
        B("The detector is only as good as its training data: 32-pixel images from one generator.",
          "The verdict is a probability from a statistical model and not proof of origin; it should be combined with other evidence.",
          f"The Grad-CAM heat map is produced for the predicted class and is an aid to reading, not a faithful account of the decision.",
          "Images smaller than 8 x 8 pixels, files that do not decode as RGB and files larger than the limit are refused.",
          "The application assumes a trusted local network and a single user session at a time."),
        FIG(F.fig("f02_branch_metrics.png"), "Accuracy, F1 and ROC-AUC of the four routes and the ensemble on the 2,000 held-out images (single run).", 5.2),
    ]


def blocks():
    return _feasibility() + _requirements()
