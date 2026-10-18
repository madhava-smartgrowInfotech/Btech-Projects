"""Server-side equivalent of Streamlit's st.session_state (single user, in memory).

The trained *active* model survives restarts through src/persistence.py exactly like
app.py restores it. The dataset and the training comparison are session-only, as in Streamlit.
"""
import sys
import threading
from dataclasses import dataclass, field
from typing import Any

from . import config

# Make src/ importable as top-level modules, the same way app.py does.
sys.path.insert(0, str(config.ROOT / "src"))

from persistence import artifacts_exist, load_artifacts  # noqa: E402
from utils import DEFAULT_RISK_THRESHOLDS  # noqa: E402


@dataclass
class AppState:
    lock: threading.RLock = field(default_factory=threading.RLock)

    # dataset
    dataset_name: str | None = None
    raw_df: Any = None
    working_df: Any = None
    target_col: str | None = None
    id_col: str | None = None
    numeric_cols: list = field(default_factory=list)
    categorical_cols: list = field(default_factory=list)
    feature_cols: list = field(default_factory=list)
    prepare_report: dict | None = None

    # trial run (the comparison shown on Training / Evaluation)
    trial: dict | None = None

    # active (saved) model
    model: Any = None
    preprocessor: Any = None
    model_name: str | None = None
    metadata: dict | None = None
    explainer: Any = None
    X_test_t: Any = None
    y_test: Any = None
    importance_cache: dict = field(default_factory=dict)

    risk_thresholds: dict = field(default_factory=lambda: DEFAULT_RISK_THRESHOLDS.copy())

    def restore_from_disk(self) -> None:
        if self.model is not None or not artifacts_exist():
            return
        try:
            model, preprocessor, metadata = load_artifacts()
        except Exception:
            return
        self.model, self.preprocessor, self.metadata = model, preprocessor, metadata
        if metadata:
            self.model_name = metadata.get("model_name")
            self.target_col = self.target_col or metadata.get("target_col")
            self.id_col = self.id_col or metadata.get("id_col")

    # --- convenience -------------------------------------------------------------
    @property
    def has_model(self) -> bool:
        return self.model is not None and self.preprocessor is not None

    @property
    def model_features(self) -> list:
        """Feature columns the active model was trained on (from its saved metadata)."""
        return list((self.metadata or {}).get("feature_cols") or self.feature_cols)

    @property
    def model_feature_names(self) -> list:
        return list((self.metadata or {}).get("feature_names") or [])


STATE = AppState()
