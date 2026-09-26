"""
KnowledgeX AI — Learn. Earn. Connect. Grow.
==============================================
AI-Driven Learning and Earning Ecosystem for Knowledge Engineers.
Main Streamlit entry point: handles session/auth state and role-based
navigation, then dispatches to the relevant page module.

Run with:  streamlit run app.py
"""
import streamlit as st

from database.database import init_db, get_session
from database.seed import seed_all
from database.models import User

from pages import (
    login, dashboard, learning, knowledge_graph, marketplace, mentorship,
    career, mock_interview, coding, profile, admin, research, mentor_panel, progress,
)

st.set_page_config(page_title="KnowledgeX AI", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def bootstrap_database():
    init_db()
    seed_all()
    return True


def get_db_session():
    if "db_session" not in st.session_state:
        st.session_state.db_session = get_session()
    return st.session_state.db_session


STUDENT_NAV = {
    "🏠 Dashboard": dashboard,
    "📚 Learning": learning,
    "🕸️ Knowledge Graph": knowledge_graph,
    "🎯 Career AI": career,
    "🛍️ Marketplace": marketplace,
    "🤝 Mentors": mentorship,
    "🎤 Mock Interview": mock_interview,
    "💻 Coding Practice": coding,
    "📈 Progress": progress,
    "🔬 Research & Innovation": research,
    "👤 Profile": profile,
}

MENTOR_NAV = {
    "🧑‍🏫 Mentor Panel": mentor_panel,
    "🛍️ Marketplace": marketplace,
    "🔬 Research & Innovation": research,
    "👤 Profile": profile,
}

ADMIN_NAV = {
    "🛡️ Admin Panel": admin,
    "🔬 Research & Innovation": research,
}


def main():
    bootstrap_database()
    session = get_db_session()

    if "user_id" not in st.session_state:
        login.render(session)
        return

    user = session.query(User).get(st.session_state.user_id)
    if user is None or not user.is_active:
        st.session_state.clear()
        st.warning("Session ended. Please log in again.")
        st.rerun()
        return

    nav_map = STUDENT_NAV if user.role == "student" else (MENTOR_NAV if user.role == "mentor" else ADMIN_NAV)

    with st.sidebar:
        st.markdown("## 🧠 KnowledgeX AI")
        st.caption("Learn. Earn. Connect. Grow.")
        st.markdown(f"**{user.name}**")
        st.caption(f"{user.role.capitalize()} • {user.email}")
        st.divider()

        selected_page = st.radio("Navigate", list(nav_map.keys()), label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            session.close()
            st.session_state.clear()
            st.rerun()

    try:
        nav_map[selected_page].render(session, user)
        session.commit()
    except Exception as e:  # noqa: BLE001
        session.rollback()
        st.error(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
