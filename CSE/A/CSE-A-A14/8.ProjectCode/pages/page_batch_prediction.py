"""Batch Prediction page: upload a new CSV of customers, validate its
columns against the trained model's expected features, score every
row, and let the user download the results."""

import streamlit as st
import pandas as pd

from data_loader import load_csv, coerce_numeric_looking_columns
from prediction import validate_columns_for_prediction, build_batch_predictions
from explainability import local_explanation, clean_feature_label


def _top_driver_lookup_factory(preprocessor, model, feature_cols, feature_names, explainer):
    def lookup(row):
        x_raw = pd.DataFrame([row[feature_cols]])
        x_t = preprocessor.transform(x_raw)
        x_dense = x_t.toarray()[0] if hasattr(x_t, "toarray") else x_t[0]
        top_pos, _, _ = local_explanation(explainer, model, x_dense, feature_names, top_n=3)
        return [clean_feature_label(f) for f, v in top_pos]
    return lookup


def render():
    st.title("📦 Batch Prediction")
    st.write(
        "Upload a new CSV of customers to score them all at once. The file must contain the same "
        "feature columns the active model was trained on."
    )

    model = st.session_state.get("model")
    preprocessor = st.session_state.get("preprocessor")
    feature_cols = st.session_state.get("feature_cols", [])
    feature_names = st.session_state.get("feature_names")
    id_col = st.session_state.get("id_col")
    thresholds = st.session_state.get("risk_thresholds", {"low": 30, "medium": 60, "high": 80})
    explainer = st.session_state.get("shap_explainer")

    if model is None or preprocessor is None:
        st.warning("No active trained model. Please train and save a model on the **Model Training** page.")
        return

    st.info(f"Active model expects these feature columns: {', '.join(feature_cols)}")

    uploaded = st.file_uploader("Upload a CSV file to score", type=["csv"], key="batch_upload")
    if uploaded is None:
        return

    try:
        new_df = load_csv(uploaded)
        new_df = coerce_numeric_looking_columns(new_df)
    except Exception as e:
        st.error(f"Could not read the uploaded file: {e}")
        return

    st.write(f"Loaded {len(new_df)} rows.")
    problems = validate_columns_for_prediction(new_df, feature_cols)
    if problems:
        for p in problems:
            st.error(p)
        st.stop()

    missing_vals = new_df[feature_cols].isna().sum().sum()
    if missing_vals > 0:
        st.warning(f"{int(missing_vals)} missing values detected in feature columns -- these will be "
                   f"automatically imputed using the same strategy learned during training.")

    include_drivers = st.checkbox("Include top risk factors per customer (slower for large files)", value=len(new_df) <= 300)

    if st.button("🔮 Run Batch Prediction", type="primary"):
        with st.spinner("Scoring customers..."):
            driver_lookup = None
            if include_drivers:
                driver_lookup = _top_driver_lookup_factory(preprocessor, model, feature_cols, feature_names, explainer)
            try:
                results = build_batch_predictions(
                    new_df, feature_cols, preprocessor, model,
                    id_col if id_col in new_df.columns else None,
                    thresholds, top_driver_lookup=driver_lookup,
                )
            except Exception as e:
                st.error(f"Prediction failed: {e}")
                st.stop()

        st.success(f"Scored {len(results)} customers.")
        st.dataframe(results, use_container_width=True, height=450)

        st.download_button(
            "⬇️ Download predictions as CSV", results.to_csv(index=False).encode("utf-8"),
            file_name="churn_batch_predictions.csv", mime="text/csv",
        )
