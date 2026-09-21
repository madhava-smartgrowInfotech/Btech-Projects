"""
FINJARVIS — Your AI-Powered Personal Finance Assistant
Entry point. Run with: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # loads .env if present; safe no-op otherwise

from database.database import init_db, get_session
from database.models import User
from auth.authentication import signup, login

from ui import dashboard, transactions, budgets, goals, investments, analytics, ai_assistant, reports, notifications, profile

st.set_page_config(page_title="FINJARVIS", page_icon="\U0001F4B0", layout="wide")

init_db()


def _get_current_user():
    """Fetch a detached copy of the logged-in user's row for this render pass."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        # Expunge so attribute access still works after the session closes
        session.expunge(user)
        return user


def _render_auth_screen():
    st.markdown(
        "<h1 style='text-align:center;'>\U0001F4B0 FINJARVIS</h1>"
        "<p style='text-align:center;color:gray;'>Your AI-Powered Personal Finance Assistant</p>",
        unsafe_allow_html=True,
    )
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                identifier = st.text_input("Username or Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log In", use_container_width=True)
            if submitted:
                result = login(identifier, password)
                if result.success:
                    st.session_state.user_id = result.user_id
                    st.rerun()
                else:
                    st.error(result.message)

        with tab_signup:
            with st.form("signup_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                result = signup(name, email, username, password, confirm_password)
                if result.success:
                    st.success(result.message)
                else:
                    st.error(result.message)


PAGES = {
    "\U0001F3E0 Dashboard": dashboard,
    "\U0001F4B3 Transactions": transactions,
    "\U0001F4CA Analytics": analytics,
    "\U0001F4B0 Budgets": budgets,
    "\U0001F3AF Goals": goals,
    "\U0001F4C8 Investments": investments,
    "\U0001F916 AI Assistant": ai_assistant,
    "\U0001F4C4 Reports": reports,
    "\U0001F514 Notifications": notifications,
    "\U0001F464 Profile": profile,
}


def _render_app(user):
    with st.sidebar:
        st.markdown("## \U0001F4B0 FINJARVIS")
        st.caption(f"Welcome, {user.name.split(' ')[0]}")
        choice = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
        st.divider()
        if st.button("\U0001F6AA Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    try:
        PAGES[choice].render(user)
    except Exception as e:
        st.error(f"Something went wrong loading this page: {e}")
        st.caption("Try navigating to a different page or refreshing.")


def main():
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    user = _get_current_user() if st.session_state.user_id else None

    if not user:
        _render_auth_screen()
    else:
        _render_app(user)


if __name__ == "__main__":
    main()
