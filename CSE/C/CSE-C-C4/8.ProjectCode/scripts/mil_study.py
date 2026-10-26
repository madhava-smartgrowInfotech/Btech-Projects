"""Multiple-instance-learning study: does a bag of real daily headlines help predict next-day direction?

QuantPulse itself has no multiple-instance component (its sentiment channel is one averaged number per day). This script
runs the formulation the project title and the objectives ask for, offline and separately from the application:

  bag      = all headlines of one ticker published before a trading day's close   (instances: FinBERT-tone features)
  label    = 1 if the next trading day's close is above today's close             (bag-level label, no headline labels)
  data     = FNSPID headlines (real) + Yahoo Finance prices for the seven tickers that have at least 1,000 headlines
             (AAPL, AMZN, FDX, MSFT, NVDA, ORCL, TSLA); headlines are dense only from 2022, so the news era is 2022-2023
  split    = three expanding-window folds, each tested on one quarter of 2023 (Q2, Q3, Q4); the two months before a test
             quarter are the validation set, everything earlier in 2022-2023 is training; test predictions are pooled
  models   = majority class | logistic regression (price) | LSTM (price), matched window | LSTM (price), full history since 2016
             | LSTM + flat mean sentiment | LSTM + MIL mean / max / gated-attention pooling | MIL-attention on news only
             | placebo: MIL-attention with bags taken from other days of the same ticker
  metrics  = accuracy, precision, recall, F1 (up = positive class), ROC-AUC; five seeds for the neural models

Needs scripts/fetch_snapshot.py, scripts/extract_news.py and scripts/mil_features.py to have run.

    .venv/Scripts/python.exe scripts/mil_study.py [--seeds 0 1 2 3 4]
"""
import argparse
import json
import os
import sys
import time

import torch  # noqa: E402  (before sklearn on this machine)
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "data", "external")
PRICES = os.path.join(ROOT, "experiments", "data_snapshot", "mil")
OUT = os.path.join(ROOT, "experiments", "mil_study")
TICKERS = ["AAPL", "AMZN", "FDX", "MSFT", "NVDA", "ORCL", "TSLA"]
WINDOW, KMAX, PCA_DIM = 20, 24, 64
NEWS_ERA = pd.Timestamp("2022-01-01")
# (validation start, test start, test end exclusive)
FOLDS = [("2023-02-01", "2023-04-01", "2023-07-01"), ("2023-05-01", "2023-07-01", "2023-10-01"), ("2023-08-01", "2023-10-01", "2024-01-01")]
torch.set_num_threads(4)


# ------------------------------------------------------------------------------------------------ data
def build():
    inst = pd.read_parquet(os.path.join(EXT, "mil_instances.parquet"))
    inst = inst[inst.ticker.isin(TICKERS)]
    feats = np.load(os.path.join(EXT, "mil_features.npy")).astype(np.float32)
    groups = {k: v.text_id.to_numpy() for k, v in inst.groupby(["ticker", "day"])}
    seq, lab, date, tick, bags = [], [], [], [], []
    for T in TICKERS:
        px = pd.read_csv(os.path.join(PRICES, f"{T}.csv"), index_col=0, parse_dates=True)
        c = px.Close.to_numpy(float)
        r = np.diff(np.log(c), prepend=np.nan)
        rng = ((px.High - px.Low) / px.Close).to_numpy(float)
        vr = np.log(px.Volume / px.Volume.rolling(20).mean()).to_numpy(float)
        f = np.stack([r, rng, vr], 1)
        for i in range(WINDOW + 20, len(px) - 1):
            w = f[i - WINDOW + 1:i + 1]
            if not np.isfinite(w).all():
                continue
            seq.append(w)
            lab.append(float(c[i + 1] > c[i]))
            d = px.index[i]
            date.append(d)
            tick.append(T)
            bags.append(groups.get((T, d), np.zeros(0, np.int64)))
    seq = np.array(seq, np.float32)
    meta = pd.DataFrame({"ticker": tick, "date": pd.to_datetime(date), "y": lab, "n_news": [len(b) for b in bags]})
    return seq, meta, bags, feats, inst


def instance_matrix(feats, bags, fit_mask):
    """67-d instance vector: 3 FinBERT-tone probabilities + PCA(64) of the [CLS] vector (PCA fitted on the fold's training headlines only)."""
    ids = np.unique(np.concatenate([b for b, m in zip(bags, fit_mask) if m and len(b)]))
    pca = PCA(PCA_DIM, random_state=0).fit(feats[ids, 3:])
    z = pca.transform(feats[:, 3:])
    z = z / (z[ids].std(0, keepdims=True) + 1e-6)
    return np.concatenate([feats[:, :3], z], 1).astype(np.float32), float(pca.explained_variance_ratio_.sum())


def pad_bags(bags):
    idx = -np.ones((len(bags), KMAX), np.int64)
    for i, b in enumerate(bags):
        b = b[:KMAX]
        idx[i, :len(b)] = b
    return idx


# ------------------------------------------------------------------------------------------------ models
class Net(nn.Module):
    def __init__(self, mode, d_inst=3 + PCA_DIM, h=32):
        super().__init__()
        self.mode = mode
        self.use_price = mode != "news_attn"
        hp = h if self.use_price else 0
        if self.use_price:
            self.lstm = nn.LSTM(3, h, batch_first=True)
        hb = 0
        if mode in ("mean", "max", "attn", "news_attn"):
            self.enc = nn.Sequential(nn.Linear(d_inst, h), nn.ReLU(), nn.Dropout(0.3))
            self.empty = nn.Parameter(torch.zeros(h))
            hb = h
            if mode in ("attn", "news_attn"):
                self.av, self.au, self.aw = nn.Linear(h, 16), nn.Linear(h, 16), nn.Linear(16, 1)
        elif mode == "flat":
            self.flat = nn.Sequential(nn.Linear(4, 8), nn.ReLU())
            hb = 8
        self.head = nn.Sequential(nn.Linear(hp + hb, 16), nn.ReLU(), nn.Dropout(0.3), nn.Linear(16, 1))

    def forward(self, x, idx, ins, return_att=False):
        parts, att = [], None
        if self.use_price:
            parts.append(self.lstm(x)[0][:, -1])
        if self.mode in ("mean", "max", "attn", "news_attn", "flat"):
            mask = (idx >= 0)
            raw = ins[idx.clamp(min=0)] * mask.unsqueeze(-1)
            cnt = mask.sum(1, keepdim=True).float()
            if self.mode == "flat":
                pos, neg = raw[..., 0], raw[..., 2]
                den = cnt.clamp(min=1).squeeze(1)
                f = torch.stack([(pos - neg).sum(1) / den, pos.sum(1) / den, neg.sum(1) / den, torch.log1p(cnt.squeeze(1))], 1)
                parts.append(self.flat(f))
            else:
                e = self.enc(raw)
                if self.mode == "mean":
                    bag = (e * mask.unsqueeze(-1)).sum(1) / cnt.clamp(min=1)
                elif self.mode == "max":
                    bag = e.masked_fill(~mask.unsqueeze(-1), -1e4).max(1).values
                    bag = torch.where(cnt > 0, bag, torch.zeros_like(bag))
                else:
                    a = self.aw(torch.tanh(self.av(e)) * torch.sigmoid(self.au(e))).squeeze(-1)
                    a = a.masked_fill(~mask, -1e4)
                    att = torch.softmax(a, 1) * mask
                    bag = (att.unsqueeze(-1) * e).sum(1)
                bag = torch.where(cnt > 0, bag, self.empty.expand_as(bag))
                parts.append(bag)
        out = self.head(torch.cat(parts, 1)).squeeze(-1)
        return (out, att) if return_att else out


def fit_predict(mode, seed, seq, y, idx, ins, tr, va, te, tick_arr, shuffle_bags=False):
    torch.manual_seed(seed)
    np.random.seed(seed)
    if shuffle_bags:          # placebo: each day gets the bag of another random day of the same ticker (same split part)
        rng = np.random.default_rng(1000 + seed)
        idx = idx.copy()
        for T in TICKERS:
            for m in (tr, va, te):
                sel = np.where(m & (tick_arr == T))[0]
                idx[sel] = idx[rng.permutation(sel)]
    X, Y, I, INS = torch.tensor(seq), torch.tensor(y, dtype=torch.float32), torch.tensor(idx), torch.tensor(ins)
    net = Net(mode)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-3)
    lossf = nn.BCEWithLogitsLoss()
    tr_i, va_i, te_i = (torch.tensor(np.where(m)[0]) for m in (tr, va, te))
    best, best_state, bad = 1e9, None, 0
    for ep in range(60):
        net.train()
        perm = tr_i[torch.randperm(len(tr_i))]
        for b in range(0, len(perm), 128):
            j = perm[b:b + 128]
            opt.zero_grad()
            loss = lossf(net(X[j], I[j], INS), Y[j])
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
        net.eval()
        with torch.no_grad():
            vl = lossf(net(X[va_i], I[va_i], INS), Y[va_i]).item()
        if vl < best - 1e-4:
            best, bad = vl, 0
            best_state = {k: v.clone() for k, v in net.state_dict().items()}
        else:
            bad += 1
            if bad >= 7:
                break
    net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        p = torch.sigmoid(net(X[te_i], I[te_i], INS)).numpy()
    return p, ep + 1, net


def metrics(y, p, thr=0.5):
    pred = (p >= thr).astype(int)
    pr, rc, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    try:
        auc = float(roc_auc_score(y, p))
    except Exception:
        auc = float("nan")
    return {"accuracy": float(accuracy_score(y, pred)), "precision": float(pr), "recall": float(rc), "f1": float(f1), "auc": auc, "pred_up_share": float(pred.mean())}


def summarise(runs):
    return {k: {"mean": float(np.nanmean([r[k] for r in runs])), "std": float(np.nanstd([r[k] for r in runs]))} for k in runs[0]}


MODES = [("lstm_price", "price", False, True), ("lstm_price_full_history", "price", False, False), ("lstm_flat_sentiment", "flat", False, True),
         ("lstm_mil_mean", "mean", False, True), ("lstm_mil_max", "max", False, True), ("lstm_mil_attention", "attn", False, True),
         ("mil_attention_news_only", "news_attn", False, True), ("placebo_mil_attention_shuffled_bags", "attn", True, True)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2, 3, 4])
    a = ap.parse_args()
    t0 = time.time()
    seq, meta, bags, feats, inst = build()
    y_all = meta.y.to_numpy()
    date = meta.date
    tick_arr = meta.ticker.to_numpy()
    n_news = meta.n_news.to_numpy()
    in_era = (date >= NEWS_ERA).to_numpy()
    # standardise the price features with statistics of the pre-2022 history
    hist = (date < NEWS_ERA).to_numpy()
    mu, sd = seq[hist].reshape(-1, 3).mean(0), seq[hist].reshape(-1, 3).std(0) + 1e-9
    seq = ((seq - mu) / sd).clip(-6, 6).astype(np.float32)
    idx = pad_bags(bags)

    test_all = np.zeros(len(meta), bool)
    pooled = {name: [np.zeros(len(meta)) for _ in a.seeds] for name, *_ in MODES}
    pooled_lr = {"logreg_price_C0.01": np.zeros(len(meta)), "logreg_price_C1.0": np.zeros(len(meta))}
    pooled_maj = np.zeros(len(meta))
    folds_out, epochs = [], {name: [] for name, *_ in MODES}
    att_net = None
    for fi, (vs, ts, te_end) in enumerate(FOLDS):
        vs, ts, te_end = pd.Timestamp(vs), pd.Timestamp(ts), pd.Timestamp(te_end)
        va = ((date >= vs) & (date < ts)).to_numpy()
        te = ((date >= ts) & (date < te_end)).to_numpy()
        tr_news = in_era & (date < vs).to_numpy()
        tr_full = (date < vs).to_numpy()
        test_all |= te
        ins, pca_var = instance_matrix(feats, bags, tr_news)
        folds_out.append({"val": [str(vs.date()), str(ts.date())], "test": [str(ts.date()), str(te_end.date())], "n_train_news_era": int(tr_news.sum()), "n_train_full_history": int(tr_full.sum()),
                          "n_val": int(va.sum()), "n_test": int(te.sum()), "pca_explained_variance": pca_var,
                          "train_up_share": float(y_all[tr_news].mean()), "test_up_share": float(y_all[te].mean())})
        pooled_maj[te] = float(round(y_all[tr_news].mean()))
        Xf = seq.reshape(len(seq), -1)
        for C in (0.01, 1.0):
            lr = LogisticRegression(C=C, max_iter=500).fit(Xf[tr_news], y_all[tr_news])
            pooled_lr[f"logreg_price_C{C}"][te] = lr.predict_proba(Xf[te])[:, 1]
        for name, mode, shuf, news_only_train in MODES:
            tr = tr_news if news_only_train else tr_full
            for si, s in enumerate(a.seeds):
                p, ep, net = fit_predict(mode, s, seq, y_all, idx, ins, tr, va, te, tick_arr, shuffle_bags=shuf)
                pooled[name][si][te] = p
                epochs[name].append(ep)
                if name == "lstm_mil_attention" and fi == len(FOLDS) - 1 and si == 0:
                    att_net, att_ins = net, ins
            print(f"[{time.time() - t0:5.0f}s] fold {fi + 1} {name}", flush=True)

    yte = y_all[test_all]
    has_news = n_news[test_all] > 0
    out = {"n_samples": int(len(meta)), "tickers": TICKERS, "folds": folds_out, "seeds": a.seeds, "n_test_pooled": int(test_all.sum()), "up_share_test": float(yte.mean()),
           "instances": {"n_headline_rows_used": int(len(inst)), "n_unique_in_features": int(len(feats)), "pca_dim": PCA_DIM,
                         "per_ticker": inst.groupby("ticker").size().to_dict(), "per_year": {str(k): int(v) for k, v in inst.groupby(inst.day.dt.year).size().items()},
                         "day_level_share": float(inst.day_level.mean()), "mean_headline_chars": float(inst.headline.str.len().mean())},
           "bags": {"share_days_with_news_news_era": float((n_news[in_era] > 0).mean()), "share_days_with_news_test": float(has_news.mean()),
                    "mean_size_nonempty_test": float(n_news[test_all][has_news].mean()), "median_size_nonempty_test": float(np.median(n_news[test_all][has_news])),
                    "p95_size_test": float(np.percentile(n_news[test_all][has_news], 95)), "max_size": int(n_news.max()), "capped_at": KMAX,
                    "share_days_with_news_per_ticker_test": {T: float((n_news[test_all & (tick_arr == T)] > 0).mean()) for T in TICKERS}},
           "models": {}, "models_news_days": {}}
    out["models"]["majority_class"] = {"runs": [metrics(yte, pooled_maj[test_all])]}
    out["models"]["majority_class"]["summary"] = summarise(out["models"]["majority_class"]["runs"])
    for k, v in pooled_lr.items():
        out["models"][k] = {"runs": [metrics(yte, v[test_all])]}
        out["models"][k]["summary"] = summarise(out["models"][k]["runs"])
    for name, *_ in MODES:
        runs = [metrics(yte, p[test_all]) for p in pooled[name]]
        out["models"][name] = {"runs": runs, "summary": summarise(runs), "epochs_mean": float(np.mean(epochs[name]))}
        out["models_news_days"][name] = summarise([metrics(yte[has_news], p[test_all][has_news]) for p in pooled[name]])
        print(f"{name:38s} acc {out['models'][name]['summary']['accuracy']['mean']:.4f}  f1 {out['models'][name]['summary']['f1']['mean']:.4f}  auc {out['models'][name]['summary']['auc']['mean']:.4f}", flush=True)

    # paired bootstrap on seed-averaged probabilities
    rng = np.random.default_rng(0)
    avg = {name: np.mean([p[test_all] for p in pooled[name]], 0) for name, *_ in MODES}
    base = (avg["lstm_price"] >= 0.5).astype(int) == yte
    out["paired_vs_lstm_price"] = {}
    for name in avg:
        if name == "lstm_price":
            continue
        cur = (avg[name] >= 0.5).astype(int) == yte
        diffs = [cur[j].mean() - base[j].mean() for j in (rng.integers(0, len(yte), len(yte)) for _ in range(2000))]
        out["paired_vs_lstm_price"][name] = {"acc_diff": float(cur.mean() - base.mean()), "ci95": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]}
    cur = (avg["lstm_mil_attention"] >= 0.5).astype(int) == yte
    accs = [cur[j].mean() for j in (rng.integers(0, len(yte), len(yte)) for _ in range(2000))]
    out["mil_attention_seed_avg_accuracy"] = float(cur.mean())
    out["mil_attention_accuracy_ci95"] = [float(np.percentile(accs, 2.5)), float(np.percentile(accs, 97.5))]
    out["always_up_accuracy_test"] = float(yte.mean())
    t_te = tick_arr[test_all]
    out["per_ticker_test_accuracy"] = {nm: {T: float(((avg[nm] >= 0.5).astype(int) == yte)[t_te == T].mean()) for T in TICKERS} for nm in ("lstm_price", "lstm_mil_attention")}
    out["per_ticker_test_n"] = {T: int((t_te == T).sum()) for T in TICKERS}

    # attention examples (last fold, first seed): what does the gated attention look at?
    ex = []
    if att_net is not None:
        att_net.eval()
        last_te = ((date >= pd.Timestamp(FOLDS[-1][1])) & (date < pd.Timestamp(FOLDS[-1][2]))).to_numpy()
        cand = [i for i in np.where(last_te)[0] if n_news[i] >= 6]
        texts = inst.drop_duplicates("text_id").set_index("text_id").headline
        if cand:
            for i in np.random.default_rng(1).choice(cand, size=min(8, len(cand)), replace=False):
                with torch.no_grad():
                    lo, att = att_net(torch.tensor(seq[i:i + 1]), torch.tensor(idx[i:i + 1]), torch.tensor(att_ins), return_att=True)
                n = int((idx[i] >= 0).sum())
                w = att[0, :n].numpy()
                top = np.argsort(-w)[:3]
                ex.append({"ticker": str(tick_arr[i]), "date": str(date[i].date()), "n_headlines": n, "label_next_day_up": int(y_all[i]), "p_up": float(torch.sigmoid(lo)[0]),
                           "uniform_weight": float(1 / n),
                           "top": [{"weight": float(w[k]), "headline": str(texts.get(idx[i, k], ""))[:150], "p_pos": float(feats[idx[i, k], 0]), "p_neg": float(feats[idx[i, k], 2])} for k in top]})
    out["attention_examples"] = ex
    out["seconds"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8"), indent=1, default=float)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    sys.exit(main())
