"""Explainable AI page: clearly separated GLOBAL explanation (what
generally drives churn across the whole model) and LOCAL explanation
(why this specific customer received their prediction)."""

import streamlit as st
import numpy as np
import pandas as pd

from explainability import global_importance, local_explanation, clean_feature_label, SHAP_AVAILABLE
from eda import top_churn_drivers_bar
from prediction import score_customers


def render():
    st.title("🧩 Explainable AI — Churn Drivers")

    df = st.session_state.get("working_df")
    model = st.session_state.get("model")
    preprocessor = st.session_state.get("preprocessor")
    feature_cols = st.session_state.get("feature_cols", [])
    feature_names = st.session_state.get("feature_names")
    model_name = st.session_state.get("model_name")
    explainer = st.session_state.get("shap_explainer")

    if df is None or model is None or preprocessor is None:
        st.warning("Please train and save a model first, on the **Model Training** page.")
        return

    if not SHAP_AVAILABLE:
        st.info(
            "SHAP is not installed in this environment, so explanations below use a "
            "permutation-importance / model-coefficient fallback instead of true SHAP values. "
            "Install `shap` (`pip install shap`) for full SHAP-based explanations."
        )

    X_test_t = st.session_state.get("X_test_t")
    y_test = st.session_state.get("y_test")

    st.header("🌍 Global Explanation")
    st.caption("What generally influences the model's churn predictions across ALL customers.")

    if X_test_t is None or feature_names is None:
        st.warning("Train a model on the Model Training page to see global explanations.")
    else:
        gi = global_importance(model, X_test_t, y_test, feature_names, model_name, explainer)
        available = list(gi.keys())
        label_map = {
            "model_importance": "Model's Built-in Importance",
            "permutation_importance": "Permutation Importance",
            "shap_importance": "SHAP Global Importance",
        }
        if available:
            tabs = st.tabs([label_map[k] for k in available])
            for tab, key in zip(tabs, available):
                with tab:
                    st.plotly_chart(
                        top_churn_drivers_bar(gi[key], label_fn=clean_feature_label, title=f"Top 10 Churn Drivers — {label_map[key]}"),
                        use_container_width=True,
                    )
        else:
            st.warning("Could not compute global importance for this model.")

    st.divider()
    st.header("👤 Local Explanation")
    st.caption("Why THIS specific customer received their churn prediction — not just the global pattern.")

    id_col = st.session_state.get("id_col")
    if id_col and id_col in df.columns:
        customer_ids = df[id_col].astype(str).tolist()
        selected_id = st.selectbox("Select a customer", customer_ids)
        row = df[df[id_col].astype(str) == selected_id].iloc[0]
    else:
        idx = st.number_input("Select a customer (row index)", 0, len(df) - 1, 0)
        row = df.iloc[int(idx)]
        selected_id = f"Row {idx}"

    x_row_raw = pd.DataFrame([row[feature_cols]])
    proba = float(score_customers(x_row_raw, preprocessor, model)[0])
    x_row_t = preprocessor.transform(x_row_raw)

    c1, c2 = st.columns(2)
    c1.metric("Customer", selected_id)
    c2.metric("Churn Probability", f"{proba:.1f}%")

    x_row_dense = x_row_t.toarray()[0] if hasattr(x_row_t, "toarray") else np.asarray(x_row_t)[0]
    top_pos, top_neg, method = local_explanation(explainer, model, x_row_dense, feature_names, top_n=5)
    st.caption(f"Explanation method: {'SHAP' if method == 'shap' else 'Approximate (importance × feature value)'}")

    lc1, lc2 = st.columns(2)
    with lc1:
        st.markdown("**Main churn drivers (push toward churn):**")
        if top_pos:
            for f, v in top_pos:
                st.write(f"🔺 {clean_feature_label(f)}")
        else:
            st.write("None identified.")
    with lc2:
        st.markdown("**Protective factors (push away from churn):**")
        if top_neg:
            for f, v in top_neg:
                st.write(f"🔻 {clean_feature_label(f)}")
        else:
            st.write("None identified.")
