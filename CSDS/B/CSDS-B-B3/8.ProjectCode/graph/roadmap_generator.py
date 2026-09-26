"""
KnowledgeX AI - Roadmap Generator
====================================
Generates a personalized, prerequisite-respecting learning roadmap towards a
student's chosen career goal, extending the base paper's graph-based
knowledge-state tracking with career-goal-aware prioritization (a proposed
extension beyond the base paper).
"""
from database.models import CareerRole, LearningTopic
from graph.knowledge_graph import build_topic_graph, get_student_knowledge_state
import networkx as nx


def _topics_relevant_to_career(session, career_title):
    career = session.query(CareerRole).filter_by(title=career_title).first()
    if not career:
        return set()
    required = {s.strip() for s in career.required_skills.split(",") if s.strip()}
    topics = session.query(LearningTopic).filter(LearningTopic.related_skill.in_(required)).all()
    return {t.id for t in topics}


def generate_roadmap(session, student_id, career_goal=None, max_steps=12):
    """
    Produces an ordered roadmap of topics respecting prerequisites, weighted
    toward the student's career goal and current weak areas.

    Each step includes: name, difficulty, priority, estimated_time,
    prerequisites, completion_percent, recommended_resources.
    """
    g = build_topic_graph(session)
    state = get_student_knowledge_state(session, student_id)

    relevant_ids = _topics_relevant_to_career(session, career_goal) if career_goal else set(g.nodes())
    if not relevant_ids:
        relevant_ids = set(g.nodes())

    # Expand to include prerequisite ancestors of relevant topics so the
    # roadmap is prerequisite-complete, not just the goal skills themselves.
    expanded = set(relevant_ids)
    for node in list(relevant_ids):
        expanded |= nx.ancestors(g, node)

    try:
        topo_order = list(nx.topological_sort(g))
    except nx.NetworkXUnfeasible:
        topo_order = list(g.nodes())

    candidates = [n for n in topo_order if n in expanded and state.get(n, 0) < 85]

    def priority_score(node_id):
        proficiency = state.get(node_id, 0.0)
        is_goal_topic = 1 if node_id in relevant_ids else 0
        gap = 100 - proficiency
        # Higher score = higher priority. Weighted per documented formula (Section 23).
        return (gap * 0.5) + (is_goal_topic * 40) + (10 if proficiency == 0 else 0)

    candidates.sort(key=priority_score, reverse=True)

    # Re-sort respecting prerequisite order among the top-priority candidates
    top_candidates = set(candidates[:max_steps * 2])
    ordered_steps = [n for n in topo_order if n in top_candidates][:max_steps]

    roadmap = []
    for idx, node_id in enumerate(ordered_steps, start=1):
        attrs = g.nodes[node_id]
        proficiency = state.get(node_id, 0.0)
        prereqs = [g.nodes[p]["name"] for p in g.predecessors(node_id)]
        roadmap.append({
            "step": idx,
            "topic_id": node_id,
            "name": attrs["name"],
            "difficulty": attrs["difficulty"],
            "priority": "High" if priority_score(node_id) > 60 else ("Medium" if priority_score(node_id) > 30 else "Low"),
            "estimated_hours": attrs["estimated_hours"],
            "prerequisites": prereqs,
            "completion_percent": proficiency,
            "recommended_resources": _recommend_resources_for_topic(session, attrs["name"]),
            "explanation": _explain(career_goal, attrs["name"], proficiency, node_id in relevant_ids),
        })
    return roadmap


def _recommend_resources_for_topic(session, topic_name):
    from database.models import Resource
    resources = session.query(Resource).filter(
        Resource.skill_tags.ilike(f"%{topic_name}%")).limit(3).all()
    return [r.title for r in resources] if resources else [f"Search marketplace for '{topic_name}' resources"]


def _explain(career_goal, topic_name, proficiency, is_goal_topic):
    if career_goal and is_goal_topic and proficiency < 50:
        return (f"Recommended because your goal is {career_goal} and your assessment indicates "
                f"that {topic_name} is currently a weak prerequisite.")
    if career_goal and is_goal_topic:
        return f"Relevant to your goal of becoming a {career_goal}."
    return f"Builds a prerequisite foundation needed for topics in your roadmap."
