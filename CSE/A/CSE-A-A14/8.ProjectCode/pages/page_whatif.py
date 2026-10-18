"""What-If Analysis page: let the user interactively modify a
customer's attributes and see how the model's churn probability
changes under that hypothetical scenario."""

import streamlit as st
import pandas as pd
import numpy as np

from prediction import score_customers


def render():
    st.title("🧪 What-If Churn Analysis")
    st.caption(
        "This is model-based scenario analysis: it shows how the trained model's prediction "
        "changes under hypothetical customer attributes. It does NOT claim that making these "
        "changes will actually cause the customer to stay."
    )

    df = st.session_state.get("working_df")
    model = st.session_state.get("model")
    preprocessor = st.session_state.get("preprocessor")
    feature_cols = st.session_state.get("feature_cols", [])
    numeric_cols = st.session_state.get("numeric_cols", [])
    categorical_cols = st.session_state.get("categorical_cols", [])
    id_col = st.session_state.get("id_col")

    if df is None:
        st.warning("Please upload and prepare a dataset first, on the **Data Upload** page.")
        return
    if model is None or preprocessor is None:
        st.warning("No active trained model. Please train and save a model on the **Model Training** page.")
        return

    if id_col and id_col in df.columns:
        customer_ids = df[id_col].astype(str).tolist()
        selected_id = st.selectbox("Select a customer as the starting point", customer_ids)
        row = df[df[id_col].astype(str) == selected_id].iloc[0]
    else:
        idx = st.number_input("Select customer (row index)", 0, len(df) - 1, 0)
        row = df.iloc[int(idx)]
        selected_id = f"Row {idx}"

    original_raw = pd.DataFrame([row[feature_cols]])
    original_proba = float(score_customers(original_raw, preprocessor, model)[0])

    st.divider()
    st.subheader("Current Attributes vs. Scenario")
    st.write("Adjust any attribute below to build a hypothetical scenario for this customer.")

    scenario_values = {}
    cols_per_row = 3
    all_editable = numeric_cols + categorical_cols
    rows_of_cols = [all_editable[i:i + cols_per_row] for i in range(0, len(all_editable), cols_per_row)]

    for group in rows_of_cols:
        ui_cols = st.columns(len(group))
        for uc, feat in zip(ui_cols, group):
            current_val = row[feat]
            with uc:
                if feat in numeric_cols:
                    col_series = df[feat].dropna()
                    lo, hi = float(col_series.min()), float(col_series.max())
                    if lo == hi:
                        hi = lo + 1
                    step = 1.0 if col_series.dtype.kind in "iu" else round((hi - lo) / 100, 2) or 0.1
                    scenario_values[feat] = st.slider(
                        feat, lo, hi, float(current_val) if pd.notna(current_val) else lo, step=step, key=f"wi_{feat}"
                    )
                else:
                    options = sorted(df[feat].dropna().unique().astype(str).tolist())
                    default_idx = options.index(str(current_val)) if str(current_val) in options else 0
                    scenario_values[feat] = st.selectbox(feat, options, index=default_idx, key=f"wi_{feat}")

    scenario_row = row.copy()
    for feat, val in scenario_values.items():
        scenario_row[feat] = val
    scenario_raw = pd.DataFrame([scenario_row[feature_cols]])
    scenario_proba = float(score_customers(scenario_raw, preprocessor, model)[0])

    st.divider()
    st.subheader("Scenario Result")
    r1, r2, r3 = st.columns(3)
    r1.metric("Original Churn Probability", f"{original_proba:.1f}%")
    r2.metric("Scenario Churn Probability", f"{scenario_proba:.1f}%")
    diff = scenario_proba - original_proba
    r3.metric("Change", f"{diff:+.1f} pp", delta=f"{diff:+.1f} pp", delta_color="inverse")

    if abs(diff) < 0.5:
        st.info("The scenario produces almost no change in predicted churn probability.")
    elif diff < 0:
        st.success(f"Under this scenario, the model's predicted churn probability decreases by {abs(diff):.1f} percentage points.")
    else:
        st.warning(f"Under this scenario, the model's predicted churn probability increases by {diff:.1f} percentage points.")

    st.caption("Label: **Model-based scenario analysis** -- demonstrates how the model's prediction changes "
               "under hypothetical customer attributes; it is not a causal guarantee of customer behavior.")
