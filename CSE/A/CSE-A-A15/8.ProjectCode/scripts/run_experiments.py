"""Extra experiments for the documentation: everything here runs the real services in backend/app.

Adds to ml/eval.py:
  A  RSA key-size study (key generation, wrap, unwrap, bundle overhead)
  B  fill-ratio study: measured PSNR/SSIM against the closed-form PSNR, 6 covers x 7 fill levels, 5 payload seeds
  C  plain LSB (no encryption) versus the encrypted bundle: changed values, bit balance, byte entropy
  D  steganalysis: chi-square (Westfeld-Pfitzmann) and weighted-stego payload estimate on cover versus stego
  E  tamper study: one flipped LSB at a random place in the embedded bundle (200 trials), outcome by field
  F  freshness: 50 encryptions of the same file under one key
  G  extra channel attacks (lossless re-encodings, WebP, grayscale, rotate, flip, palette, JPEG q100)

Writes experiments/extra/metrics.json and experiments/extra/summary.md.   venv\\Scripts\\python scripts\\run_experiments.py
"""
import io
import json
import math
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import crypto, lsb, metrics, pipeline  # noqa: E402

OUT = ROOT / "experiments" / "extra"
COVERS = [(p.name, lsb.load_rgb(str(p))) for p in sorted((ROOT / "data" / "covers").glob("*.png"))]
PAYLOADS = {p.name: p.read_bytes() for p in sorted((ROOT / "data" / "payloads").iterdir()) if p.is_file()}
FILLS = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 1.00]


def med(xs):
    return round(statistics.median(xs), 3)



def payload_for_fill(pub, cap, f, seed, name="fill.bin"):
    """Random payload whose whole bundle fills fraction f of the cover capacity (never above it)."""
    size = int((cap - 420 - 128) * f) if f < 1 else cap - 700
    while True:
        data = np.random.default_rng(seed).integers(0, 256, size, dtype=np.uint8).tobytes()
        bundle, _ = crypto.encrypt_bundle(pub, name, data)
        if len(bundle) <= cap and (f < 1 or cap - len(bundle) < 64):
            return data, bundle
        size += -1 if len(bundle) > cap else 1


# ---------------------------------------------------------------- A
def rsa_study():
    rows = []
    data = b"x" * 4096
    for bits in (2048, 3072, 4096):
        gen = []
        for _ in range(5):
            t = time.perf_counter()
            priv, pub = crypto.generate_keypair(bits)
            gen.append((time.perf_counter() - t) * 1000)
        wrap, unwrap = [], []
        for _ in range(30):
            t = time.perf_counter()
            bundle, info = crypto.encrypt_bundle(pub, "k.bin", data)
            wrap.append((time.perf_counter() - t) * 1000)
            t = time.perf_counter()
            crypto.decrypt_bundle(priv, bundle)
            unwrap.append((time.perf_counter() - t) * 1000)
        rows.append({"rsa_bits": bits, "keygen_ms_median": med(gen), "keygen_ms_min": round(min(gen), 1),
                     "keygen_ms_max": round(max(gen), 1), "encrypt_wrap_ms_median": med(wrap),
                     "unwrap_decrypt_ms_median": med(unwrap), "wrapped_key_bytes": info["wrapped_key_bytes"],
                     "overhead_bytes": info["overhead_bytes"], "bundle_bytes_for_4KiB": info["bundle_bytes"]})
        print("A", rows[-1])
    return rows


# ---------------------------------------------------------------- B
def fill_study():
    priv, pub = crypto.generate_keypair(2048)
    rows = []
    for name, cover in COVERS:
        cap = lsb.capacity_bytes(cover)
        for f in FILLS:
            psnrs, ssims = [], []
            for seed in range(5):
                data, bundle = payload_for_fill(pub, cap, f, 1000 + seed)
                size = len(data)
                stego = lsb.embed(cover, bundle)
                q = metrics.imperceptibility(cover, stego)
                psnrs.append(q["psnr_db"])
                ssims.append(q["ssim"])
            nbits = (len(bundle) + 4) * 8
            theory = 10 * math.log10(255 ** 2 * cover.size / (0.5 * nbits))
            rows.append({"cover": name, "fill": f, "payload_bytes": size, "bundle_bytes": len(bundle),
                         "used_pct": round(100 * len(bundle) / cap, 2),
                         "psnr_mean": round(statistics.mean(psnrs), 3), "psnr_std": round(statistics.pstdev(psnrs), 4),
                         "psnr_theory": round(theory, 3), "ssim_mean": round(statistics.mean(ssims), 6),
                         "ssim_min": min(ssims)})
        print("B", name)
    dev = max(abs(r["psnr_mean"] - r["psnr_theory"]) for r in rows)
    return {"rows": rows, "max_abs_dev_vs_theory_db": round(dev, 3),
            "max_psnr_std_db": max(r["psnr_std"] for r in rows)}


# ---------------------------------------------------------------- C
def entropy_bits_per_byte(b: bytes) -> float:
    c = np.bincount(np.frombuffer(b, dtype=np.uint8), minlength=256).astype(float)
    p = c[c > 0] / c.sum()
    return float(-(p * np.log2(p)).sum())


def ones_fraction(b: bytes) -> float:
    return float(np.unpackbits(np.frombuffer(b, dtype=np.uint8)).mean())


def plain_vs_encrypted():
    name, cover = next(c for c in COVERS if c[0].startswith("generated"))
    priv, pub = crypto.generate_keypair(2048)
    rows = []
    for pname, data in PAYLOADS.items():
        bundle, _ = crypto.encrypt_bundle(pub, pname, data)
        for kind, blob in (("plain", data), ("encrypted", bundle)):
            stego = lsb.embed(cover, blob)
            q = metrics.imperceptibility(cover, stego)
            rows.append({"payload": pname, "kind": kind, "bytes": len(blob),
                         "ones_fraction": round(ones_fraction(blob), 4),
                         "entropy_bits_per_byte": round(entropy_bits_per_byte(blob), 3),
                         "values_changed": q["values_changed"], "changed_pct_of_embedded_bits":
                             round(100 * q["values_changed"] / ((len(blob) + 4) * 8), 2),
                         "psnr_db": q["psnr_db"]})
    return {"cover": name, "rows": rows}


# ---------------------------------------------------------------- D
def chi_square_p(values: np.ndarray) -> float:
    """Westfeld-Pfitzmann: p close to 1 means the value pairs (2k, 2k+1) are equalised, i.e. LSB replacement."""
    h = np.bincount(values, minlength=256).astype(float)
    even, odd = h[0::2], h[1::2]
    exp = (even + odd) / 2
    keep = exp >= 5
    if keep.sum() < 3:
        return float("nan")
    stat = float((((even - exp) ** 2) / np.where(exp > 0, exp, 1))[keep].sum())
    return float(1 - chi2.cdf(stat, int(keep.sum()) - 1))


def weighted_stego_rate(arr: np.ndarray) -> float:
    """Weighted-stego estimate (Fridrich-Goljan, unit weights) of the LSB-replaced fraction of samples."""
    x = arr.astype(np.float64)
    xbar = x.copy()
    xbar[arr % 2 == 0] += 1
    xbar[arr % 2 == 1] -= 1
    pred = np.zeros_like(x)
    pred[1:-1, 1:-1] = (x[:-2, 1:-1] + x[2:, 1:-1] + x[1:-1, :-2] + x[1:-1, 2:]) / 4
    sl = (slice(1, -1), slice(1, -1), slice(None))
    p = 2 * np.mean((x[sl] - xbar[sl]) * (x[sl] - pred[sl]))
    return float(p)


def steganalysis():
    priv, pub = crypto.generate_keypair(2048)
    rows = []
    for name, cover in COVERS:
        cap = lsb.capacity_bytes(cover)
        flat_c = cover.reshape(-1)
        base_ws = weighted_stego_rate(cover)
        for f in (0.10, 0.25, 0.50, 0.75, 1.00):
            data, bundle = payload_for_fill(pub, cap, f, 77, "s.bin")
            stego = lsb.embed(cover, bundle)
            nvals = (len(bundle) + 4) * 8
            frac = nvals / cover.size
            flat_s = stego.reshape(-1)
            rows.append({"cover": name, "fill": f, "embedded_values": nvals, "true_fraction_of_samples": round(frac, 4),
                         "chi2_p_cover_prefix": round(chi_square_p(flat_c[:nvals]), 4),
                         "chi2_p_stego_prefix": round(chi_square_p(flat_s[:nvals]), 4),
                         "ws_estimate_cover": round(base_ws, 4), "ws_estimate_stego": round(weighted_stego_rate(stego), 4)})
        print("D", name)
    chi_hits = [r for r in rows if r["chi2_p_stego_prefix"] > 0.5 and r["chi2_p_cover_prefix"] < 0.5]
    return {"rows": rows, "chi2_detected": len(chi_hits), "chi2_total": len(rows),
            "note": "chi-square is evaluated on the known embedded prefix (an oracle); weighted-stego is blind"}


# ---------------------------------------------------------------- E
def tamper_study():
    priv, pub = crypto.generate_keypair(2048)
    name, cover = next(c for c in COVERS if c[0].startswith("astronaut"))
    data = np.random.default_rng(5).integers(0, 256, 4096, dtype=np.uint8).tobytes()
    bundle, _ = crypto.encrypt_bundle(pub, "t.bin", data)
    stego = lsb.embed(cover, bundle)
    nbits = (len(bundle) + 4) * 8
    wl = 2048 // 8
    fields = [("length header", 0, 32), ("magic", 32, 64), ("wrapped-key length", 64, 80),
              ("wrapped key", 80, 80 + wl * 8), ("nonce", 80 + wl * 8, 80 + wl * 8 + 96),
              ("ciphertext and tag", 80 + wl * 8 + 96, nbits)]
    rng = np.random.default_rng(9)
    outcomes = {}
    accepted_wrong = 0
    trials = 0
    for fname, lo, hi in fields:
        for _ in range(40):
            pos = int(rng.integers(lo, hi))
            bad = stego.copy().reshape(-1)
            bad[pos] ^= 1
            trials += 1
            try:
                got = crypto.decrypt_bundle(priv, lsb.extract(bad.reshape(stego.shape)))[1]
                res = "accepted" if got == data else "accepted with wrong data"
                if got != data:
                    accepted_wrong += 1
            except lsb.StegoError:
                res = "rejected: bad length header"
            except crypto.CryptoError as exc:
                res = "rejected: " + str(exc).split(" - ")[0].split(".")[0][:60]
            except Exception as exc:  # corrupted header fields can fail while parsing
                res = "rejected: " + type(exc).__name__
            d = outcomes.setdefault(fname, {})
            d[res] = d.get(res, 0) + 1
    return {"cover": name, "trials": trials, "accepted_with_wrong_data": accepted_wrong, "by_field": outcomes}


# ---------------------------------------------------------------- F
def freshness():
    priv, pub = crypto.generate_keypair(2048)
    data = PAYLOADS["accounts.csv"]
    bundles = [crypto.encrypt_bundle(pub, "accounts.csv", data)[0] for _ in range(50)]
    nonces = {b[6 + 256:6 + 256 + 12] for b in bundles}
    wrapped = {b[6:6 + 256] for b in bundles}
    ham = []
    for i in range(0, 48, 2):
        a = np.unpackbits(np.frombuffer(bundles[i], dtype=np.uint8))
        b = np.unpackbits(np.frombuffer(bundles[i + 1], dtype=np.uint8))
        n = min(a.size, b.size)
        ham.append(float(np.mean(a[:n] != b[:n])))
    ok = all(crypto.decrypt_bundle(priv, b)[1] == data for b in bundles)
    return {"encryptions": 50, "distinct_nonces": len(nonces), "distinct_wrapped_keys": len(wrapped),
            "mean_bit_difference_between_bundles": round(statistics.mean(ham), 4), "all_decrypt": ok}


# ---------------------------------------------------------------- G
def _reencode(fmt, **kw):
    def f(a):
        buf = io.BytesIO()
        Image.fromarray(a, "RGB").save(buf, format=fmt, **kw)
        return np.array(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))
    return f


def _rgba(a):
    buf = io.BytesIO()
    Image.fromarray(a, "RGB").convert("RGBA").save(buf, format="PNG")
    return np.array(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))


EXTRA_ATTACKS = [
    ("PNG re-save, compression 9", _reencode("PNG", compress_level=9)),
    ("PNG with alpha channel added", _rgba),
    ("WebP lossless", _reencode("WEBP", lossless=True)),
    ("WebP lossy q90", _reencode("WEBP", quality=90)),
    ("JPEG quality 100", _reencode("JPEG", quality=100, subsampling=0)),
    ("Grayscale conversion", lambda a: np.array(Image.fromarray(a, "RGB").convert("L").convert("RGB"))),
    ("Rotate 90 degrees", lambda a: np.ascontiguousarray(np.rot90(a))),
    ("Flip horizontally", lambda a: np.ascontiguousarray(a[:, ::-1])),
    ("256-colour palette", lambda a: np.array(Image.fromarray(a, "RGB").quantize(256).convert("RGB"))),
]


def extra_attacks():
    priv, pub = crypto.generate_keypair(2048)
    data = PAYLOADS["accounts.csv"]
    stegos = []
    for name, cover in COVERS:
        sent = pipeline.hide(pub, "accounts.csv", data, cover)
        stegos.append((name, sent["stego"], sent["info"]["input_sha256"]))
    rows = []
    for label, fn in EXTRA_ATTACKS:
        rec = 0
        for name, stego, sha in stegos:
            try:
                got = crypto.decrypt_bundle(priv, lsb.extract(fn(stego)))
                rec += got[2]["output_sha256"] == sha
            except Exception:
                pass
        rows.append({"attack": label, "recovered": rec, "of": len(stegos)})
        print("G", rows[-1])
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"rsa_study": rsa_study(), "fill_study": fill_study(), "plain_vs_encrypted": plain_vs_encrypted(),
           "steganalysis": steganalysis(), "tamper_study": tamper_study(), "freshness": freshness(),
           "extra_attacks": extra_attacks()}
    (OUT / "metrics.json").write_text(json.dumps(res, indent=2))
    md = ["# Extra experiments", ""]
    md += ["## A. RSA key size", "", "| RSA bits | keygen ms (median) | wrap ms | unwrap + decrypt ms | wrapped key B | overhead B |",
           "|---|---|---|---|---|---|"]
    md += [f"| {r['rsa_bits']} | {r['keygen_ms_median']} | {r['encrypt_wrap_ms_median']} | {r['unwrap_decrypt_ms_median']} | "
           f"{r['wrapped_key_bytes']} | {r['overhead_bytes']} |" for r in res["rsa_study"]]
    fs = res["fill_study"]
    md += ["", f"## B. Fill ratio: max |measured - theory| PSNR = {fs['max_abs_dev_vs_theory_db']} dB, "
           f"max PSNR std over 5 payload seeds = {fs['max_psnr_std_db']} dB", "",
           "| Cover | Fill | Used % | PSNR mean | PSNR theory | SSIM mean |", "|---|---|---|---|---|---|"]
    md += [f"| {r['cover']} | {r['fill']} | {r['used_pct']} | {r['psnr_mean']} | {r['psnr_theory']} | {r['ssim_mean']} |"
           for r in fs["rows"]]
    md += ["", "## C. Plain vs encrypted", "", "| Payload | Kind | Bytes | Ones fraction | Entropy b/B | Changed % of bits | PSNR |",
           "|---|---|---|---|---|---|---|"]
    md += [f"| {r['payload']} | {r['kind']} | {r['bytes']} | {r['ones_fraction']} | {r['entropy_bits_per_byte']} | "
           f"{r['changed_pct_of_embedded_bits']} | {r['psnr_db']} |" for r in res["plain_vs_encrypted"]["rows"]]
    sa = res["steganalysis"]
    md += ["", f"## D. Steganalysis (chi-square flagged {sa['chi2_detected']} of {sa['chi2_total']} cases)", "",
           "| Cover | Fill | True fraction | chi2 p cover | chi2 p stego | WS cover | WS stego |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['cover']} | {r['fill']} | {r['true_fraction_of_samples']} | {r['chi2_p_cover_prefix']} | "
           f"{r['chi2_p_stego_prefix']} | {r['ws_estimate_cover']} | {r['ws_estimate_stego']} |" for r in sa["rows"]]
    t = res["tamper_study"]
    md += ["", f"## E. Tamper study: {t['trials']} single-bit flips, accepted with wrong data: {t['accepted_with_wrong_data']}", ""]
    for fld, d in t["by_field"].items():
        md.append(f"- {fld}: {d}")
    md += ["", f"## F. Freshness: {res['freshness']}", "", "## G. Extra attacks (6 covers)", "", "| Attack | Recovered |", "|---|---|"]
    md += [f"| {r['attack']} | {r['recovered']} / {r['of']} |" for r in res["extra_attacks"]]
    (OUT / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:12]))


if __name__ == "__main__":
    main()
