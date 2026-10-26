"""Rule-engine, segmentation and complexity experiments that need no API key.

    venv\\Scripts\\python.exe scripts\\exp_rules_corpus.py

1. Re-scores the shipped 40-clause test set (the numbers in experiments/eval/metrics.json).
2. Scores a second, independently written probe set (24 predatory paraphrases + 16 benign look-alikes).
3. Cross-checks every rule against the annotated CUAD clause spans that correspond to it
   (recall proxy) and against clauses of unrelated CUAD categories (false-positive proxy).
4. Runs the non-API part of the pipeline (segment -> rules -> combinations -> complexity) over all 510
   CUAD contracts: clause counts, flag density, combinations found, complexity grades, time per contract.
Writes experiments/rules/metrics.json and experiments/corpus/metrics.json (+ contracts.csv).
"""
from __future__ import annotations

import csv
import json
import statistics as st
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import complexity, parsing  # noqa: E402
from app.services.graph import detect_risky_combinations  # noqa: E402
from app.services.rules import RULES, detect_flags  # noqa: E402

RULE_IDS = [r.id for r in RULES]

PROBE = [
    # (text, [expected rule ids])
    ("The Freelancer agrees not to accept any engagement from another software house in India for twenty-four months following the end of this Agreement.", ["restraint_of_trade"]),
    ("After leaving the Company, the Employee must not carry on or be interested in a business similar to that of the Company anywhere in India for three years.", ["restraint_of_trade"]),
    ("The Contractor shall not work for any competitor during the Term and for twelve months thereafter.", ["restraint_of_trade"]),
    ("For every day of delay the Vendor shall forfeit Rs. 50,000 from the amounts due, regardless of any loss actually suffered.", ["penalty_clause"]),
    ("If the Customer cancels the order, the Customer shall pay a sum equal to the full contract value as damages.", ["penalty_clause"]),
    ("Late delivery will attract a penalty of 2% of the order value for each day of delay.", ["penalty_clause"]),
    ("The Company reserves the right to end this engagement whenever it chooses, with no obligation to give reasons.", ["unilateral_termination"]),
    ("The Company may terminate this Agreement at any time without cause or notice.", ["unilateral_termination"]),
    ("The Landlord may terminate the lease at any time at its sole discretion.", ["unilateral_termination"]),
    ("The Supplier accepts responsibility for every loss of any kind suffered by the Buyer, with no upper cap.", ["unlimited_liability"]),
    ("The Consultant's liability under this Agreement shall be unlimited.", ["unlimited_liability"]),
    ("The Contractor shall be liable for any and all losses, damages and claims arising from the Services.", ["unlimited_liability"]),
    ("Any dispute shall be referred to a sole arbitrator appointed by the Company, whose decision shall be final.", ["one_sided_arbitration"]),
    ("Disputes shall be settled by arbitration by a person solely appointed by the Company.", ["one_sided_arbitration"]),
    ("Only the Company has the right to initiate arbitration; the Contractor may not approach any court or arbitral forum.", ["one_sided_arbitration"]),
    ("This Agreement will continue for further one-year periods unless the Customer gives ninety days' written notice before expiry.", ["auto_renewal"]),
    ("This Agreement shall automatically renew for successive one-year terms.", ["auto_renewal"]),
    ("The subscription renews for successive terms unless cancelled in writing sixty days in advance.", ["auto_renewal"]),
    ("Everything the Freelancer creates during the Term, whether or not related to the Services, belongs to the Company from the moment of creation.", ["ip_overreach"]),
    ("The Contractor irrevocably assigns all right, title and interest in all deliverables worldwide in perpetuity.", ["ip_overreach"]),
    ("All work product shall be a work made for hire and all material produced by the Contractor shall vest in the Company.", ["ip_overreach"]),
    ("Fees once paid cannot be returned for any reason.", ["no_refund"]),
    ("All fees paid under this Agreement are non-refundable.", ["no_refund"]),
    ("The Customer shall not be entitled to any refund on cancellation.", ["no_refund"]),
    # benign look-alikes: nothing should fire
    ("Either party may terminate this Agreement by giving thirty (30) days' written notice to the other party.", []),
    ("The Contractor's total liability under this Agreement shall not exceed the fees paid in the preceding twelve months.", []),
    ("The Consultant shall not disclose Confidential Information to any third party during the Term and for two years thereafter.", []),
    ("Fees paid for services not yet performed will be refunded pro rata if the Agreement is terminated by the Company without cause.", []),
    ("Either party may refer a dispute to arbitration under the Arbitration and Conciliation Act, 1996, before three arbitrators, one appointed by each party and the third jointly.", []),
    ("This Agreement renews only if both parties sign a written extension.", []),
    ("The Contractor retains ownership of its pre-existing intellectual property and grants the Company a licence to use it for the deliverables.", []),
    ("Liquidated damages of 0.5% of the contract value per week of delay, capped at 5%, represent a genuine pre-estimate of the loss.", []),
    ("The Employee shall not engage in any outside activity that creates a conflict of interest with the Company during employment.", []),
    ("This Agreement is governed by the laws of India and the courts at Hyderabad have jurisdiction.", []),
    ("The Customer may cancel at any time on fourteen days' notice and will receive a refund for the unused months.", []),
    ("Payment shall be made within thirty days of receipt of a valid invoice.", []),
    ("Each party shall maintain adequate insurance cover for the duration of this Agreement.", []),
    ("The Company may terminate this Agreement for material breach if the breach is not cured within thirty days of written notice.", []),
    ("The Licensor grants the Licensee a non-exclusive licence to use the Software in India.", []),
    ("Both parties shall be liable for any and all losses caused by their own gross negligence.", []),
]

# CUAD category -> rule it is the closest analogue of (for a recall proxy)
CUAD_MAP = {
    "Non-Compete": "restraint_of_trade",
    "Liquidated Damages": "penalty_clause",
    "Termination For Convenience": "unilateral_termination",
    "Uncapped Liability": "unlimited_liability",
    "Renewal Term": "auto_renewal",
    "Ip Ownership Assignment": "ip_overreach",
}
NEGATIVE_CATS = ["Governing Law", "Audit Rights", "Insurance", "License Grant", "Warranty Duration", "Revenue/Profit Sharing",
                 "Minimum Commitment", "Post-Termination Services", "Change Of Control", "Exclusivity", "Cap On Liability"]


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}


def score(items):
    tp = fp = fn = 0
    per = defaultdict(lambda: [0, 0, 0])
    misses, false_alarms = [], []
    for text, expected in items:
        pred = {r.id for r in detect_flags(text)}
        exp = set(expected)
        for rid in pred | exp:
            if rid in pred and rid in exp:
                per[rid][0] += 1
            elif rid in pred:
                per[rid][1] += 1
            else:
                per[rid][2] += 1
        tp += len(pred & exp)
        fp += len(pred - exp)
        fn += len(exp - pred)
        if exp - pred:
            misses.append({"text": text, "expected": sorted(exp - pred)})
        if pred - exp:
            false_alarms.append({"text": text, "fired": sorted(pred - exp)})
    return {"overall": prf(tp, fp, fn), "per_rule": {k: prf(*v) for k, v in sorted(per.items())}, "misses": misses, "false_alarms": false_alarms}


def exp_rules():
    shipped = json.loads((ROOT / "data/sample/predatory_test_set.json").read_text(encoding="utf-8"))
    s1 = score([(x["text"], x["expected_rules"]) for x in shipped])
    s2 = score(PROBE)
    s2["n_positive"] = sum(1 for _, e in PROBE if e)
    s2["n_negative"] = sum(1 for _, e in PROBE if not e)
    # rules in the shipped set: how many of its 40 clauses share vocabulary with the regexes (a leakage hint)
    return {"shipped_set": {"n": len(shipped), **s1}, "probe_set": {"n": len(PROBE), **s2}}


def load_cuad():
    return json.loads((ROOT / "data/cuad/CUADv1.json").read_text(encoding="utf-8"))["data"]


def exp_cuad_spans(data):
    pos = defaultdict(list)
    neg = []
    for doc in data:
        for para in doc["paragraphs"]:
            for qa in para["qas"]:
                cat = qa["id"].split("__")[-1]
                for ans in qa.get("answers", []):
                    t = " ".join(ans["text"].split())
                    if len(t) < 25:
                        continue
                    if cat in CUAD_MAP:
                        pos[cat].append(t)
                    elif cat in NEGATIVE_CATS:
                        neg.append(t)
    out = {"recall_proxy": {}, "false_positive_proxy": {}}
    for cat, rid in CUAD_MAP.items():
        texts = pos[cat]
        hit = sum(1 for t in texts if any(r.id == rid for r in detect_flags(t)))
        any_hit = sum(1 for t in texts if detect_flags(t))
        out["recall_proxy"][cat] = {"rule": rid, "n_spans": len(texts), "rule_fires": hit, "rate": round(hit / len(texts), 3) if texts else 0.0,
                                    "any_rule_fires": any_hit}
    neg = list(dict.fromkeys(neg))
    fires = Counter()
    for t in neg:
        for r in detect_flags(t):
            fires[r.id] += 1
    out["false_positive_proxy"] = {"n_spans": len(neg), "categories": NEGATIVE_CATS,
                                   "any_rule_fires": sum(1 for t in neg if detect_flags(t)),
                                   "per_rule": {rid: {"fires": fires.get(rid, 0), "rate": round(fires.get(rid, 0) / len(neg), 4)} for rid in RULE_IDS}}
    return out


def exp_corpus(data):
    rows = []
    rule_clauses = Counter()
    combo_counter = Counter()
    grades = Counter()
    t_all = time.perf_counter()
    for doc in data:
        text = doc["paragraphs"][0]["context"]
        t0 = time.perf_counter()
        pages = [parsing.ParsedPage(text=text, page_number=1)]
        try:
            clauses = parsing.split_into_clauses(pages)
        except ValueError:
            rows.append({"title": doc["title"][:60], "chars": len(text), "clauses": 0})
            continue
        headers = len(parsing.CLAUSE_HEADER_RE.findall(text))
        flag_map, flagged = [], 0
        for i, c in enumerate(clauses):
            fl = [r.id for r in detect_flags(c["text"])]
            if fl:
                flagged += 1
            for rid in fl:
                rule_clauses[rid] += 1
            flag_map.append({"id": i, "flags": fl})
        combos = detect_risky_combinations(flag_map)
        for c in combos:
            combo_counter[c["combo_id"]] += 1
        full = "\n\n".join(c["text"] for c in clauses)
        comp = complexity.score_contract(full, len(clauses))
        grades[comp["complexity_grade"]] += 1
        dt = time.perf_counter() - t0
        rows.append({"title": doc["title"][:60], "chars": len(text), "words": len(full.split()), "headers": headers, "clauses": len(clauses),
                     "mean_clause_chars": round(st.mean(len(c["text"]) for c in clauses), 1), "flagged_clauses": flagged,
                     "combos": len(combos), "score": comp["complexity_score"], "grade": comp["complexity_grade"],
                     "readability": comp["readability_score"], "legalese": comp["legalese_density"], "xrefs": comp["cross_reference_count"],
                     "avg_sent": comp["avg_sentence_length"], "seconds": round(dt, 4)})
    total = time.perf_counter() - t_all
    ok = [r for r in rows if r["clauses"]]
    out_dir = ROOT / "experiments" / "corpus"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "contracts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ok[0].keys()))
        w.writeheader()
        w.writerows(ok)
    scores = [r["score"] for r in ok]
    clause_counts = [r["clauses"] for r in ok]
    return {
        "contracts": len(rows), "parsed": len(ok), "total_seconds": round(total, 2), "mean_seconds_per_contract": round(total / len(rows), 4),
        "clauses_total": sum(clause_counts), "clauses_median": st.median(clause_counts), "clauses_mean": round(st.mean(clause_counts), 1),
        "clauses_min": min(clause_counts), "clauses_max": max(clause_counts),
        "contracts_with_header_split": sum(1 for r in ok if r["headers"] >= 2),
        "contracts_with_fewer_than_5_clauses": sum(1 for r in ok if r["clauses"] < 5),
        "mean_clause_chars_median": st.median(r["mean_clause_chars"] for r in ok),
        "flagged_clause_share": round(sum(r["flagged_clauses"] for r in ok) / sum(clause_counts), 4),
        "contracts_with_any_flag": sum(1 for r in ok if r["flagged_clauses"]),
        "contracts_with_combo": sum(1 for r in ok if r["combos"]),
        "rule_clause_counts": dict(rule_clauses), "combo_counts": dict(combo_counter),
        "grades": dict(sorted(grades.items())),
        "score": {"min": min(scores), "median": st.median(scores), "mean": round(st.mean(scores), 1), "max": max(scores), "stdev": round(st.pstdev(scores), 1)},
        "component_medians": {k: st.median(r[k] for r in ok) for k in ("readability", "legalese", "xrefs", "avg_sent")},
        "corr_score_vs_words": round(st.correlation([r["score"] for r in ok], [r["words"] for r in ok]), 3),
    }


def main():
    out = ROOT / "experiments" / "rules"
    out.mkdir(parents=True, exist_ok=True)
    r = exp_rules()
    data = load_cuad()
    r["cuad_spans"] = exp_cuad_spans(data)
    (out / "metrics.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
    c = exp_corpus(data)
    (ROOT / "experiments" / "corpus" / "metrics.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
    print("shipped set:", r["shipped_set"]["overall"])
    print("probe set:  ", r["probe_set"]["overall"], "misses", len(r["probe_set"]["misses"]), "false alarms", len(r["probe_set"]["false_alarms"]))
    print(json.dumps(r["cuad_spans"], indent=1)[:2500])
    print(json.dumps({k: v for k, v in c.items()}, indent=1))


if __name__ == "__main__":
    main()
