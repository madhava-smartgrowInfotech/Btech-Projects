"""A small JEPA-style self-supervised image encoder.

Joint-Embedding Predictive Architecture: a context encoder sees a masked
view of an image, a predictor tries to reconstruct the *embeddings* of the
masked-out patches as produced by a slower, EMA-updated target encoder.
No pixel reconstruction, no labels — the encoder learns structure from
unlabelled seed imagery alone, which is the point: labelled germination
images are scarce, unlabelled seed photos are not.

Kept deliberately small (a handful of patches, 2-layer transformer) so it
pretrains on CPU in a couple of minutes on a few thousand synthetic images.
"""
import copy
import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

IMAGE_SIZE_DEFAULT = 64
PATCH_SIZE = 8
NUM_PATCHES_SIDE = IMAGE_SIZE_DEFAULT // PATCH_SIZE  # 8
NUM_PATCHES = NUM_PATCHES_SIDE**2  # 64


class PatchEmbed(nn.Module):
    def __init__(self, patch_size: int, embed_dim: int, in_chans: int = 3):
        super().__init__()
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        # x: (B, 3, H, W) -> (B, N, D)
        x = self.proj(x)
        b, d, gh, gw = x.shape
        return x.flatten(2).transpose(1, 2), (gh, gw)


class TransformerTrunk(nn.Module):
    def __init__(self, embed_dim: int, depth: int, heads: int):
        super().__init__()
        layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=heads,
            dim_feedforward=embed_dim * 4,
            dropout=0.0,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=depth)

    def forward(self, x):
        return self.encoder(x)


class PositionalEncoding(nn.Module):
    def __init__(self, num_patches: int, embed_dim: int):
        super().__init__()
        pe = torch.zeros(num_patches, embed_dim)
        position = torch.arange(0, num_patches, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, embed_dim, 2).float() * (-math.log(10000.0) / embed_dim))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term[: pe[:, 1::2].shape[1]])
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, : x.shape[1]]


class ContextEncoder(nn.Module):
    """Patch embedding + small transformer -> per-patch embeddings."""

    def __init__(self, embed_dim: int, depth: int = 2, heads: int = 4, patch_size: int = PATCH_SIZE):
        super().__init__()
        self.patch_embed = PatchEmbed(patch_size, embed_dim)
        self.pos_enc = PositionalEncoding(NUM_PATCHES, embed_dim)
        self.trunk = TransformerTrunk(embed_dim, depth, heads)

    def forward(self, x):
        tokens, _ = self.patch_embed(x)
        tokens = self.pos_enc(tokens)
        return self.trunk(tokens)  # (B, N, D)


class Predictor(nn.Module):
    """Predicts target-encoder embeddings for masked patches from context tokens."""

    def __init__(self, embed_dim: int, depth: int = 1, heads: int = 4):
        super().__init__()
        self.mask_token = nn.Parameter(torch.randn(1, 1, embed_dim) * 0.02)
        self.pos_enc = PositionalEncoding(NUM_PATCHES, embed_dim)
        self.trunk = TransformerTrunk(embed_dim, depth, heads)
        self.head = nn.Linear(embed_dim, embed_dim)

    def forward(self, context_tokens, mask_bool):
        # context_tokens: (B, N, D) with masked positions already zeroed by caller
        b, n, d = context_tokens.shape
        mask_tokens = self.mask_token.expand(b, n, d)
        merged = torch.where(mask_bool.unsqueeze(-1), mask_tokens, context_tokens)
        merged = self.pos_enc(merged)
        out = self.trunk(merged)
        return self.head(out)


class JepaEncoder(nn.Module):
    """Bundles context encoder, EMA target encoder and predictor for pretraining.

    After pretraining only `context_encoder` is used at inference time to
    embed a full (unmasked) image for downstream fusion with tabular data.
    """

    def __init__(self, embed_dim: int = 48, depth: int = 2, heads: int = 4, mask_ratio: float = 0.4):
        super().__init__()
        self.embed_dim = embed_dim
        self.mask_ratio = mask_ratio
        self.context_encoder = ContextEncoder(embed_dim, depth, heads)
        self.target_encoder = copy.deepcopy(self.context_encoder)
        for p in self.target_encoder.parameters():
            p.requires_grad = False
        self.predictor = Predictor(embed_dim, depth=1, heads=heads)

    @torch.no_grad()
    def update_target(self, momentum: float = 0.996):
        for tp, cp in zip(self.target_encoder.parameters(), self.context_encoder.parameters()):
            tp.data.mul_(momentum).add_(cp.data, alpha=1 - momentum)

    def random_mask(self, batch_size: int, device) -> torch.Tensor:
        num_mask = max(1, int(NUM_PATCHES * self.mask_ratio))
        mask = torch.zeros(batch_size, NUM_PATCHES, dtype=torch.bool, device=device)
        for i in range(batch_size):
            idx = torch.randperm(NUM_PATCHES, device=device)[:num_mask]
            mask[i, idx] = True
        return mask

    def forward(self, x):
        """One self-supervised training step. Returns the JEPA loss."""
        b = x.shape[0]
        mask = self.random_mask(b, x.device)

        with torch.no_grad():
            target_tokens = self.target_encoder(x)

        ctx_tokens, _ = self.context_encoder.patch_embed(x)
        ctx_tokens = self.context_encoder.pos_enc(ctx_tokens)
        ctx_tokens_masked = ctx_tokens.clone()
        ctx_tokens_masked[mask] = 0.0
        ctx_out = self.context_encoder.trunk(ctx_tokens_masked)

        pred = self.predictor(ctx_out, mask)

        loss = F.smooth_l1_loss(pred[mask], target_tokens[mask].detach())
        return loss

    @torch.no_grad()
    def embed(self, x) -> torch.Tensor:
        """Full-image (unmasked) embedding for downstream use: mean-pooled patch tokens."""
        self.eval()
        tokens = self.context_encoder(x)
        return tokens.mean(dim=1)  # (B, D)


def load_encoder_for_inference(weights_path, embed_dim: int, device: str = "cpu") -> JepaEncoder:
    model = JepaEncoder(embed_dim=embed_dim)
    state = torch.load(weights_path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


def image_to_tensor_batch(chw_arrays: list[np.ndarray]) -> torch.Tensor:
    return torch.from_numpy(np.stack(chw_arrays, axis=0)).float()
