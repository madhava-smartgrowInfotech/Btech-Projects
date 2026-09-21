"""Budget management page."""
from __future__ import annotations

import streamlit as st

from services.budget_service import set_budget, delete_budget, get_budget_status
from services.transaction_service import get_all_categories
from utils.helpers import format_currency, current_month_year, month_name


def render(user):
    st.title("💰 Budgets")

    month, year = current_month_year()
    col_m, col_y = st.columns(2)
    with col_m:
        month = st.selectbox("Month", list(range(1, 13)), index=month - 1, format_func=month_name)
    with col_y:
        year = st.number_input("Year", min_value=2020, max_value=2100, value=year, step=1)

    st.subheader("Set a Budget")
    with st.form("budget_form", clear_on_submit=True):
        categories = get_all_categories(user.id)
        category = st.selectbox("Category", categories)
        amount = st.number_input("Budget Amount", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("Save Budget")

    if submitted:
        try:
            set_budget(user.id, category, amount, month, year)
            st.success(f"Budget for {category} set to {format_currency(amount)}.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

    st.divider()
    st.subheader(f"Budget Status — {month_name(month)} {year}")
    statuses = get_budget_status(user.id, month, year)
    if not statuses:
        st.info("No budgets set for this month yet.")
        return

    for b in statuses:
        st.markdown(f"**{b['category']}** — {format_currency(b['actual_spent'])} of {format_currency(b['budget_amount'])} "
                     f"({b['percent_used']:.0f}% used)")
        progress = min(1.0, b["percent_used"] / 100)
        st.progress(progress)
        cols = st.columns([3, 1])
        with cols[0]:
            if b["percent_used"] >= 100:
                st.error(f"Exceeded by {format_currency(abs(b['remaining']))}.")
            elif b["percent_used"] >= 90:
                st.warning("90% of this budget is used.")
            elif b["percent_used"] >= 75:
                st.info("75% of this budget is used.")
            else:
                st.caption(f"{format_currency(b['remaining'])} remaining.")
        with cols[1]:
            if st.button("Delete", key=f"del_budget_{b['id']}"):
                delete_budget(user.id, b["id"])
                st.rerun()
