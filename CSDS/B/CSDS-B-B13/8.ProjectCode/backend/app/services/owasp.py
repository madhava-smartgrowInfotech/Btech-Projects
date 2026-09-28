"""OWASP API Security Top 10 (2023) catalog, severity weights and scoring."""

OWASP_TOP10 = {
    "API1": "Broken Object Level Authorization",
    "API2": "Broken Authentication",
    "API3": "Broken Object Property Level Authorization",
    "API4": "Unrestricted Resource Consumption",
    "API5": "Broken Function Level Authorization",
    "API6": "Unrestricted Access to Sensitive Business Flows",
    "API7": "Server Side Request Forgery",
    "API8": "Security Misconfiguration",
    "API9": "Improper Inventory Management",
    "API10": "Unsafe Consumption of APIs",
}

# Points removed from a starting 100 for each finding of a given severity.
SEVERITY_WEIGHT = {
    "critical": 8,
    "high": 6,
    "medium": 2,
    "low": 1,
    "info": 0,
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def owasp_name(owasp_id: str) -> str:
    return OWASP_TOP10.get(owasp_id, "Uncategorised")


def grade_for(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 35:
        return "D"
    return "F"


def compute_score(findings: list[dict]) -> tuple[int, str]:
    """Weighted score: start at 100 and subtract each finding's severity weight.
    Clamped to 0-100. Grade bands are defined in grade_for()."""
    score = 100
    for f in findings:
        score -= SEVERITY_WEIGHT.get(f.get("severity", "info"), 0)
    score = max(0, min(100, score))
    return score, grade_for(score)


def severity_counts(findings: list[dict]) -> dict:
    counts = {k: 0 for k in SEVERITY_WEIGHT}
    for f in findings:
        sev = f.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
    return counts
