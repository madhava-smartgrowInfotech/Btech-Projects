"""
Synthetic UNSW-NB15-like generator for demo mode.
Produces realistic feature distributions for 2 classes (normal vs attack).
Same 42-feature schema so pipeline is identical to real data path.
"""
import numpy as np
import pandas as pd
from .features import FEATURE_NAMES, PROTO_VALUES, SERVICE_VALUES, STATE_VALUES

RNG_SEED = 42

def generate_synthetic(n_normal: int = 5000, n_attack: int = 5000, seed: int = RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    total = n_normal + n_attack
    rows = []

    def gen_row(is_attack: bool):
        r = {}
        # Numeric: attacks tend to have higher rate, sbytes, ct counts, etc.
        if is_attack:
            # Overlap more with normal to get realistic ~96% accuracy, not 100%
            r["dur"] = float(np.clip(rng.exponential(1.8), 0, 60))
            r["spkts"] = int(np.clip(rng.poisson(18) + rng.integers(0, 8), 1, 500))
            r["dpkts"] = int(np.clip(rng.poisson(10), 0, 300))
            r["sbytes"] = int(np.clip(rng.lognormal(7.2, 1.3), 100, 5_000_000))
            r["dbytes"] = int(np.clip(rng.lognormal(6.6, 1.2), 50, 3_000_000))
            r["rate"] = float(np.clip(rng.normal(45000, 25000), 1000, 300000))
            r["sload"] = float(np.clip(rng.normal(220000, 150000), 1000, 2e6))
            r["dload"] = float(np.clip(rng.normal(160000, 120000), 500, 1.5e6))
            r["sloss"] = int(rng.poisson(2))
            r["dloss"] = int(rng.poisson(1))
            r["sinpkt"] = float(np.clip(rng.exponential(45), 0.1, 5000))
            r["dinpkt"] = float(np.clip(rng.exponential(55), 0.1, 5000))
            r["sjit"] = float(np.clip(rng.exponential(18), 0, 1000))
            r["djit"] = float(np.clip(rng.exponential(22), 0, 1000))
            r["ct_srv_src"] = int(np.clip(rng.poisson(6) + 2, 1, 50))
            r["ct_dst_ltm"] = int(np.clip(rng.poisson(5)+2, 1, 50))
            r["ct_src_dport_ltm"] = int(np.clip(rng.poisson(5)+2, 1, 50))
            r["ct_dst_sport_ltm"] = int(np.clip(rng.poisson(4)+2, 1, 50))
            r["ct_dst_src_ltm"] = int(np.clip(rng.poisson(4)+1, 1, 50))
            r["ct_src_ltm"] = int(np.clip(rng.poisson(4)+1, 1, 50))
            r["ct_srv_dst"] = int(np.clip(rng.poisson(5)+2, 1, 50))
        else:
            r["dur"] = float(np.clip(rng.exponential(0.8), 0, 60))
            r["spkts"] = int(np.clip(rng.poisson(8), 1, 500))
            r["dpkts"] = int(np.clip(rng.poisson(6), 0, 300))
            r["sbytes"] = int(np.clip(rng.lognormal(6.3, 1.0), 100, 5_000_000))
            r["dbytes"] = int(np.clip(rng.lognormal(6.0, 1.0), 50, 3_000_000))
            r["rate"] = float(np.clip(rng.normal(18000, 10000), 10, 300000))
            r["sload"] = float(np.clip(rng.normal(90000, 50000), 1000, 2e6))
            r["dload"] = float(np.clip(rng.normal(70000, 40000), 500, 1.5e6))
            r["sloss"] = int(rng.poisson(0.7))
            r["dloss"] = int(rng.poisson(0.5))
            r["sinpkt"] = float(np.clip(rng.exponential(70), 0.1, 5000))
            r["dinpkt"] = float(np.clip(rng.exponential(80), 0.1, 5000))
            r["sjit"] = float(np.clip(rng.exponential(10), 0, 1000))
            r["djit"] = float(np.clip(rng.exponential(12), 0, 1000))
            r["ct_srv_src"] = int(np.clip(rng.poisson(2), 1, 50))
            r["ct_dst_ltm"] = int(np.clip(rng.poisson(2), 1, 50))
            r["ct_src_dport_ltm"] = int(np.clip(rng.poisson(2), 1, 50))
            r["ct_dst_sport_ltm"] = int(np.clip(rng.poisson(1), 1, 50))
            r["ct_dst_src_ltm"] = int(np.clip(rng.poisson(1), 1, 50))
            r["ct_src_ltm"] = int(np.clip(rng.poisson(2), 1, 50))
            r["ct_srv_dst"] = int(np.clip(rng.poisson(2), 1, 50))

        # Remaining numeric features: generic but distinct
        r["sttl"] = int(rng.integers(30, 255) if is_attack else rng.integers(40, 255))
        r["dttl"] = int(rng.integers(20, 255))
        r["swin"] = int(rng.integers(0, 65535))
        r["stcpb"] = int(rng.integers(0, 2_000_000_000))
        r["dtcpb"] = int(rng.integers(0, 2_000_000_000))
        r["dwin"] = int(rng.integers(0, 65535))
        r["tcprtt"] = float(np.clip(rng.exponential(0.05 if not is_attack else 0.2), 0, 5))
        r["synack"] = float(np.clip(rng.exponential(0.02 if not is_attack else 0.08), 0, 2))
        r["ackdat"] = float(np.clip(rng.exponential(0.03 if not is_attack else 0.1), 0, 2))
        r["smean"] = int(np.clip(r["sbytes"] / max(r["spkts"], 1) + rng.normal(0, 50), 50, 1500))
        r["dmean"] = int(np.clip(r["dbytes"] / max(r["dpkts"], 1) + rng.normal(0, 50), 50, 1500))
        r["trans_depth"] = int(np.clip(rng.poisson(1 if not is_attack else 2), 0, 20))
        r["response_body_len"] = int(np.clip(rng.poisson(200 if not is_attack else 800), 0, 50000))
        r["is_ftp_login"] = int(rng.choice([0, 1], p=[0.95, 0.05] if not is_attack else [0.85, 0.15]))
        r["ct_ftp_cmd"] = int(np.clip(rng.poisson(0 if not is_attack else 1), 0, 10))
        r["ct_flw_http_mthd"] = int(np.clip(rng.poisson(1 if not is_attack else 2), 0, 20))
        r["is_sm_ips_ports"] = int(rng.choice([0, 1], p=[0.97, 0.03] if not is_attack else [0.9, 0.1]))

        # Categoricals (STATE has 12 values)
        if is_attack:
            r["proto"] = str(rng.choice(PROTO_VALUES, p=[0.55, 0.25, 0.08, 0.04, 0.04, 0.04]))
            r["service"] = str(rng.choice(SERVICE_VALUES))
            r["state"] = str(rng.choice(STATE_VALUES, p=[0.15, 0.2, 0.1, 0.1, 0.15, 0.05, 0.05, 0.05, 0.03, 0.05, 0.05, 0.02]))
        else:
            r["proto"] = str(rng.choice(PROTO_VALUES, p=[0.65, 0.25, 0.02, 0.02, 0.03, 0.03]))
            r["service"] = str(rng.choice(SERVICE_VALUES, p=[0.15, 0.35, 0.05, 0.05, 0.05, 0.1, 0.02, 0.05, 0.03, 0.05, 0.03, 0.03, 0.04]))
            r["state"] = str(rng.choice(STATE_VALUES, p=[0.25, 0.05, 0.3, 0.05, 0.02, 0.01, 0.05, 0.1, 0.02, 0.08, 0.05, 0.02]))

        # Fill any missing FEATURE_NAMES with defaults
        for f in FEATURE_NAMES:
            if f not in r:
                r[f] = 0
        return r

    data = []
    for _ in range(n_normal):
        row = gen_row(False)
        row["label"] = 0
        row["attack_cat"] = "Normal"
        row["id"] = len(data) + 1
        data.append(row)
    for _ in range(n_attack):
        row = gen_row(True)
        row["label"] = 1
        row["attack_cat"] = str(np.random.choice(["Generic", "Exploits", "Fuzzers", "DoS", "Reconnaissance", "Analysis", "Backdoor", "Shellcode", "Worms"]))
        row["id"] = len(data) + 1
        data.append(row)

    df = pd.DataFrame(data)
    # Inject 2.5% label noise to avoid perfect separability (realistic)
    n_flip = int(len(df) * 0.025)
    flip_idx = rng.choice(len(df), size=n_flip, replace=False)
    for idx in flip_idx:
        df.iloc[idx, df.columns.get_loc("label")] = 1 - df.iloc[idx]["label"]
        df.iloc[idx, df.columns.get_loc("attack_cat")] = "Normal" if df.iloc[idx]["label"] == 0 else "Generic"
    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    # Order columns
    from .features import ALL_COLUMNS
    df = df[ALL_COLUMNS]
    return df
