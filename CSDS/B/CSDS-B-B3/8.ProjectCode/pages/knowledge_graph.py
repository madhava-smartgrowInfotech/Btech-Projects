"""KnowledgeX AI - Interactive Knowledge Graph (base paper concept)"""
import streamlit as st
import networkx as nx
import plotly.graph_objects as go

from database.models import StudentProfile
from graph.knowledge_graph import build_topic_graph, classify_topics

STATUS_COLORS = {
    "completed": "#2ecc71",
    "strong": "#3498db",
    "weak": "#f39c12",
    "recommended": "#9b59b6",
    "locked": "#95a5a6",
}
STATUS_LABELS = {
    "completed": "✅ Completed", "strong": "💪 Strong", "weak": "⚠️ Weak",
    "recommended": "⭐ Recommended", "locked": "🔒 Locked",
}


def render(session, user):
    st.title("🕸️ Knowledge Graph")
    st.caption("Curriculum represented as a directed prerequisite graph — the core concept adopted from the "
               "base paper, extended with career-goal-aware roadmap generation.")

    sp = session.query(StudentProfile).filter_by(user_id=user.id).first()
    g = build_topic_graph(session)
    classification = classify_topics(session, sp.id)

    if len(g.nodes) == 0:
        st.warning("No topics found. Please seed the database.")
        return

    layout = nx.spring_layout(g, seed=42, k=0.9)

    edge_x, edge_y = [], []
    for u, v in g.edges():
        x0, y0 = layout[u]
        x1, y1 = layout[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color="#c8c8c8"),
                             hoverinfo="none", mode="lines")

    node_x, node_y, node_color, node_text, node_hover = [], [], [], [], []
    for node_id in g.nodes():
        x, y = layout[node_id]
        node_x.append(x)
        node_y.append(y)
        info = classification[node_id]
        node_color.append(STATUS_COLORS[info["status"]])
        node_text.append(info["name"])
        node_hover.append(f"{info['name']}<br>Status: {STATUS_LABELS[info['status']]}<br>"
                          f"Proficiency: {info['proficiency']:.0f}%<br>Difficulty: {info['difficulty']}")

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=node_text, textposition="top center",
        hovertext=node_hover, hoverinfo="text",
        marker=dict(size=28, color=node_color, line=dict(width=2, color="white")),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False, height=560, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

    legend_cols = st.columns(len(STATUS_COLORS))
    for col, (status, color) in zip(legend_cols, STATUS_COLORS.items()):
        col.markdown(f"<span style='color:{color}; font-size:22px;'>●</span> {STATUS_LABELS[status]}",
                    unsafe_allow_html=True)

    st.divider()
    st.subheader("🔍 Explore a Topic")
    topic_names = sorted([info["name"] for info in classification.values()])
    selected_name = st.selectbox("Select a topic", topic_names)
    selected = next(v for v in classification.values() if v["name"] == selected_name)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"### {selected['name']}")
        st.markdown(selected["description"])
        st.markdown(f"**Status:** {STATUS_LABELS[selected['status']]}  \n"
                    f"**Current proficiency:** {selected['proficiency']:.0f}%  \n"
                    f"**Difficulty:** {selected['difficulty']}  \n"
                    f"**Estimated time:** {selected['estimated_hours']:.0f} hours")
        st.progress(selected["proficiency"] / 100)
    with c2:
        st.markdown("**Prerequisites:**")
        st.markdown("\n".join(f"- {p}" for p in selected["prerequisites"]) or "_None_")
        st.markdown("**Related skill:** " + selected_name)
        st.markdown("**Next recommended topics:**")
        st.markdown("\n".join(f"- {n}" for n in selected["next_topics"][:5]) or "_None — this is a terminal topic_")
