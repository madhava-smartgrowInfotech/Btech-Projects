"""
report_processor.py
--------------------
Orchestrates the full pipeline for a single uploaded report:

    upload -> OCR/text extraction -> NER structuring -> classification
    -> database persistence -> AI insight generation for abnormal results

This module is what app.py calls from the "Upload Report" page. Keeping
the orchestration here (rather than inline in the Streamlit page) makes
each stage independently testable and keeps app.py focused on UI.
"""

import os

from ocr_processor import extract_text, OCRError, get_file_extension
from ner_processor import extract_structured_tests
from result_analyzer import analyze_results
from ai_insights import generate_insight
import database as db


class ProcessingResult:
    """Simple container returned to the Streamlit UI after processing."""

    def __init__(self):
        self.report_id = None
        self.raw_text = ""
        self.classified_results = []
        self.stages_completed = []
        self.error = None
        self.status = "Pending"


def process_uploaded_report(filename: str, file_bytes: bytes, use_llm_insights: bool = False) -> ProcessingResult:
    """
    Run the full pipeline for one uploaded file and persist everything to
    the database. Returns a ProcessingResult the UI can render directly,
    including partial progress if a later stage fails.
    """
    result = ProcessingResult()
    ext = get_file_extension(filename).lstrip(".")

    # 1. Create the report row immediately so it shows up in history even
    #    if a later stage fails -- the user can see *what* went wrong.
    try:
        report_id = db.create_report(file_name=filename, file_type=ext)
        result.report_id = report_id
    except Exception as exc:
        result.error = f"Database error while creating report record: {exc}"
        return result

    db.update_report_status(report_id, "Processing")

    # 2. OCR / text extraction
    try:
        raw_text = extract_text(filename, file_bytes)
        result.raw_text = raw_text
        result.stages_completed.append("Text extraction")
    except OCRError as exc:
        db.update_report_status(report_id, "Failed", error_message=str(exc))
        result.error = str(exc)
        result.status = "Failed"
        return result
    except Exception as exc:
        msg = f"Unexpected error during text extraction: {exc}"
        db.update_report_status(report_id, "Failed", error_message=msg)
        result.error = msg
        result.status = "Failed"
        return result

    # 3. NER / structured extraction
    try:
        structured_tests = extract_structured_tests(raw_text)
        result.stages_completed.append("Test-value extraction")
    except Exception as exc:
        msg = f"Unexpected error during test extraction: {exc}"
        db.update_report_status(report_id, "Failed", error_message=msg, raw_text=raw_text)
        result.error = msg
        result.status = "Failed"
        return result

    if not structured_tests:
        msg = (
            "Text was extracted, but no recognizable lab test rows were found. "
            "The report format may not be supported yet, or the scan quality may be too low."
        )
        db.update_report_status(report_id, "Failed", error_message=msg, raw_text=raw_text)
        result.error = msg
        result.status = "Failed"
        return result

    # 4. Classification (LOW / NORMAL / HIGH)
    try:
        classified = analyze_results(structured_tests)
        result.stages_completed.append("Result classification")
    except Exception as exc:
        msg = f"Unexpected error during result classification: {exc}"
        db.update_report_status(report_id, "Failed", error_message=msg, raw_text=raw_text)
        result.error = msg
        result.status = "Failed"
        return result

    # 5. Persist test results
    try:
        result_dicts = [
            {
                "test_name": c.test_name,
                "result_value": c.result_value,
                "unit": c.unit,
                "reference_low": c.reference_low,
                "reference_high": c.reference_high,
                "status": c.status,
                "test_date": c.test_date,
                "confidence_score": c.confidence_score,
            }
            for c in classified
        ]
        new_ids = db.save_test_results(report_id, result_dicts)
        result.stages_completed.append("Database storage")
    except Exception as exc:
        msg = f"Database error while saving test results: {exc}"
        db.update_report_status(report_id, "Failed", error_message=msg, raw_text=raw_text)
        result.error = msg
        result.status = "Failed"
        return result

    # 6. Generate AI insights for abnormal results only
    try:
        for test_result_id, c in zip(new_ids, classified):
            if c.status in ("LOW", "HIGH"):
                insight = generate_insight(c.test_name, c.status, use_llm=use_llm_insights)
                db.save_health_insight(
                    test_result_id=test_result_id,
                    explanation=insight.explanation,
                    possible_causes=insight.possible_causes,
                    recommendations=insight.recommendations,
                )
        result.stages_completed.append("AI health insights")
    except Exception as exc:
        # Insights are a "nice to have" on top of the core numeric results --
        # a failure here should not mark the whole report as failed.
        result.stages_completed.append(f"AI health insights (partial: {exc})")

    db.update_report_status(report_id, "Completed", raw_text=raw_text)
    result.classified_results = classified
    result.status = "Completed"
    return result
