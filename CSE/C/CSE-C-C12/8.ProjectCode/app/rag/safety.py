"""Software safety rule layer (not a clinical triage model)."""
import re

EMERGENCY_PATTERNS = [
    (r"severe\s+chest\s+pain|crushing\s+chest|chest\s+pressure", "Severe chest pain can be an emergency."),
    (r"difficulty\s+breathing|shortness\s+of\s+breath|can.?t\s+breathe|struggling\s+to\s+breathe", "Difficulty breathing can be an emergency."),
    (r"severe\s+bleeding|heavy\s+bleeding|uncontrolled\s+bleed", "Severe bleeding needs urgent care."),
    (r"loss\s+of\s+consciousness|passed\s+out|fainted|unconscious", "Loss of consciousness needs urgent evaluation."),
    (r"slurred\s+speech|face\s+droop|one\s+side\s+(weak|numb)|stroke", "Stroke-like symptoms need emergency care."),
    (r"severe\s+allergic|anaphylaxis|throat\s+closing|swollen\s+(lips|tongue|face).*breath", "Severe allergic reaction can be an emergency."),
    (r"suicid|self.?harm|kill\s+myself|end\s+my\s+life", "Self-harm thoughts need immediate support."),
    (r"sudden\s+(severe\s+headache|vision\s+loss|numbness|weakness|confusion)", "Sudden severe neurological symptoms need emergency care."),
    (r"seizure|convulsion", "Seizures need urgent evaluation."),
    (r"severe\s+abdominal\s+pain|rigid\s+abdomen", "Severe abdominal pain needs urgent evaluation."),
]

DISCLAIMER = ("CareLens AI provides preliminary health information and is not a medical diagnosis. "
              "If symptoms are severe, rapidly worsening, or you believe you may be experiencing "
              "an emergency, seek immediate professional medical care.")

def check_safety(query: str) -> dict:
    q = (query or "").lower()
    for pattern, advice in EMERGENCY_PATTERNS:
        if re.search(pattern, q):
            return {
                "flag": "emergency",
                "message": (f"Emergency safety notice: {advice} Please seek urgent/emergency medical care "
                            "right away (local emergency number or nearest emergency department). " + DISCLAIMER)
            }
    # high-risk single keywords that merit caution banner
    cautious = ["chest pain", "breathing", "bleeding", "pregnant", "infant", "newborn"]
    if any(k in q for k in cautious):
        return {"flag": "caution",
                "message": ("Caution: your message mentions potentially serious symptoms. "
                            "Consider contacting a healthcare professional promptly. " + DISCLAIMER)}
    return {"flag": "routine", "message": DISCLAIMER}

def apply_safety_filter(answer: str) -> str:
    banned = ["take ibuprofen", "take antibiotics", "dosage", "prescribe", "mg twice daily"]
    text = answer
    for b in banned:
        if b.lower() in text.lower():
            text = text.replace(b, "[removed: specific medication instruction]")
    return text
