"""
ai_insights.py
--------------
Generates plain-language, EDUCATIONAL explanations for abnormal lab
test results.

Design principles (per project requirements):
    - Never diagnoses a disease.
    - Never claims an abnormal value "confirms" a condition.
    - Always frames possible causes as general/possible, not certain.
    - Always surfaces the medical disclaimer.

Two explanation sources are supported:
    1. A curated rule-based knowledge base (`TEST_KNOWLEDGE`) covering
       common lab tests -- used by default, works fully offline.
    2. An optional LLM call (Anthropic API) that rewrites/extends the
       rule-based explanation in friendlier language. This is used only
       if ANTHROPIC_API_KEY is set in the environment (see .env.example)
       and `use_llm=True` is passed in. If the API call fails for any
       reason, the system falls back to the rule-based explanation --
       the app must never crash or leave a blank explanation because an
       external API was unavailable.
"""

import os
from dataclasses import dataclass

MEDICAL_DISCLAIMER = (
    "This application provides educational information only and does not "
    "provide medical diagnosis or treatment. Please consult a qualified "
    "healthcare professional for medical advice."
)


@dataclass
class HealthInsight:
    test_name: str
    status: str
    explanation: str
    possible_causes: str
    recommendations: str
    disclaimer: str = MEDICAL_DISCLAIMER


# ---------------------------------------------------------------------------
# Rule-based knowledge base
# ---------------------------------------------------------------------------
# Each entry: what the test measures, plus general (non-diagnostic) possible
# reasons for LOW and HIGH results. This is intentionally general-purpose
# educational content, not clinical decision support.

TEST_KNOWLEDGE = {
    "hemoglobin": {
        "measures": "the protein in red blood cells that carries oxygen through the body.",
        "low": "Low hemoglobin can generally be associated with iron or vitamin deficiency, "
               "recent blood loss, chronic illness, or being naturally lower in some people.",
        "high": "High hemoglobin can generally be associated with dehydration, living at high "
                "altitude, smoking, or certain lung/heart conditions.",
    },
    "wbc count": {
        "measures": "white blood cells, which are part of the body's immune/infection-fighting system.",
        "low": "A low white cell count can generally be associated with certain viral infections, "
               "some medications, or bone marrow-related conditions.",
        "high": "A high white cell count can generally be associated with infection, inflammation, "
                "stress on the body, or (less commonly) certain blood disorders.",
    },
    "platelet count": {
        "measures": "platelets, the blood cells responsible for clotting.",
        "low": "A low platelet count can generally be associated with certain infections, "
               "some medications, or conditions affecting the bone marrow or spleen.",
        "high": "A high platelet count can generally be associated with inflammation, recent "
                "infection, iron deficiency, or certain bone marrow conditions.",
    },
    "glucose": {
        "measures": "the amount of sugar circulating in the blood.",
        "low": "Low blood glucose can generally be associated with fasting, certain medications, "
               "or the body's insulin response.",
        "high": "High blood glucose can generally be associated with diet, stress, insulin "
                "resistance, or conditions affecting blood sugar regulation.",
    },
    "hba1c": {
        "measures": "average blood sugar levels over roughly the past 2-3 months.",
        "low": "A low HbA1c is less common and can generally relate to certain blood conditions "
               "or very tightly controlled blood sugar.",
        "high": "A high HbA1c can generally be associated with elevated blood sugar levels over "
                "an extended period.",
    },
    "total cholesterol": {
        "measures": "the total amount of cholesterol (a fat-like substance) in the blood.",
        "low": "Low total cholesterol is less common and can generally relate to diet, certain "
               "liver conditions, or naturally lower baseline levels.",
        "high": "High total cholesterol can generally be associated with diet, physical activity "
                "levels, genetics, or metabolic factors.",
    },
    "ldl cholesterol": {
        "measures": "'LDL' cholesterol, sometimes referred to informally in general terms as the less "
                    "favorable type of cholesterol carrier in the blood.",
        "low": "Low LDL is generally not a concern for most people and can relate to diet or medication.",
        "high": "High LDL can generally be associated with diet, activity levels, genetics, or "
                "metabolic factors.",
    },
    "hdl cholesterol": {
        "measures": "'HDL' cholesterol, sometimes referred to informally in general terms as the more "
                    "favorable type of cholesterol carrier in the blood.",
        "low": "Low HDL can generally be associated with lower physical activity, smoking, or "
               "certain metabolic factors.",
        "high": "High HDL is generally not considered a health concern for most people.",
    },
    "triglycerides": {
        "measures": "a type of fat in the blood used for energy.",
        "low": "Low triglycerides are uncommon and can relate to diet or certain conditions "
               "affecting fat absorption.",
        "high": "High triglycerides can generally be associated with diet, alcohol intake, "
                "physical activity levels, or metabolic factors.",
    },
    "creatinine": {
        "measures": "a waste product filtered by the kidneys, used as a general indicator of "
                    "kidney filtering function.",
        "low": "Low creatinine is generally less concerning and can relate to lower muscle mass.",
        "high": "High creatinine can generally be associated with reduced kidney filtering "
                "efficiency, dehydration, or certain medications.",
    },
    "urea": {
        "measures": "a waste product from protein breakdown, filtered by the kidneys.",
        "low": "Low urea can generally be associated with a low-protein diet or liver-related factors.",
        "high": "High urea can generally be associated with dehydration, high protein intake, "
                "or reduced kidney filtering efficiency.",
    },
    "tsh": {
        "measures": "thyroid-stimulating hormone, which regulates thyroid gland activity.",
        "low": "Low TSH can generally be associated with an overactive thyroid gland or certain medications.",
        "high": "High TSH can generally be associated with an underactive thyroid gland.",
    },
    "vitamin d": {
        "measures": "vitamin D levels, important for bone health and immune function.",
        "low": "Low vitamin D can generally be associated with limited sun exposure, diet, or "
               "how the body absorbs the vitamin.",
        "high": "High vitamin D is uncommon and can generally relate to excess supplementation.",
    },
    "vitamin b12": {
        "measures": "vitamin B12 levels, important for nerve function and red blood cell production.",
        "low": "Low B12 can generally be associated with diet (especially plant-based diets), "
               "or how the body absorbs the vitamin.",
        "high": "High B12 is generally less concerning and often relates to supplementation.",
    },
    "iron": {
        "measures": "the amount of iron circulating in the blood.",
        "low": "Low iron can generally be associated with diet, blood loss, or absorption factors.",
        "high": "High iron can generally be associated with supplementation or certain absorption conditions.",
    },
    "esr": {
        "measures": "erythrocyte sedimentation rate, a general marker of inflammation in the body.",
        "low": "A low ESR is generally not considered a health concern.",
        "high": "A high ESR can generally be associated with inflammation, infection, or "
                "recovery from illness -- it does not point to a specific cause on its own.",
    },
    "crp": {
        "measures": "C-reactive protein, a general marker of inflammation in the body.",
        "low": "A low CRP is generally not considered a health concern.",
        "high": "A high CRP can generally be associated with inflammation, infection, or tissue "
                "stress -- it does not point to a specific cause on its own.",
    },
}

_GENERIC_KNOWLEDGE = {
    "measures": "a value reported as part of your lab panel.",
    "low": "A result below the reference range can have a number of general, non-specific causes.",
    "high": "A result above the reference range can have a number of general, non-specific causes.",
}

GENERAL_RECOMMENDATION = (
    "Consider discussing this result with a doctor or qualified healthcare professional, "
    "especially if it is significantly outside the reference range, if you have symptoms, "
    "or if this is a new or unexpected change from your previous results."
)


def _lookup_knowledge(test_name: str) -> dict:
    key = test_name.strip().lower()
    return TEST_KNOWLEDGE.get(key, _GENERIC_KNOWLEDGE)


def generate_rule_based_insight(test_name: str, status: str) -> HealthInsight:
    """Build an explanation purely from the local knowledge base (no network calls)."""
    knowledge = _lookup_knowledge(test_name)

    if status == "LOW":
        cause_text = knowledge["low"]
    elif status == "HIGH":
        cause_text = knowledge["high"]
    else:
        cause_text = "This value falls within the expected range for this test."

    explanation = (
        f"{test_name} measures {knowledge['measures']} "
        f"Your result was flagged as {status.title()} compared to the standard reference range."
        if status in ("LOW", "HIGH")
        else f"{test_name} measures {knowledge['measures']}"
    )

    return HealthInsight(
        test_name=test_name,
        status=status,
        explanation=explanation,
        possible_causes=cause_text,
        recommendations=GENERAL_RECOMMENDATION if status in ("LOW", "HIGH") else
        "No specific action is typically needed for results within the normal range.",
    )


# ---------------------------------------------------------------------------
# Optional LLM enrichment (Anthropic API) -- fully optional, never required
# ---------------------------------------------------------------------------

def _call_llm_for_insight(test_name: str, status: str, base_insight: HealthInsight) -> str:
    """
    Ask an LLM to restate the rule-based explanation in warmer, plainer
    language. Returns the LLM text, or raises on any failure so the caller
    can fall back to the rule-based explanation untouched.

    Requires the ANTHROPIC_API_KEY environment variable to be set (loaded
    from a local .env file -- never hard-code the key in source).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    import anthropic  # imported lazily so the app runs fine without the package

    client = anthropic.Anthropic(api_key=api_key)

    prompt = (
        f"A lab test called '{test_name}' came back {status.upper()}. "
        f"Here is factual background: {base_insight.explanation} "
        f"Possible general causes: {base_insight.possible_causes} "
        "Rewrite this in 3-4 short, plain-language sentences for a general audience. "
        "Do NOT diagnose any disease or condition. Do NOT say the result confirms any "
        "illness. Stay general and educational, and do not invent new medical facts."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text_parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
    text = "\n".join(text_parts).strip()
    if not text:
        raise RuntimeError("Empty LLM response")
    return text


def generate_insight(test_name: str, status: str, use_llm: bool = False) -> HealthInsight:
    """
    Public entry point used by report_processor.py. Always returns a valid
    HealthInsight -- LLM enrichment is attempted only if requested and
    configured, and any failure silently falls back to the rule-based text.
    """
    base_insight = generate_rule_based_insight(test_name, status)

    if use_llm and status in ("LOW", "HIGH"):
        try:
            enriched_text = _call_llm_for_insight(test_name, status, base_insight)
            base_insight.explanation = enriched_text
        except Exception:
            # Fall back silently to the rule-based explanation -- an LLM
            # outage must never break report processing.
            pass

    return base_insight
