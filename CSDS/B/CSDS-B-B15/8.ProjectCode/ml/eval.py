"""Evaluation for the six product objectives -> experiments/eval/metrics.json.

Everything runs through the real backend services (triage, recommendation, ILP day allocation,
queue estimator) on a separate in-memory database, with a fixed seed.

1. Online booking across the district  - simulated demand from all over Hyderabad
2. OP limits and emergency quotas      - capacity / quota violations, automatic next-day moves
3. Severity classification              - held-out condition accuracy, red-flag recall, under-triage
4. Hospital recommendation              - specialty match, distance, load balance vs nearest-hospital policy
5. Queue position and waiting time      - wait-estimate error on real no-show outcomes
6. Referrals                            - receiving-hospital specialty match and distance
plus calibrated overbooking vs fixed booking (utilisation and overflow).
"""
import json
import random
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml"))

from app import seed  # noqa: E402
from app.db import Base, Booking, Hospital  # noqa: E402
from app.services import noshow, triage  # noqa: E402
from app.services.recommend import haversine_km, recommend  # noqa: E402
from app.services.scheduling import allocate, day_stats, hard_cap, next_token  # noqa: E402
from common import NOSHOW_FEATURES, load_noshow, load_symptom_rows  # noqa: E402

SEED = 7
OUT = ROOT / "experiments" / "eval" / "metrics.json"
LEVELS = ["mild", "moderate", "severe", "critical"]
N_PATIENTS = 1200
CAPACITY_SCALE = 0.04  # shrink OP limits so simulated demand exceeds some hospitals' capacity


def session():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, expire_on_commit=False)()


def random_location(rng):
    # uniform over the populated core of Hyderabad
    return rng.uniform(17.34, 17.50), rng.uniform(78.35, 78.56)


def eval_severity(rng):
    rows = load_symptom_rows()
    acuity = {}
    for line in (ROOT / "data" / "disease_acuity.csv").read_text().splitlines()[1:]:
        d, lv = line.rsplit(",", 1)
        acuity[triage.clean_disease(d)] = lv
    uniq = sorted({(d, tuple(s)) for d, s in rows})
    agree = under = n = 0
    per_level = {lv: [0, 0] for lv in LEVELS}
    for d, syms in uniq:
        for _ in range(3):
            sub = rng.sample(list(syms), min(3, len(syms)))
            r = triage.classify(sub)
            ref = acuity[triage.clean_disease(d)]
            n += 1
            agree += r["severity"] == ref
            under += LEVELS.index(r["severity"]) < LEVELS.index(ref)
            per_level[ref][0] += 1
            per_level[ref][1] += LEVELS.index(r["severity"]) >= LEVELS.index(ref)
    red_cases = [["chest_pain", "breathlessness"], ["chest_pain", "sweating"], ["coma"], ["altered_sensorium"],
                 ["weakness_of_one_body_side", "headache"], ["slurred_speech", "dizziness"],
                 ["stomach_bleeding", "vomiting"], ["high_fever", "altered_sensorium"], ["acute_liver_failure"]]
    red_hits = sum(triage.classify(c)["severity"] == "critical" for c in red_cases)
    tm = json.loads((ROOT / "experiments" / "triage_metrics.json").read_text())
    return {
        "condition_model_held_out_3_symptoms": tm["test_3_symptoms"],
        "condition_model_held_out_full_symptoms": tm["test_full_symptoms"],
        "severity_cases": n,
        "severity_agreement_with_reference_acuity": round(agree / n, 4),
        "under_triage_rate": round(under / n, 4),
        "at_or_above_reference_by_level": {k: round(v[1] / v[0], 4) for k, v in per_level.items() if v[0]},
        "red_flag_critical_recall": round(red_hits / len(red_cases), 4),
        "demo_case_fever_cough_breathlessness": triage.classify(["high_fever", "cough", "breathlessness"])["severity"],
    }


def eval_network(rng):
    db = session()
    seed.seed_hospitals(db)
    hospitals = db.scalars(select(Hospital)).all()
    for h in hospitals:
        h.op_limit = max(3, round(h.op_limit * CAPACITY_SCALE))
        h.emergency_quota = max(1, round(h.emergency_quota * CAPACITY_SCALE))
    db.commit()

    rows = load_symptom_rows()
    today = date.today()
    days = [today + timedelta(days=i) for i in range(3)]
    stats = {"requests": 0, "booked": 0, "moved": 0, "rejected": 0, "quota_used": 0, "spec_match": 0,
             "dist": [], "nearest_dist": [], "by_severity": {lv: 0 for lv in LEVELS}}
    nearest_load = {h.id: 0 for h in hospitals}
    for i in range(N_PATIENTS):
        lat, lon = random_location(rng)
        d, syms = rows[rng.randrange(len(rows))]
        t = triage.classify(rng.sample(syms, min(len(syms), rng.randint(2, 4))))
        req = days[i * len(days) // N_PATIENTS]
        stats["requests"] += 1
        stats["by_severity"][t["severity"]] += 1
        recs = recommend(db, lat, lon, t["severity"], t["specialty"], req, limit=3)
        # baseline policy: nearest hospital with the specialty (or General Medicine), ignoring load
        cand = [h for h in hospitals if t["specialty"] in h.specialty_list()] or hospitals
        near = min(cand, key=lambda h: haversine_km(lat, lon, h.lat, h.lon))
        nearest_load[near.id] += 1
        stats["nearest_dist"].append(haversine_km(lat, lon, near.lat, near.lon))
        placed = False
        for r in recs:  # patient takes the first suggestion that can place them
            h = db.get(Hospital, r["id"])
            age, gender = rng.randint(1, 85), rng.choice("MF")
            p = noshow.predict(age, gender, req, today)
            a = allocate(db, h, req, p, t["severity"], today)
            if a["date"] is None:
                continue
            day = a["date"].isoformat()
            db.add(Booking(hospital_id=h.id, patient_name=f"sim{i}", date=day, requested_date=req.isoformat(),
                           token=next_token(db, h.id, day), uses_quota=a["uses_quota"], severity=t["severity"],
                           priority=triage.PRIORITY[t["severity"]], symptoms="[]", noshow_prob=p))
            db.commit()
            stats["booked"] += 1
            stats["moved"] += a["moved"]
            stats["quota_used"] += a["uses_quota"]
            stats["spec_match"] += t["specialty"] in h.specialty_list()
            stats["dist"].append(r["distance_km"])
            placed = True
            break
        stats["rejected"] += not placed

    # capacity and quota audit
    cap_viol = quota_viol = exp_viol = 0
    loads = []
    all_days = sorted({b.date for b in db.scalars(select(Booking)).all()})
    for h in hospitals:
        for dstr in all_days:
            s = day_stats(db, h.id, dstr)
            cap_viol += s["booked"] > hard_cap(h)
            exp_viol += s["expected"] > h.op_limit + 1e-9
            quota_viol += s["quota_used"] > h.emergency_quota
        s0 = day_stats(db, h.id, days[0].isoformat())
        loads.append(s0["booked"] / h.op_limit)
    cap_first_day = {h.id: h.op_limit for h in hospitals}
    per_day_demand = N_PATIENTS / len(days)
    near_loads = [nearest_load[hid] / len(days) / cap_first_day[hid] for hid in cap_first_day]
    cv = lambda xs: statistics.pstdev(xs) / statistics.mean(xs) if statistics.mean(xs) else 0  # noqa: E731
    return {
        "objective_1_online_booking": {
            "simulated_requests": stats["requests"], "hospitals": len(hospitals),
            "booked": stats["booked"], "booking_success_rate": round(stats["booked"] / stats["requests"], 4),
            "requests_by_severity": stats["by_severity"],
        },
        "objective_2_limits_and_quotas": {
            "capacity_scale_used_for_stress_test": CAPACITY_SCALE,
            "demand_per_day": round(per_day_demand), "district_capacity_per_day": sum(cap_first_day.values()),
            "moved_to_later_day": stats["moved"], "moved_rate": round(stats["moved"] / max(stats["booked"], 1), 4),
            "emergency_quota_bookings": stats["quota_used"],
            "hard_cap_violations": cap_viol, "expected_attendance_violations": exp_viol,
            "emergency_quota_violations": quota_viol,
        },
        "objective_4_recommendation": {
            "specialty_match_rate": round(stats["spec_match"] / max(stats["booked"], 1), 4),
            "mean_distance_km": round(statistics.mean(stats["dist"]), 2),
            "nearest_policy_mean_distance_km": round(statistics.mean(stats["nearest_dist"]), 2),
            "load_cv_mediqueue": round(cv(loads), 3),
            "load_cv_nearest_policy": round(cv(near_loads), 3),
            "max_load_mediqueue": round(max(loads), 2),
            "max_load_nearest_policy": round(max(near_loads), 2),
            "note": "load = day-1 bookings / OP limit; CV = coefficient of variation across hospitals (lower = better spread)",
        },
        "_db": db,
    }


def eval_referrals(db, rng):
    hospitals = db.scalars(select(Hospital)).all()
    specs = ["Pulmonology", "Cardiology", "Neurology", "Gastroenterology", "Hepatology", "Endocrinology"]
    match = n = 0
    dists = []
    for _ in range(200):
        src = rng.choice(hospitals)
        spec = rng.choice(specs)
        recs = [r for r in recommend(db, src.lat, src.lon, "severe", spec, date.today(), limit=4) if r["id"] != src.id]
        if not recs:
            continue
        n += 1
        match += recs[0]["specialty_match"]
        dists.append(recs[0]["distance_km"])
    return {"referral_cases": n, "target_specialty_match_rate": round(match / max(n, 1), 4),
            "mean_referral_distance_km": round(statistics.mean(dists), 2),
            "consent_gate": "summary hidden from receiving hospital until patient consent (verified in scripts/smoke_test.py)"}


def noshow_holdout():
    df = load_noshow()
    _, te = train_test_split(df, test_size=0.2, random_state=42, stratify=df["no_show"])
    model = noshow._bundle()["model"]
    te = te.copy()
    te["p"] = model.predict_proba(te[NOSHOW_FEATURES])[:, 1]
    return te


def eval_queue(te, rng):
    """Queues built from real held-out appointments (real no-show outcomes, calibrated p)."""
    errs, naive_errs, mid_errs = [], [], []
    for _ in range(150):
        day = te.sample(60, random_state=rng.randrange(10**6))
        consult = 4.0
        times = [rng.gammavariate(4, consult / 4) if not ns else 0.0 for ns in day["no_show"]]
        p = day["p"].tolist()
        for k in range(1, len(p)):
            actual = sum(times[:k])
            est = sum((1 - q) * consult for q in p[:k])
            naive = k * consult
            errs.append(abs(est - actual))
            naive_errs.append(abs(naive - actual))
            if k > 30:  # re-estimate when half the queue has been seen (live update)
                mid_errs.append(abs(sum(times[:30]) + sum((1 - q) * consult for q in p[30:k]) - actual))
    return {
        "simulated_queues": 150, "patients_per_queue": 60, "consult_minutes_mean": 4.0,
        "wait_mae_min_no_show_aware": round(statistics.mean(errs), 2),
        "wait_mae_min_naive_position_x_consult": round(statistics.mean(naive_errs), 2),
        "wait_mae_min_after_live_update_mid_session": round(statistics.mean(mid_errs), 2),
    }


def eval_overbooking(te, rng):
    nm = json.loads((ROOT / "experiments" / "noshow_metrics.json").read_text())
    C, days = 40, 300
    fixed_u, ob_u, ob_over, ob_extra = [], [], [], []
    pool = te.sample(frac=1, random_state=SEED).reset_index(drop=True)
    i = 0
    for _ in range(days):
        fixed = pool.iloc[i:i + C]
        fixed_u.append((1 - fixed["no_show"]).sum() / C)
        booked, exp = [], 0.0
        j = i
        while len(booked) < int(C * 1.15):
            r = pool.iloc[j % len(pool)]
            if exp + (1 - r["p"]) > C:
                break
            booked.append(r)
            exp += 1 - r["p"]
            j += 1
        attended = sum(1 - r["no_show"] for r in booked)
        ob_u.append(min(attended, C) / C)
        ob_over.append(attended > C)
        ob_extra.append(len(booked) - C)
        i = (i + C * 2) % (len(pool) - C * 3)
    return {
        "noshow_model": {k: nm[k] for k in ("roc_auc", "brier_uncalibrated", "brier_calibrated",
                                            "ece_uncalibrated", "ece_calibrated", "base_no_show_rate")},
        "daily_op_limit": C, "simulated_days": days,
        "utilisation_fixed_booking": round(float(np.mean(fixed_u)), 4),
        "utilisation_calibrated_overbooking": round(float(np.mean(ob_u)), 4),
        "overflow_days_rate": round(float(np.mean(ob_over)), 4),
        "mean_extra_bookings_per_day": round(float(np.mean(ob_extra)), 2),
    }


def main():
    rng = random.Random(SEED)
    print("severity...")
    sev = eval_severity(rng)
    print("district simulation (this runs the ILP for every booking)...")
    net = eval_network(rng)
    db = net.pop("_db")
    print("referrals, queue, overbooking...")
    ref = eval_referrals(db, rng)
    te = noshow_holdout()
    q = eval_queue(te, rng)
    ob = eval_overbooking(te, rng)
    metrics = {
        "seed": SEED,
        **{k: v for k, v in net.items() if k.startswith("objective_1")},
        **{k: v for k, v in net.items() if k.startswith("objective_2")},
        "objective_2_calibrated_overbooking": ob,
        "objective_3_severity": sev,
        **{k: v for k, v in net.items() if k.startswith("objective_4")},
        "objective_5_queue_wait": q,
        "objective_6_referrals": ref,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
