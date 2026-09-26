"""KnowledgeX AI - Progress & Analytics"""
import streamlit as st
import plotly.express as px

from database.models import StudentProfile
from services.analytics_service import (
    student_skill_dataframe, learning_completion_dataframe, interview_performance_dataframe,
    coding_performance_dataframe, marketplace_earnings_dataframe,
)
from ai.learning_engine import get_topic_overview


def render(session, user):
    st.title("📈 Progress & Analytics")
    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()

    overview = get_topic_overview(session, sp.id)
    counts = overview["counts"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Completed", counts["completed"])
    c2.metric("Strong", counts["strong"])
    c3.metric("Weak", counts["weak"])
    c4.metric("Recommended", counts["recommended"])
    c5.metric("Locked", counts["locked"])

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 Skill Proficiency")
        skills_df = student_skill_dataframe(session, sp.id)
        if not skills_df.empty:
            fig = px.bar(skills_df.sort_values("Proficiency"), x="Proficiency", y="Skill",
                        orientation="h", title="Skill Progress")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skill data yet.")

    with col2:
        st.subheader("📚 Learning Completion")
        progress_df = learning_completion_dataframe(session, sp.id)
        if not progress_df.empty:
            fig = px.bar(progress_df.sort_values("Completion"), x="Completion", y="Topic",
                        orientation="h", color="Status", title="Topic Completion")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No progress data yet.")

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🎤 Interview Performance")
        interview_df = interview_performance_dataframe(session, sp.id)
        if not interview_df.empty:
            fig = px.line(interview_df, x="Date", y="Overall", markers=True, title="Interview Score Trend")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No mock interviews yet.")

    with col4:
        st.subheader("💻 Coding Performance")
        coding_df = coding_performance_dataframe(session, sp.id)
        if not coding_df.empty:
            pass_rate = coding_df["Passed"].mean() * 100
            fig = px.pie(names=["Passed", "Not Passed"],
                        values=[coding_df["Passed"].sum(), (~coding_df["Passed"]).sum()],
                        title=f"Coding Submissions (Pass rate: {pass_rate:.0f}%)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No coding submissions yet.")

    st.subheader("💰 Marketplace Earnings")
    earnings_df = marketplace_earnings_dataframe(session, user.id)
    if not earnings_df.empty:
        fig = px.bar(earnings_df, x="Date", y="Earnings", title="Marketplace Earnings Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sales yet. Upload resources in the Marketplace to start earning.")
