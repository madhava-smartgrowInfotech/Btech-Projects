"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .lit import OBJECTIVES


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    hl, hk, xc = F.R["hybrid_knn_labelfree"], F.R["hybrid_xgb_knn"], F.R["xgb_calibrated"]
    return [
        H2("2.1 What is new, and what is not"),
        P("This project does not propose a new learning algorithm, and we do not claim one. Gradient boosting [3], Platt scaling [4], nearest-neighbour classification [7], SHAP [5] and the Brier score [8] are standard. "
          "The work is an *adaptation* of a published framework to a new domain, a delivery of that framework as a working web application, and an evaluation that is more critical than the source it adapts. This section states the "
          "difference from both base papers and then separates the standard from the project-specific."),
        H2("2.2 Difference from the two base papers"),
        TAB("The project against the declared base paper [1] and the technique source [2]", ["Dimension", "IJETMS placement paper [1]", "Hybrid admission paper [2]", "This project"],
            [["Problem", "Predict placement from student attributes", "Predict graduate admission and recommend universities and programs", "Predict placement for a chosen company and role and recommend company-role alternatives"],
             ["Data", "Synthetic, size not stated", "13,000 real GradCafe records", "3,000 synthetic students, 30 invented companies with cutoffs"],
             ["Core technique", "Logistic Regression, Random Forest, Gradient Boosting", "XGBoost + Platt + kNN/SVM refinement of residual cases + SHAP", "The framework of [2] with company-specific gap features and a recruiter-facing interface"],
             ["Recommendation", "None; skill-gap analysis only", "University, program and hybrid strategies with feasibility filters", "Company, role and hybrid strategies; CGPA tolerance by tier; aptitude and backlog filters; location preference"],
             ["Evaluation", "No numeric result reported", "One split, accuracy 0.8723 for the hybrid", "One split plus five-seed study, threshold and band sweeps, calibration, label-free variant"],
             ["Deliverable", "Streamlit app with CSV batch, PDF and e-mail", "A method; no application", "Flask and FastAPI back ends, React interface, officer dashboard, recruiter shortlist"]],
            widths=[1.0, 1.6, 1.9, 2.1], align=["l", "l", "l", "l"], size=9),
        P("The batch documents name the IJETMS paper [1] as the base paper and describe the project as reusing its technique, while the code and the README are built on [2]. We state what was taken from each. From [1] we took the problem "
          "(placement prediction from student attributes with skill-gap feedback) and its interface ideas; its method is a standard comparison of three classifiers and gave no numbers to reproduce. From [2] we took the complete modelling "
          "framework: frequency encoding, standardisation, a 70/15/15 split, nine-fold cross-validation, the XGBoost hyper-parameters, Platt scaling, the residual hybrid, SHAP, PCA, the feasibility filters and the proximity score."),
        H2("2.3 The mapping from admission to placement"),
        TAB("How each element of [2] was mapped to placement", ["Admission paper [2]", "This project", "Where in the code"],
            [["University", "Company", "`Target_Company`, `companies.csv`"], ["Program", "Role", "`Target_Role`"], ["QS rank", "Company tier (1 dream, 2 core, 3 mass)", "`Target_Tier`"],
             ["Applicant GPA and GPA requirement", "CGPA, aptitude and technical score against the company's cutoffs", "`CGPA_Gap`, `Apt_Gap`, `Tech_Gap` in `build_features`"],
             ["Program admission rate", "Company hiring rate", "`Company_Hiring_Rate`"], ["Program x QS rank", "CGPA x tier", "`CGPA_x_Tier`"],
             ["Delta-max GPA by QS rank", "Delta-max CGPA by tier: 0.6, 1.0, 1.5", "`delta_max_cgpa`"], ["Country and budget filters", "Location preference and minimum package", "`prefer_location`, `min_package`"],
             ["University-only, program-only, hybrid", "Company-only, role-only, hybrid", "`recommend()`"]],
            widths=[2.0, 2.6, 2.0], align=["l", "l", "l"], size=9.5),
        H2("2.4 Standard components and project-specific elements"),
        TAB("Standard components and project-specific elements", ["Element", "Standard or new", "Comment"],
            [["XGBoost, Random Forest, SVM, kNN, Logistic Regression, Decision Tree", "Standard", "Used through scikit-learn [6] and XGBoost [3]"],
             ["Platt scaling, Brier score, SHAP, PCA", "Standard", "As in [2]"],
             ["Gap features against company cutoffs", "Project-specific", "Turns company-independent scores into company-specific distances; they are the three most useful features after backlogs"],
             ["Residual hybrid with true labels (Eq. 1 of [2])", "Taken from [2]", "Reproduced as published, and reported on the dashboard"],
             ["Label-free serving rule and the evaluation of it", "New measurement", f"The gain of {hk['accuracy'] - xc['accuracy']:.3f} accuracy falls to {hl['accuracy'] - xc['accuracy']:.4f} when the labels are not used"],
             ["Rule-based skill-gap tips", "Project-specific", "Four rules on the cutoffs and internships; not a learned explanation"],
             ["Company-role recommendation with feasibility filters", "Adapted from [2]", "Three strategies; probability plus proximity plus location bonus"],
             ["FastAPI layer over unchanged core code, React interface", "Project-specific", "The Flask application and the web application use the same `src/` functions"],
             ["Officer dashboard and recruiter shortlist", "Project-specific", "Not present in [1] or [2]"]],
            widths=[2.7, 1.2, 2.7], align=["l", "c", "l"], size=9.5),
    ]


def contribution_blocks():
    hl, hk, xc = F.R["hybrid_knn_labelfree"], F.R["hybrid_xgb_knn"], F.R["xgb_calibrated"]
    return [
        P("The key contributions, in the order in which the evidence supports them, are:"),
        N("**A complete placement-prediction and recommendation system** - synthetic data generator, feature pipeline, six baselines, calibrated XGBoost, hybrid refinement, company-role recommendation, officer dashboard, "
          "recruiter shortlist, Flask and FastAPI interfaces and a React front end - that runs on one CPU-only PC with one command (`run.bat`).",
          "**An adaptation of the hybrid framework of [2] from admissions to placement**, including company-specific gap features (CGPA, aptitude and technical gap against the target company's cutoff), a tier-dependent CGPA tolerance and "
          "a recommendation module with three strategies.",
          f"**A reproducible measurement of the models.** Accuracy {F.R['xgb_calibrated']['accuracy']:.4f} for calibrated XGBoost and ROC-AUC {F.R['logreg']['roc_auc']:.4f} for the best model (Logistic Regression) on 450 held-out students, with confusion matrices, a threshold sweep, calibration and a five-seed study, "
          "all regenerated by `scripts/run_experiments.py`.",
          f"**An honest evaluation of the hybrid refinement.** The accuracy gain of the paper rule ({hk['accuracy']:.4f} against {xc['accuracy']:.4f}) disappears when the residual set is chosen without the true labels ({hl['accuracy']:.4f}), "
          "and the base paper's rule has the same property. This finding changes how the hybrid should be described.",
          "**A recommendation module with measured behaviour**: for 60 students rated below 0.5 for their own target, 52 receive a better alternative; the mean estimated gain is 43.7 percentage points, and its limits "
          "(preference for Tier-3 companies, empty role-only list, 3 to 8 seconds per request) are documented.",
          f"**Engineering quality.** {F.TEST_SUMMARY['total']} behaviour checks (all pass), a {F.SMOKE_TOTAL}-check smoke test, ten real screenshots, twelve diagrams drawn from the code, and scripts that regenerate every number in the documents."),
    ]


# ------------------------------------------------------------------ document 10
def scope_blocks():
    return [
        H2("1.1 In scope"),
        P("The scope is what the delivered system does and was tested to do. Each item exists in the code base and has the evidence named in the last column."),
        TAB("Features in scope", ["No.", "Feature", "Where", "Evidence"],
            [["1", "Synthetic campus dataset (3,000 students, 30 companies), reproducible with seed 42", "`src/generate_dataset.py`", "`data/*.csv`, REPORT_FACTS"],
             ["2", "Feature pipeline: frequency encoding, standardisation, six engineered features (24 in all)", "`src/preprocess.py`", "Unit test U2"],
             ["3", "Training and comparison of six classifiers, Platt calibration and the hybrid refinement", "`src/hybrid_model.py`", "`models/metrics.json`; Chapter 8"],
             ["4", "Placement probability, label and skill-gap tips for a student, company and role", "`POST /api/predict`, Eligibility screen", "Functional tests F1, F2; screenshot"],
             ["5", "Company-role recommendation: company-only, role-only and hybrid lists, base probability, average gain, match rate", "`POST /api/recommend`, Recommendations screen", "Tests F3 to F5; Chapter 8"],
             ["6", "Officer dashboard: model metrics, SHAP, PCA, probability histogram, placed rate by branch", "`GET /api/metrics`, `/api/stats`, `/api/plots/*`", "Integration tests I4 to I8"],
             ["7", "Recruiter shortlist by CGPA, aptitude and branch (top 50)", "`POST /api/recruiter/shortlist`", "Test F6"],
             ["8", "Companies board with tiers, cutoffs, packages and hiring rates", "`GET /api/companies`", "Test I3"],
             ["9", "Original Flask interface and the React interface over the same core", "`app.py`, `backend/`, `frontend/`", "Screens in Chapter 8"]],
            widths=[0.4, 3.0, 1.9, 1.3], align=["c", "l", "l", "l"], size=9),
        H2("1.2 Out of scope"),
        B("**Real placement data.** No record of a real student or company is used.",
          "**Accounts and permissions.** There is no login for students, recruiters or officers.",
          "**A database.** The batch description names MySQL; the system reads CSV and pickle files.",
          "**Uploading data or retraining from the interface.** Retraining is by command line (`python src/hybrid_model.py`).",
          "**Batch prediction from a CSV file, PDF reports and e-mail**, which the base paper [1] offers.",
          "**Matching against job-description vectors**, mentioned in the batch documents.",
          "**Resume parsing, interview scheduling, offer tracking and any communication with companies.**",
          "**Fairness and bias auditing** across branches, gender or institution.")]


def assumption_blocks():
    return [
        P("The system and its evaluation rest on the following assumptions. Where an assumption is doubtful it is repeated as a limitation."),
        N("The synthetic students and the generated placement labels are a plausible stand-in for a real campus. This is an assumption, not a fact; no real data was available.",
          "The 30 companies, their cutoffs, packages, locations and hiring rates are plausible; they were written by hand for the project and are not published recruiter requirements.",
          "A student's placement chance depends on the student's profile and the target company's tier and cutoffs; no calendar effects, interview performance or luck other than the generator's noise are modelled.",
          "The same profile fields are available for every student when the model is used (CGPA, 10th and 12th percentages, five scores, counts of projects, internships, certifications and backlogs, branch, degree).",
          "The user runs the application on one PC on localhost; the back end trusts the front end's origin.",
          "A placement probability of 0.5 or more means READY. The threshold is conventional and was not tuned (Chapter 8)."),
    ]


def limitation_blocks():
    return [
        P("Each limitation is stated with its consequence and with what would address it. The numbering L1 to L14 is used in the other chapters."),
        TAB("Limitations", ["ID", "Limitation", "Consequence", "What would address it"],
            [["L1", "All student and company data are synthetic", "No accuracy figure is a claim about real placements; real data are noisier (the base paper's baselines reach 0.68 to 0.73 [2])", "Data from the placement cell, with consent and anonymisation"],
             ["L2", "Labels follow a logistic rule with noise (sd 0.8)", "Logistic Regression is as good as or better than XGBoost; SHAP recovers the generator's rule", "Real outcomes; or a generator with non-linear interactions"],
             ["L3", "The hybrid gain uses true labels to pick the residual set", f"Accuracy {F.R['hybrid_xgb_knn']['accuracy']:.4f} falls to {F.R['hybrid_knn_labelfree']['accuracy']:.4f} without them; the dashboard still reports the first", "Report the label-free rule; train a classifier to recognise residual rows"],
             ["L4", "One 450-student test set, one retraining study on the same 3,000 students", "One student is 0.22 points; differences of 1 to 2 points are within one standard deviation", "A larger real test set; temporal split by placement year"],
             ["L5", "Invented company table", "Cutoffs, packages and hiring rates are not real", "Real recruiter requirements"],
             ["L6", "No authentication, authorisation or rate limiting", "Every endpoint is public, so the application is for a single machine", "Roles (student, officer, recruiter), tokens and quotas"],
             ["L7", "No database, no upload, no retraining from the interface", "The data cannot be updated by users; changes need a script run", "A database and an admin retraining job"],
             ["L8", "Free-text branch and role are not validated against the training categories", "An unknown value is accepted (HTTP 200) and scored with frequency 0", "Enumerations in the request models"],
             ["L9", "The recommendation module reloads four pickles per candidate", "3 to 8 seconds per request (mean 5.4 s over HTTP)", "Load the artefacts once per process"],
             ["L10", "Recommendation ranks by probability only", "Weak profiles are sent to Tier-3 companies; the role-only list is empty when the target is infeasible", "Add package, interest and fit to the score; explain empty lists"],
             ["L11", "Skill-gap tips are four fixed rules; SHAP is global", "A tip is not an explanation of one student's probability", "Per-student SHAP values; ranked actions"],
             ["L12", "Pickles are tied to library versions (pandas 3 needs pyarrow)", "Models may not load on other versions", "Pin versions or export to a portable format"],
             ["L13", "Tested on one CPU-only PC, sequential calls, no browser test suite", "No statement about concurrency, other platforms or browsers", "Load test, CI, cross-browser tests"],
             ["L14", "Batch CSV prediction, PDF and e-mail reports, MySQL not implemented", "Less functionality than the base paper's application", "See Chapter 10"]],
            widths=[0.4, 2.0, 2.4, 1.8], align=["c", "l", "l", "l"], size=9),
        P("Two figures illustrate limitations L3 and L4. The first shows the accuracy of four models on each of five random splits: the label-free hybrid is level with calibrated XGBoost, while the paper-rule hybrid is ahead in "
          "every split. The second shows the decision-threshold analysis: accuracy is flat between 0.30 and 0.70, so the choice of threshold changes the kind of error but not the amount."),
        FIG(F.fig("multi_seed.png"), "Test accuracy on five random splits (limitations L3 and L4).", 4.8),
        FIG(F.fig("threshold_sweep.png"), "Precision, recall, F1 and accuracy against the decision threshold.", 4.6),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and no figure for them appears in any document:"),
        B("**Accuracy on real students or real companies.** The data do not contain any.",
          "**Whether recommended alternatives lead to placements.** The gains are model-estimated.",
          "**Fairness**: whether the probability differs by branch, gender, school or other group for equal merit (the synthetic data have almost no branch effect by construction).",
          "**Behaviour under concurrent users** and on other hardware, operating systems or browsers.",
          "**Usability.** No user study was carried out; no satisfaction or task-time figure exists.",
          "**Energy use and memory** of training and serving.",
          "**Accuracy of the other published works** in a common comparison; their reported numbers use other data and are not reproduced here.",
          "**The LightGBM model** that the base paper compares; it is optional in the code and the package is not installed on the build machine."),
    ]


# ------------------------------------------------------------------ document 12
def walkthrough_blocks():
    return [
        P("This section walks through the code that carries the design. The listings are copied from the repository."),
        H2("3.1 Features: from a student record to 24 numbers"),
        CODE(src("src/preprocess.py", 26, 55), 8.0),
        P("`build_features` joins the student rows with the company table on the target company, then derives six features. `Skill_Index` is a weighted mean of technical (0.4), aptitude (0.3), communication and DSA (0.15 each). "
          "`CGPA_Gap`, `Apt_Gap` and `Tech_Gap` are the student's score minus the company's cutoff, which makes the same student look different for different companies. When `fit` is true the function learns the frequency maps "
          "of the five categorical columns and the mean and standard deviation of 19 numeric columns; otherwise it applies the stored ones. Fitting on the training split only avoids leakage of the test distribution."),
        H2("3.2 Calibration and the residual hybrid"),
        CODE(src("src/hybrid_model.py", 95, 127), 8.0),
        P("XGBoost is wrapped in `CalibratedClassifierCV` with the sigmoid (Platt) method and three folds. The residual mask is the union of the rows that the calibrated model gets wrong and the rows whose probability is between 0.4 and 0.6. "
          "The expression `pred_xgb != yte` uses the test labels, which is why this version of the hybrid cannot be applied to a new student (Chapter 8). The kNN and SVM local models are fitted on the whole training set and "
          "applied to the masked rows only."),
        H2("3.3 The serving rule"),
        CODE(src("src/recommend.py", 70, 78), 8.5),
        P("This is what the running system does. It loads the artefacts, builds the feature row, and takes the calibrated probability. Only if the probability is in the band 0.4 to 0.6 does it average it with the kNN probability. "
          "The rule uses no label. Note that `load_artifacts()` reads four pickle files on every call, which is the source of the latency reported in Chapter 7."),
        H2("3.4 Feasibility filters and scoring in the recommendation module"),
        CODE(src("src/recommend.py", 96, 117), 8.0),
        P("A company is a candidate only if the student's CGPA is within the tier tolerance of the cutoff, the aptitude score is at most 15 points below the cutoff, the student is not a Tier-1 candidate with more than two backlogs, and the package is high enough. "
          "For each surviving company the module scores up to four roles. The score is the probability plus 0.05 times the CGPA proximity plus a 0.02 bonus for the preferred location. "
          "Because the probability dominates, the easiest companies tend to win for weak profiles."),
        H2("3.5 The prediction endpoint"),
        CODE(src("backend/main.py", 189, 202), 8.5),
        P("The endpoint looks the company up (404 if unknown), dumps the validated profile, calls `predict_for` and returns the probability, the label, the company row and the tips. Pydantic has already enforced the ranges (422); "
          "an exception raised inside the model code (for example from an unseen value) becomes a 422 with the message."),
    ]


def decision_blocks():
    return [
        P("Each decision below is stated with the alternative that was available and the reason for the choice."),
        TAB("Implementation decisions", ["Decision", "Alternative", "Reason"],
            [["Add a FastAPI layer that imports `src/recommend.py` unchanged", "Rewrite the model code inside the API", "One code path: the Flask and React applications cannot disagree; the modelling code kept its tests and metrics"],
             ["Frequency encoding of categorical columns", "One-hot encoding", "As in the base paper [2]; avoids 30 company columns and keeps the feature count at 24. Costs: unseen categories get 0 silently (L8)"],
             ["Standardise numeric features, fitted on the training split", "Leave raw", "Required for kNN and SVM and harmless for trees; fitting on training data avoids leakage"],
             ["Company-specific gap features", "Raw scores only", "A score of 79 is good for one company and bad for another; the gap features are the top-ranked ones by SHAP"],
             ["XGBoost as the main model, with Platt scaling", "Logistic Regression, which was the best by AUC", "Follows the base paper and gives a non-linear model that would matter on real data; the choice is not supported by this synthetic data (Chapter 8)"],
             ["Decision threshold 0.5", "Tune on the validation set", "Accuracy is flat from 0.30 to 0.70; 0.5 is conventional and simple to explain"],
             ["Residual band 0.4 to 0.6 with a 50/50 blend at serving time", "The paper's label-based rule", "The label-based rule cannot run on a new student; the blend is a soft, label-free substitute whose effect is negligible"],
             ["Load pickles on every call", "Cache the artefacts in memory", "Simplicity of the original code; accepted at documentation time, flagged as limitation L9"],
             ["CSV and pickle files, no database", "MySQL named in the batch description", "Nothing in the system needs queries, updates or concurrency; one fewer dependency"],
             ["React with Vite, Tailwind, Recharts and a three.js backdrop", "Server-rendered Flask templates", "Interactive charts, tables and a command palette; the original Flask interface was kept as the reference"],
             ["CORS restricted to ports 5405 on localhost", "Allow all origins", "Smallest exposure for a single-machine application; checked by tests S5 and S6"],
             ["Synthetic data from a logistic label model", "Search for public placement data", "No real placement data was available; the generator is reproducible with seed 42; the consequence is stated everywhere (L1, L2)"]],
            widths=[2.2, 1.8, 2.6], align=["l", "l", "l"], size=9.5),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def conclusion_blocks():
    R = F.R
    xc, hk, hl, lr = R["xgb_calibrated"], R["hybrid_xgb_knn"], R["hybrid_knn_labelfree"], R["logreg"]
    rec = F.REC
    return [
        H2("9.1 Summary"),
        P("The Smart Campus Placement System estimates the probability that a student is placed at a chosen company and role, tells the student which gaps against the company's cutoffs hold the probability back, recommends "
          "company-role alternatives with a higher estimated probability, and gives placement officers and recruiters a dashboard and a shortlist. It adapts the hybrid XGBoost and kNN framework of Heidari Fard and Tabrizi [2] "
          "from graduate admissions to campus placement and delivers it as a Flask application and as a FastAPI service with a React interface. Because no real placement data were available, the system was built and evaluated on "
          "3,000 synthetic students and 30 invented companies; this governs how every result in this report must be read."),
        FIG(F.fig("model_comparison.png"), "Accuracy, F1 and ROC-AUC of the models on the held-out test set (seed 42).", 4.6),
        H2("9.2 Objectives achieved"),
        P("Of the six objectives, three were met (training and comparing classifiers, recommending companies, dashboards with evaluation), one was met in part (skill gaps, as cutoff rules and a global SHAP ranking), and two were "
          "met only partly (the data are synthetic; encoding was done but no resampling was needed or applied for the 59.7 / 40.3 class split). The table gives the status of each."),
        TAB("Objectives and their status", ["No.", "Objective", "Status", "Basis"],
            [[str(i), o, st, why] for i, (o, st, why) in enumerate(zip(OBJECTIVES, ["Partly met", "Partly met", "Met", "Met", "Met in part", "Met"], [
                "3,000 synthetic records; no real placement data", "Encoding and scaling done; classes 59.7 / 40.3, no resampling applied",
                "Six baselines, calibrated XGBoost and two hybrids; five-seed study", "Hybrid top-5 with three strategies; gains are model-estimated",
                "Cutoff rules and global SHAP ranking; no per-student explanation", "Officer dashboard, recruiter shortlist; accuracy, precision, recall, F1, AUC, Brier"]), 1)],
            widths=[0.4, 2.5, 0.8, 2.9], align=["c", "l", "c", "l"], size=9.5),
        H2("9.3 Key findings"),
        N(f"Calibrated XGBoost reaches {xc['accuracy']:.4f} accuracy, F1 {xc['f1']:.4f} and ROC-AUC {xc['roc_auc']:.4f} on 450 held-out synthetic students; Logistic Regression has the highest AUC ({lr['roc_auc']:.4f}) and ties the best accuracy ({lr['accuracy']:.4f}), as expected for labels generated by a logistic rule.",
          f"The hybrid XGBoost + kNN of the base paper scores {hk['accuracy']:.4f}, but only because its residual set is chosen with the true labels. With the label-free rule it scores {hl['accuracy']:.4f}, one student above XGBoost; over five splits the label-free hybrid ({F.ms('hybrid_knn_labelfree')}) and calibrated XGBoost ({F.ms('xgb_calibrated')}) are indistinguishable.",
          "The company-specific gap features (CGPA, technical and aptitude gap against the cutoff) and the number of backlogs carry most of the model's SHAP importance. This reflects how the data were generated.",
          f"Calibration helps a little (Brier {F.CAL['brier_raw_xgb']:.4f} to {F.CAL['brier_platt']:.4f}); the accuracy is flat from threshold 0.30 to 0.70, so the threshold trades precision (0.78 to 0.87) against recall (0.92 to 0.79).",
          f"The recommendation module gives {rec['with_at_least_one_better_alt']} of {rec['students']} students rated below 0.5 for their own target at least one better alternative, with a mean estimated gain of {rec['mean_avg_gain_over_improved'] * 100:.1f} percentage points; it favours Tier-3 companies and takes 3 to 8 seconds per request.",
          f"The software is sound for its purpose: all {F.TEST_SUMMARY['total']} behaviour checks and the {F.SMOKE_TOTAL}-check smoke test pass, input is validated, and hostile inputs are refused."),
        H2("9.4 Practical applications"),
        B("**A placement cell's planning tool.** After training on a cell's own anonymised history, the officer dashboard shows which profile factors and which students are close to the decision boundary, so that training effort can be directed early.",
          "**A student self-assessment.** A student can see the probability for a target company and the specific gaps against its cutoffs, and compare alternatives.",
          "**A recruiter's first filter.** The shortlist screen narrows a campus list by CGPA, aptitude and branch.",
          "**A teaching case.** The project shows the whole cycle of data, features, comparison, calibration, explanation, recommendation and deployment, and shows how to check a published evaluation protocol for leakage."),
        H2("9.5 Known limitations"),
        P("The system was not evaluated on real students, so no claim is made about real placement accuracy. The reported hybrid gain depends on the true labels. The recommender can send weak profiles to the easiest companies and is slow. "
          "The API has no authentication and accepts unknown categories. Tips are fixed rules. The tests were written by the team and cover behaviour, not real-world performance. The system is a prototype for a placement cell "
          "to adapt with its own data, not a validated decision tool, and its output must not be used to decide the fate of a student. The full list is limitations L1 to L14 in the scope and limitations document."),
        H2("9.6 Lessons learned"),
        B("**Check what a published evaluation needs at prediction time.** The headline gain of a hybrid model vanished when the information that is available at serving time was the only information used. A rule that is defined with the answer in hand needs a label-free twin before it is reported.",
          "**Report the spread, not one draw.** On 450 test students and five splits the standard deviation (1 to 2 points) was as large as most differences between models; a single table would have suggested a ranking that does not exist.",
          "**A recommendation that maximises probability is not a good recommendation.** Ranking by probability alone sends weak profiles to the easiest companies; the objective must include what the student wants."),
    ]


def future_blocks():
    return [
        H2("10.1 Improvements to the models and the data"),
        B("**Use real data first.** Obtain anonymised placement records and recruiter requirements from the placement cell, retrain, and report the accuracy on a temporal split (train on earlier years, test on the latest). This is the single most important missing measurement.",
          "**Train the residual refinement without labels.** Learn a classifier that predicts which rows XGBoost gets wrong from features and probability, and apply the kNN or SVM only to those rows; report the gain on held-out data. This replaces the label-dependent rule of [2].",
          "**Re-examine the model choice.** Compare gradient boosting with logistic regression, regularised trees and LightGBM [14] on real data, with repeated cross-validation, and test whether the hybrid adds value there.",
          "**Per-student explanations.** Compute SHAP values for the student at hand [5] and rank the actions that raise the probability most, instead of the four fixed rules.",
          "**Fairness audit.** Check calibration and error rates across branch, gender and school; report differences before the system is used for any decision."),
        H2("10.2 Additional features"),
        B("**Better recommendation scoring.** Combine probability with package, role fit, location and the student's stated interests; explain why a company is excluded and avoid empty lists.",
          "**Batch prediction from a CSV file, PDF reports and e-mail**, as offered by the base paper [1].",
          "**Accounts and roles** for students, officers and recruiters, with a student seeing only their own data.",
          "**MySQL storage** as named in the batch description, with an officer page to upload placement results and retrain.",
          "**Job-description matching**: represent requirements as vectors and match them with skill profiles.",
          "**Skill-improvement planning**: turn a gap into a schedule of mock tests and courses and track progress over a term."),
        H2("10.3 Scalability and deployment"),
        B("**Cache the loaded artefacts** once per process so that a recommendation takes tens of milliseconds, not seconds; score all candidate rows in one vectorised call.",
          "**Pin library versions or export the models** to a portable format; add a model registry with version and training-date metadata.",
          "**Container image and reverse proxy** with authentication, HTTPS, rate limits and restricted origins before any network use.",
          "**Continuous testing.** Run the 46 checks, the smoke test and the experiments script in a CI pipeline on every change, and add browser tests for the main screens.",
          "**Monitoring.** Log prediction requests (without personal data), track the distribution of inputs and detect drift when a new batch of students arrives."),
        H2("10.4 Further research"),
        B("Study whether the label-dependence of residual refinement affects other published hybrid classifiers, by re-evaluating them with a label-free selection rule.",
          "Test counterfactual recommendations: whether a student who improves the recommended gap actually moves in probability, using real longitudinal records.",
          "Combine placement prediction with salary or package prediction (a regression task) to rank alternatives by expected value and not only by probability.",
          "Run a user study with students, officers and recruiters to measure whether the dashboard changes how training is planned."),
        H2("10.5 Suggested roadmap"),
        TAB("A sequence in which the work above could be done", ["Phase", "Work", "Outcome", "Effort"],
            [["1", "Cache loaded artefacts; validate branch and role against the training categories; explain empty lists", "Recommendation in tens of milliseconds; no silent unknown categories", "Days"],
             ["2", "Collect anonymised placement history and company requirements from the placement cell; retrain; temporal test", "The first real accuracy figure", "Weeks, depends on data access"],
             ["3", "Label-free residual selection; compare with logistic regression and LightGBM [14]", "A defensible statement about the value of the hybrid", "Weeks"],
             ["4", "Accounts, roles, MySQL, CSV batch prediction, PDF and e-mail reports", "Parity with the base paper [1] and a multi-user deployment", "Weeks to months"],
             ["5", "Per-student explanations, richer recommendation scoring, fairness audit", "Advice a student can act on; evidence of equal treatment", "Months"],
             ["6", "Pilot with a placement cell and a user study", "Evidence that the tool changes planning", "A placement season"]],
            widths=[0.6, 2.8, 2.2, 1.0], align=["c", "l", "l", "c"], size=9.5),
    ]


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + future_blocks()
