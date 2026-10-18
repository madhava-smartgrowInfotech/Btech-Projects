"""Customer 360 page: a single consolidated profile view combining
customer/service/billing info, churn probability, risk category, top
drivers, and suggested retention actions."""

import streamlit as st
import pandas as pd

from prediction import score_customers
from explainability import local_explanation, clean_feature_label
from utils import assign_risk_category, RISK_COLORS
from retention_engine import generate_recommendations


PROFILE_GROUPS = {
    "Customer Information": ["gender", "SeniorCitizen", "Partner", "Dependents"],
    "Service Information": ["PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
                             "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"],
    "Billing Information": ["Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges"],
}


def render():
    st.title("🪪 Customer 360° Profile")

    df = st.session_state.get("working_df")
    model = st.session_state.get("model")
    preprocessor = st.session_state.get("preprocessor")
    feature_cols = st.session_state.get("feature_cols", [])
    feature_names = st.session_state.get("feature_names")
    explainer = st.session_state.get("shap_explainer")
    id_col = st.session_state.get("id_col")
    thresholds = st.session_state.get("risk_thresholds", {"low": 30, "medium": 60, "high": 80})

    if df is None:
        st.warning("Please upload and prepare a dataset first, on the **Data Upload** page.")
        return
    if model is None or preprocessor is None:
        st.warning("No active trained model. Please train and save a model on the **Model Training** page.")
        return

    st.subheader("Find a Customer")
    fc1, fc2 = st.columns([2, 1])
    with fc1:
        if id_col and id_col in df.columns:
            customer_ids = df[id_col].astype(str).tolist()
            search = st.text_input("Search customer ID")
            options = [c for c in customer_ids if search.lower() in c.lower()] if search else customer_ids
            selected_id = st.selectbox("Select customer", options[:200])
            row = df[df[id_col].astype(str) == selected_id].iloc[0]
        else:
            idx = st.number_input("Select customer (row index)", 0, len(df) - 1, 0)
            row = df.iloc[int(idx)]
            selected_id = f"Row {idx}"
    with fc2:
        st.write("")

    x_row_raw = pd.DataFrame([row[feature_cols]])
    proba = float(score_customers(x_row_raw, preprocessor, model)[0])
    risk = assign_risk_category(proba, thresholds)

    st.divider()
    h1, h2, h3 = st.columns(3)
    h1.metric("Customer ID", selected_id)
    h2.metric("Churn Probability", f"{proba:.1f}%")
    with h3:
        st.markdown(
            f"<div style='padding:0.5em;border-radius:6px;background-color:{RISK_COLORS.get(risk,'#ccc')}22;"
            f"border:1px solid {RISK_COLORS.get(risk,'#ccc')};text-align:center;'>"
            f"<b>Risk Category</b><br><span style='font-size:1.3em;color:{RISK_COLORS.get(risk,'#333')}'>{risk}</span></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    for group_name, cols in PROFILE_GROUPS.items():
        present = [c for c in cols if c in df.columns]
        if not present:
            continue
        st.subheader(group_name)
        vals_cols = st.columns(min(4, len(present)))
        for i, c in enumerate(present):
            vals_cols[i % len(vals_cols)].write(f"**{c}:** {row[c]}")

    if "tenure" in df.columns:
        st.write(f"**Tenure:** {row['tenure']} months")

    st.divider()
    st.subheader("Model Explanation")
    x_row_t = preprocessor.transform(x_row_raw)
    x_row_dense = x_row_t.toarray()[0] if hasattr(x_row_t, "toarray") else x_row_t[0]
    top_pos, top_neg, method = local_explanation(explainer, model, x_row_dense, feature_names, top_n=5)

    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown("**Top churn drivers:**")
        for f, v in top_pos:
            st.write(f"🔺 {clean_feature_label(f)}")
        if not top_pos:
            st.write("None identified.")
    with ec2:
        st.markdown("**Protective factors:**")
        for f, v in top_neg:
            st.write(f"🔻 {clean_feature_label(f)}")
        if not top_neg:
            st.write("None identified.")

    st.divider()
    st.subheader("Suggested Retention Actions")
    st.caption("These are model-informed suggestions, not guarantees -- final decisions should involve human judgment.")
    recs = generate_recommendations(row, proba, risk)
    for reason, suggestion in recs:
        st.write(f"- **{suggestion}**  _(reason: {reason})_")
