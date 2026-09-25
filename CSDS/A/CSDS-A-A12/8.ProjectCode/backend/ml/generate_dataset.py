"""Synthesizes a millet seed image + crop-condition dataset with a realistic,
nonlinear (not trivially separable) germination outcome.

No public labelled germination-image dataset exists for this task, so this
script builds one procedurally:

  - a latent per-seed "viability" score drives both how the seed *looks*
    (shape regularity, colour saturation/uniformity, surface blemishes) and,
    together with environmental conditions, whether it germinates — so the
    image and the label are genuinely correlated, the same way a real
    labelled corpus would be, rather than the image being decorative.
  - environmental/tabular features are drawn from realistic agronomic
    ranges with per-seed-type baselines and nonlinear interactions (e.g.
    cold + wet compounds risk beyond either alone), plus label noise, so a
    linear model can't trivially solve it.

Run directly: `python ml/generate_dataset.py`
"""
import csv
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from app.core.config import DATASET_CSV, DATASET_DIR, SEED_TYPES

random.seed(42)
np.random.seed(42)

N_SAMPLES = 3200
IMAGE_PX = 128

# Per-variety morphology baseline: (aspect_ratio_mean, size_mean_px, base_color_rgb, base_germ_rate)
SEED_TYPE_PROFILE = {
    "Pearl Millet":    (1.7, 34, (188, 150, 90), 0.78),
    "Finger Millet":   (1.15, 14, (120, 80, 55), 0.72),
    "Foxtail Millet":  (1.9, 18, (210, 190, 140), 0.68),
    "Little Millet":   (1.3, 12, (170, 140, 90), 0.65),
    "Kodo Millet":     (1.4, 20, (90, 70, 55), 0.70),
    "Proso Millet":    (1.1, 22, (225, 200, 150), 0.74),
    "Barnyard Millet": (1.6, 26, (140, 120, 80), 0.66),
}


def sample_environment():
    soil_moisture = float(np.clip(np.random.normal(60, 16), 8, 98))
    temperature = float(np.clip(np.random.normal(27, 6.5), 8, 46))
    humidity = float(np.clip(np.random.normal(64, 16), 12, 98))
    rainfall = float(np.clip(np.random.exponential(60), 0, 320))
    soil_ph = float(np.clip(np.random.normal(6.4, 0.9), 3.8, 9.2))
    return soil_moisture, temperature, humidity, rainfall, soil_ph


def viability_score() -> float:
    """Latent seed quality in [0, 1], independent of environment."""
    return float(np.clip(np.random.beta(3.2, 1.8), 0, 1))


def render_seed_image(seed_type: str, viability: float, size: int = IMAGE_PX) -> Image.Image:
    aspect, base_r, base_color, _ = SEED_TYPE_PROFILE[seed_type]

    bg_base = np.array([
        random.randint(95, 150),
        random.randint(75, 120),
        random.randint(45, 95),
    ], dtype=np.float32)
    noise = np.random.normal(0, 10, (size, size, 3))
    bg = np.clip(bg_base + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(bg, mode="RGB")
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2 + random.randint(-8, 8), size // 2 + random.randint(-8, 8)
    r_major = base_r * random.uniform(0.85, 1.15)
    r_minor = r_major / (aspect * random.uniform(0.9, 1.1))
    angle = random.uniform(0, 360)

    irregularity = (1 - viability) * 0.35  # low viability -> lumpier, less circular boundary
    n_pts = 24
    pts = []
    for i in range(n_pts):
        theta = 2 * math.pi * i / n_pts
        wobble = 1 + irregularity * (random.uniform(-1, 1))
        x = r_major * math.cos(theta) * wobble
        y = r_minor * math.sin(theta) * wobble
        rad = math.radians(angle)
        xr = x * math.cos(rad) - y * math.sin(rad)
        yr = x * math.sin(rad) + y * math.cos(rad)
        pts.append((cx + xr, cy + yr))

    saturation = 0.55 + 0.45 * viability  # healthier seeds: richer, more saturated colour
    color = tuple(int(np.clip(c * saturation + random.uniform(-8, 8), 0, 255)) for c in base_color)
    draw.polygon(pts, fill=color)

    # Blemishes / mould spots scale inversely with viability.
    n_spots = int((1 - viability) * random.uniform(0, 9))
    for _ in range(n_spots):
        sx = cx + random.uniform(-r_major, r_major) * 0.7
        sy = cy + random.uniform(-r_minor, r_minor) * 0.7
        sr = random.uniform(1.5, 4.5)
        spot_color = tuple(int(c * random.uniform(0.3, 0.6)) for c in color)
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=spot_color)

    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 1.1)))
    arr = np.array(img).astype(np.float32)
    arr += np.random.normal(0, 6, arr.shape)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return img


def germination_probability(seed_type, viability, soil_moisture, temperature, humidity, rainfall, soil_ph) -> float:
    _, _, _, base_rate = SEED_TYPE_PROFILE[seed_type]
    base_logit = math.log(base_rate / (1 - base_rate))

    moisture_term = -((soil_moisture - 65) ** 2) / (2 * 22**2)
    temp_term = -((temperature - 27) ** 2) / (2 * 8**2)
    humidity_term = -((humidity - 62) ** 2) / (2 * 28**2)
    rainfall_term = -((rainfall - 70) ** 2) / (2 * 90**2)
    ph_term = -((soil_ph - 6.4) ** 2) / (2 * 1.1**2)

    # Nonlinear interaction: cold + high moisture compounds risk (waterlogged, slow chilled imbibition).
    interaction = 0.0
    if temperature < 20 and soil_moisture > 75:
        interaction -= 1.1
    if temperature > 36 and soil_moisture < 35:
        interaction -= 0.9

    viability_term = (viability - 0.5) * 3.2

    logit = (
        base_logit
        + 1.6 * moisture_term
        + 1.6 * temp_term
        + 0.9 * humidity_term
        + 0.6 * rainfall_term
        + 1.3 * ph_term
        + interaction
        + viability_term
        + np.random.normal(0, 0.35)  # irreducible label noise
    )
    prob = 1 / (1 + math.exp(-logit))
    return float(np.clip(prob, 0.01, 0.99))


def main():
    images_dir = DATASET_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i in range(N_SAMPLES):
        seed_type = random.choice(SEED_TYPES)
        viability = viability_score()
        soil_moisture, temperature, humidity, rainfall, soil_ph = sample_environment()

        prob = germination_probability(seed_type, viability, soil_moisture, temperature, humidity, rainfall, soil_ph)
        label = 1 if random.random() < prob else 0

        img = render_seed_image(seed_type, viability)
        fname = f"seed_{i:05d}.png"
        img.save(images_dir / fname)

        rows.append({
            "image": fname,
            "seed_type": seed_type,
            "soil_moisture": round(soil_moisture, 2),
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "rainfall": round(rainfall, 2),
            "soil_ph": round(soil_ph, 3),
            "viability_latent": round(viability, 3),
            "germination_probability": round(prob, 4),
            "germinated": label,
        })

        if (i + 1) % 500 == 0:
            print(f"generated {i + 1}/{N_SAMPLES}")

    with open(DATASET_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    pos_rate = sum(r["germinated"] for r in rows) / len(rows)
    print(f"Wrote {len(rows)} samples to {DATASET_CSV}")
    print(f"Positive (germinated) rate: {pos_rate:.3f}")


if __name__ == "__main__":
    main()
