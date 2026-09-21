"""Financial goals page."""
from __future__ import annotations

from datetime import date, timedelta
import streamlit as st

from services.goal_service import add_goal, update_goal_progress, delete_goal, get_goals
from utils.helpers import format_currency


def render(user):
    st.title("🎯 Financial Goals")

    with st.expander("➕ Add a New Goal"):
        with st.form("goal_form", clear_on_submit=True):
            goal_name = st.selectbox("Goal", ["New Laptop", "Education", "Emergency Fund", "Vacation",
                                               "Car", "House", "Other"])
            custom_name = ""
            if goal_name == "Other":
                custom_name = st.text_input("Goal name")
            target_amount = st.number_input("Target Amount", min_value=0.0, step=1000.0)
            current_amount = st.number_input("Current Savings Toward Goal", min_value=0.0, step=500.0)
            target_date = st.date_input("Target Date", value=date.today() + timedelta(days=180))
            submitted = st.form_submit_button("Add Goal")

        if submitted:
            name = custom_name.strip() if goal_name == "Other" else goal_name
            if not name:
                st.error("Please provide a goal name.")
            elif target_amount <= 0:
                st.error("Target amount must be greater than zero.")
            else:
                add_goal(user.id, name, target_amount, current_amount, target_date)
                st.success(f"Goal '{name}' created.")
                st.rerun()

    st.divider()
    goals = get_goals(user.id)
    if not goals:
        st.info("No goals yet — add one above to start tracking progress.")
        return

    for g in goals:
        st.subheader(g["goal_name"])
        st.progress(min(1.0, g["percent_complete"] / 100))
        c1, c2, c3 = st.columns(3)
        c1.metric("Progress", f"{g['percent_complete']:.0f}%")
        c2.metric("Saved", format_currency(g["current_amount"]))
        c3.metric("Target", format_currency(g["target_amount"]))
        st.caption(f"Target date: {g['target_date']} · Suggested monthly savings: "
                   f"{format_currency(g['required_monthly_savings'])} · Status: {g['status']}")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_amount = st.number_input("Update saved amount", min_value=0.0,
                                          value=float(g["current_amount"]), key=f"upd_{g['id']}")
        with col2:
            if st.button("Update", key=f"upd_btn_{g['id']}"):
                update_goal_progress(user.id, g["id"], new_amount)
                st.rerun()
        with col3:
            if st.button("Delete", key=f"del_goal_{g['id']}"):
                delete_goal(user.id, g["id"])
                st.rerun()
        st.divider()
