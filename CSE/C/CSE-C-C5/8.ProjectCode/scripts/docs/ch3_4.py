"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB


def blocks():
    return chapter3() + chapter4()


def chapter3():
    E = F.ENV
    pr = F.PERF
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the proposed system can be built, whether it is worth building and whether it can be used. This chapter answers the three questions for the Smart Campus Placement "
          "System from what was actually built and measured, and adds a plan of the work. No monetary figures are given: the project had no budget line, and an invented rupee estimate would be "
          "decoration rather than evidence. The cost discussion is therefore in terms of what was and was not needed."),

        H2("3.1 Technical Feasibility"),
        P("The technology needed is mature, free and runs on an ordinary desktop. The whole system was built and measured on one machine: " + E["cpu"] + ", " + E["ram"] + " of memory, " + E["os"] + ", "
          "no graphics processor. The table lists the technology, its role and the evidence that it is sufficient."),
        TAB("Technical feasibility by component", ["Component", "Technology (measured version)", "Evidence that it is feasible"],
            [["Data preparation", f"pandas {E['pandas']}, numpy {E['numpy']}", f"{F.DS['rows']:,} students and 30 companies load and encode in well under a second"],
             ["Classifiers", f"scikit-learn {E['sklearn']}, xgboost {E['xgboost']}", "All six baselines, calibration and both local models train in about 3 s on the CPU (one full seed)"],
             ["Explainability", f"shap {E['shap']}", "TreeExplainer ranks 24 features over 450 test rows in seconds"],
             ["Serving API", f"FastAPI {E['fastapi']}, uvicorn {E['uvicorn']}, pydantic {E['pydantic']}", f"Prediction answers in {pr['POST /api/predict']['mean_ms']:.0f} ms on average on localhost"],
             ["Original UI", f"Flask {E['flask']}", "Five server-rendered pages kept working over the same `src/` code"],
             ["Web interface", f"React {E['react']}, Vite {E['vite']}, Tailwind {E['tailwind']}, three.js {E['three']}", "Six screens plus command palette and activity log, built and screenshotted at 1440x900"],
             ["Interpreter", f"Python {E['python']}, Node {E['node']}", "Same interpreter ran training, tests and the server"]],
            widths=[1.3, 2.5, 2.9], align=["l", "l", "l"], size=9.5),
        P("Two technical risks were found and handled. First, the pickled company table was written with a newer pandas and needs `pyarrow` to load, so `pyarrow` was added to `requirements.txt`. "
          "Second, pickled scikit-learn models are tied to the library version; the shipped models loaded and reproduced `models/metrics.json` exactly under scikit-learn " + E["sklearn"] + ", but a "
          "different version should be expected to need retraining, which takes seconds. One technical weakness remains: the recommendation request reloads the four model files for every candidate and "
          f"takes about {pr['POST /api/recommend']['mean_ms']/1000:.1f} seconds, which is acceptable for a single student but would not scale to a whole batch without caching."),
        P("Data is the real technical constraint. A genuine placement dataset needs several batches of real student records and a signed data-protection arrangement with the college, which was "
          "not available. A synthetic generator was used instead. It makes the system buildable and testable, but it limits what can be claimed about accuracy (Section 1.8)."),

        H2("3.2 Economic Feasibility"),
        P("The system is economically feasible because it consumes almost nothing that has to be bought."),
        TAB("Cost drivers", ["Item", "What was needed", "Cost consequence"],
            [["Software licences", "Python, scikit-learn, XGBoost, SHAP, pandas, FastAPI, Flask, React, Vite, Tailwind, three.js, Recharts (all open source)", "None"],
             ["Hardware", "One existing desktop PC; no GPU, no server, no cloud account", "None beyond equipment the team already had"],
             ["Data", "Synthetic, generated in seconds; no purchase, no survey", "None; but real data would need collection effort and consent"],
             ["Effort", "Four students and a guide over the project term; the largest effort was the interface and the evaluation, not the models", "The dominant cost, as in most student projects"]],
            widths=[1.4, 3.3, 2.0], align=["l", "l", "l"], size=9.5),
        P("The benefit side is qualitative and was not measured in this project: less time spent by the placement cell on manual shortlisting, earlier guidance for weaker students, and a recruiter "
          "list produced in one call (a shortlist request takes " + f"{pr['POST /api/recruiter/shortlist']['mean_ms']:.0f}" + " ms). Whether these benefits materialise depends on a pilot with real data, "
          "which is listed as future work (Chapter 10)."),

        H2("3.3 Operational Feasibility"),
        P("Operational feasibility asks whether the intended users can run and use the system. Three groups were considered."),
        B("**Students** need a browser. The eligibility screen has one form, a company selector and a result card with a probability bar, a cut-off comparison and tips, so no training is needed.",
          "**Placement officers** use the dashboard: four headline tiles, a model comparison chart, branch placement rates and tabs for the model table, SHAP, PCA errors and probabilities.",
          "**Recruiters** use one filter form (minimum CGPA, minimum aptitude, branch) and receive up to 50 candidates, sortable and exportable as CSV from the table."),
        P("Installation is one double-click on `run.bat`, which creates the virtual environment, installs packages, trains the models if they are missing, installs the front-end packages and starts "
          "both servers (Appendix B). The original Flask application remains available with `python app.py`, so a college that does not want Node.js can still use the system. "
          "Operational limits are that there is no login, so the system suits one trusted machine or a college network, not the open internet, and that students must enter their own scores, "
          "because there is no connection to the college record system."),

        H2("3.4 Schedule Feasibility"),
        P("The work divides naturally into phases that depend on each other in the order shown. The table gives the phases, what each produced and the share of effort it took in this project "
          "(estimated by the team from the order of the work, not recorded by a time sheet)."),
        TAB("Project phases", ["Phase", "Activity", "Output", "Share of effort"],
            [["1", "Literature survey, choice of the base papers, mapping admission to placement", "Survey table, mapping table", "10%"],
             ["2", "Synthetic dataset and company table", "`placement_dataset.csv`, `companies.csv`", "10%"],
             ["3", "Pre-processing and feature engineering", "`preprocess.py`, `preprocess.pkl`", "10%"],
             ["4", "Training, calibration, hybrid model, plots", "`hybrid_model.py`, five pickles, `metrics.json`", "15%"],
             ["5", "Recommendation module", "`recommend.py`", "10%"],
             ["6", "Original Flask application", "`app.py`, five templates", "10%"],
             ["7", "FastAPI layer and React front end", "`backend/main.py`, six screens", "20%"],
             ["8", "Testing, measurement, diagrams, screenshots, documents", "46 checks, experiments, this report", "15%"]],
            widths=[0.6, 3.0, 2.2, 0.9], align=["c", "l", "l", "c"], size=9.5),
        P("Phases 2 to 4 are strictly sequential, because each reads the files written by the one before. Phases 6 and 7 can run in parallel once phase 5 exists, because both only call "
          "`src/recommend.py`. The schedule was feasible because the ML code is small (508 lines in `src/`) and the interface work reused a component kit; the risk in the plan was the late discovery "
          "that the hybrid gain depends on labels, which belongs to the evaluation phase and is the reason evaluation was given its own phase."),

        H2("3.5 Legal, Ethical and Data Feasibility"),
        P("A placement-prediction system handles personal academic data and influences opportunities, so feasibility includes more than code. Four points were considered."),
        B("**Personal data.** Real use would involve marks, test scores and placement outcomes of identifiable students. The prototype avoids the issue by using generated records; a deployment would need the college's "
          "data-protection approval, a stated purpose, access control (not present today) and a retention rule.",
          "**Fairness.** A model trained on past placements learns past hiring patterns. In the generator the branch effect is small (placed rates 58.5% to 60.8% across six branches), but real data could encode "
          "bias by branch, gender or school background. The tool is designed as decision support: the label is a probability with an explanation, and a placement officer decides.",
          "**Transparency.** Students are shown which cut-offs they miss and why, not only a score, and the officer can see which features matter most (SHAP).",
          "**Misuse.** A low probability must not be used to bar a student from applying. The recommendation module suggests alternatives; it does not restrict choices."),
        P("The data itself is feasible to obtain in principle, because colleges already hold it, but not within this project. This is why the evaluation is reported as a measurement on synthetic data and "
          "why the conclusions in Chapters 9 and 10 call for a pilot on real records."),

        H2("3.6 Risk Analysis"),
        TAB("Main risks and responses", ["Risk", "Likelihood / impact", "Response in this project"],
            [["Synthetic data misread as real performance", "High / high", "Stated in the abstract, Chapter 1 and every results chapter; no claim of real-world accuracy"],
             ["Hybrid gain overstated", "Found / medium", "Measured separately with and without test labels (Chapter 8)"],
             ["Library or pickle incompatibility", "Medium / medium", "`requirements.txt`, `pyarrow` added, retraining takes seconds, shipped models verified to reproduce the metrics"],
             ["Slow recommendation request", "Found / low for one user", "Documented; caching named as the fix"],
             ["No access control", "Certain / high if exposed", "Documented; the prototype is meant for localhost or a trusted network"],
             ["Out-of-range or unseen input", "Medium / low", "Pydantic ranges, 404 for unknown company; unseen categories accepted and listed as a limitation"]],
            widths=[2.2, 1.5, 3.0], align=["l", "l", "l"], size=9.5),

        H2("3.7 Advantages and Constraints"),
        TAB("Advantages and constraints", ["Advantages", "Constraints"],
            [["Probability, not only yes/no, so students can be ranked and compared", "Synthetic data: accuracy says little about real placements"],
             ["Explained by cut-off gaps and SHAP, so the officer can act", "Company table is invented and static"],
             ["Runs on one ordinary PC; trains in seconds", "No authentication, database or rate limiting"],
             ["Two interfaces over the same code; the original keeps working", "Recommendation takes about 5 seconds per request"],
             ["Open-source stack; no licence cost", "Hybrid gain depends on test labels (Chapter 8)"],
             ["Reproducible scripts and tests", "Recommendation gains are model estimates, never checked against outcomes"]],
            widths=[3.35, 3.35], align=["l", "l"], size=10),
        P("**Conclusion of the study.** The system is technically, economically, operationally and schedule-wise feasible as a prototype on synthetic data. A deployment on real data would be feasible "
          "only after a data-sharing agreement, authentication and caching of the model artefacts."),
    ]


def chapter4():
    E = F.ENV
    pr = F.PERF
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter analyses the problem as it stands, states what the proposed system must do and how well, and lists the hardware, software and people involved. "
          "Requirement identifiers (FR for functional, NR for non-functional) are used again in Chapters 5 and 7."),

        H2("4.1 Existing System and its Limitations"),
        P("In the situation described by the batch documents and by the base paper [1], placement information is kept in spreadsheets and registers. The placement cell publishes company "
          "cut-offs, collects student details, filters lists by hand for each recruiter and announces results. Student-facing tools, where they exist, only store and display information."),
        TAB("Limitations of the existing system", ["No.", "Limitation", "Consequence"],
            [["L1", "No prediction from past data", "Readiness is discovered when the shortlist is published"],
             ["L2", "No company-level matching", "Students apply to companies whose cut-offs they cannot meet, or ignore companies they could clear"],
             ["L3", "Manual, inconsistent shortlisting", "Different lists for different recruiters; slow turnaround"],
             ["L4", "Generic feedback", "No statement of which gap (CGPA, aptitude, technical, internship) to close"],
             ["L5", "No dashboards", "The officer cannot see readiness by branch or which factors matter"],
             ["L6", "No audit of accuracy", "No measure of how good any estimate was"]],
            widths=[0.5, 2.7, 3.5], align=["c", "l", "l"], size=10),
        P("The declared base paper [1] improves on this with a prediction application, but it reports no numerical evaluation, offers skill-gap analysis rather than company recommendation, and "
          "relies on a synthetic dataset of unstated size. The technique paper [2] gives a stronger modelling approach for a neighbouring problem. Neither is a placement system with recommendation."),

        H2("4.2 Proposed System and its Advantages"),
        P("The proposed system is a web application with a machine-learning core. A student enters a profile and picks a company and role; the system returns a calibrated placement probability, a "
          "label (\"placement ready\" at or above 0.5, otherwise \"needs improvement\"), a comparison of the profile with the company's cut-offs and tips. A recommendation module searches the "
          "30 companies and four roles for the five company-role pairs with the highest estimated probability that pass feasibility filters. Officers see model quality, SHAP importance and "
          "placement rates; recruiters filter the student table."),
        TAB("Advantages over the existing system", ["Limitation", "How the proposed system answers it"],
            [["L1 No prediction", "Calibrated XGBoost probability for every student-company-role combination, with a kNN local model for borderline cases"],
             ["L2 No matching", "Company-role recommendation with CGPA, aptitude and backlog feasibility filters and a location preference"],
             ["L3 Manual shortlisting", "One API call returns up to 50 students for the recruiter's CGPA, aptitude and branch filters"],
             ["L4 Generic feedback", "Tips generated from the gaps against the chosen company's cut-offs, and the cut-off panel on the result card"],
             ["L5 No dashboards", "Officer dashboard: metrics, model comparison, SHAP, PCA of errors, probability histogram, branch rates"],
             ["L6 No audit", "Accuracy, precision, recall, F1, ROC-AUC, Brier score, confusion matrices, five-seed repetition, 46 automated checks"]],
            widths=[1.9, 4.8], align=["l", "l"], size=10),

        H2("4.3 Functional Requirements"),
        P("Each requirement names the endpoint or module that implements it. All were implemented and tested (Chapter 7)."),
        TAB("Functional requirements", ["ID", "Requirement", "Implemented by"],
            [["FR1", "Accept a student profile (13 attributes), a target company and a role, and return a placement probability in [0, 1]", "`POST /api/predict`, `predict_for()`"],
             ["FR2", "Label the result \"placement ready\" at probability >= 0.5, otherwise \"needs improvement\"", "`predict()` in `backend/main.py`"],
             ["FR3", "Return skill-gap tips from the profile's gaps against the company's CGPA, aptitude and technical cut-offs and the number of internships", "`_tips()`"],
             ["FR4", "Reject out-of-range input with an error and unknown companies with 404", "Pydantic models, `_company_row()`"],
             ["FR5", "Recommend the top five company-role pairs, with the original-target probability, average gain and match rate, plus company-only and role-only lists", "`POST /api/recommend`, `recommend()`"],
             ["FR6", "Apply feasibility filters (CGPA proximity by tier, aptitude margin, backlogs for Tier 1, minimum package) and a location preference", "`recommend()`, `delta_max_cgpa()`"],
             ["FR7", "Show model metrics (nine models, nine-fold CV, Brier score, residual rate)", "`GET /api/metrics`"],
             ["FR8", "Show the SHAP, PCA and probability-histogram plots", "`GET /api/plots/{name}`"],
             ["FR9", "Show dataset statistics: students, placed rate, mean CGPA, placed rate by branch", "`GET /api/stats`"],
             ["FR10", "Shortlist students by minimum CGPA, minimum aptitude and branch, top 50 by CGPA then technical score, with the total number of matches", "`POST /api/recruiter/shortlist`"],
             ["FR11", "List the 30 companies with tier, cut-offs, package, location, type and hiring rate; offer the lists of branches, roles and locations", "`GET /api/companies`, `GET /api/meta`"],
             ["FR12", "Report service health and whether the trained models are present", "`GET /api/health`"],
             ["FR13", "Train, calibrate and save the models and write the metrics and plots", "`src/hybrid_model.py`"],
             ["FR14", "Keep the original Flask pages working over the same core", "`app.py`, `templates/`"],
             ["FR15", "Provide a search and keyboard navigation (command palette, `g e/r/d/u/c`, `g l`) and a persistent dark and light theme", "`frontend/src/components/ui/`"]],
            widths=[0.55, 4.2, 1.95], align=["c", "l", "l"], size=9),

        H2("4.4 Non-functional Requirements"),
        P("Targets were set before measurement; the last column states the measured value from Chapter 7 and whether the target was met."),
        TAB("Non-functional requirements", ["ID", "Requirement", "Target", "Measured / status"],
            [["NR1", "Prediction latency", "Under 200 ms on the build machine", f"mean {pr['POST /api/predict']['mean_ms']:.0f} ms, p95 {pr['POST /api/predict']['p95_ms']:.0f} ms - met"],
             ["NR2", "Shortlist latency", "Under 200 ms", f"mean {pr['POST /api/recruiter/shortlist']['mean_ms']:.0f} ms - met"],
             ["NR3", "Recommendation latency", "Under 2 s", f"mean {pr['POST /api/recommend']['mean_ms']/1000:.1f} s - **not met**"],
             ["NR4", "Training time on a CPU", "Under 1 minute", "about 3 s for one full seed - met"],
             ["NR5", "Input validation", "No out-of-range value reaches the model", "6 of 6 validation checks of invalid input pass - met"],
             ["NR6", "Reproducibility", "Same seed gives the same data and split", "Shipped models reproduce `metrics.json` exactly - met"],
             ["NR7", "Portability", "Runs on Windows with Python 3.10+ and Node 20+", "Run on Windows 11, Python 3.14 - met on one machine only"],
             ["NR8", "Security", "No code execution from input; restricted cross-origin access", f"{F.TEST_SUMMARY['by_group']['security'][0]} of {F.TEST_SUMMARY['by_group']['security'][1]} security checks pass; **no authentication** - partly met"],
             ["NR9", "Usability", "One screen per task, visible loading, empty and error states", "Implemented in the interface; no user study was done"],
             ["NR10", "Maintainability", "Small modules, tests, scripts to re-run everything", "508 lines of ML code, 46 checks, six scripts - met"]],
            widths=[0.55, 1.7, 2.1, 2.35], align=["c", "l", "l", "l"], size=9),

        H2("4.5 Data Requirements"),
        P("The system needs two tables. The student table has one row per student and target company; the company table has one row per company. The schema below is what the code reads; the "
          "ranges are those observed in the generated data."),
        TAB("Student table (`data/placement_dataset.csv`, 3,000 rows, 19 columns)", ["Column", "Type", "Observed range / values"],
            [["CGPA", "float", "5.80 - 9.35 (mean 7.83)"],
             ["Tenth_Percent, Twelfth_Percent", "float", "45.0 - 93.8 and 40.3 - 89.2"],
             ["Aptitude_Score, Technical_Score, Communication_Score, DSA_Score", "float", "27.6 - 98.0, 26.2 - 100, 20.0 - 90.6, 10.0 - 100"],
             ["Projects, Internships, Certifications", "int", "0 - 6, 0 - 4, 0 - 6"],
             ["Backlogs", "int", "0 - 4"],
             ["Branch", "category", "CSE, IT, ECE, EEE, MECH, CIVIL"],
             ["Degree_Type, Student_Type", "category", "BTech / MTech; Regular / Lateral"],
             ["Placement_Year", "int", "2023 - 2026"],
             ["Target_Company, Target_Role, Target_Tier", "category, category, int", "30 companies, 8 roles, tier 1 - 3"],
             ["Placed", "0 / 1 (label)", "1,791 placed, 1,209 not placed"]],
            widths=[3.0, 1.2, 2.5], align=["l", "l", "l"], size=9.5),
        TAB("Company table (`data/companies.csv`, 30 rows)", ["Column", "Meaning"],
            [["Company, Tier", "Name; 1 dream, 2 core, 3 mass recruiter"],
             ["CGPA_Cutoff, Apt_Cutoff, Tech_Cutoff", "Eligibility thresholds used for gap features, feasibility filters and tips"],
             ["Package_LPA, Location, Company_Type", "Offer in lakhs per annum, city, MNC / Startup / Core"],
             ["Hiring_Rate", "Historic share of applicants hired (0.12 - 0.55)"]],
            widths=[2.6, 4.1], align=["l", "l"], size=9.5),
        P("Both tables are synthetic. A real deployment would replace them with an export from the college's records and the recruiters' published criteria, keeping the same column names so that no code changes."),

        H2("4.6 Hardware Requirements"),
        TAB("Hardware", ["Item", "Build and measurement machine", "Practical minimum (not tested)"],
            [["Processor", E["cpu"], "Any recent dual-core CPU"],
             ["Memory", E["ram"], "4 GB"],
             ["Graphics processor", E["gpu"], "Not needed"],
             ["Disk", "About 2 MB of model files; the front-end dependencies need several hundred MB", "1 GB free"],
             ["Display", "1440x900 used for screenshots", "Any; the layout is responsive"]],
            widths=[1.5, 3.0, 2.2], align=["l", "l", "l"], size=10),
        P("The minimum column is an estimate from the size of the files and was not tested; only the build machine was measured."),

        H2("4.7 Software Requirements"),
        TAB("Software (versions measured on the build machine)", ["Layer", "Software", "Version"],
            [["Operating system", "Windows 11 Pro", "10.0.26200"],
             ["Language", "Python (virtual environment `.venv`)", E["python"]],
             ["ML", "scikit-learn / xgboost / shap", f"{E['sklearn']} / {E['xgboost']} / {E['shap']}"],
             ["Data", "pandas / numpy / pyarrow", f"{E['pandas']} / {E['numpy']} / >= 14 (required)"],
             ["API", "FastAPI / uvicorn / pydantic", f"{E['fastapi']} / {E['uvicorn']} / {E['pydantic']}"],
             ["Original UI", "Flask", E["flask"]],
             ["Front end", "Node.js, React, Vite, Tailwind CSS, three.js", f"{E['node']}, {E['react']}, {E['vite']}, {E['tailwind']}, {E['three']}"],
             ["Front-end libraries", "react-router, Recharts, framer-motion, GSAP, axios (ranges declared in `package.json`)", "^7.18, ^3.10, ^14.5, ^3.15, ^1.20"],
             ["Charts and plots", "matplotlib", "3.11.1"],
             ["Browser", "Google Chrome (driven by Playwright for screenshots)", "not recorded"]],
            widths=[1.5, 3.4, 1.8], align=["l", "l", "l"], size=10),

        H2("4.8 User Roles"),
        TAB("User roles", ["Role", "Goal", "Screens and endpoints", "Authentication"],
            [["Student", "Learn the chance of placement at a company and what to improve", "Eligibility, Recommendations, Companies", "None"],
             ["Placement officer", "Judge model quality and readiness of the batch", "Officer dashboard, Companies", "None"],
             ["Recruiter", "Obtain a filtered candidate list", "Recruiter shortlist", "None"],
             ["Developer / administrator", "Regenerate data, retrain, run tests and scripts", "Command line (`src/`, `scripts/`)", "Operating-system access"]],
            widths=[1.4, 2.3, 1.9, 1.1], align=["l", "l", "l", "l"], size=9.5),
        P("The roles are a design distinction only: the application has no accounts, so any user of the interface can use every screen. Role separation by login is future work."),

        H2("4.9 Constraints and Assumptions"),
        B("The data is synthetic and the company table invented (Section 1.8).",
          "Categorical inputs unseen in training (for example a branch the model has not seen) are accepted and encoded with frequency zero rather than rejected.",
          "The 0.5 decision threshold and the 0.4-0.6 borderline band are fixed in code.",
          "The recommender considers four roles per company (the target role, SDE, Data Analyst and QA Engineer), although the data holds eight roles.",
          "The batch description mentions a MySQL database and HTML/CSS/JavaScript pages; the implementation uses CSV and pickle files, a React application and Flask templates."),

        H2("4.10 Analysis Summary"),
        P("The analysis leaves a clear target: a prediction and recommendation service with a small, explainable model, two interfaces and honest evaluation. The requirements above are "
          "traced to design elements in Chapter 5 and to tests in Chapter 7. Of the ten non-functional requirements, eight were met in full, one partly (security, because there is no "
          "authentication) and one not met (recommendation latency)."),
    ]
