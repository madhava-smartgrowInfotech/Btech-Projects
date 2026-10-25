"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import cite

_L = F.LATENCY
_SINGLE = _L["predict_single_fraud_example"]
_BATCH = _L["predict_batch_20_rows"]
_STATS = _L["dataset_stats"]
_HEALTH = _L["health"]
_TRAIN_S = {m: F.SEEDS[m]["elapsed_sec"]["mean"] for m in ("classical", "sa", "qa")}
_PIPE_S = F.FULL["pipeline_seconds"]
_ENS, _SAS, _QS, _PCD = (F.SAVED[k] for k in ("ensemble", "sa", "qa", "classical"))
_BB = F.BASE_BAL


def _r(full, short):
    """Full text for the chapter documents, compact text for the full report (F.REPORT)."""
    return short if F.REPORT else full


def _sz(full, short=9.5):
    return short if F.REPORT else full


def blocks():
    return chapter3() + chapter4()


# =====================================================================================================================
def chapter3():
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P(_r("A feasibility study asks whether a project can be built, run and maintained with the resources at hand. For SecurePay AI the question was answered partly by analysis and "
          "partly by building the system and measuring it on the development machine, so most entries below carry a measured value rather than an estimate. Where a question could "
          "not be settled with the data and hardware available to the team, the entry says so.",
          "Feasibility was settled partly by analysis and partly by building the system and measuring it on the development machine, so most entries carry a measured value; "
          "where a question could not be settled with the data and hardware available, the entry says so.")),

        H2("3.1 Technical Feasibility"),
        P(_r("The technical risk lay in four places: whether a restricted Boltzmann machine classifier could be trained on an ordinary processor without a graphics card or a quantum "
          "computer; whether the three training strategies of the base paper "
          f"{cite('base')} could be reproduced in a form that runs in seconds; whether imbalance could be handled with a pipeline built from standard libraries; and whether a "
          "scoring interface could be put in front of the models with a response time acceptable for a payment decision. The development machine is a desktop with an Intel Core "
          "i5-12500 processor (6 cores, 12 threads), 15.7 GB of RAM and no graphics processor in use, running Windows 11. On that machine:",
          "The technical risk lay in four places: training a restricted Boltzmann machine classifier without a graphics card or quantum computer, reproducing the three training "
          f"strategies of the base paper {cite('base')} in a form that runs in seconds, handling imbalance with standard libraries, and serving scores fast enough for a payment decision. "
          "The development machine is a Windows 11 desktop with an Intel Core i5-12500 (6 cores, 12 threads) and 15.7 GB of RAM, with no graphics processor in use:")),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can a GRBM classifier be trained without special hardware?",
             f"numpy implementation; 20 epochs take about {_TRAIN_S['classical']:.1f} s (PCD), {_TRAIN_S['sa']:.1f} s (SAS) and {_TRAIN_S['qa']:.1f} s (QS) on 6,400 training rows", "Feasible"],
            ["Is the simulated quantum sampler usable?",
             "classical simulation of a transverse-field tunnelling flip inside the SA sweeps; no quantum processor is involved", "Feasible, but only quantum-inspired"],
            ["Is the trained model accurate enough to be useful?",
             f"ensemble accuracy {F.pct(_ENS['accuracy'])}, precision {F.pct(_ENS['precision'])}, recall {F.pct(_ENS['recall'])}, F1 {F.pct(_ENS['f1'])} on {F.SPLIT['test'][0]:,} held-out synthetic rows", "Feasible on synthetic data"],
            ["Do all three trainers give a usable decision at 0.5?",
             f"SAS F1 {F.pct(_SAS['f1'])} and QS F1 {F.pct(_QS['f1'])}; the shipped PCD model flags almost every row (accuracy {F.pct(_PCD['accuracy'])}, recall {F.pct(_PCD['recall'])})", "Partly: PCD needs a threshold or retraining"],
            ["Can the data pipeline be built from standard libraries?",
             f"pandas, scikit-learn and imbalanced-learn; the whole 39,000-row pipeline runs in {_PIPE_S:.1f} s", "Feasible"],
            ["Can predictions be served fast enough?",
             f"median {_SINGLE['median_ms']:.1f} ms and 95th percentile {_SINGLE['p95_ms']:.1f} ms per single check; {_BATCH['median_ms']:.1f} ms for a 20-row CSV (Flask development server, 127.0.0.1)", "Feasible"],
            ["Can a modern interface be built without a database?",
             f"React and Vite front end ({F.FRONTEND_LINES:,} lines of source) over {F.N_ENDPOINTS} Flask routes; state lives in CSV, pickle and JSON files", "Feasible for a prototype"],
        ], widths=[1.9, 3.3, 1.2], size=_sz(10), align=["l", "l", "l"]),
        P(_r("Two technical risks were not removed. First, the base paper's real dataset is proprietary, so the project depends on a synthetic generator and its results cannot be "
          "carried over to real card traffic. Second, the base paper reports hours of training for the annealing-based trainers; here the same trainers finish in seconds because "
          "the sampler is a short heuristic approximation (10 sweeps, 16 reads and a 3,000-row subsample per epoch), which is a different and weaker experiment.",
          "Two risks were not removed: the base paper's real dataset is proprietary, so results rest on a synthetic generator and cannot be carried over to real card traffic; and its hours of "
          "annealing-based training become seconds here only because the sampler is a short heuristic approximation (10 sweeps, 16 reads, a 3,000-row subsample per epoch), a weaker experiment.")),

        H2("3.2 Economic Feasibility"),
        P(_r("The project was built entirely from free, open-source software on a computer the team already owned, so no purchase, licence or cloud fee was needed. The qualitative "
          "comparison with the setup of the base paper is the more useful way to read the economics, and no monetary figures are given because none were measured.",
          "The project used only free, open-source software on a computer the team already owned, so no purchase, licence or cloud fee was needed. No monetary figures are given because none were measured; the comparison with the base paper's setup is qualitative.")),
        TAB("Cost drivers: this project against the base paper's setup", ["Item", "This project", "Base paper's setup"], [
            ["Quantum processing time", "none; the sampler is simulated on the CPU", "paid cloud access to D-Wave quantum processors through the Leap programme"],
            ["Training data", "synthetic file generated locally in a few seconds", "145 million real transactions from a payment company"],
            ["Software", "Python, Flask, React, scikit-learn, imbalanced-learn, XGBoost, Matplotlib (all open source)", "Julia package for RBM training and D-Wave client libraries"],
            ["Hardware", "one desktop CPU, 15.7 GB RAM", "workstation plus quantum cloud service"],
            ["Training time", f"about {_TRAIN_S['classical']:.0f}-{max(_TRAIN_S.values()):.0f} s per model", "2 minutes, 4 hours and 1.8 hours reported"],
            *([] if F.REPORT else [["Running cost of the service", "one Python process; no per-request fee", "not reported"]]),
        ], widths=[1.5, 2.5, 2.4], size=_sz(10), align=["l", "l", "l"]),
        P(_r("The main economic risk is hidden in what is saved: a deployment at a real bank would need real labelled data, a security review, monitoring and a staffed review queue, "
          "none of which are part of this project and none of which are costed here.",
          "The saving hides a risk: a real deployment would need real labelled data, a security review, monitoring and a staffed review queue, none of which are part of this project or costed here.")),

        H2("3.3 Operational Feasibility"),
        P(_r("Operationally the system has to be usable by two kinds of people: a merchant or analyst who wants to check one transaction, and a risk-operations user who wants to screen "
          "a file, look at patterns and understand the models. The React interface covers both with six screens (dashboard, verify, bulk verification, analytics, model comparison "
          "and a retraining lab) and a landing page. A single `run.bat` starts both servers on ports 8304 and 5304. Results are shown as a score, a risk band and a plain-language "
          "recommended action (approve, challenge with 3-D Secure, decline and alert), so a user does not need to know how a Boltzmann machine works.",
          "Two kinds of people must be served: a merchant or analyst checking one transaction, and a risk-operations user screening a file and studying the models. The React interface covers both with six screens "
          "(dashboard, verify, bulk verification, analytics, model comparison, retraining lab) and a landing page, and one `run.bat` starts both servers on ports 8304 and 5304. "
          "Results are a score, a risk band and a plain-language action (approve, challenge with 3-D Secure, decline and alert).")),
        B(*_r(["**Setup effort:** install Python packages with one `pip install -r requirements.txt`, install front-end packages with `npm install`, then run `run.bat`; no database to configure.",
          "**Maintenance:** models are three pickle files and three JSON histories; the Model lab screen retrains them in seconds.",
          "**Failure handling:** when the backend is down the dashboard shows an offline state and a bulk upload with a bad file shows an error message instead of a crash.",
          "**Operational gaps:** there is no login, no audit trail and no alert delivery; these would be needed before real use."],
          ["**Setup and maintenance:** one `pip install -r requirements.txt`, one `npm install`, then `run.bat`; no database; the models are three pickle files and three JSON histories that the Model lab retrains in seconds.",
          "**Failure handling and gaps:** an offline dashboard state and a readable bulk-upload error exist; there is no login, audit trail or alert delivery, all needed before real use."])),

        H2("3.4 Schedule Feasibility"),
        P(_r("The work was organised in five overlapping phases. The week ranges below are the planned allocation for a semester project; they are plans, not recorded dates.",
          "Five overlapping phases; the week ranges are the planned allocation for a semester project, not recorded dates.")),
        TAB("Planned project phases", ["Phase", "Planned weeks", "Main outputs"], [
            ["1. Study and requirements", "1-2", "base paper reading, literature survey, objectives, problem statement"],
            ["2. Data and pipeline", "3-4", "synthetic generator, one-hot, z-score, correlation filter, undersampling, feature selection"],
            ["3. Models and training", "5-7", "GRBMC, PCD, SA and quantum-inspired samplers, evaluation, retraining lab"],
            ["4. Application", "7-10", "Flask API, React interface, bulk screening, analytics, model comparison"],
            ["5. Measurement and documentation", "10-12", "experiments, smoke test, latency, diagrams, reports"],
        ], widths=[2.1, 1.1, 3.2], size=_sz(10.5, 9.5), align=["l", "c", "l"]),
        P(_r("The plan was feasible because each phase depended only on the previous one and the heaviest computation, a full training run, takes seconds. The schedule risk was the "
          "interface work, which was rebuilt once with a new React front end on top of the original Flask page without changing any existing route.",
          "Each phase depended only on the previous one and a full training run takes seconds; the schedule risk was the interface, rebuilt once as a React front end over the original Flask routes.")),

        H2("3.5 Advantages and Constraints"),
        H3("3.5.1 Advantages"),
        B("No quantum hardware, GPU, paid service or proprietary data is needed to run or retrain the system.",
          f"Fast scoring: a median of {_SINGLE['median_ms']:.0f} ms per transaction and {_BATCH['median_ms']:.0f} ms for a 20-row file on the development machine.",
          "A complete working path from data generation to a decision screen, with a read-only API smoke test that passes "
          f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks.",
          "Every number in the project documents is regenerated by scripts (`run_experiments.py`, `measure_latency.py`), so results can be re-checked."),
        H3("3.5.2 Constraints"),
        B("All results come from a synthetic, balanced dataset; they say how the pipeline behaves, not how it would perform on real card traffic.",
          "The quantum sampler is a classical simulation; nothing here supports a claim about quantum advantage.",
          f"Simple baselines are better on the same data: logistic regression F1 {F.pct(_BB['Logistic Regression']['f1'])}, random forest {F.pct(_BB['Random Forest']['f1'])} and XGBoost {F.pct(_BB['XGBoost']['f1'])} against {F.pct(_ENS['f1'])} for the ensemble.",
          f"The batch-prediction route skips feature scaling because of a swallowed exception; on a fresh batch accuracy is {F.pct(F.SERVING['as_served_no_scaling']['ensemble']['accuracy'])} as served and {F.pct(F.SERVING['with_scaling']['ensemble']['accuracy'])} when scaling is applied.",
          "The Flask development server, absent authentication and file-based state limit the system to a single-user prototype."),
    ]


# =====================================================================================================================
def chapter4():
    base_tab = [
        ["PCD (classical)", *(str(x) for x in F.BASE_TABLE["PCD"][:4]), F.BASE_TABLE["PCD"][4]],
        ["SAS (simulated annealing)", *(str(x) for x in F.BASE_TABLE["SAS"][:4]), F.BASE_TABLE["SAS"][4]],
        ["QS (quantum sampling)", *(str(x) for x in F.BASE_TABLE["QS"][:4]), F.BASE_TABLE["QS"][4]],
    ]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P(_r("This chapter describes the situation the project starts from, the system it proposes, and the requirements that system has to meet. Requirement identifiers (FR for "
          "functional, NFR for non-functional) are referred to again in the design and testing chapters.",
          "This chapter describes the starting situation, the proposed system and its requirements; FR and NFR identifiers are used again in the design and testing chapters.")),

        H2("4.1 Existing System and its Limitations"),
        H3("4.1.1 How fraud is screened today"),
        P("Card issuers and merchants traditionally screen transactions with rule engines: a transaction is flagged when fixed conditions fire, such as a high amount, a card that "
          "is not present, a country that does not match the card, or an unusual hour. Flagged transactions are declined or sent to an analyst. Research systems replace the rules "
          "with classifiers. Published studies compare logistic regression, support vector machines, random forests and boosted trees "
          f"{cite('bhatt', 'rfpaper', 'shi')}, handle imbalance with SMOTE {cite('smote')} or undersampling {cite('tomek', 'fernandez')}, and combine models by fusion "
          f"{cite('cfa')}. The base paper {cite('base')} adds a different family, the restricted Boltzmann machine classifier trained with annealing-based samplers."),
        TAB("Reported results of the base paper (its Table 1, real data, test set)", ["Trainer", "Accuracy %", "Precision %", "Recall %", "F1 %", "Training time"],
            base_tab, widths=[2.0, 0.9, 0.9, 0.8, 0.7, 1.1], size=_sz(10.5, 9.5), align=["l", "c", "c", "c", "c", "c"]),
        H3("4.1.2 Limitations of the existing approaches"),
        B("**Static rules** cannot adapt to new fraud behaviour, are easy for fraudsters to probe, and raise false alarms that block genuine customers.",
          "**Accuracy-led evaluation** hides the problem: with fraud at about 0.013 % of the base paper's transactions "
          f"{cite('base')} or 3.5 % of IEEE-CIS {cite('cfa')}, a model that never flags anything looks excellent.",
          "**Resampling pitfalls:** the base paper found SMOTE and Tomek links poor when the fraud class was extremely small and fell back on manual undersampling.",
          "**Reproducibility:** the base paper's data is proprietary and its best trainers needed hours on a simulator or paid quantum cloud time.",
          "**No operational layer:** most studies end in a notebook; there is no interface that returns a risk band for a live transaction."),

        H2("4.2 Proposed System and its Advantages"),
        H3("4.2.1 Proposed system"),
        P(_r("SecurePay AI is a Flask and React application around a Gaussian-Bernoulli RBM classifier. The data pipeline one-hot encodes the merchant category and channel, z-scores "
          "the 24 numeric columns, filters columns with correlation above 0.95, undersamples to a 50/50 set, keeps the 18 features that a random forest ranks highest and splits "
          "80/20 with stratification. Three classifiers are trained: PCD with 200 hidden units and batches of 512, simulated-annealing sampling with 65 hidden units and batches of "
          "32, and a quantum-inspired sampler with the same shape. The three fraud probabilities are averaged; the label is fraud above 0.5, and the risk band is low below 0.4, "
          "medium from 0.4 to 0.7 and high above 0.7, which map to approve, challenge with 3-D Secure, and decline and alert.",
          "SecurePay AI is a Flask and React application around a Gaussian-Bernoulli RBM classifier. The pipeline one-hot encodes merchant and channel, z-scores the 24 numeric columns, "
          "filters correlation above 0.95, undersamples to 50/50, keeps the 18 features a random forest ranks highest and splits 80/20. Three classifiers are trained (PCD with 200 hidden units and batches of 512; "
          "simulated-annealing and quantum-inspired samplers with 65 hidden units and batches of 32); their fraud probabilities are averaged, the label is fraud above 0.5, and the risk band is low below 0.4, "
          "medium from 0.4 to 0.7 and high above 0.7 (approve, challenge with 3-D Secure, decline and alert).")),
        H3("4.2.2 Advantages over the existing approaches"),
        B(*_r(["Runs on a CPU; no quantum cloud access or proprietary data is required.",
          "Returns a score, a band and an action together with the probability of each of the three models, so a user can see where the models disagree.",
          "Supports single checks, CSV bulk screening with metrics when a label column is present, analytics over the dataset, a model comparison view and an in-app retraining lab.",
          "Every experiment (baselines, resampling strategies, five seeds, a 1 % fraud variant, serving path, latency) is a script that regenerates its numbers."],
          ["Runs on a CPU; no quantum cloud access or proprietary data is required.",
          "Returns a score, a band, an action and the probability of each of the three models, so a user can see where they disagree.",
          "Offers single checks, CSV bulk screening, analytics, model comparison and an in-app retraining lab; every experiment is a script that regenerates its numbers."])),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements and where they are implemented", ["ID", "Requirement", "Implemented in"], [
            ["FR-1", "Show dataset size, class balance and fraud patterns by merchant, channel, hour, amount and card signals", "`GET /api/dataset_info`, `/api/dataset_stats`; Dashboard and Analytics pages"],
            ["FR-2", "Generate a synthetic transaction dataset of a chosen size", "`POST /api/generate_dataset` (500-50,000 rows per class); Model lab"],
            ["FR-3", "Preprocess the data: one-hot, z-score, correlation filter, balancing (manual, SMOTE or Tomek) and top-k feature selection", "`POST /api/preprocess`; Model lab"],
            ["FR-4", "Train the three RBM classifiers with a chosen number of epochs and hidden units and record per-epoch metrics", "`POST /api/train`, `GET /api/train_status`; Model lab"],
            ["FR-5", "Compare the three trainers per epoch and at the best epoch; show feature importance and the QUBO matrix", "`GET /api/comparison`, `/api/model_history`, `/api/feature_importance`, `/api/qubo`; Model comparison page"],
            ["FR-6", "Score one transaction from a form with ensemble or single-model choice and return probability, label, risk band and per-model probabilities", "`POST /api/predict_single`; Verify page"],
            ["FR-7", "Score a CSV file, add predicted class, probability and risk per row, report metrics when a `Class` column exists, and allow export", "`POST /api/predict_batch`, `GET /api/export_predictions`, `/api/sample_batch`; Bulk page"],
            ["FR-8", "Report service health and the models that are loaded", "`GET /api/health`; status chip in the interface"],
            ["FR-9", "Show a clear offline or error state when the backend or an upload fails", "front-end error and empty states"],
        ], widths=[0.55, 3.5, 2.35], size=_sz(9.5, 9), align=["c", "l", "l"]),

        H2("4.4 Non-functional Requirements"),
        TAB("Non-functional requirements, targets and measured values", ["ID", "Requirement", "Target", "Measured"], [
            ["NFR-1", "Single-transaction response time", "under 100 ms", f"median {_SINGLE['median_ms']:.1f} ms, p95 {_SINGLE['p95_ms']:.1f} ms"],
            ["NFR-2", "20-row CSV screening time", "under 1 s", f"median {_BATCH['median_ms']:.1f} ms"],
            ["NFR-3", "Analytics page data time (full dataset aggregates)", "under 1 s", f"median {_STATS['median_ms']:.1f} ms"],
            ["NFR-4", "Retraining time in the lab", "under 1 minute", f"{_TRAIN_S['classical']:.1f} / {_TRAIN_S['sa']:.1f} / {_TRAIN_S['qa']:.1f} s for 20 epochs (PCD / SAS / QS)"],
            ["NFR-5", "Runs on a CPU-only PC with 8 GB RAM", "no GPU or quantum hardware", "met (measured on 15.7 GB; no lower-memory test made)"],
            ["NFR-6", "Reproducibility of reported numbers", "scripted", "met: `run_experiments.py`, `measure_latency.py`"],
            ["NFR-7", "Correct scoring of raw input", "scaled features at serving time", f"not met: the batch route skips scaling (accuracy {F.pct(F.SERVING['as_served_no_scaling']['ensemble']['accuracy'])} as served, {F.pct(F.SERVING['with_scaling']['ensemble']['accuracy'])} scaled)"],
            ["NFR-8", "Security: authentication, authorisation, transport encryption", "required before real use", "not implemented"],
            ["NFR-9", "Usability: responsive layout, light and dark theme", "desktop and phone widths", "met (screens captured at 1440 px and 360 px, both themes)"],
        ], widths=[0.6, 2.4, 1.4, 2.0], size=_sz(9.5, 9), align=["c", "l", "l", "l"]),
        P(_r("The response-time targets are the project's own and were chosen as comfortable limits for an interactive screen; they are not taken from a payment-network standard. "
          "The measurements use the Flask development server on 127.0.0.1 and include JSON encoding, so they describe this prototype and not a production deployment.",
          "The response-time targets are the project's own, not a payment-network standard; the measurements use the Flask development server on 127.0.0.1 and describe this prototype, not a production deployment.")),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware: measurement machine and minimum", ["Item", "Measurement machine", "Practical minimum"], [
            ["Processor", "Intel Core i5-12500, 6 cores / 12 threads", "any 64-bit dual-core CPU"],
            ["Memory", "15.7 GB RAM", "4 GB free (data 18 MB, models under 4 MB)"],
            ["Graphics / quantum hardware", "none used", "none needed"],
            ["Storage", "about 21 MB for data and models plus front-end packages", "500 MB including `node_modules`"],
            ["Operating system", "Windows 11 Pro", "Windows 10/11, Linux or macOS"],
            ["Browser", "Chrome (captures at 1440 x 900 and 360 x 780)", "current Chrome, Edge or Firefox"],
        ], widths=[1.7, 2.5, 2.2], size=_sz(10, 9.5), align=["l", "l", "l"]),
        P("The minimum column is a reasoned estimate from file sizes, not a tested configuration; only the measurement machine was actually used."),

        H2("4.6 Software Requirements"),
        TAB("Software stack", ["Layer", "Software", "Version"], [
            ["Language", "Python", "3.11.9"],
            ["Web framework", "Flask, Flask-Cors", "3.1.0, 5.0.0"],
            ["Numerics and data", "numpy, pandas, scipy, joblib", "1.26.4, 2.2.1 installed (2.2.2 pinned), 1.13.0, 1.4.2"],
            ["Machine learning", "scikit-learn, imbalanced-learn", "1.5.0, 0.12.4"],
            ["Baselines (experiments only)", "XGBoost", "2.0.3"],
            ["Plots", "matplotlib, seaborn", "3.9.0, 0.13.2"],
            ["Front end", "React, React Router, Vite, Recharts", "see `frontend/package.json`"],
            ["Tooling", "Node.js and npm for the front end; Playwright for screenshot capture", "-"],
        ], widths=[1.6, 2.8, 2.0], size=_sz(10, 9.5), align=["l", "l", "l"]),
        P(_r("`requirements.txt` pins pandas 2.2.2 while 2.2.1 is installed on the measurement machine; the experiments in this report ran on the installed versions. "
          "One practical consequence is that the pickled preprocessing pipeline in `models/` was written with a newer pandas and cannot be unpickled here, so the backend rebuilds "
          "an identical pipeline from the CSV at start-up.",
          "`requirements.txt` pins pandas 2.2.2 but 2.2.1 is installed; the experiments ran on the installed versions. The pickled pipeline in `models/` was written with a newer pandas and cannot be "
          "unpickled here, so the backend rebuilds an identical pipeline from the CSV at start-up.")),

        H2("4.7 User Roles and Constraints"),
        H3("4.7.1 User roles"),
        TAB("User roles", ["Role", "Typical goal", "Screens used"], [
            ["Merchant or customer-service agent", "check one transaction and get a decision and reason", "Verify"],
            ["Risk analyst", "screen an exported file, study fraud patterns, compare models", "Bulk, Analytics, Model comparison, Dashboard"],
            ["Model owner", "regenerate data, preprocess and retrain the models", "Model lab"],
        ], widths=[2.0, 2.9, 1.5], size=_sz(10.5, 9.5), align=["l", "l", "l"]),
        P(_r("The application has no login and no role separation: every visitor can reach every screen and every route, including the ones that regenerate the dataset and overwrite "
          "the saved models. This is acceptable for a single-user prototype and is listed as a constraint, not a feature.",
          "There is no login or role separation: every visitor can reach every route, including the ones that regenerate the dataset and overwrite the saved models. This is a constraint of a single-user prototype, not a feature.")),
        H3("4.7.2 Constraints and assumptions"),
        B(*_r(["The data are synthetic; fraud signals were put into the generator by its authors, so separability is an assumption of the data and not a finding about fraud.",
          "Class balance in the shipped file is 50/50 by construction; the 1 % fraud variant used in the experiments is generated separately and is not exposed in the interface.",
          "Request volume is assumed to be one user at a time; the Flask development server is not a production server.",
          "Evaluation metrics use a threshold of 0.5 unless stated; no cost-sensitive threshold is configured in the product.",
          "No personal or real card data are stored or processed at any point."],
          ["The data are synthetic; fraud signals were put into the generator by its authors, so separability is an assumption of the data and not a finding about fraud.",
          "The shipped file is 50/50 by construction; the 1 % fraud variant is generated separately by the experiments and is not exposed in the interface.",
          "One user at a time on the Flask development server; metrics use a 0.5 threshold and no cost-sensitive threshold is configured; no personal or real card data are stored or processed."])),
        H2("4.8 Requirement Analysis"),
        H3("4.8.1 Prioritisation and traceability to the objectives"),
        P(_r("Each requirement was ranked by how much of the batch objectives it carries. The ranking explains why the product was built around scoring and comparison and why "
          "the baseline classifiers named in the objectives live in an experiment script and not in the interface: the objectives ask for classifiers to be trained and evaluated, "
          "and the base paper asks for the RBM trainers to be compared, and only the second is a screen a user can operate.",
          "Requirements were ranked by how much of the batch objectives they carry; this explains why the product centres on scoring and comparison while the baseline classifiers named in the objectives "
          "live in an experiment script and not in the interface.")),
        TAB("Requirement priority and objective traceability", ["Requirement", "Priority", "Objective served", "Status"], [
            ["FR-6 single scoring, FR-7 bulk scoring", "Must", "6 (deploy behind an interface)", "built; serving defect documented"],
            ["FR-3 preprocessing, FR-4 training", "Must", "2, 3 (preprocessing and balancing)", "built; SMOTE and Tomek selectable by API"],
            ["FR-5 model comparison", "Must", "5 (evaluate beyond accuracy)", "built"],
            ["FR-1 dataset and analytics", "Should", "1 (quantify the imbalance)", "built; data are synthetic"],
            ["FR-2 data generation", "Should", "1", "built"],
            ["FR-8, FR-9 health and error states", "Should", "6", "built"],
            ["Logistic regression, random forest, XGBoost comparison", "Must (objective 4)", "4", "done in `run_experiments.py`, not in the interface"],
            ["Authentication, audit log, alert delivery", "Could", "none", "not built"],
        ], widths=[2.3, 1.0, 1.7, 1.4], size=_sz(9.5, 9), align=["l", "c", "l", "l"]),
        H3("4.8.2 Data requirements"),
        P(_r(f"The system expects a transaction record with the fields `Amount`, `Time`, `Merchant_Category`, `Transaction_Type`, `Card_Present`, `Country_Match` and the anonymised "
          f"features `V1` to `V22`, plus a `Class` column (0 genuine, 1 fraud) when labels are available. The shipped file has {F.DATASET['rows']:,} rows of which "
          f"{F.DATASET['fraud']:,} are fraud and {F.DATASET['legit']:,} genuine. In the generator, fraudulent amounts average {F.DATASET['amount_mean_fraud']:.2f} against "
          f"{F.DATASET['amount_mean_legit']:.2f} for genuine ones, fraud is more often online or card-not-present, and five of the anonymised features are shifted. A single-transaction "
          "request may leave any field out; missing numeric fields are filled with the dataset mean and missing categorical fields with the most common value, which is "
          "how the Verify screen can score a form that only asks for nine of the 28 inputs.",
          f"A record needs `Amount`, `Time`, `Merchant_Category`, `Transaction_Type`, `Card_Present`, `Country_Match`, the anonymised `V1` to `V22` and, when labels exist, `Class`. "
          f"The shipped file has {F.DATASET['rows']:,} rows ({F.DATASET['fraud']:,} fraud, {F.DATASET['legit']:,} genuine); in the generator fraudulent amounts average {F.DATASET['amount_mean_fraud']:.2f} against "
          f"{F.DATASET['amount_mean_legit']:.2f}, fraud is more often online or card-not-present, and five anonymised features are shifted. A single-transaction request may omit any field: missing numeric fields "
          "take the dataset mean and categorical ones the most common value, which is how the Verify form can ask for only nine of the 28 inputs.")),
        H3("4.8.3 Analysis of risks to the requirements"),
        TAB("Main risks and how each was handled", ["Risk", "Effect on requirements", "Handling"], [
            ["Synthetic data are easier than real fraud", "accuracy figures overstate real performance", "stated in every results chapter; base-paper comparison flagged as not comparable"],
            ["PCD model unstable and poorly thresholded", "NFR on correct scoring at 0.5 fails for PCD", f"reported with five seeds (F1 {F.seed_cell('classical', 'f1')}); the ensemble and the threshold sweep are shown"],
            ["Serving skips scaling", "NFR-7 not met", "documented with measured effect; fix proposed as future work"],
            ["No authentication", "NFR-8 not met", "stated as a constraint; single-user prototype"],
            ["Pickled pipeline written by a newer pandas", "start-up could fail on another machine", "backend rebuilds the same pipeline from the CSV"],
        ], widths=[2.0, 2.1, 2.3], size=_sz(9.5, 9), align=["l", "l", "l"]),
        P(_r("Taken together, the requirement analysis shows a system whose functional requirements are met and whose weak points are in correctness of the serving path and in "
          "security, both of which are visible in the tables above instead of being left for the reader to discover.",
          "In sum, the functional requirements are met and the weak points, correctness of the bulk serving path and security, are visible in the tables above; coverage is reviewed again in Chapters 7 and 8.")),
        *([] if F.REPORT else [N("Requirement coverage is reviewed again in Chapter 7 (testing) and Chapter 8 (objectives against outcomes).")]),
    ]
