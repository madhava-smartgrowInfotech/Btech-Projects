"""Capacity and speed measurements over a set of covers and payload sizes."""
import statistics

import numpy as np

from . import crypto, lsb, pipeline


def capacity_table(covers: list[tuple[str, np.ndarray]]) -> list[dict]:
    rows = []
    for name, arr in covers:
        h, w = arr.shape[:2]
        cap = lsb.capacity_bytes(arr)
        rows.append({"cover": name, "width": w, "height": h, "pixels": w * h,
                     "max_bundle_bytes": cap, "max_bundle_kib": round(cap / 1024, 1),
                     "max_bits_per_pixel": round(cap * 8 / (w * h), 3)})
    return rows


def run(covers: list[tuple[str, np.ndarray]], sizes: list[int], key_bits: int = 3072, repeats: int = 3) -> dict:
    private_pem, public_pem = crypto.generate_keypair(key_bits)
    rng = np.random.default_rng(2024)
    rows = []
    for name, arr in covers:
        for size in sizes:
            payload = rng.integers(0, 256, size, dtype=np.uint8).tobytes()
            runs = []
            try:
                for _ in range(repeats):
                    sent = pipeline.hide(public_pem, "bench.bin", payload, arr)
                    got = pipeline.reveal(private_pem, sent["stego"])
                    assert got["data"] == payload
                    runs.append((sent, got))
            except lsb.StegoError:
                rows.append({"cover": name, "payload_bytes": size, "fits": False})
                continue
            med = lambda f: round(statistics.median(f(s, g) for s, g in runs), 3)
            q = runs[0][0]["quality"]
            rows.append({
                "cover": name, "payload_bytes": size, "fits": True,
                "pixels": runs[0][0]["capacity"]["pixels"],
                "used_pct": runs[0][0]["capacity"]["used_pct"],
                "bits_per_pixel": runs[0][0]["capacity"]["payload_bits_per_pixel"],
                "psnr_db": q["psnr_db"], "ssim": q["ssim"], "changed_pct": q["changed_pct"],
                "encrypt_ms": med(lambda s, g: s["timings_ms"]["encrypt"]),
                "embed_ms": med(lambda s, g: s["timings_ms"]["embed"]),
                "extract_ms": med(lambda s, g: g["timings_ms"]["extract"]),
                "decrypt_ms": med(lambda s, g: g["timings_ms"]["decrypt"]),
                "round_trip_ok": True,
            })
    return {"key_bits": key_bits, "repeats": repeats, "rows": rows}
