"""
ThreatSense Engine inference: load artifacts, score records.
Supports both TF and PyTorch CNN backends.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from .features import FEATURE_NAMES, CATEGORICAL_FEATURES
from .preprocessing import transform_with_preprocessor

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

class ThreatSenseEngine:
    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.preprocessor = None
        self.xgb_model = None
        self.cnn_model = None
        self.meta_model = None
        self.input_dim = None
        self.cnn_backend = None
        self.loaded = False

    def load(self):
        pre_path = self.models_dir / "preprocessor.joblib"
        xgb_path = self.models_dir / "xgb_model.joblib"
        meta_path = self.models_dir / "stacking_meta.joblib"
        cnn_keras = self.models_dir / "cnn_model.keras"
        cnn_h5 = self.models_dir / "cnn_model.h5"
        cnn_pt = self.models_dir / "cnn_model.pt"

        if not pre_path.exists() or not xgb_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Model artifacts missing in {self.models_dir}. Run training first.")

        self.preprocessor = joblib.load(pre_path)
        self.xgb_model = joblib.load(xgb_path)
        self.meta_model = joblib.load(meta_path)

        info_path = self.models_dir / "feature_info.json"
        if info_path.exists():
            with open(info_path) as f:
                info = json.load(f)
                self.input_dim = info.get("input_dim")
                self.cnn_backend = info.get("cnn_backend", "tf")

        # Try to determine backend by files
        if cnn_pt.exists():
            self.cnn_backend = "torch"
        elif cnn_keras.exists() or cnn_h5.exists():
            self.cnn_backend = "tf"
        else:
            # Check feature_info
            if self.cnn_backend is None:
                raise FileNotFoundError(f"CNN model not found in {self.models_dir}")

        if self.cnn_backend == "tf":
            cnn_file = cnn_keras if cnn_keras.exists() else cnn_h5
            try:
                from tensorflow import keras
                self.cnn_model = keras.models.load_model(str(cnn_file))
            except Exception as e:
                raise RuntimeError(f"Failed to load TF CNN model: {e}")
        else:
            # Torch
            try:
                import torch
                import torch.nn as nn
                # Need architecture definition
                class CNN1D_Torch(nn.Module):
                    def __init__(self, input_dim: int):
                        super().__init__()
                        self.conv1 = nn.Conv1d(1, 32, 3, padding=1)
                        self.pool1 = nn.MaxPool1d(2)
                        self.conv2 = nn.Conv1d(32, 64, 3, padding=1)
                        self.pool2 = nn.MaxPool1d(2)
                        flat = (input_dim // 4) * 64
                        self.fc1 = nn.Linear(flat, 64)
                        self.dropout = nn.Dropout(0.3)
                        self.fc2 = nn.Linear(64, 1)
                    def forward(self, x):
                        x = torch.relu(self.conv1(x))
                        x = self.pool1(x)
                        x = torch.relu(self.conv2(x))
                        x = self.pool2(x)
                        x = x.view(x.size(0), -1)
                        x = torch.relu(self.fc1(x))
                        x = self.dropout(x)
                        x = torch.sigmoid(self.fc2(x))
                        return x
                if self.input_dim is None:
                    # Infer from state dict
                    sd = torch.load(str(cnn_pt), map_location="cpu")
                    # fc1 weight shape gives input_dim: weight shape [64, flat]
                    flat = sd["fc1.weight"].shape[1]
                    self.input_dim = (flat // 64) * 4
                self.cnn_model = CNN1D_Torch(self.input_dim)
                self.cnn_model.load_state_dict(torch.load(str(cnn_pt), map_location="cpu"))
                self.cnn_model.eval()
            except Exception as e:
                raise RuntimeError(f"Failed to load Torch CNN model: {e}")

        self.loaded = True

    def ensure_loaded(self):
        if not self.loaded:
            self.load()

    def _prepare_X(self, df: pd.DataFrame) -> np.ndarray:
        for f in FEATURE_NAMES:
            if f not in df.columns:
                lower_map = {str(c).lower(): c for c in df.columns}
                if f.lower() in lower_map:
                    df = df.rename(columns={lower_map[f.lower()]: f})
                else:
                    df[f] = 0
        for c in CATEGORICAL_FEATURES:
            if c not in df.columns:
                df[c] = "-"
            df[c] = df[c].astype(str)
        X = transform_with_preprocessor(df, self.preprocessor)
        return X

    def _cnn_predict(self, X: np.ndarray) -> np.ndarray:
        if self.cnn_backend == "tf":
            X_cnn = X.reshape(X.shape[0], X.shape[1], 1).astype(np.float32)
            return self.cnn_model.predict(X_cnn, verbose=0).ravel()
        else:
            import torch
            self.cnn_model.eval()
            with torch.no_grad():
                Xt = torch.tensor(X, dtype=torch.float32).unsqueeze(1)
                out = self.cnn_model(Xt).numpy().ravel()
            return out

    def predict_proba(self, df: pd.DataFrame) -> dict:
        self.ensure_loaded()
        X = self._prepare_X(df)
        xgb_proba = self.xgb_model.predict_proba(X)[:, 1]
        cnn_proba = self._cnn_predict(X)
        stack_X = np.column_stack([xgb_proba, cnn_proba])
        ensemble_proba = self.meta_model.predict_proba(stack_X)[:, 1]
        preds = (ensemble_proba >= 0.5).astype(int)
        return {
            "ensemble_proba": ensemble_proba.tolist(),
            "ensemble_pred": preds.tolist(),
            "xgb_proba": xgb_proba.tolist(),
            "cnn_proba": cnn_proba.tolist(),
            "labels": ["attack" if p == 1 else "normal" for p in preds],
        }

    def score_single(self, record: dict) -> dict:
        df = pd.DataFrame([record])
        res = self.predict_proba(df)
        idx = 0
        prob = res["ensemble_proba"][idx]
        label = res["labels"][idx]
        severity = "low"
        if label == "attack":
            if prob >= 0.85:
                severity = "critical"
            elif prob >= 0.70:
                severity = "high"
            else:
                severity = "medium"
        return {
            "label": label,
            "confidence": float(prob),
            "severity": severity,
            "xgb_score": float(res["xgb_proba"][idx]),
            "cnn_score": float(res["cnn_proba"][idx]),
        }

    def get_metrics(self) -> dict:
        path = REPORTS_DIR / "metrics.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        alt = Path(__file__).resolve().parents[2] / "reports" / "metrics.json"
        if alt.exists():
            with open(alt) as f:
                return json.load(f)
        return {}
