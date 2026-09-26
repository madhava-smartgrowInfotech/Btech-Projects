"""
KnowledgeX AI - Mentor Recommendation Engine
================================================
Matches students to mentors using skill/domain/keyword similarity, rating and
experience -- a locally computed similarity-matching algorithm (no external
API needed).
"""
from database.models import MentorProfile, User


def _text_overlap_score(text_a: str, text_b: str) -> float:
    """Simple keyword-overlap similarity between two comma/space separated strings."""
    set_a = {w.strip().lower() for w in text_a.replace(",", " ").split() if w.strip()}
    set_b = {w.strip().lower() for w in text_b.replace(",", " ").split() if w.strip()}
    if not set_a or not set_b:
        return 0.0
    overlap = len(set_a & set_b)
    return overlap / max(len(set_a), 1)


def recommend_mentors(session, required_skill="", career_goal="", domain="", top_n=5):
    mentors = session.query(MentorProfile).filter_by(is_verified=True).all()
    query_text = f"{required_skill} {career_goal} {domain}"

    scored = []
    for m in mentors:
        skill_score = _text_overlap_score(query_text, m.expertise)
        domain_score = _text_overlap_score(query_text, m.domain)
        experience_score = min(m.experience_years / 10, 1.0)
        rating_score = m.rating / 5.0

        total_score = (skill_score * 0.4) + (domain_score * 0.25) + (experience_score * 0.15) + (rating_score * 0.2)

        user = session.query(User).get(m.user_id)
        scored.append({
            "mentor_id": m.id,
            "name": user.name if user else "Unknown",
            "expertise": m.expertise,
            "domain": m.domain,
            "experience_years": m.experience_years,
            "rating": m.rating,
            "rating_count": m.rating_count,
            "availability": m.availability,
            "match_score": round(total_score * 100, 1),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_n]
