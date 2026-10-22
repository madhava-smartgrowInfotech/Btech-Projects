"""Local HyDE-style query expansion (rule-based, no external API).

Given a raw symptom query, builds:
  1. normalized query (lowercased, trimmed, punctuation tidied)
  2. hypothetical medical-information representation used alongside the
     original query for retrieval.

This is a lightweight local heuristic, not a separate trained model.
"""
import re

_SYMPTOM_HINTS = [
    "fever", "headache", "cough", "cold", "pain", "nausea", "vomiting",
    "diarrhea", "fatigue", "rash", "sore throat", "breath", "chest",
    "dizziness", "chills", "sweat", "ache", "stomach", "joint",
]

def normalize_query(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[?!;]+", ".", t)
    return t[:2000]

def expand_query_hyde(raw_query: str) -> dict:
    """Return {'normalized': str, 'hypothetical': str, 'combined': str}."""
    norm = normalize_query(raw_query)
    # Extract mention-like fragments (split on commas/periods/and)
    frags = [f.strip() for f in re.split(r"[,.]| and | with ", norm) if f.strip()]
    frags = [f for f in frags if len(f) > 1][:8]
    core = ", ".join(frags) if frags else norm
    hypothetical = (
        f"Medical symptom presentation involving {core}. "
        "Patient-reported symptoms with possible associated systemic features, "
        "onset information and relevant clinical observations for matching medical information."
    )
    combined = f"{norm} {hypothetical}"
    return {"normalized": norm, "hypothetical": hypothetical, "combined": combined}
