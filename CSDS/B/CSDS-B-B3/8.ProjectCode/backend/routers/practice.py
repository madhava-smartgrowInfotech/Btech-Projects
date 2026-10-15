"""Mock interviews and coding practice."""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.deps import get_db, require, student_of
from database.models import (
    User, CareerRole, InterviewQuestion, MockInterview, InterviewAnswer, InterviewFeedback,
    CodingProblem, CodingSubmission,
)
from ai.interview_engine import get_questions, score_answer_semantic, generate_feedback
from services.code_executor import run_submission
from services.gamification_service import award_xp, grant_badge
from services.analytics_service import interview_performance_dataframe, coding_performance_dataframe

router = APIRouter(tags=["practice"])
student_only = require("student")

INTERVIEW_TYPES = ["Mixed", "Technical", "HR", "Behavioral", "Coding"]
DIFFICULTIES = ["Mixed", "Easy", "Medium", "Hard"]


# ---------------------------------------------------------------- mock interview
@router.get("/interview/meta")
def interview_meta(user: User = Depends(student_only), db=Depends(get_db)):
    return {"roles": [c.title for c in db.query(CareerRole).all()] + ["General"],
            "types": INTERVIEW_TYPES, "difficulties": DIFFICULTIES}


class StartIn(BaseModel):
    role: str
    interview_type: str = "Mixed"
    difficulty: str = "Mixed"
    num_questions: int = Field(default=5, ge=3, le=8)


@router.post("/interview/start")
def start(body: StartIn, user: User = Depends(student_only), db=Depends(get_db)):
    qs = get_questions(db, body.role, body.interview_type, body.difficulty, num_questions=body.num_questions)
    if not qs:
        raise HTTPException(404, "No interview questions are available for this selection.")
    return {"questions": [{"id": q.id, "question": q.question} for q in qs]}


class AnswerIn(BaseModel):
    question_id: int
    answer: str = ""


class SubmitIn(BaseModel):
    role: str
    interview_type: str = "Mixed"
    difficulty: str = "Mixed"
    answers: List[AnswerIn]


@router.post("/interview/submit")
def submit(body: SubmitIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    scored = []
    for a in body.answers:
        q = db.get(InterviewQuestion, a.question_id)
        if not q:
            continue
        score = score_answer_semantic(a.answer, q.question, q.keywords)
        scored.append({"question": q.question, "answer": a.answer, "score": score, "question_id": q.id})
    if not scored:
        raise HTTPException(422, "No valid answers were submitted.")

    fb = generate_feedback(scored, body.role)
    interview = MockInterview(
        student_id=sp.id, role=body.role, interview_type=body.interview_type, difficulty=body.difficulty,
        overall_score=fb["overall_score"], technical_score=fb["technical_score"],
        communication_score=fb["communication_score"], relevance_score=fb["relevance_score"],
        confidence_score=fb["confidence_score"],
    )
    db.add(interview)
    db.flush()
    for a in scored:
        db.add(InterviewAnswer(interview_id=interview.id, question_id=a["question_id"],
                               answer_text=a["answer"], score=a["score"]))
    db.add(InterviewFeedback(interview_id=interview.id, strengths=fb["strengths"], weaknesses=fb["weaknesses"],
                             suggested_topics=fb["suggested_topics"], summary=fb["summary"]))
    award_xp(db, user.id, "mock_interview_completed")
    badge = None
    if fb["overall_score"] >= 80:
        badge = "Interview Ace"
        grant_badge(db, user.id, badge, "Scored 80+ in a mock interview")
    return {**fb, "badge": badge,
            "answers": [{"question": a["question"], "answer": a["answer"], "score": a["score"]} for a in scored]}


@router.get("/interview/history")
def history(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    df = interview_performance_dataframe(db, sp.id)
    return json.loads(df.to_json(orient="records"))


# ---------------------------------------------------------------- coding practice
@router.get("/coding/problems")
def problems(difficulty: str = "All", user: User = Depends(student_only), db=Depends(get_db)):
    solved = {s.problem_id for s in db.query(CodingSubmission).filter_by(
        student_id=student_of(db, user).id, passed=True).all()}
    rows = [p for p in db.query(CodingProblem).all() if difficulty == "All" or p.difficulty == difficulty]
    return [{"id": p.id, "title": p.title, "difficulty": p.difficulty, "concept_tag": p.concept_tag,
             "solved": p.id in solved} for p in rows]


@router.get("/coding/problems/{problem_id}")
def problem(problem_id: int, user: User = Depends(student_only), db=Depends(get_db)):
    p = db.get(CodingProblem, problem_id)
    if not p:
        raise HTTPException(404, "Problem not found.")
    return {"id": p.id, "title": p.title, "difficulty": p.difficulty, "concept_tag": p.concept_tag,
            "description": p.description, "starter_code": p.starter_code, "function_name": p.function_name,
            "test_count": len(json.loads(p.test_cases))}


class CodeIn(BaseModel):
    code: str


@router.post("/coding/problems/{problem_id}/submit")
def submit_code(problem_id: int, body: CodeIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    p = db.get(CodingProblem, problem_id)
    if not p:
        raise HTTPException(404, "Problem not found.")
    result = run_submission(body.code, p.function_name, json.loads(p.test_cases))
    db.add(CodingSubmission(student_id=sp.id, problem_id=p.id, code=body.code, passed=result["passed"],
                            tests_passed=result["tests_passed"], tests_total=result["tests_total"]))
    if result["passed"]:
        award_xp(db, user.id, "coding_problem_solved")
        if p.difficulty == "Hard":
            grant_badge(db, user.id, "Hard Problem Solver")
        grant_badge(db, user.id, "Coding Streak Starter")
    # submitted code can return arbitrary objects; make sure the response is always JSON-safe
    return json.loads(json.dumps(result, default=repr))


@router.get("/coding/stats")
def coding_stats(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    df = coding_performance_dataframe(db, sp.id)
    total = len(df)
    passed = int(df["Passed"].sum()) if total else 0
    recent = [{"date": r["Date"], "tests_passed": r["TestsPassed"], "tests_total": r["TestsTotal"],
               "passed": bool(r["Passed"])} for r in df.tail(15).to_dict("records")]
    return {"attempted": total, "solved": passed, "accuracy": round(passed / total * 100) if total else 0,
            "recent": recent}
