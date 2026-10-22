"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import cite

_A = F.A
_D = F.DEMO


def blocks():
    return chapter3() + chapter4()


def chapter3():
    l, d = F.LAT[0], F.LAT[1]
    tt = _A["train_time_s"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether a project can be built and used with the resources at hand. For this project the question was answered partly by analysis and partly by building the system and measuring it, "
          "so most entries below carry a measured value rather than an estimate. Where a question could not be answered favourably, the entry says so."),

        H2("3.1 Technical Feasibility"),
        P("The technical risk lay in four places: whether a text pipeline of TF-IDF, stylometric features, PCA and an SVM could be fitted on an ordinary computer without a graphics processor; whether a population-based search "
          "(the Firefly algorithm) is affordable when every candidate needs a cross-validated SVM fit; whether predictions are fast enough for an interactive web page; and whether the model reaches a useful accuracy on real fact-checked news. "
          f"The development machine is {F.HARDWARE}. On that machine:"),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can the pipeline be trained on a CPU?", f"Demo corpus ({_D['n_docs']} documents, 10 fireflies x 12 generations at most): {_D['train_time_s']:.1f} s. Real statements ({F.NTRAIN:,} documents): {tt['mean']:.0f} s on average (range {min(tt['values']):.0f}-{max(tt['values']):.0f} s)", "Feasible"],
            ["Is the Firefly search affordable?", f"About {_A['n_firefly_evals']['mean']:.0f} cross-validated SVM fits per search; roughly {tt['mean'] / 60:.0f} minutes. A linear SVM on the same documents trains in {_A['ref_subsample_LinearSVC_time']['mean']:.1f} s", "Feasible, but 1,000 times dearer than a linear model"],
            ["Are predictions fast enough?", f"Server time {l['predict_server_ms']['mean']:.1f} ms per article (95th percentile {l['predict_server_ms']['p95']:.1f} ms); HTTP round trip median {l['predict_client_ms']['p50']:.1f} ms; {l['batch']['2296']['rows']:,} statements in {l['batch']['2296']['server_s']} s", "Feasible"],
            ["Does the model start quickly?", f"API ready {l['startup_s']} s after start with the {F.NTRAIN:,}-document model; {d['startup_s']} s with the demo model", "Feasible"],
            ["Is the accuracy useful?", f"On {F.NTEST:,} real test statements: accuracy {F.pm(_A['proposed_test'], 'accuracy')}, macro-F1 {F.pm(_A['proposed_test'])} (three classes, three seeds)", "Feasible as a system; accuracy is modest"],
            ["Is the model small enough to ship?", "0.81 MB (demo model) and 12.0 MB (model trained on real statements)", "Feasible"],
        ], widths=[1.7, 3.5, 1.2], size=9.5, align=["l", "l", "l"]),
        P(f"The weakest answer is the last but one. Real fact-checked statements are hard: the majority class alone scores an accuracy of {F.pct(_A['majority_test']['accuracy']['mean'])} but a macro-F1 of only {F.pm(_A['majority_test'])}, and the survey by "
          f"Dell'Oglio et al. {cite('compare')} finds LIAR-PLUS the hardest of ten datasets for nearly all models even when the labels are reduced to two classes. The optimised pipeline reaches a macro-F1 of {F.pm(_A['proposed_test'])}. "
          "Technical feasibility of building and running the system is therefore established; technical feasibility of a large accuracy gain from the Firefly search is not, and Chapter 8 reports that plainly. "
          "A smaller risk is the dependency chain: the saved model was written with scikit-learn 1.9 and an older version may not load it, so `run.bat` builds an environment with the packages in `backend/requirements.txt`."),

        H2("3.2 Economic Feasibility"),
        P("The whole software stack is open source: Python, scikit-learn, NumPy, SciPy, pandas, FastAPI, uvicorn, React, Vite and Tailwind CSS. No licence fee is payable and no cloud service is needed at run time, because the model runs in the same process as the API. "
          "The dataset used for the real measurements, LIAR2 " + cite("liar2") + ", is a public download released under the Apache-2.0 licence. The only hardware needed is an ordinary computer; no graphics card, camera or other peripheral is required."),
        P("We did not record purchase prices and we do not quote money figures. The running cost is the electricity of a computer for a training run of a few minutes and for interactive use, and since no text leaves the machine there is no per-call charge "
          "and no privacy exposure to a third party. The one real cost of the method is time: the Firefly search is the most expensive step of training (Section 3.1), so a team without spare minutes should lower the number of fireflies and generations, "
          "which the Retrain screen allows."),

        H2("3.3 Operational Feasibility"),
        P("A user starts the whole system by double-clicking `run.bat`. The script checks for Python 3.11 or newer and Node.js 20 or newer, creates (or rebuilds) the virtual environment, installs the backend packages and the frontend packages on the first run, "
          "starts the API on port 8406 and the web interface on port 5406, waits until `/api/health` answers and opens the browser. The interface has a landing page and five application screens (Detect, Batch check, Model analytics, Retrain, About). "
          "A first-time user can paste an article and see a verdict immediately because a model ships with the project; a user with a labelled CSV can retrain from the same interface without a command line."),
        P("Maintenance is simple because the web layer is thin: the API contains no model logic and calls the library that the command-line scripts and the Streamlit application also use. The application is local and single-user. "
          "Its operational limits are stated on the screens: verdicts come from writing style and vocabulary and not from checking sources, which the sidebar says in the sentence \"A screening aid, not a fact-check\"."),

        H2("3.4 Schedule Feasibility"),
        P("The calendar dates of the work were not recorded in the project artefacts, so none are given. The table is a plan: the phases the work followed, in the order in which their products exist in the repository, and what each phase produced. "
          "It is not a measured timeline."),
        TAB("Project phases (plan) and their products", ["Phase", "Work", "Product"], [
            ["1", "Literature survey, base paper study, problem statement and objectives", "Batch documents 1-6"],
            ["2", "The library: cleaning, features, PCA, Firefly search, MSVM; command-line scripts and a Streamlit application", "`src/`, `train.py`, `predict.py`, `app.py`, demo model"],
            ["3", "Web layer: FastAPI endpoints and the React interface", "`backend/main.py`, `frontend/`, `run.bat`"],
            ["4", "Testing and real-data experiments on LIAR2", f"{F.N_TESTS} automated checks, `scripts/run_experiments.py`, `experiments/liar2/`"],
            ["5", "Documentation, diagrams and screenshots", "Review decks, chapter documents, report, paper"],
        ], widths=[0.7, 3.4, 2.3], size=10, align=["c", "l", "l"]),

        H2("3.5 Advantages and Constraints"),
        H3("Advantages"),
        B("Runs offline on a normal computer: no cloud account, no GPU and no licence fee.",
          f"Fast at prediction time: about {l['predict_server_ms']['mean']:.0f} ms per article inside the server and {l['batch']['2296']['rows']:,} statements in about {l['batch']['2296']['server_s']:.1f} s.",
          "Three verdicts instead of two, with the probability of every class and the sensational or credibility cue words that were noticed.",
          "Retrainable by the user from a labelled CSV, with the Firefly budget chosen on a slider.",
          "Reproducible and measured: one script regenerates every real-data number, and the analytics screen always shows the baseline next to the optimised model."),
        H3("Constraints"),
        B(f"Modest accuracy on real fact-checked statements (macro-F1 {F.pm(_A['proposed_test'])}); PARTIALLY TRUE is the weakest class (F1 {F.pm(_A['per_class_test']['PARTIALLY TRUE'], 'f1-score')}).",
          "Training with the Firefly search takes minutes and, on the data tried, did not beat simpler variants (Chapter 8).",
          "Verdicts reflect writing style and vocabulary of the training data, not the truth of a claim; no source or evidence is checked.",
          f"The displayed probabilities and the verdict disagree for {F.pct(F.LV['disagree_rate'])} of real test statements, so the confidence figure must be read with care.",
          "English text only; one local user; no authentication."),
    ]


def chapter4():
    l, d = F.LAT[0], F.LAT[1]
    fr = [
        ["FR-1", "Classify one article (headline optional, body required) as REAL, PARTIALLY TRUE or FAKE", "POST /api/predict; Detect screen", "Detect"],
        ["FR-2", "Refuse input of fewer than five words with a clear message", "422 from the API; field error in the form", "Detect"],
        ["FR-3", "Show the verdict, the confidence, the probability of each class and the response time", "Verdict badge, confidence bar, probability chart, latency chip", "Detect"],
        ["FR-4", "Show the sensational and credibility cue words found in the text", "Up to ten of each from fixed vocabularies", "Detect"],
        ["FR-5", "Offer example articles", "GET /api/samples (six demo-corpus documents; three buttons)", "Detect, Landing"],
        ["FR-6", "Preview a CSV and let the user choose the text column", "POST /api/batch/preview; guessed column; ten-row preview", "Batch check"],
        ["FR-7", "Classify every row of a CSV and show the distribution of verdicts", "POST /api/batch/run; summary cards and distribution chart", "Batch check"],
        ["FR-8", "Download the results with a verdict and confidence per row", "Results CSV returned in the response; first 50 rows shown in a sortable table", "Batch check"],
        ["FR-9", "Show model analytics: accuracy, macro-F1, features, training time, confusion matrix, Firefly curve, classification report, baseline", "GET /api/model", "Model analytics"],
        ["FR-10", "Retrain on the demo corpus or an uploaded labelled CSV with a chosen Firefly budget", "POST /api/retrain (202) and GET /api/retrain/{job_id}", "Retrain"],
        ["FR-11", "Use the new model without restarting", "Atomic file replacement and in-memory swap", "Retrain, Detect"],
        ["FR-12", "Show that the API is reachable", "GET /api/health polled every 20 s; status chip", "All app screens"],
        ["FR-13", "Explain the pipeline, the classes and how to run the system", "GET /api/model pipeline steps; About page", "About, Landing"],
        ["FR-14", "Offer light and dark themes", "Theme toggle, remembered in the browser", "All screens"],
    ]
    nfr = [
        ["NFR-1 Response time", "An article is classified fast enough to feel instant", f"Server {l['predict_server_ms']['mean']:.1f} ms mean, {l['predict_server_ms']['p95']:.1f} ms p95; HTTP round trip median {l['predict_client_ms']['p50']:.1f} ms, p95 {l['predict_client_ms']['p95']:.1f} ms (300 requests, 127.0.0.1)", "Met"],
        ["NFR-2 Throughput", "A CSV of a few thousand rows is classified in seconds", f"{l['batch']['100']['rows']} rows in {l['batch']['100']['server_s']} s; {l['batch']['1000']['rows']:,} in {l['batch']['1000']['server_s']} s; {l['batch']['2296']['rows']:,} in {l['batch']['2296']['server_s']} s", "Met"],
        ["NFR-3 Start-up", "Ready within seconds of starting", f"{l['startup_s']} s (real-data model), {d['startup_s']} s (demo model)", "Met"],
        ["NFR-4 Accuracy", "Reported on held-out data with per-class scores and a baseline", f"LIAR2 test: accuracy {F.pm(_A['proposed_test'], 'accuracy')}, macro-F1 {F.pm(_A['proposed_test'])}", "Reported; modest"],
        ["NFR-5 Input limits", "Bad input is refused with a clear sentence and changes nothing", "At least 5 words; CSV up to 25 MB and 20,000 rows; fireflies 4-20, generations 3-30, TF-IDF 1,000-8,000; at least 30 labelled rows", "Met (tested)"],
        ["NFR-6 Reliability", "A failed retrain must not break detection", "Model saved to a temporary file and renamed; one job at a time (409); the previous model stays in use on error", "Met"],
        ["NFR-7 Usability", "Usable by a non-expert, in light and dark, on narrow screens", "One start script; labelled fields, hints and error sentences; verdicts carry an icon and a word as well as a colour; sidebar becomes a drawer", "Met"],
        ["NFR-8 Privacy", "Text stays on the user's computer", "No external calls; uploads are parsed and deleted", "Met"],
        ["NFR-9 Portability", "Runs on a normal Windows PC", "Python 3.11+, Node 20+; `run.bat` for Windows; other systems untested", "Met on Windows only"],
        ["NFR-10 Maintainability", "No model logic duplicated between front ends", "API, CLI and Streamlit call the same `src/` library", "Met"],
        ["NFR-11 Testability", "Automated tests", f"{F.N_SMOKE} smoke checks and {F.N_UNIT_LIB + F.N_UNIT_API} unit and edge checks pass", "Met"],
    ]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),

        H2("4.1 Existing System and Its Limitations"),
        P("Fake news is mostly checked today by people. Professional fact-checkers examine a claim, gather evidence and publish a rating on a scale such as true, mostly true, half true, barely true, false and pants on fire; "
          "the LIAR benchmark " + cite("liar") + " is built from such ratings. The method is reliable but slow and expensive, and as the project problem statement says, fabricated news reaches large audiences before any fact-check is published. "
          "Vosoughi et al. " + cite("vosoughi") + " found that false stories spread farther and faster than true ones, which widens the gap."),
        P("Automatic detectors exist in several families " + cite("shu", "survey") + ". Classical systems use n-gram or TF-IDF features with a linear classifier " + cite("ahmed") + " or add stylistic cues " + cite("potthast") + ". "
          "Recent systems use transformer embeddings with a neural classifier, as in the base paper " + cite("base") + ", or tune a transformer with Bayesian optimisation " + cite("hybrid") + ". "
          "Their limitations, as the survey in Chapter 2 shows, are that most are binary (real or fake) and so have no place for a half-true claim, that the strongest depend on large pre-trained models and a graphics processor, that accuracy is often reported without the cost of reaching it, "
          "and that many are research code rather than an application a non-expert can run."),

        H2("4.2 Proposed System and Its Advantages"),
        P("The proposed system is a feature-based optimised multi-class SVM packaged as a web application, TruthGlow. Text is cleaned and turned into TF-IDF and stylometric features, reduced by PCA, and classified by an RBF multi-class SVM whose feature subset and parameters (C and gamma) are chosen "
          "by the Firefly algorithm. It has an explicit PARTIALLY TRUE class. The user pastes an article, uploads a CSV, inspects the analytics or retrains the model on their own labelled data."),
        B("Three verdicts, including PARTIALLY TRUE, with the probability of every class and the cue words that were noticed.",
          f"Light: no graphics processor, a 12 MB model, about {l['predict_server_ms']['mean']:.0f} ms per article.",
          "Complete: single detection, batch detection, analytics and retraining in one tool, with a command-line and a Streamlit alternative.",
          "Private: runs locally; no text leaves the computer.",
          "Honest: the analytics screen shows the unoptimised baseline beside the optimised model and the Firefly curve, so the user can see what the optimisation did."),
        P(f"The advantages above concern cost, size and usability. They do not include a higher accuracy: on real data the optimised pipeline scores a macro-F1 of {F.pm(_A['proposed_test'])}, the same, within the seed-to-seed variation, as the default SVM on the same features "
          f"({F.pm(_A['pca_svc_default_test'])}) and below a logistic regression on plain TF-IDF ({F.pm(_A['ref_full_LogisticRegression_test'])} when trained on all {F.NTRAIN_FULL:,} statements)."),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements and how they are realised", ["ID", "Requirement", "Realisation", "Screen"], fr,
            widths=[0.55, 2.45, 2.35, 0.95], size=9, align=["c", "l", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and the measured outcome", ["Requirement", "Target", "Measured or evidence", "Status"], nfr,
            widths=[1.05, 1.6, 2.95, 0.75], size=9, align=["l", "l", "l", "c"]),
        P("The accuracy requirement is a reporting requirement, not a target number. Objective 6 asks for accuracy, precision, recall and F1 against unoptimised baselines, and it is met; no figure such as \"95 %\" was set in advance because the achievable level on real fact-checked statements "
          "was not known before the experiments."),

        H2("4.5 Hardware Requirements"),
        P("The system was developed and measured on one machine. We report its specification and do not invent a minimum; a smaller machine may work but was not tested."),
        TAB("Hardware used for development and measurement", ["Item", "Specification"], [
            ["Processor", "Intel Core i5-12500, 6 cores, 12 threads, 3.0 GHz base"],
            ["Memory", "15.7 GB RAM"],
            ["Graphics processor", "none used (the Intel UHD 770 on the processor is not used)"],
            ["Storage", "12.0 MB for the real-data model, 0.81 MB for the demo model; about 24 MB for the LIAR2 CSV files used in the experiments"],
            ["Display", "any browser window; the screenshots were taken at 1440 x 900"],
            ["Operating system", "Windows 11 Pro"],
        ], widths=[1.7, 4.6], size=10.5, align=["l", "l"]),

        H2("4.6 Software Requirements"),
        TAB("Software used", ["Component", "Version", "Role"], [
            ["Python", "3.11.9 (3.11 or newer required by `run.bat`)", "Language of the library and the API"],
            ["scikit-learn", "1.9.1", "TF-IDF, scaler, PCA, SVC, metrics, cross-validation " + cite("sklearn")],
            ["NumPy, SciPy, pandas, joblib", "2.4.6, 1.17.1, 3.0.6, as installed", "Arrays, sparse matrices, CSV reading, model file"],
            ["FastAPI, uvicorn, python-multipart", "0.159.1, 0.54.0", "Web service and uploads"],
            ["Streamlit, Plotly (optional)", "per `requirements.txt`", "The original Streamlit interface"],
            ["Node.js and npm", "24.19.0 and 11.17.0 (Node 20 or newer required)", "Build and development server of the web interface"],
            ["React, TypeScript, Vite, Tailwind CSS", "18.3, 5.9, 8, 4", "Web interface"],
            ["TanStack Query, react-router, Recharts, GSAP, Framer Motion", "5, 7, 3, 3, current", "Data fetching, routing, charts, motion"],
            ["Playwright with Chrome", "installed for the screenshots", "Capturing the output screens"],
        ], widths=[2.0, 2.0, 2.3], size=10, align=["l", "l", "l"]),

        H2("4.7 User Roles"),
        P("The system has no accounts, passwords or permissions, because it runs on the user's own computer and serves only that computer. Two kinds of use can nevertheless be told apart. The **reader or analyst** pastes articles, runs batches and reads the analytics. "
          "The **model owner** retrains the model with a labelled CSV and reads the analytics to judge the new model. Both use the same screens. The consequence of having no roles is that anyone who can reach the port can retrain and replace the model; "
          "multi-user operation would need authentication and is listed under future scope."),

        H2("4.8 Constraints and Assumptions"),
        N("The text is English; the stop-word list, the lexicons and the training data are English.",
          "The input is plain text of at least five words; markup is not interpreted.",
          "A labelled CSV has a text column (or title and text, statement, news or content) and a label column; labels are REAL, PARTIALLY TRUE or FAKE, the numbers 0, 1, 2, or the LIAR names.",
          "Only one retraining job runs at a time, and retraining replaces the model file the API was started with.",
          "The verdict is a screening aid based on style and vocabulary; it does not check sources or evidence.",
          "Training on real data was done with a 3,000-statement subsample because the Firefly search needs thousands of SVM fits; larger training sets were not tried with the search."),
    ]
