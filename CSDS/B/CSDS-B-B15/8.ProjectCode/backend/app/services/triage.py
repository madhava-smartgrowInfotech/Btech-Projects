"""Severity classification: symptom model + symptom severity weights + red-flag rules.

Also maps free text to the symptom vocabulary with Gemini (keyword matching as fallback).
"""
import csv
import json
import logging
import re
import urllib.error
import urllib.request
from functools import lru_cache

import joblib
import numpy as np

from ..config import DATA, DISCLAIMER, GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL, MODELS

log = logging.getLogger("uvicorn.error")
LEVELS = ["mild", "moderate", "severe", "critical"]
PRIORITY = {"critical": 0, "severe": 1, "moderate": 2, "mild": 2}
HIDDEN = {"prognosis", "foul_smell_ofurine"}  # dataset artefacts, not real symptoms

# Symptom-weight score thresholds (weights 1-7 from Symptom-severity.csv)
SCORE_BANDS = [(24, "critical"), (15, "severe"), (8, "moderate"), (0, "mild")]

# Red-flag rules: any single symptom or combination listed forces the given level
RED_FLAG_SINGLE = {
    "coma": "critical", "altered_sensorium": "critical", "weakness_of_one_body_side": "critical",
    "slurred_speech": "critical", "stomach_bleeding": "critical", "acute_liver_failure": "critical",
    "blood_in_sputum": "severe", "bloody_stool": "severe", "fluid_overload": "severe",
}
RED_FLAG_COMBOS = [
    ({"chest_pain", "breathlessness"}, "critical", "chest pain with breathlessness"),
    ({"chest_pain", "sweating"}, "critical", "chest pain with sweating"),
    ({"breathlessness", "fast_heart_rate"}, "severe", "breathlessness with fast heart rate"),
    ({"high_fever", "stiff_neck"}, "severe", "high fever with stiff neck"),
    ({"high_fever", "altered_sensorium"}, "critical", "high fever with confusion"),
]

SPECIALTY_NORMALISE = {
    "allergist": "Allergy", "cardiologist": "Cardiology", "dermatologist": "Dermatology",
    "endocrinologist": "Endocrinology", "gastroenterologist": "Gastroenterology",
    "gynecologist": "Gynecology", "hepatologist": "Hepatology", "internal medcine": "General Medicine",
    "neurologist": "Neurology", "osteopathic": "General Medicine", "otolaryngologist": "ENT",
    "pediatrician": "Pediatrics", "phlebologist": "Vascular Surgery", "pulmonologist": "Pulmonology",
    "rheumatologists": "Rheumatology", "tuberculosis": "Pulmonology",
}

SYNONYMS = {
    "fever": "high_fever", "high temperature": "high_fever", "temperature": "high_fever",
    "low grade fever": "mild_fever", "slight fever": "mild_fever",
    "short of breath": "breathlessness", "shortness of breath": "breathlessness",
    "breathing difficulty": "breathlessness", "difficulty breathing": "breathlessness",
    "breathless": "breathlessness", "can't breathe": "breathlessness", "wheez": "breathlessness",
    "coughing": "cough", "vomit": "vomiting", "throwing up": "vomiting", "loose motion": "diarrhoea",
    "diarrhea": "diarrhoea", "rash": "skin_rash", "tired": "fatigue", "tiredness": "fatigue",
    "weak": "fatigue", "dizzy": "dizziness", "giddiness": "dizziness", "unconscious": "coma",
    "confused": "altered_sensorium", "confusion": "altered_sensorium", "sweat": "sweating",
    "heart racing": "fast_heart_rate", "palpitation": "palpitations", "stomach ache": "stomach_pain",
    "tummy pain": "stomach_pain", "belly ache": "belly_pain", "chest tightness": "chest_pain",
    "sneezing": "continuous_sneezing", "runny nose": "runny_nose", "blocked nose": "congestion",
    "sore throat": "throat_irritation", "yellow eyes": "yellowing_of_eyes", "jaundice": "yellowish_skin",
    "burning urine": "burning_micturition", "painful urination": "burning_micturition",
    "body ache": "muscle_pain", "body pain": "muscle_pain", "joint ache": "joint_pain",
    "blood in cough": "blood_in_sputum", "coughing blood": "blood_in_sputum", "shivers": "shivering",
    "one side weakness": "weakness_of_one_body_side", "paralysis": "weakness_of_one_body_side",
    "itchy": "itching", "headaches": "headache", "migraine": "headache", "nauseous": "nausea",
    "no appetite": "loss_of_appetite", "blurry vision": "blurred_and_distorted_vision",
}


@lru_cache
def _assets():
    bundle = joblib.load(MODELS / "triage_model.joblib")
    model, vocab = bundle["model"], bundle["vocab"]
    weights = {}
    with open(DATA / "disease_symptom" / "Symptom-severity.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            weights[clean_symptom(r["Symptom"])] = int(r["weight"])
    acuity = {}
    with open(DATA / "disease_acuity.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            acuity[r["disease"].strip()] = r["baseline_severity"]
    specialty = {}
    with open(DATA / "doctor_specialist" / "Doctor_Versus_Disease.csv", encoding="latin-1") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                spec = re.sub(r"[^a-z ]", "", row[1].strip().lower()).strip()
                specialty[row[0].strip().lower()] = SPECIALTY_NORMALISE.get(spec, "General Medicine")
    descriptions = {}
    with open(DATA / "disease_symptom" / "symptom_Description.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            descriptions[r["Disease"].strip().lower()] = r["Description"].strip()
    return model, vocab, weights, acuity, specialty, descriptions


def symptom_vocab():
    _, vocab, weights, *_ = _assets()
    return [{"key": s, "label": label(s), "weight": weights.get(s, 3)} for s in vocab if s not in HIDDEN]


def clean_symptom(s: str) -> str:
    return re.sub(r"\s+", "_", re.sub(r"\s*_\s*", "_", s.strip())).lower()


def label(s: str) -> str:
    return s.replace("_", " ").replace("(typhos)", "").strip().capitalize()


def clean_disease(d: str) -> str:
    d = d.strip()
    fixes = {"(vertigo) Paroymsal  Positional Vertigo": "Positional vertigo", "Peptic ulcer diseae": "Peptic ulcer disease",
             "Dimorphic hemmorhoids(piles)": "Haemorrhoids (piles)", "Osteoarthristis": "Osteoarthritis"}
    return fixes.get(d, d[:1].upper() + d[1:])


def classify(symptoms: list[str]) -> dict:
    model, vocab, weights, acuity, specialty_map, descriptions = _assets()
    idx = {s: i for i, s in enumerate(vocab)}
    syms = sorted({s for s in symptoms if s in idx and s not in HIDDEN})
    if not syms:
        raise ValueError("Select at least one recognised symptom")

    x = np.zeros((1, len(vocab)), dtype=np.float32)
    for s in syms:
        x[0, idx[s]] = 1
    proba = model.predict_proba(x)[0]
    order = proba.argsort()[::-1][:3]
    top = [{"condition": clean_disease(model.classes_[i]), "raw": model.classes_[i].strip(),
            "probability": round(float(proba[i]), 3)} for i in order]

    score = sum(weights.get(s, 3) for s in syms)
    score_level = next(level for cut, level in SCORE_BANDS if score >= cut)
    reasons = [f"symptom severity score {score} -> {score_level}"]
    level = score_level

    best = top[0]
    if best["probability"] >= 0.5:
        base = acuity.get(best["raw"], "moderate")
        reasons.append(f"likely condition {best['condition']} ({best['probability']:.0%}) -> {base}")
        if LEVELS.index(base) > LEVELS.index(level):
            level = base

    red_flags = []
    sset = set(syms)
    for s, lv in RED_FLAG_SINGLE.items():
        if s in sset:
            red_flags.append(label(s))
            if LEVELS.index(lv) > LEVELS.index(level):
                level = lv
    for combo, lv, text in RED_FLAG_COMBOS:
        if combo <= sset:
            red_flags.append(text)
            if LEVELS.index(lv) > LEVELS.index(level):
                level = lv
    if red_flags:
        reasons.append("red flags: " + ", ".join(red_flags))

    spec = specialty_map.get(best["raw"].lower(), "General Medicine") if best["probability"] >= 0.3 else "General Medicine"
    advice = {
        "critical": "Possible emergency. Go to the nearest emergency department now or call 108. "
                    "An emergency-quota slot is reserved for you today.",
        "severe": "Needs prompt medical attention today. Book the earliest slot and avoid exertion.",
        "moderate": "See a doctor within a day or two. Rest, fluids, and watch for worsening.",
        "mild": "Usually manageable with a routine OP visit. Book a convenient slot.",
    }[level]
    return {
        "symptoms": [{"key": s, "label": label(s), "weight": weights.get(s, 3)} for s in syms],
        "severity": level, "score": score, "red_flags": red_flags, "reasons": reasons,
        "conditions": [{"condition": t["condition"], "probability": t["probability"]} for t in top],
        "condition": best["condition"], "specialty": spec,
        "description": descriptions.get(best["raw"].lower(), ""),
        "advice": advice, "emergency": level == "critical", "disclaimer": DISCLAIMER,
    }


def keyword_map(text: str) -> list[str]:
    _, vocab, *_ = _assets()
    t = " " + re.sub(r"[^a-z' ]", " ", text.lower()) + " "
    found = set()
    for s in vocab:
        if s in HIDDEN:
            continue
        if " " + s.replace("_", " ") + " " in t:
            found.add(s)
    for phrase, s in SYNONYMS.items():
        if phrase in t and s in vocab:
            found.add(s)
    if re.search(r"chest\w*\b.{0,30}\b(tight|pain|pressure|heavy|heaviness|hurts?|burning)|"
                 r"(tight|pain|pressure|heavy|heaviness)\w*\b.{0,15}\bchest", t):
        found.add("chest_pain")
    if re.search(r"(can ?not|can't|cant|unable to|difficult\w*|trouble|hard|struggl\w*|short\w*)\b.{0,20}\bbreath", t):
        found.add("breathlessness")
    if "mild_fever" in found:
        found.discard("high_fever")
    return sorted(found)


def gemini_map(text: str) -> list[str] | None:
    if not GEMINI_API_KEY:
        return None
    _, vocab, *_ = _assets()
    allowed = [s for s in vocab if s not in HIDDEN]
    prompt = (
        "You map a patient's own description of their symptoms to a fixed symptom vocabulary.\n"
        f"Vocabulary: {', '.join(allowed)}\n"
        "Return JSON {\"symptoms\": [...]} using only exact vocabulary keys that the text clearly describes. "
        "Plain 'fever' means high_fever unless described as mild or low grade. Do not guess extra symptoms.\n"
        f"Patient text: {text[:1000]}"
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }).encode()
    # busy / rate-limited / retired models are skipped in favour of the next one in the list
    for model in [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json",
                                                               "x-goog-api-key": GEMINI_API_KEY})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
            out = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
            return sorted({s for s in out.get("symptoms", []) if s in allowed})
        except urllib.error.HTTPError as e:
            msg = e.read()[:160].decode(errors="ignore").replace(chr(10), " ")
            log.warning("Gemini %s HTTP %s: %s", model, e.code, msg)
            if e.code not in (404, 429, 500, 503):
                break
        except Exception as e:
            log.warning("Gemini %s unavailable (%s)", model, type(e).__name__)
    log.warning("Gemini not reachable - using keyword matching")
    return None


def map_text(text: str) -> dict:
    mapped = gemini_map(text)
    if mapped is not None:
        return {"symptoms": mapped, "source": "gemini"}
    return {"symptoms": keyword_map(text), "source": "keyword"}
