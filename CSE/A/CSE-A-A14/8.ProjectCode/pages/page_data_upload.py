"""Data Upload page: upload a CSV, auto-detect columns, review data
quality, and confirm the target/id columns before moving on to EDA
and model training."""

import streamlit as st
import pandas as pd

from data_loader import (
    load_csv, profile_dataset, coerce_numeric_looking_columns,
    detect_target_column, detect_id_column, normalize_target,
    validate_dataset_for_training,
)
from preprocessing import clean_missing_and_duplicates
from sample_data import generate_sample_churn_data


def _apply_dataset(df: pd.DataFrame):
    df = coerce_numeric_looking_columns(df)
    prof = profile_dataset(df)
    st.session_state["raw_df"] = df
    st.session_state["target_col"] = prof.target_col
    st.session_state["id_col"] = prof.id_col
    st.session_state["numeric_cols"] = prof.numeric_cols
    st.session_state["categorical_cols"] = prof.categorical_cols
    return prof


def render():
    st.title("📁 Data Upload")
    st.write(
        "Upload a telecom customer dataset (CSV) to begin, or use the built-in "
        "sample dataset for demonstration. The app auto-detects the churn "
        "target column, the customer ID column, and numeric vs. categorical "
        "features -- but you can override any of these below."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
    with col2:
        st.write("")
        st.write("")
        use_sample = st.button("Use sample dataset instead", use_container_width=True)

    if uploaded is not None:
        try:
            df = load_csv(uploaded)
            _apply_dataset(df)
            st.success(f"Loaded '{uploaded.name}' with {len(df)} rows and {len(df.columns)} columns.")
        except Exception as e:
            st.error(f"Could not read the uploaded file: {e}")

    if use_sample:
        df = generate_sample_churn_data()
        _apply_dataset(df)
        st.success("Sample telecom churn dataset loaded (1,000 synthetic customers).")

    df = st.session_state.get("raw_df")
    if df is None:
        st.info("No dataset loaded yet. Upload a CSV or click 'Use sample dataset instead' to continue.")
        return

    st.divider()
    st.subheader("Dataset Preview")
    st.dataframe(df.head(15), use_container_width=True)

    st.divider()
    st.subheader("Column Configuration")

    all_cols = df.columns.tolist()
    current_target = st.session_state.get("target_col") or detect_target_column(df)
    current_id = st.session_state.get("id_col") or detect_id_column(df)

    c1, c2 = st.columns(2)
    with c1:
        target_options = ["-- none detected --"] + all_cols
        default_idx = target_options.index(current_target) if current_target in target_options else 0
        target_choice = st.selectbox("Churn / target column", target_options, index=default_idx)
    with c2:
        id_options = ["-- none --"] + all_cols
        default_id_idx = id_options.index(current_id) if current_id in id_options else 0
        id_choice = st.selectbox("Customer ID column (optional)", id_options, index=default_id_idx)

    target_col = None if target_choice == "-- none detected --" else target_choice
    id_col = None if id_choice == "-- none --" else id_choice
    st.session_state["target_col"] = target_col
    st.session_state["id_col"] = id_col

    if target_col is None:
        st.warning("Please select a churn/target column to proceed to model training.")
        return

    feature_candidates = [c for c in all_cols if c not in [target_col, id_col]]
    numeric_default = [c for c in st.session_state.get("numeric_cols", []) if c in feature_candidates]
    categorical_default = [c for c in st.session_state.get("categorical_cols", []) if c in feature_candidates]

    numeric_cols, categorical_cols = numeric_default, categorical_default
    with st.expander("Advanced: manually adjust feature column types", expanded=False):
        cc1, cc2 = st.columns(2)
        with cc1:
            numeric_cols = st.multiselect("Numeric feature columns", feature_candidates, default=numeric_default)
        with cc2:
            remaining = [c for c in feature_candidates if c not in numeric_cols]
            categorical_cols = st.multiselect(
                "Categorical feature columns", remaining,
                default=[c for c in categorical_default if c in remaining]
            )

    st.session_state["numeric_cols"] = numeric_cols
    st.session_state["categorical_cols"] = categorical_cols
    st.session_state["feature_cols"] = numeric_cols + categorical_cols

    st.divider()
    st.subheader("Data Quality Report")

    prof = profile_dataset(df, target_col=target_col, id_col=id_col)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", prof.n_rows)
    m2.metric("Columns", prof.n_cols)
    m3.metric("Duplicate Rows", prof.n_duplicates)
    m4.metric("Columns with Missing Values", len(prof.missing_summary) if prof.missing_summary is not None else 0)

    if prof.warnings:
        for w in prof.warnings:
            st.warning(w)
    else:
        st.success("No major data quality issues detected.")

    if prof.missing_summary is not None and len(prof.missing_summary) > 0:
        st.write("**Missing values by column:**")
        st.dataframe(prof.missing_summary.rename("missing_count"), use_container_width=True)

    errors = validate_dataset_for_training(df, target_col)
    if errors:
        for e in errors:
            st.error(e)
    else:
        st.success("Dataset passes basic training-readiness checks.")

    st.divider()
    if st.button("✅ Clean data & prepare for training", type="primary"):
        cleaned, report = clean_missing_and_duplicates(df, drop_duplicates=True)
        st.session_state["working_df"] = cleaned
        st.success(
            f"Data prepared: {report['duplicates_removed']} duplicate rows removed, "
            f"{report['rows_remaining']} rows remaining. Missing values will be imputed "
            f"automatically during model training."
        )
        st.info("Proceed to **Exploratory Analysis** or **Model Training** from the sidebar.")
