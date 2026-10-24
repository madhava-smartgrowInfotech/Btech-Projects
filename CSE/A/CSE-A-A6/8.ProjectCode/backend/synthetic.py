"""A SYNTHETIC frame-measurement CSV in the research.py format, for demonstrating the Research screen only.

It is generated from a seeded random generator, not from people. Metrics computed from it say nothing about
real-world performance; the API flags any report built from this exact file as synthetic.
"""
import csv
import hashlib
import io

import numpy as np

from research import FIELDS

SUBJECTS = ['S01', 'S02', 'S03', 'S04', 'S05', 'S06']
HELD_OUT = ['S05', 'S06']
HZ = 10
SECONDS = 30


def _session(rng, label):
    n = HZ * SECONDS
    t = np.arange(n) / HZ
    if label == 'normal':
        ear = rng.normal(0.30, 0.012, n)
        roll = rng.normal(0, 2.5, n)
        for start in rng.choice(n - 4, size=7, replace=False):       # short blinks (~0.3 s)
            ear[start:start + 3] = rng.normal(0.12, 0.01, 3)
    else:
        ear = rng.normal(0.25, 0.018, n)
        roll = rng.normal(0, 7.0, n)
        for start in rng.choice(n - 24, size=5, replace=False):      # long closures (~1.5-2.3 s)
            length = int(rng.integers(15, 23))
            ear[start:start + length] = rng.normal(0.10, 0.012, length)
    return t, np.clip(ear, 0.02, 0.6), np.clip(roll, -60, 60)


def csv_text(seed=2026):
    rng = np.random.default_rng(seed)
    out = io.StringIO()
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(FIELDS)
    for subject in SUBJECTS:
        for label in ('normal', 'possible_impairment'):
            session = f'{subject}-{label[:3]}'
            t, ear, roll = _session(rng, label)
            for a, b, c in zip(t, ear, roll):
                writer.writerow([subject, session, f'{a:.1f}', f'{b:.4f}', f'{c:.2f}', 'Good', label, 'yes'])
    return out.getvalue()


def sha256():
    return hashlib.sha256(csv_text().encode('utf-8')).hexdigest()
