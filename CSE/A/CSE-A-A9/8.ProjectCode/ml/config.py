"""Shared paths and constants for the BotGraph pipeline."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MODELS = Path(os.environ.get("BOTGRAPH_MODELS_DIR", ROOT / "models"))
EXPERIMENTS = Path(os.environ.get("BOTGRAPH_EXPERIMENTS_DIR", ROOT / "experiments"))

SEED = 7
ARCHS = ["gcn", "gat", "sage"]
BASELINE = "baseline"
ALL_MODELS = [BASELINE] + ARCHS
MODEL_LABELS = {
    "baseline": "Feature-only baseline (MLP)",
    "gcn": "GCN",
    "gat": "GAT",
    "sage": "GraphSAGE",
}

# Training configuration - deliberately small so the whole pipeline runs on a laptop CPU.
HIDDEN = 64
EPOCHS = 160
PATIENCE = 40
LR = 0.01
WEIGHT_DECAY = 5e-4
DROPOUT = 0.3
EVAL_SEEDS = [0, 1, 2]

# Botnet cluster detection
CANDIDATE_PROB = 0.30   # accounts at or above this probability are considered for clustering
KNN = 5                 # neighbours per account in the embedding similarity graph
MIN_CLUSTER = 5

# Synthetic graph (injected botnets)
N_CLUSTERS = 8
CLUSTER_SIZE = (26, 64)
N_LONE_BOTS = 150
