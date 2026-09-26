"""KnowledgeX AI - Login & Registration Page"""
import streamlit as st

from services.authentication import authenticate_user, register_user
from services.gamification_service import award_xp, grant_badge
from database.models import StudentProfile, MentorProfile, UserPoints


def render(session):
    st.markdown(
        "<h1 style='text-align:center;'>🧠 KnowledgeX AI</h1>"
        "<p style='text-align:center; color:#6c757d;'>Learn. Earn. Connect. Grow.</p>",
        unsafe_allow_html=True,
    )

    tab_login, tab_register, tab_demo = st.tabs(["🔐 Login", "📝 Register", "🎬 Demo Accounts"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
        if submitted:
            user, error = authenticate_user(session, email, password)
            if error:
                st.error(error)
            else:
                st.session_state.user_id = user.id
                st.session_state.user_role = user.role
                st.success(f"Welcome back, {user.name}!")
                st.rerun()

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password", help="Minimum 6 characters")
            role = st.selectbox("I am a...", ["student", "mentor"], format_func=lambda x: x.capitalize())
            submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
        if submitted:
            user, error = register_user(session, name, email, password, role)
            if error:
                st.error(error)
            else:
                if role == "student":
                    session.add(StudentProfile(user_id=user.id, wallet_balance=500.0))
                else:
                    session.add(MentorProfile(user_id=user.id))
                session.add(UserPoints(user_id=user.id, xp=0, level="Newcomer"))
                session.commit()
                award_xp(session, user.id, "profile_completed")
                session.commit()
                st.success("Account created! Please log in from the Login tab.")
                if role == "mentor":
                    st.info("Your mentor profile will need admin verification before students can find you.")

    with tab_demo:
        st.markdown("Use these pre-seeded accounts to explore the platform instantly:")
        st.markdown("""
        | Role | Email | Password |
        |------|-------|----------|
        | 🎓 Student | `student@example.com` | `Demo@1234` |
        | 🧑‍🏫 Mentor | `mentor@example.com` | `Demo@1234` |
        | 🛡️ Admin | `admin@example.com` | `Demo@1234` |
        """)
        st.caption("⚠️ Change these credentials before any production deployment.")
