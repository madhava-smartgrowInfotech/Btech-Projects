"""ForgetSafe's method on a small real neural language model with a LoRA-style adapter, trained on SYNTHETIC text.

    python scripts/run_neural_experiment.py            # pre-train, pilot, 5 seeds, charts  (~10-15 min on 4 CPU threads)

What is applied, unchanged from the product (certified_unlearning/engine.py):
  clip each client's parameter update to L2 norm C  ->  sum  ->  add N(0, (sigma*C)^2) per coordinate  ->  divide by n;
  unlearn client j by subtracting its stored clipped update from the noisy sum and dividing by (n-1), keeping the same noise.
What differs: the model is a character-level GRU (frozen base, pre-trained on a synthetic public pool) with a low-rank
adapter (LoRA-FA: the down-projection A is a fixed random matrix shared by all clients, so averaging the trainable
factors B is exactly averaging the weight updates).  The only trainable, communicated parameters are the B factors.

Everything is synthetic: a grammar-based text generator makes 8 client domains (own pseudo-word vocabularies and sentence
templates), a public pool and one outsider domain that never joins the federation.  Results are recorded as measured.
"""
from __future__ import annotations

import torch  # noqa: I001  (must be imported before anything else on this machine)

import json
import math
import os
import platform
import random
import statistics as st
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

torch.set_num_threads(4)
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "neural_adapter"
CHARTS = ROOT / "docs" / "charts"
CACHE = Path(os.environ.get("NA_CACHE", tempfile.gettempdir())) / "forgetsafe_neural_cache"
CACHE.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------------------------- configuration
CFG = {
    "n_clients": 8, "train_per_client": 150, "heldout_per_client": 150, "public_eval": 200, "public_train": 6000,
    "outsider_sentences": 150, "max_len": 72,
    "syllable_inventory_per_domain": 14, "domain_words": {"N": 20, "V": 15, "A": 15}, "templates_per_domain": [6, 10],
    "public_inventory": 20, "public_words": {"N": 40, "V": 30, "A": 30},
    "corpus_seed": 1,
    "base": {"emb": 32, "hidden": 192, "pretrain_steps": 2500, "batch": 64, "lr": 3e-3, "lr_late": 1e-3, "seed": 0},
    "adapter": {"kind": "LoRA-FA on hidden state (residual) and output projection; A frozen+shared, only B trained", "lr": 5e-3,
                "batch_tokens": 256, "optimizer": "Adam"},
    "pilot": {"client": 0, "seed": 99, "ranks": [4, 16, 64], "epochs": [20, 60],
              "rule": "choose the (rank, epochs) with the lowest held-out perplexity on the pilot client; ties -> smaller rank"},
    "seeds": [0, 1, 2, 3, 4], "sigmas": [0.0, 0.003, 0.01, 0.03, 0.05, 0.1, 0.3, 1.0, 3.0], "delta": 1e-5,
    "sequential_sigmas": [0.0, 0.01, 0.1], "sequential_order": [0, 1, 2],
    "ppl_cap": 1e9, "clip_rule": "C = median of the raw adapter update norms of the 8 clients (per seed)",
}

CONS = "bdfgklmnprstvz"
VOW = "aeiou"
ALL_SYL = [c + v for c in CONS for v in VOW]
SKELETONS = ["the A N V the N .", "a N V the A N .", "the N of the N V .", "A N and A N V .", "the N V a N with the N .", "a A N is A .",
             "the N V to the N .", "N V the N and the N .", "the A A N V .", "a N in the N V the A N .", "the N and the N V A .",
             "a N V with a A N .", "the N is in the A N .", "A N V the N of the N .", "the N V and the N V .", "a A N of the N is A ."]
CHARS = "abcdefghijklmnopqrstuvwxyz ."
PAD, BOS, EOS = 0, 1, 2
PPL_CAP_LOG = math.log(1e9)   # perplexities above 1e9 (noise-destroyed models) are recorded as 1e9
IDX = {c: i + 3 for i, c in enumerate(CHARS)}
V = len(CHARS) + 3


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------------------------------------- synthetic corpus
def make_words(rng, inventory, counts):
    words, out = set(), {}
    for kind, n in counts.items():
        out[kind] = []
        while len(out[kind]) < n:
            w = "".join(rng.choice(inventory) for _ in range(rng.choice([2, 3])))
            if w not in words:
                words.add(w)
                out[kind].append(w)
    return out


class Domain:
    def __init__(self, seed, public=False):
        rng = random.Random(seed)
        if public:
            self.inv = rng.sample(ALL_SYL, CFG["public_inventory"])
            self.words = make_words(rng, self.inv, CFG["public_words"])
            self.templates = list(SKELETONS)
        else:
            self.inv = rng.sample(ALL_SYL, CFG["syllable_inventory_per_domain"])
            self.words = make_words(rng, self.inv, CFG["domain_words"])
            lo, hi = CFG["templates_per_domain"]
            self.templates = rng.sample(SKELETONS, rng.randint(lo, hi))

    def sentence(self, rng):
        toks = rng.choice(self.templates).split()
        out = [rng.choice(self.words[t]) if t in self.words else t for t in toks]
        return " ".join(out).replace(" .", ".")

    def unique(self, n, rng, exclude=()):
        seen, out = set(exclude), []
        while len(out) < n:
            s = self.sentence(rng)
            if len(s) <= CFG["max_len"] - 2 and s not in seen:
                seen.add(s)
                out.append(s)
        return out


def encode(sents):
    L = CFG["max_len"]
    X = np.zeros((len(sents), L), dtype=np.int64)
    Y = np.zeros((len(sents), L), dtype=np.int64)
    for i, s in enumerate(sents):
        ids = [IDX[c] for c in s]
        x = [BOS] + ids
        y = ids + [EOS]
        X[i, :len(x)] = x
        Y[i, :len(y)] = y
    return torch.from_numpy(X), torch.from_numpy(Y)


# ---------------------------------------------------------------------------------------------- base model
class Base(torch.nn.Module):
    def __init__(self):
        super().__init__()
        b = CFG["base"]
        self.emb = torch.nn.Embedding(V, b["emb"], padding_idx=0)
        self.gru = torch.nn.GRU(b["emb"], b["hidden"], batch_first=True)
        self.head = torch.nn.Linear(b["hidden"], V)

    def hidden(self, X):
        return self.gru(self.emb(X))[0]

    def forward(self, X):
        return self.head(self.hidden(X))


def pretrain(public_train, public_eval):
    path = CACHE / "base.pt"
    torch.manual_seed(CFG["base"]["seed"])
    model = Base()
    n_params = sum(p.numel() for p in model.parameters())
    if path.exists():
        model.load_state_dict(torch.load(path))
        log("loaded cached base model", path)
    else:
        X, Y = encode(public_train)
        opt = torch.optim.Adam(model.parameters(), lr=CFG["base"]["lr"])
        g = torch.Generator().manual_seed(CFG["base"]["seed"])
        t0 = time.perf_counter()
        for step in range(CFG["base"]["pretrain_steps"]):
            if step == 1500:
                for pg in opt.param_groups:
                    pg["lr"] = CFG["base"]["lr_late"]
            idx = torch.randint(0, X.shape[0], (CFG["base"]["batch"],), generator=g)
            x, y = X[idx], Y[idx]
            loss = torch.nn.functional.cross_entropy(model(x).reshape(-1, V), y.reshape(-1), ignore_index=PAD)
            opt.zero_grad(); loss.backward(); opt.step()
            if step % 500 == 0:
                log(f"pretrain step {step} loss {loss.item():.4f}")
        log(f"pretraining took {time.perf_counter() - t0:.1f}s")
        torch.save(model.state_dict(), path)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model, n_params


class Data:
    """Frozen-GRU hidden states and targets of one set of sentences, flattened over tokens."""

    def __init__(self, model, sents):
        X, Y = encode(sents)
        with torch.no_grad():
            H = model.hidden(X)
        m = Y != PAD
        self.H = H[m].contiguous()
        self.Y = Y[m].contiguous()
        counts = m.sum(1)
        self.starts = torch.cumsum(counts, 0) - counts
        self.counts = counts
        self.n_sent = len(sents)
        self.n_tok = int(counts.sum())


class Concat:
    """All evaluation sets stacked so that one forward pass scores every set."""

    def __init__(self, named):
        self.names = list(named)
        self.H = torch.cat([named[k].H for k in self.names])
        self.Y = torch.cat([named[k].Y for k in self.names])
        self.sent_starts, self.sent_slices, self.tok_slices = [], {}, {}
        tok_off = sent_off = 0
        starts = []
        for k in self.names:
            d = named[k]
            starts.append(d.starts + tok_off)
            self.tok_slices[k] = (tok_off, tok_off + d.n_tok)
            self.sent_slices[k] = (sent_off, sent_off + d.n_sent)
            tok_off += d.n_tok
            sent_off += d.n_sent
        self.sent_starts = torch.cat(starts).numpy()
        self.counts = torch.cat([named[k].counts for k in self.names]).numpy()


# ---------------------------------------------------------------------------------------------- adapter
class Adapter:
    """theta = [B_hid (hidden x r), B_out (V x r)] flattened; A matrices fixed and shared."""

    def __init__(self, model, r, seed):
        self.r = r
        self.hid = CFG["base"]["hidden"]
        g = torch.Generator().manual_seed(1000 + seed)
        self.A_h = torch.randn(r, self.hid, generator=g) / math.sqrt(self.hid)
        self.A_o = torch.randn(r, self.hid, generator=g) / math.sqrt(self.hid)
        self.W, self.b = model.head.weight, model.head.bias
        self.dim = self.hid * r + V * r

    def logits(self, theta, H):
        Bh = theta[:self.hid * self.r].view(self.hid, self.r)
        Bo = theta[self.hid * self.r:].view(V, self.r)
        h2 = H + (H @ self.A_h.T) @ Bh.T
        return h2 @ self.W.T + self.b + (h2 @ self.A_o.T) @ Bo.T


def train_adapter(ad, data, epochs, seed):
    theta = torch.zeros(ad.dim, requires_grad=True)
    opt = torch.optim.Adam([theta], lr=CFG["adapter"]["lr"])
    g = torch.Generator().manual_seed(seed)
    bs = CFG["adapter"]["batch_tokens"]
    t0 = time.perf_counter()
    for _ in range(epochs):
        perm = torch.randperm(data.n_tok, generator=g)
        for i in range(0, data.n_tok, bs):
            idx = perm[i:i + bs]
            loss = torch.nn.functional.cross_entropy(ad.logits(theta, data.H[idx]), data.Y[idx])
            opt.zero_grad(); loss.backward(); opt.step()
    return theta.detach(), time.perf_counter() - t0


def score(ad, theta, cat):
    """Per-token NLL and correctness over the stacked evaluation sets."""
    with torch.no_grad():
        lg = ad.logits(theta, cat.H)
        nll = torch.nn.functional.cross_entropy(lg, cat.Y, reduction="none")
        ok = (lg.argmax(1) == cat.Y).float()
    return nll.numpy(), ok.numpy()


class Scores:
    def __init__(self, cat, nll, ok):
        self.cat, self.nll, self.ok = cat, nll, ok
        self.sent_nll = np.add.reduceat(nll, cat.sent_starts) / cat.counts   # mean NLL per sentence

    def ppl(self, *names):
        a = np.concatenate([self.nll[slice(*self.cat.tok_slices[n])] for n in names])
        return float(math.exp(min(float(a.mean()), PPL_CAP_LOG)))

    def acc(self, *names):
        return float(np.concatenate([self.ok[slice(*self.cat.tok_slices[n])] for n in names]).mean())

    def sent(self, name):
        return self.sent_nll[slice(*self.cat.sent_slices[name])]


def auc(neg_nll_members, neg_nll_non):
    """Probability that a member (lower NLL) scores above a non-member; ties count 1/2."""
    m, n = -np.asarray(neg_nll_members), -np.asarray(neg_nll_non)
    return float(((m[:, None] > n[None, :]).mean() + 0.5 * (m[:, None] == n[None, :]).mean()))


def mean_sd(v):
    v = [float(x) for x in v]
    return {"mean": st.fmean(v), "sd": st.stdev(v) if len(v) > 1 else 0.0, "n": len(v), "min": min(v), "max": max(v)}


def eps_of(sigma, delta=1e-5):
    return math.sqrt(2.0 * math.log(1.25 / delta)) / sigma if sigma > 0 else float("inf")


# ---------------------------------------------------------------------------------------------- the experiment
def main() -> None:
    t_start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    log("generating synthetic corpus")
    crng = random.Random(CFG["corpus_seed"])
    pub = Domain(CFG["corpus_seed"] * 7919, public=True)
    pool = pub.unique(CFG["public_train"] + CFG["public_eval"], crng)
    public_train, public_eval = pool[:CFG["public_train"]], pool[CFG["public_train"]:]
    n = CFG["n_clients"]
    domains = [Domain(CFG["corpus_seed"] * 101 + 17 * i) for i in range(n)]
    outsider = Domain(CFG["corpus_seed"] * 101 + 9999)
    train, held = [], []
    for d in domains:
        both = d.unique(CFG["train_per_client"] + CFG["heldout_per_client"], crng)
        train.append(both[:CFG["train_per_client"]])
        held.append(both[CFG["train_per_client"]:])
    out_sents = outsider.unique(CFG["outsider_sentences"], crng)
    examples = {"public": public_eval[:3], "client_0_train": train[0][:3], "client_0_heldout": held[0][:3], "client_3_train": train[3][:3], "outsider": out_sents[:3]}
    corpus_stats = {
        "domains": [{"client": i, "templates": len(d.templates), "words": {k: len(v) for k, v in d.words.items()},
                     "syllables": len(d.inv), "mean_len": st.fmean(len(s) for s in train[i])} for i, d in enumerate(domains)],
        "train_overlap_with_heldout": sum(len(set(train[i]) & set(held[i])) for i in range(n)),
        "domain_word_overlap_between_clients_mean": st.fmean(
            len(set(sum(domains[i].words.values(), [])) & set(sum(domains[j].words.values(), []))) for i in range(n) for j in range(i + 1, n)),
        "examples": examples,
    }

    model, n_base = pretrain(public_train, public_eval)
    log("building frozen hidden states")
    D = {"public": Data(model, public_eval), "outsider": Data(model, out_sents)}
    for i in range(n):
        D[f"train{i}"] = Data(model, train[i])
        D[f"held{i}"] = Data(model, held[i])
    cat = Concat(D)

    # ------------------------------------------------------------------ pilot (client 0, separate seed)
    log("pilot")
    pil, best = [], None
    for r in CFG["pilot"]["ranks"]:
        for ep in CFG["pilot"]["epochs"]:
            ad = Adapter(model, r, CFG["pilot"]["seed"])
            th, secs = train_adapter(ad, D["train0"], ep, 5000 + r + ep)
            sc = Scores(cat, *score(ad, th, cat))
            base_sc = Scores(cat, *score(ad, torch.zeros(ad.dim), cat))
            row = {"rank": r, "epochs": ep, "dim": ad.dim, "train_seconds": secs,
                   "train_ppl": sc.ppl("train0"), "heldout_ppl": sc.ppl("held0"), "base_heldout_ppl": base_sc.ppl("held0"),
                   "sample_auc": auc(sc.sent("train0"), sc.sent("held0")), "raw_norm": float(th.norm())}
            pil.append(row)
            log("pilot", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})
            key = (row["heldout_ppl"], r)
            if best is None or key < best[0]:
                best = (key, r, ep)
    R, EPOCHS = best[1], best[2]
    CFG["chosen"] = {"rank": R, "epochs": EPOCHS}
    log(f"chosen rank {R}, epochs {EPOCHS}")

    # ------------------------------------------------------------------ base model numbers
    ad0 = Adapter(model, R, 0)
    base_sc = Scores(cat, *score(ad0, torch.zeros(ad0.dim), cat))
    held_all = [f"held{i}" for i in range(n)]
    base_numbers = {
        "base_parameters": n_base, "adapter_dimension": ad0.dim, "adapter_rank": R,
        "public_ppl": base_sc.ppl("public"), "public_acc": base_sc.acc("public"),
        "heldout_ppl_all_clients": base_sc.ppl(*held_all), "outsider_ppl": base_sc.ppl("outsider"),
        "uniform_ppl_reference": float(V - 2),
        "client_level_auc_base": [auc(base_sc.sent(f"held{i}"), base_sc.sent("outsider")) for i in range(n)],
    }
    log("base", {k: v for k, v in base_numbers.items() if k != "client_level_auc_base"})

    runs = []          # per (seed, sigma, client) rows
    per_seed = []
    adapter_only = []
    timing = {"retrain_seven_adapters_s": [], "train_one_adapter_s": [], "subtract_us": [], "unlearn_with_metrics_ms": []}
    seq_rows = []
    sigmas = CFG["sigmas"]

    def save(final=False):
        OUT.mkdir(parents=True, exist_ok=True)
        payload = {"config": CFG, "corpus": corpus_stats, "pilot": pil, "base": base_numbers, "adapter_only": adapter_only,
                   "per_seed": per_seed, "timing_raw": timing, "sequential": seq_rows, "runs": runs, "complete": final,
                   "environment": {"python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__,
                                   "threads": torch.get_num_threads(), "machine": platform.processor(), "platform": platform.platform()},
                   "runtime_seconds": time.perf_counter() - t_start}
        if final:
            payload["summary"] = summarise(runs, adapter_only, timing, seq_rows)
        (OUT / "metrics.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")

    for seed in CFG["seeds"]:
        log(f"seed {seed}: training 3 x {n} adapters")
        ad = Adapter(model, R, seed)
        sets, times = [], []
        for variant in range(3):         # 0 = the federation; 1, 2 = two independent re-trainings (fresh data order)
            ths, ts = [], []
            for i in range(n):
                th, secs = train_adapter(ad, D[f"train{i}"], EPOCHS, 10_000 * (variant + 1) + 100 * seed + i)
                ths.append(th); ts.append(secs)
            sets.append(ths); times.append(ts)
        norms = [float(t.norm()) for t in sets[0]]
        C = st.median(norms)
        clipped = [[t * min(1.0, C / float(t.norm())) for t in ths] for ths in sets]
        sums = [torch.stack(c).sum(0) for c in clipped]
        timing["train_one_adapter_s"] += times[1]
        timing["retrain_seven_adapters_s"].append(sum(times[1]) * 7 / 8)
        per_seed.append({"seed": seed, "raw_norms": norms, "C": C, "clip_scales": [min(1.0, C / x) for x in norms],
                         "train_seconds_mean": st.fmean(times[0])})
        for i in range(n):
            th = sets[0][i]
            sc = Scores(cat, *score(ad, th, cat))
            adapter_only.append({"seed": seed, "client": i, "raw_norm": norms[i], "own_heldout_ppl": sc.ppl(f"held{i}"),
                                 "base_own_heldout_ppl": base_sc.ppl(f"held{i}"), "own_train_ppl": sc.ppl(f"train{i}"),
                                 "public_ppl": sc.ppl("public"), "outsider_ppl": sc.ppl("outsider"),
                                 "sample_auc": auc(sc.sent(f"train{i}"), sc.sent(f"held{i}")),
                                 "client_auc": auc(sc.sent(f"held{i}"), sc.sent("outsider"))})
        for sigma in sigmas:
            gen = [torch.Generator().manual_seed(7_000_000 + 1000 * seed + 10 * k + int(round(sigma * 1000))) for k in range(3)]
            noises = [torch.randn(ad.dim, generator=g) * (sigma * C) for g in gen]
            S0 = sums[0] + noises[0]
            model_all = S0 / n
            sc_all = Scores(cat, *score(ad, model_all, cat))
            for j in range(n):
                retained = [f"held{i}" for i in range(n) if i != j]
                unl = (S0 - clipped[0][j]) / (n - 1)
                ref = (noises[0] + sum(clipped[0][i] for i in range(n) if i != j)) / (n - 1)
                R1 = (noises[1] + sum(clipped[1][i] for i in range(n) if i != j)) / (n - 1)
                R2 = (noises[2] + sum(clipped[2][i] for i in range(n) if i != j)) / (n - 1)
                sc_u = Scores(cat, *score(ad, unl, cat))
                sc_r = Scores(cat, *score(ad, R1, cat))
                runs.append({
                    "seed": seed, "sigma": sigma, "client": j, "epsilon": eps_of(sigma), "C": C, "noise_l2": float(noises[0].norm()),
                    "signal_l2_sum": float(sum(clipped[0]).norm()),
                    "identity_max_abs": float((unl - ref).abs().max()),
                    "l2_unl_vs_retrain": float((unl - R1).norm()), "l2_retrain_vs_retrain": float((R1 - R2).norm()),
                    "public_ppl_before": sc_all.ppl("public"), "public_ppl_after": sc_u.ppl("public"), "public_ppl_retrain": sc_r.ppl("public"),
                    "public_acc_before": sc_all.acc("public"), "public_acc_after": sc_u.acc("public"),
                    "retained_ppl_before": sc_all.ppl(*retained), "retained_ppl_after": sc_u.ppl(*retained), "retained_ppl_retrain": sc_r.ppl(*retained),
                    "retained_acc_before": sc_all.acc(*retained), "retained_acc_after": sc_u.acc(*retained),
                    "target_ppl_before": sc_all.ppl(f"held{j}"), "target_ppl_after": sc_u.ppl(f"held{j}"), "target_ppl_retrain": sc_r.ppl(f"held{j}"),
                    "sample_auc_before": auc(sc_all.sent(f"train{j}"), sc_all.sent(f"held{j}")),
                    "sample_auc_after": auc(sc_u.sent(f"train{j}"), sc_u.sent(f"held{j}")),
                    "sample_auc_retrain": auc(sc_r.sent(f"train{j}"), sc_r.sent(f"held{j}")),
                    "client_auc_before": auc(sc_all.sent(f"held{j}"), sc_all.sent("outsider")),
                    "client_auc_after": auc(sc_u.sent(f"held{j}"), sc_u.sent("outsider")),
                    "client_auc_retrain": auc(sc_r.sent(f"held{j}"), sc_r.sent("outsider")),
                })
            # timing of the unlearning operation itself (seed 0, mid sigma, client 0)
            if seed == 0 and sigma == 0.01:
                t0 = time.perf_counter()
                for _ in range(2000):
                    _ = (S0 - clipped[0][0]) / (n - 1)
                timing["subtract_us"].append((time.perf_counter() - t0) / 2000 * 1e6)
                for _ in range(20):
                    t0 = time.perf_counter()
                    u = (S0 - clipped[0][0]) / (n - 1)
                    sc_t = Scores(cat, *score(ad, u, cat))
                    _ = sc_t.ppl("public"), sc_t.ppl(*held_all), auc(sc_t.sent("train0"), sc_t.sent("held0"))
                    timing["unlearn_with_metrics_ms"].append((time.perf_counter() - t0) * 1e3)
        # sequential removal
        for sigma in CFG["sequential_sigmas"]:
            g = torch.Generator().manual_seed(7_000_000 + 1000 * seed + int(round(sigma * 1000)))
            z = torch.randn(ad.dim, generator=g) * (sigma * C)
            S = sums[0] + z
            active = list(range(n))
            for step, j in enumerate([None] + CFG["sequential_order"]):
                if j is not None:
                    S = S - clipped[0][j]
                    active.remove(j)
                th = S / len(active)
                sc = Scores(cat, *score(ad, th, cat))
                removed = [f"held{i}" for i in range(n) if i not in active]
                row = {"seed": seed, "sigma": sigma, "step": step, "active": len(active), "public_ppl": sc.ppl("public"),
                       "remaining_ppl": sc.ppl(*[f"held{i}" for i in active]),
                       "removed_ppl": sc.ppl(*removed) if removed else None,
                       "client_auc_removed": [auc(sc.sent(f"held{i}"), sc.sent("outsider")) for i in range(n) if i not in active]}
                seq_rows.append(row)
        save(False)
        log(f"seed {seed} done; elapsed {time.perf_counter() - t_start:.0f}s")

    save(True)
    make_charts()
    log(f"finished in {time.perf_counter() - t_start:.0f}s")


# ---------------------------------------------------------------------------------------------- summary
def summarise(runs, adapter_only, timing, seq_rows):
    out = {"by_sigma": []}
    for sigma in CFG["sigmas"]:
        rs = [r for r in runs if r["sigma"] == sigma]
        seeds = sorted({r["seed"] for r in rs})
        per_seed_pub = [st.fmean(r["public_ppl_before"] for r in rs if r["seed"] == s) for s in seeds]
        d = {"sigma": sigma, "epsilon": eps_of(sigma) if sigma > 0 else None,
             "epsilon_in_classical_range": (eps_of(sigma) < 1) if sigma > 0 else None, "n_requests": len(rs)}
        for key in ("public_ppl_before", "public_ppl_after", "public_ppl_retrain", "public_acc_before", "retained_ppl_before",
                    "retained_ppl_after", "retained_ppl_retrain", "retained_acc_before", "retained_acc_after", "target_ppl_before",
                    "target_ppl_after", "target_ppl_retrain", "sample_auc_before", "sample_auc_after", "sample_auc_retrain",
                    "client_auc_before", "client_auc_after", "client_auc_retrain", "identity_max_abs", "l2_unl_vs_retrain",
                    "l2_retrain_vs_retrain", "noise_l2", "signal_l2_sum"):
            d[key] = mean_sd(r[key] for r in rs)
        ok = [100.0 * min(1.0, r["retained_ppl_before"] / r["retained_ppl_after"]) for r in rs
              if r["retained_ppl_before"] < 9.9e8 and r["retained_ppl_after"] < 9.9e8]   # a capped (destroyed) model has no meaningful retention
        d["retention_retained_ppl_percent"] = mean_sd(ok) if ok else None
        d["models_destroyed_fraction"] = sum(1 for r in rs if r["retained_ppl_before"] >= 9.9e8) / len(rs)
        out["by_sigma"].append(d)
    out["adapter_only"] = {
        "own_heldout_ppl": mean_sd(a["own_heldout_ppl"] for a in adapter_only),
        "base_own_heldout_ppl": mean_sd(a["base_own_heldout_ppl"] for a in adapter_only),
        "own_train_ppl": mean_sd(a["own_train_ppl"] for a in adapter_only),
        "sample_auc": mean_sd(a["sample_auc"] for a in adapter_only), "client_auc": mean_sd(a["client_auc"] for a in adapter_only),
        "public_ppl": mean_sd(a["public_ppl"] for a in adapter_only), "raw_norm": mean_sd(a["raw_norm"] for a in adapter_only)}
    t = timing
    sub, met, retr = st.median(t["subtract_us"]), st.median(t["unlearn_with_metrics_ms"]), st.median(t["retrain_seven_adapters_s"])
    out["timing"] = {"subtract_us_median": sub, "unlearn_with_metrics_ms_median": met, "retrain_seven_adapters_s_median": retr,
                     "train_one_adapter_s_mean": st.fmean(t["train_one_adapter_s"]),
                     "speedup_retrain_over_subtract": retr / (sub * 1e-6), "speedup_retrain_over_unlearn_with_metrics": retr / (met * 1e-3)}
    seq = {}
    for sigma in CFG["sequential_sigmas"]:
        for step in range(4):
            rs = [r for r in seq_rows if r["sigma"] == sigma and r["step"] == step]
            seq[f"sigma={sigma:g}|step={step}"] = {
                "public_ppl": mean_sd(r["public_ppl"] for r in rs), "remaining_ppl": mean_sd(r["remaining_ppl"] for r in rs),
                "removed_ppl": mean_sd(r["removed_ppl"] for r in rs) if step else None,
                "client_auc_removed": mean_sd(a for r in rs for a in r["client_auc_removed"]) if step else None}
    out["sequential"] = seq
    return out


# ---------------------------------------------------------------------------------------------- charts
def make_charts():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    INDIGO, MINT, ROSE, AMBER, SKY, INK, GREY = "#5b5bd6", "#2f9e77", "#d6455d", "#e0a030", "#3b8ed0", "#1b2238", "#9aa5ba"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK,
                         "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": "#e3e7ef", "grid.linewidth": 0.7, "axes.axisbelow": True})
    m = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
    rows = m["summary"]["by_sigma"]
    base = m["base"]
    xs = [r["sigma"] for r in rows]
    xp = [x if x > 0 else 0.0012 for x in xs]       # sigma = 0 drawn at the left edge of the log axis

    def save(fig, name):
        fig.savefig(CHARTS / name, dpi=150, facecolor="white", bbox_inches="tight")
        plt.close(fig)
        log("saved", name)

    def ticks(ax):
        ax.set_xscale("log"); ax.set_xticks(xp)
        ax.set_xticklabels(["0" if x == 0 else f"{x:g}" for x in xs], rotation=0, fontsize=7.5)
        ax.minorticks_off()

    # n01: utility vs noise
    fig, ax = plt.subplots(1, 2, figsize=(8.8, 3.3))
    for key, col, lab in (("retained_ppl_before", INDIGO, "retained clients' held-out text, released model"),
                          ("public_ppl_before", MINT, "public evaluation text")):
        ax[0].errorbar(xp, [r[key]["mean"] for r in rows], yerr=[r[key]["sd"] for r in rows], color=col, marker="o", ms=4, capsize=2, lw=1.4, label=lab)
    ax[0].axhline(base["heldout_ppl_all_clients"], color=INDIGO, ls=":", lw=1); ax[0].text(0.0013, base["heldout_ppl_all_clients"] * 1.08, "base, no adapter (clients)", fontsize=7, color=INDIGO)
    ax[0].axhline(base["public_ppl"], color=MINT, ls=":", lw=1); ax[0].text(0.0013, base["public_ppl"] * 0.72, "base (public)", fontsize=7, color=MINT, va="top")
    ax[0].axhline(base["uniform_ppl_reference"], color=ROSE, ls="--", lw=1); ax[0].text(0.0013, base["uniform_ppl_reference"] * 1.1, "uniform (29)", fontsize=7, color=ROSE)
    ax[0].set_yscale("log"); ticks(ax[0]); ax[0].set_xlabel("noise multiplier sigma (0 drawn at left)"); ax[0].set_ylabel("perplexity")
    ax[0].legend(frameon=False, fontsize=6.8, loc="center left", bbox_to_anchor=(0.0, 0.62)); ax[0].set_title("Neural adapter: quality vs noise", fontsize=9.5, fontweight="bold")
    good = [(x, r) for x, r in zip(xp, rows) if r["retention_retained_ppl_percent"] is not None]
    ax[1].errorbar([x for x, _ in good], [r["retention_retained_ppl_percent"]["mean"] for _, r in good],
                   yerr=[r["retention_retained_ppl_percent"]["sd"] for _, r in good], color=SKY, marker="s", ms=4, capsize=2, lw=1.4)
    ax[1].axhline(70, color=ROSE, ls="--", lw=1); ticks(ax[1]); ax[1].set_ylim(0, 108); ax[1].set_xlim(ax[0].get_xlim())
    dead = [x for x, r in zip(xp, rows) if r["retention_retained_ppl_percent"] is None]
    if dead:
        ax[1].axvspan(min(dead) / 1.25, max(dead) * 1.25, color="#f3d5d9", alpha=0.6)
        ax[1].text((min(dead) * max(dead)) ** 0.5, 50, "model destroyed by noise\n(perplexity capped,\nretention undefined)", ha="center", fontsize=7.5, color=ROSE)
    ax[1].set_xlabel("noise multiplier sigma"); ax[1].set_ylabel("utility retention on retained clients (%)")
    ax[1].set_title("Retention after removing one client", fontsize=9.5, fontweight="bold")
    fig.tight_layout(); save(fig, "n01_neural_noise_vs_quality.png")

    # n02: membership AUC
    fig, ax = plt.subplots(1, 2, figsize=(8.8, 3.3))
    for a_, title, kb, ka, kr in ((ax[0], "Client-level attack (domain vs outsider)", "client_auc_before", "client_auc_after", "client_auc_retrain"),
                                  (ax[1], "Sample-level attack (trained vs held-out)", "sample_auc_before", "sample_auc_after", "sample_auc_retrain")):
        for key, col, mk, lab in ((kb, INDIGO, "o", "before removal"), (ka, MINT, "s", "after removal (subtraction)"), (kr, AMBER, "^", "fresh retrain without client")):
            a_.errorbar(xp, [r[key]["mean"] for r in rows], yerr=[r[key]["sd"] / math.sqrt(max(r[key]["n"], 1)) for r in rows], color=col, marker=mk, ms=4, capsize=2, lw=1.3, label=lab)
        a_.axhline(0.5, color=ROSE, ls="--", lw=1); ticks(a_); a_.set_xlabel("noise multiplier sigma"); a_.set_ylabel("AUC")
        a_.set_title(title, fontsize=9.5, fontweight="bold")
    ax[0].legend(frameon=False, fontsize=7.5, loc="lower left")
    fig.tight_layout(); save(fig, "n02_neural_membership_auc.png")

    # n03: unlearned vs retrain, cost
    fig, ax = plt.subplots(1, 2, figsize=(8.8, 3.3))
    sel = [r for r in rows if r["sigma"] > 0]
    xs2 = np.arange(len(sel))
    ax[0].bar(xs2 - 0.2, [r["l2_unl_vs_retrain"]["mean"] for r in sel], 0.4, color=INDIGO, label="unlearned vs fresh retrain")
    ax[0].bar(xs2 + 0.2, [r["l2_retrain_vs_retrain"]["mean"] for r in sel], 0.4, color=AMBER, label="fresh retrain vs fresh retrain")
    ax[0].set_xticks(xs2); ax[0].set_xticklabels([f"{r['sigma']:g}" for r in sel], fontsize=7.5); ax[0].set_yscale("log")
    ax[0].set_xlabel("noise multiplier sigma"); ax[0].set_ylabel("L2 distance between models"); ax[0].legend(frameon=False, fontsize=7.5)
    ax[0].set_title("Is the unlearned model a retrained one?", fontsize=9.5, fontweight="bold")
    t = m["summary"]["timing"]
    labels = ["subtract\n(vector op)", "subtract +\nmetrics + attack", "retrain 7\nadapters"]
    vals = [t["subtract_us_median"] * 1e-3, t["unlearn_with_metrics_ms_median"], t["retrain_seven_adapters_s_median"] * 1e3]
    ax[1].bar(range(3), vals, color=[MINT, SKY, AMBER], width=0.55); ax[1].set_yscale("log")
    for i, v in enumerate(vals):
        ax[1].text(i, v * 1.15, f"{v:,.2f} ms" if v < 1000 else f"{v / 1000:,.2f} s", ha="center", fontsize=8)
    ax[1].set_xticks(range(3)); ax[1].set_xticklabels(labels, fontsize=8); ax[1].set_ylabel("median wall time (ms, log)")
    ax[1].set_title("Cost of removing one client", fontsize=9.5, fontweight="bold")
    fig.tight_layout(); save(fig, "n03_neural_retrain_and_cost.png")


def resummary():
    m = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
    m["summary"] = summarise(m["runs"], m["adapter_only"], m["timing_raw"], m["sequential"])
    (OUT / "metrics.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    make_charts()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "resummary":
        resummary()
    elif len(sys.argv) > 1 and sys.argv[1] == "charts":
        make_charts()
    else:
        main()
