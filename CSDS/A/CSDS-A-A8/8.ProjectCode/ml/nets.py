"""BioSight networks shared by training scripts and the API.

- TokenEncoder: one transformer that runs on ViT image patches (2-D grid) or k-mer DNA tokens (1-D grid).
- MultiScalePredictor: JEPA predictor whose queries (masked positions) cross-attend to
  context tokens at two scales (fine tokens + pooled coarse tokens).
- ViTSeg / SegDecoder: light decoder on top of the image encoder for tumour masks.
- UNet: supervised baseline.
- SeqClassifier: pooled head on top of the DNA encoder.
"""
import copy
import math

import torch
import torch.nn as nn
import torch.nn.functional as F
from timm.layers import PatchEmbed
from timm.models.vision_transformer import Block

IMG_SIZE = 128
PATCH = 8
IMG_GRID = (IMG_SIZE // PATCH, IMG_SIZE // PATCH)

KMER = 4
DNA_WINDOW = 99                      # bases per window -> 96 overlapping 4-mers
DNA_TOKENS = DNA_WINDOW - KMER + 1
DNA_GRID = (1, DNA_TOKENS)
PAD_ID = 4 ** KMER                   # 256
MASK_ID = PAD_ID + 1                 # 257
DNA_VOCAB = PAD_ID + 2


def sincos_1d(n, dim):
    pos = torch.arange(n, dtype=torch.float32)[:, None]
    omega = 1.0 / (10000 ** (torch.arange(dim // 2, dtype=torch.float32) / (dim // 2)))
    out = pos * omega[None]
    return torch.cat([out.sin(), out.cos()], dim=1)


def sincos_grid(grid, dim):
    h, w = grid
    if h == 1:
        return sincos_1d(w, dim)
    ys = sincos_1d(h, dim // 2)[:, None, :].expand(h, w, dim // 2)
    xs = sincos_1d(w, dim // 2)[None, :, :].expand(h, w, dim // 2)
    return torch.cat([ys, xs], dim=-1).reshape(h * w, dim)


class KmerEmbed(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.emb = nn.Embedding(DNA_VOCAB, dim)

    def forward(self, x):
        return self.emb(x)


class TokenEncoder(nn.Module):
    def __init__(self, embed, grid, dim, depth, heads):
        super().__init__()
        self.embed = embed
        self.grid = grid
        self.dim = dim
        self.register_buffer("pos", sincos_grid(grid, dim)[None], persistent=False)
        self.blocks = nn.ModuleList([Block(dim, heads, mlp_ratio=4.0, qkv_bias=True) for _ in range(depth)])
        self.norm = nn.LayerNorm(dim)

    def tokens(self, x):
        return self.embed(x) + self.pos

    def forward(self, x, keep_idx=None, pre_embedded=False):
        t = x if pre_embedded else self.tokens(x)
        if keep_idx is not None:
            t = t[:, keep_idx]
        for blk in self.blocks:
            t = blk(t)
        return self.norm(t)


def image_encoder(dim=128, depth=6, heads=4):
    embed = PatchEmbed(img_size=IMG_SIZE, patch_size=PATCH, in_chans=3, embed_dim=dim)
    return TokenEncoder(embed, IMG_GRID, dim, depth, heads)


def dna_encoder(dim=128, depth=4, heads=4):
    return TokenEncoder(KmerEmbed(dim), DNA_GRID, dim, depth, heads)


class CrossAttnLayer(nn.Module):
    def __init__(self, dim, heads):
        super().__init__()
        self.nq = nn.LayerNorm(dim)
        self.nkv = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, heads, batch_first=True)
        self.self_block = Block(dim, heads, mlp_ratio=4.0, qkv_bias=True)

    def forward(self, q, kv):
        kv = self.nkv(kv)
        q = q + self.attn(self.nq(q), kv, kv, need_weights=False)[0]
        return self.self_block(q)


class MultiScalePredictor(nn.Module):
    """Predicts target-encoder features at masked positions from the visible context."""

    def __init__(self, enc_dim, grid, pool, dim=96, depth=3, heads=4):
        super().__init__()
        self.grid, self.pool, self.dim = grid, pool, dim
        self.inp = nn.Linear(enc_dim, dim)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, dim))
        self.scale_emb = nn.Parameter(torch.zeros(2, dim))
        coarse_grid = (math.ceil(grid[0] / pool[0]), math.ceil(grid[1] / pool[1]))
        self.register_buffer("pos", sincos_grid(grid, dim), persistent=False)
        self.register_buffer("coarse_pos", sincos_grid(coarse_grid, dim), persistent=False)
        self.layers = nn.ModuleList([CrossAttnLayer(dim, heads) for _ in range(depth)])
        self.out = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, enc_dim))
        nn.init.normal_(self.mask_token, std=0.02)

    def coarse(self, c, ctx_idx):
        h, w = self.grid
        b = c.shape[0]
        g = c.new_zeros(b, h * w, self.dim)
        m = c.new_zeros(1, h * w, 1)
        g[:, ctx_idx] = c
        m[:, ctx_idx] = 1.0
        g = g.transpose(1, 2).reshape(b, self.dim, h, w)
        m = m.transpose(1, 2).reshape(1, 1, h, w)
        gp = F.avg_pool2d(g, self.pool, ceil_mode=True)
        mp = F.avg_pool2d(m, self.pool, ceil_mode=True)
        pooled = (gp / mp.clamp_min(1e-6)).flatten(2).transpose(1, 2)
        valid = mp.flatten() > 0
        return pooled[:, valid] + self.coarse_pos[valid] + self.scale_emb[1]

    def forward(self, ctx, ctx_idx, tgt_idx):
        c = self.inp(ctx)
        fine = c + self.pos[ctx_idx] + self.scale_emb[0]
        kv = torch.cat([fine, self.coarse(c, ctx_idx)], dim=1)
        q = (self.mask_token + self.pos[tgt_idx][None]).expand(ctx.shape[0], -1, -1)
        for layer in self.layers:
            q = layer(q, kv)
        return self.out(q)


def ema_copy(module):
    tgt = copy.deepcopy(module)
    for p in tgt.parameters():
        p.requires_grad_(False)
    return tgt


@torch.no_grad()
def ema_update(target, online, m):
    for pt, po in zip(target.parameters(), online.parameters()):
        pt.mul_(m).add_(po.detach(), alpha=1 - m)


def conv_bn(cin, cout):
    return nn.Sequential(nn.Conv2d(cin, cout, 3, padding=1, bias=False), nn.BatchNorm2d(cout), nn.ReLU(inplace=True))


class SegDecoder(nn.Module):
    """Light decoder: 16x16 token map -> 128x128 mask logits (3 x2 upsampling stages)."""

    def __init__(self, dim):
        super().__init__()
        self.proj = conv_bn(dim, 96)
        self.up = nn.ModuleList([conv_bn(96, 64), conv_bn(64, 32), conv_bn(32, 16)])
        self.head = nn.Conv2d(16, 1, 1)

    def forward(self, t, grid):
        b, n, d = t.shape
        x = self.proj(t.transpose(1, 2).reshape(b, d, *grid))
        for layer in self.up:
            x = layer(F.interpolate(x, scale_factor=2, mode="bilinear", align_corners=False))
        return self.head(x)


class ViTSeg(nn.Module):
    def __init__(self, encoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = SegDecoder(encoder.dim)

    def forward(self, x):
        return self.decoder(self.encoder(x), self.encoder.grid)


class UNet(nn.Module):
    def __init__(self, base=16):
        super().__init__()
        ch = [base, base * 2, base * 4, base * 8]
        self.downs = nn.ModuleList()
        cin = 3
        for c in ch:
            self.downs.append(nn.Sequential(conv_bn(cin, c), conv_bn(c, c)))
            cin = c
        self.mid = nn.Sequential(conv_bn(ch[-1], ch[-1] * 2), conv_bn(ch[-1] * 2, ch[-1] * 2))
        self.ups = nn.ModuleList()
        self.upconvs = nn.ModuleList()
        cin = ch[-1] * 2
        for c in reversed(ch):
            self.upconvs.append(nn.ConvTranspose2d(cin, c, 2, stride=2))
            self.ups.append(nn.Sequential(conv_bn(c * 2, c), conv_bn(c, c)))
            cin = c
        self.head = nn.Conv2d(ch[0], 1, 1)

    def forward(self, x):
        skips = []
        for d in self.downs:
            x = d(x)
            skips.append(x)
            x = F.max_pool2d(x, 2)
        x = self.mid(x)
        for upc, up, s in zip(self.upconvs, self.ups, reversed(skips)):
            x = up(torch.cat([upc(x), s], dim=1))
        return self.head(x)


class SeqClassifier(nn.Module):
    def __init__(self, encoder, n_classes):
        super().__init__()
        self.encoder = encoder
        self.head = nn.Sequential(nn.LayerNorm(encoder.dim), nn.Linear(encoder.dim, n_classes))

    def features(self, x):
        t = self.encoder(x)
        valid = (x != PAD_ID).unsqueeze(-1).float()
        return (t * valid).sum(1) / valid.sum(1).clamp_min(1.0)

    def forward(self, x):
        return self.head(self.features(x))


# ---------- masking ----------

def block_mask_2d(grid, gen, n_targets=4, t_scale=(0.15, 0.2), aspect=(0.75, 1.5), c_scale=(0.85, 1.0)):
    """I-JEPA style multi-block masking. Returns (context_idx, target_idx) as LongTensors."""
    h, w = grid
    n = h * w

    def sample_block(scale, ar):
        s = scale[0] + (scale[1] - scale[0]) * torch.rand(1, generator=gen).item()
        a = math.exp(math.log(ar[0]) + (math.log(ar[1]) - math.log(ar[0])) * torch.rand(1, generator=gen).item())
        bh = max(1, min(h, int(round(math.sqrt(s * n * a)))))
        bw = max(1, min(w, int(round(math.sqrt(s * n / a)))))
        top = torch.randint(0, h - bh + 1, (1,), generator=gen).item()
        left = torch.randint(0, w - bw + 1, (1,), generator=gen).item()
        m = torch.zeros(h, w, dtype=torch.bool)
        m[top:top + bh, left:left + bw] = True
        return m.flatten()

    tgt = torch.zeros(n, dtype=torch.bool)
    for _ in range(n_targets):
        tgt |= sample_block(t_scale, aspect)
    ctx = sample_block(c_scale, (1.0, 1.0)) & ~tgt
    if ctx.sum() < 8:
        ctx = ~tgt
    return ctx.nonzero().flatten(), tgt.nonzero().flatten()


def span_mask_1d(n, gen, n_targets=3, t_scale=(0.1, 0.15)):
    tgt = torch.zeros(n, dtype=torch.bool)
    for _ in range(n_targets):
        s = t_scale[0] + (t_scale[1] - t_scale[0]) * torch.rand(1, generator=gen).item()
        length = max(2, int(round(s * n)))
        start = torch.randint(0, n - length + 1, (1,), generator=gen).item()
        tgt[start:start + length] = True
    return (~tgt).nonzero().flatten(), tgt.nonzero().flatten()


# ---------- k-mer tokenisation ----------

_BASE = {"A": 0, "C": 1, "G": 2, "T": 3}


def kmer_tokens(seq, window=DNA_WINDOW):
    """Overlapping 4-mer ids for one window; ambiguous bases / padding -> PAD_ID."""
    seq = seq.upper()[:window]
    ids = []
    for i in range(DNA_TOKENS):
        kmer = seq[i:i + KMER]
        if len(kmer) < KMER or any(ch not in _BASE for ch in kmer):
            ids.append(PAD_ID)
            continue
        v = 0
        for ch in kmer:
            v = v * 4 + _BASE[ch]
        ids.append(v)
    return ids


def seq_windows(seq, stride=50):
    seq = seq.upper()
    if len(seq) <= DNA_WINDOW:
        return [seq]
    starts = list(range(0, len(seq) - DNA_WINDOW + 1, stride))
    if starts[-1] != len(seq) - DNA_WINDOW:
        starts.append(len(seq) - DNA_WINDOW)
    return [seq[s:s + DNA_WINDOW] for s in starts]
