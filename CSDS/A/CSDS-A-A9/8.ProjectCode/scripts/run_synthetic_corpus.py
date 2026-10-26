"""Synthetic-corpus study of the real ForgetSafe engine, plus a dated timeline taken from git.

The product ships a 25-sentence corpus, so its bigram model cannot learn and the membership attack has five
members.  This script generates a larger SYNTHETIC federated corpus with a seeded grammar and runs the real
engine classes (FederatedUnlearningEngine, ClientDataset, CharacterLanguageModel, membership_auc) on it.

    python scripts/run_synthetic_corpus.py            # all sections
    python scripts/run_synthetic_corpus.py timeline   # only the git timeline

Outputs: experiments/synthetic_corpus/metrics.json, experiments/timeline/metrics.json, docs/charts/s0*.png.

Two things are patched at run time and nowhere else: (1) `clipped_update` is memoised on the raw bigram counts
(same arithmetic, computed once per client) and (2) the model's `_row_probabilities` is memoised per character
(same arithmetic, computed once per model).  `check_patch_equivalence()` verifies bit-identical results.  The
timing section (5) runs BEFORE the patches, on the unmodified classes.
"""

from __future__ import annotations

import copy
import json
import math
import random
import shutil
import statistics as st
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH = ROOT.parent
sys.path.insert(0, str(ROOT))

import certified_unlearning.engine as eng  # noqa: E402
from certified_unlearning.audit import AuditLedger  # noqa: E402
from certified_unlearning.dataset import ClientDataset  # noqa: E402
from certified_unlearning.model import (  # noqa: E402
    ALPHABET,
    DIMENSION,
    INDEX,
    CharacterLanguageModel,
    clipped_update,
    l2_norm,
    membership_auc,
    raw_update,
)

OUT = ROOT / "experiments"
TMP = Path(tempfile.mkdtemp(prefix="fs_syn_"))
_ctr = [0]
DELTA = 1e-5


def new_audit() -> Path:
    _ctr[0] += 1
    return TMP / f"a{_ctr[0]}.jsonl"


def save(name: str, payload: dict) -> None:
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote experiments/{name}/metrics.json", flush=True)


def mean_sd(values):
    values = list(values)
    return {"mean": st.fmean(values), "sd": st.stdev(values) if len(values) > 1 else 0.0, "min": min(values), "max": max(values), "n": len(values)}


def eps_of(sigma: float) -> float:
    return math.sqrt(2.0 * math.log(1.25 / DELTA)) / sigma


# ================================================================================================ synthetic grammar
# domain: roles | nouns | adjectives | verb pairs (base/third-person) | adverbs.  Letters, spaces and . ? ! only.
DOMAINS = {
    "Finance": ("banker auditor trader advisor", "account loan payment ledger deposit invoice budget interest", "secure monthly annual overdue digital", "approve/approves review/reviews record/records audit/audits transfer/transfers", "quickly carefully promptly"),
    "Healthcare": ("doctor nurse patient surgeon", "clinic symptom treatment diagnosis vaccine therapy ward prescription", "chronic mild urgent routine sterile", "examine/examines treat/treats monitor/monitors prescribe/prescribes discharge/discharges", "gently calmly closely"),
    "Education": ("teacher student mentor professor", "lesson course exam library project lecture grade syllabus", "advanced practical weekly optional creative", "explain/explains teach/teaches grade/grades revise/revises present/presents", "patiently clearly regularly"),
    "Retail": ("cashier shopper manager supplier", "store basket receipt discount shelf order product coupon", "popular fresh seasonal damaged bulk", "scan/scans pack/packs refund/refunds display/displays restock/restocks", "smoothly cheaply early"),
    "Travel": ("traveler pilot guide driver", "flight hotel ticket station route passport journey luggage", "scenic delayed direct crowded quiet", "book/books board/boards reach/reaches cancel/cancels explore/explores", "safely slowly lightly"),
    "Energy": ("engineer operator inspector planner", "turbine grid reactor cable battery panel substation meter", "renewable stable offline heavy efficient", "install/installs repair/repairs connect/connects measure/measures shut/shuts", "steadily silently locally"),
    "Agriculture": ("farmer harvester breeder gardener", "field harvest tractor seed orchard irrigation barn soil", "organic fertile rural dry abundant", "plant/plants water/waters sow/sows gather/gathers fertilize/fertilizes", "early patiently daily"),
    "Legal": ("lawyer judge clerk witness", "contract verdict hearing statute appeal brief clause tribunal", "binding formal disputed valid pending", "draft/drafts argue/argues sign/signs dismiss/dismisses file/files", "formally firmly lawfully"),
    "Telecom": ("technician subscriber operator analyst", "network tower signal router cable plan roaming bandwidth", "wireless stable congested rapid global", "upgrade/upgrades route/routes activate/activates test/tests extend/extends", "instantly reliably remotely"),
    "Manufacturing": ("welder foreman machinist assembler", "factory machine shift pallet mold gear assembly conveyor", "automated precise industrial rusty durable", "cut/cuts weld/welds polish/palishes inspect/inspects assemble/assembles", "accurately steadily noisily"),
    "Insurance": ("insurer claimant broker assessor", "policy premium claim coverage damage quote reserve renewal", "annual partial comprehensive disputed fair", "assess/assesses renew/renews cover/covers settle/settles reject/rejects", "fairly slowly strictly"),
    "Logistics": ("dispatcher courier loader planner", "warehouse parcel pallet freight depot manifest container shipment", "express bulky fragile overnight tracked", "load/loads ship/ships sort/sorts deliver/delivers weigh/weighs", "overnight swiftly steadily"),
    "Media": ("editor reporter producer anchor", "article headline episode channel studio script broadcast archive", "breaking live exclusive critical weekly", "publish/publishes edit/edits film/films broadcast/broadcasts interview/interviews", "boldly live daily"),
    "Sports": ("coach player referee captain", "match season stadium league trophy practice tournament record", "decisive close national veteran youthful", "train/trains score/scores defend/defends referee/referees win/wins", "fiercely fairly quickly"),
    "Government": ("mayor officer councillor clerk", "budget permit ballot census policy council register service", "public municipal federal annual open", "approve/approves vote/votes publish/publishes regulate/regulates fund/funds", "openly lawfully slowly"),
    "RealEstate": ("agent buyer tenant landlord", "apartment lease mortgage listing deed garden lobby valuation", "spacious modern vacant historic compact", "rent/rents inspect/inspects sell/sells appraise/appraises renovate/renovates", "privately quickly happily"),
    "Hospitality": ("chef waiter host concierge", "restaurant menu reservation suite kitchen banquet lobby buffet", "elegant cozy seasonal popular quiet", "serve/serves cook/cooks welcome/welcomes reserve/reserves clean/cleans", "warmly politely promptly"),
    "Automotive": ("mechanic driver dealer tester", "engine brake sedan garage tire warranty chassis dashboard", "electric hybrid compact worn reliable", "tune/tunes drive/drives service/services replace/replaces test/tests", "smoothly carefully loudly"),
    "Science": ("researcher analyst chemist physicist", "sample experiment theory laboratory dataset microscope result hypothesis", "accurate novel controlled noisy robust", "measure/measures test/tests publish/publishes model/models replicate/replicates", "precisely carefully rigorously"),
    "Construction": ("builder architect surveyor crane", "bridge tower foundation beam concrete site blueprint scaffold", "steel tall unstable temporary solid", "pour/pours lift/lifts survey/surveys design/designs demolish/demolishes", "steadily safely slowly"),
}
DOMAIN_NAMES = list(DOMAINS)
FIX = {"palishes": "polishes", "shuts": "shuts", "crane": "crane"}
TEMPLATES = [
    "the {role} {v3} the {adj} {n1} {adv}.",
    "every {role} {v3} a {n1} and a {n2}.",
    "a {adj} {n1} helps the {role} {vb} the {n2}.",
    "why does the {role} {vb} the {adj} {n1}?",
    "the {n1} stays {adj} when the {role} {v3} the {n2}.",
    "{adj} {n1}s support the {role} during the {n2} review.",
    "the {role} said that the {n1} is {adj} and the {n2} is {adj2}.",
    "after the {n1} the {role} {v3} every {n2}.",
    "can the {role} {vb} a {adj} {n1} before the {n2}?",
    "the {role} and the {role2} {vb} the {n1} {adv}!",
    "our {n1} needs a {adj} {n2} for the {role}.",
    "the {role} {v3} the {n1} and the {n2} {adv}.",
]
PW_TEMPLATES = ["the {role} {v3} {pw} for the {n1}.", "{pw} {v3} the {n1} {adv}.", "did the {role} {vb} {pw} and the {n1}?"]


def _pairs(spec: str):
    out = []
    for p in spec.split():
        b, s = p.split("/")
        out.append((b, FIX.get(s, s)))
    return out


def _pseudo_word(rng: random.Random) -> str:
    cons, vow = "bdfgklmnprstvz", "aeiou"
    return "".join(rng.choice(cons) + rng.choice(vow) for _ in range(rng.randint(2, 3))) + rng.choice("nrkxl")


def gen_sentence(rng: random.Random, domain: str, private: list[str] | None) -> str:
    roles, nouns, adjs, verbs, advs = DOMAINS[domain]
    roles, nouns, adjs, advs = roles.split(), nouns.split(), adjs.split(), advs.split()
    verbs = _pairs(verbs)
    vb, v3 = rng.choice(verbs)
    use_pw = private and rng.random() < 0.3
    tpl = rng.choice(PW_TEMPLATES) if use_pw else rng.choice(TEMPLATES)
    return tpl.format(role=rng.choice(roles), role2=rng.choice(roles), n1=rng.choice(nouns), n2=rng.choice(nouns), adj=rng.choice(adjs),
                      adj2=rng.choice(adjs), adv=rng.choice(advs), vb=vb, v3=v3, pw=rng.choice(private) if use_pw else "")


class Corpus:
    """Seeded synthetic federated corpus: client i has domain DOMAIN_NAMES[i % 20] and six private pseudo-words."""

    def __init__(self, per_client: int, held_out: int = 200, public_n: int = 300, seed: int = 11):
        self.per_client, self.held_out_n, self.public_n, self.seed = per_client, held_out, public_n, seed
        self._clients: dict[int, ClientDataset] = {}
        self._held: dict[int, tuple[str, ...]] = {}
        self._private: dict[int, list[str]] = {}

    def private(self, i: int) -> list[str]:
        if i not in self._private:
            rng = random.Random(f"pw-{self.seed}-{i}")
            self._private[i] = [_pseudo_word(rng) for _ in range(6)]
        return self._private[i]

    def _unique(self, rng, dom, pw, k, exclude=()):
        seen, out = set(exclude), []
        guard = 0
        while len(out) < k and guard < k * 200:
            guard += 1
            s = gen_sentence(rng, dom, pw)
            if s not in seen:
                seen.add(s)
                out.append(s)
        return tuple(out)

    def client(self, i: int) -> ClientDataset:
        if i not in self._clients:
            dom = DOMAIN_NAMES[i % 20]
            recs = self._unique(random.Random(f"train-{self.seed}-{i}"), dom, self.private(i), self.per_client)
            self._clients[i] = ClientDataset(f"client_{i:05d}", f"Client {i + 1:04d}", dom, recs)
        return self._clients[i]

    def clients(self, n: int):
        return [self.client(i) for i in range(n)]

    def heldout(self, i: int) -> tuple[str, ...]:
        if i not in self._held:
            dom = DOMAIN_NAMES[i % 20]
            self._held[i] = self._unique(random.Random(f"held-{self.seed}-{i}"), dom, self.private(i), self.held_out_n, exclude=self.client(i).records)
        return self._held[i]

    def other_nonmembers(self, i: int, n: int, k: int = 200) -> tuple[str, ...]:
        """Held-out sentences of the OTHER clients among the first n (the product's own 'unrelated text' design)."""
        rng = random.Random(f"other-{self.seed}-{i}-{n}")
        pool = []
        for j in range(min(n, 20)):
            if j != i:
                pool += list(self.heldout(j))
        rng.shuffle(pool)
        return tuple(pool[:k])

    def public(self, n: int) -> tuple[str, ...]:
        """300 sentences spread evenly over the domains of the first n clients, without private words, not equal to any training sentence."""
        doms = [DOMAIN_NAMES[j] for j in range(min(n, 20))]
        rng = random.Random(f"public-{self.seed}")
        out, seen = [], set()
        k = 0
        while len(out) < self.public_n:
            s = gen_sentence(rng, doms[k % len(doms)], None)
            k += 1
            if s not in seen:
                seen.add(s)
                out.append(s)
        return tuple(out)


# ================================================================================================ patches (data and speed)
_raw_cache: dict[int, tuple] = {}
_ORIG_CLIPPED = clipped_update
_ORIG_MODEL = CharacterLanguageModel


def fast_clipped_update(records, clip_norm):
    ent = _raw_cache.get(id(records))
    if ent is None:
        raw = raw_update(records)
        ent = (raw, l2_norm(raw), records)  # keep `records` alive so its id cannot be reused
        _raw_cache[id(records)] = ent
    raw, norm, _ = ent
    scale = min(1.0, clip_norm / norm) if norm else 1.0
    return [v * scale for v in raw], norm, scale


class FastModel(CharacterLanguageModel):
    def _row_probabilities(self, character):
        cache = self.__dict__.setdefault("_cache", {})
        key = character if character in INDEX else " "
        row = cache.get(key)
        if row is None:
            row = CharacterLanguageModel._row_probabilities(self, key)
            cache[key] = row
        return row


def apply_patches() -> None:
    eng.clipped_update = fast_clipped_update
    eng.CharacterLanguageModel = FastModel


def check_patch_equivalence(corpus: Corpus) -> dict:
    rng = random.Random(5)
    recs = corpus.client(0).records
    a = _ORIG_CLIPPED(recs, 25.0)
    b = fast_clipped_update(recs, 25.0)
    params = [rng.gauss(0, 30) for _ in range(DIMENSION)]
    m0, m1 = _ORIG_MODEL(params), FastModel(params)
    texts = corpus.public(5)[:40]
    same_update = a == b
    same_ppl = m0.perplexity(texts) == m1.perplexity(texts)
    same_acc = m0.next_character_accuracy(texts) == m1.next_character_accuracy(texts)
    same_auc = membership_auc(m0, recs, texts) == membership_auc(m1, recs, texts)
    ok = same_update and same_ppl and same_acc and same_auc
    print("patch equivalence:", ok, flush=True)
    return {"bit_identical": ok, "clipped_update": same_update, "perplexity": same_ppl, "accuracy": same_acc, "auc": same_auc}


def make_engine(clients, **kw):
    return eng.FederatedUnlearningEngine(clients=tuple(clients), audit_path=new_audit(), **kw)


# ================================================================================================ one experiment cell
def run_cell(corpus: Corpus, n: int, clip: float, sigma: float, seeds, targets) -> dict:
    clients = corpus.clients(n)
    eng.PUBLIC_EVALUATION = corpus.public(n)
    keys = ("ppl_before", "acc_before", "ppl_after", "acc_after", "auc_same_before", "auc_same_after", "auc_other_before",
            "auc_other_after", "retention", "ref_l2")
    acc = {k: [] for k in keys}
    certified = total = 0
    eps = None
    for seed in seeds:
        e0 = make_engine(clients, clip_norm=clip, noise_multiplier=sigma, random_seed=seed)
        m = e0.train()
        eps = e0.epsilon
        for t in targets:
            e = copy.deepcopy(e0)
            e.audit = AuditLedger(new_audit())
            cid = clients[t].client_id
            members = clients[t].records
            eng.NON_MEMBER_TEXTS = corpus.heldout(t)
            before_model = e.model
            cert = e.unlearn(cid)
            other = corpus.other_nonmembers(t, n)
            acc["ppl_before"].append(cert.perplexity_before)
            acc["acc_before"].append(cert.accuracy_before)
            acc["ppl_after"].append(cert.perplexity_after)
            acc["acc_after"].append(cert.accuracy_after)
            acc["auc_same_before"].append(cert.membership_auc_before)
            acc["auc_same_after"].append(cert.membership_auc_after)
            acc["auc_other_before"].append(membership_auc(before_model, members, other))
            acc["auc_other_after"].append(membership_auc(e.model, members, other))
            acc["retention"].append(cert.utility_retention_percent)
            acc["ref_l2"].append(cert.reference_retrain_l2)
            certified += cert.status == "CERTIFIED"
            total += 1
    out = {"n_clients": n, "clip_norm": clip, "sigma": sigma, "epsilon": eps, "requests": total, "certified_fraction": certified / total}
    for k, v in acc.items():
        out[k] = mean_sd(v)
    return out


# ================================================================================================ sections
def section_norms(corpus: Corpus) -> dict:
    norms = [_ORIG_CLIPPED(corpus.client(i).records, 1e18)[1] for i in range(20)]
    ntoks = [sum(len(r) + 1 for r in corpus.client(i).records) for i in range(20)]
    prod = [_ORIG_CLIPPED(c.records, 25.0)[2] for c in corpus.clients(20)]
    return {"raw_update_norms_20_clients": norms, "median": st.median(norms), "mean": st.fmean(norms), "min": min(norms), "max": max(norms),
            "characters_per_client_mean": st.fmean(ntoks), "scale_applied_by_product_C25": mean_sd(prod),
            "ratio_median_norm_to_C25": st.median(norms) / 25.0}


def section_sweep(corpus: Corpus) -> dict:
    sigmas = [1e-9, 0.001, 0.01, 0.1, 0.3, 1.0, 3.0, 10.0]
    seeds, targets = list(range(10)), list(range(5))
    rows = []
    for n in (5, 10, 20):
        norms = [_ORIG_CLIPPED(corpus.client(i).records, 1e18)[1] for i in range(n)]
        med = st.median(norms)
        for s in sigmas:
            r = run_cell(corpus, n, med, s, seeds, targets)
            r["clip_mode"] = "median"
            rows.append(r)
            print(f"sweep n={n} sigma={s:g} ppl={r['ppl_before']['mean']:.1f} auc_same {r['auc_same_before']['mean']:.3f}->{r['auc_same_after']['mean']:.3f}", flush=True)
    return {"seeds": len(seeds), "targets": len(targets), "rows": rows, "uniform_perplexity": len(ALPHABET) - 1}


def section_clip(corpus: Corpus) -> dict:
    n = 10
    norms = [_ORIG_CLIPPED(corpus.client(i).records, 1e18)[1] for i in range(n)]
    med = st.median(norms)
    rows = []
    for mode, C in (("C = 25 (product default)", 25.0), ("C = median raw norm", med), ("C = 2 x median raw norm", 2 * med)):
        for s in (1e-9, 0.01, 0.1, 0.3, 1.0, 3.0):
            r = run_cell(corpus, n, C, s, list(range(10)), list(range(5)))
            r["clip_mode"] = mode
            rows.append(r)
        print("clip", mode, flush=True)
    return {"n_clients": n, "median_norm": med, "rows": rows}


def l2(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def section_gold(corpus: Corpus) -> dict:
    n = 10
    clients = corpus.clients(n)
    med = st.median([_ORIG_CLIPPED(c.records, 1e18)[1] for c in clients])
    eng.PUBLIC_EVALUATION = corpus.public(n)
    results = []
    for sigma, n_seeds in ((1e-9, 10), (0.1, 20), (1.0, 20)):
        d_ur, d_rr, a_u, a_r, ao_u, ao_r, p_u, p_r = ([] for _ in range(8))
        for seed in range(n_seeds):
            e0 = make_engine(clients, clip_norm=med, noise_multiplier=sigma, random_seed=seed)
            e0.train()
            for t in range(5):
                e = copy.deepcopy(e0)
                e.audit = AuditLedger(new_audit())
                eng.NON_MEMBER_TEXTS = corpus.heldout(t)
                e.unlearn(clients[t].client_id)
                retained = [c for k, c in enumerate(clients) if k != t]
                r1 = make_engine(retained, clip_norm=med, noise_multiplier=sigma, random_seed=10_000 + seed)
                r1.train()
                r2 = make_engine(retained, clip_norm=med, noise_multiplier=sigma, random_seed=20_000 + seed)
                r2.train()
                other = corpus.other_nonmembers(t, n)
                members = clients[t].records
                d_ur.append(l2(e.model.parameters, r1.model.parameters))
                d_rr.append(l2(r1.model.parameters, r2.model.parameters))
                a_u.append(membership_auc(e.model, members, corpus.heldout(t)))
                a_r.append(membership_auc(r1.model, members, corpus.heldout(t)))
                ao_u.append(membership_auc(e.model, members, other))
                ao_r.append(membership_auc(r1.model, members, other))
                p_u.append(e.model.perplexity(eng.PUBLIC_EVALUATION))
                p_r.append(r1.model.perplexity(eng.PUBLIC_EVALUATION))
        results.append({"sigma": sigma, "pairs": len(d_ur), "l2_unlearned_vs_fresh_retrain": mean_sd(d_ur),
                        "l2_fresh_retrain_vs_fresh_retrain": mean_sd(d_rr), "auc_same_unlearned": mean_sd(a_u), "auc_same_fresh_retrain": mean_sd(a_r),
                        "auc_other_unlearned": mean_sd(ao_u), "auc_other_fresh_retrain": mean_sd(ao_r),
                        "perplexity_unlearned": mean_sd(p_u), "perplexity_fresh_retrain": mean_sd(p_r)})
        print("gold sigma", sigma, flush=True)
    return {"n_clients": n, "clip_norm": med, "results": results}


def section_n_sweep() -> dict:
    """Does averaging over more clients make sigma >= 4.85 (epsilon < 1) usable?  100 sentences per client."""
    corpus = Corpus(per_client=100, held_out=100)
    ns = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 4000]
    sigmas = [1.0, 3.0, 4.85, 10.0]
    rows = []
    for n in ns:
        clients = corpus.clients(n)
        med = st.median([fast_clipped_update(c.records, 1e18)[1] for c in clients])
        eng.PUBLIC_EVALUATION = corpus.public(n)
        free = make_engine(clients, clip_norm=med, noise_multiplier=1e-9, random_seed=0)
        mf = free.train()
        seeds = 5 if n <= 1000 else 3
        for s in sigmas:
            ppl, acc = [], []
            for seed in range(seeds):
                e = make_engine(clients, clip_norm=med, noise_multiplier=s, random_seed=seed)
                m = e.train()
                ppl.append(m.perplexity)
                acc.append(m.next_character_accuracy)
            rows.append({"n_clients": n, "sigma": s, "epsilon": eps_of(s), "clip_norm": med, "seeds": seeds,
                         "perplexity": mean_sd(ppl), "accuracy": mean_sd(acc), "noise_free_perplexity": mf.perplexity,
                         "noise_free_accuracy": mf.next_character_accuracy, "ratio_to_noise_free": st.fmean(ppl) / mf.perplexity,
                         "within_1_2x": st.fmean(ppl) / mf.perplexity <= 1.2})
        print("n sweep", n, [round(r["ratio_to_noise_free"], 2) for r in rows[-len(sigmas):]], flush=True)
        _raw_cache_trim(keep=n)
    best = {}
    for s in sigmas:
        hits = [r["n_clients"] for r in rows if r["sigma"] == s and r["within_1_2x"]]
        best[str(s)] = min(hits) if hits else None
    # unlearning at the smallest n for sigma = 4.85
    unl = None
    n_star = best.get("4.85")
    if n_star:
        clients = corpus.clients(n_star)
        med = st.median([fast_clipped_update(c.records, 1e18)[1] for c in clients])
        eng.PUBLIC_EVALUATION = corpus.public(n_star)
        e = make_engine(clients, clip_norm=med, noise_multiplier=4.85, random_seed=0)
        e.train()
        steps = []
        for t in range(5):
            eng.NON_MEMBER_TEXTS = corpus.heldout(t)
            before = e.model
            cert = e.unlearn(clients[t].client_id)
            other = corpus.other_nonmembers(t, 20)
            steps.append({"client": clients[t].client_id, "status": cert.status, "reference_l2": cert.reference_retrain_l2,
                          "retention_percent": cert.utility_retention_percent, "ppl_before": cert.perplexity_before, "ppl_after": cert.perplexity_after,
                          "auc_same_before": cert.membership_auc_before, "auc_same_after": cert.membership_auc_after,
                          "auc_other_before": membership_auc(before, clients[t].records, other),
                          "auc_other_after": membership_auc(e.model, clients[t].records, other)})
        unl = {"n_clients": n_star, "sigma": 4.85, "epsilon": eps_of(4.85), "sequential_removals": steps}
    return {"per_client_sentences": 100, "rows": rows, "smallest_n_within_1_2x": best, "unlearning_at_smallest_n": unl}


def _raw_cache_trim(keep: int) -> None:
    """Nothing to trim: raw counts are reused by larger n (clients are nested).  Kept for clarity."""
    return None


def section_timing(corpus: Corpus) -> dict:
    """UNPATCHED engine; n = 20 clients x 200 sentences; median of 5 repetitions (seconds -> ms)."""
    n = 20
    clients = corpus.clients(n)
    eng.PUBLIC_EVALUATION = corpus.public(n)
    med = st.median([_ORIG_CLIPPED(c.records, 1e18)[1] for c in clients])
    tr, un, rt = [], [], []
    for rep in range(5):
        e = make_engine(clients, clip_norm=med, noise_multiplier=1.0, random_seed=rep)
        t0 = time.perf_counter(); e.train(); tr.append((time.perf_counter() - t0) * 1000)
        eng.NON_MEMBER_TEXTS = corpus.heldout(0)
        t0 = time.perf_counter(); e.unlearn(clients[0].client_id); un.append((time.perf_counter() - t0) * 1000)
        r = make_engine(clients[1:], clip_norm=med, noise_multiplier=1.0, random_seed=rep)
        t0 = time.perf_counter(); r.train(); rt.append((time.perf_counter() - t0) * 1000)
    print("timing", st.median(tr), st.median(un), st.median(rt), flush=True)
    return {"n_clients": n, "sentences_per_client": 200, "eval_sentences": 300, "nonmember_sentences": 200, "engine": "unmodified classes",
            "train_ms_median": st.median(tr), "unlearn_ms_median": st.median(un), "retrain_retained_ms_median": st.median(rt),
            "retrain_over_unlearn": st.median(rt) / st.median(un), "repetitions": 5,
            "note": "unlearn() includes the metrics before and after, two membership attacks and the audit write; train() includes one metrics call."}


# ================================================================================================ timeline from git
def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=BATCH, capture_output=True, text=True, encoding="utf-8").stdout


def commits(path) -> list[dict]:
    specs = [path] if isinstance(path, str) else list(path)
    out = []
    for line in git("log", "--format=%H|%ad|%s", "--date=short", "--", *specs).splitlines():
        h, d, s = line.split("|", 2)
        num = git("show", "--numstat", "--format=", h, "--", *specs).splitlines()
        files = ins = dele = 0
        for row in num:
            parts = row.split("\t")
            if len(parts) == 3:
                files += 1
                ins += int(parts[0]) if parts[0].isdigit() else 0
                dele += int(parts[1]) if parts[1].isdigit() else 0
        out.append({"commit": h[:8], "date": d, "message": s, "files_in_path": files, "lines_added": ins, "lines_deleted": dele})
    return sorted(out, key=lambda c: c["date"])


def section_timeline() -> dict:
    import datetime
    paths = {"batch folder": ".", "8.ProjectCode": "8.ProjectCode", "certified_unlearning (backend)": "8.ProjectCode/certified_unlearning",
             "frontend": "8.ProjectCode/frontend", "docs": "8.ProjectCode/docs", "root documents": [":(glob)*.docx", ":(glob)*.pptx"]}
    per = {k: commits(v) for k, v in paths.items()}
    first_seen = {}
    for p in ("8.ProjectCode/certified_unlearning/engine.py", "8.ProjectCode/certified_unlearning/web.py", "8.ProjectCode/tests/test_end_to_end.py",
              "8.ProjectCode/scripts/smoke_test.py", "8.ProjectCode/frontend/src/App.jsx", "8.ProjectCode/docs/FRONTEND_PLAN.md", "1.A9_BATCH_DETAILS.docx",
              "2.ABSTRACT.docx", "7.Review_1_PPT.pptx", "8.ProjectCode/PROJECT_REPORT.md", "8.ProjectCode/README.md"):
        lines = git("log", "--format=%ad|%h|%s", "--date=short", "--diff-filter=A", "--", p).splitlines()
        first_seen[p] = lines[-1] if lines else None
    mtimes = {}
    for p in sorted(BATCH.glob("[1-6].*")) + [BATCH / "8.ProjectCode" / f for f in ("app.py", "README.md", "PROJECT_REPORT.md")]:
        if p.exists():
            mtimes[p.name] = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    for p in sorted((BATCH / "8.ProjectCode" / "certified_unlearning").glob("*.py")) + sorted((BATCH / "8.ProjectCode" / "tests").glob("*.py")):
        mtimes["8.ProjectCode/" + p.relative_to(BATCH / "8.ProjectCode").as_posix()] = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    for folder in ("Documentary", "archived_base_papers"):
        for p in sorted((BATCH / folder).glob("*.pdf")):
            mtimes[f"{folder}/{p.name[:48]}"] = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    all_dates = sorted({c["date"] for v in per.values() for c in v})

    def find(path_key, fragment):
        return next(c for c in per[path_key] if fragment in c["message"])

    c_init, c_ignore, c_restore = find("batch folder", "Initial project files"), find("batch folder", "gitignore"), find("batch folder", "Restore CSDS")
    c_front, c_docs = find("frontend", "Rebuild frontend"), find("8.ProjectCode", "Add project documentation")
    c_back = per["certified_unlearning (backend)"][0]
    phases = [
        {"date": "2026-09-16 to 2026-09-19", "phase": "Batch documents prepared", "evidence": "file modification times of 1.-6. batch documents (2026-09-19) and of the base-paper PDFs; not in git history", "source": "filesystem mtimes"},
        {"date": c_init["date"], "phase": "Repository set-up: initial project files, batch folders and master prompts", "evidence": f"commit {c_init['commit']} ({c_init['files_in_path']} files in the batch folder); commits 57ebf6ff, c527e811, d04fd80b, 9a8a1f80 the same day", "source": "git"},
        {"date": c_back["date"], "phase": "Backend implementation: first commit that contains certified_unlearning/, tests/, README and PROJECT_REPORT", "evidence": f"commit {c_back['commit']}: {c_back['files_in_path']} backend files, {c_back['lines_added']} lines; file modification times of the backend files are also 2026-09-25", "source": "git + mtimes"},
        {"date": c_restore["date"], "phase": "Prompt files restored", "evidence": f"commit {c_restore['commit']} ({c_restore['files_in_path']} files)", "source": "git"},
        {"date": c_front["date"], "phase": "React front end built over the unchanged API", "evidence": f"commit {c_front['commit']}: {c_front['files_in_path']} files, {c_front['lines_added']} lines in frontend/; docs/FRONTEND_PLAN.md and scripts/smoke_test.py added in the same commit", "source": "git"},
        {"date": c_docs["date"], "phase": "Measurements, screenshots, diagrams and the eleven submission documents", "evidence": f"commit {c_docs['commit']}: {c_docs['files_in_path']} files under 8.ProjectCode and the root documents", "source": "git"},
    ]
    undatable = ["Design and implementation steps before the 2026-09-25 commit (the backend has no history of its own; git shows it arriving in one commit)",
                 "Dates of guide meetings, reviews and test runs (not recorded in the repository)",
                 "The calendar of the report writing other than the 2026-10-26 commit"]
    return {"phases": phases, "undatable": undatable, "source": "git log of the shared repository restricted to this batch folder, plus file modification times (filesystem facts)",
            "commits_by_path": per, "first_commit_that_added_file": first_seen, "file_mtimes": mtimes, "distinct_commit_dates": all_dates}


# ================================================================================================ charts
def charts(syn: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    INDIGO, MINT, ROSE, AMBER, SKY, INK, GREY = "#5b5bd6", "#2f9e77", "#d6455d", "#e0a030", "#3b8ed0", "#1b2238", "#9aa5ba"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK,
                         "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e7ef",
                         "grid.linewidth": 0.7, "axes.axisbelow": True})
    charts_dir = ROOT / "docs" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    def save_fig(fig, name):
        fig.savefig(charts_dir / name, dpi=150, facecolor="white", bbox_inches="tight")
        plt.close(fig)
        print("saved", name, flush=True)

    rows = syn["sweep"]["rows"]
    # s01: noise sweep on the synthetic corpus
    fig, ax = plt.subplots(1, 2, figsize=(8.8, 3.4))
    cols = {5: INDIGO, 10: MINT, 20: AMBER}
    for n, col in cols.items():
        rr = [r for r in rows if r["n_clients"] == n and r["sigma"] > 1e-6]
        free = [r for r in rows if r["n_clients"] == n and r["sigma"] <= 1e-6][0]
        ax[0].errorbar([r["sigma"] for r in rr], [r["ppl_before"]["mean"] for r in rr], yerr=[r["ppl_before"]["sd"] for r in rr], color=col, marker="o", ms=4,
                       capsize=2, lw=1.4, label=f"n = {n} clients")
        ax[0].axhline(free["ppl_before"]["mean"], color=col, ls=":", lw=1)
    ax[0].axhline(32, color=ROSE, ls="--", lw=1, label="uniform (32)")
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel("noise multiplier sigma"); ax[0].set_ylabel("public-set perplexity (dotted: no noise)")
    ax[0].axvline(4.85, color=GREY, ls=":", lw=1); ax[0].text(4.5, 9, "epsilon < 1\nright of here", fontsize=7.5, ha="right", color=INK)
    ax[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    ax[0].set_title("Synthetic corpus (200 sentences/client)", fontsize=9.5, fontweight="bold")
    sel = [r for r in rows if r["n_clients"] == 10]
    sg = [r["sigma"] for r in sel if r["sigma"] > 1e-6]
    ax[1].plot(sg, [r["auc_same_before"]["mean"] for r in sel if r["sigma"] > 1e-6], color=INDIGO, marker="o", ms=4, lw=1.4, label="held-out of same client, before")
    ax[1].plot(sg, [r["auc_same_after"]["mean"] for r in sel if r["sigma"] > 1e-6], color=INDIGO, marker="o", ms=4, lw=1.4, ls="--", label="same client, after")
    ax[1].plot(sg, [r["auc_other_before"]["mean"] for r in sel if r["sigma"] > 1e-6], color=MINT, marker="s", ms=4, lw=1.4, label="other clients' text, before")
    ax[1].plot(sg, [r["auc_other_after"]["mean"] for r in sel if r["sigma"] > 1e-6], color=MINT, marker="s", ms=4, lw=1.4, ls="--", label="other clients, after")
    ax[1].axhline(0.5, color=ROSE, ls="--", lw=1)
    ax[1].set_xscale("log"); ax[1].set_xlabel("noise multiplier sigma"); ax[1].set_ylabel("membership AUC (200 vs 200)"); ax[1].set_ylim(0.0, 0.7)
    ax[1].legend(frameon=False, fontsize=7, loc="upper right")
    ax[1].set_title("Membership attack, n = 10 clients", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "s01_synthetic_noise_sweep.png")

    # s02: clip-norm choice
    fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.3))
    clip_rows = syn["clip"]["rows"]
    modes = []
    for r in clip_rows:
        if r["clip_mode"] not in modes:
            modes.append(r["clip_mode"])
    for mode, col in zip(modes, (ROSE, INDIGO, MINT)):
        rr = [r for r in clip_rows if r["clip_mode"] == mode and r["sigma"] > 1e-6]
        ax[0].plot([r["sigma"] for r in rr], [r["ppl_before"]["mean"] for r in rr], marker="o", ms=4, lw=1.4, color=col, label=mode)
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("noise multiplier sigma"); ax[0].set_ylabel("perplexity (n = 10)")
    ax[0].legend(frameon=False, fontsize=7.5); ax[0].set_title("Perplexity by clip-norm choice", fontsize=9.5, fontweight="bold")
    free = [(m, [r for r in clip_rows if r["clip_mode"] == m and r["sigma"] <= 1e-6][0]) for m in modes]
    ax[1].bar(range(len(free)), [f[1]["ppl_before"]["mean"] for f in free], color=[ROSE, INDIGO, MINT], width=0.55)
    for i, f in enumerate(free):
        ax[1].text(i, f[1]["ppl_before"]["mean"] + 0.5, f"{f[1]['ppl_before']['mean']:.1f}", ha="center", fontsize=8)
    ax[1].set_xticks(range(len(free))); ax[1].set_xticklabels(["C = 25", "C = median", "C = 2 x median"], fontsize=8)
    ax[1].set_ylabel("perplexity without noise"); ax[1].set_title("Without noise: scale vs fixed smoothing", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "s02_clip_norm_choice.png")

    # s03: n needed for epsilon < 1
    nrows = syn["n_sweep"]["rows"]
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    for s, col in zip((1.0, 3.0, 4.85, 10.0), (SKY, AMBER, MINT, INDIGO)):
        rr = [r for r in nrows if r["sigma"] == s]
        lab = f"sigma = {s:g} (epsilon {eps_of(s):.2f})"
        ax.plot([r["n_clients"] for r in rr], [r["ratio_to_noise_free"] for r in rr], marker="o", ms=4, lw=1.4, color=col, label=lab)
    ax.axhline(1.2, color=ROSE, ls="--", lw=1); ax.text(5.2, 1.27, "1.2 x noise-free", color=ROSE, fontsize=7.5)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("number of federated clients n (100 sentences each)")
    ax.set_ylabel("perplexity / noise-free perplexity")
    ax.legend(frameon=False, fontsize=7.5); ax.set_title("More clients average the noise away", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "s03_clients_needed_for_epsilon_below_1.png")

    # s04: fresh retrain comparison
    g = syn["gold"]["results"]
    g = [r for r in g if r["sigma"] > 1e-6]
    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))
    for a_, r in zip(ax, g):
        a = r["l2_unlearned_vs_fresh_retrain"]; b = r["l2_fresh_retrain_vs_fresh_retrain"]
        a_.bar([0, 1], [a["mean"], b["mean"]], yerr=[a["sd"], b["sd"]], color=[INDIGO, AMBER], capsize=4, width=0.55)
        a_.set_xticks([0, 1]); a_.set_xticklabels(["unlearned vs\nfresh retrain", "fresh retrain vs\nfresh retrain"], fontsize=8)
        a_.set_ylabel("L2 distance between models"); a_.set_title(f"sigma = {r['sigma']:g}, n = 10 ({r['pairs']} pairs)", fontsize=9.5, fontweight="bold")
        for i, v in enumerate([a["mean"], b["mean"]]):
            a_.text(i, v * 0.5, f"{v:.0f}", ha="center", color="white", fontsize=9, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "s04_synthetic_fresh_retrain.png")


# ================================================================================================ main
def main() -> None:
    wanted = sys.argv[1:]
    if wanted == ["timeline"]:
        save("timeline", section_timeline())
        return
    t0 = time.perf_counter()
    corpus = Corpus(per_client=200)
    lens = [len(c.records) for c in corpus.clients(20)]
    print("corpus ok", min(lens), max(lens), flush=True)
    # data-only patches for the unmodified-engine timing section
    out: dict = {"design": {
        "generator": "seeded template grammar, 12 sentence templates + 3 private-word templates, 20 domain vocabularies, six private pseudo-words per client (used in ~30 % of sentences)",
        "per_client_train_sentences": 200, "per_client_held_out_sentences": 200, "public_evaluation_sentences": 300,
        "membership_auc_resolution": 1 / (200 * 200) * 2, "uniform_perplexity": len(ALPHABET) - 1, "delta": DELTA,
        "auc_same": "client's 200 training sentences vs its own 200 held-out sentences (same generator: hard)",
        "auc_other": "client's 200 training sentences vs 200 held-out sentences of the other clients (the product's 'unrelated text' design)",
        "example_sentences": {d: list(corpus.client(i).records[:2]) for i, d in enumerate(DOMAIN_NAMES[:5])},
    }}
    out["timing"] = section_timing(corpus)  # unmodified classes
    apply_patches()
    out["patch_equivalence"] = check_patch_equivalence(corpus)
    out["raw_norms"] = section_norms(corpus)
    out["sweep"] = section_sweep(corpus)
    out["clip"] = section_clip(corpus)
    out["gold"] = section_gold(corpus)
    out["n_sweep"] = section_n_sweep()
    out["runtime_seconds"] = time.perf_counter() - t0
    save("synthetic_corpus", out)
    save("timeline", section_timeline())
    charts(out)
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
