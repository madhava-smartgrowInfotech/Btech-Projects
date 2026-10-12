"""Write the cover images and sample payloads (seeded, repeatable).

Covers: public-domain / CC0 photographs shipped with scikit-image (astronaut: NASA, public domain;
coffee and chelsea: CC0; rocket: public domain) at different sizes, plus one procedurally
generated landscape. Payloads are synthetic documents made here.
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
from skimage import data

ROOT = Path(__file__).resolve().parents[1]
COVERS = ROOT / "data" / "covers"
PAYLOADS = ROOT / "data" / "payloads"


def save(arr, name):
    Image.fromarray(arr).save(COVERS / name, format="PNG", optimize=True)
    print("cover", name, arr.shape[1], "x", arr.shape[0])


def landscape(w=1280, h=720, seed=11):
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h)[:, None]
    sky = np.stack([40 + 150 * y, 90 + 130 * y, 170 + 70 * y], axis=-1) * np.ones((1, w, 1))
    x = np.linspace(0, 8 * np.pi, w)
    img = sky.copy()
    for layer, (base, amp, col) in enumerate([(0.55, 0.10, (92, 110, 140)), (0.68, 0.12, (60, 85, 95)),
                                              (0.82, 0.10, (34, 58, 52))]):
        ridge = base + amp * (np.sin(x * (1 + layer) + rng.uniform(0, 6)) * 0.5
                              + np.sin(x * 2.7 + rng.uniform(0, 6)) * 0.3 + np.sin(x * 6.1) * 0.1)
        mask = (np.linspace(0, 1, h)[:, None] >= ridge[None, :])[..., None]
        img = np.where(mask, np.array(col, dtype=float)[None, None, :], img)
    img += rng.normal(0, 2.0, img.shape)  # fine grain, like sensor noise
    return np.clip(img, 0, 255).astype(np.uint8)


def make_covers():
    COVERS.mkdir(parents=True, exist_ok=True)
    save(data.astronaut(), "astronaut_512x512.png")
    save(data.coffee(), "coffee_600x400.png")
    save(data.rocket(), "rocket_640x427.png")
    save(data.chelsea(), "cat_451x300.png")
    small = Image.fromarray(data.coffee()).crop((100, 0, 500, 400)).resize((200, 200), Image.LANCZOS)
    save(np.array(small), "coffee_small_200x200.png")
    save(landscape(), "generated_landscape_1280x720.png")


def make_payloads():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    PAYLOADS.mkdir(parents=True, exist_ok=True)
    with PdfPages(PAYLOADS / "confidential_memo.pdf", metadata={
            "Title": "Sample memo", "CreationDate": datetime(2025, 1, 1), "ModDate": datetime(2025, 1, 1)}) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.1, 0.92, "CONFIDENTIAL - SAMPLE MEMO", fontsize=18, weight="bold")
        body = ["This is synthetic sample text used to demonstrate CipherVeil.",
                "", "Subject: Q3 supplier price renegotiation (fictional)", "",
                "- Target discount: 7.5% on volume above 40,000 units",
                "- Walk-away price: 4.10 per unit", "- Decision owner: Operations lead", "",
                "If you can read this after extraction, the file survived the round trip byte for byte."]
        for i, line in enumerate(body):
            fig.text(0.1, 0.86 - i * 0.03, line, fontsize=11)
        pdf.savefig(fig)
        plt.close(fig)

    rng = np.random.default_rng(5)
    rows = ["id,name,balance"] + [f"{i},account_{i:03d},{rng.integers(100, 99999) / 100:.2f}" for i in range(1, 121)]
    (PAYLOADS / "accounts.csv").write_text("\n".join(rows) + "\n")
    (PAYLOADS / "meeting_notes.txt").write_text(
        "Sample meeting notes (synthetic)\n\n1. Release moves to the 14th.\n2. Rotate the signing keys before launch.\n"
        "3. Share the client list only over the protected channel.\n")
    (PAYLOADS / "settings.json").write_text(json.dumps(
        {"service": "demo", "region": "eu-west", "retries": 3, "note": "synthetic sample"}, indent=2) + "\n")
    for p in sorted(PAYLOADS.iterdir()):
        print("payload", p.name, p.stat().st_size, "bytes")


if __name__ == "__main__":
    make_covers()
    make_payloads()
