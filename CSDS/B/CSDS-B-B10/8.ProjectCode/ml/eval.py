"""Evaluate SkyCipher on the committed sample set and write experiments/eval/metrics.json.

  venv\\Scripts\\python ml\\eval.py

Covers the objectives: DWT decomposition + chaotic keys + XOR diffusion (exact recovery), entropy, histogram,
correlation, NPCR, UACI, key sensitivity, PSNR, MSE, encryption / decryption time, channel damage and a
speed comparison with AES-256-CTR and ChaCha20. Keys and nonces come from a seeded generator, so every number
except timing is reproducible.
"""
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import attacks, bench, cipher as C, metrics  # noqa: E402
from app.services.imaging import list_samples, list_sequences, read_path, sample_path, sequence_frames  # noqa: E402
from app.services.live import fit_width  # noqa: E402

OUT = ROOT / "experiments" / "eval"
RNG = np.random.default_rng(2026)


def seeded_key():
    return RNG.bytes(32).hex()


def seeded_nonce():
    return RNG.bytes(16).hex()


def summary(values):
    a = np.asarray(values, dtype=np.float64)
    return {"mean": float(a.mean()), "std": float(a.std()), "min": float(a.min()), "max": float(a.max())}


def per_image(img, name, kind):
    r = metrics.analyze(img, seeded_key(), seeded_nonce(), seed=int(RNG.integers(1 << 30)), thumbs=False)
    q = r["quality"]
    return {
        "name": name, "set": kind, "width": r["image"]["width"], "height": r["image"]["height"],
        "channels": r["image"]["channels"],
        "entropy_plain": r["entropy"]["plain"]["mean"], "entropy_cipher": r["entropy"]["cipher"]["mean"],
        "chi2_cipher_max": max(r["chi_square"]["cipher"]["per_channel"]),
        "histogram_uniform": r["chi_square"]["cipher"]["uniform"],
        **{f"corr_plain_{d}": r["correlation"]["plain"][d] for d in ("horizontal", "vertical", "diagonal")},
        **{f"corr_cipher_{d}": r["correlation"]["cipher"][d] for d in ("horizontal", "vertical", "diagonal")},
        "npcr": r["differential"]["npcr"], "uaci": r["differential"]["uaci"],
        "decrypt_identical": q["decrypted"]["identical"], "decrypt_mse": q["decrypted"]["mse"],
        "decrypt_psnr": q["decrypted"]["psnr"],
        "cipher_mse": q["cipher_vs_plain"]["mse"], "cipher_psnr": q["cipher_vs_plain"]["psnr"],
        "cipher_ssim": q["cipher_vs_plain"]["ssim"],
        "key_sens_cipher_npcr_min": r["key_sensitivity"]["min_cipher_npcr"],
        "key_sens_wrong_key_psnr_max": max(t["wrong_key_decrypt"]["psnr"] for t in r["key_sensitivity"]["tests"]),
        "wrong_key_recovers": r["key_sensitivity"]["wrong_key_recovers"],
        "key_setup_ms": r["timing"]["key_setup_ms"],
        "enc_ms": r["timing"]["encrypt_ms"], "dec_ms": r["timing"]["decrypt_ms"],
        "throughput_mbps": r["timing"]["throughput_mbps"],
    }


def main():
    t_start = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    samples = list_samples()
    if not samples:
        sys.exit("No sample images - run scripts/download_data.py first")

    # warm-up so the first image's timing does not include one-off costs
    C.encrypt(np.zeros((64, 64, 3), np.uint8), seeded_key(), seeded_nonce())

    rows = []
    for i, s in enumerate(samples, 1):
        img, _ = read_path(sample_path(s["kind"], s["name"]))
        rows.append(per_image(img, s["name"], s["kind"]))
        print(f"[{i}/{len(samples)}] {s['name']}: H={rows[-1]['entropy_cipher']:.4f} NPCR={rows[-1]['npcr']:.3f} "
              f"UACI={rows[-1]['uaci']:.3f} enc={rows[-1]['enc_ms']:.1f} ms", flush=True)

    keys = ["entropy_plain", "entropy_cipher", "chi2_cipher_max", "npcr", "uaci", "cipher_mse", "cipher_psnr",
            "cipher_ssim", "key_sens_cipher_npcr_min", "key_sens_wrong_key_psnr_max", "key_setup_ms", "enc_ms", "dec_ms",
            "throughput_mbps"] + [f"corr_{w}_{d}" for w in ("plain", "cipher") for d in ("horizontal", "vertical", "diagonal")]
    aggregate = {k: summary([r[k] for r in rows]) for k in keys}
    aggregate["decrypt_identical_all"] = all(r["decrypt_identical"] for r in rows)
    aggregate["decrypt_mse_max"] = max(r["decrypt_mse"] for r in rows)
    aggregate["histogram_uniform_pct"] = 100.0 * np.mean([r["histogram_uniform"] for r in rows])
    aggregate["wrong_key_recovers_any"] = any(r["wrong_key_recovers"] for r in rows)
    by_set = {}
    for kind in sorted({r["set"] for r in rows}):
        sub = [r for r in rows if r["set"] == kind]
        by_set[kind] = {"images": len(sub), **{k: summary([r[k] for r in sub])["mean"] for k in
                        ("entropy_cipher", "npcr", "uaci", "corr_cipher_horizontal", "corr_cipher_vertical",
                         "corr_cipher_diagonal", "enc_ms", "dec_ms")}}

    # channel damage on 10 drone images
    print("Attack tests ...", flush=True)
    drone = [s for s in samples if s["kind"] == "visdrone"][:10]
    att = {}
    for s in drone:
        img, _ = read_path(sample_path(s["kind"], s["name"]))
        for a in attacks.run(img, seeded_key(), seeded_nonce(), previews=False)["results"]:
            d = att.setdefault(a["label"], {"psnr": [], "ssim": [], "intact_pct": [], "median_psnr": []})
            d["psnr"].append(a["recovered"]["psnr"])
            d["ssim"].append(a["recovered"]["ssim"])
            d["intact_pct"].append(a["recovered"]["intact_pct"])
            d["median_psnr"].append(a["median_filtered"]["psnr"])
    attack_summary = {k: {m: float(np.mean(v)) for m, v in d.items()} for k, d in att.items()}

    # speed vs AES / ChaCha20
    print("Benchmark ...", flush=True)
    imgs = [read_path(sample_path(s["kind"], s["name"]))[0] for s in drone]
    speed = {str(size): bench.run(imgs, size, repeats=3) for size in (256, 512, 1024)}

    # live-link frame budget (480 px wide frames from the committed sequences)
    print("Live frame timing ...", flush=True)
    live = {}
    key = seeded_key()
    for q in list_sequences():
        enc_t, dec_t = [], []
        for p in sequence_frames(q["name"]):
            f = fit_width(read_path(p, False)[0], 480)
            n = seeded_nonce()
            t0 = time.perf_counter()
            e = C.encrypt(f, key, n)
            t1 = time.perf_counter()
            d = C.decrypt(e, key, n)
            t2 = time.perf_counter()
            assert np.array_equal(d, f)
            enc_t.append((t1 - t0) * 1000)
            dec_t.append((t2 - t1) * 1000)
        live[q["name"]] = {"frames": len(enc_t), "frame_shape": list(f.shape),
                           "enc_ms_mean": float(np.mean(enc_t)), "dec_ms_mean": float(np.mean(dec_t)),
                           "fps_capacity_enc": float(1000 / np.mean(enc_t)),
                           "fps_capacity_enc_plus_dec": float(1000 / (np.mean(enc_t) + np.mean(dec_t))),
                           "all_frames_exact": True}

    result = metrics.jsonable({
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "machine": platform.machine(), "processor": platform.processor()},
        "cipher": {"key_bits": 256, "nonce_bits": 128, "dwt": "one-level integer Haar lifting mod 256",
                   "permutation": "Henon map", "diffusion": "2-D logistic (sine-modulated) XOR + key-dependent S-box + chained add, forward and backward",
                   "rounds": C.ROUNDS},
        "dataset": {"images": len(rows), "by_set": {k: v["images"] for k, v in by_set.items()}},
        "aggregate": aggregate, "by_set": by_set, "attacks": attack_summary, "speed": speed, "live_frames": live,
        "per_image": rows, "runtime_s": time.time() - t_start,
    })
    (OUT / "metrics.json").write_text(json.dumps(result, indent=2))
    print(f"\nWrote {OUT / 'metrics.json'} in {time.time() - t_start:.0f} s")
    a = aggregate
    print(f"entropy {a['entropy_cipher']['mean']:.4f}  NPCR {a['npcr']['mean']:.4f}  UACI {a['uaci']['mean']:.4f}  "
          f"exact={a['decrypt_identical_all']}  corrH {a['corr_cipher_horizontal']['mean']:.5f}")


if __name__ == "__main__":
    main()
