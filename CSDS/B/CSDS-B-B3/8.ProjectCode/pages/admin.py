"""KnowledgeX AI - Admin Panel"""
import streamlit as st
import plotly.express as px

from database.models import User, MentorProfile, Resource, Report, StudentProfile
from services.analytics_service import platform_overview


def render(session, user):
    st.title("🛡️ Admin Panel")

    tabs = st.tabs(["📊 Overview", "👥 Manage Users", "🧑‍🏫 Verify Mentors",
                    "📦 Moderate Resources", "🚩 Reports"])

    with tabs[0]:
        overview = platform_overview(session)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎓 Students", overview["total_students"])
        c2.metric("🧑‍🏫 Mentors", overview["total_mentors"])
        c3.metric("📦 Resources", overview["total_resources"])
        c4.metric("💰 Marketplace Volume", f"₹{overview['gross_marketplace_volume']:.0f}")

        c5, c6, c7 = st.columns(3)
        c5.metric("🛒 Purchases", overview["total_purchases"])
        c6.metric("🎤 Mock Interviews", overview["total_interviews"])
        c7.metric("💻 Code Submissions", overview["total_submissions"])

        fig = px.bar(
            x=["Students", "Mentors", "Resources", "Purchases", "Sessions", "Interviews", "Submissions"],
            y=[overview["total_students"], overview["total_mentors"], overview["total_resources"],
               overview["total_purchases"], overview["total_sessions"], overview["total_interviews"],
               overview["total_submissions"]],
            title="Platform Activity Overview", labels={"x": "Metric", "y": "Count"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        users = session.query(User).all()
        for u in users:
            with st.container(border=True):
                cols = st.columns([3, 1, 1])
                cols[0].markdown(f"**{u.name}** ({u.email}) — {u.role.capitalize()}")
                status = "🟢 Active" if u.is_active else "🔴 Deactivated"
                cols[1].markdown(status)
                toggle_label = "Deactivate" if u.is_active else "Reactivate"
                if cols[2].button(toggle_label, key=f"toggle_{u.id}") and u.role != "admin":
                    u.is_active = not u.is_active
                    session.commit()
                    st.rerun()

    with tabs[2]:
        unverified = session.query(MentorProfile).filter_by(is_verified=False).all()
        if not unverified:
            st.info("No mentors pending verification.")
        for mp in unverified:
            mentor_user = session.query(User).get(mp.user_id)
            with st.container(border=True):
                st.markdown(f"**{mentor_user.name}** — {mp.domain}")
                st.caption(f"Expertise: {mp.expertise} • {mp.experience_years} yrs experience")
                if st.button("✅ Verify Mentor", key=f"verify_{mp.id}"):
                    mp.is_verified = True
                    session.commit()
                    st.success(f"{mentor_user.name} verified!")
                    st.rerun()

    with tabs[3]:
        resources = session.query(Resource).all()
        for r in resources:
            with st.container(border=True):
                cols = st.columns([3, 1, 1])
                cols[0].markdown(f"**{r.title}** — ₹{r.price:.0f} • {r.category}")
                flag = "🚩 Reported" if r.is_reported else ("✅ Approved" if r.is_approved else "⏳ Pending")
                cols[1].markdown(flag)
                if cols[2].button("Remove", key=f"remove_{r.id}"):
                    session.delete(r)
                    session.commit()
                    st.rerun()

    with tabs[4]:
        reports = session.query(Report).filter_by(status="open").all()
        if not reports:
            st.info("No open reports.")
        for rep in reports:
            with st.container(border=True):
                st.markdown(f"Report #{rep.id} — {rep.reason}")
                if st.button("Mark Resolved", key=f"resolve_{rep.id}"):
                    rep.status = "resolved"
                    session.commit()
                    st.rerun()
