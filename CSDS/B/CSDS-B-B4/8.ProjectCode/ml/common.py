"""Shared helpers for training: paths, experiment folders, metrics and plots."""
from __future__ import annotations

import json
import logging
import platform
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.calibration import calibration_curve  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_SAMPLE = ROOT / "data" / "sample"
EXPERIMENTS = ROOT / "experiments"
MODELS = ROOT / "models"
SEED = 42

sys.path.insert(0, str(ROOT / "backend"))  # shared feature code lives in backend/app/ml

BRAND = {"primary": "#0d9488", "accent": "#f59e0b", "danger": "#e11d48", "muted": "#64748b", "blue": "#3b82f6", "violet": "#8b5cf6"}
SERIES = [BRAND["primary"], BRAND["accent"], BRAND["blue"], BRAND["violet"], BRAND["danger"], BRAND["muted"]]

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 140,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titleweight": "bold",
        "axes.titlesize": 10,
    }
)


@dataclass
class Experiment:
    """One training run: writes everything under experiments/<name>/."""

    name: str
    family: str
    directory: Path = field(init=False)
    started: float = field(default_factory=time.time)
    log: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        self.directory = EXPERIMENTS / self.name
        self.directory.mkdir(parents=True, exist_ok=True)
        self.log = logging.getLogger(f"train.{self.name}")
        self.log.setLevel(logging.INFO)
        self.log.handlers.clear()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
        fh = logging.FileHandler(self.directory / "training.log", mode="w", encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        self.log.addHandler(fh)
        self.log.addHandler(sh)
        self.log.info("run %s started (python %s, %s)", self.name, platform.python_version(), platform.platform())

    def path(self, filename: str) -> Path:
        return self.directory / filename

    def save_metrics(self, metrics: dict[str, Any]) -> Path:
        payload = {
            "run": self.name,
            "family": self.family,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "duration_seconds": round(time.time() - self.started, 1),
            "seed": SEED,
            **metrics,
        }
        out = self.path("metrics.json")
        out.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
        self.log.info("metrics written to %s", out.relative_to(ROOT))
        return out


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return o.as_posix()
    raise TypeError(f"not serialisable: {type(o)}")


def best_f1_threshold(y_true: np.ndarray, scores: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-12, None)
    idx = int(np.nanargmax(f1[:-1])) if len(thresholds) else 0
    return float(thresholds[idx]) if len(thresholds) else 0.5


def threshold_for_recall(y_true: np.ndarray, scores: np.ndarray, target: float) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    ok = np.where(recall[:-1] >= target)[0]
    return float(thresholds[ok[-1]]) if len(ok) else float(thresholds[0])


def threshold_for_precision(y_true: np.ndarray, scores: np.ndarray, target: float) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    ok = np.where(precision[:-1] >= target)[0]
    return float(thresholds[ok[0]]) if len(ok) else float(thresholds[-1])


def classification_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    y_true = np.asarray(y_true).astype(int)
    pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "n": int(len(y_true)),
        "positives": int(y_true.sum()),
        "prevalence": round(float(y_true.mean()), 5),
        "threshold": round(float(threshold), 5),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "pr_auc": round(float(average_precision_score(y_true, scores)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, scores)), 4) if len(np.unique(y_true)) > 1 else None,
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def plot_confusion(cm: dict[str, int], title: str, path: Path, labels=("Legitimate", "Fraud")) -> None:
    mat = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    ax.grid(False)
    im = ax.imshow(mat, cmap="Greens")
    for (i, j), v in np.ndenumerate(mat):
        ax.text(j, i, f"{v:,}", ha="center", va="center", color="white" if v > mat.max() / 2 else "#0f172a", fontsize=12)
    ax.set_xticks([0, 1], [f"Predicted\n{labels[0]}", f"Predicted\n{labels[1]}"])
    ax.set_yticks([0, 1], [f"Actual\n{labels[0]}", f"Actual\n{labels[1]}"])
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_pr_roc(curves: dict[str, tuple[np.ndarray, np.ndarray]], title: str, path_pr: Path, path_roc: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    for i, (name, (y, s)) in enumerate(curves.items()):
        p, r, _ = precision_recall_curve(y, s)
        ax.plot(r, p, color=SERIES[i % len(SERIES)], lw=2, label=f"{name} (AP {average_precision_score(y, s):.3f})")
    base = float(np.mean(next(iter(curves.values()))[0]))
    ax.axhline(base, color=BRAND["muted"], ls="--", lw=1, label=f"Base rate {base:.3f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(f"{title} - precision-recall")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path_pr)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    for i, (name, (y, s)) in enumerate(curves.items()):
        fpr, tpr, _ = roc_curve(y, s)
        ax.plot(fpr, tpr, color=SERIES[i % len(SERIES)], lw=2, label=f"{name} (AUC {roc_auc_score(y, s):.3f})")
    ax.plot([0, 1], [0, 1], color=BRAND["muted"], ls="--", lw=1)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(f"{title} - ROC")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path_roc)
    plt.close(fig)


def plot_calibration(y: np.ndarray, s: np.ndarray, title: str, path: Path, bins: int = 10) -> None:
    frac, mean = calibration_curve(y, s, n_bins=bins, strategy="quantile")
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.plot([0, 1], [0, 1], color=BRAND["muted"], ls="--", lw=1, label="Perfect")
    ax.plot(mean, frac, marker="o", color=BRAND["primary"], lw=2, label="Model")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed rate")
    ax.set_title(f"{title} - calibration")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_bars(values: dict[str, float], title: str, xlabel: str, path: Path, color: str = BRAND["primary"]) -> None:
    items = sorted(values.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(6.4, max(2.6, 0.32 * len(items) + 1)))
    ax.barh([k for k, _ in items], [v for _, v in items], color=color)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=_json_default, ensure_ascii=False), encoding="utf-8")


def run_name(prefix: str) -> str:
    return f"{prefix}_{datetime.now():%Y%m%d}"
