"""KnowledgeX AI - Student Dashboard"""
import streamlit as st

from database.models import StudentProfile, LearningRoadmap, Purchase, Resource, MentorshipSession, MentorRequest
from ai.learning_engine import get_topic_overview
from services.gamification_service import get_user_points, get_user_badges, get_leaderboard
from services.marketplace_service import get_seller_dashboard
from services.mentorship_service import get_sessions_for_student


def render(session, user):
    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()
    if not sp:
        st.error("Student profile not found.")
        return

    st.title(f"👋 Welcome back, {user.name.split()[0]}!")
    st.caption(f"{sp.branch or 'Branch not set'} • {sp.year or 'Year not set'} • Goal: **{sp.career_goal or 'Not set'}**")

    points = get_user_points(session, user.id)
    overview = get_topic_overview(session, sp.id)
    seller = get_seller_dashboard(session, user.id)
    purchases_count = session.query(Purchase).filter_by(buyer_id=user.id).count()
    sessions = get_sessions_for_student(session, sp.id)
    upcoming_sessions = [s for s in sessions if s.status == "scheduled"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("⚡ XP", points.xp, delta=f"Level: {points.level}")
    c2.metric("🔥 Streak", f"{points.streak_days} days")
    c3.metric("📚 Topics Completed", overview["counts"]["completed"])
    c4.metric("💰 Wallet", f"₹{sp.wallet_balance:.0f}")
    c5.metric("🤝 Active Mentors", len({s.request_id for s in upcoming_sessions}))

    st.divider()
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 Learning Snapshot")
        counts = overview["counts"]
        st.progress(counts["completed"] / max(counts["total"], 1),
                    text=f"{counts['completed']} / {counts['total']} topics completed")
        cc1, cc2, cc3, cc4 = st.columns(4)
        cc1.metric("✅ Completed", counts["completed"])
        cc2.metric("💪 Strong", counts["strong"])
        cc3.metric("⚠️ Weak", counts["weak"])
        cc4.metric("🔒 Locked", counts["locked"])

        st.subheader("🗺️ Latest Roadmap")
        latest = session.query(LearningRoadmap).filter_by(student_id=sp.id).order_by(
            LearningRoadmap.generated_at.desc()).first()
        if latest:
            import json
            steps = json.loads(latest.roadmap_json)[:5]
            for step in steps:
                st.markdown(f"**{step['step']}. {step['name']}** — {step['priority']} priority, "
                            f"{step['completion_percent']:.0f}% complete")
            st.caption("Visit **Learning** for the full personalized roadmap.")
        else:
            st.info("No roadmap generated yet. Head to the **Learning** page to generate one.")

    with col_right:
        st.subheader("🏆 Badges")
        badges = get_user_badges(session, user.id)
        if badges:
            for b in badges[:5]:
                st.markdown(f"🎖️ **{b.badge_name}**")
        else:
            st.caption("No badges yet — complete activities to earn some!")

        st.subheader("🛍️ Marketplace")
        st.markdown(f"Uploads: **{len(seller['resources'])}**  \n"
                    f"Purchases: **{purchases_count}**  \n"
                    f"Earnings: **₹{seller['total_earnings']:.0f}**")

        st.subheader("🥇 Leaderboard (Top 5)")
        for i, row in enumerate(get_leaderboard(session, limit=5), start=1):
            st.markdown(f"{i}. **{row['name']}** — {row['xp']} XP ({row['level']})")
