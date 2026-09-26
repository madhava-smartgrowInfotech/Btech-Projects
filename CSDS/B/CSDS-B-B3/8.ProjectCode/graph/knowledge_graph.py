"""
KnowledgeX AI - Knowledge Graph Module
=========================================
BASE PAPER CONCEPT (adopted & extended):
"Enhancing Efficient Personalized Learning and Educational Management in
Universities Using Graph Neural Networks in Intelligent Tutoring Systems"
(IEEE Access, 2026, DOI: 10.1109/ACCESS.2026.3662800)

This module implements the paper's core idea -- representing curriculum and
knowledge as a directed graph, tracking per-topic proficiency, and using
graph structure to reason about what a student should learn next -- using
NetworkX. (The paper uses a full Graph Neural Network; this prototype uses
graph-traversal + weighted scoring as a transparent, dependency-free local
substitute that captures the same underlying idea and can later be swapped
for a trained GNN without changing the rest of the app.)
"""
import networkx as nx

from database.models import LearningTopic, TopicPrerequisite, LearningProgress, StudentSkill, Skill


def build_topic_graph(session) -> nx.DiGraph:
    """Builds the global directed prerequisite graph: prerequisite -> topic."""
    g = nx.DiGraph()
    topics = session.query(LearningTopic).all()
    for t in topics:
        g.add_node(t.id, name=t.name, difficulty=t.difficulty,
                   description=t.description, estimated_hours=t.estimated_hours,
                   related_skill=t.related_skill)

    for edge in session.query(TopicPrerequisite).all():
        g.add_edge(edge.prerequisite_id, edge.topic_id)

    return g


def get_student_knowledge_state(session, student_id) -> dict:
    """Returns {topic_id: proficiency_percent} for the student, derived from
    both explicit LearningProgress completion and related skill proficiency."""
    g = build_topic_graph(session)
    state = {}

    progress_rows = {p.topic_id: p.completion_percent for p in
                      session.query(LearningProgress).filter_by(student_id=student_id).all()}

    skill_rows = {s.name: ss.proficiency for ss, s in
                  session.query(StudentSkill, Skill).join(Skill).filter(StudentSkill.student_id == student_id).all()}

    for node_id, attrs in g.nodes(data=True):
        if node_id in progress_rows:
            state[node_id] = progress_rows[node_id]
        elif attrs["related_skill"] in skill_rows:
            state[node_id] = skill_rows[attrs["related_skill"]]
        else:
            state[node_id] = 0.0

    return state


def classify_topics(session, student_id):
    """
    Classifies every topic into one of: completed, strong, weak, recommended, locked.
    Mirrors the base paper's idea of tracking knowledge-state over a
    prerequisite graph to decide what a student is ready to learn next.
    """
    g = build_topic_graph(session)
    state = get_student_knowledge_state(session, student_id)

    classification = {}
    for node_id, attrs in g.nodes(data=True):
        proficiency = state.get(node_id, 0.0)
        prereqs = list(g.predecessors(node_id))
        prereqs_met = all(state.get(p, 0.0) >= 50 for p in prereqs) if prereqs else True

        if proficiency >= 85:
            status = "completed"
        elif proficiency >= 60:
            status = "strong"
        elif not prereqs_met:
            status = "locked"
        elif proficiency > 0:
            status = "weak"
        else:
            status = "recommended" if prereqs_met else "locked"

        classification[node_id] = {
            "name": attrs["name"],
            "proficiency": proficiency,
            "status": status,
            "difficulty": attrs["difficulty"],
            "description": attrs["description"],
            "estimated_hours": attrs["estimated_hours"],
            "prerequisites": [g.nodes[p]["name"] for p in prereqs],
            "next_topics": [g.nodes[n]["name"] for n in g.successors(node_id)],
        }
    return classification


def get_weak_prerequisites(session, student_id, threshold=50):
    """Identify weak prerequisite topics blocking further progress -- the
    key diagnostic step adopted from the base paper's approach."""
    classification = classify_topics(session, student_id)
    weak = [v for v in classification.values() if v["status"] == "weak" and v["proficiency"] < threshold]
    weak.sort(key=lambda x: x["proficiency"])
    return weak


def topological_learning_order(session, student_id):
    """Returns topic ids in a valid prerequisite-respecting order, prioritizing
    topics the student hasn't completed yet."""
    g = build_topic_graph(session)
    state = get_student_knowledge_state(session, student_id)
    try:
        order = list(nx.topological_sort(g))
    except nx.NetworkXUnfeasible:
        order = list(g.nodes())
    return [n for n in order if state.get(n, 0) < 85]
