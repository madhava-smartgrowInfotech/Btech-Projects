"""Main Dashboard page: top KPI cards, key charts, and an at-risk
customer table -- the first thing a user/evaluator sees."""

import streamlit as st
import plotly.express as px

from data_loader import normalize_target
from eda import compute_kpis, churn_distribution_fig, churn_by_category_fig, churn_by_tenure_group_fig, top_churn_drivers_bar
from risk_segmentation import build_risk_table, risk_distribution_summary
from explainability import global_importance, clean_feature_label
from utils import RISK_ORDER, RISK_COLORS


def render():
    st.title("Explainable AI Customer Churn & Retention Intelligence")
    st.caption("An advanced, explainable extension of a traditional telecom churn prediction system.")

    df = st.session_state.get("working_df")
    target_col = st.session_state.get("target_col")
    model = st.session_state.get("model")
    preprocessor = st.session_state.get("preprocessor")

    if df is None or target_col is None:
        st.info("👋 Welcome! Start on the **Data Upload** page to load a dataset (or use the built-in sample data).")
        return

    y = normalize_target(df, target_col)
    kpis = compute_kpis(df, target_col, y)

    thresholds = st.session_state.get("risk_thresholds", {"low": 30, "medium": 60, "high": 80})
    feature_cols = st.session_state.get("feature_cols", [])
    id_col = st.session_state.get("id_col")

    has_model = model is not None and preprocessor is not None
    if has_model:
        risk_table = build_risk_table(
            df, feature_cols, preprocessor, model, id_col, thresholds,
            display_cols=[c for c in ["Contract", "tenure", "MonthlyCharges"] if c in df.columns],
        )
        summary = risk_distribution_summary(risk_table)

    st.subheader("Key Performance Indicators")
    if has_model:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Customers", kpis["total_customers"])
        c2.metric("Churn Rate", f"{kpis['churn_rate_pct']}%")
        c3.metric("High-Risk Customers", summary["counts"].get("High Risk", 0))
        c4.metric("Critical-Risk Customers", summary["counts"].get("Critical Risk", 0))
        c5.metric("Avg. Churn Probability", f"{summary['avg_probability']}%")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Customers", kpis["total_customers"])
        c2.metric("Churn Rate", f"{kpis['churn_rate_pct']}%")
        c3.metric("Avg. Tenure", kpis.get("avg_tenure", "N/A"))
        st.info("Train and save a model on the **Model Training** page to unlock risk scoring and at-risk customer views.")

    st.divider()
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(churn_distribution_fig(y), use_container_width=True)
    with ch2:
        if has_model:
            fig = px.bar(
                x=RISK_ORDER, y=[summary["counts"].get(b, 0) for b in RISK_ORDER],
                color=RISK_ORDER, color_discrete_map=RISK_COLORS,
                labels={"x": "Risk Category", "y": "Customers"}, title="Risk Distribution",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        elif "Contract" in df.columns:
            st.plotly_chart(churn_by_category_fig(df, "Contract", y), use_container_width=True)

    ch3, ch4 = st.columns(2)
    with ch3:
        if "Contract" in df.columns:
            st.plotly_chart(churn_by_category_fig(df, "Contract", y), use_container_width=True)
    with ch4:
        if "tenure" in df.columns:
            st.plotly_chart(churn_by_tenure_group_fig(df, y), use_container_width=True)

    if has_model:
        X_test_t = st.session_state.get("X_test_t")
        y_test = st.session_state.get("y_test")
        feature_names = st.session_state.get("feature_names")
        model_name = st.session_state.get("model_name")
        if X_test_t is not None and feature_names is not None:
            gi = global_importance(model, X_test_t, y_test, feature_names, model_name,
                                    st.session_state.get("shap_explainer"))
            key = "shap_importance" if "shap_importance" in gi else (
                "permutation_importance" if "permutation_importance" in gi else "model_importance"
            )
            if key in gi:
                st.plotly_chart(
                    top_churn_drivers_bar(gi[key], label_fn=clean_feature_label, title="Top Churn Drivers"),
                    use_container_width=True,
                )

        st.divider()
        st.subheader("At-Risk Customers")
        top_risk = risk_table.head(20)
        st.dataframe(top_risk, use_container_width=True, height=400)
