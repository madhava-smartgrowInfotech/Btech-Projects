"""Seeded generator for the STR repeat-type task (sample data).

Each 100 bp sequence has random background DNA and, except for class "none", one short tandem repeat
tract (motif length 2-5 bp, 4-10 copies, ~3% point substitutions inside the tract).
Output: data/dna/repeat_sequences.csv  (sequence, label, motif, start, copies)
"""
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "dna" / "repeat_sequences.csv"
SEED = 7
N_PER_CLASS = 1000
LENGTH = 100
LABELS = ["none", "dinucleotide", "trinucleotide", "tetranucleotide", "pentanucleotide"]


def rand_seq(rng, n):
    return "".join(rng.choice("ACGT") for _ in range(n))


def motif_of(rng, k):
    while True:
        m = rand_seq(rng, k)
        # skip motifs that are themselves shorter repeats (e.g. ATAT for k=4)
        if all(m != m[:d] * (k // d) for d in range(1, k) if k % d == 0):
            return m


def main():
    rng = random.Random(SEED)
    rows = []
    for label_id, label in enumerate(LABELS):
        for _ in range(N_PER_CLASS):
            seq = list(rand_seq(rng, LENGTH))
            motif, start, copies = "", -1, 0
            if label_id > 0:
                k = label_id + 1
                motif = motif_of(rng, k)
                copies = rng.randint(max(4, 12 // k + 1), max(6, 40 // k))
                tract = list(motif * copies)
                for i in range(len(tract)):
                    if rng.random() < 0.03:
                        tract[i] = rng.choice("ACGT")
                start = rng.randint(0, LENGTH - len(tract))
                seq[start:start + len(tract)] = tract
            rows.append(["".join(seq), label, motif, start, copies])
    rng.shuffle(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sequence", "label", "motif", "start", "copies"])
        w.writerows(rows)
    print(f"wrote {len(rows)} sequences -> {OUT}")


if __name__ == "__main__":
    main()
