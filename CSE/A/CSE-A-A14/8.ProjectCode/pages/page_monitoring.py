"""Model Monitoring page: shows current active-model metadata and lets
the user compare a newly uploaded dataset's feature distributions
against the training dataset to spot potential drift or data-quality
issues before running predictions."""

import streamlit as st
import pandas as pd
import numpy as np

from data_loader import load_csv, coerce_numeric_looking_columns


def render():
    st.title("🩺 Model Monitoring")

    metadata = st.session_state.get("model_metadata")
    if metadata is None:
        st.warning("No active saved model. Please train and save a model on the **Model Training** page.")
        return

    st.subheader("Current Active Model")
    c1, c2, c3 = st.columns(3)
    c1.metric("Model Name", metadata.get("model_name", "N/A"))
    c2.metric("Training Dataset Size", metadata.get("training_dataset_size", "N/A"))
    c3.metric("Feature Count", len(metadata.get("feature_names", []) or []))

    c4, c5 = st.columns(2)
    c4.metric("Saved At", metadata.get("saved_at", "N/A"))
    c5.metric("Imbalance Strategy", metadata.get("imbalance_strategy", "N/A"))

    st.write("**Model metrics at save time:**")
    metrics = metadata.get("metrics", {})
    if metrics:
        mc = st.columns(len(metrics))
        for col, (k, v) in zip(mc, metrics.items()):
            col.metric(k.replace("_", " ").title(), f"{v:.4f}" if isinstance(v, float) else v)

    with st.expander("Feature columns used by this model"):
        st.write(", ".join(metadata.get("feature_cols", [])))

    st.divider()
    st.subheader("Data Drift Check (optional)")
    st.write(
        "Upload a new dataset to compare its structure and feature distributions against the "
        "training dataset, and surface warnings about missing columns, unexpected categories, "
        "high missingness, or severe class imbalance."
    )

    uploaded = st.file_uploader("Upload a dataset to compare", type=["csv"], key="monitor_upload")
    if uploaded is None:
        return

    try:
        new_df = load_csv(uploaded)
        new_df = coerce_numeric_looking_columns(new_df)
    except Exception as e:
        st.error(f"Could not read the uploaded file: {e}")
        return

    expected_cols = metadata.get("feature_cols", [])
    missing_cols = [c for c in expected_cols if c not in new_df.columns]
    if missing_cols:
        st.error(f"⚠️ Missing expected column(s): {', '.join(missing_cols)}")

    present_cols = [c for c in expected_cols if c in new_df.columns]
    numeric_cols = [c for c in metadata.get("numeric_cols", []) if c in present_cols]
    categorical_cols = [c for c in metadata.get("categorical_cols", []) if c in present_cols]

    missing_pct = new_df[present_cols].isna().mean().mean() * 100 if present_cols else 0
    if missing_pct > 10:
        st.warning(f"⚠️ High missing-value percentage in the new data: {missing_pct:.1f}% of feature cells are empty.")

    working_df = st.session_state.get("working_df")
    if working_df is not None and categorical_cols:
        st.write("**Unexpected categorical values (not seen during training):**")
        found_any = False
        for c in categorical_cols:
            if c in working_df.columns:
                known = set(working_df[c].dropna().unique())
                new_vals = set(new_df[c].dropna().unique()) - known
                if new_vals:
                    found_any = True
                    st.write(f"- `{c}`: {', '.join(map(str, new_vals))}")
        if not found_any:
            st.success("No unexpected categorical values found.")

    if numeric_cols and working_df is not None:
        st.write("**Numeric feature distribution comparison (mean):**")
        rows = []
        for c in numeric_cols:
            if c in working_df.columns and c in new_df.columns:
                rows.append({
                    "feature": c,
                    "training_mean": round(pd.to_numeric(working_df[c], errors="coerce").mean(), 2),
                    "new_data_mean": round(pd.to_numeric(new_df[c], errors="coerce").mean(), 2),
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    target_col = metadata.get("target_col")
    if target_col and target_col in new_df.columns:
        from data_loader import normalize_target
        y_new = normalize_target(new_df, target_col)
        churn_rate = y_new.mean() * 100
        st.metric("New Data Churn Rate", f"{churn_rate:.1f}%")
        if y_new.value_counts().min() < 5:
            st.warning("⚠️ Severe class imbalance detected in the new data (one class has fewer than 5 examples).")
