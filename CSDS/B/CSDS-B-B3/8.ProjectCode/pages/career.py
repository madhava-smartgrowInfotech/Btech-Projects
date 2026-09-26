"""KnowledgeX AI - AI Career Recommendation System"""
import streamlit as st

from database.models import StudentProfile
from ai.career_engine import recommend_careers


def render(session, user):
    st.title("🎯 AI Career Recommendation")
    st.caption("These are AI-generated suggestions based on your current skills and profile — not an absolute "
               "decision. Use them to guide your exploration.")

    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()

    if st.button("🔮 Get My Career Recommendations", type="primary"):
        st.session_state["_career_recs"] = recommend_careers(session, sp.id, top_n=8)

    recs = st.session_state.get("_career_recs", [])
    if not recs:
        st.info("Click the button above to generate AI-based career recommendations from your skill profile.")
        return

    for rec in recs:
        with st.container(border=True):
            top_row = st.columns([3, 1])
            with top_row[0]:
                st.markdown(f"### {rec['title']}")
                st.markdown(rec["description"])
            with top_row[1]:
                st.metric("Overall Match", f"{rec['match_score']:.0f}%")
                st.caption(f"💰 {rec['avg_salary_lpa']}")

            st.progress(rec["skill_match_percent"] / 100, text=f"Skill coverage: {rec['skill_match_percent']:.0f}%")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**✅ Matched Skills**")
                st.markdown("\n".join(f"- {s}" for s in rec["matched_skills"]) or "_None yet_")
            with c2:
                st.markdown("**❌ Missing Skills**")
                st.markdown("\n".join(f"- {s}" for s in rec["missing_skills"]) or "_None — you're fully equipped!_")

            with st.expander("📋 Roadmap, Projects & Interview Prep"):
                st.markdown("**Suggested certifications:** " + ", ".join(rec["suggested_certifications"]))
                st.markdown("**Suggested projects:**")
                for p in rec["suggested_projects"]:
                    st.markdown(f"- {p}")
                st.markdown("**Interview preparation topics:**")
                for t in rec["interview_topics"]:
                    st.markdown(f"- {t}")

            if st.button(f"Set as My Career Goal", key=f"goal_{rec['title']}"):
                sp.career_goal = rec["title"]
                session.commit()
                st.success(f"Career goal updated to {rec['title']}! Visit the Learning page to regenerate your roadmap.")
                st.rerun()

    st.caption("_AI-generated suggestion based on your current skills, assessments and interests. "
              "This is not a guaranteed outcome — explore what resonates with you._")
