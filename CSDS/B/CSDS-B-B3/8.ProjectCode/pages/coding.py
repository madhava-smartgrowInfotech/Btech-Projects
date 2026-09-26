"""KnowledgeX AI - Coding Practice"""
import json
import streamlit as st

from database.models import StudentProfile, CodingProblem, CodingSubmission
from services.code_executor import run_submission
from services.gamification_service import award_xp, grant_badge
from services.analytics_service import coding_performance_dataframe


def render(session, user):
    st.title("💻 Coding Practice")
    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()

    tab_practice, tab_stats = st.tabs(["🧩 Practice", "📈 My Stats"])

    with tab_practice:
        problems = session.query(CodingProblem).all()
        difficulty_filter = st.selectbox("Filter by difficulty", ["All", "Easy", "Medium", "Hard"])
        filtered = [p for p in problems if difficulty_filter == "All" or p.difficulty == difficulty_filter]

        titles = [f"{p.title} ({p.difficulty})" for p in filtered]
        if not titles:
            st.info("No problems match this filter.")
            return
        choice = st.selectbox("Choose a problem", titles)
        problem = filtered[titles.index(choice)]

        st.markdown(f"### {problem.title}")
        st.markdown(f"**Difficulty:** {problem.difficulty} • **Concept:** {problem.concept_tag}")
        st.markdown(problem.description)

        code_key = f"code_{problem.id}"
        if code_key not in st.session_state:
            st.session_state[code_key] = problem.starter_code

        code = st.text_area("Your Python solution", value=st.session_state[code_key], height=250, key=f"editor_{problem.id}")

        if st.button("▶️ Run & Submit", type="primary", key=f"run_{problem.id}"):
            test_cases = json.loads(problem.test_cases)
            result = run_submission(code, problem.function_name, test_cases)

            submission = CodingSubmission(
                student_id=sp.id, problem_id=problem.id, code=code,
                passed=result["passed"], tests_passed=result["tests_passed"], tests_total=result["tests_total"],
            )
            session.add(submission)

            if result["error"]:
                st.error(f"Execution error: {result['error']}")
            else:
                st.markdown(f"**Result: {result['tests_passed']} / {result['tests_total']} test cases passed**")
                for i, d in enumerate(result["details"], start=1):
                    icon = "✅" if d["passed"] else "❌"
                    st.markdown(f"{icon} Test {i}: input=`{d['input']}` expected=`{d['expected']}` "
                              f"got=`{d['actual']}`")
                if result["passed"]:
                    st.success("All test cases passed! 🎉")
                    award_xp(session, user.id, "coding_problem_solved")
                    if problem.difficulty == "Hard":
                        grant_badge(session, user.id, "Hard Problem Solver")
                    grant_badge(session, user.id, "Coding Streak Starter")

            session.commit()

    with tab_stats:
        df = coding_performance_dataframe(session, sp.id)
        total = len(df)
        passed = int(df["Passed"].sum()) if total else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Problems Attempted", total)
        c2.metric("Problems Solved", passed)
        c3.metric("Accuracy", f"{(passed/total*100):.0f}%" if total else "0%")

        if total:
            import plotly.express as px
            fig = px.bar(df.tail(15), x="Date", y="TestsPassed", color="Passed",
                        title="Recent Submissions: Tests Passed")
            st.plotly_chart(fig, use_container_width=True)
