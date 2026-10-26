import math

import numpy as np

from app.services import benchmark, lsb, metrics, pipeline, robustness


def test_identical_images_give_infinite_psnr(cover):
    q = metrics.imperceptibility(cover, cover.copy())
    assert q["psnr_db"] is None and q["ssim"] == 1.0 and q["values_changed"] == 0


def test_psnr_matches_closed_form(cover):
    stego = cover.copy()
    stego.reshape(-1)[:1000] ^= 1                    # exactly 1000 values change by 1
    mse = 1000 / cover.size
    expected = 10 * math.log10(255 ** 2 / mse)
    assert abs(metrics.imperceptibility(cover, stego)["psnr_db"] - expected) < 0.01


def test_pipeline_round_trip_and_quality(keypair, cover):
    priv, pub = keypair
    data = b"id,name\n" * 400
    sent = pipeline.hide(pub, "x.csv", data, cover)
    got = pipeline.reveal(priv, sent["stego"])
    assert got["data"] == data and got["filename"] == "x.csv"
    assert sent["quality"]["psnr_db"] > 50 and sent["quality"]["max_abs_change"] <= 1
    assert sent["capacity"]["used_pct"] < 100


def test_theoretical_floor_about_51_db(cover):
    # random bits flip half of the touched values: PSNR >= 10log10(255^2/0.5) = 51.1 dB when every value is used
    rng = np.random.default_rng(0)
    full = rng.integers(0, 256, lsb.capacity_bytes(cover), dtype=np.uint8).tobytes()
    q = metrics.imperceptibility(cover, lsb.embed(cover, full))
    assert 50.9 < q["psnr_db"] < 51.5


def test_robustness_lossless_survives_lossy_destroys(keypair, cover):
    priv, pub = keypair
    data = b"payload " * 300
    sent = pipeline.hide(pub, "p.bin", data, cover)
    res = {r["attack"]: r for r in robustness.run_attacks(sent["stego"], priv, sent["info"]["input_sha256"], sent["bundle_len"])}
    assert res["png_resave"]["status"] == "recovered"
    assert res["crop_bottom_10"]["status"] == "recovered"
    for k in ("jpeg_q95", "jpeg_q75", "jpeg_q50", "noise_s1", "noise_s3", "resize_90", "crop_left_10"):
        assert res[k]["status"] == "lost", k
        assert 0.3 < res[k]["bit_error_rate"] < 0.7


def test_benchmark_marks_oversize_rows(cover):
    rows = benchmark.run([("c", cover)], [1024, 10 ** 6], key_bits=2048, repeats=1)["rows"]
    assert rows[0]["fits"] and rows[0]["round_trip_ok"]
    assert rows[1]["fits"] is False


def test_capacity_table_bits_per_pixel(cover):
    row = benchmark.capacity_table([("c", cover)])[0]
    assert row["max_bits_per_pixel"] == 3.0
