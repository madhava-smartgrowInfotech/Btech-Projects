"""
KnowledgeX AI - Career Recommendation Engine
================================================
Locally computed, transparent career-fit scoring using cosine similarity
between the student's skill vector and each career role's required-skill
vector (scikit-learn), combined with interest-keyword matching. No external
LLM required; runs entirely offline.
"""
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from database.models import CareerRole, StudentSkill, Skill


def _student_skill_vector(session, student_id, all_skill_names):
    rows = session.query(StudentSkill, Skill).join(Skill).filter(StudentSkill.student_id == student_id).all()
    proficiency_map = {s.name: ss.proficiency for ss, s in rows}
    return np.array([proficiency_map.get(name, 0.0) for name in all_skill_names])


def _career_requirement_vector(career: CareerRole, all_skill_names):
    required = {s.strip() for s in career.required_skills.split(",") if s.strip()}
    return np.array([100.0 if name in required else 0.0 for name in all_skill_names])


def recommend_careers(session, student_id, top_n=5):
    """Returns a ranked list of career recommendations with skill-gap analysis."""
    all_skills = [s.name for s in session.query(Skill).all()]
    if not all_skills:
        return []

    student_vec = _student_skill_vector(session, student_id, all_skills).reshape(1, -1)
    careers = session.query(CareerRole).all()

    results = []
    for career in careers:
        career_vec = _career_requirement_vector(career, all_skills).reshape(1, -1)
        if np.linalg.norm(student_vec) == 0 or np.linalg.norm(career_vec) == 0:
            similarity = 0.0
        else:
            similarity = float(cosine_similarity(student_vec, career_vec)[0][0])

        required_skills = [s.strip() for s in career.required_skills.split(",") if s.strip()]
        student_props = {name: val for name, val in zip(all_skills, student_vec[0])}
        matched = [s for s in required_skills if student_props.get(s, 0) >= 50]
        missing = [s for s in required_skills if student_props.get(s, 0) < 50]
        match_percent = round((len(matched) / len(required_skills)) * 100, 1) if required_skills else 0.0

        results.append({
            "title": career.title,
            "description": career.description,
            "match_score": round(similarity * 100, 1),
            "skill_match_percent": match_percent,
            "matched_skills": matched,
            "missing_skills": missing,
            "avg_salary_lpa": career.avg_salary_lpa,
            "suggested_certifications": [c.strip() for c in career.suggested_certifications.split(",") if c.strip()],
            "interview_topics": [c.strip() for c in career.interview_topics.split(",") if c.strip()],
            "suggested_projects": _suggest_projects(career.title, missing),
        })

    results.sort(key=lambda x: (x["match_score"] + x["skill_match_percent"]) / 2, reverse=True)
    return results[:top_n]


def _suggest_projects(career_title, missing_skills):
    base_projects = {
        "Machine Learning Engineer": ["End-to-end ML pipeline with deployment", "Kaggle competition project"],
        "Data Scientist": ["Exploratory data analysis on a real dataset", "A/B testing simulation project"],
        "Data Analyst": ["Interactive sales dashboard", "Business KPI reporting project"],
        "AI Engineer": ["Custom chatbot with NLP", "Image classification web app"],
        "Software Developer": ["Full-stack CRUD application", "Open-source contribution"],
        "Backend Developer": ["REST API with authentication", "Microservices demo project"],
        "Cloud Engineer": ["Deploy a scalable app on AWS/GCP free tier", "CI/CD pipeline project"],
        "Cybersecurity Analyst": ["Vulnerability assessment report", "Home-lab intrusion detection setup"],
    }
    projects = base_projects.get(career_title, ["Portfolio project demonstrating core skills"])
    if missing_skills:
        projects.append(f"A project focused on strengthening: {', '.join(missing_skills[:3])}")
    return projects
