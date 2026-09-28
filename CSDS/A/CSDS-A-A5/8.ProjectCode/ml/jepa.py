"""Small Joint-Embedding Predictive Architecture (JEPA) for behaviour vectors.

A sample is one taxpayer-month (or one transaction when window=0). The model never
reconstructs raw values; it predicts the *embedding* of the current vector:

  context  = embeddings of the previous `window` months (online encoder)
           + the current vector with one block hidden (online encoder)
  target   = embedding of the full current vector (EMA target encoder, no gradient)
  predictor(context, which-block-is-hidden) -> predicted target embedding

Mask variant 0 hides the whole current vector (pure "what should this month look like
given its history"); variant k hides feature group k ("is this layer consistent with the
others"). The prediction error averaged over variants is the anomaly score; per-variant
errors say which layer deviates. A variance term keeps the online encoder from collapsing.
"""
import copy
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class Encoder(nn.Module):
    def __init__(self, d_in, hidden, emb):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, hidden), nn.LayerNorm(hidden), nn.GELU(),
                                 nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, emb))

    def forward(self, x):
        return self.net(x)


class JEPA(nn.Module):
    def __init__(self, d_in, groups, window=3, hidden=64, emb=32):
        super().__init__()
        self.d_in, self.window, self.emb = d_in, window, emb
        self.groups = [list(g) for g in groups]
        keep = torch.ones(len(groups) + 1, d_in)
        keep[0] = 0
        for k, g in enumerate(self.groups):
            keep[k + 1, g] = 0
        self.register_buffer("keep", keep)
        self.encoder = Encoder(d_in, hidden, emb)
        self.target = copy.deepcopy(self.encoder)
        for p in self.target.parameters():
            p.requires_grad_(False)
        n_var = len(groups) + 1
        self.predictor = nn.Sequential(nn.Linear(window * (emb + 1) + emb + n_var, 128), nn.GELU(),
                                       nn.Linear(128, 128), nn.GELU(), nn.Linear(128, emb))

    @property
    def n_variants(self):
        return len(self.groups) + 1

    def predict(self, ctx, ctx_present, cur, variant):
        b = cur.shape[0]
        parts = []
        if self.window:
            h = self.encoder(ctx.reshape(-1, self.d_in)).reshape(b, self.window, self.emb)
            h = h * ctx_present.unsqueeze(-1)
            parts += [h.reshape(b, -1), ctx_present]
        parts += [self.encoder(cur * self.keep[variant]), F.one_hot(variant, self.n_variants).float()]
        return self.predictor(torch.cat(parts, dim=1))

    @torch.no_grad()
    def update_target(self, momentum):
        for p, q in zip(self.encoder.parameters(), self.target.parameters()):
            q.mul_(momentum).add_(p.detach(), alpha=1 - momentum)


def make_samples(Z, present, window):
    """Z: (n, T, D) scaled features, present: (n, T). Returns context/current arrays for present cells."""
    n, T, D = Z.shape
    Zp = np.concatenate([np.zeros((n, window, D), np.float32), Z], axis=1)
    Pp = np.concatenate([np.zeros((n, window), np.float32), present.astype(np.float32)], axis=1)
    ii, mm = np.nonzero(present)
    ctx = np.stack([Zp[ii, mm + k] for k in range(window)], axis=1) if window else np.zeros((len(ii), 0, D), np.float32)
    ctxp = np.stack([Pp[ii, mm + k] for k in range(window)], axis=1) if window else np.zeros((len(ii), 0), np.float32)
    return ii, mm, ctx.astype(np.float32), ctxp.astype(np.float32), Z[ii, mm].astype(np.float32)


def train_jepa(ctx, ctxp, cur, groups, window, epochs=40, batch=256, lr=1e-3, seed=42, ema=0.99,
               var_weight=1.0, progress=None):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = JEPA(cur.shape[1], groups, window)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=1e-4)
    tc, tp, tx = torch.from_numpy(ctx), torch.from_numpy(ctxp), torch.from_numpy(cur)
    n = len(tx)
    g = torch.Generator().manual_seed(seed)
    history = []
    t0 = time.time()
    for ep in range(epochs):
        perm = torch.randperm(n, generator=g)
        tot, nb = 0.0, 0
        for s in range(0, n, batch):
            idx = perm[s:s + batch]
            c, p, x = tc[idx], tp[idx], tx[idx]
            variant = torch.randint(0, model.n_variants, (len(idx),), generator=g)
            pred = model.predict(c, p, x, variant)
            with torch.no_grad():
                target = model.target(x)
            loss_pred = F.mse_loss(pred, target)
            z = model.encoder(x)
            loss_var = F.relu(1 - z.std(dim=0)).mean()
            loss = loss_pred + var_weight * loss_var
            opt.zero_grad()
            loss.backward()
            opt.step()
            model.update_target(ema)
            tot += loss_pred.item()
            nb += 1
        history.append(round(tot / nb, 5))
        if progress:
            progress(ep + 1, epochs, history[-1])
    return model, dict(epochs=epochs, batch=batch, lr=lr, ema=ema, window=window, samples=n,
                       loss_history=history, final_loss=history[-1], train_seconds=round(time.time() - t0, 1))


@torch.no_grad()
def score(model, ctx, ctxp, cur, batch=4096):
    """Returns (n, n_variants) squared prediction errors in embedding space."""
    model.eval()
    out = []
    for s in range(0, len(cur), batch):
        c, p, x = (torch.from_numpy(a[s:s + batch]) for a in (ctx, ctxp, cur))
        target = model.target(x)
        errs = []
        for v in range(model.n_variants):
            pred = model.predict(c, p, x, torch.full((len(x),), v, dtype=torch.long))
            errs.append(((pred - target) ** 2).mean(dim=1))
        out.append(torch.stack(errs, dim=1))
    model.train()
    return torch.cat(out).numpy()


def save_model(model, path, extra):
    torch.save({"state_dict": model.state_dict(), "d_in": model.d_in, "groups": model.groups,
                "window": model.window, **extra}, path)


def load_model(path):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    model = JEPA(ck["d_in"], ck["groups"], ck["window"])
    model.load_state_dict(ck["state_dict"])
    model.eval()
    return model, ck
