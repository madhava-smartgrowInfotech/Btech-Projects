"""User profile management page."""
from __future__ import annotations

import streamlit as st

from database.database import get_session
from database.models import User
from utils.validators import is_valid_email
from utils.demo_data import load_demo_data


def render(user):
    st.title("👤 Profile")

    with st.form("profile_form"):
        name = st.text_input("Name", value=user.name)
        email = st.text_input("Email", value=user.email)
        monthly_income = st.number_input("Monthly Income", min_value=0.0, value=float(user.monthly_income or 0), step=500.0)
        currency = st.selectbox("Preferred Currency", ["INR", "USD", "EUR", "GBP"],
                                 index=["INR", "USD", "EUR", "GBP"].index(user.currency) if user.currency in ["INR", "USD", "EUR", "GBP"] else 0)
        risk_profile = st.selectbox("Risk Preference", ["Conservative", "Moderate", "Aggressive"],
                                     index=["Conservative", "Moderate", "Aggressive"].index(user.risk_profile) if user.risk_profile in ["Conservative", "Moderate", "Aggressive"] else 1)
        savings_target = st.number_input("Savings Target", min_value=0.0, value=float(user.savings_target or 0), step=500.0)
        submitted = st.form_submit_button("Save Changes")

    if submitted:
        if not is_valid_email(email):
            st.error("Please enter a valid email address.")
        else:
            with get_session() as session:
                db_user = session.query(User).filter(User.id == user.id).first()
                db_user.name = name.strip()
                db_user.email = email.strip().lower()
                db_user.monthly_income = monthly_income
                db_user.currency = currency
                db_user.risk_profile = risk_profile
                db_user.savings_target = savings_target
            st.success("Profile updated.")
            st.session_state.pop("current_user_cache", None)
            st.rerun()

    st.divider()
    st.subheader("Demo Data")
    st.write("Load fictional sample transactions, budgets, goals, and investments to explore FINJARVIS immediately.")
    if st.button("Load Demo Data"):
        load_demo_data(user.id)
        st.success("Demo data loaded! Visit the Dashboard to see it.")
        st.rerun()
