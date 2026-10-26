"""
run_experiments.py
------------------
Measures the real LabLens pipeline on a labelled synthetic corpus and writes
experiments/lablens/metrics.json plus figures in docs/figures/.

The project ships no evaluation data, so the corpus is generated here with known
ground truth: synthetic lab-report PDFs (with a text layer) in several layouts, rendered
with PyMuPDF and pushed through the unchanged ocr_processor -> ner_processor ->
result_analyzer -> ai_insights code. Nothing here is real patient data.

Run from the project root:  python -X utf8 scripts/run_experiments.py
All database writes go to a temporary SQLite file, never data/medical_lab.db.
"""

import difflib
import json
import os
import platform
import random
import statistics
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pymupdf  # noqa: E402
import numpy as np  # noqa: E402

import ner_processor as ner  # noqa: E402
import ocr_processor as ocr  # noqa: E402
import result_analyzer as ra  # noqa: E402
import ai_insights as ai  # noqa: E402

OUT_DIR = ROOT / "experiments" / "lablens"
FIG_DIR = ROOT / "docs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)
SEED = 42

# name, unit as printed on a real report, low, high  (units deliberately NOT limited to the regex list)
TESTS = [
    ("Hemoglobin", "g/dL", 12.0, 16.0), ("Hematocrit", "%", 36.0, 46.0), ("RBC Count", "10^6/uL", 4.0, 5.5),
    ("WBC Count", "10^3/uL", 4.0, 11.0), ("Platelet Count", "10^3/uL", 150, 400), ("MCV", "fL", 80, 100),
    ("MCH", "pg", 27, 33), ("MCHC", "g/dL", 32, 36), ("RDW", "%", 11.5, 14.5), ("Glucose", "mg/dL", 70, 99),
    ("HbA1c", "%", 4.0, 5.6), ("Total Cholesterol", "mg/dL", 125, 200), ("LDL Cholesterol", "mg/dL", "<", 100),
    ("HDL Cholesterol", "mg/dL", ">", 40), ("Triglycerides", "mg/dL", "<", 150), ("Urea", "mg/dL", 15, 40),
    ("Creatinine", "mg/dL", 0.6, 1.3), ("Uric Acid", "mg/dL", 3.5, 7.2), ("Sodium", "mEq/L", 135, 145),
    ("Potassium", "mEq/L", 3.5, 5.1), ("Chloride", "mEq/L", 98, 107), ("Calcium", "mg/dL", 8.6, 10.2),
    ("Phosphorus", "mg/dL", 2.5, 4.5), ("Magnesium", "mg/dL", 1.7, 2.2), ("Total Protein", "g/dL", 6.0, 8.3),
    ("Albumin", "g/dL", 3.5, 5.0), ("Bilirubin Total", "mg/dL", 0.2, 1.2), ("SGOT", "U/L", 5, 40),
    ("SGPT", "U/L", 7, 56), ("Alkaline Phosphatase", "U/L", 44, 147), ("GGT", "U/L", 8, 61),
    ("TSH", "uIU/mL", 0.4, 4.0), ("Vitamin D", "ng/mL", 30, 100), ("Vitamin B12", "pg/mL", 200, 900),
    ("Iron", "ug/dL", 60, 170), ("Ferritin", "ng/mL", 15, 200), ("ESR", "mm/hr", 0, 20), ("CRP", "mg/L", "<", 5),
    ("PSA", "ng/mL", "<", 4), ("Free T4", "ng/dL", 0.8, 1.8), ("Free T3", "pg/mL", 2.0, 4.4),
]
# tests that are not in KNOWN_TEST_NAMES (to measure what the dictionary snap does to unseen names)
OOD_TESTS = [
    ("Lipase", "U/L", 13, 60), ("Amylase", "U/L", 28, 100), ("Homocysteine", "umol/L", 5, 15),
    ("Lactate", "mmol/L", 0.5, 2.2), ("Sodium Bicarbonate", "mEq/L", 22, 29), ("Ammonia", "ug/dL", 15, 45),
    ("Cortisol", "ug/dL", 6, 23), ("Folate", "ng/mL", 3.0, 17.0),
]
DECOYS = [
    "Patient Name: Rahul Sharma", "Age/Sex: 34 Y / Male", "Registration No: 20458", "Ref. By: Dr. K. Rao",
    "Phone: 98480 12345",
]


def fmt(v):
    return f"{v:g}"


def rng_range(low, high):
    if low == "<":
        return f"<{fmt(high)}"
    if low == ">":
        return f">{fmt(high)}"
    return f"{fmt(low)} - {fmt(high)}"


def draw_value(rnd, low, high):
    """Draw a value: ~55% inside the range, ~25% below, ~20% above (one-sided limits use the limit only)."""
    r = rnd.random()
    if low == "<":
        v = high * (rnd.uniform(0.35, 0.98) if r < 0.7 else rnd.uniform(1.02, 1.8))
    elif low == ">":
        v = high * (rnd.uniform(1.02, 1.6) if r < 0.7 else rnd.uniform(0.5, 0.98))
    else:
        span = high - low
        if r < 0.55:
            v = rnd.uniform(low + 0.05 * span, high - 0.05 * span)
        elif r < 0.80:
            v = low - rnd.uniform(0.04, 0.35) * span if low > 0.5 * span else low * rnd.uniform(0.4, 0.96)
        else:
            v = high + rnd.uniform(0.04, 0.35) * span
    v = max(v, 0.1)
    return round(v) if v >= 100 else round(v, 1)


def gt_bounds(low, high):
    if low == "<":
        return None, float(high)
    if low == ">":
        return float(high), None
    return float(low), float(high)


# --------------------------------------------------------------------------- noise (for names)
CONF = {"o": "0", "0": "o", "l": "1", "1": "l", "i": "1", "s": "5", "S": "5", "B": "8", "e": "c", "a": "o", "m": "rn"}


def add_noise(name, rate, rnd):
    out = []
    for ch in name:
        if ch != " " and rnd.random() < rate:
            p = rnd.random()
            if p < 0.6 and ch in CONF:
                out.append(CONF[ch])
            elif p < 0.85:
                continue
            else:
                out.append(rnd.choice("abcdefghilmnorstu"))
                out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


# --------------------------------------------------------------------------- layouts
def cells_row(test, v, flag, layout, rnd):
    name, unit, low, high = test
    rg = rng_range(low, high)
    if layout == "plain":
        return [f"{name} {fmt(v)} {unit} {rg}"]
    if layout == "paren":
        return [f"{name} {fmt(v)} {unit} ({rg})"]
    if layout == "flag":
        return [f"{name} {fmt(v)} {flag} {unit} {rg}".replace("  ", " ")]
    if layout == "colon":
        return [f"{name}: {fmt(v)} {unit}   Ref: {rg}"]
    if layout == "unit_last":
        return [f"{name} {fmt(v)} {rg} {unit}"]
    if layout == "mixed_sep":
        sep = rnd.choice([" - ", " to ", "-"])
        rg2 = rg if low in ("<", ">") else f"{fmt(low)}{sep}{fmt(high)}"
        return [f"{name} {fmt(v)} {unit} {rg2}"]
    if layout == "tabular":
        return [name, fmt(v), unit, rg]  # one text cell each, placed in columns
    if layout == "ocr_noise":
        return [f"{add_noise(name, 0.10, rnd)} {fmt(v)} {unit} {rg}"]
    raise ValueError(layout)


LAYOUTS = ["plain", "paren", "flag", "colon", "unit_last", "mixed_sep", "tabular", "ocr_noise"]
COLS = [56, 230, 300, 380]


def render(rows, layout, header_lines):
    doc = pymupdf.open()
    page = doc.new_page()
    y = 60
    page.insert_text((56, y), "Sample Diagnostics - Laboratory Report", fontsize=14)
    y += 24
    for h in header_lines:
        page.insert_text((56, y), h, fontsize=10)
        y += 15
    y += 8
    if layout == "tabular":
        for x, t in zip(COLS, ["Test Name", "Result", "Unit", "Reference Range"]):
            page.insert_text((x, y), t, fontsize=10)
        y += 18
    for cells in rows:
        if layout == "tabular":
            for x, t in zip(COLS, cells):
                page.insert_text((x, y), t, fontsize=10)
        else:
            page.insert_text((56, y), cells[0], fontsize=10)
        y += 17
        if y > 780:
            page = doc.new_page()
            y = 60
    data = doc.tobytes()
    doc.close()
    return data


def build_corpus(per_layout=15, n_in=12, n_ood=2):
    rnd = random.Random(SEED)
    corpus = []
    for layout in LAYOUTS:
        for i in range(per_layout):
            picks = rnd.sample(TESTS, n_in)
            ood = rnd.sample(OOD_TESTS, n_ood)
            rows_gt, cell_rows = [], []
            order = picks + ood
            rnd.shuffle(order)
            for t in order:
                v = draw_value(rnd, t[2], t[3])
                lo, hi = gt_bounds(t[2], t[3])
                status = ra.classify_result(v, lo, hi)
                flag = {"LOW": "L", "HIGH": "H", "NORMAL": ""}[status]
                cell_rows.append(cells_row(t, v, flag, layout, rnd))
                rows_gt.append({"name": t[0], "in_dict": t in picks, "value": float(v), "unit": t[1],
                                "low": lo, "high": hi, "status": status})
            dfmt = "%d/%m/%Y" if i % 2 == 0 else "%d-%m-%Y"
            header = [rnd.choice(DECOYS), rnd.choice(DECOYS), f"Sample Collected: 12{dfmt[2:].replace('%m', '04').replace('%Y', '2026')} 10:30"]
            pdf = render(cell_rows, layout, header)
            corpus.append({"layout": layout, "id": f"{layout}_{i:02d}", "pdf": pdf, "gt": rows_gt})
    return corpus


# --------------------------------------------------------------------------- experiment A: extraction
def feq(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) < 1e-9


def norm_unit(u):
    return (u or "").replace("µ", "u").replace("μ", "u").lower()


def evaluate_report(item):
    text = ocr.extract_text(item["id"] + ".pdf", item["pdf"])
    pred = ra.analyze_results(ner.extract_structured_tests(text))
    gt = item["gt"]
    used = set()
    stats = Counter()
    failures = []
    for g in gt:
        hit = None
        for j, p in enumerate(pred):
            if j not in used and feq(p.result_value, g["value"]):
                hit = j
                break
        stats["gt_rows"] += 1
        if g["in_dict"]:
            stats["gt_rows_dict"] += 1
        else:
            stats["gt_rows_ood"] += 1
        if hit is None:
            failures.append({"report": item["id"], "kind": "missed row", "gt": g["name"], "value": g["value"]})
            continue
        used.add(hit)
        p = pred[hit]
        stats["detected"] += 1
        name_ok = p.test_name.lower() == g["name"].lower()
        unit_ok = norm_unit(p.unit) == norm_unit(g["unit"])
        range_ok = feq(p.reference_low, g["low"]) and feq(p.reference_high, g["high"])
        status_ok = p.status == g["status"]
        for key, ok in (("name_ok", name_ok), ("unit_ok", unit_ok), ("range_ok", range_ok), ("status_ok", status_ok)):
            if ok:
                stats[key] += 1
                if g["in_dict"]:
                    stats[key + "_dict"] += 1
                else:
                    stats[key + "_ood"] += 1
        if g["in_dict"]:
            stats["detected_dict"] += 1
        else:
            stats["detected_ood"] += 1
        if name_ok and unit_ok and range_ok and status_ok:
            stats["exact"] += 1
        else:
            bad = [k for k, ok in (("name", name_ok), ("unit", unit_ok), ("range", range_ok), ("status", status_ok)) if not ok]
            failures.append({"report": item["id"], "kind": "field error: " + ",".join(bad), "gt": g["name"],
                             "gt_unit": g["unit"], "value": g["value"], "pred_name": p.test_name, "pred_unit": p.unit,
                             "pred_low": p.reference_low, "pred_high": p.reference_high, "pred_status": p.status})
    stats["pred_rows"] += len(pred)
    for j, p in enumerate(pred):
        if j not in used:
            stats["false_positive"] += 1
            failures.append({"report": item["id"], "kind": "false positive row", "pred_name": p.test_name,
                             "value": p.result_value, "pred_low": p.reference_low, "pred_high": p.reference_high})
    return stats, failures, text


def ratio(a, b):
    return round(a / b, 4) if b else None


def summarize(stats):
    tp, gtn, pn = stats["detected"], stats["gt_rows"], stats["pred_rows"]
    prec, rec = ratio(tp, pn), ratio(tp, gtn)
    f1 = round(2 * prec * rec / (prec + rec), 4) if prec and rec else 0.0
    d = stats["detected"]
    return {
        "reports_rows": gtn, "predicted_rows": pn, "row_precision": prec, "row_recall": rec, "row_f1": f1,
        "name_acc": ratio(stats["name_ok"], d), "unit_acc": ratio(stats["unit_ok"], d),
        "range_acc": ratio(stats["range_ok"], d), "status_acc": ratio(stats["status_ok"], d),
        "exact_row_rate": ratio(stats["exact"], gtn),
        "name_acc_dict_tests": ratio(stats["name_ok_dict"], stats["detected_dict"]),
        "name_acc_ood_tests": ratio(stats["name_ok_ood"], stats["detected_ood"]),
        "false_positive_rows": stats["false_positive"],
    }


def experiment_extraction(corpus):
    per_layout = defaultdict(Counter)
    total = Counter()
    failures = []
    for item in corpus:
        s, f, _ = evaluate_report(item)
        per_layout[item["layout"]].update(s)
        total.update(s)
        failures.extend(f)
    res = {"overall": summarize(total), "per_layout": {k: summarize(v) for k, v in per_layout.items()}}
    kinds = Counter(f["kind"] for f in failures)
    res["failure_kinds"] = dict(kinds)
    return res, failures


# --------------------------------------------------------------------------- experiment B: name normalisation
SYNONYMS = {
    "Hb": "Hemoglobin", "Hgb": "Hemoglobin", "Haemoglobin": "Hemoglobin", "Blood Sugar Fasting": "Fasting Glucose",
    "Total Leucocyte Count": "WBC Count", "TLC": "WBC Count", "Platelets": "Platelet Count",
    "SGPT (ALT)": "SGPT", "Serum Creatinine": "Creatinine", "Cholesterol Total": "Total Cholesterol",
    "LDL": "LDL Cholesterol", "HDL": "HDL Cholesterol", "Triglyceride": "Triglycerides",
    "Urea Nitrogen": "Blood Urea Nitrogen", "Vitamin B-12": "Vitamin B12", "Total Bilirubin": "Bilirubin Total",
    "Serum Sodium": "Sodium", "Glycosylated Hemoglobin": "HbA1c", "Red Blood Cell Count": "RBC Count",
}
OOD_NAMES = [t[0] for t in OOD_TESTS] + [
    "Amylase Pancreatic", "Lipoprotein (a)", "Apolipoprotein B", "Zinc", "Copper", "Selenium", "Troponin I",
    "D-Dimer", "Fibrinogen", "Procalcitonin", "Insulin Fasting", "Cystatin C", "Bicarbonate", "Anion Gap",
    "Osmolality", "Reticulocyte Count",
]


def sim_matrix():
    return ner._TEST_NAME_VECTORIZER, ner._KNOWN_NAME_VECTORS


def tfidf_pred(raw, thr):
    from sklearn.metrics.pairwise import cosine_similarity
    vec, mat = sim_matrix()
    cleaned = ner.re.sub(r"[^A-Za-z0-9/() %]", " ", raw)
    cleaned = ner.re.sub(r"\s+", " ", cleaned).strip(" :.-")
    s = cosine_similarity(vec.transform([cleaned]), mat)[0]
    i = int(s.argmax())
    return (ner.KNOWN_TEST_NAMES[i] if s[i] >= thr else None), float(s[i])


def difflib_pred(raw, thr=0.6):
    best, bs = None, 0.0
    for k in ner.KNOWN_TEST_NAMES:
        r = difflib.SequenceMatcher(None, raw.lower(), k.lower()).ratio()
        if r > bs:
            best, bs = k, r
    return best if bs >= thr else None


def experiment_names():
    rnd = random.Random(SEED + 1)
    names = ner.KNOWN_TEST_NAMES
    out = {"n_dictionary_names": len(names), "trials_per_name": 30, "noise": {}, "threshold_sweep": [], "synonyms": {}}
    for rate in (0.0, 0.05, 0.10, 0.20):
        trials = [(n, add_noise(n, rate, rnd)) for n in names for _ in range(30)]
        acc_t = np.mean([tfidf_pred(raw, ner.FUZZY_MATCH_THRESHOLD)[0] == n for n, raw in trials])
        acc_d = np.mean([difflib_pred(raw) == n for n, raw in trials])
        acc_e = np.mean([raw.lower() == n.lower() for n, raw in trials])
        out["noise"][str(rate)] = {"tfidf_0.55": round(float(acc_t), 4), "difflib_0.60": round(float(acc_d), 4),
                                   "exact_match": round(float(acc_e), 4)}
    trials10 = [(n, add_noise(n, 0.10, rnd)) for n in names for _ in range(30)]
    trials20 = [(n, add_noise(n, 0.20, rnd)) for n in names for _ in range(30)]
    for thr in [round(x, 2) for x in np.arange(0.30, 0.86, 0.05)]:
        a10 = np.mean([tfidf_pred(r, thr)[0] == n for n, r in trials10])
        a20 = np.mean([tfidf_pred(r, thr)[0] == n for n, r in trials20])
        fs = np.mean([tfidf_pred(r, thr)[0] is not None for r in OOD_NAMES])
        sy = np.mean([tfidf_pred(r, thr)[0] == c for r, c in SYNONYMS.items()])
        out["threshold_sweep"].append({"threshold": thr, "acc_noise_10": round(float(a10), 4),
                                       "acc_noise_20": round(float(a20), 4), "false_snap_rate_ood": round(float(fs), 4),
                                       "synonym_acc": round(float(sy), 4)})
    # at the shipped threshold, which synonyms / unseen names are handled
    thr = ner.FUZZY_MATCH_THRESHOLD
    out["synonyms"] = {"n": len(SYNONYMS), "shipped_threshold": thr,
                       "correct": [r for r, c in SYNONYMS.items() if tfidf_pred(r, thr)[0] == c],
                       "wrong_or_unmatched": {r: tfidf_pred(r, thr)[0] for r, c in SYNONYMS.items() if tfidf_pred(r, thr)[0] != c}}
    out["ood_names"] = {"n": len(OOD_NAMES), "shipped_threshold": thr,
                        "wrongly_snapped": {r: tfidf_pred(r, thr)[0] for r in OOD_NAMES if tfidf_pred(r, thr)[0] is not None}}
    return out


# --------------------------------------------------------------------------- experiment C: classification
def experiment_classification():
    rnd = random.Random(SEED + 2)
    cases = 0
    wrong = 0
    for _ in range(20000):
        low = rnd.choice([None, round(rnd.uniform(0, 100), 1)])
        high = rnd.choice([None, round((low or 0) + rnd.uniform(1, 100), 1)])
        v = round(rnd.uniform(-5, 250), 1)
        if low is not None and high is not None:
            exp = "LOW" if v < low else "HIGH" if v > high else "NORMAL"
        elif high is not None:
            exp = "HIGH" if v > high else "NORMAL"
        elif low is not None:
            exp = "LOW" if v < low else "NORMAL"
        else:
            exp = "UNKNOWN"
        cases += 1
        wrong += ra.classify_result(v, low, high) != exp
    boundary = [ra.classify_result(5, 5, 10), ra.classify_result(10, 5, 10), ra.classify_result(4.99, 5, 10),
                ra.classify_result(10.01, 5, 10)]
    return {"random_cases": cases, "disagreements_with_reference_rule": int(wrong),
            "boundary_5_in_5to10": boundary[0], "boundary_10_in_5to10": boundary[1],
            "just_below": boundary[2], "just_above": boundary[3]}


# --------------------------------------------------------------------------- experiment D: insight coverage
def experiment_insights(corpus):
    kb = set(ai.TEST_KNOWLEDGE)
    dict_names = [n.lower() for n in ner.KNOWN_TEST_NAMES]
    covered = [n for n in dict_names if n in kb]
    abnormal = specific = 0
    for item in corpus:
        for g in item["gt"]:
            if g["status"] in ("LOW", "HIGH") and g["in_dict"]:
                abnormal += 1
                specific += g["name"].lower() in kb
    return {"knowledge_base_entries": len(kb), "dictionary_tests": len(dict_names),
            "dictionary_tests_with_specific_text": len(covered),
            "coverage_of_dictionary": round(len(covered) / len(dict_names), 4),
            "abnormal_dictionary_rows_in_corpus": abnormal, "abnormal_rows_with_specific_text": specific,
            "abnormal_rows_specific_rate": round(specific / abnormal, 4)}


# --------------------------------------------------------------------------- experiment E: latency
def timeit(fn, n):
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t) * 1000)
    return {"mean_ms": round(statistics.mean(ts), 2), "median_ms": round(statistics.median(ts), 2),
            "p95_ms": round(float(np.percentile(ts, 95)), 2), "max_ms": round(max(ts), 2), "n": n}


def experiment_latency(corpus):
    import database as db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import report_processor as rp
    from models import Base

    tmpdb = Path(tempfile.mkdtemp(prefix="lablens_exp_")) / "scratch.db"
    db.engine = create_engine(f"sqlite:///{tmpdb}", connect_args={"check_same_thread": False})
    db.SessionLocal = sessionmaker(bind=db.engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=db.engine)

    from backend.demo_data import render_pdf
    from datetime import datetime
    pdf = render_pdf(2, datetime(2026, 8, 2))  # the 14-row demo report
    text = ocr.extract_text("r.pdf", pdf)
    structured = ner.extract_structured_tests(text)
    classified = ra.analyze_results(structured)
    res = {"report_rows": len(structured), "pdf_bytes": len(pdf)}
    res["text_layer_extraction"] = timeit(lambda: ocr.extract_text("r.pdf", pdf), 100)
    res["field_extraction"] = timeit(lambda: ner.extract_structured_tests(text), 100)
    res["classification"] = timeit(lambda: ra.analyze_results(structured), 100)
    res["insight_generation_all_abnormal"] = timeit(
        lambda: [ai.generate_insight(c.test_name, c.status) for c in classified if c.status in ("LOW", "HIGH")], 100)
    res["end_to_end_pipeline_with_db"] = timeit(lambda: rp.process_uploaded_report("r.pdf", pdf), 40)
    # scaling with report length (text only)
    scale = {}
    base = [c for c in corpus if c["layout"] == "plain"][0]
    for n_lines in (14, 50, 100, 200):
        lines = []
        rnd = random.Random(1)
        while len(lines) < n_lines:
            t = rnd.choice(TESTS)
            lines.append(f"{t[0]} {fmt(draw_value(rnd, t[2], t[3]))} {t[1]} {rng_range(t[2], t[3])}")
        txt = "\n".join(lines)
        scale[str(n_lines)] = timeit(lambda: ner.extract_structured_tests(txt), 30)
    res["field_extraction_scaling_by_rows"] = scale
    # image path availability
    res["tesseract_available"] = ocr.pytesseract is not None and bool(__import__("shutil").which("tesseract"))
    # large file guard
    return res


def make_figures(extraction, names, latency):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "serif", "font.size": 10})
    # fig 1: per-layout metrics
    lay = extraction["per_layout"]
    order = [k for k in LAYOUTS]
    x = np.arange(len(order))
    w = 0.2
    fig, ax = plt.subplots(figsize=(8.6, 4.0), dpi=150)
    series = [("row_recall", "Row recall"), ("row_precision", "Row precision"), ("unit_acc", "Unit accuracy"), ("exact_row_rate", "Exact-row rate")]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]
    for i, (k, lab) in enumerate(series):
        ax.bar(x + (i - 1.5) * w, [lay[o][k] or 0 for o in order], w, label=lab, color=colors[i])
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=20)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Field extraction by report layout (synthetic corpus)")
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.24), frameon=False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_extraction_by_layout.png", bbox_inches="tight")
    plt.close(fig)
    # fig 2: threshold sweep
    sw = names["threshold_sweep"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    th = [s["threshold"] for s in sw]
    ax.plot(th, [s["acc_noise_10"] for s in sw], "o-", label="Accuracy, 10% char noise")
    ax.plot(th, [s["acc_noise_20"] for s in sw], "s-", label="Accuracy, 20% char noise")
    ax.plot(th, [s["false_snap_rate_ood"] for s in sw], "^-", label="False-snap rate, unseen names")
    ax.plot(th, [s["synonym_acc"] for s in sw], "d-", label="Synonym accuracy")
    ax.axvline(0.55, color="gray", ls="--", lw=1)
    ax.text(0.555, 0.03, "shipped 0.55", fontsize=8, color="gray")
    ax.set_xlabel("TF-IDF cosine threshold")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    ax.set_title("Test-name matcher threshold analysis")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_threshold_sweep.png", bbox_inches="tight")
    plt.close(fig)
    # fig 3: noise robustness
    nz = names["noise"]
    fig, ax = plt.subplots(figsize=(6.0, 3.6), dpi=150)
    rates = list(nz)
    xs = np.arange(len(rates))
    for i, (k, lab) in enumerate([("tfidf_0.55", "TF-IDF char n-gram (shipped)"), ("difflib_0.60", "difflib ratio (baseline)"), ("exact_match", "Exact match")]):
        ax.bar(xs + (i - 1) * 0.26, [nz[r][k] for r in rates], 0.26, label=lab)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{float(r) * 100:.0f}%" for r in rates])
    ax.set_xlabel("Simulated per-character OCR noise")
    ax.set_ylabel("Name accuracy")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_name_noise.png", bbox_inches="tight")
    plt.close(fig)
    # fig 4: latency by stage
    stages = [("text_layer_extraction", "PDF text layer"), ("field_extraction", "Field extraction"), ("classification", "Classification"),
              ("insight_generation_all_abnormal", "Insights (9 abnormal)"), ("end_to_end_pipeline_with_db", "End-to-end + DB")]
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=150)
    vals = [latency[k]["median_ms"] for k, _ in stages]
    ax.barh([l for _, l in stages], vals, color="#1f77b4")
    for i, v in enumerate(vals):
        ax.text(v, i, f" {v:.2f} ms" if v < 10 else f" {v:.1f} ms", va="center", fontsize=8)
    ax.set_xlabel("Median latency (ms)")
    ax.set_xlim(0, max(vals) * 1.25)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_latency_stages.png")
    plt.close(fig)


def main():
    t0 = time.time()
    corpus = build_corpus()
    extraction, failures = experiment_extraction(corpus)
    names = experiment_names()
    cls = experiment_classification()
    ins = experiment_insights(corpus)
    lat = experiment_latency(corpus)
    make_figures(extraction, names, lat)
    metrics = {
        "protocol": {
            "corpus": "synthetic, generated with seed %d: %d reports (%d layouts x 15), 12 dictionary tests + 2 unseen tests each, "
                      "plus header decoys and a date line" % (SEED, len(corpus), len(LAYOUTS)),
            "labels": "generated ground truth (not manually labelled real reports)",
            "pdf_text_layer_only": True,
            "machine": {"cpu": platform.processor(), "python": platform.python_version(), "platform": platform.platform()},
            "wall_seconds": round(time.time() - t0, 1),
        },
        "extraction": extraction, "name_normalisation": names, "classification": cls,
        "insight_coverage": ins, "latency": lat,
    }
    (OUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    # failure cases (capped) for the write-up
    by_kind = defaultdict(list)
    for f in failures:
        by_kind[f["kind"]].append(f)
    sample = {k: v[:6] for k, v in by_kind.items()}
    (OUT_DIR / "failure_cases.json").write_text(json.dumps(sample, indent=2, default=str), encoding="utf-8")
    # one example of raw extracted text per layout (for the write-up)
    ex = {}
    for item in corpus:
        if item["layout"] not in ex:
            ex[item["layout"]] = ocr.extract_text(item["id"] + ".pdf", item["pdf"])[:900]
    (OUT_DIR / "layout_text_samples.json").write_text(json.dumps(ex, indent=2), encoding="utf-8")
    print(json.dumps(metrics["extraction"]["overall"], indent=1))
    print("done in", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
