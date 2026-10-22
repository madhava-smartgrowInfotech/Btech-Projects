"""Dataset utilities: load ISOT/LIAR-style CSVs or build a demo dataset.

Expected CSV formats (any one works):
  1. columns: [text, label]  with label in {REAL,PARTIALLY TRUE,FAKE} or {0,1,2}
     - 'title' + 'text' columns are auto-combined if present
  2. ISOT style: True.csv / Fake.csv (separate files, label inferred)
  3. LIAR style: statement + 6-way label mapped to 3 classes:
     true/mostly-true -> REAL | half-true -> PARTIALLY TRUE |
     barely-true/false/pants-fire -> FAKE
"""
import os
import glob
import numpy as np
import pandas as pd

LABEL_MAP_LIAR = {
    "true": 0, "mostly-true": 0,
    "half-true": 1,
    "barely-true": 2, "false": 2, "pants-fire": 2,
}
CANON = {"real": 0, "true": 0, "0": 0, 0: 0,
         "partially true": 1, "partially-true": 1, "mixed": 1,
         "half-true": 1, "half true": 1, "1": 1, 1: 1,
         "fake": 0 if False else 2, "false": 2, "2": 2, 2: 2}


def _canon_label(v):
    if isinstance(v, (int, np.integer)):
        return int(v) if int(v) in (0, 1, 2) else 2
    s = str(v).strip().lower()
    if s in LABEL_MAP_LIAR:
        return LABEL_MAP_LIAR[s]
    return CANON.get(s, 2)


def load_csv(path_or_dir):
    """Load any supported CSV layout into (texts, labels)."""
    if os.path.isdir(path_or_dir):
        files = glob.glob(os.path.join(path_or_dir, "*.csv"))
        if not files:
            raise FileNotFoundError("No CSV files found in " + path_or_dir)
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = pd.read_csv(path_or_dir)
    cols = {c.lower(): c for c in df.columns}
    # ISOT single-file with 'label' True/FAKE etc.
    if "title" in cols and "text" in cols:
        texts = (df[cols["title"]].fillna("") + " " +
                 df[cols["text"]].fillna("")).tolist()
    elif "statement" in cols:
        texts = df[cols["statement"]].fillna("").tolist()
    elif "text" in cols:
        texts = df[cols["text"]].fillna("").tolist()
    elif "news" in cols:
        texts = df[cols["news"]].fillna("").tolist()
    elif "content" in cols:
        texts = df[cols["content"]].fillna("").tolist()
    else:
        texts = df.iloc[:, 0].fillna("").tolist()
    label_col = None
    for cand in ("label", "class", "target", "veracity", "rating"):
        if cand in cols:
            label_col = cols[cand]
            break
    if label_col is None:
        raise ValueError("Could not find a label column (need label/class/target).")
    labels = [_canon_label(v) for v in df[label_col].tolist()]
    return texts, np.array(labels)


def build_demo_dataset(n_per_class=300, seed=42):
    """Balanced 3-class synthetic news corpus for offline demo/evaluation."""
    rng = np.random.default_rng(seed)
    real_templates = [
        "Government releases official {topic} report confirmed by independent experts with verified data",
        "Central bank announces {topic} policy after review of economic indicators and official statistics",
        "Health ministry confirms {topic} guidelines based on peer reviewed clinical trial evidence",
        "Election commission publishes verified {topic} results with observer statements and audit data",
        "Research institute presents {topic} findings with methodology documentation and datasets",
    ]
    mixed_templates = [
        "Report claims {topic} breakthrough but experts say evidence is partial and needs verification",
        "Viral post about {topic} mixes accurate statistics with unconfirmed rumours say analysts",
        "Article on {topic} cites real study yet exaggerates conclusions beyond what data supports",
        "Opinion piece blends factual {topic} background with disputed assertions lacking sources",
        "Coverage of {topic} partly accurate but key details remain unverified investigators note",
    ]
    fake_templates = [
        "SHOCKING secret {topic} miracle exposed hidden truth they banned urgent share now",
        "You wont believe this unbelievable {topic} conspiracy click now viral breaking exclusive",
        "Banned video reveals hidden {topic} hoax miracle cure officials dont want you to know",
        "Urgent breaking {topic} scandal exposed secret documents leaked share before deleted",
        "Miracle {topic} secret discovered shocking coverup hidden by media click urgently",
    ]
    topics = ["economic growth figures", "vaccination drive results", "election turnout data",
              "climate assessment", "education reform plan", "monsoon relief measures",
              "digital payment adoption", "census publication", "trade agreement terms",
              "public health survey"]
    texts, labels = [], []
    for cls, tpls in enumerate([real_templates, mixed_templates, fake_templates]):
        for _ in range(n_per_class):
            t = rng.choice(tpls).format(topic=rng.choice(topics))
            # light noise so TF-IDF is non-trivial
            if rng.random() < 0.3:
                t += " according to statements issued on record"
            texts.append(t)
            labels.append(cls)
    idx = rng.permutation(len(texts))
    return [texts[i] for i in idx], np.array(labels)[idx]
