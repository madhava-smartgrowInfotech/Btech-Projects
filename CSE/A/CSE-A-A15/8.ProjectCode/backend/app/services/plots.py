import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_CH = (("R", "#d9534f"), ("G", "#3a9b5c"), ("B", "#3b72c4"))


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def histogram_png(cover: np.ndarray, stego: np.ndarray) -> bytes:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.2), sharey=False)
    for i, (name, color) in enumerate(_CH):
        hc = np.bincount(cover[..., i].ravel(), minlength=256)
        hs = np.bincount(stego[..., i].ravel(), minlength=256)
        ax = axes[i]
        ax.fill_between(range(256), hc, step="mid", color="#888", alpha=0.55, label="cover")
        ax.step(range(256), hs, where="mid", color=color, linewidth=0.9, label="stego")
        ax.set_title(f"{name} channel", fontsize=10)
        ax.set_xlim(0, 255)
        ax.tick_params(labelsize=8)
        if i == 0:
            ax.legend(fontsize=8, frameon=False)
    fig.suptitle("Pixel-value histograms: cover vs stego", fontsize=11)
    fig.tight_layout()
    return _png(fig)


def bitplanes_png(cover: np.ndarray, stego: np.ndarray) -> bytes:
    cg, sg = cover[..., 0], stego[..., 0]  # red channel
    planes = (0, 1, 7)
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.4))
    for col, p in enumerate(planes):
        for row, (img, label) in enumerate(((cg, "cover"), (sg, "stego"))):
            ax = axes[row, col]
            ax.imshow((img >> p) & 1, cmap="gray", interpolation="nearest")
            ax.set_title(f"{label} - bit plane {p}" + (" (LSB)" if p == 0 else " (MSB)" if p == 7 else ""),
                         fontsize=9)
            ax.axis("off")
    fig.suptitle("Bit planes of the red channel: only the least significant plane changes", fontsize=11)
    fig.tight_layout()
    return _png(fig)
