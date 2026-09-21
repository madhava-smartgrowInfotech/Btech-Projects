"""Analytics page with filters, summary metrics, spending trends, and ML spending predictions."""
from __future__ import annotations

from datetime import date, timedelta
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from services.analytics_service import (
    analytics_overview, spending_by_category, monthly_trend, transactions_dataframe,
)
from services.budget_service import get_budget_status
from ml.spending_prediction import predict_next_month_expense, predict_category_spending, check_budget_overrun_risk
from utils.helpers import format_currency, current_month_year


def render(user):
    st.title("📊 Analytics")

    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("From", value=date.today() - timedelta(days=90))
    with col2:
        end_date = st.date_input("To", value=date.today())
    with col3:
        txn_type_filter = st.selectbox("Type", ["All", "income", "expense"])

    overview = analytics_overview(user.id, start_date, end_date)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", format_currency(overview["total_income"]))
    c2.metric("Total Expenses", format_currency(overview["total_expenses"]))
    c3.metric("Savings Rate", f"{overview['savings_rate']:.1f}%")

    c4, c5 = st.columns(2)
    c4.metric("Avg Daily Spending", format_currency(overview["avg_daily_spending"]))
    if overview["largest_expense"]:
        c5.metric("Largest Expense", format_currency(overview["largest_expense"]["amount"]),
                   delta=overview["largest_expense"]["description"])
    if overview["top_category"]:
        st.caption(f"Top spending category in this period: **{overview['top_category']}**")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        by_cat = spending_by_category(user.id, start_date, end_date)
        if not by_cat.empty:
            fig = px.bar(by_cat, x="category", y="amount", title="Category Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data in this range.")
    with col2:
        df = transactions_dataframe(user.id, start_date, end_date)
        if not df.empty:
            fig = px.pie(df, names="transaction_type", values="amount", title="Income vs Expenses")
            st.plotly_chart(fig, use_container_width=True)

    trend = monthly_trend(user.id)
    if not trend.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["month"], y=trend["expense"], name="Expenses", fill="tozeroy"))
        fig.update_layout(title="Spending Trend", height=320)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🔮 Spending Prediction (ML)")
    df_all = transactions_dataframe(user.id)
    result = predict_next_month_expense(df_all)
    if not result["available"]:
        st.info(result["message"])
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Predicted Next-Month Expense", format_currency(result["predicted_next_month_expense"]))
        c2.metric("Recent 3-Month Average", format_currency(result["recent_average"]))
        c3.metric("Trend", result["trend"].capitalize())

        cat_result = predict_category_spending(df_all)
        if cat_result["available"]:
            month, year = current_month_year()
            budgets = get_budget_status(user.id, month, year)
            risks = check_budget_overrun_risk(cat_result["predictions"], budgets)
            if risks:
                st.warning("Predicted potential budget overruns next month:")
                for r in risks:
                    st.write(f"- **{r['category']}**: predicted {format_currency(r['predicted_spend'])} "
                              f"vs budget {format_currency(r['budget'])} "
                              f"(over by {format_currency(r['overrun_amount'])})")
            else:
                st.success("No predicted budget overruns based on current trends.")
        else:
            st.caption(cat_result["message"])
