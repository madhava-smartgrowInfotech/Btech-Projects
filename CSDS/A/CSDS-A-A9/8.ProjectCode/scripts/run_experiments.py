"""Measurement suite for the ForgetSafe docs run.

Every number in the report comes from here.  Each experiment writes
``experiments/<name>/metrics.json``.  Nothing touches the real audit ledger: every
engine uses a throw-away audit file in a temporary directory.

    python scripts/run_experiments.py            # all experiments
    python scripts/run_experiments.py baseline sweep
"""

from __future__ import annotations

import json
import math
import platform
import random
import statistics as st
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from certified_unlearning.audit import GENESIS_HASH, AuditLedger  # noqa: E402
from certified_unlearning.dataset import CLIENTS, NON_MEMBER_TEXTS, PUBLIC_EVALUATION, ClientDataset  # noqa: E402
from certified_unlearning.engine import FederatedUnlearningEngine  # noqa: E402
from certified_unlearning.model import (  # noqa: E402
    ALPHABET,
    DIMENSION,
    CharacterLanguageModel,
    clipped_update,
    l2_norm,
    membership_auc,
)

OUT = ROOT / "experiments"
TMP = Path(tempfile.mkdtemp(prefix="forgetsafe_exp_"))
_counter = [0]


def audit_path() -> Path:
    _counter[0] += 1
    return TMP / f"audit_{_counter[0]}.jsonl"


def engine(clients=CLIENTS, **kw) -> FederatedUnlearningEngine:
    return FederatedUnlearningEngine(clients=clients, audit_path=audit_path(), **kw)


def save(name: str, payload: dict) -> None:
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote experiments/{name}/metrics.json")


def mean_sd(values):
    values = list(values)
    return {
        "mean": st.fmean(values),
        "sd": st.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "n": len(values),
    }


def eps_of(sigma: float, delta: float = 1e-5) -> float:
    return math.sqrt(2.0 * math.log(1.25 / delta)) / sigma


# --------------------------------------------------------------------------- baseline
def exp_baseline() -> None:
    """Default configuration (seed 2026, clip 25, sigma 3, delta 1e-5)."""
    e = engine()
    t0 = time.perf_counter()
    m = e.train()
    train_ms = (time.perf_counter() - t0) * 1000
    contributions = [c.__dict__ for c in e.contributions()]
    uniform_ppl = float(len(ALPHABET) - 1)  # 33 symbols minus the start marker
    per_client = []
    for client in CLIENTS:
        e2 = engine()
        e2.train()
        t0 = time.perf_counter()
        cert = e2.unlearn(client.client_id)
        ms = (time.perf_counter() - t0) * 1000
        d = cert.to_dict()
        d["unlearn_ms"] = ms
        per_client.append(d)
    cert_statuses = [c["status"] for c in per_client]
    save(
        "baseline",
        {
            "config": {"seed": 2026, "clip_norm": 25.0, "noise_multiplier": 3.0, "delta": 1e-5, "clients": len(CLIENTS),
                       "records_per_client": [len(c.records) for c in CLIENTS], "parameter_dimension": DIMENSION,
                       "alphabet_size": len(ALPHABET)},
            "training": {**m.__dict__, "train_ms": train_ms},
            "uniform_perplexity_reference": uniform_ppl,
            "contributions": contributions,
            "unlearning_per_client": per_client,
            "certified_count": cert_statuses.count("CERTIFIED"),
            "max_reference_l2": max(c["reference_retrain_l2"] for c in per_client),
            "mean_retention_percent": st.fmean(c["utility_retention_percent"] for c in per_client),
            "min_retention_percent": min(c["utility_retention_percent"] for c in per_client),
        },
    )


# --------------------------------------------------------------------------- seeds
def run_seed(seed: int, **kw):
    """Train, then unlearn each client on a fresh engine; return per-client certificate dicts."""
    rows = []
    for client in CLIENTS:
        e = engine(random_seed=seed, **kw)
        e.train()
        rows.append(e.unlearn(client.client_id).to_dict())
    return rows


def exp_seeds(n_seeds: int = 50) -> None:
    pre_ppl, pre_acc, pre_util = [], [], []
    auc_b, auc_a, auc_delta, ret, ref_l2 = [], [], [], [], []
    ppl_after = []
    statuses = {"CERTIFIED": 0, "REVIEW_REQUIRED": 0}
    n_below_70 = 0
    auc_before_by_client = {c.client_id: [] for c in CLIENTS}
    auc_after_by_client = {c.client_id: [] for c in CLIENTS}
    for seed in range(n_seeds):
        e = engine(random_seed=seed)
        m = e.train()
        pre_ppl.append(m.perplexity)
        pre_acc.append(m.next_character_accuracy)
        pre_util.append(m.utility_score)
        for row in run_seed(seed):
            auc_b.append(row["membership_auc_before"])
            auc_a.append(row["membership_auc_after"])
            auc_delta.append(row["membership_auc_after"] - row["membership_auc_before"])
            ret.append(row["utility_retention_percent"])
            ref_l2.append(row["reference_retrain_l2"])
            ppl_after.append(row["perplexity_after"])
            statuses[row["status"]] += 1
            n_below_70 += row["utility_retention_percent"] < 70.0
            auc_before_by_client[row["client_id"]].append(row["membership_auc_before"])
            auc_after_by_client[row["client_id"]].append(row["membership_auc_after"])
    save(
        "seeds",
        {
            "n_seeds": n_seeds,
            "n_unlearning_requests": len(auc_b),
            "pre_unlearning_perplexity": mean_sd(pre_ppl),
            "pre_unlearning_accuracy": mean_sd(pre_acc),
            "pre_unlearning_utility": mean_sd(pre_util),
            "perplexity_after_unlearning": mean_sd(ppl_after),
            "membership_auc_before": mean_sd(auc_b),
            "membership_auc_after": mean_sd(auc_a),
            "membership_auc_change": mean_sd(auc_delta),
            "utility_retention_percent": mean_sd(ret),
            "reference_l2": {"max": max(ref_l2), "mean": st.fmean(ref_l2)},
            "status_counts": statuses,
            "retention_below_70_count": int(n_below_70),
            "auc_before_by_client": {k: mean_sd(v) for k, v in auc_before_by_client.items()},
            "auc_after_by_client": {k: mean_sd(v) for k, v in auc_after_by_client.items()},
        },
    )


# --------------------------------------------------------------------------- noise sweep
def exp_sweep(n_seeds: int = 20) -> None:
    sigmas = [0.001, 0.01, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0, 3.0, 4.85, 6.0, 10.0]
    rows = []
    for sigma in sigmas:
        ppl, acc, aucb, auca, ret, util, status_ok = [], [], [], [], [], [], 0
        total = 0
        for seed in range(n_seeds):
            e = engine(random_seed=seed, noise_multiplier=sigma)
            m = e.train()
            ppl.append(m.perplexity)
            acc.append(m.next_character_accuracy)
            util.append(m.utility_score)
            for row in run_seed(seed, noise_multiplier=sigma):
                aucb.append(row["membership_auc_before"])
                auca.append(row["membership_auc_after"])
                ret.append(row["utility_retention_percent"])
                status_ok += row["status"] == "CERTIFIED"
                total += 1
        rows.append(
            {
                "noise_multiplier": sigma,
                "epsilon": eps_of(sigma),
                "epsilon_within_classical_range": eps_of(sigma) < 1.0,
                "perplexity": mean_sd(ppl),
                "accuracy": mean_sd(acc),
                "utility_score": mean_sd(util),
                "membership_auc_before": mean_sd(aucb),
                "membership_auc_after": mean_sd(auca),
                "retention_percent": mean_sd(ret),
                "certified_fraction": status_ok / total,
            }
        )
    save("noise_sweep", {"n_seeds": n_seeds, "delta": 1e-5, "clip_norm": 25.0, "rows": rows})


# --------------------------------------------------------------------------- retrain-from-scratch gold reference
def exp_gold(n_seeds: int = 40) -> None:
    """Compare the unlearned model with TRUE retraining that draws fresh Gaussian noise.

    The engine's own 'reference' re-uses the stored noise, so it is exact by construction.
    The honest gold standard is a retrain on the retained clients with an independent noise draw:
    the two models cannot be equal sample-by-sample, but they should be distributed identically.
    """
    results = []
    for sigma in (3.0, 0.5):
        d_unl_ret, d_ret_ret = [], []
        auc_unl, auc_ret = [], []
        ppl_unl, ppl_ret = [], []
        acc_unl, acc_ret = [], []
        for seed in range(n_seeds):
            for client in CLIENTS:
                e = engine(random_seed=seed, noise_multiplier=sigma)
                e.train()
                e.unlearn(client.client_id)
                unlearned = e.model
                retained = tuple(c for c in CLIENTS if c.client_id != client.client_id)
                r1 = engine(clients=retained, random_seed=10_000 + seed, noise_multiplier=sigma)
                r1.train()
                r2 = engine(clients=retained, random_seed=20_000 + seed, noise_multiplier=sigma)
                r2.train()
                d_unl_ret.append(l2_norm([a - b for a, b in zip(unlearned.parameters, r1.model.parameters)]))
                d_ret_ret.append(l2_norm([a - b for a, b in zip(r1.model.parameters, r2.model.parameters)]))
                auc_unl.append(membership_auc(unlearned, client.records, NON_MEMBER_TEXTS))
                auc_ret.append(membership_auc(r1.model, client.records, NON_MEMBER_TEXTS))
                ppl_unl.append(unlearned.perplexity(PUBLIC_EVALUATION))
                ppl_ret.append(r1.model.perplexity(PUBLIC_EVALUATION))
                acc_unl.append(unlearned.next_character_accuracy(PUBLIC_EVALUATION))
                acc_ret.append(r1.model.next_character_accuracy(PUBLIC_EVALUATION))
        results.append(
            {
                "noise_multiplier": sigma,
                "pairs": len(d_unl_ret),
                "l2_unlearned_vs_fresh_retrain": mean_sd(d_unl_ret),
                "l2_fresh_retrain_vs_fresh_retrain": mean_sd(d_ret_ret),
                "membership_auc_unlearned": mean_sd(auc_unl),
                "membership_auc_fresh_retrain": mean_sd(auc_ret),
                "perplexity_unlearned": mean_sd(ppl_unl),
                "perplexity_fresh_retrain": mean_sd(ppl_ret),
                "accuracy_unlearned": mean_sd(acc_unl),
                "accuracy_fresh_retrain": mean_sd(acc_ret),
            }
        )
    save("gold_retrain", {"n_seeds": n_seeds, "results": results})


# --------------------------------------------------------------------------- noise-free leave-one-out leakage
def exp_noise_free() -> None:
    """Without noise the member signal is visible; show what unlearning removes (sigma = 1e-6)."""
    rows = []
    for client in CLIENTS:
        e = engine(noise_multiplier=1e-6)
        e.train()
        before_nll = st.fmean(e.model.negative_log_likelihood(r) for r in client.records)
        auc_b = membership_auc(e.model, client.records, NON_MEMBER_TEXTS)
        cert = e.unlearn(client.client_id)
        after_nll = st.fmean(e.model.negative_log_likelihood(r) for r in client.records)
        rows.append(
            {
                "client_id": client.client_id,
                "member_nll_before": before_nll,
                "member_nll_after": after_nll,
                "auc_before": auc_b,
                "auc_after": cert.membership_auc_after,
                "retention_percent": cert.utility_retention_percent,
                "status": cert.status,
                "perplexity_before": cert.perplexity_before,
                "perplexity_after": cert.perplexity_after,
            }
        )
    save(
        "noise_free_leakage",
        {
            "noise_multiplier": 1e-6,
            "rows": rows,
            "mean_auc_before": st.fmean(r["auc_before"] for r in rows),
            "mean_auc_after": st.fmean(r["auc_after"] for r in rows),
            "mean_member_nll_before": st.fmean(r["member_nll_before"] for r in rows),
            "mean_member_nll_after": st.fmean(r["member_nll_after"] for r in rows),
        },
    )


# --------------------------------------------------------------------------- sequential removal
def exp_sequential() -> None:
    e = engine()
    e.train()
    order = [c.client_id for c in CLIENTS]
    steps = [{"step": 0, "active_clients": 5, **{k: v for k, v in e.metrics().__dict__.items()}}]
    certs = []
    for cid in order[:4]:
        cert = e.unlearn(cid)
        m = e.metrics()
        steps.append({"step": len(steps), "removed": cid, "active_clients": m.active_clients, **m.__dict__,
                      "status": cert.status, "reference_l2": cert.reference_retrain_l2,
                      "retention_percent": cert.utility_retention_percent})
        certs.append(cert.status)
    last = None
    try:
        e.unlearn(order[4])
    except ValueError as error:
        last = str(error)
    valid, detail = e.audit.verify()
    save("sequential", {"steps": steps, "last_client_error": last, "audit_valid": valid, "audit_detail": detail,
                        "statuses": certs})


# --------------------------------------------------------------------------- scaling
def synthetic_clients(n: int, records: int, rng: random.Random):
    words = ["data", "model", "client", "privacy", "secure", "report", "update", "system", "learning", "record",
             "account", "patient", "order", "travel", "school", "bank", "health", "store", "plan", "trust"]
    clients = []
    for i in range(n):
        recs = tuple(" ".join(rng.choice(words) for _ in range(rng.randint(5, 9))) + "." for _ in range(records))
        clients.append(ClientDataset(f"client_{i:04d}", f"Client {i:04d}", "Synthetic", recs))
    return clients


def exp_scaling() -> None:
    rng = random.Random(7)
    rows = []
    for n, recs in ((5, 5), (25, 20), (100, 50), (250, 100), (500, 100)):
        clients = tuple(synthetic_clients(n, recs, rng))
        unl, tr = [], []
        for rep in range(5):
            e = engine(clients=clients)
            t0 = time.perf_counter()
            e.train()
            tr.append((time.perf_counter() - t0) * 1000)
            t0 = time.perf_counter()
            e.unlearn(clients[0].client_id)
            unl.append((time.perf_counter() - t0) * 1000)
        # retraining baseline = train() on the retained clients only
        retr = []
        for rep in range(5):
            e = engine(clients=clients[1:])
            t0 = time.perf_counter()
            e.train()
            retr.append((time.perf_counter() - t0) * 1000)
        rows.append(
            {
                "clients": n,
                "records_per_client": recs,
                "total_records": n * recs,
                "train_ms_median": st.median(tr),
                "unlearn_ms_median": st.median(unl),
                "full_retrain_ms_median": st.median(retr),
                "speedup_retrain_over_unlearn": st.median(retr) / st.median(unl),
            }
        )
        print("scaling", rows[-1])
    # ledger append cost as the ledger grows
    ledger = AuditLedger(audit_path())
    marks = {}
    t_start = time.perf_counter()
    for i in range(1, 2001):
        t0 = time.perf_counter()
        ledger.append({"event_type": "PROBE", "i": i})
        if i in (1, 100, 500, 1000, 2000):
            marks[i] = (time.perf_counter() - t0) * 1000
    total_s = time.perf_counter() - t_start
    t0 = time.perf_counter()
    ok, _ = ledger.verify()
    verify_2000_ms = (time.perf_counter() - t0) * 1000
    save("scaling", {"rows": rows, "ledger_append_ms_at_length": marks, "ledger_2000_appends_total_s": total_s,
                     "ledger_verify_2000_ms": verify_2000_ms, "ledger_valid": ok})


# --------------------------------------------------------------------------- audit tamper matrix
def _rehash(records):
    """Recompute a full valid chain over edited records (what an attacker with file access can do)."""
    import hashlib

    prev = GENESIS_HASH
    out = []
    for n, rec in enumerate(records, 1):
        rec = {k: v for k, v in rec.items() if k != "record_hash"}
        rec["sequence"] = n
        rec["previous_hash"] = prev
        canon = json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        rec["record_hash"] = hashlib.sha256(f"{prev}|{canon}".encode()).hexdigest()
        prev = rec["record_hash"]
        out.append(rec)
    return out


def exp_audit() -> None:
    def fresh():
        e = engine()
        e.train()
        e.unlearn("client_finance")
        e.unlearn("client_health")
        return e

    cases = []

    def run(name, mutate, expect_detect):
        e = fresh()
        path = e.audit.path
        recs = e.audit.read_all()
        new = mutate(recs)
        path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in new), encoding="utf-8")
        valid, detail = AuditLedger(path).verify()
        cases.append({"case": name, "detected": not valid, "detail": detail, "expected_detected": expect_detect})

    def edit_field(r):
        r = [dict(x) for x in r]
        r[1]["utility_retention_percent"] = 100.0
        return r

    def edit_status(r):
        r = [dict(x) for x in r]
        r[1]["status"] = "REVIEW_REQUIRED"
        return r

    def delete_middle(r):
        return [r[0], r[2]]

    def swap(r):
        return [r[0], r[2], r[1]]

    def truncate_tail(r):
        return r[:2]

    def forge_rechain(r):
        r = [dict(x) for x in r]
        r[1]["utility_retention_percent"] = 100.0
        return _rehash(r)

    def insert_forged(r):
        r = [dict(x) for x in r]
        extra = dict(r[1]); extra["client_id"] = "client_forged"
        return _rehash(r + [extra])

    def nothing(r):
        return r

    run("untouched ledger", nothing, False)
    run("edit a numeric field in a middle record", edit_field, True)
    run("flip a certificate status", edit_status, True)
    run("delete a middle record", delete_middle, True)
    run("swap two records", swap, True)
    run("truncate the newest record(s) from the tail", truncate_tail, False)
    run("edit a record AND recompute every hash (forgery)", forge_rechain, False)
    run("append a forged record with a valid hash", insert_forged, False)
    save("audit_tamper", {"cases": cases,
                          "detected_when_expected": sum(c["detected"] == c["expected_detected"] for c in cases),
                          "undetected_attacks": [c["case"] for c in cases if not c["detected"] and c["expected_detected"] is False and c["case"] != "untouched ledger"]})


# --------------------------------------------------------------------------- DP accounting facts
def exp_dp() -> None:
    delta = 1e-5
    c = math.sqrt(2.0 * math.log(1.25 / delta))
    save(
        "dp_accounting",
        {
            "delta": delta,
            "formula": "epsilon = sqrt(2 ln(1.25/delta)) / sigma",
            "numerator": c,
            "default_sigma": 3.0,
            "default_epsilon": c / 3.0,
            "sigma_needed_for_epsilon_below_1": c,
            "noise_std_per_coordinate_default": 3.0 * 25.0,
            "clip_norm": 25.0,
            "raw_update_norms": {c.client_id: clipped_update(c.records, 25.0)[1] for c in CLIENTS},
            "clients_clipped": sum(clipped_update(c.records, 25.0)[2] < 1.0 for c in CLIENTS),
            "signal_to_noise_per_coordinate_note": "clipped L2 norm 25 spread over 1089 coordinates vs noise std 75 per coordinate",
            "expected_noise_l2": 75.0 * math.sqrt(DIMENSION),
            "epsilon_by_sigma": {str(s): c / s for s in (0.5, 1, 2, 3, 4.85, 6, 10)},
            "noise_reused_after_unlearning": True,
        },
    )


# --------------------------------------------------------------------------- live API: latency + edge cases
def exp_api() -> None:
    import http.client
    import subprocess
    import urllib.error
    import urllib.request

    port = 8198
    workdir = tempfile.mkdtemp(prefix="forgetsafe_api_")
    proc = subprocess.Popen([sys.executable, str(ROOT / "app.py"), "--port", str(port)], cwd=workdir,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"127.0.0.1:{port}"

    def call(method, path, body=None, raw=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        h = {"Content-Type": "application/json"} if data else {}
        h.update(headers or {})
        t0 = time.perf_counter()
        try:
            conn.request(method, path, body=data, headers=h)
            resp = conn.getresponse()
            payload = resp.read()
            ms = (time.perf_counter() - t0) * 1000
            return resp.status, payload, ms
        except Exception as exc:  # noqa: BLE001
            return -1, str(exc).encode(), (time.perf_counter() - t0) * 1000
        finally:
            conn.close()

    try:
        for _ in range(60):
            s, _, _ = call("GET", "/api/health")
            if s == 200:
                break
            time.sleep(0.2)
        lat = {}

        def bench(label, method, path, body=None, n=100, setup=None):
            times = []
            for _ in range(n):
                if setup:
                    setup()
                s, _, ms = call(method, path, body)
                times.append(ms)
            times.sort()
            lat[label] = {"n": n, "p50_ms": times[len(times) // 2], "p95_ms": times[int(len(times) * 0.95) - 1],
                          "max_ms": times[-1], "mean_ms": st.fmean(times)}

        bench("GET /api/health", "GET", "/api/health")
        bench("GET /api/state (untrained)", "GET", "/api/state")
        bench("POST /api/train", "POST", "/api/train", n=50)
        bench("GET /api/state (trained)", "GET", "/api/state")
        bench("POST /api/generate", "POST", "/api/generate", {"seed": "privacy"}, n=50)
        bench("POST /api/audit/verify", "POST", "/api/audit/verify", n=50)
        # unlearn needs a fresh trained session each time
        times = []
        for i in range(30):
            call("POST", "/api/session")
            call("POST", "/api/train")
            s, _, ms = call("POST", "/api/unlearn", {"client_id": "client_finance"})
            assert s == 200, s
            times.append(ms)
        times.sort()
        lat["POST /api/unlearn"] = {"n": 30, "p50_ms": times[len(times) // 2], "p95_ms": times[int(len(times) * 0.95) - 1],
                                    "max_ms": times[-1], "mean_ms": st.fmean(times)}
        s, payload, ms = call("GET", "/api/state")
        ledger_len = len(json.loads(payload)["audit"]["records"])
        lat["GET /api/state (ledger %d records)" % ledger_len] = {"n": 1, "p50_ms": ms}
        bench("GET /api/state (grown ledger)", "GET", "/api/state", n=30)

        call("POST", "/api/session")
        edge = []

        def case(name, method, path, body=None, raw=None, headers=None):
            s, payload, _ = call(method, path, body, raw, headers)
            try:
                msg = json.loads(payload).get("error") or json.loads(payload)
            except Exception:  # noqa: BLE001
                msg = payload[:80].decode("utf-8", "replace")
            edge.append({"case": name, "status": s, "response": msg if isinstance(msg, str) else "ok"})

        case("unlearn before training", "POST", "/api/unlearn", {"client_id": "client_finance"})
        case("generate before training", "POST", "/api/generate", {"seed": "x"})
        case("certificate before any unlearning", "GET", "/api/certificate/latest")
        case("unknown route (GET)", "GET", "/api/nope")
        case("unknown route (POST)", "POST", "/api/nope", {})
        case("malformed JSON body", "POST", "/api/unlearn", raw=b"{not json")
        case("JSON array instead of object", "POST", "/api/unlearn", raw=b"[1,2]")
        case("oversized body (2 MB)", "POST", "/api/unlearn", raw=b"{" + b" " * 2_000_000 + b"}")
        case("unlearn without client_id", "POST", "/api/unlearn", {})
        call("POST", "/api/train")
        case("unlearn unknown client id", "POST", "/api/unlearn", {"client_id": "client_nobody"})
        case("unlearn with SQL-ish id", "POST", "/api/unlearn", {"client_id": "x'; DROP TABLE--"})
        case("generate with empty seed", "POST", "/api/generate", {"seed": ""})
        case("generate with unicode seed", "POST", "/api/generate", {"seed": "üñî \U0001f600"})
        case("generate with 5,000-char seed", "POST", "/api/generate", {"seed": "privacy " * 625})
        case("unsupported method (PUT)", "PUT", "/api/train")
        case("unlearn first client ok", "POST", "/api/unlearn", {"client_id": "client_finance"})
        case("repeat unlearn same client", "POST", "/api/unlearn", {"client_id": "client_finance"})
        for cid in ("client_health", "client_education", "client_retail"):
            call("POST", "/api/unlearn", {"client_id": cid})
        case("unlearn the last remaining client", "POST", "/api/unlearn", {"client_id": "client_travel"})
        case("path traversal on /", "GET", "/../../etc/passwd")
        s, _, _ = call("GET", "/")
        edge.append({"case": "legacy single-page UI at /", "status": s, "response": "html"})
        save("api", {"host": base, "latency": lat, "edge_cases": edge})
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            proc.kill()


def exp_env() -> None:
    save("environment", {"python": platform.python_version(), "platform": platform.platform(),
                         "machine": platform.machine(), "processor": platform.processor()})


ALL = {
    "environment": exp_env,
    "baseline": exp_baseline,
    "seeds": exp_seeds,
    "sweep": exp_sweep,
    "gold": exp_gold,
    "noisefree": exp_noise_free,
    "sequential": exp_sequential,
    "audit": exp_audit,
    "dp": exp_dp,
    "scaling": exp_scaling,
    "api": exp_api,
}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(ALL)
    for name in wanted:
        t0 = time.perf_counter()
        print(f"== {name}")
        ALL[name]()
        print(f"   {time.perf_counter() - t0:.1f}s")
