"""Loads the trained model files once and reports what is available."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

import joblib

from app.core.config import MODELS_DIR
from app.core.logging import get_logger

log = get_logger("upi_guardian.models")

MODEL_FILES = {
    "behaviour": "behaviour_model.joblib",
    "sms": "sms_model.joblib",
    "risk": "risk_model.joblib",
}
POLICY_FILE = "risk_policy.json"


@dataclass
class ModelRegistry:
    directory: Path = MODELS_DIR
    bundles: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def load(self) -> None:
        with self._lock:
            self.bundles.clear()
            self.errors.clear()
            for name, filename in MODEL_FILES.items():
                path = self.directory / filename
                if not path.exists():
                    self.errors[name] = f"{filename} not found - run ml/train_all.py"
                    continue
                try:
                    self.bundles[name] = joblib.load(path)
                except Exception as exc:  # pragma: no cover - corrupted file
                    self.errors[name] = f"could not load {filename}: {exc}"
                    log.exception("model load failed", extra={"model": name})
            policy_path = self.directory / POLICY_FILE
            self.policy = json.loads(policy_path.read_text(encoding="utf-8")) if policy_path.exists() else {}

    def get(self, name: str) -> Any:
        bundle = self.bundles.get(name)
        if bundle is None:
            raise RuntimeError(self.errors.get(name, f"model '{name}' is not loaded"))
        return bundle

    def available(self, name: str) -> bool:
        return name in self.bundles

    def status(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name in MODEL_FILES:
            bundle = self.bundles.get(name)
            if bundle is not None:
                out[name] = {"loaded": True, "version": bundle.get("version", "unknown")}
            else:
                out[name] = {"loaded": False, "error": self.errors.get(name, "not loaded")}
        return out


registry = ModelRegistry()
