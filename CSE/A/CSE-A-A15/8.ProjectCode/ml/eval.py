"""Evaluation: imperceptibility (PSNR, SSIM), capacity, speed and robustness of the combined scheme.

Runs the same services the API uses, over every committed cover, and writes
experiments/eval/metrics.json plus experiments/eval/summary.md. Fully seeded and offline.

    venv\\Scripts\\python ml\\eval.py
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import benchmark, crypto, lsb, pipeline, robustness  # noqa: E402

OUT = ROOT / "experiments" / "eval"
KEY_BITS = 3072
SIZES = [1024, 4 * 1024, 16 * 1024, 64 * 1024, 128 * 1024]
ROBUST_PAYLOAD = ROOT / "data" / "payloads" / "accounts.csv"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    covers = [(p.name, lsb.load_rgb(str(p))) for p in sorted((ROOT / "data" / "covers").glob("*.png"))]

    print(f"capacity over {len(covers)} covers ...")
    capacity = benchmark.capacity_table(covers)

    print(f"quality and speed (RSA-{KEY_BITS}, sizes {SIZES}) ...")
    bench = benchmark.run(covers, SIZES, key_bits=KEY_BITS, repeats=3)

    print("robustness ...")
    private_pem, public_pem = crypto.generate_keypair(KEY_BITS)
    payload = ROBUST_PAYLOAD.read_bytes()
    rob_rows = []
    for name, arr in covers:
        sent = pipeline.hide(public_pem, ROBUST_PAYLOAD.name, payload, arr)
        res = robustness.run_attacks(sent["stego"], private_pem, sent["info"]["input_sha256"], sent["bundle_len"])
        for r in res:
            rob_rows.append({"cover": name, "attack": r["attack"], "label": r["label"], "status": r["status"],
                             "bit_error_rate": r["bit_error_rate"]})
    attacks = {}
    for r in rob_rows:
        a = attacks.setdefault(r["attack"], {"label": r["label"], "recovered": 0, "lost": 0, "ber": []})
        a["recovered" if r["status"] == "recovered" else "lost"] += 1
        if r["bit_error_rate"] is not None:
            a["ber"].append(r["bit_error_rate"])
    robustness_summary = [
        {"attack": k, "label": v["label"], "recovered": v["recovered"], "lost": v["lost"],
         "mean_bit_error_rate": round(statistics.mean(v["ber"]), 4) if v["ber"] else None}
        for k, v in attacks.items()]

    fit = [r for r in bench["rows"] if r["fits"]]
    psnr_all = [r["psnr_db"] for r in fit]
    summary = {
        "runs": len(fit), "runs_skipped_too_large": len(bench["rows"]) - len(fit),
        "psnr_db_min": min(psnr_all), "psnr_db_mean": round(statistics.mean(psnr_all), 3),
        "ssim_min": min(r["ssim"] for r in fit), "ssim_mean": round(statistics.mean(r["ssim"] for r in fit), 6),
        "all_round_trips_byte_exact": all(r["round_trip_ok"] for r in fit),
        "median_encrypt_ms": round(statistics.median(r["encrypt_ms"] for r in fit), 2),
        "median_embed_ms": round(statistics.median(r["embed_ms"] for r in fit), 2),
        "median_extract_ms": round(statistics.median(r["extract_ms"] for r in fit), 2),
        "median_decrypt_ms": round(statistics.median(r["decrypt_ms"] for r in fit), 2),
        "max_capacity_bits_per_pixel": max(c["max_bits_per_pixel"] for c in capacity),
        "robustness_payload": ROBUST_PAYLOAD.name,
    }
    metrics = {"key_bits": KEY_BITS, "scheme": "AES-256-GCM + RSA-OAEP-SHA256 + 1-bit LSB, sequential, RGB",
               "summary": summary, "capacity": capacity, "quality_and_speed": bench["rows"],
               "robustness": robustness_summary, "robustness_detail": rob_rows}
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))

    md = ["# Evaluation summary", "", f"Scheme: {metrics['scheme']} (RSA-{KEY_BITS}).", "",
          f"- Runs: {summary['runs']} (every round trip byte-exact: {summary['all_round_trips_byte_exact']})",
          f"- PSNR: min {summary['psnr_db_min']} dB, mean {summary['psnr_db_mean']} dB",
          f"- SSIM: min {summary['ssim_min']}, mean {summary['ssim_mean']}",
          f"- Median time: encrypt {summary['median_encrypt_ms']} ms, embed {summary['median_embed_ms']} ms, "
          f"extract {summary['median_extract_ms']} ms, decrypt {summary['median_decrypt_ms']} ms",
          f"- Capacity: up to {summary['max_capacity_bits_per_pixel']} bits per pixel", "",
          "## Capacity", "", "| Cover | Pixels | Max hidden (KiB) | Bits/pixel |", "|---|---|---|---|"]
    md += [f"| {c['cover']} | {c['width']}x{c['height']} | {c['max_bundle_kib']} | {c['max_bits_per_pixel']} |" for c in capacity]
    md += ["", "## Quality and speed", "", "| Cover | Payload | Used % | PSNR dB | SSIM | Encrypt ms | Embed ms | Extract ms | Decrypt ms |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {r['cover']} | {r['payload_bytes']} B | {r['used_pct']} | {r['psnr_db']} | {r['ssim']} | {r['encrypt_ms']} | "
           f"{r['embed_ms']} | {r['extract_ms']} | {r['decrypt_ms']} |" if r["fits"] else
           f"| {r['cover']} | {r['payload_bytes']} B | does not fit | | | | | | |" for r in bench["rows"]]
    md += ["", f"## Robustness ({len(covers)} covers, {ROBUST_PAYLOAD.name})", "",
           "| Attack | Payload recovered | Payload lost | Mean LSB error rate |", "|---|---|---|---|"]
    md += [f"| {r['label']} | {r['recovered']} | {r['lost']} | {r['mean_bit_error_rate']} |" for r in robustness_summary]
    (OUT / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:12]))
    print("\nwrote", OUT / "metrics.json")


if __name__ == "__main__":
    main()
