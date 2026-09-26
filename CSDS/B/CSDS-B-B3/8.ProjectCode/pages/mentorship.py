"""KnowledgeX AI - Peer Mentorship System"""
import streamlit as st

from database.models import StudentProfile, MentorProfile, User, MentorRequest
from ai.mentor_engine import recommend_mentors
from services.mentorship_service import (
    send_request, get_requests_for_student, get_sessions_for_student, submit_feedback,
)
from services.gamification_service import award_xp


def render(session, user):
    st.title("🤝 Peer Mentorship")
    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()

    tabs = st.tabs(["🔍 Find a Mentor", "📨 My Requests", "📅 My Sessions"])

    with tabs[0]:
        st.subheader("AI Mentor Recommendation")
        c1, c2, c3 = st.columns(3)
        required_skill = c1.text_input("Skill you need help with", value="Machine Learning")
        career_goal = c2.text_input("Career goal", value=sp.career_goal or "")
        domain = c3.text_input("Preferred domain", value="")

        if st.button("Find Matching Mentors", type="primary"):
            st.session_state["_mentor_matches"] = recommend_mentors(
                session, required_skill=required_skill, career_goal=career_goal, domain=domain)

        matches = st.session_state.get("_mentor_matches", [])
        if matches:
            for m in matches:
                with st.container(border=True):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**{m['name']}** — {m['domain']}")
                        st.caption(f"Expertise: {m['expertise']} • {m['experience_years']} yrs experience • "
                                  f"⭐ {m['rating']} ({m['rating_count']}) • {m['availability']}")
                        st.progress(min(m["match_score"] / 100, 1.0), text=f"Match score: {m['match_score']}%")
                    with cols[1]:
                        msg_key = f"msg_{m['mentor_id']}"
                        if st.button("Send Request", key=f"req_{m['mentor_id']}", use_container_width=True):
                            req, err = send_request(session, sp.id, m["mentor_id"],
                                                     f"Hi {m['name']}, I'd love your guidance on {required_skill}.")
                            if err:
                                st.error(err)
                            else:
                                session.commit()
                                st.success(f"Request sent to {m['name']}!")
        else:
            st.info("Click 'Find Matching Mentors' to get AI-recommended mentors.")

    with tabs[1]:
        requests = get_requests_for_student(session, sp.id)
        if not requests:
            st.info("You haven't sent any mentorship requests yet.")
        for r in requests:
            mp = session.query(MentorProfile).get(r.mentor_id)
            mentor_user = session.query(User).get(mp.user_id) if mp else None
            status_emoji = {"pending": "🟡", "accepted": "🟢", "rejected": "🔴"}[r.status]
            st.markdown(f"{status_emoji} **{mentor_user.name if mentor_user else 'Unknown'}** — "
                       f"{r.status.capitalize()} • {r.created_at.strftime('%Y-%m-%d')}")
            st.caption(r.message)

    with tabs[2]:
        sessions = get_sessions_for_student(session, sp.id)
        if not sessions:
            st.info("No mentorship sessions scheduled yet.")
        for s in sessions:
            req = session.query(MentorRequest).get(s.request_id)
            mp = session.query(MentorProfile).get(req.mentor_id)
            mentor_user = session.query(User).get(mp.user_id) if mp else None
            with st.container(border=True):
                st.markdown(f"**{s.topic}** with {mentor_user.name if mentor_user else 'Unknown'}")
                st.caption(f"Status: {s.status.capitalize()} • Scheduled: {s.scheduled_time}")
                if s.status == "scheduled":
                    rating = st.slider("Rate this session after completion", 1, 5, 5, key=f"rate_{s.id}")
                    if st.button("Mark Completed & Submit Rating", key=f"complete_{s.id}"):
                        submit_feedback(session, s.id, rating=rating)
                        award_xp(session, user.id, "mentorship_session_completed")
                        session.commit()
                        st.success("Session marked complete. Thank you for your feedback!")
                        st.rerun()
                elif s.status == "completed":
                    st.markdown(f"Your rating: {'⭐' * int(s.student_rating)}")
