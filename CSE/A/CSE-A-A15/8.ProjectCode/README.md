# CipherVeil

Double-layer protection for sensitive files: **AES-256-GCM** for the data, **RSA-OAEP** for the key, and the result hidden by **LSB steganography** inside an ordinary-looking PNG. The receiver extracts, decrypts and gets the file back byte for byte.

## Features

- **Keys** - generate, import and export RSA keypairs (2048/3072/4096); a fresh AES session key for every message.
- **Send** - encrypt, wrap the key, check capacity, embed, download the stego PNG.
- **Receive** - extract, unwrap, verify the GCM tag, restore the file; input and output SHA-256 side by side.
- **Analysis** - PSNR, SSIM, histograms and bit planes before and after.
- **Robustness and benchmark** - JPEG, noise, resize and crop attacks with an honest verdict; capacity and timings per cover.
- **Log** - every operation with sizes, timings and metrics; no secrets recorded.

## Quick start

```
setup.bat      # once: venv, packages, npm install
run.bat        # backend :8315, frontend :5315, opens the browser
```

Demo login: **demo / Demo@12345**. Details in [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Evaluation results

From `ml/eval.py` (6 covers, payloads 1 KiB-128 KiB, RSA-3072, full numbers in `experiments/eval/metrics.json` and `summary.md`):

| Measure | Result |
|---|---|
| Round trips | 22 of 22 byte-exact (oversized payloads are blocked by the capacity check) |
| PSNR | min 52.5 dB, mean 61.7 dB (74.6 dB at 0.45% fill, 52.5 dB at 73% fill) |
| SSIM | min 0.9958, mean 0.9990 |
| Capacity | 3.0 bits per pixel; 14.6 KiB (200x200) to 337.5 KiB (1280x720) |
| Median time | encrypt 0.15 ms, embed 0.25 ms, extract 0.05 ms, RSA unwrap + decrypt 86 ms |

Robustness (same 6 covers, a 2.7 KB CSV payload):

| Attack | Payload recovered |
|---|---|
| Lossless PNG re-save | 6 / 6 |
| Crop bottom 10% | 6 / 6 (only while the payload sits in the remaining rows) |
| JPEG quality 95 / 75 / 50 | 0 / 6 each (about 50% of LSBs flipped) |
| Gaussian noise sigma 1 / 3 | 0 / 6 each |
| Resize to 90%, crop left 10% | 0 / 6 each |

LSB data survives lossless handling only. Send the stego image as a PNG file.

## Documentation

- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, features, limits
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - bundle format, measurements, data sources
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, run, checks
- [docs/PLAN.md](docs/PLAN.md) - architecture and endpoints

## Stack

React + Vite + Tailwind - FastAPI + SQLAlchemy/SQLite - `cryptography`, Pillow, NumPy, scikit-image, matplotlib.
