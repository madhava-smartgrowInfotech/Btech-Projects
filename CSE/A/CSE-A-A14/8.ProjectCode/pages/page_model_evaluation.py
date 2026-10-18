"""Model Evaluation page: confusion matrices, ROC and Precision-Recall
curves for every trained model in this session."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


def _confusion_matrix_fig(cm, model_name):
    labels = ["Retained (0)", "Churned (1)"]
    fig = px.imshow(cm, text_auto=True, x=labels, y=labels, color_continuous_scale="Blues",
                     title=f"Confusion Matrix — {model_name}")
    fig.update_layout(xaxis_title="Predicted", yaxis_title="Actual", coloraxis_showscale=False)
    return fig


def _roc_fig(results):
    fig = go.Figure()
    for name, m in results.items():
        fpr, tpr = m["roc_curve"]
        fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", name=f"{name} (AUC={m['roc_auc']:.3f})"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random", line=dict(dash="dash", color="gray")))
    fig.update_layout(title="ROC Curves", xaxis_title="False Positive Rate", yaxis_title="True Positive Rate")
    return fig


def _pr_fig(results):
    fig = go.Figure()
    for name, m in results.items():
        prec, rec = m["pr_curve"]
        fig.add_trace(go.Scatter(x=rec, y=prec, mode="lines", name=name))
    fig.update_layout(title="Precision-Recall Curves", xaxis_title="Recall", yaxis_title="Precision")
    return fig


def render():
    st.title("📈 Model Evaluation")

    results = st.session_state.get("eval_results", {})
    if not results:
        st.warning("No trained models in this session yet. Please train models on the **Model Training** page.")
        return

    st.subheader("ROC Curves — All Trained Models")
    st.plotly_chart(_roc_fig(results), use_container_width=True)

    st.subheader("Precision-Recall Curves — All Trained Models")
    st.plotly_chart(_pr_fig(results), use_container_width=True)

    st.divider()
    st.subheader("Per-Model Confusion Matrix")
    model_name = st.selectbox("Select a model", list(results.keys()))
    m = results[model_name]

    cm1, cm2 = st.columns([1, 1])
    with cm1:
        st.plotly_chart(_confusion_matrix_fig(m["confusion_matrix"], model_name), use_container_width=True)
    with cm2:
        st.metric("Accuracy", f"{m['accuracy']:.4f}")
        st.metric("Precision", f"{m['precision']:.4f}")
        st.metric("Recall", f"{m['recall']:.4f}")
        st.metric("F1-Score", f"{m['f1_score']:.4f}")
        st.metric("ROC-AUC", f"{m['roc_auc']:.4f}" if not np.isnan(m["roc_auc"]) else "N/A")

    if st.session_state.get("model_name") == model_name:
        st.success(f"'{model_name}' is currently the ACTIVE saved model used across the app.")

    st.caption(
        "Note: the best model is not chosen on accuracy alone -- on an imbalanced churn "
        "dataset, precision, recall, F1-score and ROC-AUC together give a more reliable picture "
        "of how well the model identifies customers who will actually churn."
    )
