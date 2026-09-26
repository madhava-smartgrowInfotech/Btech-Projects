"""KnowledgeX AI - Profile Management"""
import streamlit as st

from database.models import StudentProfile, MentorProfile, Skill, StudentSkill, CareerRole
from services.gamification_service import award_xp, get_user_points, get_user_badges


def render(session, user):
    st.title("👤 My Profile")

    if user.role == "student":
        _render_student_profile(session, user)
    elif user.role == "mentor":
        _render_mentor_profile(session, user)
    else:
        st.info("Admin accounts don't have a learner/mentor profile.")


def _render_student_profile(session, user):
    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()
    careers = [c.title for c in session.query(CareerRole).all()]

    with st.form("student_profile_form"):
        c1, c2 = st.columns(2)
        branch = c1.text_input("Branch", value=sp.branch)
        year = c2.text_input("Year", value=sp.year)
        college = st.text_input("College", value=sp.college)
        bio = st.text_area("Bio", value=sp.bio)
        interests = st.text_input("Interests (comma separated)", value=sp.interests)
        goal_index = careers.index(sp.career_goal) if sp.career_goal in careers else 0
        career_goal = st.selectbox("Career Goal", careers, index=goal_index if careers else 0)
        submit = st.form_submit_button("Save Profile", type="primary")

    if submit:
        sp.branch, sp.year, sp.college, sp.bio = branch, year, college, bio
        sp.interests, sp.career_goal = interests, career_goal
        award_xp(session, user.id, "profile_completed")
        session.commit()
        st.success("Profile updated!")

    st.divider()
    st.subheader("🧠 My Skills")
    all_skills = session.query(Skill).all()
    my_skills = {ss.skill_id: ss for ss in session.query(StudentSkill).filter_by(student_id=sp.id).all()}

    with st.form("skills_form"):
        updates = {}
        for skill in all_skills:
            current = my_skills[skill.id].proficiency if skill.id in my_skills else 0
            updates[skill.id] = st.slider(skill.name, 0, 100, int(current), key=f"skill_{skill.id}")
        save_skills = st.form_submit_button("Save Skills")

    if save_skills:
        for skill_id, val in updates.items():
            if skill_id in my_skills:
                my_skills[skill_id].proficiency = val
            elif val > 0:
                session.add(StudentSkill(student_id=sp.id, skill_id=skill_id, proficiency=val))
        session.commit()
        st.success("Skills updated!")
        st.rerun()

    st.divider()
    points = get_user_points(session, user.id)
    badges = get_user_badges(session, user.id)
    st.subheader("🏅 Achievements")
    st.markdown(f"**Level:** {points.level} • **XP:** {points.xp} • **Streak:** {points.streak_days} days")
    if badges:
        st.markdown(" ".join(f"`🎖️ {b.badge_name}`" for b in badges))
    else:
        st.caption("No badges yet.")


def _render_mentor_profile(session, user):
    mp = session.query(MentorProfile).filter_by(user_id=user.id).first()
    with st.form("mentor_profile_form"):
        expertise = st.text_input("Expertise (comma separated)", value=mp.expertise)
        domain = st.text_input("Domain", value=mp.domain)
        experience = st.number_input("Years of Experience", min_value=0.0, max_value=50.0,
                                     value=float(mp.experience_years), step=0.5)
        bio = st.text_area("Bio", value=mp.bio)
        availability = st.text_input("Availability", value=mp.availability)
        submit = st.form_submit_button("Save Profile", type="primary")

    if submit:
        mp.expertise, mp.domain, mp.experience_years = expertise, domain, experience
        mp.bio, mp.availability = bio, availability
        session.commit()
        st.success("Mentor profile updated!")

    st.divider()
    verification_status = "✅ Verified" if mp.is_verified else "⏳ Pending Admin Verification"
    st.markdown(f"**Verification status:** {verification_status}")
    st.markdown(f"**Rating:** ⭐ {mp.rating} ({mp.rating_count} reviews)")
