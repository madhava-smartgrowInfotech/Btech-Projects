"""
result_analyzer.py
-------------------
Classifies each extracted lab test result as LOW / NORMAL / HIGH (or
UNKNOWN when there isn't enough information) by comparing it against
its reference range.

Rules
-----
    result <  reference_low                 -> LOW
    reference_low <= result <= reference_high -> NORMAL
    result >  reference_high                 -> HIGH

    Only reference_high known (e.g. "<200")  -> HIGH if result > high else NORMAL
    Only reference_low known  (e.g. ">40")   -> LOW  if result < low  else NORMAL
    Neither bound known                      -> UNKNOWN
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ClassifiedResult:
    test_name: str
    result_value: Optional[float]
    unit: Optional[str]
    reference_low: Optional[float]
    reference_high: Optional[float]
    status: str  # LOW / NORMAL / HIGH / UNKNOWN
    test_date: object = None
    confidence_score: float = 0.0

    def reference_range_display(self) -> str:
        if self.reference_low is not None and self.reference_high is not None:
            return f"{self.reference_low} - {self.reference_high}"
        if self.reference_high is not None:
            return f"< {self.reference_high}"
        if self.reference_low is not None:
            return f"> {self.reference_low}"
        return "N/A"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["reference_range"] = self.reference_range_display()
        return d


def classify_result(result_value, reference_low, reference_high) -> str:
    """Pure classification function -- returns one of LOW/NORMAL/HIGH/UNKNOWN."""
    if result_value is None:
        return "UNKNOWN"

    if reference_low is not None and reference_high is not None:
        if result_value < reference_low:
            return "LOW"
        if result_value > reference_high:
            return "HIGH"
        return "NORMAL"

    if reference_high is not None:  # only an upper bound is known
        return "HIGH" if result_value > reference_high else "NORMAL"

    if reference_low is not None:  # only a lower bound is known
        return "LOW" if result_value < reference_low else "NORMAL"

    return "UNKNOWN"


def analyze_results(structured_tests: list) -> list:
    """
    Takes the list of dicts produced by ner_processor.extract_structured_tests
    and returns a list of ClassifiedResult objects (dicts via .as_dict()).
    """
    classified = []
    for t in structured_tests:
        status = classify_result(
            t.get("result_value"), t.get("reference_low"), t.get("reference_high")
        )
        classified.append(
            ClassifiedResult(
                test_name=t.get("test_name"),
                result_value=t.get("result_value"),
                unit=t.get("unit"),
                reference_low=t.get("reference_low"),
                reference_high=t.get("reference_high"),
                status=status,
                test_date=t.get("test_date"),
                confidence_score=t.get("confidence_score", 0.0),
            )
        )
    return classified


def summarize_statuses(classified_results: list) -> dict:
    """Quick counts used by the dashboard/report analysis pages."""
    summary = {"NORMAL": 0, "LOW": 0, "HIGH": 0, "UNKNOWN": 0}
    for r in classified_results:
        summary[r.status] = summary.get(r.status, 0) + 1
    return summary
