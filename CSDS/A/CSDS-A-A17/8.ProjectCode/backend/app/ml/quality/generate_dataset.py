"""Generates a labeled feature-space dataset for crop quality grading.

No real labeled crop-image dataset was available for this project, so we
generate the dataset in the SAME feature space the CV pipeline produces
(see feature_extraction.py) rather than fabricating fake images. Each
grade is drawn from realistic, overlapping distributions (with label
noise) so the classifier has to actually learn a decision boundary
instead of memorizing separable clusters. This is disclosed in the admin
"model card" panel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.ml.quality.feature_extraction import FEATURE_NAMES

GRADES = ["A", "B", "C", "Reject"]

# (mean, std) per feature per grade
PROFILES: dict[str, dict[str, tuple[float, float]]] = {
    "A": {
        "mean_hue": (0.28, 0.05),
        "mean_saturation": (0.62, 0.08),
        "mean_value": (0.66, 0.08),
        "saturation_std": (0.09, 0.03),
        "color_uniformity": (0.90, 0.05),
        "texture_contrast": (0.18, 0.06),
        "texture_homogeneity": (0.86, 0.06),
        "texture_energy": (0.55, 0.10),
        "edge_density": (0.09, 0.03),
        "blemish_ratio": (0.02, 0.015),
        "size_score": (0.82, 0.10),
    },
    "B": {
        "mean_hue": (0.27, 0.06),
        "mean_saturation": (0.52, 0.09),
        "mean_value": (0.58, 0.09),
        "saturation_std": (0.14, 0.04),
        "color_uniformity": (0.74, 0.08),
        "texture_contrast": (0.30, 0.08),
        "texture_homogeneity": (0.72, 0.08),
        "texture_energy": (0.42, 0.10),
        "edge_density": (0.15, 0.04),
        "blemish_ratio": (0.07, 0.03),
        "size_score": (0.68, 0.12),
    },
    "C": {
        "mean_hue": (0.26, 0.07),
        "mean_saturation": (0.40, 0.10),
        "mean_value": (0.48, 0.10),
        "saturation_std": (0.20, 0.05),
        "color_uniformity": (0.55, 0.10),
        "texture_contrast": (0.46, 0.10),
        "texture_homogeneity": (0.56, 0.09),
        "texture_energy": (0.30, 0.09),
        "edge_density": (0.23, 0.05),
        "blemish_ratio": (0.15, 0.05),
        "size_score": (0.52, 0.13),
    },
    "Reject": {
        "mean_hue": (0.24, 0.09),
        "mean_saturation": (0.28, 0.10),
        "mean_value": (0.36, 0.11),
        "saturation_std": (0.27, 0.06),
        "color_uniformity": (0.35, 0.12),
        "texture_contrast": (0.64, 0.12),
        "texture_homogeneity": (0.38, 0.10),
        "texture_energy": (0.18, 0.08),
        "edge_density": (0.33, 0.07),
        "blemish_ratio": (0.30, 0.09),
        "size_score": (0.35, 0.15),
    },
}


def generate(n_per_grade: int = 1500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for grade in GRADES:
        profile = PROFILES[grade]
        for _ in range(n_per_grade):
            row = {}
            for feat in FEATURE_NAMES:
                mean, std = profile[feat]
                val = rng.normal(mean, std)
                row[feat] = float(np.clip(val, 0.0, 1.0))
            # label noise: ~6% of samples get relabeled to a neighboring grade
            row["grade"] = grade
            rows.append(row)

    df = pd.DataFrame(rows)
    noise_idx = rng.choice(len(df), size=int(len(df) * 0.06), replace=False)
    neighbor = {"A": "B", "B": "C", "C": "B", "Reject": "C"}
    df.loc[noise_idx, "grade"] = df.loc[noise_idx, "grade"].map(neighbor)
    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    from app.core.config import DATA_DIR

    df = generate()
    out_path = DATA_DIR / "quality_dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"wrote {len(df)} rows to {out_path}")
