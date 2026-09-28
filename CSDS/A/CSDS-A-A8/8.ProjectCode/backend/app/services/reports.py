"""Structured reports written by Gemini from real model outputs (F6)."""
import json
import time

import requests

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SCHEMA_HINT = """Return JSON only, with exactly these keys:
{"title": str, "summary": str (2-3 sentences), "findings": [str, ...] (3-6 items),
 "measurements": [{"name": str, "value": str}, ...], "interpretation": str,
 "limitations": [str, ...] (2-4 items), "recommendation": str}"""

PROMPTS = {
    "mri": ("You are a radiology reporting assistant. Write a structured segmented-region description for a "
            "brain-MRI slice (FLAIR-based, lower-grade glioma data) from the automatic segmentation output below. "
            "Use only the numbers given; do not invent clinical history. State that the result is decision support "
            "and needs review by a radiologist."),
    "str": ("You are a forensic DNA reporting assistant. Write a structured STR match summary from the "
            "database search output below (likelihood ratios computed with theta correction and a typing-error "
            "model against synthetic reference profiles). Use only the numbers given and the verbal scale provided. "
            "State that conclusions need review by a qualified DNA analyst."),
    "dna": ("You are a bioinformatics assistant. Write a structured sequence-analysis summary from the model output "
            "below (k-mer JEPA encoder: STR repeat-type classifier, organism-class classifier with its held-out "
            "accuracy, and an exact tandem-repeat scan). Be explicit about model reliability using the accuracies given."),
}


def _call(model, prompt):
    r = requests.post(URL.format(model=model), params={"key": GEMINI_API_KEY}, timeout=45, json={
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    })
    if r.status_code != 200:
        raise RuntimeError(f"{model}: HTTP {r.status_code}")
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def _fallback(kind, data):
    """Plain deterministic summary used only when the Gemini API cannot be reached (clearly labelled)."""
    if kind == "mri":
        found = data.get("tumour_detected")
        meas = [{"name": "Tumour area", "value": f"{data.get('area_pixels')} px ({data.get('area_mm2')} mm2)"},
                {"name": "Share of brain area", "value": f"{data.get('percent_of_brain')}%"}]
        summary = (f"Segmented region of {data.get('area_mm2')} mm2 detected at the {data.get('location')}."
                   if found else "No tumour region above the 0.5 probability threshold was segmented.")
    elif kind == "str":
        top = (data.get("matches") or [{}])[0]
        meas = [{"name": "Top candidate", "value": str(top.get("id"))},
                {"name": "log10 LR", "value": str(top.get("log10_lr"))},
                {"name": "Loci compared", "value": str(top.get("loci_compared"))}]
        summary = f"Top-ranked reference {top.get('id')} with log10 LR {top.get('log10_lr')} ({top.get('verbal')})."
    else:
        rt = data.get("repeat_type", {})
        meas = [{"name": "Length", "value": str(data.get("sequence", {}).get("length"))},
                {"name": "GC %", "value": str(data.get("sequence", {}).get("gc_percent"))},
                {"name": "Repeat type", "value": f"{rt.get('prediction')} ({rt.get('confidence')})"}]
        summary = f"Predicted repeat type: {rt.get('prediction')}."
    return {"title": "Automatic summary", "summary": summary, "findings": [m["name"] + ": " + m["value"] for m in meas],
            "measurements": meas, "interpretation": "Generated without the AI report service (it was unreachable).",
            "limitations": ["AI report service unavailable - this is a plain summary of the model output."],
            "recommendation": "Retry the report later for a full structured narrative."}


_last_ok = {"model": None, "at": 0.0}


def generate(kind, data):
    payload = json.dumps(data, default=str)[:12000]
    prompt = f"{PROMPTS[kind]}\n\n{SCHEMA_HINT}\n\nModel output:\n{payload}"
    errors = []
    if GEMINI_API_KEY:
        models = [GEMINI_MODEL] + [m for m in GEMINI_FALLBACK_MODELS if m != GEMINI_MODEL]
        # while the primary model is overloaded, start with the model that answered in the last 10 minutes
        if _last_ok["model"] in models and time.time() - _last_ok["at"] < 600:
            models.remove(_last_ok["model"])
            models.insert(0, _last_ok["model"])
        for model in models + models[:1]:
            try:
                rep = _call(model, prompt)
                _last_ok.update(model=model, at=time.time())
                return {"source": "gemini", "model": model, "report": rep}
            except Exception as e:  # noqa: BLE001
                errors.append(str(e)[:120])
    return {"source": "fallback", "model": None, "errors": errors[-3:], "report": _fallback(kind, data)}
