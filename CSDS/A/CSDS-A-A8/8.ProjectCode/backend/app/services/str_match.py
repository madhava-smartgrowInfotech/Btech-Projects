"""STR profile matching against the seeded reference database with a likelihood ratio.

Per locus:  LR = P(query genotype | same source) / P(query genotype | unrelated person)
  same source : allele-typing error model, (1-e)^2 identical, e(1-e) one allele differs, e^2 none shared
  unrelated   : NRC II 4.10 genotype probability with theta (sub-population correction)
The combined LR is the product over loci typed in both profiles; candidates are ranked by log10 LR.
"""
import json
import math
import random
from functools import lru_cache

from ..config import DATA

THETA = 0.01
ERROR = 0.001
N_POP = 1036
MIN_FREQ = 5 / (2 * N_POP)


@lru_cache(maxsize=1)
def load():
    freqs = json.loads((DATA / "str" / "codis20_frequencies.json").read_text())
    db = json.loads((DATA / "str" / "str_database.json").read_text())
    return freqs, db


def norm_allele(a):
    a = str(a).strip()
    v = float(a)
    return str(int(v)) if v.is_integer() else str(v)


def parse_profile(raw):
    freqs, _ = load()
    prof = {}
    for locus, val in (raw or {}).items():
        if locus not in freqs:
            raise ValueError(f"Unknown locus {locus}")
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        parts = val if isinstance(val, list) else str(val).replace(";", ",").replace("/", ",").split(",")
        parts = [p for p in (str(x).strip() for x in parts) if p]
        try:
            alleles = [norm_allele(p) for p in parts]
        except ValueError:
            raise ValueError(f"{locus}: alleles must be numbers such as 9.3 or 12")
        if len(alleles) == 1:
            alleles = alleles * 2
        if len(alleles) != 2:
            raise ValueError(f"{locus}: enter one or two alleles")
        prof[locus] = sorted(alleles, key=float)
    if len(prof) < 3:
        raise ValueError("Enter genotypes for at least 3 loci.")
    return prof


def freq(locus, allele):
    freqs, _ = load()
    return max(freqs[locus].get(allele, 0.0), MIN_FREQ)


def genotype_prob(locus, g):
    a, b = g
    t = THETA
    denom = (1 + t) * (1 + 2 * t)
    p = freq(locus, a)
    if a == b:
        return (2 * t + (1 - t) * p) * (3 * t + (1 - t) * p) / denom
    q = freq(locus, b)
    return 2 * (t + (1 - t) * p) * (t + (1 - t) * q) / denom


def shared(g1, g2):
    rest = list(g2)
    n = 0
    for a in g1:
        if a in rest:
            rest.remove(a)
            n += 1
    return n


def compare(query, ref):
    log_lr, loci, matched, mismatched = 0.0, [], 0, 0
    for locus, qg in query.items():
        rg = ref.get(locus)
        if rg is None:
            continue
        k = shared(qg, rg)
        p_same = [(ERROR ** 2), ERROR * (1 - ERROR), (1 - ERROR) ** 2][k]
        lr = p_same / genotype_prob(locus, qg)
        log_lr += math.log10(lr)
        matched += k == 2
        mismatched += k < 2
        loci.append({"locus": locus, "query": "/".join(qg), "reference": "/".join(rg), "shared_alleles": k,
                     "lr": float(f"{lr:.4g}")})
    return log_lr, loci, matched, mismatched


def verbal(log_lr):
    if log_lr < 0:
        return "supports the unrelated-person hypothesis"
    for thr, text in ((1, "weak support"), (2, "moderate support"), (4, "moderately strong support"),
                      (6, "strong support")):
        if log_lr < thr:
            return f"{text} for same source"
    return "very strong support for same source"


def match(raw_query, top_k=10):
    query = parse_profile(raw_query)
    _, db = load()
    results = []
    for p in db["profiles"]:
        log_lr, loci, m, mm = compare(query, p["genotype"])
        results.append({"id": p["id"], "log10_lr": round(log_lr, 2), "loci_compared": len(loci),
                        "loci_matched": m, "loci_mismatched": mm, "loci": loci})
    results.sort(key=lambda r: -r["log10_lr"])
    rmp = 1.0
    for locus, g in query.items():
        rmp *= genotype_prob(locus, g)
    top = results[:top_k]
    for r in top:
        r["verbal"] = verbal(r["log10_lr"])
        r["lr_display"] = f"1e{r['log10_lr']:.1f}" if abs(r["log10_lr"]) >= 4 else f"{10 ** r['log10_lr']:.3g}"
    return {
        "query_loci": len(query), "database_size": len(db["profiles"]),
        "random_match_probability": float(f"{rmp:.3g}"), "log10_inverse_rmp": round(-math.log10(rmp), 2),
        "theta": THETA, "typing_error_rate": ERROR,
        "candidates_with_positive_support": sum(r["log10_lr"] > 0 for r in results),
        "matches": [{k: v for k, v in r.items()} for r in top],
    }


def sample_query(seed=None):
    """Sample query derived from a database profile with simulated partial typing (labelled as sample data)."""
    freqs, db = load()
    rng = random.Random(seed)
    src = rng.choice(db["profiles"])
    loci = db["loci"][:]
    rng.shuffle(loci)
    dropped = loci[:3]
    changed = loci[3]
    g = {l: "/".join(v) for l, v in src["genotype"].items() if l not in dropped}
    alle = list(freqs[changed])
    a = src["genotype"][changed]
    g[changed] = "/".join(sorted([a[0], rng.choice([x for x in alle if x not in a])], key=float))
    return {"profile": g, "note": f"Sample query built from {src['id']} with 3 loci not typed and one allele "
                                  f"changed at {changed} (simulated typing error).", "source_id": src["id"]}


def loci():
    freqs, db = load()
    return {"loci": db["loci"], "alleles": {l: list(freqs[l]) for l in db["loci"]},
            "database_size": len(db["profiles"]), "frequency_source": db["source_frequencies"]}
