"""
KnowledgeX AI - AI Mock Interview Engine
============================================
Generates role-specific interview questions and scores free-text answers
using local keyword-overlap + heuristic NLP scoring (TF-IDF cosine
similarity via scikit-learn). Falls back gracefully to a generic question
bank when no exact role match exists. Can be swapped for an LLM through the
AI abstraction layer (ai/recommendation_engine.py) without changing callers.
"""
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.models import InterviewQuestion


def get_questions(session, role, interview_type, difficulty, num_questions=5):
    q = session.query(InterviewQuestion).filter(InterviewQuestion.role == role)
    if interview_type != "Mixed":
        q = q.filter(InterviewQuestion.interview_type == interview_type)
    if difficulty != "Mixed":
        q = q.filter(InterviewQuestion.difficulty == difficulty)
    questions = q.all()

    if len(questions) < num_questions:
        # Fall back to General pool + relax filters
        general = session.query(InterviewQuestion).filter(InterviewQuestion.role == "General").all()
        questions = list({q.id: q for q in (questions + general)}.values())

    if len(questions) < num_questions:
        questions = session.query(InterviewQuestion).all()

    random.shuffle(questions)
    return questions[:num_questions]


def score_answer(answer_text: str, keywords: str) -> float:
    """
    Scores an answer 0-100 using keyword coverage + basic length/effort signal.
    A lightweight, fully local substitute for an LLM-based grader.
    """
    if not answer_text or not answer_text.strip():
        return 0.0

    keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    answer_lower = answer_text.lower()

    if keyword_list:
        matched = sum(1 for kw in keyword_list if kw in answer_lower)
        keyword_coverage = matched / len(keyword_list)
    else:
        keyword_coverage = 0.5

    # Reward reasonable elaboration (not too short, not just keyword-stuffed)
    word_count = len(answer_text.split())
    length_factor = min(word_count / 40, 1.0)  # full credit at ~40+ words

    score = (keyword_coverage * 70) + (length_factor * 30)
    return round(min(score, 100), 1)


def score_answer_semantic(answer_text: str, question_text: str, keywords: str) -> float:
    """Optional TF-IDF cosine-similarity based scoring against an ideal-answer
    proxy built from the question + keywords, blended with keyword scoring."""
    keyword_score = score_answer(answer_text, keywords)
    if not answer_text.strip():
        return keyword_score
    try:
        ideal_proxy = f"{question_text} {keywords.replace(',', ' ')}"
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform([ideal_proxy, answer_text])
        similarity = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        semantic_score = similarity * 100
        return round((keyword_score * 0.6) + (semantic_score * 0.4), 1)
    except ValueError:
        return keyword_score


def generate_feedback(answers_with_scores, role):
    """
    answers_with_scores: list of dicts {question, answer, score}
    Returns strengths, weaknesses, suggested_topics, summary, plus aggregate
    technical/communication/relevance/confidence scores.
    """
    if not answers_with_scores:
        return {
            "technical_score": 0, "communication_score": 0, "relevance_score": 0,
            "confidence_score": 0, "overall_score": 0,
            "strengths": "No answers submitted.", "weaknesses": "N/A",
            "suggested_topics": "Attempt the interview to get feedback.",
            "summary": "No interview data available.",
        }

    scores = [a["score"] for a in answers_with_scores]
    avg = sum(scores) / len(scores)

    word_counts = [len(a["answer"].split()) for a in answers_with_scores]
    avg_words = sum(word_counts) / len(word_counts)

    technical_score = round(avg, 1)
    communication_score = round(min(avg_words / 35 * 100, 100), 1)
    relevance_score = round(avg * 0.9 + 5, 1)
    confidence_score = round((technical_score + communication_score) / 2, 1)
    overall_score = round((technical_score + communication_score + relevance_score + confidence_score) / 4, 1)

    weak_answers = [a for a in answers_with_scores if a["score"] < 50]
    strong_answers = [a for a in answers_with_scores if a["score"] >= 75]

    strengths = ("Strong grasp of: " + "; ".join(a["question"][:60] for a in strong_answers[:3])
                 if strong_answers else "Keep practicing to build stronger demonstrable strengths.")
    weaknesses = ("Needs improvement on: " + "; ".join(a["question"][:60] for a in weak_answers[:3])
                  if weak_answers else "No major weak areas detected in this attempt.")
    suggested_topics = (", ".join(sorted({w["question"][:40] for w in weak_answers}))
                        if weak_answers else f"Continue reinforcing core {role} fundamentals.")

    if overall_score >= 80:
        summary = f"Excellent performance for the {role} role. You're interview-ready for this level."
    elif overall_score >= 55:
        summary = f"Good attempt for the {role} role, with some gaps to close before you're fully ready."
    else:
        summary = f"This attempt shows several gaps for the {role} role. Focus on the suggested topics and retry."

    return {
        "technical_score": technical_score, "communication_score": communication_score,
        "relevance_score": relevance_score, "confidence_score": confidence_score,
        "overall_score": overall_score, "strengths": strengths, "weaknesses": weaknesses,
        "suggested_topics": suggested_topics, "summary": summary,
    }
