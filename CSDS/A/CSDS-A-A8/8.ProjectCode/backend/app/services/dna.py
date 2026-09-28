"""DNA sequence analysis: Biopython parsing/statistics, k-mer JEPA classifiers and an exact tandem-repeat scan."""
import csv
import io
import json
import re
from functools import lru_cache

import torch
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction

from ..config import DATA, EXPERIMENTS, MODELS
from nets import PAD_ID, SeqClassifier, dna_encoder, kmer_tokens, seq_windows  # noqa: E402

MAX_LEN = 20000


def parse_sequence(text):
    text = (text or "").strip()
    if not text:
        raise ValueError("Paste a DNA sequence (raw bases or FASTA).")
    seq_id = "query"
    if text.startswith(">"):
        records = list(SeqIO.parse(io.StringIO(text), "fasta"))
        if not records:
            raise ValueError("Could not parse the FASTA text.")
        seq_id, seq = records[0].id, str(records[0].seq)
    else:
        seq = text
    seq = re.sub(r"\s+", "", seq).upper()
    bad = set(seq) - set("ACGTN")
    if bad:
        raise ValueError(f"Unexpected characters in sequence: {''.join(sorted(bad))[:10]}")
    if len(seq) < 20:
        raise ValueError("Sequence is too short (need at least 20 bases).")
    if len(seq) > MAX_LEN:
        raise ValueError(f"Sequence is too long (max {MAX_LEN} bases).")
    return seq_id, seq


@lru_cache(maxsize=2)
def load_classifier(name):
    path = MODELS / f"dna_{name}_classifier.pt"
    if not path.exists():
        raise FileNotFoundError(f"{path.name} not found - run ml/train_dna.py")
    ck = torch.load(path, map_location="cpu")
    model = SeqClassifier(dna_encoder(), len(ck["labels"]))
    model.load_state_dict(ck["model"])
    model.eval()
    return model, ck["labels"], ck.get("metrics", {})


def classify_windows(name, windows):
    model, labels, metrics = load_classifier(name)
    x = torch.tensor([kmer_tokens(w) for w in windows])
    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)
    valid = (x != PAD_ID).any(1)
    return probs, labels, metrics, valid


def repeat_scan(seq, min_copies=4, kmin=2, kmax=6):
    """Exact tandem repeats: motif of length kmin..kmax repeated at least min_copies times."""
    found = []
    for k in range(kmin, kmax + 1):
        for m in re.finditer(r"([ACGT]{%d})\1{%d,}" % (k, min_copies - 1), seq):
            motif = m.group(1)
            if any(motif == motif[:d] * (k // d) for d in range(1, k) if k % d == 0):
                continue
            found.append({"motif": motif, "period": k, "start": m.start() + 1, "end": m.end(),
                          "copies": round((m.end() - m.start()) / k, 1)})
    found.sort(key=lambda r: (r["start"], -r["end"]))
    kept = []
    for r in found:
        if not any(r["start"] >= o["start"] and r["end"] <= o["end"] for o in kept):
            kept.append(r)
    return kept


def analyse(text):
    seq_id, seq = parse_sequence(text)
    s = Seq(seq)
    windows = seq_windows(seq)
    stats = {
        "id": seq_id, "length": len(seq), "gc_percent": round(100 * gc_fraction(s, ambiguous="ignore"), 2),
        "counts": {b: seq.count(b) for b in "ACGTN"},
        "reverse_complement_preview": str(s.reverse_complement())[:60],
        "windows_analysed": len(windows),
    }
    rp, rlabels, rmetrics, rvalid = classify_windows("repeat", windows)
    per_window = []
    for i, (w, p) in enumerate(zip(windows, rp)):
        j = int(p.argmax())
        per_window.append({"window": i + 1, "label": rlabels[j], "confidence": round(float(p[j]), 3)})
    non_none = 1 - rp[:, 0]
    best = int(non_none.argmax())
    best_label = rlabels[int(rp[best].argmax())]
    repeat = {
        "prediction": best_label,
        "confidence": round(float(rp[best].max()), 3),
        "probabilities": {l: round(float(v), 3) for l, v in zip(rlabels, rp[best])},
        "strongest_window": best + 1,
        "windows": per_window[:50],
        "model_test_accuracy": rmetrics.get("accuracy"),
    }
    op, olabels, ometrics, ovalid = classify_windows("organism", windows)
    mean = op[ovalid].mean(0) if ovalid.any() else op.mean(0)
    j = int(mean.argmax())
    organism = {
        "prediction": olabels[j], "confidence": round(float(mean[j]), 3),
        "probabilities": {l: round(float(v), 3) for l, v in zip(olabels, mean)},
        "model_test_accuracy": ometrics.get("accuracy"), "chance_accuracy": ometrics.get("chance_accuracy"),
        "note": "Class labels in the source dataset are not predictable from sequence (every model scores near chance on held-out data); treat this prediction as low-reliability.",
    }
    return {"sequence": stats, "repeat_type": repeat, "organism_class": organism, "repeat_scan": repeat_scan(seq)[:30]}


@lru_cache(maxsize=1)
def samples():
    out = []
    with open(DATA / "dna" / "repeat_sequences.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    for label in ("dinucleotide", "trinucleotide", "tetranucleotide", "pentanucleotide", "none"):
        r = next(r for r in rows[-1000:] if r["label"] == label)
        out.append({"name": f"Sample read - {label} repeat" if label != "none" else "Sample read - no repeat",
                    "sequence": r["sequence"]})
    with open(DATA / "dna" / "synthetic_dna_dataset.csv", newline="") as f:
        r = next(iter(csv.DictReader(f)))
    out.append({"name": f"Kaggle dataset {r['Sample_ID']} ({r['Class_Label']})", "sequence": f">{r['Sample_ID']}\n{r['Sequence']}"})
    return out


def metrics():
    p = EXPERIMENTS / "dna_metrics.json"
    return json.loads(p.read_text()) if p.exists() else None
