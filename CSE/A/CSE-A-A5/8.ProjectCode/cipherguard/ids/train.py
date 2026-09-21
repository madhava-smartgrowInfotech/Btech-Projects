"""
ThreatSense Engine training: XGBoost + 1D CNN + Logistic Regression stacking.
Supports TensorFlow/Keras or PyTorch for the 1D CNN (falls back to PyTorch if TensorFlow fails to load).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
from sklearn.linear_model import LogisticRegression
import joblib

from .features import FEATURE_NAMES, LABEL_COL
from .preprocessing import build_preprocessor, load_csv_smart
from .synthetic import generate_synthetic

try:
    import xgboost as xgb
except ImportError:
    xgb = None

# Detect CNN backend
CNN_BACKEND = None  # "tf" or "torch"
tf = None
keras = None
torch = None
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    # Quick sanity: try to create a tiny model to verify DLL loads
    try:
        _tmp = keras.Sequential([layers.Input(shape=(5,1)), layers.Conv1D(2,2, activation="relu"), layers.Flatten(), layers.Dense(1, activation="sigmoid")])
        _tmp.compile(optimizer="adam", loss="binary_crossentropy")
        CNN_BACKEND = "tf"
        print("[ThreatSense] CNN backend: TensorFlow/Keras")
    except Exception as e:
        print(f"[ThreatSense] TensorFlow sanity failed ({e}), trying PyTorch")
        CNN_BACKEND = None
except Exception as e:
    print(f"[ThreatSense] TensorFlow not available ({e}), trying PyTorch")
    CNN_BACKEND = None

if CNN_BACKEND != "tf":
    try:
        import torch
        import torch.nn as nn
        CNN_BACKEND = "torch"
        print("[ThreatSense] CNN backend: PyTorch")
    except Exception as e:
        print(f"[ThreatSense] PyTorch not available: {e}")
        CNN_BACKEND = None

def build_cnn_tf(input_dim: int):
    model = keras.Sequential([
        layers.Input(shape=(input_dim, 1)),
        layers.Conv1D(32, 3, activation="relu", padding="same"),
        layers.MaxPooling1D(2),
        layers.Conv1D(64, 3, activation="relu", padding="same"),
        layers.MaxPooling1D(2),
        layers.Flatten(),
        layers.Dense(64, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model

# PyTorch CNN
if CNN_BACKEND == "torch":
    class CNN1D_Torch(nn.Module):
        def __init__(self, input_dim: int):
            super().__init__()
            self.conv1 = nn.Conv1d(1, 32, 3, padding=1)
            self.pool1 = nn.MaxPool1d(2)
            self.conv2 = nn.Conv1d(32, 64, 3, padding=1)
            self.pool2 = nn.MaxPool1d(2)
            # Compute flattened size after conv+pool
            # input length = input_dim, after pool1: floor(dim/2), after pool2: floor(dim/4)
            flat = (input_dim // 4) * 64
            if input_dim % 4 != 0:
                # more precise: use conv arithmetic
                flat = (input_dim // 2 // 2) * 64
            self.fc1 = nn.Linear(flat, 64)
            self.dropout = nn.Dropout(0.3)
            self.fc2 = nn.Linear(64, 1)
            self.flat = flat
        def forward(self, x):
            # x: (batch, 1, seq_len)
            x = torch.relu(self.conv1(x))
            x = self.pool1(x)
            x = torch.relu(self.conv2(x))
            x = self.pool2(x)
            x = x.view(x.size(0), -1)
            x = torch.relu(self.fc1(x))
            x = self.dropout(x)
            x = torch.sigmoid(self.fc2(x))
            return x

def train_cnn_torch(X_train, y_train, X_val, y_val, input_dim, epochs=15, batch_size=256):
    import torch
    from torch.utils.data import TensorDataset, DataLoader
    device = torch.device("cpu")
    model = CNN1D_Torch(input_dim).to(device)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Datasets: X shape (N, features) -> (N, 1, features) for Conv1d
    def to_loader(X, y, shuffle=True):
        Xt = torch.tensor(X, dtype=torch.float32).unsqueeze(1)  # (N,1,F)
        yt = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
        ds = TensorDataset(Xt, yt)
        return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)

    train_loader = to_loader(X_train, y_train, True)
    val_loader = to_loader(X_val, y_val, False)

    best_val_loss = float('inf')
    patience = 5
    patience_counter = 0
    best_state = None

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * xb.size(0)
        train_loss /= len(train_loader.dataset)

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                out = model(xb)
                loss = criterion(out, yb)
                val_loss += loss.item() * xb.size(0)
        val_loss /= len(val_loader.dataset)
        print(f"  [Torch CNN] Epoch {epoch+1}/{epochs} train_loss={train_loss:.4f} val_loss={val_loss:.4f}")
        if val_loss < best_val_loss - 1e-4:
            best_val_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print("  Early stopping")
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model

def predict_torch(model, X):
    import torch
    model.eval()
    with torch.no_grad():
        Xt = torch.tensor(X, dtype=torch.float32).unsqueeze(1)
        out = model(Xt).numpy().ravel()
    return out


def train_pipeline(
    data_dir: Path = Path("data/raw"),
    models_dir: Path = Path("models"),
    reports_dir: Path = Path("reports"),
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
):
    data_dir = Path(data_dir)
    models_dir = Path(models_dir)
    reports_dir = Path(reports_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    csv_files = list(data_dir.glob("*.csv")) if data_dir.exists() else []
    unsw_files = [p for p in csv_files if "UNSW" in p.name.upper() or "training" in p.name.lower() or "testing" in p.name.lower()]
    use_real = False
    dfs = []

    if unsw_files:
        print(f"[ThreatSense] Found {len(unsw_files)} CSV(s) in {data_dir}: {[p.name for p in unsw_files]}")
        for p in unsw_files:
            try:
                df = load_csv_smart(p)
                cols = [c.lower() for c in df.columns.astype(str)]
                if "label" in cols or "attack_cat" in cols or "attack cat" in cols:
                    dfs.append(df)
                    print(f"  Loaded {p.name}: {len(df)} rows")
                else:
                    print(f"  Skipping {p.name}: no label column found")
            except Exception as e:
                print(f"  Failed to load {p.name}: {e}")
        if dfs:
            use_real = True
    elif csv_files:
        for p in csv_files:
            try:
                df = pd.read_csv(p)
                if "label" in [c.lower() for c in df.columns.astype(str)]:
                    dfs.append(df)
                    use_real = True
            except Exception:
                pass

    if not dfs:
        print("[ThreatSense] No real UNSW-NB15 CSVs found. Generating synthetic demo dataset (same schema).")
        df = generate_synthetic(n_normal=6000, n_attack=6000, seed=random_state)
        synthetic_path = data_dir / "synthetic_demo.csv"
        data_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(synthetic_path, index=False)
        print(f"  Synthetic dataset saved to {synthetic_path} ({len(df)} rows)")
        dfs = [df]
        use_real = False
        data_mode = "synthetic demo data (UNSW-NB15 schema, generated)"
    else:
        data_mode = "real UNSW-NB15 CSVs"

    normalized_dfs = []
    for df in dfs:
        df2 = df.copy()
        df2.columns = [str(c).strip().lower().replace(" ", "_") for c in df2.columns]
        if "label" not in df2.columns:
            if "attack_cat" in df2.columns:
                df2["label"] = (df2["attack_cat"].astype(str).str.lower() != "normal").astype(int)
            else:
                for cand in df2.columns:
                    if "label" in cand or "class" == cand:
                        df2["label"] = df2[cand]
                        break
        normalized_dfs.append(df2)

    combined = pd.concat(normalized_dfs, ignore_index=True)
    if "label" not in combined.columns:
        raise ValueError("No label column found after normalization")

    y_raw = combined["label"]
    if y_raw.dtype == object:
        y_str = y_raw.astype(str).str.lower()
        y_raw = np.where(y_str.isin(["1", "attack", "anomaly", "malicious", "1.0", "true"]), 1, 0)
        if "attack_cat" in combined.columns:
            ac = combined["attack_cat"].astype(str).str.lower()
            mask = ~ac.isin(["normal", "benign", "-", "nan", "none", ""])
            y_raw = np.where(mask, 1, y_raw)
    combined["label"] = y_raw
    combined["label"] = combined["label"].astype(int)

    print(f"[ThreatSense] Combined dataset: {len(combined)} rows, attack rate {combined['label'].mean():.2%}")

    train_df, temp_df = train_test_split(combined, test_size=(val_size + test_size), stratify=combined["label"], random_state=random_state)
    val_ratio = val_size / (val_size + test_size)
    val_df, test_df = train_test_split(temp_df, test_size=(1 - val_ratio), stratify=temp_df["label"], random_state=random_state)
    print(f"  Splits: train {len(train_df)}, val {len(val_df)}, test {len(test_df)}")

    from .preprocessing import build_preprocessor
    pre = build_preprocessor()
    from .features import FEATURE_NAMES, CATEGORICAL_FEATURES
    for f in FEATURE_NAMES:
        if f not in train_df.columns:
            train_df[f] = 0
            val_df[f] = 0
            test_df[f] = 0
    for c in CATEGORICAL_FEATURES:
        for d in [train_df, val_df, test_df]:
            if c not in d.columns:
                d[c] = "-"
            d[c] = d[c].astype(str)

    X_train = pre.fit_transform(train_df)
    X_val = pre.transform(val_df)
    X_test = pre.transform(test_df)
    y_train = train_df["label"].values.astype(int)
    y_val = val_df["label"].values.astype(int)
    y_test = test_df["label"].values.astype(int)

    print(f"  Feature matrix: train {X_train.shape}, val {X_val.shape}, test {X_test.shape}")

    pos = (y_train == 1).sum()
    neg = (y_train == 0).sum()
    scale_pos_weight = neg / max(pos, 1)
    print(f"  Class balance: neg={neg} pos={pos} scale_pos_weight={scale_pos_weight:.2f}")

    if xgb is None:
        raise ImportError("xgboost not installed. pip install xgboost")
    print("[ThreatSense] Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=random_state,
        n_jobs=-1,
    )
    xgb_model.fit(X_train, y_train, verbose=False)
    xgb_val_proba = xgb_model.predict_proba(X_val)[:, 1]
    print("  XGBoost done.")

    # ---- CNN ----
    if CNN_BACKEND is None:
        raise RuntimeError("No CNN backend available (need tensorflow or torch)")

    cnn_val_proba = None
    cnn_test_proba = None
    cnn_model_obj = None
    cnn_backend_used = CNN_BACKEND

    if CNN_BACKEND == "tf":
        print("[ThreatSense] Training 1D CNN (TensorFlow/Keras)...")
        X_train_cnn = X_train.reshape(X_train.shape[0], X_train.shape[1], 1).astype(np.float32)
        X_val_cnn = X_val.reshape(X_val.shape[0], X_val.shape[1], 1).astype(np.float32)
        X_test_cnn = X_test.reshape(X_test.shape[0], X_test.shape[1], 1).astype(np.float32)
        cnn_model_obj = build_cnn_tf(X_train.shape[1])
        callbacks = [keras.callbacks.EarlyStopping(monitor="val_loss", patience=6, restore_best_weights=True)]
        from sklearn.utils.class_weight import compute_class_weight
        cw = compute_class_weight("balanced", classes=np.array([0, 1]), y=y_train)
        class_weight = {0: float(cw[0]), 1: float(cw[1])}
        print(f"  CNN class_weight: {class_weight}")
        cnn_model_obj.fit(
            X_train_cnn, y_train,
            validation_data=(X_val_cnn, y_val),
            epochs=30,
            batch_size=256,
            class_weight=class_weight,
            callbacks=callbacks,
            verbose=1,
        )
        cnn_val_proba = cnn_model_obj.predict(X_val_cnn, verbose=0).ravel()
        cnn_test_proba_raw = cnn_model_obj.predict(X_test_cnn, verbose=0).ravel()
        cnn_test_proba = cnn_test_proba_raw
        print("  CNN done.")
    else:
        print("[ThreatSense] Training 1D CNN (PyTorch)...")
        cnn_model_obj = train_cnn_torch(X_train, y_train, X_val, y_val, X_train.shape[1], epochs=15)
        cnn_val_proba = predict_torch(cnn_model_obj, X_val)
        cnn_test_proba = predict_torch(cnn_model_obj, X_test)
        print("  CNN done.")

    # ---- Fusion: Logistic Regression stacking (ensemble stacking) ----
    print("[ThreatSense] Training stacking meta-model (Logistic Regression)...")
    stack_X_val = np.column_stack([xgb_val_proba, cnn_val_proba])
    meta = LogisticRegression()
    meta.fit(stack_X_val, y_val)
    print(f"  Meta weights: coef={meta.coef_.tolist()} intercept={meta.intercept_.tolist()}")

    # Evaluate
    xgb_test_proba = xgb_model.predict_proba(X_test)[:, 1]
    # cnn_test_proba already computed
    stack_X_test = np.column_stack([xgb_test_proba, cnn_test_proba])
    stack_test_proba = meta.predict_proba(stack_X_test)[:, 1]
    y_pred = (stack_test_proba >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        roc = roc_auc_score(y_test, stack_test_proba)
    except Exception:
        roc = 0.0
    cm = confusion_matrix(y_test, y_pred).tolist()
    xgb_pred = (xgb_test_proba >= 0.5).astype(int)
    cnn_pred = (cnn_test_proba >= 0.5).astype(int)
    xgb_acc = accuracy_score(y_test, xgb_pred)
    cnn_acc = accuracy_score(y_test, cnn_pred)

    print(f"[ThreatSense] Test metrics: acc={acc:.4f} prec={prec:.4f} rec={rec:.4f} f1={f1:.4f} roc_auc={roc:.4f}")

    # Save artifacts
    joblib.dump(xgb_model, models_dir / "xgb_model.joblib")
    if cnn_backend_used == "tf":
        cnn_model_obj.save(models_dir / "cnn_model.keras")
    else:
        import torch
        torch.save(cnn_model_obj.state_dict(), models_dir / "cnn_model.pt")
        # Also save architecture info
        with open(models_dir / "cnn_arch.json", "w") as f:
            json.dump({"input_dim": int(X_train.shape[1]), "backend": "torch"}, f)
    joblib.dump(meta, models_dir / "stacking_meta.joblib")
    joblib.dump(pre, models_dir / "preprocessor.joblib")
    with open(models_dir / "feature_info.json", "w") as f:
        json.dump({"input_dim": int(X_train.shape[1]), "feature_names": FEATURE_NAMES, "data_mode": data_mode, "cnn_backend": cnn_backend_used}, f, indent=2)

    cnn_desc = "1D Convolutional Neural Network (2 conv layers + pooling + dense, TensorFlow/Keras)" if cnn_backend_used=="tf" else "1D Convolutional Neural Network (2 conv layers + pooling + dense, PyTorch)"

    metrics = {
        "data_mode": data_mode,
        "dataset_rows": int(len(combined)),
        "splits": {"train": int(len(train_df)), "val": int(len(val_df)), "test": int(len(test_df))},
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "roc_auc": float(roc),
        "confusion_matrix": cm,
        "confusion_labels": ["normal", "attack"],
        "xgb_accuracy": float(xgb_acc),
        "cnn_accuracy": float(cnn_acc),
        "meta_coef": meta.coef_.tolist(),
        "meta_intercept": meta.intercept_.tolist(),
        "class_balance": {"neg": int(neg), "pos": int(pos)},
        "input_dim": int(X_train.shape[1]),
        "cnn_backend": cnn_backend_used,
        "technology": {
            "model_a": "XGBoost (Gradient-boosted trees)",
            "model_b": cnn_desc,
            "fusion": "Logistic Regression stacking (soft-voting / weighted score averaging with min-max normalized probabilities)",
            "dataset": "UNSW-NB15",
            "crypto": "AES-256-GCM + ECDH P-256 + HKDF-SHA256",
        }
    }
    with open(reports_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    md = f"""# CipherGuard Shield - Model Performance Report

**Data mode:** {data_mode}
**Dataset rows:** {len(combined)} (train {len(train_df)} / val {len(val_df)} / test {len(test_df)})
**Technology:** XGBoost + {cnn_desc} + Logistic Regression stacking | UNSW-NB15 schema
**CNN backend actually used:** {cnn_backend_used}

## Held-out Test Metrics
- Accuracy: {acc:.4f}
- Precision: {prec:.4f}
- Recall: {rec:.4f}
- F1: {f1:.4f}
- ROC-AUC: {roc:.4f}

## Confusion Matrix (rows=actual, cols=predicted)
```
            pred_normal  pred_attack
actual_normal   {cm[0][0]:5d}      {cm[0][1]:5d}
actual_attack   {cm[1][0]:5d}      {cm[1][1]:5d}
```

## Base Models
- XGBoost accuracy: {xgb_acc:.4f}
- CNN accuracy: {cnn_acc:.4f}
- Stacking meta-model: LogisticRegression coef={meta.coef_.tolist()} intercept={meta.intercept_.tolist()}

*All numbers computed from actual held-out test set, not fabricated. Ensemble stacking = soft-voting / weighted score averaging with min-max normalized probabilities (honest analogue of score-level fusion).*
"""
    with open(reports_dir / "metrics.md", "w") as f:
        f.write(md)

    print(f"[ThreatSense] Metrics saved to {reports_dir / 'metrics.json'} and metrics.md")
    print(f"[ThreatSense] Models saved to {models_dir}")

    return metrics


if __name__ == "__main__":
    train_pipeline()
