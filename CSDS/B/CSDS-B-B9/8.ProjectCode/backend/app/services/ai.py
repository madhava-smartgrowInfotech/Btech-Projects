"""Gemini client: role-specific interview questions, rubric scoring, explanations and resume tips."""
import json
import re

from fastapi import HTTPException

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL

_client = None


def configured():
    return bool(GEMINI_API_KEY)


def _get_client():
    global _client
    if not GEMINI_API_KEY:
        raise HTTPException(503, "AI features need GEMINI_API_KEY in .env (get one at https://aistudio.google.com/apikey)")
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _parse_json(text):
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    return json.loads(text)


RETRYABLE = ("429", "503", "404", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "NOT_FOUND", "overloaded", "high demand")


def generate_json(prompt, temperature=0.4):
    """Call Gemini in JSON mode; on busy / quota / retired-model errors fall through the fallback models."""
    from google.genai import types
    client = _get_client()
    models = [GEMINI_MODEL] + [m for m in GEMINI_FALLBACK_MODELS if m != GEMINI_MODEL]
    errors = []
    for model in models:
        for _ in range(2):  # one retry for malformed JSON
            try:
                resp = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=temperature))
                return _parse_json(resp.text)
            except (ValueError, json.JSONDecodeError) as e:
                errors.append(f"{model}: malformed JSON ({e})")
            except Exception as e:  # network / quota / auth errors from the API
                msg = str(e)
                errors.append(f"{model}: {msg[:160]}")
                if not any(k in msg for k in RETRYABLE):
                    raise HTTPException(502, f"Gemini request failed: {msg[:300]}")
                break  # try the next model
    raise HTTPException(502, "Gemini is unavailable right now (all models busy or over quota) - please retry shortly. "
                             + " | ".join(errors[-3:]))


def interview_questions(role, level, count, skills=None, kind="mixed"):
    skills_txt = f" The candidate lists these skills: {', '.join(skills[:15])}." if skills else ""
    prompt = f"""You are an experienced technical interviewer hiring for the role "{role}" at {level} level.{skills_txt}
Write {count} interview questions for a {kind} interview: mostly role-specific technical questions,
plus one behavioural question. Each question must be answerable verbally in 1-3 minutes.
Return JSON: {{"questions": [{{"q": "question text", "type": "technical|behavioural|scenario",
"focus": "short topic label", "ideal_points": ["key point an ideal answer covers", "..."]}}]}}"""
    data = generate_json(prompt, temperature=0.8)
    qs = data.get("questions", data if isinstance(data, list) else [])
    return [{"q": str(q.get("q", "")).strip(), "type": q.get("type", "technical"), "focus": q.get("focus", ""),
             "ideal_points": [str(x) for x in q.get("ideal_points", [])][:6]} for q in qs if q.get("q")][:count]


RUBRIC = ["relevance", "technical_accuracy", "clarity", "structure", "depth"]


def score_interview(role, level, qa):
    items = "\n\n".join(
        f"Q{i+1}: {x['q']}\nIdeal points: {'; '.join(x.get('ideal_points', []))}\nCandidate answer: {x['answer'] or '(no answer)'}"
        for i, x in enumerate(qa))
    prompt = f"""You are a strict but fair interviewer for the role "{role}" ({level} level).
Score each answer on this rubric, each criterion an integer 0-10:
relevance (answers the question asked), technical_accuracy (facts are correct), clarity (easy to follow),
structure (logical order, examples), depth (goes beyond surface level). An empty or off-topic answer scores 0-2.
Give specific, actionable feedback for each answer and a short model answer.

{items}

Return JSON: {{"answers": [{{"scores": {{"relevance": 0, "technical_accuracy": 0, "clarity": 0, "structure": 0, "depth": 0}},
"feedback": "2-3 sentences", "model_answer": "2-4 sentences"}}],
"strengths": ["..."], "improvements": ["..."], "summary": "3-4 sentence overall assessment",
"hire_signal": "strong_yes|yes|lean_no|no"}}"""
    data = generate_json(prompt, temperature=0.2)
    answers = data.get("answers", [])
    out = []
    for i, x in enumerate(qa):
        a = answers[i] if i < len(answers) else {}
        sc = {k: max(0, min(10, int(round(float((a.get("scores") or {}).get(k, 0) or 0))))) for k in RUBRIC}
        if not (x.get("answer") or "").strip():
            sc = {k: 0 for k in RUBRIC}
        out.append({"scores": sc, "score": round(sum(sc.values()) / len(RUBRIC), 1),
                    "feedback": a.get("feedback", ""), "model_answer": a.get("model_answer", "")})
    return {"answers": out, "strengths": data.get("strengths", [])[:5], "improvements": data.get("improvements", [])[:5],
            "summary": data.get("summary", ""), "hire_signal": data.get("hire_signal", "")}


def explain_question(text, options, answer):
    opts = "\n".join(f"({'ABCD'[i]}) {o}" for i, o in enumerate(options))
    prompt = f"""Explain step by step, in at most 120 words, why option ({'ABCD'[answer]}) is correct.
Question: {text}
Options:
{opts}
Return JSON: {{"explanation": "..."}}"""
    return str(generate_json(prompt, temperature=0.2).get("explanation", "")).strip()


def resume_tips(text, target_role, missing):
    prompt = f"""You are a career coach reviewing a resume for the target role "{target_role}".
Skills the resume is missing for this role: {', '.join(missing) or 'none'}.
Resume (truncated):
{text[:6000]}

Return JSON: {{"tips": ["4-6 specific, actionable improvements to this resume"],
"summary": "2 sentence overall assessment"}}"""
    data = generate_json(prompt, temperature=0.3)
    return {"tips": [str(t) for t in data.get("tips", [])][:6], "summary": str(data.get("summary", ""))}
