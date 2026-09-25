"""Uses the trained cEmoGAN generator to synthesize compound-emotion faces: for each
of the 11 compound classes, the condition vector activates both contributing basic
emotions (sum-normalized, matching the one-hot norm the generator was trained on).
"""
import numpy as np
import torch

from app.config import CHECKPOINT_DIR
from app.ml.gan_model import ConditionalGenerator, NOISE_DIM
from app.ml.taxonomy import BASIC_INDEX, COMPOUND_COMPONENTS, COMPOUND_EMOTIONS, LABEL_INDEX, NUM_BASIC, NUM_LABELS

DEVICE = torch.device("cpu")


def load_generator() -> ConditionalGenerator:
    g = ConditionalGenerator(cond_dim=NUM_BASIC)
    state = torch.load(CHECKPOINT_DIR / "generator.pt", map_location=DEVICE)
    g.load_state_dict(state)
    g.eval()
    return g


@torch.no_grad()
def synthesize(generator: ConditionalGenerator, n_per_class: int = 200):
    """Returns (images uint8 [N,64,64], multihot_labels float32 [N, NUM_LABELS])."""
    all_images = []
    all_labels = []
    for compound_key in COMPOUND_EMOTIONS:
        a, b = COMPOUND_COMPONENTS[compound_key]
        cond = torch.zeros(n_per_class, NUM_BASIC)
        cond[:, BASIC_INDEX[a]] = 0.5
        cond[:, BASIC_INDEX[b]] = 0.5
        z = torch.randn(n_per_class, NOISE_DIM)
        imgs = generator(z, cond)  # [-1, 1], N x 1 x 64 x 64
        imgs_uint8 = ((imgs.squeeze(1).numpy() * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)

        label_vec = np.zeros(NUM_LABELS, dtype=np.float32)
        label_vec[LABEL_INDEX[a]] = 1.0
        label_vec[LABEL_INDEX[b]] = 1.0
        label_vec[LABEL_INDEX[compound_key]] = 1.0
        labels = np.tile(label_vec, (n_per_class, 1))

        all_images.append(imgs_uint8)
        all_labels.append(labels)

    return np.concatenate(all_images, axis=0), np.concatenate(all_labels, axis=0)
