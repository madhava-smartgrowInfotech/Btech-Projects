"""Small PyTorch models: a landmark-sequence Transformer for words, an MLP for letters."""
import torch
from torch import nn

from ml.features import LETTER_DIM, T, WORD_DIM


class WordTransformer(nn.Module):
    def __init__(self, n_classes, d=128, layers=2, heads=4, dropout=0.2):
        super().__init__()
        self.embed = nn.Sequential(nn.Linear(WORD_DIM, d), nn.LayerNorm(d), nn.GELU(), nn.Dropout(dropout))
        self.pos = nn.Parameter(torch.zeros(1, T, d))
        layer = nn.TransformerEncoderLayer(d, heads, d * 2, dropout, batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.head = nn.Sequential(nn.LayerNorm(d), nn.Dropout(dropout), nn.Linear(d, n_classes))

    def forward(self, x):  # (B, T, WORD_DIM) -> logits
        h = self.encoder(self.embed(x) + self.pos)
        return self.head(h.mean(dim=1))


class LetterMLP(nn.Module):
    def __init__(self, n_classes, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(LETTER_DIM, 256), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(256, 128), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(128, n_classes),
        )

    def forward(self, x):
        return self.net(x)
