"""Investigator-style narratives from the evidence, written by Gemini and checked for grounding."""
import json
import re
import time

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL, GEMINI_TIMEOUT_SECONDS

SYSTEM = """You are a senior GST investigator writing a case note for colleagues in a tax-administration
analytics unit. You explain why a taxpayer was flagged for possible input-tax-credit (ITC) fraud.

Rules:
- Use ONLY the facts in the evidence list. Never invent numbers, names, dates or events.
- Cite evidence after each claim with its ID in square brackets, e.g. [E1] or [E2][E4].
- Plain, direct language an auditor can act on. No legal conclusions: this is a risk indication, not proof.
- Keep amounts in the same format as the evidence (₹ with L for lakh, Cr for crore).
- Output exactly these three sections in Markdown:
## Summary
(2-3 sentences: who, overall risk, the main pattern)
## Why it was flagged
(3-6 bullet points, strongest first, each with citations)
## Suggested next steps
(2-4 bullet points of concrete checks, e.g. verify e-way bills, confirm supplier existence, reconcile GSTR-2B)
Stay under 320 words."""


class ExplainError(Exception):
    pass


def build_prompt(tp, evidence, pattern_labels):
    profile = {k: tp[k] for k in ("legal_name", "gstin", "sector", "state", "constitution", "registration_date")}
    scores = {"overall_risk": tp["risk"], "rank": tp["rank"], "jepa_deviation": tp["jepa"],
              "behaviour_layer": tp["behaviour"], "network_layer": tp["network"], "invoice_layer": tp["invoice"]}
    patterns = [pattern_labels.get(p, p) for p in tp["patterns"]]
    ev = [{"id": e["id"], "layer": e["layer"], "severity": e["severity"], "title": e["title"], "detail": e["detail"]}
          for e in evidence]
    return (f"Taxpayer profile:\n{json.dumps(profile, ensure_ascii=False)}\n\n"
            f"Risk scores (0-1):\n{json.dumps(scores)}\n\nSuspected patterns: {', '.join(patterns) or 'none'}\n\n"
            f"Evidence list:\n{json.dumps(ev, ensure_ascii=False, indent=1)}\n\nWrite the case note.")


def generate(prompt):
    if not GEMINI_API_KEY:
        raise ExplainError("GEMINI_API_KEY is not set. Add it to .env (https://aistudio.google.com/apikey) "
                           "and restart the backend.")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY,
                          http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_SECONDS * 1000))
    errors = []
    for model in [GEMINI_MODEL] + [m for m in GEMINI_FALLBACK_MODELS if m != GEMINI_MODEL]:
        # thinking_budget=0 keeps 2.5 models fast; newer models manage thinking themselves
        attempts = [True, False] if "2.5" in model else [False]
        retried = False
        while attempts:
            thinking = attempts[0]
            cfg = dict(system_instruction=SYSTEM, temperature=0.2, max_output_tokens=2048)
            if thinking:
                cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            try:
                resp = client.models.generate_content(model=model, contents=prompt,
                                                      config=types.GenerateContentConfig(**cfg))
                text = (resp.text or "").strip()
                if text:
                    return text, model
                errors.append(f"{model}: empty response")
                break
            except Exception as e:
                msg = str(e)
                errors.append(f"{model}: {msg[:200]}")
                if not retried and ("503" in msg or "429" in msg):  # busy or rate-limited: one short retry
                    retried = True
                    time.sleep(3)
                    continue
                if thinking and ("thinking" in msg.lower() or "INVALID_ARGUMENT" in msg):
                    attempts.pop(0)  # try without the thinking config
                    continue
                break  # next model
    raise ExplainError("Gemini request failed - " + " | ".join(errors))


NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def check_quality(text, evidence):
    """Grounding checks: citation validity/coverage and whether the numbers used appear in the evidence."""
    ids = {e["id"] for e in evidence}
    cited = re.findall(r"\[(E\d+)\]", text)
    valid = [c for c in cited if c in ids]
    high = {e["id"] for e in evidence if e["severity"] == "high"}
    ev_text = " ".join(e["title"] + " " + e["detail"] for e in evidence)
    ev_nums = {n.replace(",", "") for n in NUM_RE.findall(ev_text)}
    body = re.sub(r"\[E\d+\]", "", text)
    nums = [n.replace(",", "") for n in NUM_RE.findall(body) if len(n.replace(",", "").replace(".", "")) >= 2]
    grounded = [n for n in nums if n in ev_nums]
    sections = all(h in text for h in ("## Summary", "## Why it was flagged", "## Suggested next steps"))
    return dict(
        citations=len(cited),
        invalid_citations=len(cited) - len(valid),
        evidence_coverage=round(len(set(valid)) / len(ids), 3) if ids else None,
        high_severity_coverage=round(len(set(valid) & high) / len(high), 3) if high else None,
        numbers=len(nums), numbers_grounded=len(grounded),
        numeric_grounding=round(len(grounded) / len(nums), 3) if nums else 1.0,
        has_sections=sections, words=len(body.split()))
