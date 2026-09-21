"""Main dashboard: KPI cards, charts, budget alerts, financial health gauge."""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from services.analytics_service import summary_metrics, spending_by_category, monthly_trend
from services.budget_service import get_budget_status, check_and_raise_alerts
from services.investment_service import portfolio_summary
from services.goal_service import get_goals
from ml.financial_health import calculate_financial_health
from utils.helpers import format_currency, current_month_year, month_name


def render(user):
    st.title("🏠 Dashboard")
    st.caption("Your AI-Powered Personal Finance Assistant")

    month, year = current_month_year()
    metrics = summary_metrics(user.id, month, year, user.monthly_income)
    budget_status = get_budget_status(user.id, month, year)
    port = portfolio_summary(user.id)
    goals = get_goals(user.id)

    # Raise/refresh budget alerts as notifications (idempotent — dedupes internally)
    check_and_raise_alerts(user.id, month, year)

    st.subheader(f"Overview — {month_name(month)} {year}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Balance", format_currency(metrics["total_balance"]))
    c2.metric("Monthly Income", format_currency(metrics["monthly_income"]))
    c3.metric("Monthly Expenses", format_currency(metrics["monthly_expenses"]))
    c4.metric("Total Savings", format_currency(metrics["monthly_savings"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Savings Rate", f"{metrics['savings_rate']:.1f}%")
    c6.metric("Investment Value", format_currency(metrics["investment_value"]))
    c7.metric("Net Worth", format_currency(metrics["net_worth"]))
    budget_used_avg = (sum(b["percent_used"] for b in budget_status) / len(budget_status)) if budget_status else 0
    c8.metric("Avg. Budget Usage", f"{budget_used_avg:.0f}%")

    # Financial health score
    health = calculate_financial_health(
        monthly_income=metrics["monthly_income"], monthly_expenses=metrics["monthly_expenses"],
        savings_rate=metrics["savings_rate"], total_balance=metrics["total_balance"],
        budget_status=budget_status, holdings=port["holdings"], goals=goals,
    )
    st.subheader("Financial Health Score")
    gauge_col, exp_col = st.columns([1, 2])
    with gauge_col:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=health["score"],
            gauge={"axis": {"range": [0, 100]},
                   "bar": {"color": "#1f77b4"},
                   "steps": [
                       {"range": [0, 40], "color": "#f8d7da"},
                       {"range": [40, 60], "color": "#fff3cd"},
                       {"range": [60, 75], "color": "#d1ecf1"},
                       {"range": [75, 90], "color": "#d4edda"},
                       {"range": [90, 100], "color": "#c3e6cb"},
                   ]},
        ))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with exp_col:
        st.markdown(f"**Rating: {health['rating']}**")
        st.write(health["explanation"])
        st.caption(f"Area to focus on: {health['weakest_area'].replace('_', ' ').title()} — "
                   f"{health['weakest_area_reason']}.")

    # Budget alerts
    alerts = [b for b in budget_status if b["percent_used"] >= 75]
    if alerts:
        st.subheader("⚠️ Budget Alerts")
        for b in alerts:
            if b["percent_used"] >= 100:
                st.error(f"{b['category']}: exceeded budget ({b['percent_used']:.0f}% used).")
            elif b["percent_used"] >= 90:
                st.warning(f"{b['category']}: {b['percent_used']:.0f}% of budget used.")
            else:
                st.info(f"{b['category']}: {b['percent_used']:.0f}% of budget used.")

    st.divider()
    st.subheader("Charts")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(data=[go.Bar(name="Income", x=["This Month"], y=[metrics["monthly_income"]]),
                               go.Bar(name="Expenses", x=["This Month"], y=[metrics["monthly_expenses"]])])
        fig.update_layout(title="Income vs Expenses", barmode="group", height=320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        by_cat = spending_by_category(user.id)
        if not by_cat.empty:
            fig = px.pie(by_cat, names="category", values="amount", title="Spending by Category")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add transactions to see category breakdown.")

    col3, col4 = st.columns(2)
    with col3:
        trend = monthly_trend(user.id)
        if not trend.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend["month"], y=trend["income"], name="Income", mode="lines+markers"))
            fig.add_trace(go.Scatter(x=trend["month"], y=trend["expense"], name="Expenses", mode="lines+markers"))
            fig.update_layout(title="Monthly Spending Trend", height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add more transactions across months to see spending trends.")

    with col4:
        if port["holdings"]:
            fig = px.pie(
                names=[h["asset_name"] for h in port["holdings"]],
                values=[h["current_value"] for h in port["holdings"]],
                title="Investment Allocation",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add investments to see portfolio allocation.")

    col5, col6 = st.columns(2)
    with col5:
        if budget_status:
            fig = go.Figure(data=[
                go.Bar(name="Budget", x=[b["category"] for b in budget_status], y=[b["budget_amount"] for b in budget_status]),
                go.Bar(name="Actual", x=[b["category"] for b in budget_status], y=[b["actual_spent"] for b in budget_status]),
            ])
            fig.update_layout(title="Budget vs Actual Spending", barmode="group", height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Set up budgets to see this chart.")

    with col6:
        if goals:
            fig = go.Figure(data=[go.Bar(x=[g["goal_name"] for g in goals], y=[g["percent_complete"] for g in goals])])
            fig.update_layout(title="Savings Goals Progress (%)", height=320, yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add goals to track savings progress.")
