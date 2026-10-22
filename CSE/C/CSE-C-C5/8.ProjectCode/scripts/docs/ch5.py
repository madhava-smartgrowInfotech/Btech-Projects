"""Chapter 5: System Design. Also holds DIAGRAMS, the list used by 11. BLOCK DIAGRAMS ALL.docx."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB

# (key, title, file, caption, explanatory paragraph(s))
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of the Smart Campus Placement System: presentation, application and core layers with the file stores.",
     "The system has four columns. The presentation column holds the React 19 single-page application (Vite, Tailwind 4, port 5405) and the original Flask pages (`app.py` and five templates, "
     "port 5000). The application column is the FastAPI service `backend/main.py` (port 8405): nine route handlers, Pydantic validation, a CORS rule that admits only the front-end origin and a few helpers "
     "(`_tips`, `_company_row`, `_records`, `_dataset`). The core column is the `src/` package: `recommend.py` serves predictions and recommendations, `preprocess.py` builds the 24 features, "
     "`hybrid_model.py` trains and evaluates, `generate_dataset.py` writes the synthetic data. The data column holds the two CSV tables, the five pickled model files with `metrics.json`, and three plot images. "
     "The FastAPI layer contains no model logic: it imports `predict_for`, `recommend` and `pre_comp_cache` from `src/recommend.py`, which is the same code the Flask app calls, so the two interfaces cannot drift apart. "
     "There is no SQL database; the pickled models are read from disk on each request."),
    ("wf", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow from data generation to recruiter shortlist.",
     "The workflow has an offline half and an online half. Offline, `generate_dataset.py` writes 3,000 synthetic students and 30 companies (seed 42), `preprocess.py` frequency-encodes and standardises the features, and "
     "`hybrid_model.py` splits the data 70/15/15, trains six baseline classifiers, calibrates XGBoost with Platt scaling, builds the kNN and SVM residual models and writes the pickles, `metrics.json` and three plots. "
     "`run.bat` repeats this only when the model files are missing. Online, every request loads the saved models: the student pages ask for a probability or a recommendation, the officer dashboard reads the metrics and plots, "
     "and the recruiter page filters the student table."),
    ("dfd0", "Data flow diagram, level 0 (context)", "03_dfd_level0.png",
     "Level 0 data flow diagram: the system as one process with three external entities and four data stores.",
     "At the context level the system is a single process. A student sends a profile with a target company and role and receives a probability, a label, skill-gap tips and up to five alternatives. A placement officer "
     "requests the dashboard and receives metrics, plots and placement statistics. A recruiter sends shortlist filters (CGPA, aptitude, branch) and receives matching students. The process reads the student records (D1), "
     "the company table (D2), the trained models (D3) and the metrics and plots (D4). Nothing is written at run time: the stores are only read."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Level 1 data flow diagram: six processes, three external entities and four data stores.",
     "Level 1 splits the process into six. Process 1 prepares the data and features from D1; process 2 trains and evaluates the models and writes the models to D3 and the metrics and plots to D4; process 3 predicts "
     "the placement probability from the models in D3 and the cutoffs in D2; process 4 recommends company-role pairs from the same two stores and the probability of process 3; process 5 serves the officer analytics from D4; "
     "process 6 filters D1 for the recruiter. Processes 1 and 2 run offline through the scripts in `src/`; processes 3 to 6 run per request. Stores shown more than once are the same store, repeated only to keep the arrows short."),
    ("dfd2", "Data flow diagram, level 2 (process 4)", "05_dfd_level2.png",
     "Level 2 data flow diagram of process 4, Recommend company-role pairs.",
     "Process 4 is the most complex request, so it is decomposed. 4.1 scores the student's original target to obtain the base probability p0. 4.2 applies the feasibility filters to the 30 companies: the CGPA gap must "
     "not exceed delta_max of the company tier, aptitude must be at least the cutoff minus 15, a student with more than two backlogs is not offered Tier-1 companies, and an optional minimum package is honoured. "
     "4.3 scores every feasible company with four roles (the target role, SDE, Data Analyst, QA Engineer). 4.4 ranks the candidates by score and builds the three lists, and 4.5 computes the average gain and the match rate. "
     "The trained models (D3) are read by 4.1 and 4.3, the company table (D2) by 4.2."),
    ("class", "UML class diagram", "06_class_diagram.png",
     "UML class diagram: request models, API module, core modules and the trained artefacts.",
     "The code base is written as modules of functions with four Pydantic classes, so the diagram shows each module as a class box with its operations. `PredictIn` extends `Profile`; `RecommendIn` and `ShortlistIn` "
     "are independent request models. The API module uses them and calls `recommend.py`, which imports `preprocess.py`, loads the pickled artefacts and wraps scikit-learn and XGBoost objects "
     "(`CalibratedClassifierCV` around `XGBClassifier`, `KNeighborsClassifier`, `SVC`). `hybrid_model.py` saves the artefacts and uses `build_features`; `generate_dataset.py` writes the CSV files."),
    ("seq", "Sequence diagram: placement prediction", "07_sequence_prediction.png",
     "Sequence diagram of `POST /api/predict`, the main flow of the system.",
     "The student enters a profile on the Eligibility page and picks a company and a role. The page posts JSON to `/api/predict`. FastAPI validates the body with Pydantic (422 on a bad range) and looks the "
     "company up (404 if unknown). `predict_for` loads the four pickles, `build_features` turns the single row into a 1 x 24 vector, the calibrated XGBoost model gives a probability and, when the probability lies "
     "between 0.4 and 0.6, it is averaged with the kNN probability. The endpoint labels the result PLACEMENT READY at 0.5 or above, adds the skill-gap tips and returns JSON; the page shows a result card and a toast."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram with three user roles and one offline developer role.",
     "A student checks placement eligibility, reads the skill-gap tips (an included use case), gets company-role recommendations and browses the companies with their cutoffs. A placement officer views the model "
     "metrics and plots and the placement statistics, and may use the recommendations and the company board. A recruiter shortlists students and also reads the company board and the statistics. The developer retrains the models "
     "with the three scripts in `src/`; this role is offline because the interface cannot retrain. There is no login: every use case is open to anyone who can reach the server."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the logical data model (CSV and pickle files).",
     "The system has no SQL database, so the diagram shows the logical model of its files. STUDENT_RECORD (19 columns) targets one COMPANY and one ROLE; many students may target the same company. MODEL_ARTIFACT is trained on "
     "the student records, METRICS records how the models were evaluated and PLOT_FILE holds the three images. Relationships are enforced by value only: a `target_company` that is not in `companies.csv` makes the API answer 404."),
    ("flow", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png",
     "Flowchart of the hybrid placement probability computed at serving time.",
     "A feature row of 24 values is built for the student, company and role. The calibrated XGBoost model gives p. If p lies in the borderline band 0.4 to 0.6 the kNN model (k = 9) is consulted and p becomes "
     "0.5 p + 0.5 p_knn; otherwise p is kept. A probability of at least 0.5 is labelled PLACEMENT READY, anything lower NEEDS IMPROVEMENT with skill-gap tips. The band is used because these are the cases where the global model is least sure."),
    ("train", "Training pipeline", "11_training_pipeline.png",
     "Training pipeline of `src/generate_dataset.py`, `preprocess.py` and `hybrid_model.py`.",
     "Eight steps: generate the data, split it 70/15/15 (2,100 / 450 / 450, seed 42), fit the encodings and scaler on the training split only, train six baselines with 9-fold cross-validation for XGBoost, calibrate "
     "XGBoost (sigmoid, three folds), define the residual set (Equation 1 of the technique paper [2]), fit the kNN and SVM local models and save five pickles, `metrics.json` and the SHAP, PCA and histogram plots. "
     "The note on the figure matters: the residual set of Equation 1 uses the true labels of the evaluated rows, which a deployed system does not have (Section 6.6)."),
    ("reco", "Flowchart of the recommendation algorithm", "12_recommendation_flowchart.png",
     "Flowchart of `recommend()` in `src/recommend.py`.",
     "The base probability of the student's own target is computed first (0 when no target is given). Each company is then tested against the feasibility rules; a feasible company is scored for four roles and "
     "each candidate receives score = p + 0.05 x proximity + 0.02 x location bonus. Candidates are sorted by score and three lists are cut from them: company-only (best role per company), role-only (the target "
     "company with other roles) and hybrid (the best five pairs). The average gain and the match rate are computed over the hybrid items that beat the base probability."),
]


def _dg(key):
    for k, t, f, c, x in DIAGRAMS:
        if k == key:
            return t, f, c, x
    raise KeyError(key)


def _fig_text(key, width=5.6, with_text=True):
    t, f, c, x = _dg(key)
    out = [FIG(F.diag(f), c, width)]
    if with_text:
        out.append(P(x))
    return out


ENDPOINTS = [
    ["GET", "/api/health", "status, models_ready (true when all four model files exist)", "-"],
    ["GET", "/api/meta", "branches (6), degrees (2), predict_roles (6), recommend_roles (4), locations (6), companies (30 names)", "-"],
    ["GET", "/api/companies", "All 30 company rows: Company, Tier, CGPA_Cutoff, Apt_Cutoff, Tech_Cutoff, Package_LPA, Location, Company_Type, Hiring_Rate", "-"],
    ["GET", "/api/metrics", "Content of `models/metrics.json`: results per model, cv_xgb_9fold, brier_platt, residual_rate, test_size", "503 file missing"],
    ["GET", "/api/stats", "total, placed_rate, avg_cgpa, by_branch placed rates", "503 dataset missing"],
    ["GET", "/api/plots/{name}", "PNG of prob_hist, pca or shap", "404 other name or file missing"],
    ["POST", "/api/predict", "In: profile (11 numbers, branch, degree) + target_company + target_role. Out: placement_probability, eligible, label, company, role, company_detail, tips", "404 unknown company, 422 out of range or wrong type"],
    ["POST", "/api/recommend", "In: 9 numbers, branch, optional target_company, target_role, location. Out: base_prob, company_only, role_only, hybrid, avg_gain, match_rate", "404 unknown company, 422"],
    ["POST", "/api/recruiter/shortlist", "In: min_cgpa, min_apt, branch (or ALL). Out: total_matches, students (at most 50, sorted by CGPA then Technical_Score)", "422 out of range"],
]

MODULES = [
    ["src/generate_dataset.py", "121", "Company table (30 tuples), synthetic students and the logit label model; writes `data/*.csv`", "`COMPANIES`, `SEED = 42`"],
    ["src/preprocess.py", "69", "Frequency encoding, z-score, six engineered features; saves `preprocess.pkl`", "`build_features`, `load_raw`"],
    ["src/hybrid_model.py", "186", "Split, six baselines, 9-fold CV, Platt calibration, residual hybrid, SHAP/PCA/histogram plots", "`main`, `metrics`"],
    ["src/recommend.py", "132", "Single-row features, calibrated probability with kNN blend, feasibility filters, three recommendation lists", "`predict_for`, `recommend`, `delta_max_cgpa`"],
    ["backend/main.py", "221", "Nine FastAPI endpoints, Pydantic models, CORS, tips, error mapping", "`predict`, `recommend_endpoint`, `shortlist`"],
    ["app.py + templates/ + static/style.css", "140 + 99 + 12", "Original Flask interface: five pages and `POST /api/predict`", "`predict`, `recommend_page`, `dashboard`"],
    ["frontend/src", "3,017", "Six React pages, UI kit, charts, three.js backdrop, activity log, command palette", "`Predict.jsx`, `Recommend.jsx`, `api.js`"],
    ["scripts/", "1,256", "Smoke test, edge tests, experiments, diagrams and screenshot capture written or kept for this work", "`smoke_test.py`, `edge_tests.py`"],
    ["run.bat", "70", "Creates `.venv`, installs packages, trains if needed, installs npm packages, starts both servers", "-"],
]

STORAGE = [
    ["`data/placement_dataset.csv`", "3,000 student records, 19 columns (277 KB)", "CSV, one row per student"],
    ["`data/companies.csv`", "30 companies with tier, cutoffs, package, location, type, hiring rate (1.4 KB)", "CSV"],
    ["`models/preprocess.pkl`", "Frequency maps, scaler (mean, sd), feature names (2.7 KB)", "Python pickle"],
    ["`models/xgb_calibrated.pkl`", "Platt-calibrated XGBoost (1.49 MB)", "Pickle of `CalibratedClassifierCV`"],
    ["`models/knn_residual.pkl`, `svm_residual.pkl`", "kNN (k = 9, 0.42 MB) and RBF SVM (0.20 MB) local models", "Pickle"],
    ["`models/companies.pkl`", "Company table as a DataFrame (4.3 KB; needs `pyarrow` under pandas 3)", "Pickle"],
    ["`models/metrics.json`", "Test metrics of nine models, 9-fold CV, Brier, residual rate (1.5 KB)", "JSON"],
    ["`static/prob_hist.png`, `pca.png`, `shap.png`", "Probability histogram, PCA of the test set, mean |SHAP| bars", "PNG"],
]

SCREENS = [
    ["Landing", "/", "Animated hero, live counters, terminal-style log, three.js wire grid, model table and company marquee"],
    ["Eligibility", "/predict", "Profile form, company and role pickers, probability, label, cutoff comparison, skill-gap tips"],
    ["Recommendations", "/recommend", "Profile form, base probability, average gain, match rate, top pick, chart and three ranked lists"],
    ["Officer dashboard", "/dashboard", "Four KPI tiles, model comparison chart, placed rate by branch, tabs: model table, SHAP, PCA, probabilities"],
    ["Recruiter", "/recruiter", "Filters, sortable paged table of the top 50 matches, CSV export"],
    ["Companies", "/companies", "Searchable, filterable board of the 30 companies"],
]

STUDENT_COLS = [
    ["CGPA", "float", "5.80 - 9.35", "Cumulative grade point average out of 10"],
    ["Tenth_Percent", "float", "45.0 - 93.8", "Class 10 percentage"],
    ["Twelfth_Percent", "float", "40.3 - 89.2", "Class 12 percentage"],
    ["Aptitude_Score", "float", "27.6 - 98.0", "Quantitative and logical aptitude test score"],
    ["Technical_Score", "float", "26.2 - 100", "Technical (core subject) test score"],
    ["Communication_Score", "float", "20.0 - 90.6", "Communication assessment score"],
    ["DSA_Score", "float", "10.0 - 100", "Data-structures and algorithms assessment score"],
    ["Projects, Internships, Certifications", "int", "0-6, 0-4, 0-6", "Counts of completed projects, internships and certifications"],
    ["Backlogs", "int", "0 - 4", "Number of failed subjects still pending"],
    ["Branch", "text", "6 values", "CSE, IT, ECE, EEE, MECH, CIVIL"],
    ["Degree_Type, Student_Type", "text", "2 + 2 values", "BTech / MTech; Regular / Lateral entry"],
    ["Placement_Year", "int", "2023 - 2026", "Year of the placement season"],
    ["Target_Company", "text (FK)", "30 values", "Company the student applied to; must exist in `companies.csv`"],
    ["Target_Role", "text", "8 values", "SDE, Data Analyst, ML Engineer, QA Engineer, DevOps, Support Engineer, Embedded Engineer, Design Engineer"],
    ["Target_Tier", "int", "1, 2, 3", "Tier of the target company (copied from the company table)"],
    ["Placed", "int (label)", "0 / 1", "1 = placed (1,791 rows, 59.7%), 0 = not placed (1,209 rows)"],
]

COMPANY_COLS = [
    ["Company", "text (PK)", "30 names", "Company name, for example Google, Infosys, L&T"],
    ["Tier", "int", "1, 2, 3", "1 = dream (7 companies), 2 = core (15), 3 = mass recruiter (8)"],
    ["CGPA_Cutoff", "float", "6.0 - 8.5", "Minimum CGPA the company usually asks for"],
    ["Apt_Cutoff, Tech_Cutoff", "int", "55 - 85, 50 - 85", "Aptitude and technical score cutoffs"],
    ["Package_LPA", "float", "4.0 - 28.0", "Offered package in lakhs per annum"],
    ["Location", "text", "7 values", "Bangalore, Hyderabad, Chennai, Pune, Mumbai, Noida, Mysore"],
    ["Company_Type", "text", "3 values", "MNC, Startup, Core"],
    ["Hiring_Rate", "float", "0.12 - 0.55", "Share of applicants normally hired; lower for dream companies"],
]


def blocks():
    b = [H1("CHAPTER 5: SYSTEM DESIGN")]
    b += [H2("5.1 Design goals"),
          P("The design follows from the requirements of Chapter 4. It must (i) give one prediction function that every interface uses, so that the Flask pages, the JSON API and the React application always agree; "
            "(ii) run on one ordinary Windows PC without a GPU or a database server; (iii) answer a single prediction in well under a second; (iv) tell the student not only a probability but the specific gaps behind it; "
            "and (v) leave the original Flask application working, so that the new interface is an addition rather than a rewrite."),
          B("**Reuse over rewrite.** `backend/main.py` contains no model logic; every endpoint calls `predict_for`, `recommend` or `pre_comp_cache` from `src/recommend.py`, or reads the same files as the Flask app.",
            "**Files instead of a database.** The data are two small read-only tables and a few model files; a database server would add a dependency without a capability.",
            "**Validate at the edge, explain the result.** Pydantic ranges give 422, an unknown company 404, a missing model 503; the result carries the cutoff comparison and tips, and the dashboard the SHAP ranking.")]
    b += [H2("5.2 System architecture")] + _fig_text("arch", 4.7)
    b += [P("The contract between browser and server is narrow: JSON in both directions. In development the Vite server proxies `/api` to port 8405, so the interface never needs to know the API address and CORS is not exercised; "
            "the API nevertheless allows the two front-end origins (`localhost:5405` and `127.0.0.1:5405`) and no others.")]
    b += [H2("5.3 High-level workflow")] + _fig_text("wf", 4.5, False)
    b += [P("Training (data generation, encoding, split, calibration, residual models) runs offline; every request then loads the saved models. `run.bat` retrains only when the model files are missing.")]
    b += [H2("5.4 Data flow diagrams"), H3("5.4.1 Level 0")] + _fig_text("dfd0", 3.9, False)
    b += [P("A student, a placement officer and a recruiter exchange profiles, filters and results with one process that only reads four stores: student records (D1), companies (D2), models (D3), metrics and plots (D4).")]
    b += [H3("5.4.2 Level 1")] + _fig_text("dfd1", 3.5, False)
    b += [P("Processes 1 and 2 (prepare data, train and evaluate) run offline; processes 3 to 6 (predict, recommend, officer analytics, recruiter shortlist) run per request. Repeated stores are the same store.")]
    b += [H3("5.4.3 Level 2: recommending company-role pairs")] + _fig_text("dfd2", 4.3)
    b += [H2("5.5 UML diagrams"), H3("5.5.1 Class diagram")] + _fig_text("class", 3.7, False)
    b += [P("The code is modules of functions plus four Pydantic classes, so modules are drawn as class boxes; `PredictIn` extends `Profile`, the API calls `recommend.py`, which imports `preprocess.py` and loads the pickled artefacts.")]
    b += [H3("5.5.2 Sequence diagram")] + _fig_text("seq", 3.4)
    b += [H3("5.5.3 Use-case diagram")] + _fig_text("uc", 3.4, False)
    b += [P("Students check eligibility, read tips and get recommendations; officers view metrics, plots and statistics; recruiters shortlist students. The developer role is offline (retraining scripts). There is no login.")]
    b += [H2("5.6 Database design"),
          P("A design chapter normally describes a database, so we state it plainly: this system has no SQL database. The batch description mentions MySQL, but the implemented system stores its data in files, for three reasons. "
            "The data are two small tables (3,000 and 30 rows) that are never modified while the application runs; the models are pickles that must be loaded as a whole; and the users are anonymous, so there are no accounts to store. "
            "The logical data model is therefore described by the data dictionary below and drawn as an entity-relationship diagram. Moving to MySQL would be a natural extension (Chapter 10)."),
          TAB("Data dictionary of `data/placement_dataset.csv` (3,000 rows, 19 columns, no missing values)", ["Column", "Type", "Observed range", "Meaning"], STUDENT_COLS,
              widths=[1.7, 0.8, 1.15, 2.95], align=["l", "c", "c", "l"], size=9.5),
          TAB("Data dictionary of `data/companies.csv` (30 rows, 9 columns)", ["Column", "Type", "Observed range", "Meaning"], COMPANY_COLS,
              widths=[1.7, 0.8, 1.15, 2.95], align=["l", "c", "c", "l"], size=9.5),
          P("Both tables are synthetic: the student records were generated by `src/generate_dataset.py` and the company values are plausible but invented, not real recruiter requirements. Section 6.2 describes the generator.")]
    b += _fig_text("er", 3.9, False)
    b += [P("Persistent files: the two CSV tables (277 KB and 1.4 KB), five pickles in `models/` (xgb_calibrated 1.49 MB, knn_residual 0.42 MB, svm_residual 0.20 MB, preprocess 2.7 KB, companies 4.3 KB), `metrics.json` and three PNG plots in `static/`.")]
    b += [H2("5.7 Module design"),
          P("The table below lists the modules with their sizes (lines, measured with `wc -l`) and responsibilities. The training and serving core is small: 508 lines in four files. The API layer is 221 lines, "
            "the original Flask application 140 lines plus five templates, and the React interface about 3,000 lines of JavaScript."),
          TAB("Module breakdown", ["Module", "Lines", "Responsibility", "Key names"], MODULES, widths=[1.5, 0.6, 3.0, 1.5], align=["l", "c", "l", "l"], size=9.5),
          P("Dependencies run in one direction only: interfaces call `src/recommend.py`, which calls `src/preprocess.py`; the training script uses `preprocess.py` and writes the files that `recommend.py` loads. "
            "No module in `src/` imports Flask, FastAPI or React.")]
    b += [H2("5.8 Algorithm design"), H3("5.8.1 Hybrid prediction")] + _fig_text("flow", 3.2, False)
    b += [P("A 24-value feature row gives the calibrated XGBoost probability p; if 0.4 <= p <= 0.6 it is averaged with the kNN probability; p >= 0.5 is labelled PLACEMENT READY, otherwise NEEDS IMPROVEMENT with tips.")]
    b += [H3("5.8.2 Training pipeline")] + _fig_text("train", 4.4, False)
    b += [P("The residual set of Equation 1 in the technique paper [2] uses the true labels of the evaluated rows, which a deployed system does not have (Section 6.6).")]
    b += [H3("5.8.3 Recommendation")] + _fig_text("reco", 3.2, False)
    b += [P("Each feasible company is scored for four roles with score = p + 0.05 x proximity + 0.02 x location bonus; the sorted candidates give the company-only, role-only and hybrid lists, and the gain and match rate are computed over hybrid items that beat the base probability.")]
    b += [P("Three design choices deserve a reason. The probability is **calibrated** (Platt scaling) because the recommender ranks companies by probability and a ranking is only meaningful if probabilities are comparable [4, 9]. "
            "The local model is applied only in the **borderline band**, where the global model is least certain [2]. The recommender is **filtered before it is scored**, so that it never suggests a company whose CGPA "
            "requirement is far from the student's or a Tier-1 company for a student with more than two backlogs.")]
    b += [H2("5.9 API design"),
          P("The nine endpoints below are the whole server interface; the interactive documentation is generated at `/docs` by FastAPI. Request bodies use Pydantic models, so type and range errors are reported per field."),
          TAB("Endpoints of `backend/main.py`", ["Method", "Path", "Request and response", "Errors"], ENDPOINTS, widths=[0.6, 1.55, 3.45, 1.0], align=["c", "l", "l", "l"], size=9),
          P("Two request models are shared: `Profile` (cgpa 0-10, tenth, twelfth, aptitude, technical, communication, dsa 0-100, projects, internships, certifications, backlogs 0-20, branch, degree) is extended by `PredictIn` with a "
            "company and a role; `RecommendIn` repeats the numeric fields without tenth, twelfth and degree and makes the company, role and location optional; `ShortlistIn` carries min_cgpa, min_apt and branch.")]
    b += [H2("5.10 User interface design"),
          P("The React interface was rebuilt on the *Kinetic Mono* design kit (version 5): a terminal-inspired look with a monospaced accent font, a dark theme by default and a light theme, a navigation sidebar on desktop "
            "that becomes a drawer on small screens, and a slowly moving wire-grid backdrop drawn with three.js. The kit was adapted to this project: the API client, the formatting helpers, the activity log and the chart "
            "components were written for the placement data, and the three.js scene falls back to a plain background when WebGL is unavailable or the user prefers reduced motion."),
          TAB("Screens of the React application", ["Screen", "Route", "Content"], SCREENS, widths=[1.35, 1.0, 4.25], align=["l", "l", "l"], size=10),
          B("**Theme.** Dark and light themes share one set of colour tokens; the choice is stored in the browser and follows the operating-system preference until the user picks one.",
            "**Command palette and shortcuts.** `/` opens a search box that jumps to a company or a screen; `g e`, `g r`, `g d`, `g u`, `g c` go to Eligibility, Recommendations, Officer dashboard, Recruiter and Companies; `g l` opens the activity log; `?` lists the shortcuts and `Esc` closes any overlay.",
            "**Activity log.** A terminal-style panel records every API call with its status and time in milliseconds, every error and every navigation (the last 200 events); it is what the screenshots of the log in Appendix C show.",
            "**States.** Every data-driven screen has a loading skeleton, an empty state that says what to do, and an error state with a retry button; `describeError` turns a network failure into \"Could not reach the placement API\" with the command that starts the backend, a 503 into a pointer to the setup guide, and a 422 into the per-field message.",
            "**Forms and motion.** The profile forms validate ranges before sending, using the same ranges as the server; counters, the typewriter headline and the backdrop respect `prefers-reduced-motion`, and pages are code-split so that three.js and the chart library load only when needed."),
          PAIR([(F.shot("02_predict.png"), "Eligibility screen with a real prediction (Microsoft, SDE)."),
                (F.shot("04_dashboard.png"), "Officer dashboard overview.")], 3.1),
          ]
    return b
