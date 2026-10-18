"""Exploratory Data Analysis page: KPIs, churn distributions, and
interactive filtering across key customer attributes."""

import streamlit as st
import pandas as pd

from data_loader import normalize_target
from eda import (
    compute_kpis, churn_distribution_fig, churn_by_category_fig,
    churn_by_numeric_fig, churn_by_tenure_group_fig, correlation_heatmap_fig,
)


CATEGORY_CANDIDATES = [
    "Contract", "InternetService", "PaymentMethod", "SeniorCitizen",
    "Partner", "Dependents", "TechSupport", "OnlineSecurity",
    "PaperlessBilling", "MultipleLines",
]


def render():
    st.title("🔍 Exploratory Data Analysis")

    df = st.session_state.get("working_df")
    target_col = st.session_state.get("target_col")
    if df is None or target_col is None:
        st.warning("Please upload and prepare a dataset first, on the **Data Upload** page.")
        return

    y = normalize_target(df, target_col)

    st.subheader("Key Metrics")
    kpis = compute_kpis(df, target_col, y)
    cols = st.columns(len(kpis))
    labels = {
        "total_customers": "Total Customers", "churned_customers": "Churned",
        "retained_customers": "Retained", "churn_rate_pct": "Churn Rate (%)",
        "avg_tenure": "Avg. Tenure (months)", "avg_monthly_charges": "Avg. Monthly Charges",
        "avg_total_charges": "Avg. Total Charges",
    }
    for c, (k, v) in zip(cols, kpis.items()):
        c.metric(labels.get(k, k), v)

    st.divider()

    filtered = df.copy()
    with st.expander("🔧 Filter data for this analysis", expanded=False):
        available_filters = [c for c in CATEGORY_CANDIDATES if c in df.columns]
        chosen_filter_cols = st.multiselect("Filter by attribute(s)", available_filters)
        for fc in chosen_filter_cols:
            options = sorted(df[fc].dropna().unique().tolist())
            selected = st.multiselect(f"Values for {fc}", options, default=options, key=f"eda_filter_{fc}")
            if selected:
                filtered = filtered[filtered[fc].isin(selected)]
        if len(filtered) != len(df):
            st.caption(f"Showing {len(filtered)} of {len(df)} customers after filtering.")
    y_f = normalize_target(filtered, target_col)

    st.subheader("Churn Distribution")
    st.plotly_chart(churn_distribution_fig(y_f), use_container_width=True)

    st.subheader("Churn Rate by Customer Attributes")
    tab_titles = [c for c in ["Contract", "InternetService", "PaymentMethod", "SeniorCitizen",
                               "TechSupport", "OnlineSecurity", "Partner", "Dependents"] if c in filtered.columns]
    if tab_titles:
        tabs = st.tabs(tab_titles)
        for tab, col in zip(tabs, tab_titles):
            with tab:
                st.plotly_chart(churn_by_category_fig(filtered, col, y_f), use_container_width=True)

    st.subheader("Churn by Tenure Group")
    if "tenure" in filtered.columns:
        st.plotly_chart(churn_by_tenure_group_fig(filtered, y_f), use_container_width=True)

    st.subheader("Numeric Feature Distributions")
    numeric_cols = st.session_state.get("numeric_cols", [])
    numeric_show = [c for c in numeric_cols if c in filtered.columns and filtered[c].nunique() > 2]
    if numeric_show:
        chosen = st.selectbox("Select a numeric feature", numeric_show)
        st.plotly_chart(churn_by_numeric_fig(filtered, chosen, y_f), use_container_width=True)

    if len(numeric_cols) >= 2:
        st.subheader("Correlation Between Numerical Features")
        st.plotly_chart(correlation_heatmap_fig(filtered, numeric_cols), use_container_width=True)
