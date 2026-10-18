"""Chapter 6: Methodology and software implementation."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import cite

N_TRAIN_CHURN = F.DS["class_distribution"]["counts"]["1"] - F.SP["test_churners"]
N_TRAIN_STAY = F.SP["train_rows"] - N_TRAIN_CHURN
W_CHURN = F.SP["train_rows"] / (2 * N_TRAIN_CHURN)
W_STAY = F.SP["train_rows"] / (2 * N_TRAIN_STAY)

RULES = [
    ["R1", "Probability >= 60 and Contract is Month-to-month", "Offer a longer-term contract with an incentive"],
    ["R2", "Probability >= 60 and TechSupport = No", "Proactive support outreach or a free trial of tech support"],
    ["R3", "Probability >= 60 and OnlineSecurity = No", "Highlight the online-security add-on in the retention conversation"],
    ["R4", "Probability >= 60 and MonthlyCharges >= 80", "Check the plan against usage; present lower-cost alternatives"],
    ["R5", "Probability >= 60 and PaymentMethod = Electronic check", "Review the payment experience; offer an automatic payment option"],
    ["R6", "Probability >= 60 and tenure <= 6 months", "Early-lifecycle onboarding check-in"],
    ["R7", "Probability >= 60 and InternetService = Fiber optic", "Service-quality and satisfaction check-in"],
    ["R8", "Probability >= 60, internet service present, no StreamingTV and no StreamingMovies", "Promotional trial of streaming add-ons"],
    ["R9", "Probability >= 60, PaperlessBilling = Yes and Electronic check", "Billing-experience review"],
    ["R10", "Risk band is Critical", "Prioritise for a direct retention conversation with a case-specific offer"],
    ["F1", "No rule fired and probability < 30", "Low risk: no urgent action; continue standard engagement"],
    ["F2", "No rule fired and probability >= 30", "Moderate risk without a dominant factor: general satisfaction check-in; monitor the account"],
]


def methodology_blocks():
    return [
        H2("6.1 Overview of the Methodology"),
        P("The method is a supervised-learning pipeline wrapped in an explanation and action layer. Thirteen steps run in order; the first eight are executed once per data set (training time), the last five for each customer or batch (scoring time)."),
        N("**Load and profile.** Read the CSV, detect the target (Churn) and ID (customerID) columns, convert numeric-looking text columns, and report types, missing values and duplicates.",
          "**Clean.** Drop exact duplicate rows; keep missing values for the pipeline to impute.",
          "**Split.** Stratified 80/20 train/test split with random_state 42 (test size selectable from 10% to 40%).",
          "**Preprocess.** Fit a ColumnTransformer on the training split only: median imputation and standardisation for numeric fields, most-frequent imputation and one-hot encoding (unseen categories ignored) for categorical fields.",
          "**Handle imbalance.** Class weights (default), SMOTE on the transformed training split only, or no handling.",
          "**Train.** Logistic Regression, Decision Tree and Random Forest (required); Gradient Boosting and Histogram Gradient Boosting (optional).",
          "**Evaluate.** Accuracy, precision, recall, F1-score, ROC-AUC, confusion matrix, ROC and precision-recall curves on the untouched test split.",
          "**Select and save.** Choose the best model on the selected metric (F1 by default); save the model, preprocessor and metadata to `models/`.",
          "**Score.** Churn probability = predict_proba x 100 for every customer.",
          "**Segment.** Assign Low, Medium, High or Critical risk from editable thresholds (30 / 60 / 80 by default).",
          "**Explain.** Global importance of features and, for one customer, the drivers that push the score up and down.",
          "**Recommend.** Apply the retention rules to customers at or above 60%.",
          "**Monitor.** Score new files in batch and compare new data with the training data for drift."),
        H2("6.2 Data Acquisition and Loading"),
        P(f"The sample data are produced by `generate_sample_churn_data(n_customers=1000, random_state=42)`. The generator draws the 21 Telco-style fields with realistic proportions (for example 55% month-to-month contracts, 44% fibre-optic, 34% electronic check) "
          "and sets churn from a latent logistic risk score: month-to-month contract adds risk, long tenure reduces it, electronic check, fibre optic, missing tech support and online security and higher charges add risk, and Gaussian noise "
          f"(standard deviation 0.55) is added before the label is drawn. The resulting churn rate is {F.DS['churn_rate_pct']}%. The generator exists so that the application can be demonstrated without a data file; it is not a model of any real operator."),
        P("An uploaded file is read with pandas. The target is found by name (churn, target, label, exited, is_churn or churned, in any case) and the identifier by name (customerID, customer_id, id, custid) or, as a fallback, as a text column whose values are all unique. "
          "A text column whose name suggests money (TotalCharges, MonthlyCharges, charges, amount) is converted to numbers; blank strings, which occur in the public Telco file, become missing values. "
          "The target is normalised to 0/1: the strings yes, 1, true, churned, churn and y (any case) are positive, everything else is negative. `validate_dataset_for_training` refuses an empty table, a missing target, fewer than 30 rows, a single class or a class with fewer than 5 examples before any model is trained."),
        H2("6.3 Cleaning, Preprocessing and Splitting"),
        P(f"Exact duplicate rows are dropped (none in the sample). The remaining columns are split into numeric ({', '.join(F.DS['numeric_features'])}) and categorical (15 fields). "
          "The ColumnTransformer treats them differently because the models need numbers and because categories have no order:"),
        TAB("Preprocessing of the feature types", ["Type", "Fields", "Steps"],
            [["Numeric", "SeniorCitizen, tenure, MonthlyCharges, TotalCharges", "Median imputation, then StandardScaler (z = (x - mean) / sd)"],
             ["Categorical", "15 fields (gender, Partner, ..., PaymentMethod)", "Most-frequent imputation, then one-hot encoding with handle_unknown = ignore"]],
            widths=[1.0, 2.3, 2.7], size=10),
        P(f"After encoding, the {F.DS['n_features_raw']} raw features become {F.SP['encoded_feature_count']} numeric inputs. The preprocessor is **fitted on the training split only** and applied to the test split, so no test information reaches the models. "
          "The split is stratified, so training and test sets keep the churn proportion: with test size 0.20 and seed 42 the sample gives "
          f"{F.SP['train_rows']} training rows ({N_TRAIN_CHURN} churners) and {F.SP['test_rows']} test rows ({F.SP['test_churners']} churners). Unseen categories at scoring time are ignored (all-zero one-hot) instead of raising an error."),
        H2("6.4 Handling Class Imbalance"),
        P(f"Three strategies are offered, and the Train page lets the analyst choose one. **Class weights** make an error on the rare class cost more: for the Logistic Regression, Decision Tree and Random Forest the weight of a class is n / (2 x n_class). "
          f"On the training split this is {W_CHURN:.3f} for churners and {W_STAY:.3f} for retained customers. Gradient Boosting and Histogram Gradient Boosting in this implementation take no class weight, so this strategy leaves them unchanged. "
          f"**SMOTE** {cite('smote')} creates synthetic churners by interpolating between a minority example and one of its nearest minority neighbours, x_new = x_i + u (x_nn - x_i) with u drawn uniformly from [0, 1]; it is applied to the transformed training split only, never to the test split, "
          "and the application falls back to class weights if the imbalanced-learn package is missing. **None** trains on the data as they are and exists to show the cost of ignoring imbalance (Chapter 8)."),
        H2("6.5 Classification Algorithms"),
        P("Five learners are registered in `MODEL_REGISTRY`. Their settings were fixed in advance and are the same in every experiment; no hyper-parameter search was run."),
        TAB("Models and their settings", ["Model", "Setting in the code", "Why it is included"],
            [["Logistic Regression", "max_iter 2000, L2 penalty (default), random_state 42", "Transparent baseline; coefficients are directly interpretable"],
             ["Decision Tree", "max_depth 8, min_samples_leaf 10, Gini", "Rules a business user can read"],
             ["Random Forest", "300 trees, max_depth 12, min_samples_leaf 5", "Robust ensemble for mixed data"],
             ["Gradient Boosting (optional)", "200 trees, max_depth 3, learning_rate 0.08", "Sequential boosting"],
             ["Hist Gradient Boosting (optional)", "max_depth 6, learning_rate 0.08", "Fast histogram boosting"]],
            widths=[1.7, 2.3, 2.0], size=9.5),
        P("**Logistic Regression** models the log-odds of churn as a linear function of the encoded inputs and turns them into a probability with the logistic function:"),
        EQ("P(churn | x) = 1 / (1 + exp(-(b0 + w1 x1 + ... + wp xp)))"),
        P("Because the inputs are standardised, the size of a coefficient w_j compares features directly, and the product w_j x_j is the contribution of feature j to the log-odds of a given customer; this is the quantity the local explanation uses. "
          "A **Decision Tree** splits the data repeatedly on the feature and threshold that most reduces Gini impurity,"),
        EQ("G = 1 - sum over classes k of p_k^2"),
        P(f"and stops at depth 8 or when a leaf would hold fewer than 10 customers. A **Random Forest** {cite('breiman')} averages the probabilities of 300 such trees, each grown on a bootstrap sample with random feature subsets. "
          f"**Gradient Boosting** {cite('friedman')} adds trees one at a time, each fitted to the errors of the ensemble so far, with a shrinkage of 0.08."),
        H2("6.6 Evaluation Metrics"),
        P("With TP, FP, TN and FN the counts of the confusion matrix (churn is the positive class):"),
        EQ("Accuracy = (TP + TN) / (TP + TN + FP + FN)"),
        EQ("Precision = TP / (TP + FP)          Recall = TP / (TP + FN)"),
        EQ("F1 = 2 x Precision x Recall / (Precision + Recall)"),
        P("**Precision** is the share of customers flagged as churners who really leave; **recall** is the share of real churners that are flagged; **F1** is their harmonic mean. **ROC-AUC** is the probability that a randomly chosen churner is scored higher than a randomly chosen "
          "retained customer; 0.5 is chance and 1.0 is perfect ranking. Accuracy is reported but is not used to choose the model, because on 26% churn a classifier that never predicts churn scores 74%."),
        H2("6.7 Model Selection"),
        P("`select_best_model(results, metric)` returns the model with the highest value of the metric chosen on the Train page; the default is F1 and the alternatives are accuracy, precision, recall and ROC-AUC. "
          "The Evaluation page shows the comparison table, the confusion matrix of the selected model and the ROC and precision-recall curves of every model, and recommends one. The analyst saves the chosen model, which writes the three joblib files."),
        H2("6.8 Risk Segmentation"),
        P("`assign_risk_category` maps the probability (0-100) to a band using three editable thresholds:"),
        TAB("Risk bands at the default thresholds", ["Band", "Probability range", "Meaning"],
            [["Low Risk", "below 30", "No action beyond normal service"],
             ["Medium Risk", "30 to below 60", "Watch; general satisfaction check"],
             ["High Risk", "60 to below 80", "Rules R1-R9 can fire"],
             ["Critical Risk", "80 and above", "Rules R1-R10 can fire; direct conversation"]],
            widths=[1.4, 1.8, 2.8], size=10),
        P("The server rejects thresholds that are not ordered with a minimum gap (Low between 5 and 50, Medium at least 5 points above Low and at most 85, High at least 5 points above Medium and at most 95), so the four bands always exist. "
          f"On the sample, the saved Logistic Regression model places {F.RISK['counts']['Low Risk']}, {F.RISK['counts']['Medium Risk']}, {F.RISK['counts']['High Risk']} and {F.RISK['counts']['Critical Risk']} customers in the four bands. "
          "Because class weights raise the scores of all customers (mean score 45.9% against 26.4% real churn), the bands are best read as a ranking of customers and not as chances of leaving."),
    ]


def application_blocks():
    return [
        H2("6.9 Explainability"),
        P("Two levels of explanation are provided."),
        P(f"**Global.** `global_importance` returns up to three tables: the model's built-in importance (absolute coefficients for Logistic Regression, impurity-based importances for trees), permutation importance (the fall in accuracy when one feature is shuffled, computed on at most 300 test rows with 5 repeats), "
          f"and, if the SHAP library is installed, mean absolute SHAP value. SHAP was not installed in the environment used for this report, so only the first two were produced and no SHAP result is reported. For the saved Logistic Regression model the largest coefficients are "
          f"{', '.join(i['feature'] + ' (' + str(round(i['importance'], 3)) + ')' for i in F.M['importance']['model_importance'][:4])}."),
        P("**Local.** `local_explanation` explains one customer. With SHAP available it uses SHAP values; otherwise it multiplies each feature's weight (coefficient or importance) by the customer's standardised feature value:"),
        EQ("contribution_j = weight_j x x_j"),
        P("The five largest positive contributions are shown as the factors pushing the score towards churn, and the five most negative as protective factors. This is an approximation of the model's behaviour for that customer, not a causal statement, and the interface labels the method used (\"shap\" or \"approximate\")."),
        H2("6.10 What-If Analysis"),
        P("The What-if page lets the analyst change attributes of a customer (for example the contract from Month-to-month to Two year, or the monthly charge) and re-scores the edited record with the same preprocessor and model. "
          "The result is the new probability, the change in score and the new band next to the original. It is a model-based scenario analysis: it shows what the model would predict for the changed record, not what the customer would actually do."),
        H2("6.11 Rule-Based Retention Engine"),
        P("`generate_recommendations(row, probability, band)` turns a customer's profile into suggestions with transparent IF/THEN rules. There is no language model and no external service. Nine rules require a probability of at least 60 and the tenth requires the Critical band; two fallback messages cover customers for whom no rule fired."),
        TAB("Retention rules", ["ID", "Condition", "Suggestion"], RULES, widths=[0.5, 3.0, 2.5], align=["c", "l", "l"], size=9),
        P("Every suggestion carries the reason that produced it, so a retention agent can see why it appears. The thresholds in the rules (60, 80 charges, 6 months) were chosen by the team as reasonable starting points; **their business effect was not measured**, because there are no campaign data."),
        H2("6.12 Batch Prediction and Monitoring"),
        P("The Batch page scores a CSV in one step. The file must contain the feature columns the active model was trained on; otherwise the API answers 422 and names the missing columns. The output table has the customer ID, the churn probability, "
          "`predicted_churn` (Yes when the probability is at least 50), the risk band and, optionally, the three largest risk factors (on by default, up to 300 rows). A template with 25 rows can be downloaded."),
        P("The Monitoring page shows the active model's details and, for a new file, a drift check against the data the model was trained on: columns that are missing, the percentage of missing values (flagged above 10%), categories not seen in training, the shift in the mean of each numeric field, "
          "and the churn rate of the new file when it has a target column. It is a simple screening tool; it does not compute statistical drift tests."),
        H2("6.13 API Implementation"),
        P(f"`backend/main.py` defines, with FastAPI {cite('fastapi')}, the routes in two routers: `public` (health, login) and `private` (all others), the latter protected by the dependency `require_user`, which reads the bearer token. Each handler loads or updates `STATE`, calls the matching functions of `src/` and returns JSON in a common envelope. "
          "Helper functions convert numpy and pandas values, find a customer by ID, build the risk table and the explanation of one row. A background thread warms the importance cache after a model is saved, and a lock stops a request and the warm-up from computing it twice. "
          "CORS is configured for the development origin of the web interface, which also reaches the API through the Vite proxy."),
        CODE("""def make_token(email: str) -> str:
    body = _b64(json.dumps({"sub": email, "exp": int(time.time()) + config.TOKEN_TTL_SECONDS}).encode())
    return f"{body}.{_sign(body)}"

def read_token(token: str) -> dict | None:
    try:
        body, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body)):
            return None
        data = json.loads(_unb64(body))
        return data if data.get("exp", 0) > time.time() else None
    except Exception:
        return None""", 8.5),
        P("The listing shows the token functions of `backend/auth.py`: the token is a base64 payload plus an HMAC-SHA256 signature, and `read_token` returns nothing for a bad signature, an expired token or a malformed string."),
        H2("6.14 ChurnIQ Web Interface"),
        P("The interface is a React 19 single-page application built with Vite 8. It has a landing page, a demo sign-in and thirteen working pages (Dashboard, Data, Explore, Train, Evaluation, Customer risk, Customer 360, Explain, What-if, Retention, Batch, Monitoring, About), "
          "routed with React Router 7. Charts use Recharts, motion uses Framer Motion and GSAP, and the styling is a soft pastel kit with light and dark themes. During development Vite serves the pages on port 5314 and proxies `/api` to the FastAPI service on port 8314, "
          "so no cross-origin calls occur. The token is kept in the browser's local storage and sent as a bearer header; a 401 on any call except the login ends the session and returns the user to the sign-in page."),
        H2("6.15 Original Streamlit Application"),
        P("The Streamlit application (`app.py` and thirteen modules in `pages/`) was the first interface and remains runnable (`streamlit run app.py`, port 8501). Both interfaces call the same `src/` functions. "
          "Streamlit keeps its state in `st.session_state`; the FastAPI layer reproduces that with `AppState`, so both behave the same way."),
        H2("6.16 Running the System"),
        P("From the project folder, `run.bat` creates the virtual environment, installs the Python and Node packages and starts the API and the web interface. The sample data and the saved model are used automatically. "
          "Appendix B gives the commands, the demo credentials and the order in which to use the pages."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
