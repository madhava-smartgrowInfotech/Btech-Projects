"""About Project page: static project documentation shown inside the app."""

import streamlit as st


def render():
    st.title("ℹ️ About This Project")

    st.markdown("""
## Explainable AI-Based Customer Churn Prediction and Intelligent Retention System

**B.Tech Final-Year Major Project** — an advanced extension of
*"Customer Churn Prediction in Telecom Industry (Machine Learning Based
Customer Retention System)."*

### Problem Statement
A basic churn prediction system only answers **whether** a customer may
churn. An actionable retention system must also answer:

1. **WHO** is likely to churn?
2. **HOW LIKELY** are they to churn?
3. **WHY** are they likely to churn?
4. **WHAT RETENTION ACTION** could be considered?

### System Architecture

```
Customer data
   → preprocessing (imputation, encoding, scaling)
   → exploratory data analysis
   → class imbalance handling (class_weight / SMOTE)
   → multiple ML models (Logistic Regression, Decision Tree, Random Forest, ...)
   → model comparison (Accuracy, Precision, Recall, F1, ROC-AUC)
   → churn probability (0-100%)
   → customer risk segmentation (Low / Medium / High / Critical)
   → local explainable AI (per-customer SHAP explanations)
   → global explainable AI (model-wide feature importance)
   → rule-based retention recommendation engine
   → what-if scenario analysis
   → interactive Customer 360° profile
   → batch prediction
   → retention intelligence dashboard
```

### Technology Stack
- **Language:** Python only
- **UI:** Streamlit
- **ML:** scikit-learn (Logistic Regression, Decision Tree, Random Forest,
  Gradient Boosting / HistGradientBoosting)
- **Explainability:** SHAP (with a local permutation-importance /
  coefficient-based fallback if SHAP is unavailable)
- **Imbalance handling:** class_weight='balanced' or SMOTE (imbalanced-learn)
- **Visualization:** Plotly
- **Persistence:** joblib

### Explainable AI Approach
- **Global explanation:** model built-in feature importance, permutation
  importance, and SHAP mean |value| across the test set — answers
  *"what generally influences churn predictions?"*
- **Local explanation:** SHAP values (or the fallback heuristic) for a
  single customer's transformed feature vector — answers
  *"why was THIS customer predicted to churn?"*

### Risk Scoring
Churn probability (0-100%) is mapped to **configurable** risk bands
(Low / Medium / High / Critical) via adjustable thresholds in the UI.
These bands are **application-defined**, not universally valid
probability cut-offs.

### Retention Recommendation Engine
A fully local, rule-based IF/THEN engine — **no external AI/LLM API is
used**. Recommendations are always phrased as *suggested actions*, never
guarantees of retention outcomes.

### What-If Scenario Analysis
Lets a user hypothetically change a customer's attributes and observe
how the trained model's prediction changes. This is explicitly labeled
**"model-based scenario analysis"** — it does not claim the change will
cause the customer to stay.

### Dataset
Supports the classic Telco Customer Churn schema (customerID, gender,
SeniorCitizen, Partner, Dependents, tenure, PhoneService, MultipleLines,
InternetService, OnlineSecurity, OnlineBackup, DeviceProtection,
TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling,
PaymentMethod, MonthlyCharges, TotalCharges, Churn) but is not
hardcoded to it — any CSV with a detectable target column will work,
and a synthetic sample dataset is generated automatically if none is
uploaded.

### Evaluation Metrics
Accuracy, Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix, ROC
Curve, and Precision-Recall Curve. The best model is **not** selected
on accuracy alone.

### Base Paper
*"Explaining Customer Churn Through Unified Perturbation-Based XAI Soft
Computing,"* IEEE Access, 2026. DOI: `10.1109/ACCESS.2026.3663648`.

This application is an **applied extension** of the base paper's
motivation — that traditional churn prediction should be paired with
individual-level explanation and actionable retention support — for a
telecom customer retention scenario. It does not claim to reproduce
every algorithm or experiment from the base paper.

### Security & Privacy
- No customer data is sent to any external API.
- No external AI/LLM service is used anywhere in the application.
- All prediction, explanation, and recommendation logic runs **locally**.

### Future Enhancements
- Deep learning-based churn models (e.g. TabNet, neural nets) for comparison
- Automated periodic retraining / MLOps pipeline
- Integration with a live CRM data source
- Cohort-based retention campaign tracking and outcome measurement
- Multi-language support for the retention recommendation text
    """)
