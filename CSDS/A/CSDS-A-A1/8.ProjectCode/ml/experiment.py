"""Experiment run folders: ``experiments/<run-name>/`` with metrics.json, predictions, plots and a log."""

from __future__ import annotations

import json
import logging
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT / "experiments"


@dataclass
class ExperimentRun:
    name: str
    path: Path
    started_at: str
    logger: logging.Logger
    metrics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, prefix: str = "eval", name: str | None = None) -> "ExperimentRun":
        """Create (or reopen, for resumed runs) ``experiments/<prefix>-YYYYMMDD-HHMM``."""
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        run_name = name or f"{prefix}-{stamp}"
        path = EXPERIMENTS_DIR / run_name
        (path / "plots").mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(f"policylens.eval.{run_name}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
            file_handler = logging.FileHandler(path / "eval.log", encoding="utf-8")
            file_handler.setFormatter(fmt)
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(fmt)
            logger.addHandler(file_handler)
            logger.addHandler(console)

        existing = path / "metrics.json"
        metrics = json.loads(existing.read_text(encoding="utf-8")) if existing.exists() else {}
        started = metrics.get("started_at") or datetime.now(timezone.utc).isoformat(timespec="seconds")
        run = cls(name=run_name, path=path, started_at=started, logger=logger, metrics=metrics)
        logger.info("Run %s -> %s", run_name, path)
        return run

    # --- artefacts -------------------------------------------------------------

    def plot_path(self, filename: str) -> Path:
        return self.path / "plots" / filename

    def append_prediction(self, record: dict[str, Any], filename: str = "predictions.jsonl") -> None:
        with (self.path / filename).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_predictions(self, filename: str = "predictions.jsonl") -> list[dict[str, Any]]:
        file = self.path / filename
        if not file.exists():
            return []
        return [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]

    def update_metrics(self, section: str, values: dict[str, Any]) -> None:
        self.metrics[section] = values
        self.save()

    def save(self, *, dataset: dict[str, Any] | None = None, settings: dict[str, Any] | None = None) -> Path:
        self.metrics.setdefault("run", self.name)
        self.metrics["started_at"] = self.started_at
        self.metrics["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.metrics.setdefault("environment", {
            "python": platform.python_version(),
            "platform": platform.platform(),
        })
        if dataset is not None:
            self.metrics["dataset"] = dataset
        if settings is not None:
            self.metrics["settings"] = settings
        out = self.path / "metrics.json"
        out.write_text(json.dumps(self.metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    def mark_latest(self) -> None:
        """Point ``experiments/latest.json`` at this run (read by the Model performance page)."""
        EXPERIMENTS_DIR.mkdir(exist_ok=True)
        pointer = {
            "run": self.name,
            "path": f"experiments/{self.name}",
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        (EXPERIMENTS_DIR / "latest.json").write_text(json.dumps(pointer, indent=2), encoding="utf-8")
        self.logger.info("experiments/latest.json -> %s", self.name)
