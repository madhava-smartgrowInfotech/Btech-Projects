"""Gemini assistant: plain-language report explanations, treatment summaries and health questions."""
from fastapi import HTTPException
from google import genai
from google.genai import types

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_MODEL

LIPID_CODES = {"2093-3", "2571-8", "18262-6", "2085-9", "13457-7"}
SAFETY = ("You support patients and clinicians. You never give a final diagnosis and never change a prescription; "
          "you explain, summarise and suggest questions to ask a qualified doctor. Keep it clear and concise. "
          "Use short headings and bullet points. End with one line reminding the reader to confirm with their doctor.")

_client = None


def generate(prompt: str) -> str:
    global _client
    if not GEMINI_API_KEY:
        raise HTTPException(503, "AI assistant is not configured: set GEMINI_API_KEY in .env")
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=45_000))
    error = None
    # Free-tier keys have small per-model rate limits and models can be overloaded: try the fallbacks in order.
    models = [GEMINI_MODEL] + [m.strip() for m in GEMINI_FALLBACK_MODEL.split(",") if m.strip()]
    for model in dict.fromkeys(models):
        try:
            resp = _client.models.generate_content(model=model, contents=prompt,
                                                   config={"system_instruction": SAFETY, "temperature": 0.3})
            return resp.text or ""
        except Exception as e:
            error = e
            busy = ("429", "RESOURCE_EXHAUSTED", "404", "503", "UNAVAILABLE", "timed out", "Timeout")
            if not any(code in f"{e.__class__.__name__} {e}" for code in busy):
                break
    raise HTTPException(502, f"AI assistant unavailable (Gemini busy or over quota, try again shortly): {str(error)[:250]}")


def report_lines(timeline: list[dict], report_id: str | None) -> tuple[str, list[str]]:
    """Find a lab report (or the latest lipid panel) and its result values."""
    reports = [i for i in timeline if i["type"] == "DiagnosticReport"]
    obs_by_id = {i["id"]: i for i in timeline if i["type"] == "Observation"}
    if report_id:
        rep = next((r for r in reports if r["id"] == report_id), None)
    else:
        rep = next((r for r in reports if r.get("code") == "57698-3" or "lipid" in r["title"].lower()), None)
    if rep:
        lines = [f"{obs_by_id[x]['title']}: {obs_by_id[x]['value']}" for x in rep.get("results", []) if x in obs_by_id]
        if lines:
            return f"{rep['title']} ({(rep['date'] or '')[:10]}, {rep['hospital_name']})", lines
    if not report_id:  # no panel resource: use the latest lipid observations
        lipids = [i for i in timeline if i["type"] == "Observation" and i.get("code") in LIPID_CODES]
        if lipids:
            day = lipids[0]["date"][:10]
            return f"Lipid results ({day})", [f"{i['title']}: {i['value']}" for i in lipids if i["date"][:10] == day]
    raise HTTPException(404, "No matching lab report with results was found in this record")


def explain_report(timeline: list[dict], report_id: str | None, language: str) -> dict:
    title, lines = report_lines(timeline, report_id)
    prompt = (f"Explain this lab report to a patient in plain language. Write the whole answer in {language}.\n"
              f"For each value say what it measures and whether it is within the usual adult reference range, "
              f"then give 2-3 practical next steps and questions for the doctor.\n\nReport: {title}\n" + "\n".join(lines))
    return {"title": title, "values": lines, "language": language, "text": generate(prompt)}


def context_block(timeline: list[dict]) -> str:
    conds = sorted({i["title"] for i in timeline if i["type"] == "Condition" and i["status"] == "active"})
    past = sorted({i["title"] for i in timeline if i["type"] == "Condition" and i["status"] != "active"})[:15]
    meds = sorted({f"{i['title']} ({i['value']})" if i["value"] else i["title"]
                   for i in timeline if i["type"] == "MedicationRequest" and i["status"] == "active"})
    allergies = sorted({i["title"] for i in timeline if i["type"] == "AllergyIntolerance"})
    labs, seen = [], set()
    for i in timeline:
        if i["type"] == "Observation" and i["title"] not in seen and len(labs) < 20:
            seen.add(i["title"])
            labs.append(f"{i['title']}: {i['value']} ({(i['date'] or '')[:10]})")
    visits = [f"{(i['date'] or '')[:10]} {i['title']} at {i['hospital_name']}" for i in timeline if i["type"] == "Encounter"][:12]
    return (f"Active conditions: {', '.join(conds) or 'none recorded'}\n"
            f"Past conditions: {', '.join(past) or 'none recorded'}\n"
            f"Active medications: {', '.join(meds) or 'none recorded'}\n"
            f"Allergies: {', '.join(allergies) or 'none recorded'}\n"
            f"Latest measurements:\n  " + "\n  ".join(labs) + "\nRecent visits:\n  " + "\n  ".join(visits))


def summarise(timeline: list[dict], language: str) -> dict:
    prompt = (f"Summarise this patient's treatment history across hospitals in plain language, in {language}. "
              f"Cover: main health problems, current medicines and what they are for, recent visits, and follow-up "
              f"that seems due.\n\n{context_block(timeline)}")
    return {"language": language, "text": generate(prompt)}


def ask(timeline: list[dict], question: str, language: str) -> dict:
    prompt = (f"Answer the patient's question in {language}, using their record below. For medication questions give "
              f"general guidance on timing, common side effects and interactions with their other medicines.\n\n"
              f"Record:\n{context_block(timeline)}\n\nQuestion: {question}")
    return {"language": language, "question": question, "text": generate(prompt)}
