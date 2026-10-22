"""Chapter 6: Methodology and Software Implementation. methodology_blocks() feeds document 9, application_blocks() feeds document 12."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB

SEED_NOTE = "seed 42"


def _bandrow(r):
    return [f"{r['lo']:.2f} - {r['hi']:.2f}" if r["replaced"] else "none", str(r["replaced"]), f"{r['accuracy']:.4f}", f"{r['f1']:.4f}", f"{r['roc_auc']:.4f}"]


def methodology_blocks():
    R, C, S = F.R, F.CONF, F.RES
    b = []
    b += [H2("6.1 Overall methodology"),
          P("The method is a supervised tabular-classification pipeline followed by a ranking step. A student profile and a target company are turned into a vector of 24 features; a calibrated gradient-boosted model "
            "returns the probability of placement; a local nearest-neighbour model refines the probability when it is borderline; and a recommendation step repeats the computation over feasible companies and roles to find "
            "alternatives with a higher probability. The design is adapted from the technique paper [2], which solved the same two-stage problem for graduate admissions, and extends the declared base paper [1], which predicts "
            "placement only. The steps are:"),
          N("**Generate** 3,000 synthetic student records and a table of 30 companies (Section 6.2).",
            "**Encode and scale** the records into 24 features, fitting the encodings on the training split only (Section 6.3).",
            "**Split** the records 70/15/15 with a stratified split (seed 42): 2,100 training, 450 validation and 450 test rows.",
            "**Train** six baseline classifiers and compare them on the test split; run 9-fold cross-validation for XGBoost on the training split.",
            "**Calibrate** the XGBoost probabilities with Platt scaling (sigmoid, three folds) so that they can be compared across companies.",
            "**Refine** borderline cases with a kNN or SVM model fitted on all training rows (the residual hybrid).",
            "**Serve** predictions through `predict_for` and recommendations through `recommend`; explain with cutoff gaps, rule-based tips and a SHAP ranking."),
          ]

    b += [H2("6.2 Dataset"),
          P("**The data are synthetic, and this is the most important fact about the results.** No real student records were available for this project, so `src/generate_dataset.py` draws them from fixed distributions with "
            "numpy seed 42. The declared base paper [1] also states that it generated a synthetic dataset, for the same reason. The file `data/placement_dataset.csv` has 3,000 rows and 19 columns; `data/companies.csv` "
            "has 30 invented but plausible companies (7 Tier-1, 15 Tier-2, 8 Tier-3) with CGPA, aptitude and technical cutoffs, package, location, type and hiring rate."),
          P("Academic scores are generated from CGPA with noise so that they correlate, as they do in practice. With N(m, s) denoting a normal draw: CGPA = clip(5.6 + 3.8 Beta(3.5, 2.5), 5, 10); "
            "Tenth = 9 CGPA + N(0, 4); Twelfth = 8.6 CGPA + N(0, 5); Aptitude = 40 + 9 (CGPA - 5) + N(0, 9); Technical = 38 + 10 (CGPA - 5) + N(0, 10); DSA = 0.9 Technical + N(0, 10); "
            "Communication = 50 + N(0, 12) + 0.1 (Technical - 60). Projects, internships and certifications are Poisson draws (means 1.8, 0.9, 1.5), backlogs are drawn from {0, 0, 0, 0, 1, 1, 2, 3, 4}, the branch, degree "
            "type, student type and year from fixed probabilities, the role uniformly from eight roles, and the target company with probability proportional to its hiring rate, so mass recruiters receive more applicants."),
          P("The placement label is then drawn from a logistic model of the student's gaps against the target company's requirements. Let g_c = CGPA - CGPA_cutoff, g_a = Aptitude - Apt_cutoff, g_t = Technical - Tech_cutoff, "
            "and Skill the skill index of Section 6.3:"),
          EQ("z = 1.4 g_c + 0.035 g_a + 0.045 g_t + (Skill - 0.68) + 0.35 Internships + 0.18 Projects + 0.12 Certifications - 0.9 Backlogs + 0.25 [Branch in {CSE, IT}] + tier term - 0.55 + e"),
          P("where the tier term is -1.6, -0.7 and -0.1 for Tier 1, 2 and 3, e is N(0, 0.8) noise, and Placed is a Bernoulli draw with probability 1 / (1 + exp(-z))."),
          TAB("Properties of the generated dataset", ["Property", "Value"],
              [["Students / companies", f"{F.DS['rows']:,} / {F.DS['companies']}"],
               ["Placed / not placed", f"{F.DS['placed']:,} ({F.pct(F.DS['placed_rate'])}) / {F.DS['not_placed']:,} ({F.pct(1 - F.DS['placed_rate'])})"],
               ["CGPA mean (sd), min - max", f"{F.DS['cgpa_mean']:.3f} ({F.DS['cgpa_sd']:.3f}), {F.DS['cgpa_min']:.2f} - {F.DS['cgpa_max']:.2f}"],
               ["Placed rate by target tier (T1 / T2 / T3)", f"{F.pct(F.DS['by_tier']['1']['mean'])} / {F.pct(F.DS['by_tier']['2']['mean'])} / {F.pct(F.DS['by_tier']['3']['mean'])}"],
               ["Placed rate by backlogs 0 / 1 / 2 / 3 / 4", " / ".join(F.pct(F.DS['backlog_effect'][str(k)]) for k in range(5))],
               ["Placed rate by internships 0 / 1 / 2 / 3 / 4", " / ".join(F.pct(F.DS['internship_effect'][str(k)]) for k in range(5))],
               ["Placed rate by branch (range)", "58.5% (ECE) - 60.8% (CSE)"],
               ["Missing values", str(F.DS["missing_values"])],
               ["Split (train / validation / test)", f"{F.TRAIN_N:,} / {F.VAL_N} / {F.TEST_N} (stratified, seed 42)"]],
              widths=[3.0, 3.6], align=["l", "l"], size=10),
          P("Because the labels follow a logistic rule plus noise, a model that recovers the rule scores well: that is why even logistic regression reaches high accuracy in Chapter 8. The numbers measure how well each method "
            "recovers a known rule from 2,100 examples; they are not evidence of accuracy on real placement records, which are noisier and depend on factors (interview performance, openings, reservations) that are absent here. "
            "The class balance of 59.7 % placed is close to the balanced data of the technique paper [2] (51 % accepted), so no resampling is applied, although objective 2 of the project asked to address imbalance: the stratified split keeps "
            "the ratio in every part.")]

    b += [H2("6.3 Pre-processing and feature engineering"),
          P("`src/preprocess.py` turns each row, together with the company table, into a vector of 24 numbers: 13 standardised numeric columns, 6 engineered columns and 5 frequency-encoded categories. Encodings and scaler are "
            "fitted on the training split only and saved in `models/preprocess.pkl`, so validation, test and live inputs are transformed with training statistics and no information leaks from the test rows."),
          B("**Frequency encoding** of Branch, Target_Company, Target_Role, Degree_Type and Student_Type: each value is replaced by its relative frequency in the training data, f(v) = count(v) / n. This keeps one column per "
            "category instead of one per value, as in the technique paper [2]; a value never seen in training maps to 0.",
            "**Standardisation** of numeric columns: z = (x - mean) / (sd + 1e-9), with mean and sd from the training split.",
            "**Engineered features** that encode the match between the student and the company, shown below.")]
    b += [EQ("Skill = (0.4 Technical + 0.3 Aptitude + 0.15 Communication + 0.15 DSA) / 100"),
          EQ("CGPA_Gap = CGPA - CGPA_Cutoff;   Apt_Gap = Aptitude - Apt_Cutoff;   Tech_Gap = Technical - Tech_Cutoff"),
          EQ("CGPA_x_Tier = CGPA x Tier;   Company_Hiring_Rate = Hiring_Rate of the target company"),
          P("The gap features are the heart of the design: a CGPA of 8.0 is a comfortable margin at Infosys (cutoff 6.0) and a shortfall at Google (cutoff 8.5). The interaction CGPA_x_Tier plays the role of the "
            "Program x QS-rank interaction of the technique paper, and Company_Hiring_Rate that of its program admission rate."),
          TAB("The 24 model features", ["Group", "Count", "Columns"],
              [["Standardised numeric", "13", "CGPA, Tenth_Percent, Twelfth_Percent, Aptitude_Score, Technical_Score, Communication_Score, DSA_Score, Projects, Internships, Certifications, Backlogs, Placement_Year, Target_Tier"],
               ["Standardised engineered", "6", "Skill_Index, Company_Hiring_Rate, CGPA_x_Tier, CGPA_Gap, Apt_Gap, Tech_Gap"],
               ["Frequency-encoded", "5", "Branch, Target_Company, Target_Role, Degree_Type, Student_Type"]],
              widths=[1.6, 0.7, 4.3], align=["l", "c", "l"], size=10)]

    b += [H2("6.4 Algorithm choice and justification"),
          P("Six baselines were trained so that the added complexity of the hybrid could be judged against simpler methods, as in the technique paper [2]. All use scikit-learn [6] or XGBoost [3] with seed 42."),
          TAB("Classifiers and the reason for including each", ["Model", "Configuration", "Why it is included"],
              [["Logistic regression", "max_iter 1000", "Linear, interpretable reference; the label rule is logistic, so it is a strong baseline"],
               ["Decision tree", "defaults", "Shows threshold rules (cutoffs) but overfits"],
               ["Random forest [10]", "200 trees", "Variance-reduced tree ensemble"],
               ["SVM [11]", "RBF kernel, probability = True", "Non-linear margin classifier; also used as a residual model"],
               ["kNN [7]", "k = 9, uniform", "Local similarity; the residual model of the hybrid"],
               ["XGBoost [3]", "100 trees, depth 8, lr 0.1, subsample 0.8, colsample 0.8, L1 0.1, L2 1.0", "Gradient boosting [12]: the primary model, hyper-parameters taken from the technique paper [2]"],
               ["XGBoost + Platt [4]", "sigmoid, 3-fold", "Calibrated probabilities for ranking and residual selection"],
               ["Hybrid XGB + kNN / SVM", "k = 9; RBF SVM", "Local refinement of residual cases [2]"]],
              widths=[1.45, 2.2, 2.95], align=["l", "l", "l"], size=9.5),
          P("XGBoost is the primary model because boosted trees capture threshold rules and interactions (a CGPA just above a cutoff, a backlog with a Tier-1 company) without feature engineering beyond what Section 6.3 provides, "
            "and because TreeExplainer makes SHAP values [5] cheap. A LightGBM branch [14] exists in the training script but LightGBM is not installed, so it was not run. Platt scaling [4] was chosen over isotonic regression "
            "because it has two parameters and is stable on 2,100 rows [9].")]

    b += [H2("6.5 Mathematical formulation"),
          P("**Calibration.** Platt scaling maps the raw XGBoost score f to a probability with two fitted parameters A and B, and the quality of the probabilities is measured by the Brier score [8]:"),
          EQ("p = 1 / (1 + exp(A f + B));      Brier = (1/n) sum (p_i - y_i)^2"),
          P("**Residual hybrid.** Let y_i be the true label, p_i the calibrated probability and the hard prediction yhat_i = 1 if p_i >= 0.5. Equation 1 of the technique paper [2] defines the residual set and the hybrid prediction as"),
          EQ("R = { i : yhat_i != y_i  or  0.4 <= p_i <= 0.6 };      yhat_hybrid_i = yhat_kNN_i if i in R, else yhat_i"),
          P("The first condition (the prediction is wrong) needs the true label. It can be evaluated on a test set, where it measures what a local model could achieve if the wrong rows were known, but not on a new student. "
            "The served model therefore uses only the second condition (Section 6.6)."),
          P("**Serving rule** (`predict_for` in `src/recommend.py`):"),
          EQ("p = p_XGB;   if 0.4 <= p <= 0.6:  p = 0.5 p_XGB + 0.5 p_kNN;   label = READY if p >= 0.5"),
          P("**Feasibility and ranking.** The maximum CGPA gap depends on the company tier, the proximity of a student to a company is one at an exact match and zero at the maximum gap, and each company-role candidate is scored:"),
          EQ("delta_max = 0.6, 1.0, 1.5 for Tier 1, 2, 3;      Proximity = max(0, 1 - |CGPA - CGPA_Cutoff| / delta_max)"),
          EQ("Score = p + 0.05 Proximity + 0.02 [company location = preferred location]"),
          P("A company is feasible if |CGPA - cutoff| <= delta_max, Aptitude >= Apt_Cutoff - 15, not (Backlogs > 2 and Tier = 1) and, if given, Package >= the minimum. These rules mirror the GPA feasibility filters "
            "of the technique paper [2], with tiers instead of QS ranks. For the hybrid list of the five best candidates, with base probability p0:"),
          EQ("improved = { c : p_c > p0 };      avg_gain = mean(p_c - p0) over improved;      match_rate = |improved| / 5"),
          P("**Skill-gap tips** are rules, not model outputs: a tip is added when CGPA, Aptitude or Technical is below the company cutoff and when the student has no internship; if none applies the message is "
            "\"Strong profile - apply and prepare for interviews\". The global importance of each feature is shown separately by the mean absolute SHAP value [5]."),
          ]

    top = F.SHAP
    b += [H2("6.5A Explainability and worked example"),
          P(f"Global explanations use SHAP [5]: `TreeExplainer` is applied to the XGBoost model and the mean absolute SHAP value of each feature over the {F.EXP['shap_n']} test rows ranks the features. "
            f"The five largest are {top[0]['feature']} ({top[0]['mean_abs_shap']:.2f}), {top[1]['feature']} ({top[1]['mean_abs_shap']:.2f}), {top[2]['feature']} ({top[2]['mean_abs_shap']:.2f}), {top[3]['feature']} ({top[3]['mean_abs_shap']:.2f}) and "
            f"{top[4]['feature']} ({top[4]['mean_abs_shap']:.2f}). The gap features dominate because the generator made the label depend on exactly those gaps (Section 6.2); on real data the ranking would have to be re-examined. "
            "The ranking is global: the system does not compute a SHAP explanation for an individual student, and the per-student advice comes from the cutoff rules."),
          P("**Worked example of the feasibility filter.** Take a CSE student with CGPA 7.2, aptitude 65 and technical 65 who targets Google (Tier 1, CGPA cutoff 8.5). The gap is 1.3, which exceeds delta_max = 0.6 for Tier 1, so Google is "
            "itself infeasible and the role-only list (which keeps only the target company) is empty. Infosys (Tier 3, cutoff 6.0) has a gap of 1.2, within delta_max = 1.5; its proximity is 1 - 1.2 / 1.5 = 0.2, so a candidate with "
            "probability 0.90 scores 0.90 + 0.05 x 0.2 = 0.91, plus 0.02 if the student prefers Mysore. The example shows a property of the design that Chapter 8 returns to: because the score is dominated by the probability, weak profiles "
            "are steered to Tier-3 companies, where the probability is highest, regardless of package."),
          P("**Controls against leakage.** Encodings and scaler are fitted on the training split only, the test split is used once for reporting, and cross-validation uses training rows alone. The paper's residual rule is the exception: it looks at test labels by definition and is reported separately (Section 6.6). No hyper-parameter search was run; the hyper-parameters are those of the technique paper [2].")]

    b += [H2("6.6 Model training, configuration and the label-dependence of the hybrid"),
          TAB("Training configuration", ["Item", "Value"],
              [["Split", "stratified 70 / 15 / 15, seed 42: 2,100 / 450 / 450 (test placed 59.56%)"],
               ["XGBoost", "n_estimators 100, max_depth 8, learning_rate 0.1, subsample 0.8, colsample_bytree 0.8, reg_alpha 0.1, reg_lambda 1.0, eval_metric logloss"],
               ["Cross-validation", f"9-fold stratified on the training split: accuracy {F.CV9:.4f}"],
               ["Calibration", f"CalibratedClassifierCV, sigmoid, 3 folds; Brier {F.BRIER:.4f}"],
               ["Local models", "kNN k = 9 (uniform), SVC RBF; both fitted on all 2,100 training rows"],
               ["Hardware / time", "CPU only (i5-12500); one full retraining run of all models about 3 s"],
               ["Artefacts", "xgb_calibrated.pkl 1.49 MB, knn_residual.pkl 0.42 MB, svm_residual.pkl 0.20 MB"]],
              widths=[1.6, 5.0], align=["l", "l"], size=10),
          P("The shipped model files reproduce `models/metrics.json` exactly when evaluated on the seed-42 test split; a fresh retraining with the library versions installed for this work differs by at most 0.011 in any metric, "
            "which is the run-to-run variation of calibration and tree building."),
          P("**Why the paper rule cannot be used as stated.** In the shipped evaluation the residual set contains every test row that XGBoost gets wrong. "
            f"On the {S['n_test']}-row test split XGBoost errs on {S['xgb_errors']} rows; {S['xgb_errors'] - S['xgb_errors_inside_band']} of them lie outside the borderline band and enter the {S['oracle_residual']}-row residual set only because the true label shows they are wrong. "
            f"The local kNN is then correct on {F.pct(S['knn_acc_on_oracle'])} of those rows, against {F.pct(S['xgb_acc_on_oracle'])} for XGBoost: a selection effect. A deployed system never knows the label, so it can apply the local model only "
            f"to the {S['borderline_only']} borderline rows. Three versions were therefore measured on the same split:"),
          TAB("Residual rules compared (seed 42, 450 test rows, shipped models)", ["Rule", "Needs true labels", "Accuracy", "F1", "ROC-AUC"],
              [["XGBoost + Platt only", "no", f"{R['xgb_calibrated']['accuracy']:.4f}", f"{R['xgb_calibrated']['f1']:.4f}", f"{R['xgb_calibrated']['roc_auc']:.4f}"],
               ["Hybrid, paper rule (wrong or borderline)", "yes", f"{R['hybrid_xgb_knn']['accuracy']:.4f}", f"{R['hybrid_xgb_knn']['f1']:.4f}", f"{R['hybrid_xgb_knn']['roc_auc']:.4f}"],
               ["Hybrid, label-free (borderline, hard kNN label)", "no", f"{R['hybrid_knn_labelfree']['accuracy']:.4f}", f"{R['hybrid_knn_labelfree']['f1']:.4f}", f"{R['hybrid_knn_labelfree']['roc_auc']:.4f}"],
               ["Hybrid, serving rule (0.5 p + 0.5 p_kNN)", "no", f"{R['hybrid_knn_serving']['accuracy']:.4f}", f"{R['hybrid_knn_serving']['f1']:.4f}", f"{R['hybrid_knn_serving']['roc_auc']:.4f}"]],
              widths=[2.7, 1.1, 0.9, 0.9, 1.0], align=["l", "c", "c", "c", "c"], size=10),
          P(f"The gain of the paper rule ({R['xgb_calibrated']['accuracy']:.4f} to {R['hybrid_xgb_knn']['accuracy']:.4f}) disappears under the label-free rule ({R['hybrid_knn_labelfree']['accuracy']:.4f}, one student more than XGBoost alone). "
            "The project keeps the paper rule in its reported metrics, because that is what the technique paper evaluates and what `metrics.json` contains, but this report states the label-free figure next to it wherever the hybrid is discussed."),
          TAB("Width of the borderline band (label-free kNN replacement)", ["Band", "Rows replaced", "Accuracy", "F1", "ROC-AUC"], [_bandrow(r) for r in F.BAND], widths=[1.6, 1.3, 1.2, 1.2, 1.3], align=["c", "c", "c", "c", "c"], size=10),
          P("Widening the band changes accuracy by at most 0.4 points. The served band 0.40 - 0.60 is the one prescribed by the technique paper; the sweep shows that no other width would have been measurably better."),
          P(f"The decision threshold was left at 0.5. Accuracy is flat between {min(t['accuracy'] for t in F.THR):.3f} and {max(t['accuracy'] for t in F.THR):.3f} over thresholds 0.30 to 0.70, while precision rises from {F.THR[0]['precision']:.3f} to {F.THR[-1]['precision']:.3f} and recall falls from "
            f"{F.THR[0]['recall']:.3f} to {F.THR[-1]['recall']:.3f}; a placement cell that prefers not to miss placeable students could lower the threshold."),
          P(f"Platt scaling lowers the Brier score only slightly, from {F.CAL['brier_raw_xgb']:.4f} to {F.CAL['brier_platt']:.4f}; logistic regression is better calibrated still ({F.CAL['brier_logreg']:.4f}). The mean predicted probability on the test split "
            f"({F.CAL['mean_prob_test']:.3f}) matches the observed placed rate ({F.CAL['base_rate_test']:.3f}).")]
    return b


def application_blocks():
    b = []
    b += [H2("6.7 Application architecture"),
          P("A request travels from the React page through the Vite proxy to FastAPI, which validates it and calls `src/recommend.py`. For every prediction `predict_for` calls `load_artifacts()`, which reads four pickle "
            "files (preprocessing, calibrated XGBoost, kNN and the company table) from disk, builds a one-row feature vector and returns the probability. The core of the function is:"),
          CODE("def predict_for(profile, company_row, role):\n"
               "    pre, xgb, knn, comp = load_artifacts()\n"
               "    X = _row_features(profile, company_row, role, pre)\n"
               "    p = float(xgb.predict_proba(X)[0, 1])\n"
               "    # residual refinement: if borderline, blend with kNN (paper Fig.8)\n"
               "    if 0.4 <= p <= 0.6:\n"
               "        pk = float(knn.predict_proba(X)[0, 1])\n"
               "        p = 0.5 * p + 0.5 * pk\n"
               "    return round(p, 4)", 8.5),
          P(f"Reloading the pickles on every call keeps the code simple and the server stateless, but it costs time: one prediction takes a mean of {F.PERF['POST /api/predict']['mean_ms']:.0f} ms over HTTP, and a recommendation, "
            f"which calls `predict_for` once per feasible company and role (up to 4 x 30 times), takes a mean of {F.PERF['POST /api/recommend']['mean_ms'] / 1000:.1f} s. Caching the loaded artefacts in the module would remove most of this "
            "and is the first improvement listed in Chapter 10; it was not done because it changes the shared core code that the Flask interface also uses."),
          P("The skill-gap tips are produced in the API layer by `_tips`, which applies the same four rules as the Flask route:"),
          CODE("def _tips(profile, row):\n"
               "    tips = []\n"
               "    if profile['cgpa'] < float(row['CGPA_Cutoff']):\n"
               "        tips.append('CGPA ... below <company> cutoff ... - target Tier-2/3 companies.')\n"
               "    if profile['aptitude'] < float(row['Apt_Cutoff']):\n"
               "        tips.append('Improve aptitude (target 75+) via weekly mock tests.')\n"
               "    if profile['technical'] < float(row['Tech_Cutoff']):\n"
               "        tips.append('Strengthen DSA + core subjects; build 2+ projects.')\n"
               "    if profile['internships'] == 0:\n"
               "        tips.append('Get at least 1 internship - strongly boosts probability.')\n"
               "    if not tips:\n"
               "        tips.append('Strong profile - apply and prepare for interviews.')\n"
               "    return tips", 8.5)]

    b += [H2("6.8 API design"),
          P("The endpoint list is in Section 5.9. A prediction request and response look as follows (values from a real call with a strong CSE profile and target Infosys, role SDE; fields not shown are omitted):"),
          CODE("POST /api/predict\n"
               "{ \"cgpa\": 8.4, \"tenth\": 88, \"twelfth\": 86, \"aptitude\": 82, \"technical\": 84, \"communication\": 75,\n"
               "  \"dsa\": 80, \"projects\": 3, \"internships\": 1, \"certifications\": 2, \"backlogs\": 0,\n"
               "  \"branch\": \"CSE\", \"degree\": \"BTech\", \"target_company\": \"Infosys\", \"target_role\": \"SDE\" }\n\n"
               "200 { \"placement_probability\": 0.9032, \"eligible\": true, \"label\": \"PLACEMENT READY\",\n"
               "       \"company\": \"Infosys\", \"role\": \"SDE\", \"company_detail\": { \"Tier\": 3, \"CGPA_Cutoff\": 6.0, ... },\n"
               "       \"tips\": [\"Strong profile - apply and prepare for interviews.\"] }", 8.5),
          P("`POST /api/recommend` returns `base_prob`, the three lists `company_only`, `role_only` and `hybrid` (each item has company, role, tier, package, location, prob, score and proximity), `avg_gain` and `match_rate`. "
            "`POST /api/recruiter/shortlist` filters the student table with the thresholds and returns `total_matches` and at most 50 rows; `total_matches` was added to the response of the Flask page so that the interface can say "
            "\"1394 candidates match\" while showing only the top 50. The React client keeps one axios instance with a 60 s timeout; an interceptor logs every call, its status and its duration to the activity log.")]

    b += [H2("6.9 Security and error handling"),
          TAB("Input validation and errors", ["Situation", "Behaviour", "HTTP"],
              [["Number outside its range (CGPA 14, aptitude -5, backlogs 99)", "Pydantic rejects the request; the page shows the field message", "422"],
               ["Text where a number is required", "Rejected by Pydantic", "422"],
               ["Missing required field (`target_company`)", "Rejected by Pydantic", "422"],
               ["Unknown company name", "`_company_row` raises", "404"],
               ["Unknown plot name or path-traversal text in the plot name", "Only three names are allowed", "404"],
               ["Model or data file missing", "Clear message naming the command to run", "503"],
               ["Model raises on unseen values", "Caught and returned as `Prediction failed: ...`", "422"],
               ["Foreign browser origin", "No CORS header is returned", "-"]],
              widths=[2.8, 2.9, 0.9], align=["l", "l", "c"], size=10),
          P("The security posture is that of a local teaching prototype, and the limits should be read plainly. There is **no authentication and no authorisation**: any client that can reach the port can read the student table through the "
            "shortlist endpoint, so the server must not be exposed to an untrusted network. There is no database, so SQL injection is not possible; a test with a SQL-injection string, a script tag, a path-traversal name and a 100 kB "
            "company name all returned 404 and nothing was executed (Chapter 7). There is no rate limiting, no HTTPS and no audit log. An unseen branch or role value is accepted and encoded with frequency 0 instead of being rejected. "
            "The pickled model files are loaded with `pickle`, which is safe only for files the operator trained; they must not be replaced by files from an untrusted source.")]

    b += [H2("6.9A Front-end implementation"),
          P("The React application rests on four shared pieces: `api.js` (axios client whose interceptors feed the activity log and turn failures into a message and a hint), `lib/useFetch.js` (data, error, loading and reload for every GET), `lib/profile.js` (field ranges, defaults and validation mirroring the server) and `lib/theme.jsx` (theme and colour tokens, so charts and the three.js backdrop re-tint). Pages are lazy-loaded; the Recruiter page sorts and pages the 50 returned rows in the browser and exports them as CSV, and the dashboard tabs show the PNG files served by `/api/plots/{name}`.")]

    b += [H2("6.10 Installation and execution"),
          TAB("Software environment used for this work", ["Component", "Version"],
              [["Operating system / hardware", f"{F.ENV['os']}; {F.ENV['cpu']}; {F.ENV['ram']} RAM; {F.ENV['gpu']}"],
               ["Python and packages", f"Python {F.ENV['python']}; scikit-learn {F.ENV['sklearn']}; xgboost {F.ENV['xgboost']}; pandas {F.ENV['pandas']}; numpy {F.ENV['numpy']}; shap {F.ENV['shap']}"],
               ["Back end", f"FastAPI {F.ENV['fastapi']}; uvicorn {F.ENV['uvicorn']}; pydantic {F.ENV['pydantic']}; Flask {F.ENV['flask']} (original interface)"],
               ["Front end", f"Node {F.ENV['node']}; React {F.ENV['react']}; Vite {F.ENV['vite']}; Tailwind {F.ENV['tailwind']}; three.js {F.ENV['three']}; Recharts, framer-motion, GSAP"]],
              widths=[1.8, 4.8], align=["l", "l"], size=10),
          P("**One-command start.** Python 3.10 or newer and Node.js 20 or newer are required. Running `run.bat` in `8.ProjectCode` (i) reads the ports from `.env` (backend 8405, frontend 5405), (ii) creates `.venv` and installs "
            "`requirements.txt` if the packages are missing, (iii) generates the data and trains the models only if `models/xgb_calibrated.pkl` is absent, (iv) runs `npm install` in `frontend/` if needed, and (v) opens two windows, "
            "one for `uvicorn backend.main:app --port 8405` and one for `npm run dev`, and the browser at `http://localhost:5405`."),
          CODE("python -m venv .venv\n"
               ".venv\\Scripts\\python.exe -m pip install -r requirements.txt\n"
               ".venv\\Scripts\\python.exe src\\generate_dataset.py     # data/*.csv\n"
               ".venv\\Scripts\\python.exe src\\preprocess.py           # models/preprocess.pkl\n"
               ".venv\\Scripts\\python.exe src\\hybrid_model.py         # models, metrics.json, plots\n"
               ".venv\\Scripts\\python.exe -m uvicorn backend.main:app --port 8405\n"
               "cd frontend && npm install && npm run dev            # http://localhost:5405\n"
               "python app.py                                        # original Flask UI, port 5000", 8.5),
          P("The checks are run with `python scripts/smoke_test.py` (15 checks against the running API) and `python scripts/edge_tests.py` (46 checks); `python scripts/capture_screens.py` records the screens with Playwright. "
            "Typical problems are a missing `pyarrow` (the pickled company table needs it under pandas 3; it is in `requirements.txt`), a port already in use (change `.env`) and \"Could not reach the placement API\" when the backend window is not running."),
          P("**Implementation notes.** The front end is built into code-split chunks (three.js, charts, motion and GSAP are separate bundles) with `npm run build`; `npm run preview` serves the build on 5405 with the same `/api` proxy. "
            "All ports come from `.env`, so the system can run beside other projects on the same PC.")]
    return b


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
