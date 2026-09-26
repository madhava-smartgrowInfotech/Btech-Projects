"""KnowledgeX AI - AI Mock Interview Module"""
import streamlit as st

from database.models import StudentProfile, CareerRole, MockInterview, InterviewAnswer, InterviewFeedback
from ai.interview_engine import get_questions, score_answer_semantic, generate_feedback
from services.gamification_service import award_xp, grant_badge
from services.analytics_service import interview_performance_dataframe


def render(session, user):
    st.title("🎤 AI Mock Interview")
    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()

    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False

    if not st.session_state.interview_active:
        st.subheader("Configure Your Mock Interview")
        roles = [c.title for c in session.query(CareerRole).all()] + ["General"]
        c1, c2, c3 = st.columns(3)
        role = c1.selectbox("Job Role", roles, index=0)
        itype = c2.selectbox("Interview Type", ["Mixed", "Technical", "HR", "Behavioral", "Coding"])
        difficulty = c3.selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard"])
        num_q = st.slider("Number of questions", 3, 8, 5)

        if st.button("🚀 Start Interview", type="primary"):
            questions = get_questions(session, role, itype, difficulty, num_questions=num_q)
            st.session_state.interview_active = True
            st.session_state.interview_role = role
            st.session_state.interview_type = itype
            st.session_state.interview_difficulty = difficulty
            st.session_state.interview_questions = [
                {"id": q.id, "question": q.question, "keywords": q.keywords} for q in questions]
            st.session_state.interview_answers = {}
            st.rerun()

        st.divider()
        st.subheader("📊 Your Past Interview Performance")
        df = interview_performance_dataframe(session, sp.id)
        if not df.empty:
            import plotly.express as px
            fig = px.line(df, x="Date", y=["Overall", "Technical", "Communication", "Relevance"],
                          markers=True, title="Interview Performance Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No mock interviews taken yet.")
        return

    # ---------------- Active Interview ----------------
    st.subheader(f"{st.session_state.interview_role} — {st.session_state.interview_type} Interview")
    with st.form("interview_form"):
        for i, q in enumerate(st.session_state.interview_questions):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            st.session_state.interview_answers[q["id"]] = st.text_area(
                "Your answer", key=f"ans_{q['id']}", height=100, label_visibility="collapsed")
        submit = st.form_submit_button("Submit Interview & Get AI Feedback", type="primary")

    if submit:
        answers_with_scores = []
        for q in st.session_state.interview_questions:
            answer_text = st.session_state.interview_answers.get(q["id"], "")
            score = score_answer_semantic(answer_text, q["question"], q["keywords"])
            answers_with_scores.append({"question": q["question"], "answer": answer_text, "score": score,
                                        "question_id": q["id"]})

        feedback = generate_feedback(answers_with_scores, st.session_state.interview_role)

        interview = MockInterview(
            student_id=sp.id, role=st.session_state.interview_role,
            interview_type=st.session_state.interview_type, difficulty=st.session_state.interview_difficulty,
            overall_score=feedback["overall_score"], technical_score=feedback["technical_score"],
            communication_score=feedback["communication_score"], relevance_score=feedback["relevance_score"],
            confidence_score=feedback["confidence_score"],
        )
        session.add(interview)
        session.flush()

        for a in answers_with_scores:
            session.add(InterviewAnswer(interview_id=interview.id, question_id=a["question_id"],
                                        answer_text=a["answer"], score=a["score"]))

        session.add(InterviewFeedback(
            interview_id=interview.id, strengths=feedback["strengths"], weaknesses=feedback["weaknesses"],
            suggested_topics=feedback["suggested_topics"], summary=feedback["summary"],
        ))

        award_xp(session, user.id, "mock_interview_completed")
        if feedback["overall_score"] >= 80:
            grant_badge(session, user.id, "Interview Ace", "Scored 80+ in a mock interview")
        session.commit()

        st.session_state.interview_active = False
        st.session_state["_last_feedback"] = feedback
        st.session_state["_last_answers"] = answers_with_scores
        st.rerun()

    if st.button("❌ Cancel Interview"):
        st.session_state.interview_active = False
        st.rerun()

    # Show last feedback if available (after rerun following submit)
    if not st.session_state.interview_active and st.session_state.get("_last_feedback"):
        fb = st.session_state.pop("_last_feedback")
        answers = st.session_state.pop("_last_answers")
        st.success("Interview Complete! Here's your AI-generated report:")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Overall", f"{fb['overall_score']:.0f}")
        c2.metric("Technical", f"{fb['technical_score']:.0f}")
        c3.metric("Communication", f"{fb['communication_score']:.0f}")
        c4.metric("Relevance", f"{fb['relevance_score']:.0f}")
        c5.metric("Confidence", f"{fb['confidence_score']:.0f}")
        st.markdown(f"**Summary:** {fb['summary']}")
        st.markdown(f"**💪 Strengths:** {fb['strengths']}")
        st.markdown(f"**⚠️ Weaknesses:** {fb['weaknesses']}")
        st.markdown(f"**📚 Suggested topics to revise:** {fb['suggested_topics']}")
        with st.expander("View your answers and per-question scores"):
            for a in answers:
                st.markdown(f"**{a['question']}** — Score: {a['score']:.0f}/100")
                st.caption(a["answer"] or "_No answer provided_")
