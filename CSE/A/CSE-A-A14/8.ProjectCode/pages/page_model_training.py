"""Model Training page: configure preprocessing/imbalance handling,
train and compare Logistic Regression / Decision Tree / Random Forest
(+ optional boosting models), and save the chosen model to disk."""

import streamlit as st
import numpy as np
import pandas as pd

from data_loader import normalize_target
from preprocessing import build_preprocessor, get_feature_names, train_test_split_data, class_distribution
from train_models import train_selected_models, select_best_model, REQUIRED_MODELS, OPTIONAL_MODELS
from evaluation import results_to_table
from explainability import get_shap_explainer
from persistence import save_artifacts


def render():
    st.title("🧠 Model Training")

    df = st.session_state.get("working_df")
    target_col = st.session_state.get("target_col")
    feature_cols = st.session_state.get("feature_cols", [])
    numeric_cols = st.session_state.get("numeric_cols", [])
    categorical_cols = st.session_state.get("categorical_cols", [])

    if df is None or target_col is None or not feature_cols:
        st.warning("Please upload, configure and clean a dataset first, on the **Data Upload** page.")
        return

    st.subheader("Dataset Summary")
    y_full = normalize_target(df, target_col)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dataset Size", len(df))
    c2.metric("Total Features", len(feature_cols))
    c3.metric("Numeric Features", len(numeric_cols))
    c4.metric("Categorical Features", len(categorical_cols))

    dist = class_distribution(y_full)
    st.write(
        f"**Class distribution:** Retained = {dist['counts'].get(0, 0)} "
        f"({dist['percentages'].get(0, 0)}%), Churned = {dist['counts'].get(1, 0)} "
        f"({dist['percentages'].get(1, 0)}%) -- imbalance ratio ≈ {dist['imbalance_ratio']}:1"
    )

    st.divider()
    st.subheader("Training Configuration")

    tc1, tc2 = st.columns(2)
    with tc1:
        test_size = st.slider("Test set size", 0.1, 0.4, 0.2, 0.05)
        imbalance_strategy = st.selectbox(
            "Class imbalance handling",
            ["class_weight", "smote", "none"],
            format_func=lambda x: {"class_weight": "class_weight='balanced'", "smote": "SMOTE oversampling", "none": "None"}[x],
        )
    with tc2:
        model_choices = st.multiselect(
            "Models to train", REQUIRED_MODELS + OPTIONAL_MODELS,
            default=REQUIRED_MODELS,
            help="Logistic Regression, Decision Tree and Random Forest are required by the project spec."
        )
        selection_metric = st.selectbox(
            "Metric used to recommend the best model", ["f1_score", "roc_auc", "recall", "precision", "accuracy"],
            help="Per project requirement, the best model is NOT selected on accuracy alone by default."
        )

    if imbalance_strategy == "smote":
        try:
            import imblearn  # noqa: F401
        except Exception:
            st.warning("The `imbalanced-learn` package is not installed -- SMOTE will not be available. "
                       "Install it with `pip install imbalanced-learn`, or choose another strategy.")

    missing_required = [m for m in REQUIRED_MODELS if m not in model_choices]
    if missing_required:
        st.info(f"Note: the project requires {', '.join(REQUIRED_MODELS)} to be trained and compared.")

    train_clicked = st.button("🚀 Train Models", type="primary", disabled=len(model_choices) == 0)

    if train_clicked:
        with st.spinner("Preprocessing data and training models..."):
            X = df[feature_cols]
            y = y_full
            X_train, X_test, y_train, y_test = train_test_split_data(X, y, test_size=test_size)

            preprocessor = build_preprocessor(numeric_cols, categorical_cols)
            X_train_t = preprocessor.fit_transform(X_train)
            X_test_t = preprocessor.transform(X_test)
            feature_names = get_feature_names(preprocessor)

            try:
                strategy = imbalance_strategy
                if strategy == "smote":
                    import imblearn  # noqa: F401
            except Exception:
                strategy = "class_weight"

            trained_models, results = train_selected_models(
                X_train_t, y_train.values, X_test_t, y_test.values,
                model_choices, imbalance_strategy=strategy,
            )

        st.session_state.update({
            "preprocessor": preprocessor,
            "trained_models": trained_models,
            "eval_results": results,
            "X_train_t": X_train_t, "X_test_t": X_test_t,
            "y_train": y_train.values, "y_test": y_test.values,
            "feature_names": feature_names,
            "imbalance_strategy": strategy,
        })
        st.success(f"Trained {len(trained_models)} model(s) successfully.")

    results = st.session_state.get("eval_results", {})
    if results:
        st.divider()
        st.subheader("Model Comparison")
        table = results_to_table(results)
        st.dataframe(table, use_container_width=True)

        recommended = select_best_model(results, metric=selection_metric)
        st.info(f"📌 Recommended model based on **{selection_metric}**: **{recommended}**")

        st.subheader("Save Final Model")
        final_choice = st.selectbox("Select the model to save for use across the app", list(results.keys()),
                                     index=list(results.keys()).index(recommended) if recommended in results else 0)

        if st.button("💾 Save Best Model", type="primary"):
            model = st.session_state["trained_models"][final_choice]
            preprocessor = st.session_state["preprocessor"]
            feature_names = st.session_state["feature_names"]

            metadata = {
                "model_name": final_choice,
                "target_col": target_col,
                "id_col": st.session_state.get("id_col"),
                "numeric_cols": numeric_cols,
                "categorical_cols": categorical_cols,
                "feature_cols": feature_cols,
                "feature_names": feature_names,
                "metrics": {k: v for k, v in results[final_choice].items()
                            if k in ("accuracy", "precision", "recall", "f1_score", "roc_auc")},
                "training_dataset_size": len(df),
                "imbalance_strategy": st.session_state.get("imbalance_strategy"),
            }
            saved_meta = save_artifacts(model, preprocessor, metadata)

            with st.spinner("Building explainability engine..."):
                explainer = get_shap_explainer(model, st.session_state["X_train_t"], final_choice)

            st.session_state.update({
                "model": model, "model_name": final_choice, "model_metadata": saved_meta,
                "shap_explainer": explainer,
            })
            st.success(f"'{final_choice}' saved as the active model. You can now use Customer Risk, "
                       "Explainable AI, What-If Analysis, and Batch Prediction.")
