# Explainable AI-Based Customer Churn Prediction and Intelligent Retention System

A B.Tech final-year major project — an advanced, explainable extension of a
traditional telecom customer churn prediction system, built entirely in
Python with Streamlit.

> Base paper: *"Explaining Customer Churn Through Unified Perturbation-Based
> XAI Soft Computing,"* IEEE Access, 2026. DOI: `10.1109/ACCESS.2026.3663648`.
> This application is an applied extension of the base paper's motivation for
> a telecom customer retention scenario — it does not claim to reproduce
> every algorithm or experiment from the paper.

## Abstract

Traditional churn prediction systems tell an organization *which* customers
may churn but stop there. This project builds an **intelligent retention
system** that additionally explains *why* a customer is at risk and *what*
retention action could be considered — combining Machine Learning,
Explainable AI (SHAP), customer risk segmentation, and a local rule-based
retention recommendation engine, all wrapped in an interactive Streamlit
dashboard.

## Problem Statement

A basic churn prediction system only answers: *"Will this customer churn?"*
An advanced, actionable system must answer four questions:

1. **WHO** is likely to churn?
2. **HOW LIKELY** are they to churn (as a probability, not just a label)?
3. **WHY** are they likely to churn (individual-level explanation)?
4. **WHAT RETENTION ACTION** could be considered?

## Objectives

- Predict customer churn probability using multiple ML models
- Explain predictions both globally (model-wide) and locally (per customer)
- Segment customers into configurable risk bands
- Generate explainable, rule-based retention suggestions
- Support what-if scenario analysis and batch prediction
- Run entirely locally with no paid APIs, cloud services, or external AI

## Existing System (Baseline)

Data acquisition → cleaning/preprocessing → EDA → class imbalance handling
→ train Logistic Regression / Decision Tree / Random Forest → evaluate
(Accuracy, Precision, Recall, F1, ROC-AUC) → identify important features →
dashboard of at-risk customers.

## Proposed System (Advanced)

```
Customer data
   → preprocessing
   → EDA
   → class imbalance handling
   → multiple ML models
   → model comparison
   → churn probability (0-100%)
   → customer risk segmentation
   → local explainable AI (SHAP)
   → global explainable AI (SHAP / permutation / built-in importance)
   → retention recommendation engine (rule-based, local)
   → what-if scenario analysis
   → interactive Customer 360° profile
   → batch prediction
   → retention intelligence dashboard
```

## System Architecture

```
customer_churn_app/
│
├── app.py                      # Streamlit entry point, session state, routing
├── requirements.txt            # Streamlit app dependencies
├── run.bat                     # one-command launcher for the React app + API
├── backend/                    # FastAPI layer over src/ (React app's API)
├── frontend/                   # React + Vite app (V4 "Soft Pastel Calm" kit)
├── scripts/                    # smoke_test.py, capture_screens.py
├── docs/                       # FRONTEND_PLAN.md, 03_HOW_TO_RUN.md, screenshots/
├── README.md
│
├── data/
│   └── customer_churn.csv      # Synthetic sample dataset (~26% churn rate)
│
├── models/                     # Saved model.pkl / preprocessor.pkl / model_metadata.pkl
│                                # (created after you train & save a model)
│
├── src/
│   ├── sample_data.py          # Synthetic dataset generator
│   ├── utils.py                # Risk thresholds, tenure grouping, helpers
│   ├── data_loader.py          # CSV loading, column detection, validation
│   ├── preprocessing.py        # ColumnTransformer pipeline, SMOTE, splitting
│   ├── train_models.py         # Trains LR / Decision Tree / RF / GB / HGB
│   ├── evaluation.py           # Metrics, confusion matrix, ROC/PR curve data
│   ├── prediction.py           # Scoring individual customers & batches
│   ├── explainability.py       # SHAP local/global explanations + fallback
│   ├── risk_segmentation.py    # Risk table & distribution summary
│   ├── retention_engine.py     # Rule-based retention recommendation engine
│   ├── eda.py                  # Plotly chart builders
│   └── persistence.py          # joblib save/load of model artifacts
│
└── pages/
    ├── page_dashboard.py
    ├── page_data_upload.py
    ├── page_eda.py
    ├── page_model_training.py
    ├── page_model_evaluation.py
    ├── page_customer_risk.py
    ├── page_customer_360.py
    ├── page_explainable_ai.py
    ├── page_whatif.py
    ├── page_retention.py
    ├── page_batch_prediction.py
    ├── page_monitoring.py
    └── page_about.py
```

## Technology Stack

| Layer            | Technology |
|-------------------|------------|
| UI                | Streamlit, and React + Vite (via FastAPI) |
| Data handling     | pandas, numpy |
| Machine learning  | scikit-learn |
| Class imbalance   | imbalanced-learn (SMOTE) / class_weight |
| Explainability    | SHAP (with automatic fallback if unavailable) |
| Visualization     | Plotly |
| Persistence       | joblib |

**All prediction, explanation and recommendation logic is Python.** The original interface is
Streamlit. A second, modern interface (**ChurnIQ**, React + a thin FastAPI layer in `backend/`) sits on top of
the very same `src/` modules; it adds a landing page, a demo login and dark mode but changes no model logic.
No external AI/LLM API is called, and no customer data leaves the machine.

## Machine Learning Models

Required baseline (per project spec): **Logistic Regression, Decision
Tree, Random Forest**. Optionally: Gradient Boosting, Hist Gradient
Boosting. All models share the same preprocessing pipeline for a fair
comparison, and are evaluated on Accuracy, Precision, Recall, F1-score,
and ROC-AUC — the best model is **not** selected on accuracy alone.

## Explainable AI Approach

- **Global explanation** — "What generally influences churn predictions?"
  Shown via the model's built-in feature importance, permutation
  importance, and SHAP mean |value| across the test set.
- **Local explanation** — "Why is THIS customer predicted to churn?"
  Shown via SHAP values for that customer's individual feature vector
  (top positive/negative contributors), with a permutation/coefficient
  based fallback if SHAP is not installed, so the app always works.

## Risk Scoring

Churn probability (0–100%) is mapped into **Low / Medium / High /
Critical** risk bands using thresholds that are configurable from the
UI (Customer Risk page) — these are application-defined risk bands, not
universally valid probability cut-offs.

## Retention Recommendation Engine

A fully local, explainable, **rule-based** engine (no external AI API)
that evaluates each customer's risk and attributes (contract type,
tenure, payment method, tech support, etc.) against IF/THEN rules and
produces suggested — never guaranteed — retention actions.

## What-If Scenario Analysis

Lets you hypothetically change a customer's attributes (contract,
charges, tenure, etc.) and see how the trained model's churn probability
changes. Explicitly labeled **"model-based scenario analysis"** — it
demonstrates how the model reacts to hypothetical inputs, not a causal
guarantee about real customer behavior.

## Dataset Description

Supports the classic Telco Customer Churn schema (customerID, gender,
SeniorCitizen, Partner, Dependents, tenure, PhoneService, MultipleLines,
InternetService, OnlineSecurity, OnlineBackup, DeviceProtection,
TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling,
PaymentMethod, MonthlyCharges, TotalCharges, Churn) but is **not**
hardcoded to it. Any CSV with a detectable churn/target column works,
and column types/target can be manually overridden in the UI. If no
dataset is available, a synthetic ~1,000-row sample dataset (calibrated
to a realistic ~26% churn rate) can be generated with one click.

## Evaluation Metrics

Accuracy, Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix, ROC
Curve, Precision-Recall Curve — all shown per model on the Model
Evaluation page.

## Installation

1. **Requirements:** Python 3.10+ recommended.
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > If `shap` fails to install on your machine (common on some Windows
   > setups without a C++ build toolchain), the app will still run —
   > explanations automatically fall back to a permutation-importance /
   > coefficient-based method.

## How to Run

**React interface (recommended):** double-click or run `run.bat`, then sign in at `http://localhost:5314` with the
demo account `demo@churniq.com` / `Demo@1234` (ports 5314 web, 8314 API). Full instructions, troubleshooting and the
smoke test are in `docs/03_HOW_TO_RUN.md`; the screen-by-screen plan is in `docs/FRONTEND_PLAN.md`.

**Original Streamlit interface:**

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

## Usage Walkthrough

1. **Data Upload** — upload a CSV or click "Use sample dataset instead".
   Confirm/adjust the target and ID columns, review the data-quality
   report, and click "Clean data & prepare for training".
2. **Exploratory Analysis** — review KPIs and churn-rate breakdowns by
   contract, tenure, payment method, etc.
3. **Model Training** — choose imbalance handling and models to train,
   click "Train Models", review the comparison table, then "Save Best
   Model" to make it the active model used across the rest of the app.
4. **Model Evaluation** — ROC/PR curves and confusion matrices per model.
5. **Customer Risk** — adjust risk thresholds and browse the at-risk
   customer table.
6. **Customer 360** — look up a single customer's full profile,
   explanation, and suggested retention actions.
7. **Explainable AI** — global churn drivers and a dedicated local
   explanation view.
8. **What-If Analysis** — build hypothetical scenarios for a customer.
9. **Retention Recommendations** — bulk view of suggested actions for
   at-risk customers, downloadable as CSV.
10. **Batch Prediction** — score a new CSV of customers and download results.
11. **Model Monitoring** — active model metadata and a simple data-drift
    check against newly uploaded data.

## Error Handling

The app validates for missing files, empty datasets, missing/invalid
target columns, missing values, unseen categorical values in new data,
non-numeric values in numeric columns, insufficient rows, and prediction
attempted before training — surfacing friendly Streamlit messages instead
of raw Python tracebacks.

## Security and Data Privacy

- No customer data is sent to any external API or cloud service.
- No external AI/LLM service is used anywhere in the application.
- Uploaded data stays local to the machine running the app.

## Academic Note

This application is intentionally built to go well beyond a standard
churn classification notebook — see **About Project** inside the app for
the full basic-vs-advanced comparison and base paper acknowledgment.

## Future Enhancements

- Deep learning-based churn models for comparison
- Automated periodic retraining / MLOps pipeline
- Integration with a live CRM data source
- Cohort-based retention campaign tracking and outcome measurement
- Multi-language support for retention recommendation text
