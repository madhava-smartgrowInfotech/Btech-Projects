"""QuantPulse deep models (TensorFlow/Keras, Sequential + Functional APIs).

Tiers:
  - baseline LSTM: 1x LSTM(64) + BatchNorm + Dropout + Dense(1)
  - LSTM+Attention: LSTM(64, return_sequences) + MultiHeadAttention(4 heads)
    + residual + LayerNorm + GlobalAveragePooling + Dense(32) + Dense(1)
  - +Sentiment variants: same architectures with an extra sentiment channel
    concatenated to the OHLCV input (window x (F+1)).

Windowing: 20-trading-day sliding window, Min-Max normalized to [0,1]
(scalers fit on train only). Training: batch 32, up to 50 epochs with
early stopping (patience 7, restore best).
"""
from __future__ import annotations
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from . import config


def make_windows(values: np.ndarray, window: int = 20):
    X, y, idx = [], [], []
    for i in range(window, len(values)):
        X.append(values[i - window:i]); y.append(values[i, 3])  # Close is col 3 of OHLCV
        idx.append(i)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32), np.array(idx)


def scale_split(X, y, idx, n: int):
    k = int(len(X) * config.TRAIN_SPLIT)
    return (X[:k], y[:k], idx[:k]), (X[k:], y[k:], idx[k:])


def fit_scalers(train_raw: np.ndarray):
    scalers = [MinMaxScaler().fit(train_raw[:, j:j + 1]) for j in range(train_raw.shape[1])]
    return scalers


def apply_scalers(raw: np.ndarray, scalers) -> np.ndarray:
    out = np.zeros_like(raw, float)
    for j, sc in enumerate(scalers):
        out[:, j] = sc.transform(raw[:, j:j + 1]).ravel()
    return np.clip(out, 0, 1)


def build_lstm(input_shape) -> "keras.Model":
    from tensorflow import keras
    m = keras.Sequential([
        keras.layers.Input(shape=input_shape),
        keras.layers.LSTM(config.LSTM_UNITS),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(1),
    ])
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return m


def build_attention_lstm(input_shape) -> "keras.Model":
    from tensorflow import keras
    inp = keras.layers.Input(shape=input_shape)
    x = keras.layers.LSTM(config.LSTM_UNITS, return_sequences=True)(inp)
    attn = keras.layers.MultiHeadAttention(num_heads=config.ATTENTION_HEADS, key_dim=16)(x, x)
    x = keras.layers.Add()([x, attn])
    x = keras.layers.LayerNormalization()(x)
    x = keras.layers.GlobalAveragePooling1D()(x)
    x = keras.layers.Dense(32, activation="relu")(x)
    x = keras.layers.Dropout(0.2)(x)
    out = keras.layers.Dense(1)(x)
    m = keras.Model(inp, out)
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return m


def train_model(model, Xtr, ytr, validation_split=0.15, epochs=None, verbose=0):
    from tensorflow import keras
    cb = [keras.callbacks.EarlyStopping(monitor="val_loss", patience=7, restore_best_weights=True)]
    h = model.fit(Xtr, ytr, batch_size=config.BATCH_SIZE, epochs=epochs or config.EPOCHS,
                  validation_split=validation_split, callbacks=cb, verbose=verbose)
    return h


def evaluate_dl(y_true_scaled, y_pred_scaled, close_scaler, y_true_actual_tail=None) -> dict:
    yt = close_scaler.inverse_transform(np.asarray(y_true_scaled).reshape(-1, 1)).ravel()
    yp = close_scaler.inverse_transform(np.asarray(y_pred_scaled).reshape(-1, 1)).ravel()
    mae = float(mean_absolute_error(yt, yp)); mse = float(mean_squared_error(yt, yp))
    try:
        r2 = float(r2_score(yt, yp))
    except Exception:
        r2 = 0.0
    dt = (yt[1:] - yt[:-1]) > 0
    dp = (yp[1:] - yt[:-1]) > 0
    da = float((dt == dp).mean()) if len(dt) else 0.0
    return {"mae": mae, "mse": mse, "rmse": float(np.sqrt(mse)), "r2": r2,
            "directional_accuracy": da, "n_test": int(len(yt))}


def prepare_features(df, sentiment: np.ndarray | None):
    cols = ["Open", "High", "Low", "Close", "Volume"]
    raw = df[cols].to_numpy(float)
    if sentiment is not None:
        s = np.asarray(sentiment, float).reshape(-1, 1)
        raw = np.concatenate([raw, s], axis=1)
    return raw
