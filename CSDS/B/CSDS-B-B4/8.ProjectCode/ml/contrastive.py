"""Hybrid contrastive (Siamese) + attention network for tabular fraud detection.

A compact re-implementation of the published approach UPI Guardian builds on, used as a
comparison model: every feature becomes a token, self-attention mixes the tokens, and a
Siamese contrastive loss pulls same-class transactions together and pushes fraud away
from legitimate traffic, which helps under heavy class imbalance.
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn


class FeatureTokenizer(nn.Module):
    def __init__(self, n_features: int, dim: int) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.randn(n_features, dim) * 0.1)
        self.bias = nn.Parameter(torch.zeros(n_features, dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # [B, F] -> [B, F, D]
        return x.unsqueeze(-1) * self.weight + self.bias


class ContrastiveAttentionNet(nn.Module):
    def __init__(self, n_features: int, dim: int = 32, heads: int = 4, layers: int = 2, proj_dim: int = 16) -> None:
        super().__init__()
        self.tokenizer = FeatureTokenizer(n_features, dim)
        self.cls = nn.Parameter(torch.zeros(1, 1, dim))
        layer = nn.TransformerEncoderLayer(dim, heads, dim_feedforward=dim * 4, dropout=0.1, batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, layers)
        self.norm = nn.LayerNorm(dim)
        self.projection = nn.Sequential(nn.Linear(dim, dim), nn.ReLU(), nn.Linear(dim, proj_dim))
        self.classifier = nn.Sequential(nn.Linear(dim, dim), nn.ReLU(), nn.Dropout(0.1), nn.Linear(dim, 1))

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        tokens = self.tokenizer(x)
        tokens = torch.cat([self.cls.expand(x.size(0), -1, -1), tokens], dim=1)
        return self.norm(self.encoder(tokens)[:, 0])

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.embed(x)
        return self.classifier(h).squeeze(-1), nn.functional.normalize(self.projection(h), dim=-1)


def siamese_contrastive_loss(z: torch.Tensor, y: torch.Tensor, margin: float = 0.8) -> torch.Tensor:
    """Pairs each sample with a shuffled partner: same label -> close, different label -> at least `margin` apart."""
    perm = torch.randperm(z.size(0), device=z.device)
    d = (z - z[perm]).norm(dim=-1)
    same = (y == y[perm]).float()
    return (same * d.pow(2) + (1 - same) * torch.clamp(margin - d, min=0).pow(2)).mean()


def train_contrastive(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    *,
    epochs: int = 6,
    batch_size: int = 512,
    fraud_share: float = 0.25,
    contrastive_weight: float = 0.5,
    seed: int = 42,
    log=print,
) -> ContrastiveAttentionNet:
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    torch.set_num_threads(max(1, torch.get_num_threads()))
    model = ContrastiveAttentionNet(x_train.shape[1])
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    pos = np.where(y_train == 1)[0]
    neg = np.where(y_train == 0)[0]
    n_pos = max(1, int(batch_size * fraud_share))
    steps = len(y_train) // batch_size
    # Balanced batches oversample fraud. Scores are used for ranking (PR-AUC) with a threshold
    # tuned on validation, so no probability re-weighting is needed.
    bce = nn.BCEWithLogitsLoss()
    xt, yt = torch.tensor(x_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.float32)
    xv = torch.tensor(x_val, dtype=torch.float32)
    best_state, best_ap = None, -1.0
    from sklearn.metrics import average_precision_score

    for epoch in range(epochs):
        model.train()
        total = 0.0
        for _ in range(steps):
            idx = np.concatenate([rng.choice(pos, n_pos), rng.choice(neg, batch_size - n_pos)])
            xb, yb = xt[idx], yt[idx]
            logits, z = model(xb)
            loss = bce(logits, yb) + contrastive_weight * siamese_contrastive_loss(z, yb)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total += float(loss)
        val_scores = predict_contrastive(model, xv)
        ap = average_precision_score(y_val, val_scores)
        log(f"contrastive epoch {epoch + 1}/{epochs}  loss {total / steps:.4f}  val PR-AUC {ap:.4f}")
        if ap > best_ap:
            best_ap = ap
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)
    return model


@torch.no_grad()
def predict_contrastive(model: ContrastiveAttentionNet, x: np.ndarray | torch.Tensor, batch: int = 8192) -> np.ndarray:
    model.eval()
    x = torch.as_tensor(x, dtype=torch.float32)
    out = []
    for i in range(0, x.size(0), batch):
        logits, _ = model(x[i : i + batch])
        out.append(torch.sigmoid(logits))
    return torch.cat(out).numpy()
