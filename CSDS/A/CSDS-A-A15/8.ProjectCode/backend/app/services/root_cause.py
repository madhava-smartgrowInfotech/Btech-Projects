"""Rule-based root-cause & corrective-action narrative generator.

Deterministic and fully offline: maps a detected defect type, its
confidence and Grad-CAM coverage onto the curated knowledge base in
app.ml.labels, and renders it into inspector-facing prose.
"""
from app.ml.labels import DEFECT_INFO

SEVERITY_COPY = {
    "low": "This is a minor occurrence with limited surface impact.",
    "medium": "This defect has moderate surface coverage and should be tracked for recurrence.",
    "high": "This defect covers a significant portion of the inspected region and warrants immediate attention.",
}


def build_root_cause_report(defect_type: str, confidence: float, severity: str) -> dict:
    info = DEFECT_INFO.get(defect_type, {})
    display_name = info.get("display_name", defect_type)
    causes = info.get("likely_causes", [])
    actions = info.get("corrective_actions", [])
    description = info.get("description", "")

    confidence_pct = round(confidence * 100, 1)
    severity_line = SEVERITY_COPY.get(severity, "")

    narrative_parts = [
        f"The inspection model classified this sample as {display_name} with {confidence_pct}% confidence. "
        f"{description}",
        severity_line,
        "Based on known process-failure patterns for this defect category, the most probable root causes are:",
    ]
    for i, cause in enumerate(causes, start=1):
        narrative_parts.append(f"{i}. {cause}")

    narrative_parts.append(
        "Recommended corrective actions to resolve and prevent recurrence:"
    )

    root_cause_text = "\n".join(p for p in narrative_parts if p)

    return {
        "root_cause_text": root_cause_text,
        "corrective_actions": actions,
    }
