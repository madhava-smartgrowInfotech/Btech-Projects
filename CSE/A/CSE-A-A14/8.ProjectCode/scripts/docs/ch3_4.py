"""Chapter 3 (feasibility study) and Chapter 4 (system requirements and analysis)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB

LAT = F.LAT
API = F.API["repeated_ms"]


def feasibility_blocks():
    t5 = round(F.M["app_default_split"]["class_weight"]["wall_seconds"], 1)
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the proposed system can be built and used with the resources at hand. The five aspects below are assessed with measurements from this project wherever a measurement exists "
          "and are described qualitatively where one does not; no monetary figure is invented."),
        H2("3.1 Technical Feasibility"),
        P("Every component is available as free, open-source software and runs on an ordinary desktop. The measurements in the table below were taken on a single machine without a graphics processor."),
        TAB("Technical feasibility: measured evidence", ["Question", "Measurement"],
            [["Can the five models be trained on a desktop CPU?", f"Yes. All five (LR, DT, RF, GB, HGB) train and evaluate in {t5} s on {F.SP['train_rows']} training rows (Intel Core i5-12500, 15.7 GB RAM)"],
             ["Can customers be scored interactively?", f"Yes. One customer in a median {LAT['single_customer_median']} ms (95th percentile {LAT['single_customer_p95']} ms); all 1,000 customers in {LAT['full_dataset_1000_rows_ms']} ms"],
             ["Is the API fast enough for a web interface?", f"Yes. Median response {API['xai_global']['median']}-{API['dashboard']['median']} ms for the endpoints measured over 127.0.0.1; training three models through the API takes {F.API['once_ms']['train_3_models'] / 1000:.1f} s"],
             ["Is the software stack mature?", "Python 3.11, scikit-learn, pandas, FastAPI, React 19 and Vite 8 are widely used and documented"],
             ["Can the pipeline be tested?", f"Yes. {F.TESTS['pytest']} unit tests and a {F.TESTS['smoke']}-check end-to-end API test pass"]],
            widths=[2.2, 3.8], size=10),
        H2("3.2 Economic Feasibility"),
        P("The software cost is zero: no commercial licence, cloud service or paid API is used, and the retention advice is produced by local rules, not by a paid language model. "
          "The only hardware needed is a computer that can run Python; the development machine was an ordinary desktop. Operating cost is limited to the time of the analyst who uses it."),
        P("The benefit side is the value of the customers retained. Industry sources describe acquisition as several times more costly than retention, but this project has no campaign or revenue data, "
          "so it does **not** estimate a monetary saving. What it can support is an indication of targeting value: on the test split, contacting the 20% of customers with the highest scores reached 39.6% of the churners, "
          "a lift of about 2 over random contact (Section 8.8). Whether that justifies the cost of a campaign depends on the cost per contact and the value per saved customer, which are operator-specific inputs."),
        H2("3.3 Operational Feasibility"),
        B("**Usability.** The interface needs no programming. The pages follow the workflow (Data, Train, Evaluate, then the analysis pages), and each page says what it needs when a step is missing.",
          "**Skills.** An analyst who can read a metrics table and a bar chart can use every page; the explanations are phrased in business terms (for example, \"Contract: Month-to-month pushes the score up\").",
          "**Deployment.** One script (`run.bat`) creates the virtual environment, installs the packages and starts the API (port 8314) and the web interface (port 5314). The original Streamlit application starts with one command.",
          "**Data handling.** The system works on a CSV file. A new CSV is validated and rejected with a plain message if columns are missing."),
        H2("3.4 Schedule Feasibility"),
        P("The work was organised in phases that depend on one another. The table lists them in order; calendar dates are not given because the batch records do not include a dated plan."),
        TAB("Project phases", ["Phase", "Activity", "Output"],
            [["1", "Problem definition, base paper study, literature survey", "Abstract, objectives, survey"],
             ["2", "Data preparation and exploratory analysis", "Cleaned data, EDA pages"],
             ["3", "Model training, imbalance handling and evaluation", "Model comparison, saved model"],
             ["4", "Risk bands, explanations, what-if, retention rules", "Customer 360, XAI, retention pages"],
             ["5", "Batch scoring, monitoring, API layer and React interface", "FastAPI service, ChurnIQ interface"],
             ["6", "Testing, experiments and documentation", "Tests, metrics, report, decks, paper"]],
            widths=[0.7, 3.4, 1.9], align=["c", "l", "l"], size=10),
        H2("3.5 Legal, Ethical and Data-Protection Feasibility"),
        P("The data used in this project are synthetic and contain no personal information, so no consent or anonymisation was needed. In real use, customer records are personal data: processing them for churn scoring "
          "needs a lawful basis, access control and retention limits under the data-protection rules that apply to the operator. The demo login in this project is a convenience for demonstration and is not an access-control system for real customer data."),
        P("There is also an ethical point about retention offers. A score is a ranking that can be wrong, and the explanations are model attributions, not causes (the base paper and the surveyed work say the same). "
          "The retention rules therefore phrase their output as suggestions to \"consider\" and never trigger an action automatically."),
        H2("3.6 Risk Analysis"),
        TAB("Project risks and mitigation", ["Risk", "Effect", "Mitigation in this project"],
            [["No real operator data", "Metrics do not transfer to a real customer base", "Synthetic data are declared in every document; the pipeline accepts any CSV with the Telco schema"],
             ["Small test set (200 rows, 53 churners)", "Single-split metrics are noisy (sd 0.03-0.10)", "5-fold cross-validation and five repeated splits are reported beside the headline figure"],
             ["Class imbalance", "High accuracy, low recall", "Class weights or SMOTE; model chosen on F1, not accuracy; recall measured with and without handling"],
             ["Uncalibrated probabilities", "A score of 60 is not a 60% chance", "Scores are described as rankings; calibration is measured and reported (Section 8.8)"],
             ["Optional SHAP library missing", "No SHAP explanations", "Coefficient-times-value and permutation importance fall back automatically; SHAP is stated as not demonstrated"],
             ["Library version differences", "Tree-ensemble scores change on a 200-row split", "Environment of record stated; a second environment is archived (Section 8.3)"],
             ["Single-user in-memory state", "No concurrent users; dataset lost on restart", "Documented limitation; the active model is restored from disk"]],
            widths=[1.6, 1.8, 2.6], size=9.5),
        H2("3.7 Conclusion of the Feasibility Study"),
        P("The system is technically feasible (measured), economically feasible in terms of cost (no licences, ordinary hardware), operationally feasible for a non-programmer, and acceptable from a legal and ethical point of view when "
          "used on properly governed data. Its main risk is not the build but the evidence: the metrics come from synthetic data and a small test set, and must be re-measured on real data before any operational decision rests on them."),
    ]


FIELDS = [
    ["customerID", "text", "Unique customer identifier (detected automatically; excluded from the features)"],
    ["gender", "category", "Female / Male"],
    ["SeniorCitizen", "numeric 0/1", "Customer is a senior citizen"],
    ["Partner, Dependents", "category", "Yes / No"],
    ["tenure", "numeric", "Months with the company (0-72 in the sample)"],
    ["PhoneService, MultipleLines", "category", "Phone service taken; multiple lines (or no phone service)"],
    ["InternetService", "category", "DSL / Fiber optic / No"],
    ["OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies", "category", "Yes / No / No internet service"],
    ["Contract", "category", "Month-to-month / One year / Two year"],
    ["PaperlessBilling", "category", "Yes / No"],
    ["PaymentMethod", "category", "Electronic check / Mailed check / Bank transfer (automatic) / Credit card (automatic)"],
    ["MonthlyCharges", "numeric", "Monthly bill (18.00-105.97 in the sample)"],
    ["TotalCharges", "numeric", "Total billed to date (1.15-6,747.02 in the sample)"],
    ["Churn", "target Yes/No", "Whether the customer left (detected automatically)"],
]


def analysis_blocks():
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Functional Requirements"),
        P("The functional requirements were derived from the objectives (Section 1.4) and from the way a retention analyst works. Each requirement is implemented by a page of the application and one or more API routes."),
        TAB("Functional requirements", ["ID", "Requirement", "Implemented by"],
            [["FR1", "Sign in with a demo account; reject wrong or expired credentials", "Sign in page; POST /api/auth/login, bearer token"],
             ["FR2", "Load the sample data or upload a customer CSV; preview rows", "Data page; /api/data/sample, /upload, /preview"],
             ["FR3", "Detect or set the target and ID columns; report data quality (types, missing values, duplicates)", "Data page; /api/data/config, /quality"],
             ["FR4", "Clean the table and build the feature set", "Data page; /api/data/prepare"],
             ["FR5", "Explore churn by segment and numeric field with filters", "Explore page; /api/eda"],
             ["FR6", "Train the required models (LR, DT, RF) and optional models (GB, HGB) with a chosen imbalance strategy and test size", "Train page; /api/models/train"],
             ["FR7", "Show accuracy, precision, recall, F1, ROC-AUC, confusion matrix, ROC and precision-recall curves; recommend the best model", "Evaluation page; /api/evaluation"],
             ["FR8", "Save the chosen model and restore it after a restart", "Evaluation page; /api/models/save; models/*.pkl"],
             ["FR9", "Show portfolio KPIs and risk distribution", "Dashboard; /api/dashboard"],
             ["FR10", "Group customers into Low, Medium, High and Critical risk with editable, validated thresholds", "Customer risk page; /api/risk, /api/risk/thresholds"],
             ["FR11", "Show one customer's profile, score, drivers and actions (Customer 360)", "Customer 360; /api/customers/{id}"],
             ["FR12", "Explain the model globally and each prediction locally", "Explain page; /api/xai/global, /api/xai/local/{id}"],
             ["FR13", "Re-score a customer after attribute changes (what-if)", "What-if page; /api/whatif"],
             ["FR14", "Generate rule-based retention actions per customer and for a risk group", "Retention page; /api/retention"],
             ["FR15", "Score a new CSV and download the result; reject files with missing columns", "Batch page; /api/batch/template, /predict"],
             ["FR16", "Show the active model's details and check new data for drift", "Monitoring page; /api/monitoring, /drift"]],
            widths=[0.5, 3.4, 2.1], align=["c", "l", "l"], size=9.5),
        H2("4.2 Non-Functional Requirements"),
        TAB("Non-functional requirements and how they are met", ["Quality", "Requirement", "Evidence"],
            [["Performance", "Interactive response on a desktop", f"Median API response {API['xai_global']['median']}-{API['dashboard']['median']} ms; single score {LAT['single_customer_median']} ms"],
             ["Usability", "Usable without programming; clear errors", "Guided pages; 422 / 409 messages in plain language; light and dark themes; keyboard focus and skip link"],
             ["Reliability", "Invalid input never crashes the service", "Server-side validation of thresholds, columns and file type; 63-check smoke test includes the error paths"],
             ["Security", "No open endpoints except health and login", "HMAC-SHA256 signed bearer token with 12 h expiry; credentials in `.env`; protected routes return 401"],
             ["Portability", "Runs on Windows and any system with Python 3.11", "requirements.txt; run.bat; no GPU or external service"],
             ["Maintainability", "Core logic independent of the interface", "src/ has no UI imports; FastAPI layer only calls src/; 44 unit tests"],
             ["Reproducibility", "Same numbers on re-run", "Fixed seed 42; scripts/run_experiments.py writes metrics.json; environment recorded"]],
            widths=[1.1, 2.0, 2.9], size=9.5),
        H2("4.3 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum", "Used in this project"],
            [["Processor", "Dual-core 2 GHz", "Intel Core i5-12500 (6 cores, 12 threads)"],
             ["Memory", "4 GB", "15.7 GB"],
             ["Storage", "1 GB free (environment, node packages, data)", "SSD"],
             ["Graphics", "Not required", "Not used (CPU only)"],
             ["Display", "1280 x 720", "1440 x 900 used for screenshots; layouts checked at 360, 768 and 1440 px"]],
            widths=[1.3, 2.4, 2.3], size=10),
        P("The minimum column is a conservative estimate for a 1,000-row data set and was not tested on smaller machines."),
        H2("4.4 Software Requirements"),
        TAB("Software", ["Component", "Version / note"],
            [["Operating system", "Windows 11 (run.bat); the Python parts also run on Linux and macOS"],
             ["Python", "3.11.9"],
             ["scikit-learn / pandas / numpy", "1.9.1 / 3.0.6 / 2.4.6 in the environment of record (the same code also passes its tests on 1.5.0 / 2.2.1 / 1.26.4)"],
             ["imbalanced-learn, joblib", "SMOTE oversampling; saving and loading model files"],
             ["Streamlit, plotly", "Original 13-page application and its charts"],
             ["FastAPI, uvicorn", "0.143.3 and 0.54.0: API layer, port 8314, interactive docs at /docs"],
             ["Node.js", "24.19.0, for the web interface build"],
             ["React, Vite, React Router, Recharts", "19.3, 8.3, 7, 3: ChurnIQ interface, port 5314"],
             ["pytest", "9.1.1: unit tests"],
             ["Optional: SHAP", "Not installed; the code falls back to built-in explanations"]],
            widths=[2.2, 3.8], size=10),
        H2("4.5 Data Requirements"),
        P("The system expects one row per customer with the columns below (the 21-column Telco schema). The target is detected from a column named Churn (or a similar name) and the identifier from a column such as customerID; both can be changed on the Data page. "
          "Rows with exact duplicates are removed, blanks in numeric-looking text columns are converted to missing values, and missing values are imputed inside the pipeline."),
        TAB("Data fields", ["Field(s)", "Type", "Meaning"], FIELDS, widths=[2.4, 0.9, 2.7], size=9),
        P(f"The sample file has {F.DS['rows']:,} rows and no missing values or duplicates; {F.DS['n_features_raw']} raw feature columns (4 numeric, 15 categorical) become {F.SP['encoded_feature_count']} model inputs after one-hot encoding."),
        H2("4.6 Actors and Use Cases"),
        P("There is a single role, the retention analyst, who also trains models when needed; the demo account is shared and there are no permissions to separate duties. "
          "The use-case diagram shows the fifteen use cases. Sign in precedes all others; training precedes saving, risk analysis, explanation, what-if and retention."),
        FIG(F.diag("08_use_case_diagram.png"), "Use-case diagram of ChurnIQ", 5.6),
        TAB("Main use cases", ["Use case", "Precondition", "Main flow", "Result"],
            [["Train and compare models", "Data prepared", "Choose models, strategy, test size; start training", "Metrics table, curves, recommended model"],
             ["Open Customer 360", "Model saved", "Select a customer from the risk list", "Profile, score, band, drivers, actions"],
             ["Run what-if", "Model saved", "Change contract, charges or add-ons; re-score", "Original and new score side by side"],
             ["Batch-score a CSV", "Model saved", "Upload CSV with required columns", "Scored table, download; 422 if columns missing"],
             ["Check drift", "Model saved", "Upload new data", "Missing columns, missingness, unseen categories, mean shift, churn rate"]],
            widths=[1.4, 1.1, 2.0, 1.5], size=9),
        H2("4.7 Analysis of the Data"),
        P(f"The sample has {F.DS['class_distribution']['counts']['0']} retained and {F.DS['class_distribution']['counts']['1']} churned customers, an imbalance of {F.DS['class_distribution']['imbalance_ratio']} to 1. "
          "A classifier that predicted \"stays\" for everyone would be 73.6% accurate and find no churner, which is why accuracy is not used alone to choose the model."),
        FIG(F.fig("class_balance.png"), "Class balance of the customer data", 3.6),
        P("Churn varies strongly with a few attributes, as the figure below shows. Month-to-month customers churn at 34.1% against 19.2% for one-year and 12.5% for two-year contracts; customers in their first year churn at 36.6% against 18.7% after four years; "
          "fibre-optic customers churn more (32.7%) than DSL (25.1%) or no-internet customers (14.7%); and electronic-check payers churn at 33.4% against 18.3% for automatic bank transfer. "
          "These are the relationships built into the generator, so they confirm that the analysis reads the data correctly, not that real customers behave this way."),
        FIG(F.fig("churn_by_segment.png"), "Churn rate by contract type, tenure group, internet service and payment method", 6.0),
        FIG(F.fig("numeric_distributions.png"), "Distribution of tenure, monthly charges and total charges for retained and churned customers", 6.0),
        H2("4.8 Assumptions and Constraints"),
        B("One analyst works at a time; state is held in memory and is not shared between users.",
          "The input has the Telco schema; other schemas work as long as a binary target is present, but the retention rules read the Telco field names and stay silent on other fields.",
          "The churn label is available for training; the system does not infer churn from usage.",
          "Probabilities are model scores, not calibrated chances of leaving (Section 8.8).",
          "Only scikit-learn models are used; no deep learning and no external gradient-boosting library."),
    ]
