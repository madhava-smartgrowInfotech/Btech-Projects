"""Simulated federated learning with manual FedAvg (in-process, no network).

Each ticker's dataset is treated as an independent client. A local
LSTM+Attention+Sentiment model is trained per client for a few epochs, then
weights are aggregated centrally with Federated Averaging (weight average
proportional to local sample count) for a small number of global rounds.

NOTE (code comment, not UI): this is a simulated decentralized-training mode
that runs fully in-process; it can later point at real client endpoints by
replacing `_train_client` with remote calls (e.g. Flower `flwr`).
"""
from __future__ import annotations
import numpy as np


def fedavg(weight_list: list[list[np.ndarray]], counts: list[int]) -> list[np.ndarray]:
    total = float(sum(counts))
    agg = []
    for layers in zip(*weight_list):
        agg.append(sum(w * (c / total) for w, c in zip(layers, counts)))
    return agg


def run_federated(build_fn, client_data: dict[str, tuple], rounds: int = 2, local_epochs: int = 5, input_shape=None):
    """client_data: ticker -> (X_train, y_train). Returns global weights + per-round loss."""
    import tensorflow as tf
    tf.random.set_seed(42); np.random.seed(42)
    global_model = build_fn(input_shape)
    history = {"rounds": []}
    tickers = list(client_data.keys())
    for r in range(rounds):
        w_list, counts, losses = [], [], []
        for t in tickers:
            Xtr, ytr = client_data[t]
            local = build_fn(input_shape)
            local.set_weights(global_model.get_weights())
            h = local.fit(Xtr, ytr, batch_size=32, epochs=local_epochs, verbose=0)
            w_list.append(local.get_weights())
            counts.append(len(Xtr))
            losses.append(float(h.history["loss"][-1]))
        global_model.set_weights(fedavg(w_list, counts))
        history["rounds"].append({"round": r + 1, "mean_local_loss": float(np.mean(losses))})
    return global_model, history
