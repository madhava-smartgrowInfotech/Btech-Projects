"""F1 graph builder + F2 node features.

Real parts
  * topology      - the ego-network social graph (SNAP Facebook circles: ten ego networks merged, ~3,960 accounts, ~88k ties)
  * profile rows  - labelled genuine / fake profile attributes (Instagram fake-account dataset)
  * posting rows  - retweet / mention / tweet-length / hashtag / account-age rows (Twitter bot dataset)

Synthetic parts (seeded, documented in docs/02_HOW_IT_WORKS.md)
  * injected botnets - coordinated bot accounts added to the real topology, so cluster detection
    can be measured against known ground truth
  * temporal + interaction features, handles and display names
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C

REF_DATE = pd.Timestamp("2024-01-01")

PROFILE_FEATURES = [
    "has_profile_pic", "username_digit_ratio", "fullname_words", "fullname_digit_ratio",
    "name_equals_username", "bio_length", "has_external_url", "is_private",
    "log_posts", "log_followers", "log_following", "follower_following_ratio",
]
POSTING_FEATURES = ["log_avg_retweets", "avg_mentions", "avg_post_length", "hashtags_per_post"]
TEMPORAL_FEATURES = [
    "log_account_age_days", "log_posts_per_day", "posting_burstiness",
    "peak_hour_share", "peak_hour_sin", "peak_hour_cos",
]
INTERACTION_FEATURES = ["log_interactions_per_week"]
FEATURES = PROFILE_FEATURES + POSTING_FEATURES + TEMPORAL_FEATURES + INTERACTION_FEATURES

FEATURE_GROUPS = {f: "Profile metadata" for f in PROFILE_FEATURES}
FEATURE_GROUPS.update({f: "Posting behaviour" for f in POSTING_FEATURES})
FEATURE_GROUPS.update({f: "Temporal pattern" for f in TEMPORAL_FEATURES})
FEATURE_GROUPS.update({f: "Interaction frequency" for f in INTERACTION_FEATURES})

FEATURE_LABELS = {
    "has_profile_pic": "Has profile picture",
    "username_digit_ratio": "Digits in username",
    "fullname_words": "Words in display name",
    "fullname_digit_ratio": "Digits in display name",
    "name_equals_username": "Name equals username",
    "bio_length": "Bio length",
    "has_external_url": "Has external link",
    "is_private": "Private account",
    "log_posts": "Posts (log)",
    "log_followers": "Followers (log)",
    "log_following": "Following (log)",
    "follower_following_ratio": "Follower / following ratio",
    "log_avg_retweets": "Avg retweets (log)",
    "avg_mentions": "Avg mentions per post",
    "avg_post_length": "Avg post length",
    "hashtags_per_post": "Hashtags per post",
    "log_account_age_days": "Account age (log days)",
    "log_posts_per_day": "Posts per day (log)",
    "posting_burstiness": "Posting burstiness",
    "peak_hour_share": "Share of activity in peak hour",
    "peak_hour_sin": "Peak hour (sin)",
    "peak_hour_cos": "Peak hour (cos)",
    "log_interactions_per_week": "Interactions per week (log)",
}

_WORDS = [
    "river", "stone", "maple", "cloud", "ember", "harbor", "willow", "falcon", "meadow", "lotus", "amber",
    "cedar", "ripple", "sunny", "coral", "breeze", "pixel", "orchid", "monsoon", "spice", "saffron", "indigo",
    "jasmine", "lantern", "marigold", "pebble", "quartz", "raven", "sparrow", "tulip", "velvet", "zephyr",
    "aurora", "banyan", "chai", "dune", "echo", "fern", "glow", "haze", "iris", "juniper", "kite", "lime",
    "mango", "nova", "olive", "peony", "quill", "reef", "sage", "thistle", "umber", "violet", "wren", "yarrow",
]


# --------------------------------------------------------------------------- raw loading
def load_facebook() -> tuple[int, np.ndarray]:
    """Union of the ego networks (ego -> every alter plus the alter-alter ties)."""
    pairs = []
    for f in sorted((C.RAW / "facebook").glob("*.edges")):
        ego = int(f.stem)
        arr = np.loadtxt(f, dtype=np.int64, ndmin=2)
        pairs.append(arr)
        alters = np.unique(arr)
        pairs.append(np.stack([np.full_like(alters, ego), alters], axis=1))
    e = np.concatenate(pairs)
    e = e[e[:, 0] != e[:, 1]]
    e = np.sort(e, axis=1)
    e = np.unique(e, axis=0)
    ids = np.unique(e)
    remap = {int(v): i for i, v in enumerate(ids)}
    mapped = np.vectorize(remap.get)(e)
    return len(ids), mapped.astype(np.int64)


def load_instagram() -> pd.DataFrame:
    df = pd.concat([pd.read_csv(C.RAW / "instagram_train.csv"), pd.read_csv(C.RAW / "instagram_test.csv")], ignore_index=True)
    df = df.rename(columns={
        "profile pic": "pic", "nums/length username": "user_dig", "fullname words": "name_words",
        "nums/length fullname": "name_dig", "name==username": "name_eq", "description length": "bio",
        "external URL": "url", "private": "private", "#posts": "posts", "#followers": "followers",
        "#follows": "follows", "fake": "fake",
    })
    return df


def load_twitter() -> pd.DataFrame:
    df = pd.read_csv(C.RAW / "twitter_bot_detection.csv")
    created = pd.to_datetime(df["Created At"], errors="coerce")
    out = pd.DataFrame({
        "retweets": df["Retweet Count"].astype(float),
        "mentions": df["Mention Count"].astype(float),
        "post_len": df["Tweet"].fillna("").str.len().astype(float),
        "hashtags": df["Hashtags"].fillna("").map(lambda s: len(str(s).split()) if str(s).strip() else 0).astype(float),
        "age_days": (REF_DATE - created).dt.days.clip(lower=5).astype(float),
    })
    return out.dropna().reset_index(drop=True)


# --------------------------------------------------------------------------- feature sampling
def _profile_rows(pool: pd.DataFrame, n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Resample real labelled profile rows and jitter them so no two accounts are identical."""
    rows = pool.sample(n=n, replace=True, random_state=int(rng.integers(1 << 30))).reset_index(drop=True)
    for c in ["posts", "followers", "follows"]:
        rows[c] = np.round(rows[c] * rng.lognormal(0, 0.35, n))
    rows["bio"] = np.clip(np.round(rows["bio"] + rng.normal(0, 4, n)), 0, 150)
    for c in ["user_dig", "name_dig"]:
        rows[c] = np.clip(rows[c] + rng.normal(0, 0.02, n), 0, 1)
    for c in ["pic", "url", "private", "name_eq"]:
        flip = rng.random(n) < 0.03
        rows.loc[flip, c] = 1 - rows.loc[flip, c]
    return rows


def _temporal(n: int, bot_like: np.ndarray, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Per-account temporal / interaction traits. bot_like selects the bot-leaning generator."""
    b = bot_like
    ppd = np.where(b, rng.lognormal(np.log(2.2), 0.9, n), rng.lognormal(np.log(0.8), 0.8, n))
    burst = np.where(b, rng.beta(4, 3, n), rng.beta(2, 5, n))
    share = np.where(b, rng.beta(6, 12, n), rng.beta(3, 20, n))
    inter = np.where(b, rng.lognormal(np.log(70), 0.9, n), rng.lognormal(np.log(25), 0.9, n))
    return {"ppd": ppd, "burst": burst, "share": share, "inter": inter}


def _handle(rng: np.random.Generator, digit_ratio: float, same_as_name: bool, fullname: str) -> str:
    if same_as_name:
        return fullname.lower().replace(" ", "")
    base = f"{rng.choice(_WORDS)}{rng.choice(['_', '.', ''])}{rng.choice(_WORDS)}"
    n_dig = int(round(digit_ratio * (len(base) / max(1e-6, 1 - digit_ratio))))
    n_dig = min(max(n_dig, 0), 8)
    return base + "".join(str(rng.integers(0, 10)) for _ in range(n_dig))


# --------------------------------------------------------------------------- the build
def build(seed: int = C.SEED) -> dict:
    rng = np.random.default_rng(seed)
    n_real, real_edges = load_facebook()
    ig, tw = load_instagram(), load_twitter()
    genuine, fake = ig[ig["fake"] == 0], ig[ig["fake"] == 1]

    # ---- node roster ------------------------------------------------------------------
    sizes = rng.integers(C.CLUSTER_SIZE[0], C.CLUSTER_SIZE[1] + 1, C.N_CLUSTERS)
    n_cluster_bots = int(sizes.sum())
    n_total = n_real + n_cluster_bots + C.N_LONE_BOTS
    y = np.zeros(n_total, dtype=np.int64)
    cluster = np.full(n_total, -1, dtype=np.int64)
    is_real = np.zeros(n_total, dtype=bool)
    is_real[:n_real] = True
    start = n_real
    for k, s in enumerate(sizes):
        cluster[start:start + s] = k
        y[start:start + s] = 1
        start += s
    y[start:] = 1  # lone spammers

    # ---- which accounts look like what ---------------------------------------------------
    camouflage = np.zeros(n_total, dtype=bool)           # bots with a genuine-looking profile
    camouflage[n_real:n_real + n_cluster_bots] = rng.random(n_cluster_bots) < 0.40
    camouflage[n_real + n_cluster_bots:] = rng.random(C.N_LONE_BOTS) < 0.25
    suspicious_human = np.zeros(n_total, dtype=bool)     # genuine accounts that look fake-ish
    suspicious_human[:n_real] = rng.random(n_real) < 0.06

    use_fake_profile = ((y == 1) & ~camouflage) | suspicious_human
    prof = pd.concat([_profile_rows(fake, int(use_fake_profile.sum()), rng).assign(_i=np.where(use_fake_profile)[0]),
                      _profile_rows(genuine, int((~use_fake_profile).sum()), rng).assign(_i=np.where(~use_fake_profile)[0])])
    prof = prof.sort_values("_i").reset_index(drop=True)

    post = tw.sample(n=n_total, replace=True, random_state=int(rng.integers(1 << 30))).reset_index(drop=True)

    bot_like = (y == 1) & ~camouflage
    t = _temporal(n_total, bot_like, rng)

    # coordination: clusters share a creation window and a peak hour
    peak_hour = np.clip(np.round(rng.normal(20.5, 3.5, n_total)), 0, 47) % 24
    peak_hour[(y == 1) & (cluster < 0)] = rng.integers(0, 24, C.N_LONE_BOTS)
    cluster_hour = rng.integers(0, 24, C.N_CLUSTERS)
    cluster_date = rng.integers(60, 330, C.N_CLUSTERS)   # days after 2023-01-01
    age_days = post["age_days"].to_numpy().copy()
    for k in range(C.N_CLUSTERS):
        m = cluster == k
        peak_hour[m] = (cluster_hour[k] + rng.integers(-1, 2, m.sum())) % 24
        created = cluster_date[k] + rng.normal(0, 6, m.sum())
        age_days[m] = np.clip((REF_DATE - pd.Timestamp("2023-01-01")).days - created, 5, None)

    followers, follows = prof["followers"].to_numpy(), prof["follows"].to_numpy()
    X = np.column_stack([
        prof["pic"], prof["user_dig"], prof["name_words"], prof["name_dig"], prof["name_eq"], prof["bio"],
        prof["url"], prof["private"], np.log1p(prof["posts"]), np.log1p(followers), np.log1p(follows),
        np.log1p(followers / np.maximum(follows, 1)),
        np.log1p(post["retweets"]), post["mentions"], post["post_len"], post["hashtags"],
        np.log(age_days), np.log(t["ppd"]), t["burst"], t["share"],
        np.sin(2 * np.pi * peak_hour / 24), np.cos(2 * np.pi * peak_hour / 24),
        np.log1p(t["inter"]),
    ]).astype(np.float32)
    assert X.shape[1] == len(FEATURES)

    # ---- edges -------------------------------------------------------------------------------------
    edges = [real_edges]
    kinds = [np.zeros(len(real_edges), dtype=np.int8)]
    deg = np.bincount(real_edges.ravel(), minlength=n_real).astype(float)
    pick_p = deg ** 0.5 / (deg ** 0.5).sum()

    def add(pairs):
        pairs = np.sort(np.asarray(pairs, dtype=np.int64).reshape(-1, 2), axis=1)
        pairs = pairs[pairs[:, 0] != pairs[:, 1]]
        edges.append(pairs)
        kinds.append(np.ones(len(pairs), dtype=np.int8))

    for k in range(C.N_CLUSTERS):
        members = np.where(cluster == k)[0]
        m = len(members)
        iu = np.triu_indices(m, 1)
        keep = rng.random(len(iu[0])) < 0.28                      # coordinated mutual follows / likes
        add(np.stack([members[iu[0][keep]], members[iu[1][keep]]], axis=1))
        add(np.stack([members, np.roll(members, 1)], axis=1))     # a ring so every cluster is connected
        for b in members:                                         # follow-spam towards real accounts
            tg = rng.choice(n_real, size=int(rng.integers(2, 8)), replace=False, p=pick_p)
            add(np.stack([np.full(len(tg), b), tg], axis=1))
    for a in range(C.N_CLUSTERS):                                 # a few ties between botnets
        for b in range(a + 1, C.N_CLUSTERS):
            if rng.random() < 0.35:
                add([[rng.choice(np.where(cluster == a)[0]), rng.choice(np.where(cluster == b)[0])]])
    lone = np.where((y == 1) & (cluster < 0))[0]
    for b in lone:
        tg = rng.choice(n_real, size=int(rng.integers(3, 11)), replace=False, p=pick_p)
        add(np.stack([np.full(len(tg), b), tg], axis=1))
    edge_index = np.concatenate(edges)
    edge_kind = np.concatenate(kinds)
    order = np.lexsort((edge_index[:, 1], edge_index[:, 0]))
    edge_index, edge_kind = edge_index[order], edge_kind[order]
    _, uniq = np.unique(edge_index, axis=0, return_index=True)
    edge_index, edge_kind = edge_index[uniq], edge_kind[uniq]

    # ---- stratified split ----------------------------------------------------------------------------
    split = np.zeros(n_total, dtype=np.int8)
    for cls in (0, 1):
        idx = rng.permutation(np.where(y == cls)[0])
        n_tr, n_va = int(0.6 * len(idx)), int(0.2 * len(idx))
        split[idx[n_tr:n_tr + n_va]] = 1
        split[idx[n_tr + n_va:]] = 2

    # ---- account roster (display attributes) ---------------------------------------------------------
    handles, names = [], []
    for i in range(n_total):
        full = " ".join(w.capitalize() for w in rng.choice(_WORDS, size=max(1, int(prof["name_words"].iloc[i])), replace=False))
        names.append(full)
        handles.append(_handle(rng, float(prof["user_dig"].iloc[i]), bool(prof["name_eq"].iloc[i]), full))
    seen: dict[str, int] = {}
    for i, h in enumerate(handles):          # keep handles unique
        seen[h] = seen.get(h, 0) + 1
        if seen[h] > 1:
            handles[i] = f"{h}{seen[h]}"
    accounts = pd.DataFrame({
        "id": np.arange(n_total), "handle": handles, "display_name": names,
        "label": y, "origin": np.where(is_real, "real topology", "injected"),
        "botnet_truth": cluster, "split": np.array(["train", "val", "test"])[split],
        "followers": followers.astype(int), "following": follows.astype(int), "posts": prof["posts"].astype(int),
        "bio_length": prof["bio"].astype(int), "has_profile_pic": prof["pic"].astype(int),
        "account_age_days": age_days.astype(int), "peak_hour": peak_hour.astype(int),
        "posts_per_day": np.round(t["ppd"], 2), "interactions_per_week": np.round(t["inter"], 1),
    })

    return {
        "X": X, "y": y, "edge_index": edge_index, "edge_kind": edge_kind, "cluster": cluster,
        "is_real": is_real, "split": split, "accounts": accounts,
        "meta": {
            "seed": seed, "n_real_nodes": int(n_real), "n_injected_nodes": int(n_total - n_real),
            "n_real_edges": int((edge_kind == 0).sum()), "n_injected_edges": int((edge_kind == 1).sum()),
            "botnet_sizes": [int(s) for s in sizes], "n_lone_bots": C.N_LONE_BOTS,
            "camouflaged_bots": int(camouflage.sum()), "suspicious_genuine": int(suspicious_human.sum()),
        },
    }


def save(g: dict) -> None:
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        C.PROCESSED / "graph.npz", X=g["X"], y=g["y"], edge_index=g["edge_index"], edge_kind=g["edge_kind"],
        cluster=g["cluster"], is_real=g["is_real"], split=g["split"], features=np.array(FEATURES),
    )
    g["accounts"].to_csv(C.PROCESSED / "accounts.csv", index=False)
    (C.PROCESSED / "graph_meta.json").write_text(json.dumps(g["meta"], indent=2))


def load() -> dict:
    z = np.load(C.PROCESSED / "graph.npz", allow_pickle=False)
    g = {k: z[k] for k in z.files if k != "features"}
    g["accounts"] = pd.read_csv(C.PROCESSED / "accounts.csv")
    g["meta"] = json.loads((C.PROCESSED / "graph_meta.json").read_text())
    return g


def summary(g: dict) -> dict:
    """Counts + feature summary shown by 'build the graph'."""
    X, y, ei, ek = g["X"], g["y"], g["edge_index"], g["edge_kind"]
    n = len(y)
    deg = np.bincount(ei.ravel(), minlength=n)
    feats = []
    for j, f in enumerate(FEATURES):
        col = X[:, j]
        feats.append({
            "name": f, "label": FEATURE_LABELS[f], "group": FEATURE_GROUPS[f],
            "mean_genuine": float(col[y == 0].mean()), "mean_fake": float(col[y == 1].mean()),
            "std": float(col.std()),
        })
    return {
        "nodes": int(n), "edges": int(len(ei)),
        "real_nodes": int(g["is_real"].sum()), "injected_nodes": int((~g["is_real"]).sum()),
        "real_edges": int((ek == 0).sum()), "injected_edges": int((ek == 1).sum()),
        "fake_accounts": int(y.sum()), "genuine_accounts": int((y == 0).sum()),
        "fake_share": float(y.mean()),
        "avg_degree": float(deg.mean()), "max_degree": int(deg.max()),
        "n_features": len(FEATURES), "features": feats,
        "split": {k: int((g["split"] == i).sum()) for i, k in enumerate(["train", "val", "test"])},
        "botnets_injected": int(g["cluster"].max() + 1),
        "meta": g["meta"],
    }


if __name__ == "__main__":
    graph = build()
    save(graph)
    print(json.dumps({k: v for k, v in summary(graph).items() if k != "features"}, indent=2))
