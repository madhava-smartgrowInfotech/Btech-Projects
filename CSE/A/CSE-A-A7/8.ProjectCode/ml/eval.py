"""Evaluation numbers for the objectives: triage accuracy against recorded priority, per-class recall,
report-reading quality, and processing seconds per patient (report reading + model, end to end).

Writes experiments/eval/metrics.json.   Run:  venv\\Scripts\\python ml\\eval.py
"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import extract, triage  # noqa: E402


def main():
    model = json.loads((ROOT / "experiments" / "metrics.json").read_text())
    expected = json.loads((ROOT / "data" / "sample_reports" / "expected.json").read_text())
    extract._ocr()  # engine start-up is a one-off, keep it out of the per-patient timing
    triage.predict(next(iter(expected.values()))["vitals"], {})

    tp = fp = fn = 0
    per_patient = []
    exact = 0
    for fname, exp in expected.items():
        data = (ROOT / "data" / "sample_reports" / fname).read_bytes()
        t0 = time.time()
        rep = extract.extract_report(data, fname)
        res = triage.predict(exp["vitals"], rep["flags"])
        per_patient.append(time.time() - t0)
        got = {f for f, v in rep["flags"].items() if v}
        want = set(exp["flags"])
        tp, fp, fn = tp + len(got & want), fp + len(got - want), fn + len(want - got)
        exact += got == want
    out = {
        "triage_model": {k: model[k] for k in ("data", "n_test", "accuracy", "within_one_priority", "macro_f1",
                                                "per_class_recall", "model_seconds_per_patient")},
        "report_reading": {
            "reports": len(expected),
            "precision": round(tp / max(tp + fp, 1), 4),
            "recall": round(tp / max(tp + fn, 1), 4),
            "reports_read_exactly": exact,
            "note": "sample reports are generated; they test the pipeline, not real-world scan variety",
        },
        "end_to_end_seconds_per_patient": {
            "mean": round(statistics.mean(per_patient), 3),
            "median": round(statistics.median(per_patient), 3),
            "max": round(max(per_patient), 3),
        },
    }
    dest = ROOT / "experiments" / "eval"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
