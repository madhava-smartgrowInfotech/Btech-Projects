"""Seeded synthetic STR profile database (sample data).

Allele frequencies: NIST U.S. population dataset (N=1036, Steffen et al. 2017 revision), taken from
data/str/nist1036_allele_freqs.csv (column "all"). Genotypes are drawn under Hardy-Weinberg equilibrium
for the 20 CODIS core loci. Output:
  data/str/codis20_frequencies.json   {locus: {allele: freq}}
  data/str/str_database.json          1000 synthetic reference profiles
"""
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STR = ROOT / "data" / "str"
SEED = 2026
N_PROFILES = 1000
CODIS20 = ["CSF1PO", "D3S1358", "D5S818", "D7S820", "D8S1179", "D13S317", "D16S539", "D18S51", "D21S11", "FGA",
           "TH01", "TPOX", "vWA", "D1S1656", "D2S441", "D2S1338", "D10S1248", "D12S391", "D19S433", "D22S1045"]


def norm_allele(a):
    v = float(a)
    return str(int(v)) if v.is_integer() else str(v)


def main():
    freqs = {loc: {} for loc in CODIS20}
    with open(STR / "nist1036_allele_freqs.csv", newline="") as f:
        for r in csv.DictReader(f):
            if r["marker"] in freqs and float(r["all"]) > 0:
                freqs[r["marker"]][norm_allele(r["allele"])] = float(r["all"])
    for loc, fr in freqs.items():
        s = sum(fr.values())
        freqs[loc] = {a: round(p / s, 6) for a, p in sorted(fr.items(), key=lambda kv: float(kv[0]))}
    (STR / "codis20_frequencies.json").write_text(json.dumps(freqs, indent=1))

    rng = random.Random(SEED)
    profiles = []
    for i in range(N_PROFILES):
        g = {}
        for loc in CODIS20:
            alleles, weights = list(freqs[loc]), list(freqs[loc].values())
            pair = sorted(rng.choices(alleles, weights, k=2), key=float)
            g[loc] = pair
        profiles.append({"id": f"REF-{i + 1:04d}", "category": "synthetic reference", "genotype": g})
    db = {"description": "Synthetic STR reference profiles (sample data, seeded).",
          "source_frequencies": "NIST U.S. population dataset, N=1036 (all populations)", "seed": SEED,
          "loci": CODIS20, "profiles": profiles}
    (STR / "str_database.json").write_text(json.dumps(db))
    print(f"wrote {len(profiles)} profiles over {len(CODIS20)} loci")


if __name__ == "__main__":
    main()
