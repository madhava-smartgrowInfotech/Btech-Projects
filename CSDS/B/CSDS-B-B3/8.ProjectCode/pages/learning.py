"""KnowledgeX AI - Learning: Assessments + Personalized Roadmap"""
import streamlit as st

from database.models import (
    StudentProfile, Assessment, AssessmentQuestion, AssessmentResult,
    StudentSkill, Skill, LearningTopic
)
from ai.learning_engine import analyze_and_generate_roadmap, update_topic_progress
from services.gamification_service import award_xp, grant_badge


def render(session, user):
    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()
    st.title("📚 Learning Center")

    tab_assess, tab_roadmap, tab_progress = st.tabs(
        ["🧪 Skill Assessment", "🗺️ AI Roadmap", "✅ Mark Progress"])

    # ---------------- Assessment ----------------
    with tab_assess:
        st.subheader("Take a Skill Assessment")
        assessments = session.query(Assessment).all()
        topic_names = [a.topic for a in assessments]
        chosen_topic = st.selectbox("Choose a topic to assess", topic_names)
        assessment = next(a for a in assessments if a.topic == chosen_topic)
        questions = session.query(AssessmentQuestion).filter_by(assessment_id=assessment.id).all()

        with st.form(f"assessment_{assessment.id}"):
            answers = {}
            for i, q in enumerate(questions):
                answers[q.id] = st.radio(
                    f"**Q{i+1}. {q.question}**",
                    options=["A", "B", "C", "D"],
                    format_func=lambda opt, q=q: f"{opt}. " + {
                        "A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}[opt],
                    key=f"q_{q.id}", index=None,
                )
            submit = st.form_submit_button("Submit Assessment", type="primary")

        if submit:
            unanswered = [qid for qid, ans in answers.items() if ans is None]
            if unanswered:
                st.warning("Please answer all questions before submitting.")
            else:
                correct = sum(1 for q in questions if answers[q.id] == q.correct_option)
                score = round((correct / len(questions)) * 100, 1)
                session.add(AssessmentResult(student_id=sp.id, assessment_id=assessment.id,
                                              topic=chosen_topic, score_percent=score))

                skill = session.query(Skill).filter_by(name=chosen_topic).first()
                if skill:
                    ss = session.query(StudentSkill).filter_by(student_id=sp.id, skill_id=skill.id).first()
                    if not ss:
                        ss = StudentSkill(student_id=sp.id, skill_id=skill.id, proficiency=score)
                        session.add(ss)
                    else:
                        ss.proficiency = round((ss.proficiency + score) / 2, 1)  # blended update

                topic = session.query(LearningTopic).filter_by(name=chosen_topic).first()
                if topic:
                    update_topic_progress(session, sp.id, topic.id, score)

                award_xp(session, user.id, "assessment_completed")
                if score >= 80:
                    grant_badge(session, user.id, f"{chosen_topic} Master", f"Scored {score}% in {chosen_topic}")
                session.commit()

                st.success(f"You scored **{score}%** in {chosen_topic}! Your knowledge state has been updated.")
                st.balloons()

    # ---------------- Roadmap ----------------
    with tab_roadmap:
        st.subheader("AI-Generated Personalized Roadmap")
        st.caption("Adopts the base paper's graph-based knowledge-state tracking, extended with "
                    "career-goal-aware prioritization.")
        goal = st.text_input("Career goal for roadmap generation", value=sp.career_goal or "Machine Learning Engineer")

        if st.button("🔄 Generate / Refresh Roadmap", type="primary"):
            sp.career_goal = goal
            result = analyze_and_generate_roadmap(session, sp.id)
            session.commit()
            st.session_state["_last_roadmap"] = result
            st.success("Roadmap generated!")

        result = st.session_state.get("_last_roadmap")
        if result:
            if result["weak_prerequisites"]:
                st.warning("⚠️ Weak prerequisite topics detected: " +
                           ", ".join(f"{w['name']} ({w['proficiency']:.0f}%)" for w in result["weak_prerequisites"][:5]))

            for step in result["roadmap"]:
                with st.expander(f"**Step {step['step']}: {step['name']}** — {step['priority']} priority "
                                  f"({step['completion_percent']:.0f}% complete)"):
                    st.markdown(f"**Difficulty:** {step['difficulty']}  \n"
                                f"**Estimated time:** {step['estimated_hours']:.0f} hours  \n"
                                f"**Prerequisites:** {', '.join(step['prerequisites']) or 'None'}  \n"
                                f"**Why recommended:** {step['explanation']}")
                    st.markdown("**Recommended resources:**")
                    for r in step["recommended_resources"]:
                        st.markdown(f"- {r}")
        else:
            st.info("Generate a roadmap to see your personalized learning path here.")

    # ---------------- Manual progress update ----------------
    with tab_progress:
        st.subheader("Mark Topic Progress")
        topics = session.query(LearningTopic).all()
        topic_choice = st.selectbox("Topic", [t.name for t in topics])
        pct = st.slider("Completion %", 0, 100, 50)
        if st.button("Update Progress"):
            topic = next(t for t in topics if t.name == topic_choice)
            update_topic_progress(session, sp.id, topic.id, pct)
            if pct >= 85:
                award_xp(session, user.id, "topic_completed")
                grant_badge(session, user.id, f"{topic_choice} Completed")
            session.commit()
            st.success(f"Updated {topic_choice} to {pct}% completion.")
            st.rerun()
