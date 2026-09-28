# SkyCipher

Lightweight, chaos-based image encryption for drone links. Wavelet decomposition, chaotic key streams and
XOR diffusion, fast enough for live transmission, plus a full security lab.

## Features

- **Encryption engine** - integer Haar lifting DWT (sub-bands LL / LH / HL / HH), Henon-map permutation,
  2-D logistic key streams, XOR diffusion with a key-dependent S-box and chained addition (3 rounds),
  256-bit key + per-image nonce. Decryption is bit-exact (SHA-256 verified).
- **Image studio** - upload or pick an image; view sub-bands, the coefficient map, the cipher image and
  histograms; decrypt, try a 1-bit-wrong key, download the cipher PNG and decrypt it later.
- **Security lab** - entropy, chi-square histogram uniformity, correlation (horizontal / vertical / diagonal)
  with scatter plots, NPCR, UACI, PSNR, MSE, SSIM, key sensitivity and key space; saved reports exported as
  HTML or JSON.
- **Attack tests** - salt-and-pepper noise, Gaussian noise and cropping applied to the cipher image; the
  report shows how much of the image still recovers.
- **Live UAV link** - a sender streams encrypted drone frames (sample flight or webcam) over a WebSocket; the
  ground station decrypts and shows FPS, latency and throughput.
- **Benchmark** - encryption / decryption time against AES-256-CTR and ChaCha20 on the same images.

## Quick start (Windows)

1. Install Python 3.11+ and Node.js LTS.
2. Double-click `setup.bat` (once).
3. Double-click `run.bat` - the browser opens http://localhost:5210 (API on port 8210).

**Demo login:** `demo@skycipher.app` / `SkyCipher@2026` (pre-filled on the sign-in page).

Details, manual commands and troubleshooting: [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Evaluation results

`venv\Scripts\python ml\eval.py` -> [experiments/eval/metrics.json](experiments/eval/metrics.json).
66 images (60 VisDrone drone images up to 1024 px + 6 USC-SIPI test images); keys and nonces from a seeded
generator. Intel CPU, Python 3.11, NumPy 1.26, single process.

### Security (mean over 66 images; min-max in brackets)

| Metric | Original image | SkyCipher cipher | Ideal |
|---|---|---|---|
| Entropy (bits) | 7.1242 | **7.9996** (7.9967-7.9997) | 8 |
| Correlation - horizontal | 0.9572 | **0.0001** (-0.0020-0.0067) | 0 |
| Correlation - vertical | 0.9571 | **0.0000** (-0.0019-0.0026) | 0 |
| Correlation - diagonal | 0.9283 | **-0.0000** (-0.0017-0.0018) | 0 |
| NPCR (1-pixel change, %) | - | **99.6098** (99.6015-99.6318) | 99.6094 |
| UACI (1-pixel change, %) | - | **33.4644** (33.4263-33.5075) | 33.4635 |
| Key sensitivity - cipher NPCR for a 1-bit key change (%) | - | **99.6037** | 99.6094 |
| Decrypting with a 1-bit-wrong key - PSNR | - | **8.82 dB** (nothing recovered) | low |
| Cipher vs original - PSNR / MSE / SSIM | - | 8.82 dB / 8713 / 0.009 | low / high / ~0 |
| Decrypted vs original - PSNR / MSE | - | **infinite / 0** - all 66 bit-identical | infinite / 0 |
| Key space | - | 2^256 (+128-bit public nonce) | > 2^100 |

Histogram uniformity (chi-square < 293.25 on every channel, alpha = 0.05): mean worst-channel value 275;
80 % of images pass on all channels, in line with the ~86 % an ideal random cipher passes when three channels
are each tested at the 5 % level.

### Channel damage (10 drone images, cipher damaged then decrypted)

| Attack on the cipher image | Recovered PSNR | Pixels recovered exactly | PSNR after 3x3 median |
|---|---|---|---|
| Salt & pepper 0.1 % | 27.8 dB | 98.9 % | 34.1 dB |
| Salt & pepper 1 % | 17.9 dB | 89.0 % | 27.2 dB |
| Salt & pepper 5 % | 11.7 dB | 54.7 % | 16.8 dB |
| Cropping 6.25 % of the area | 14.7 dB | 77.3 % | 22.2 dB |
| Cropping 25 % of the area | 9.9 dB | 31.9 % | 13.4 dB |
| Gaussian noise sigma = 2 or 10 (changes ~every byte) | 8.0 dB | 0.4 % | 10.3 dB |

### Speed (median of 3 runs, 10 drone images)

| Image | SkyCipher enc / dec | AES-256-CTR enc / dec | ChaCha20 enc / dec |
|---|---|---|---|
| 256 x 256 RGB | 20.0 / 19.4 ms | 0.11 / 0.06 ms | 0.13 / 0.09 ms |
| 512 x 512 RGB | 53.3 / 58.2 ms | 0.29 / 0.20 ms | 0.37 / 0.31 ms |
| 1024 x 1024 RGB | 217.8 / 213.7 ms | 1.67 / 1.56 ms | 2.07 / 2.04 ms |

Live-link frames (480 x 270 RGB, both drone sequences): encryption **32.7 ms** and decryption **31.7 ms** per
frame on average, so about **30 fps** of encryption capacity, or about 15 fps with sender and ground station
sharing one CPU. A new key costs a one-off setup (permutation) of about 270 ms for a 1024 px image; it is
cached for as long as the key is in use. AES and ChaCha20 run as native OpenSSL code with hardware
acceleration and are roughly 130-180x faster. SkyCipher is pure NumPy and adds the wavelet, permutation and
image-level diffusion analysed above.

## Project layout

```
backend/app/          FastAPI app: main.py, db.py, auth.py, routes/, services/ (cipher, metrics, attacks, bench, live)
frontend/src/         React + Vite + Tailwind: pages/, components/, api.js
ml/eval.py            evaluation -> experiments/eval/metrics.json
scripts/              smoke_test.py (end-to-end API test), download_data.py (data sample / full dataset)
data/sample/          VisDrone images + 2 drone sequences, USC-SIPI test images
docs/                 documentation
setup.bat, run.bat    one-time setup and start
```

## Documentation

- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, users, features, screens, architecture
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - cipher design, metrics, live link, data sources and licences, data model, API
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, demo walkthrough, checks, troubleshooting
- [docs/PLAN.md](docs/PLAN.md) - build plan

## Data licences

VisDrone sample: CC BY-NC-SA 3.0 IGO (non-commercial use). USC-SIPI test images: provided for research use.
See [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md#6-data).
