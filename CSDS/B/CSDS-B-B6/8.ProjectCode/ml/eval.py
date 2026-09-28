"""Evaluation for every objective. Writes experiments/eval/metrics.json.

Offline parts (always run): risk models (5-fold CV), MPI linkage vs seeded ground truth,
FHIR R4 validation of every hospital resource, ledger tamper detection.
Online parts (need run.bat running): consent enforcement, record unification completeness,
retrieval latency, assistant availability.
"""
import copy
import itertools
import json
import os
import sqlite3
import statistics
import sys
import time
from pathlib import Path

import httpx
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml"))

from fhir.resources.R4B import construct_fhir_element  # noqa: E402

from backend.app.config import DATA_DIR, HOSPITALS  # noqa: E402
from backend.app.services.ledger import GENESIS, entry_hash, verify_entries  # noqa: E402
from backend.app.services.mpi import THRESHOLD, link_records, record_from_patient  # noqa: E402
from train import SEED, SPECS, load  # noqa: E402

API = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8206')}/api"
PW = os.getenv("DEMO_PASSWORD", "demo123")


def eval_models():
    out = {}
    for name, spec in SPECS.items():
        X, y = load(spec)
        X = np.where(np.isnan(X), np.nanmedian(X, axis=0), X)
        cv = cross_validate(RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=SEED, n_jobs=-1),
                            X, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
                            scoring=["accuracy", "precision", "recall", "f1", "roc_auc"])
        out[name] = {"rows": int(len(y)), "features": spec["features"],
                     **{k[5:]: round(float(v.mean()), 3) for k, v in cv.items() if k.startswith("test_")}}
    return out


def hospital_records():
    recs, resources = [], []
    for k, h in HOSPITALS.items():
        conn = sqlite3.connect(h["db"])
        for t, j in conn.execute("SELECT type, json FROM resources"):
            r = json.loads(j)
            resources.append(r)
            if t == "Patient":
                recs.append(record_from_patient(k, r))
    return recs, resources


def eval_mpi(recs):
    truth = {(t["hospital"], t["local_id"]): t["person_key"] for t in json.loads((DATA_DIR / "sample" / "mpi_truth.json").read_text())}
    recs = [r for r in recs if (r["hospital"], r["local_id"]) in truth]  # ignore records added after seeding
    groups = {}
    for i, r in enumerate(recs):
        groups.setdefault(truth[(r["hospital"], r["local_id"])], []).append(i)
    pairs = lambda clusters: {tuple(sorted(p)) for c in clusters for p in itertools.combinations(c, 2)}  # noqa: E731
    true_pairs = pairs(groups.values())
    sweep = {}
    for th in (0.70, 0.75, THRESHOLD, 0.85, 0.90):
        clusters = link_records(recs, th)
        pred = pairs([[i for i, _ in c] for c in clusters])
        tp = len(pred & true_pairs)
        p, r = tp / max(1, len(pred)), tp / max(1, len(true_pairs))
        sweep[f"{th:.2f}"] = {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / max(1e-9, p + r), 3),
                              "persons_found": len(clusters)}
    return {"hospital_records": len(recs), "true_persons": len(groups), "true_link_pairs": len(true_pairs),
            "threshold": THRESHOLD, "at_threshold": sweep[f"{THRESHOLD:.2f}"], "threshold_sweep": sweep}


def eval_fhir(resources):
    bad = 0
    for r in resources:
        try:
            construct_fhir_element(r["resourceType"], r)
        except Exception:
            bad += 1
    return {"resources_validated": len(resources), "valid": len(resources) - bad,
            "valid_rate": round((len(resources) - bad) / max(1, len(resources)), 4), "fhir_version": "R4 (fhir.resources R4B models)"}


def synthetic_chain(n=200):
    prev, chain = GENESIS, []
    for i in range(n):
        e = {"id": i + 1, "ts": f"2026-01-01T00:{i // 60:02d}:{i % 60:02d}+00:00", "actor": "eval", "action": "record.view",
             "person_id": f"UH-{i % 7}", "detail": json.dumps({"n": i}), "prev_hash": prev}
        e["hash"] = entry_hash(e["ts"], e["actor"], e["action"], e["person_id"], e["detail"], prev)
        prev = e["hash"]
        chain.append(e)
    return chain


def eval_ledger():
    chain = synthetic_chain()
    assert verify_entries(chain)["intact"]
    attacks = {"edit_detail": 0, "edit_actor": 0, "delete_entry": 0, "swap_entries": 0}
    positions = range(0, len(chain) - 1, 4)
    for i in positions:
        for kind in attacks:
            c = copy.deepcopy(chain)
            if kind == "edit_detail":
                c[i]["detail"] = json.dumps({"n": -1})
            elif kind == "edit_actor":
                c[i]["actor"] = "someone-else"
            elif kind == "delete_entry":
                del c[i]
            else:
                c[i], c[i + 1] = c[i + 1], c[i]
            attacks[kind] += not verify_entries(c)["intact"]
    n = len(positions)
    return {"chain_length": len(chain), "tamper_trials_per_attack": n,
            "detection_rate": {k: round(v / n, 3) for k, v in attacks.items()}, "false_alarms_on_intact_chain": 0}


def eval_online():
    c = httpx.Client(timeout=120)
    try:
        c.get(f"{API}/health").raise_for_status()
    except Exception:
        return {"skipped": "platform API not running - start run.bat and re-run for consent/unification numbers"}

    def login(u):
        return {"Authorization": f"Bearer {c.post(f'{API}/auth/login', json={'username': u, 'password': PW}).json()['token']}"}

    doctors = {"A": login("dr.northbridge"), "B": login("dr.riverside"), "C": login("dr.lakeview")}
    trials = {"denied_without_consent": [], "allowed_with_consent": [], "denied_after_revoke": [], "category_filter_respected": []}
    completeness, latency = [], []
    for username in ("patient", "patient2", "patient3"):
        pat = login(username)
        pid = c.get(f"{API}/auth/me", headers=pat).json()["person_id"]
        t0 = time.perf_counter()
        rec = c.get(f"{API}/records/me", headers=pat).json()
        latency.append((time.perf_counter() - t0) * 1000)
        live = sum(sum(s["counts"].values()) for s in rec["sources"])
        completeness.append({"patient": username, "hospitals": len(rec["sources"]), "resources_at_hospitals": live,
                             "timeline_items": len(rec["timeline"])})
        for cons in c.get(f"{API}/consents", headers=pat).json():
            if cons["status"] == "active":
                c.post(f"{API}/consents/{cons['id']}/revoke", headers=pat)
        for hkey, doc in doctors.items():
            body = {"person_id": pid, "reason": "evaluation"}
            trials["denied_without_consent"].append(c.post(f"{API}/access/request", json=body, headers=doc).status_code == 403)
            cons = c.post(f"{API}/consents", json={"hospital": hkey, "categories": ["conditions", "medications"], "days": 1}, headers=pat).json()
            r = c.post(f"{API}/access/request", json=body, headers=doc)
            trials["allowed_with_consent"].append(r.status_code == 200)
            if r.status_code == 200:
                trials["category_filter_respected"].append({i["category"] for i in r.json()["timeline"]} <= {"conditions", "medications"})
            c.post(f"{API}/consents/{cons['id']}/revoke", headers=pat)
            trials["denied_after_revoke"].append(c.post(f"{API}/access/request", json=body, headers=doc).status_code == 403)
    admin = login("admin")
    verify = c.get(f"{API}/audit/verify", headers=admin).json()
    r = c.post(f"{API}/assistant/explain", json={"language": "Telugu"}, headers=login("patient"))
    return {
        "consent_enforcement": {k: {"trials": len(v), "correct": sum(v), "rate": round(sum(v) / max(1, len(v)), 3)} for k, v in trials.items()},
        "unified_record": completeness,
        "record_retrieval_ms": {"median": round(statistics.median(latency)), "max": round(max(latency))},
        "ledger_after_evaluation": verify,
        "assistant_status": "ok" if r.status_code == 200 else f"error {r.status_code}: {r.json().get('detail', '')[:160]}",
    }


def main():
    recs, resources = hospital_records()
    out = {"risk_models_cv5": eval_models(), "mpi_linkage": eval_mpi(recs), "fhir_validation": eval_fhir(resources),
           "ledger_tamper_detection": eval_ledger(), "online": eval_online()}
    path = ROOT / "experiments" / "eval" / "metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
