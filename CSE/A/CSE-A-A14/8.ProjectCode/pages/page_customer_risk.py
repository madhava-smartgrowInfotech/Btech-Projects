"""Customer Risk page: score the full dataset, segment customers into
configurable Low / Medium / High / Critical risk bands, and provide a
filterable, sortable table of at-risk customers."""

import streamlit as st
import plotly.express as px

from risk_segmentation import build_risk_table, risk_distribution_summary
from utils import RISK_ORDER, RISK_COLORS


DISPLAY_COLS = ["Contract", "tenure", "MonthlyCharges", "InternetService", "PaymentMethod"]


def render():
    st.title("🚦 Customer Risk Segmentation")

    df = st.session_state.get("working_df")
    model = st.session_state.get("model")
    preprocessor = st.session_state.get("preprocessor")
    feature_cols = st.session_state.get("feature_cols", [])

    if df is None:
        st.warning("Please upload and prepare a dataset first, on the **Data Upload** page.")
        return
    if model is None or preprocessor is None:
        st.warning("No active trained model. Please train and save a model on the **Model Training** page.")
        return

    st.subheader("Risk Threshold Configuration")
    st.caption(
        "These bands are application-defined risk categories based on the model's predicted "
        "churn probability -- they are not universally valid probability cut-offs and can be "
        "adjusted for your business context."
    )
    t = st.session_state.get("risk_thresholds", {"low": 30, "medium": 60, "high": 80})
    c1, c2, c3 = st.columns(3)
    with c1:
        low = st.slider("Low / Medium boundary (%)", 5, 50, t["low"])
    with c2:
        medium = st.slider("Medium / High boundary (%)", low + 5, 85, max(t["medium"], low + 5))
    with c3:
        high = st.slider("High / Critical boundary (%)", medium + 5, 95, max(t["high"], medium + 5))
    thresholds = {"low": low, "medium": medium, "high": high}
    st.session_state["risk_thresholds"] = thresholds

    display_cols = [c for c in DISPLAY_COLS if c in df.columns]
    risk_table = build_risk_table(
        df, feature_cols, preprocessor, model, st.session_state.get("id_col"),
        thresholds, display_cols=display_cols,
    )

    st.divider()
    st.subheader("Risk Distribution")
    summary = risk_distribution_summary(risk_table)
    cols = st.columns(5)
    cols[0].metric("Total Customers", summary["total"])
    for i, band in enumerate(RISK_ORDER):
        cols[i + 1].metric(band, summary["counts"].get(band, 0), f"{summary['percentages'].get(band, 0)}%")

    fig = px.bar(
        x=RISK_ORDER, y=[summary["counts"].get(b, 0) for b in RISK_ORDER],
        color=RISK_ORDER, color_discrete_map=RISK_COLORS,
        labels={"x": "Risk Category", "y": "Number of Customers"}, title="Customer Count by Risk Category",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("At-Risk Customer Table")
    f1, f2 = st.columns([1, 2])
    with f1:
        risk_filter = st.multiselect("Filter by risk category", RISK_ORDER, default=RISK_ORDER)
    with f2:
        search_id = st.text_input("Search by Customer ID (contains)")

    view = risk_table[risk_table["risk_category"].isin(risk_filter)]
    if search_id:
        view = view[view["customerID"].astype(str).str.contains(search_id, case=False, na=False)]

    st.caption(f"Showing {len(view)} of {len(risk_table)} customers, sorted by churn probability.")
    st.dataframe(view, use_container_width=True, height=450)

    st.download_button(
        "⬇️ Download risk table as CSV", view.to_csv(index=False).encode("utf-8"),
        file_name="customer_risk_table.csv", mime="text/csv",
    )
