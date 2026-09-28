"""Resume parsing (pdfplumber), role classification (scikit-learn) and ATS-style scoring."""
import io
import json
import re
from functools import lru_cache

import joblib

from ..config import MODELS
from .skills import extract_skills

SECTION_PATTERNS = {
    "summary": r"\b(summary|objective|profile|about me)\b",
    "experience": r"\b(experience|employment|work history)\b",
    "education": r"\b(education|degree|bachelor|master|diploma|university|school)\b",
    "skills": r"\b(skills|technical skills|competencies|highlights)\b",
    "projects": r"\b(projects?|accomplishments|achievements|certifications?|awards)\b",
}
ACTION_VERBS = ["managed", "led", "developed", "designed", "built", "implemented", "created", "improved", "increased",
                "reduced", "delivered", "launched", "coordinated", "analyzed", "analysed", "trained", "organized",
                "negotiated", "achieved", "streamlined", "supervised", "optimized", "automated", "resolved"]


@lru_cache(maxsize=1)
def model():
    return joblib.load(MODELS / "resume_clf.joblib")


@lru_cache(maxsize=1)
def role_skills():
    return json.loads((MODELS / "role_skills.json").read_text())


def roles():
    return sorted(role_skills().keys())


def pretty(role):
    return role.replace("-", " ").title().replace("Hr", "HR").replace("Bpo", "BPO")


def extract_text(pdf_bytes):
    import pdfplumber
    parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:10]:
            parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def classify(text):
    clf = model()
    proba = clf.predict_proba([text])[0]
    ranked = sorted(zip(clf.classes_, proba), key=lambda x: -x[1])
    return [{"role": r, "label": pretty(r), "prob": round(float(p), 4)} for r, p in ranked]


def analyze(text, target_role=None):
    ranked = classify(text)
    predicted = ranked[0]["role"]
    target = target_role if target_role in role_skills() else predicted
    probs = {r["role"]: r["prob"] for r in ranked}
    found = extract_skills(text)
    required = [x["skill"] for x in role_skills()[target]]
    matched = [s for s in required if s in found]
    missing = [s for s in required if s not in found]
    low = text.lower()
    words = re.findall(r"[A-Za-z][A-Za-z+#.\-]*", text)
    wc = len(words)

    contact = {"email": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)),
               "phone": bool(re.search(r"(\+?\d[\d\s().-]{8,}\d)", text))}
    sections = {k: bool(re.search(p, low)) for k, p in SECTION_PATTERNS.items()}
    sec_pts = 5 * sum(sections.values()) / len(sections) * 4 + 2.5 * sum(contact.values())  # max 25
    skill_pts = 35 * (len(matched) / len(required) if required else 0)
    fit_pts = 15 * min(1.0, probs.get(target, 0) * 2.5)
    numbers = len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:%|percent|\+|k\b|million|users|clients|projects)|\$\s?\d[\d,]*", low))
    verbs = sum(1 for v in ACTION_VERBS if re.search(r"\b" + v + r"\b", low))
    length_pts = 8 if 300 <= wc <= 1200 else 5 if 150 <= wc <= 2000 else 2
    quant_pts = min(6, numbers * 2)
    verb_pts = min(6, verbs)
    breadth_pts = min(5, len(found) / 3)
    quality = length_pts + quant_pts + verb_pts + breadth_pts  # max 25
    ats = round(min(100.0, sec_pts + skill_pts + fit_pts + quality), 1)

    issues = []
    if not contact["email"]:
        issues.append("No email address found - ATS systems use it to contact you.")
    if not contact["phone"]:
        issues.append("No phone number found.")
    for k, ok in sections.items():
        if not ok:
            issues.append(f"Missing a clear '{k.title()}' section heading.")
    if numbers < 3:
        issues.append("Add quantified achievements (percentages, counts, amounts) to show impact.")
    if verbs < 5:
        issues.append("Start bullet points with strong action verbs (led, built, improved, reduced).")
    if wc < 300:
        issues.append(f"Resume is short ({wc} words); aim for 300-1200 words.")
    elif wc > 2000:
        issues.append(f"Resume is long ({wc} words); trim to the most relevant 1-2 pages.")
    if missing:
        issues.append(f"Add evidence for key {pretty(target)} skills: {', '.join(missing[:6])}.")

    return {
        "ats_score": ats,
        "breakdown": {"sections_contact": round(sec_pts, 1), "skill_match": round(skill_pts, 1),
                      "role_fit": round(fit_pts, 1), "content_quality": round(quality, 1)},
        "predicted_role": predicted, "predicted_label": pretty(predicted), "top_roles": ranked[:3],
        "target_role": target, "target_label": pretty(target), "target_match_prob": probs.get(target, 0),
        "skills": found, "required_skills": required, "matched_skills": matched, "missing_skills": missing,
        "sections": sections, "contact": contact, "word_count": wc, "quantified_achievements": numbers,
        "action_verbs": verbs, "issues": issues,
    }
