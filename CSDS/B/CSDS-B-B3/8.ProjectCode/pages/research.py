"""KnowledgeX AI - Research & Innovation Page"""
import streamlit as st


def render(session, user):
    st.title("🔬 Research & Innovation")

    st.markdown("""
### Base Paper

**Enhancing Efficient Personalized Learning and Educational Management in Universities
Using Graph Neural Networks in Intelligent Tutoring Systems**
*IEEE Access, 2026 — DOI: 10.1109/ACCESS.2026.3662800*
""")

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📖 Base Paper Contribution")
        st.markdown("""
- Represents a student's curriculum and knowledge as a **directed graph**,
  where topics are nodes and prerequisite relationships are edges.
- Tracks a **per-topic knowledge state / proficiency** for each student.
- Uses the graph structure (via a Graph Neural Network in the original paper)
  to reason about which prerequisite topics are weak and what should be
  learned next, enabling **personalized tutoring paths**.

**Adopted in this project:** the directed prerequisite graph, per-topic
proficiency tracking, and weak-prerequisite detection are implemented using
**NetworkX** (see `graph/knowledge_graph.py`). Rather than a trained GNN,
this prototype uses transparent graph-traversal and weighted-scoring
algorithms as a dependency-free local substitute that captures the same
underlying idea — and can be swapped for a trained GNN later without
changing the rest of the application (see `ai/recommendation_engine.py`).
""")

    with c2:
        st.subheader("🚀 Proposed System Extension")
        st.markdown("""
This project extends the base paper's graph-based personalized learning
concept into a **complete student ecosystem**:

- 🎯 **AI Career Recommendation** — cosine-similarity skill matching against
  target career roles.
- 🤝 **Peer Mentorship** — similarity-based mentor-student matching.
- 🛍️ **Learn & Earn Marketplace** — monetizing and sharing knowledge
  resources with a simulated in-app economy.
- 🎤 **AI Mock Interviews** — role-specific question generation and
  local NLP-based answer scoring.
- 💻 **Coding Practice** — sandboxed code execution and skill tracking.
- 🏆 **Gamification** — XP, levels, badges and leaderboards to drive
  engagement.
- 📊 **Student Analytics** — dashboards spanning learning, interviews,
  coding and marketplace activity.
""")

    st.divider()
    st.subheader("🧩 System Architecture")
    st.code("""
Student Data
   ↓
Profile Analysis
   ↓
Skill Assessment
   ↓
Knowledge-State Tracking   ← (Base paper concept)
   ↓
Knowledge Graph            ← (Base paper concept, NetworkX)
   ↓
Weak Skill Detection       ← (Base paper concept)
   ↓
Career Goal Analysis       ← (Proposed extension)
   ↓
Recommendation Engine      ← (Proposed extension: local ML + graph algorithms)
   ↓
Personalized Learning Roadmap
   ↓
Resources + Mentors + Projects   ← (Proposed extension)
   ↓
Progress Tracking
   ↓
Continuous Recommendation Update
""", language="text")

    st.info("This page is intended for project review, viva and research presentation purposes, "
           "clearly separating what was adopted from the base paper versus what was newly proposed.")
