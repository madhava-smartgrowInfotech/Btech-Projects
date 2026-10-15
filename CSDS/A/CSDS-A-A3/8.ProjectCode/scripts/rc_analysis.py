"""Chapters 3 and 4: feasibility study and system requirements and analysis."""
from __future__ import annotations

from doc_common import LAT, M, R, T, X, p


# ---------------------------------------------------------------- Chapter 3
def sec_feasibility_technical(d):
    d.h2("Technical Feasibility")
    d.p("The technology needed is mature and freely available: Python 3.11, scikit-learn [23], XGBoost [22], pandas, NumPy and joblib for the "
        "machine-learning pipeline, Flask [27] for the API and SQLite for storage, and React [28] with Vite for the interface. No GPU is needed: all "
        "three classifiers train on a 12-thread desktop CPU in seconds.")
    d.table([["Technical question", "Finding", "Evidence"],
             ["Can the features be computed offline?", "Yes: 47 features from the URL string alone", f"{LAT['feature_extraction_ms_per_url']:.3f} ms per URL; 40,000 URLs in {R['dataset']['featurize_seconds_40k']} s"],
             ["Can the models be trained on a PC?", "Yes", f"RF {RF_T()} s, XGBoost {X['train_seconds']} s, LR {LR_T()} s on 32,000 URLs (Intel Core i5-12500, 15.7 GB RAM)"],
             ["Is real-time response possible?", "Yes", f"/api/check mean {LAT['api_check_ms_mean']:.1f} ms, p95 {LAT['api_check_ms_p95']:.1f} ms"],
             ["Can crowd data be stored and queried?", "Yes: SQLite, three tables", "Parameterised SQL; consensus computed on each report"],
             ["Can a model be replaced while serving?", "Yes", "Detector.reload() swaps the model under a lock"],
             ["Are public feeds reachable?", "Yes, when online", "OpenPhish +300 and URLhaus +500 URLs in the demonstration run"]],
            "Technical feasibility checks", widths=[0.3, 0.3, 0.4], font=9.5)
    d.p("The one technical risk identified was version drift of saved model files: the saved logistic-regression file could not be loaded under "
        "the installed scikit-learn (it was written by a newer version), although the application, which loads only the best model, is unaffected. "
        "The project therefore records the library versions it was measured with (Chapter 6).")


def RF_T():
    return M["models"]["random_forest"]["train_seconds"]


def LR_T():
    return M["models"]["logistic_regression"]["train_seconds"]


def sec_feasibility_economic(d):
    d.h2("Economic Feasibility")
    d.p("Every component is open-source software, so there is no licence cost. The system runs on a single ordinary computer; the measuring machine "
        "was an Intel Core i5-12500 with 15.7 GB of memory and no GPU. There is no cloud cost, because the system runs locally. "
        "The two public feeds used for synchronisation are free to download. The shipped model files total about 168 MB, of which the Random Forest "
        "file alone is 165 MB; the selected XGBoost model is 2.5 MB.")
    d.p("The recurring cost is human effort: someone has to decide which reports to trust and to review false positives. This cost is not "
        "estimated here because it depends on the deployment, and the project did not run a pilot with real users.")


def sec_feasibility_operational(d):
    d.h2("Operational Feasibility")
    d.bullets(["**Ease of use.** One text box and one button give a verdict; batch checking accepts a pasted list or a .txt/.csv file.",
               "**Understandability.** Every verdict shows a probability gauge, red flags and a reason sentence.",
               "**Set-up.** `run.bat` trains the models if needed, installs the frontend dependencies and opens both servers and the browser.",
               "**Maintenance.** Retraining is one button, or automatic after 25 new confirmations; the model version and training time are shown.",
               "**Fit with users.** The same JSON API serves the React interface, the original Flask pages and scripts, so other tools can call it."])
    d.p("Operational limits: the system has no sign-in and no moderation workflow, so it fits a trusted local or team setting, not an open deployment.")


def sec_feasibility_schedule(d):
    d.h2("Schedule Feasibility")
    d.p("The project was carried out in four phases. The dates below are the modification dates of the artefacts in the project folder, not a "
        "planned calendar, because no project-management plan was kept.")
    d.table([["Phase", "Work", "Evidence in the folder"],
             ["1", "Dataset sample, feature extractor, three classifiers, threat-intelligence store, Flask interface, CLI", "Python package and models dated 22 Sep 2026"],
             ["2", "API layer for the React interface (backend/server.py) and the seven-page React frontend", "Rebuilt and verified on 14 Oct 2026"],
             ["3", "Measurement, extra tests, screenshots, diagrams, live retraining demonstration", "scripts/ and docs/experiments, 15 Oct 2026"],
             ["4", "Documentation: chapter documents, three decks, full report and paper", "Batch folder, 15 Oct 2026"]],
            "Project phases", widths=[0.1, 0.55, 0.35], font=10)


def sec_feasibility_summary(d):
    d.h2("Advantages and Constraints")
    d.table([["Advantages", "Constraints"],
             ["Runs offline on one PC; no GPU, no cloud, no licence cost.", "40,000-URL sample from one source; modest accuracy compared with the base paper."],
             ["Real-time: under 10 ms per API check on average.", "URL-only features miss phishing pages on clean-looking domains."],
             ["Interpretable features and red flags.", "Hand-written popular-domain list (145 names) causes some false positives."],
             ["Community verdicts act at once, in both directions.", "Votes are anonymous; no sign-in, moderation or rate limit."],
             ["Retraining and hot reload from the interface.", "Retraining benefit on new campaigns is unmeasured."]],
            "Advantages and constraints", widths=[0.5, 0.5], font=10)


# ---------------------------------------------------------------- Chapter 4
def sec_existing(d):
    d.h2("Existing System and its Limitations")
    d.p("Today a link is checked by one or more of the following.")
    d.bullets(["**Blacklists** such as browser safe-browsing lists and PhishTank. A URL is blocked only after it has been reported and listed.",
               "**Rule-based filters** that flag fixed patterns such as an IP address, a long URL or a keyword. The rules are easy to evade with small changes.",
               "**One-time-trained classifiers**, trained on a fixed dataset and not updated.",
               "**Manual reporting**, in which users report sites and staff process the reports by hand."])
    d.table([["Limitation", "Consequence"],
             ["Blacklists cannot detect zero-day URLs that have not been reported", "Victims meet new phishing pages unprotected"],
             ["Manually updated databases lag behind fast campaigns", "Domains are abandoned before they are listed"],
             ["Fixed rules are bypassed by small structural changes", "Low recall against adaptive attackers"],
             ["Models trained once degrade as patterns evolve", "Accuracy falls over time"],
             ["High false-positive rates block legitimate sites", "Loss of user trust"]],
            "Limitations of the existing system", widths=[0.55, 0.45], font=10)


def sec_proposed(d):
    d.h2("Proposed System and its Advantages")
    d.p("PhishGuard classifies a URL in three steps and keeps itself current. The URL is normalised and 47 offline features are extracted. "
        "The detector then consults the community store: a confirmed phishing or confirmed safe entry for the URL, or for its host, decides the "
        "verdict at once. Otherwise the best of three trained classifiers scores the URL, a reputation discount is applied to well-known domains, "
        "pending votes nudge the score, and two thresholds (0.35 and 0.60) give safe, suspicious or phishing. Users report URLs in the "
        "interface; two net votes confirm a URL, and trusted feeds confirm at once. Confirmed URLs are added to the training data with a weight "
        "of three, and the models are retrained and hot-reloaded.")
    d.bullets(["Detects unseen URLs without a list, and uses community knowledge the moment it is confirmed.",
               "Can correct its own false positives through \"safe\" reports.",
               "Explains each verdict with red flags and a reason.",
               "Updates itself and shows the model version, training time and metrics.",
               "Offline, fast, and runnable on an ordinary PC."])


def sec_requirements_functional(d):
    d.h2("Functional Requirements")
    d.table([["ID", "Requirement", "Status"],
             ["FR1", "Accept a URL (with or without scheme) and return verdict, probability, decided-by, reason, red flags and the 47 features", "Implemented"],
             ["FR2", "Check a batch of up to 100 URLs from a pasted list or a .txt/.csv file", "Implemented (React interface)"],
             ["FR3", "Accept community reports (phishing or safe) with reporter name and note", "Implemented"],
             ["FR4", "Count votes and confirm a URL when net votes reach 2; confirm trusted-feed reports at once", "Implemented"],
             ["FR5", "Apply a confirmed community verdict over the model, for the URL and for its host", "Implemented"],
             ["FR6", "Import phishing URLs from OpenPhish and URLhaus on request", "Implemented"],
             ["FR7", "Compare three classifiers and show metrics, confusion matrices and feature importances", "Implemented"],
             ["FR8", "Retrain from the interface or automatically after 25 new confirmations, and hot-reload the model", "Implemented"],
             ["FR9", "Log every check and show activity, verdict mix and probability trend", "Implemented"],
             ["FR10", "Provide a command-line interface for check, report, train, retrain, sync and serve", "Implemented"],
             ["FR11", "Authenticate users and restrict who may report or retrain", "Not implemented"],
             ["FR12", "Administrator verification of reports before they reach training", "Not implemented"]],
            "Functional requirements", widths=[0.08, 0.7, 0.22], font=9.5)


def sec_requirements_nonfunctional(d):
    d.h2("Non-Functional Requirements")
    d.table([["ID", "Requirement", "Target", "Measured"],
             ["NFR1", "Response time of a single check", "Interactive (under 100 ms)", f"mean {LAT['api_check_ms_mean']:.1f} ms, p95 {LAT['api_check_ms_p95']:.1f} ms"],
             ["NFR2", "Training time on a desktop CPU", "Under one minute for the base data", f"{RF_T() + X['train_seconds'] + LR_T():.1f} s for all three models"],
             ["NFR3", "Offline operation", "No internet needed except feed sync", "Met"],
             ["NFR4", "Robustness to malformed input", "No crash on any string", "17 validation checks pass, including malformed ports and 5,000-character URLs"],
             ["NFR5", "Resistance to injection", "SQL and HTML injection neutralised", "8 security checks pass"],
             ["NFR6", "Explainability", "Reasons shown with every verdict", "Red flags and reason text on every result"],
             ["NFR7", "Portability", "Windows 10/11 with Python and Node", "Met on Windows 11; other systems not tested"],
             ["NFR8", "Accuracy", "Compare three classifiers fairly", f"Same split and features; XGBoost F1 {p(X['f1'])}"]],
            "Non-functional requirements", widths=[0.08, 0.3, 0.27, 0.35], font=9.5)


def sec_requirements_platform(d):
    d.h2("Hardware and Software Requirements")
    d.table([["Item", "Minimum", "Used for the measurements"],
             ["Processor", "Any modern multi-core CPU", "Intel Core i5-12500, 6 cores / 12 threads"],
             ["Memory", "4 GB (8 GB recommended to train Random Forest)", "15.7 GB"],
             ["Disk", "About 170 MB for the shipped model files, plus the frontend dependencies (node_modules)", "Not measured"],
             ["GPU", "Not needed", "Intel UHD Graphics 770 (not used)"],
             ["Operating system", "Windows 10 or 11 (run.bat); other systems with manual commands", "Windows 11 Pro 10.0.26200"],
             ["Python", "3.10 or later", "3.11.9"],
             ["Python libraries", "flask>=3.0, scikit-learn>=1.4, xgboost>=2.0, pandas>=2.0, numpy>=1.26, joblib>=1.3", "Flask 3.1.0, scikit-learn 1.4.2, XGBoost 2.0.3, pandas 2.2.1, NumPy 1.26.4, joblib 1.3.2"],
             ["Node.js", "18 or later", "v24.19.0 (React 18.3, Vite 5.4)"],
             ["Browser", "A current Chromium-based browser", "Google Chrome"]],
            "Hardware and software requirements", widths=[0.2, 0.42, 0.38], font=9.5)


def sec_roles(d):
    d.h2("User Roles and Constraints")
    d.p("The application has no sign-in, so roles are functional, not enforced. The same interface serves all of them.")
    d.table([["Role", "What they do", "Pages used"],
             ["Analyst / end user", "Check one URL or a batch; read the verdict and red flags; review activity", "Check URL, Activity"],
             ["Community reporter", "Report a URL as phishing or safe; follow the vote tally", "Report, Threat intelligence"],
             ["Maintainer", "Sync public feeds, compare models, retrain", "Threat intelligence, Models"],
             ["Public threat feeds", "External systems that supply trusted phishing URLs", "Used by the sync action"]],
            "User roles", widths=[0.22, 0.5, 0.28], font=10)
    d.p("**Constraints.** The system needs a trained model to give an ML verdict; without one it returns \"unknown\". A retrain takes from under a minute "
        "to several minutes, depending on the machine; in the demonstration run XGBoost alone took 203.8 s while a "
        "browser was polling the page. Feed synchronisation needs internet access.")
