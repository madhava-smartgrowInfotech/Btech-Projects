"""
app.py
-------
Main entry point for the "Explainable AI-Based Customer Churn
Prediction and Intelligent Retention System" Streamlit application.

Run with:
    streamlit run app.py

This file owns:
- global page config / styling
- session_state initialization
- sidebar navigation
- routing to each page module in pages/
"""

import sys
import os

# Make src/ and pages/ importable as top-level modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages"))

import streamlit as st

from persistence import load_artifacts, artifacts_exist
from utils import DEFAULT_RISK_THRESHOLDS

st.set_page_config(
    page_title="Explainable AI Churn & Retention Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------
DEFAULTS = {
    "raw_df": None,              # originally uploaded / sample dataframe
    "working_df": None,          # cleaned dataframe used for training
    "target_col": None,
    "id_col": None,
    "numeric_cols": [],
    "categorical_cols": [],
    "feature_cols": [],
    "preprocessor": None,
    "model": None,
    "model_name": None,
    "trained_models": {},        # name -> model, for comparison page
    "eval_results": {},          # name -> metrics dict
    "X_train": None, "X_test": None, "y_train": None, "y_test": None,
    "X_train_t": None, "X_test_t": None,
    "feature_names": None,
    "shap_explainer": None,
    "risk_thresholds": DEFAULT_RISK_THRESHOLDS.copy(),
    "model_metadata": None,
    "imbalance_strategy": "class_weight",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# On first load, try restoring a previously-saved model from disk
if st.session_state["model"] is None and artifacts_exist():
    try:
        model, preprocessor, metadata = load_artifacts()
        st.session_state["model"] = model
        st.session_state["preprocessor"] = preprocessor
        st.session_state["model_metadata"] = metadata
        if metadata:
            st.session_state["model_name"] = metadata.get("model_name")
            st.session_state["target_col"] = metadata.get("target_col")
            st.session_state["id_col"] = metadata.get("id_col")
            st.session_state["numeric_cols"] = metadata.get("numeric_cols", [])
            st.session_state["categorical_cols"] = metadata.get("categorical_cols", [])
            st.session_state["feature_cols"] = metadata.get("feature_cols", [])
            st.session_state["feature_names"] = metadata.get("feature_names")
    except Exception:
        pass

# ---------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------
st.sidebar.title("📊 Churn Intelligence")
st.sidebar.caption("Explainable AI-Based Customer Churn Prediction & Intelligent Retention System")

PAGES = [
    "Dashboard",
    "Data Upload",
    "Exploratory Analysis",
    "Model Training",
    "Model Evaluation",
    "Customer Risk",
    "Customer 360",
    "Explainable AI",
    "What-If Analysis",
    "Retention Recommendations",
    "Batch Prediction",
    "Model Monitoring",
    "About Project",
]

if "nav" not in st.session_state:
    st.session_state["nav"] = "Dashboard"

choice = st.sidebar.radio("Navigate", PAGES, key="nav")

st.sidebar.divider()
if st.session_state["working_df"] is not None:
    st.sidebar.success(f"Dataset loaded: {len(st.session_state['working_df'])} rows")
else:
    st.sidebar.warning("No dataset loaded yet")

if st.session_state["model"] is not None:
    st.sidebar.success(f"Model ready: {st.session_state.get('model_name', 'Unknown')}")
else:
    st.sidebar.info("No trained model yet")

st.sidebar.divider()
st.sidebar.caption("Base paper: *Explaining Customer Churn Through Unified "
                    "Perturbation-Based XAI Soft Computing*, IEEE Access, 2026 "
                    "(DOI: 10.1109/ACCESS.2026.3663648)")

# ---------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------
if choice == "Dashboard":
    import page_dashboard
    page_dashboard.render()
elif choice == "Data Upload":
    import page_data_upload
    page_data_upload.render()
elif choice == "Exploratory Analysis":
    import page_eda
    page_eda.render()
elif choice == "Model Training":
    import page_model_training
    page_model_training.render()
elif choice == "Model Evaluation":
    import page_model_evaluation
    page_model_evaluation.render()
elif choice == "Customer Risk":
    import page_customer_risk
    page_customer_risk.render()
elif choice == "Customer 360":
    import page_customer_360
    page_customer_360.render()
elif choice == "Explainable AI":
    import page_explainable_ai
    page_explainable_ai.render()
elif choice == "What-If Analysis":
    import page_whatif
    page_whatif.render()
elif choice == "Retention Recommendations":
    import page_retention
    page_retention.render()
elif choice == "Batch Prediction":
    import page_batch_prediction
    page_batch_prediction.render()
elif choice == "Model Monitoring":
    import page_monitoring
    page_monitoring.render()
elif choice == "About Project":
    import page_about
    page_about.render()
