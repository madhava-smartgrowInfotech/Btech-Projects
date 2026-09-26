"""KnowledgeX AI - Mentor Panel (for mentor role)"""
import streamlit as st

from database.models import MentorProfile, StudentProfile, User, MentorRequest
from services.mentorship_service import (
    get_requests_for_mentor, respond_to_request, get_sessions_for_mentor, submit_feedback,
)
from services.analytics_service import student_skill_dataframe, learning_completion_dataframe


def render(session, user):
    st.title("🧑‍🏫 Mentor Panel")
    mp = session.query(MentorProfile).filter_by(user_id=user.id).first()

    if not mp.is_verified:
        st.warning("⏳ Your mentor profile is pending admin verification. You can still configure your profile, "
                   "but students won't see you in recommendations until verified.")

    tabs = st.tabs(["📨 Requests", "📅 Sessions & Mentee Progress"])

    with tabs[0]:
        pending = get_requests_for_mentor(session, mp.id, status="pending")
        if not pending:
            st.info("No pending mentorship requests.")
        for r in pending:
            sp = session.query(StudentProfile).get(r.student_id)
            student_user = session.query(User).get(sp.user_id)
            with st.container(border=True):
                st.markdown(f"**{student_user.name}** ({sp.branch}, {sp.year}) — Goal: {sp.career_goal}")
                st.caption(r.message)
                c1, c2 = st.columns(2)
                if c1.button("✅ Accept", key=f"accept_{r.id}", use_container_width=True):
                    respond_to_request(session, r.id, accept=True)
                    session.commit()
                    st.success("Request accepted!")
                    st.rerun()
                if c2.button("❌ Reject", key=f"reject_{r.id}", use_container_width=True):
                    respond_to_request(session, r.id, accept=False)
                    session.commit()
                    st.info("Request rejected.")
                    st.rerun()

    with tabs[1]:
        sessions = get_sessions_for_mentor(session, mp.id)
        if not sessions:
            st.info("No mentorship sessions yet.")
        for s in sessions:
            req = session.query(MentorRequest).get(s.request_id)
            sp = session.query(StudentProfile).get(req.student_id)
            student_user = session.query(User).get(sp.user_id)
            with st.container(border=True):
                st.markdown(f"**{s.topic}** with {student_user.name} — {s.status.capitalize()}")

                skills_df = student_skill_dataframe(session, sp.id)
                progress_df = learning_completion_dataframe(session, sp.id)
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("Mentee skill snapshot")
                    if not skills_df.empty:
                        st.dataframe(skills_df, hide_index=True, use_container_width=True)
                with c2:
                    st.caption("Mentee topic progress")
                    if not progress_df.empty:
                        st.dataframe(progress_df, hide_index=True, use_container_width=True)

                feedback_text = st.text_area("Feedback for mentee", value=s.mentor_feedback or "",
                                             key=f"fb_{s.id}")
                if st.button("Save Feedback", key=f"savefb_{s.id}"):
                    submit_feedback(session, s.id, feedback_text=feedback_text)
                    session.commit()
                    st.success("Feedback saved and shared with the student.")
