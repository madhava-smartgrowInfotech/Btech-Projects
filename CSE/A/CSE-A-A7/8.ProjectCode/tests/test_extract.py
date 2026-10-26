"""Unit tests for the report reader (negation, abbreviations, OCR run-ons, labs, pages)."""
import json
from pathlib import Path

import pytest

from app.services import extract

ROOT = Path(__file__).resolve().parents[1]


def flags(text, page=1):
    return {f for f, v in extract.parse([{"page": page, "text": text}])["flags"].items() if v}


def test_plain_symptom_and_finding():
    assert flags("Presents with chest pain. ECG shows ST elevation.") == {"chest_pain", "st_elevation"}


@pytest.mark.parametrize("text", ["Denies chest pain.", "No fever, no vomiting.", "Negative for fracture.", "Without bleeding."])
def test_negation_drops_flag(text):
    assert flags(text) == set()


@pytest.mark.xfail(strict=True, reason="known limitation: negation scope does not stop at 'but' (45-character window)")
def test_negation_is_clause_local():
    assert flags("Denies syncope but reports chest tightness.") == {"chest_pain"}


def test_abbreviations():
    assert {"dyspnea", "hypertension", "diabetes"} <= flags("SOB since morning. Known HTN and DM2.")


def test_ocr_run_on_words():
    assert {"dyspnea", "chest_pain"} <= flags("Complains of shortnessofbreath and chestpain.")


def test_brain_bleed_is_finding_not_symptom():
    f = flags("CT head shows subarachnoid haemorrhage.")
    assert "ct_hemorrhage" in f and "bleeding" not in f


@pytest.mark.parametrize("text,flag", [
    ("Troponin: 0.52 ng/mL", "lab_troponin_high"), ("Lactate 4.1", "lab_lactate_high"), ("WBC 15.2", "lab_wbc_high"),
    ("Glucose 310", "lab_glucose_abn"), ("Glucose 42", "lab_glucose_abn"), ("Creatinine 2.4", "lab_creatinine_high"),
    ("Hb 7.8 g/dL", "lab_hgb_low"),
])
def test_abnormal_labs_set_flag(text, flag):
    assert flag in flags(text)


def test_normal_labs_do_not_set_flags():
    assert flags("Glucose 95. WBC 7.4. Creatinine 0.9. Lactate 1.1. Troponin 0.01.") == set()


def test_items_keep_their_page():
    parsed = extract.parse([{"page": 1, "text": "Alert and well."}, {"page": 2, "text": "Chest pain for two hours."}])
    assert parsed["symptoms"][0]["page"] == 2


def test_unsupported_upload_rejected():
    with pytest.raises(ValueError):
        extract.read_pages(b"not a document", "x.txt")


def test_all_sample_reports_read_exactly():
    expected = json.loads((ROOT / "data" / "sample_reports" / "expected.json").read_text())
    for fname, exp in expected.items():
        rep = extract.extract_report((ROOT / "data" / "sample_reports" / fname).read_bytes(), fname)
        assert {f for f, v in rep["flags"].items() if v} == set(exp["flags"]), fname
