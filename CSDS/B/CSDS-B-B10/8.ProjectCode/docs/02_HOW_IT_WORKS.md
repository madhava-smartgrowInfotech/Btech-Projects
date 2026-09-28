# How SkyCipher works

## 1. Encryption pipeline (F1)

```
image (H x W x C, uint8)
  -> integer Haar lifting DWT (mod 256)           LL | HL / LH | HH quadrants, same size, exactly reversible
  -> Henon-map permutation of every coefficient    key-dependent, cached per key and image size
  -> 3 rounds of:  forward chained XOR diffusion   c[i] = c[i-1] + S[x[i] XOR k[i]]  (mod 256)
                   backward chained XOR diffusion   same, from the last byte to the first
  -> cipher image (same shape, uint8, saved as PNG)
```

Decryption runs every step backwards (difference of neighbours, inverse S-box, XOR, inverse permutation,
inverse lifting), so the recovered pixels are **bit-identical**: the SHA-256 of the pixel array matches.

### Wavelet step - integer Haar lifting

For every pair of neighbouring values `(a, b)` along the width and then the height:

```
d = b - a           (mod 256)     detail
s = a + (d >> 1)    (mod 256)     approximation
inverse: a = s - (d >> 1), b = d + a
```

Because each lifting step is inverted exactly, the transform is lossless in 8-bit arithmetic; no float
wavelet round-off can break decryption. An odd last row / column is passed through unchanged. The studio
also shows the classic floating-point Haar sub-bands from PyWavelets (`pywt.dwt2`) for inspection.

### Key streams - chaotic maps

- **Key**: 256 bits (64 hex characters). **Nonce**: 128 bits, random and public, new for every image and
  every video frame, so key streams never repeat.
- Initial conditions for 4,096 parallel chaotic trajectories are taken from SHAKE-256(key, nonce, label).
  Running many short trajectories side by side keeps the NumPy code vectorised and fast.
- **Permutation**: Henon map `x' = 1 - 1.4 x^2 + y, y' = 0.3 x` (256 burn-in iterations); the
  positions are sorted by the fractional part of the scaled trajectory.
- **S-box**: a key-dependent bijective 8-bit substitution `S`, the sort order of 256 points of the 2-D
  logistic map below.
- **Diffusion**: 2-D logistic map with sine modulation
  `x' = (sin(pi y) + 3) x (1 - x),  y' = (sin(pi x') + 3) y (1 - y)` (64 burn-in iterations); bits 16-47
  of each coordinate become 4 key-stream bytes.
- A change of one key bit changes every SHAKE-256 seed, and the chaotic maps amplify it, so the key
  streams become unrelated (key sensitivity).

### Diffusion

Each pass XORs the key stream into the data, substitutes every byte through `S` and chains the bytes with a
running sum mod 256, so byte `i` depends on every byte before it. A backward pass makes every byte depend on
every byte after it as well. Three rounds spread a one-pixel change over the whole cipher image
(NPCR ~99.61 %, UACI ~33.46 %, the values expected for an ideal cipher).

Why the S-box and the third round: plain add/XOR chains are linear on the low bit-planes, and a small difference
(e.g. +1) drifts through a running sum in small steps, so parts of the cipher kept a structured difference
(single trials reached UACI 36-41 %). The non-linear S-box makes every step difference random. A chained sum can
still cancel a difference exactly (probability 1/256 per round), which with two rounds left a block of bytes
with one constant difference in about 1 trial in 256; with three rounds that needs two cancellations
(about 1 in 65,000). Over 600 differential trials the spread of NPCR and UACI now matches an ideal random cipher.

Decryption of a pass only needs neighbouring bytes (`x[i] = S^-1[c[i] - c[i-1]] XOR k[i]`), so a byte damaged in
transit spoils only a handful of coefficients. That is why impulse noise and cropping leave most of the image
readable (F4).

## 2. Security metrics (F3)

| Metric | What it measures | Ideal for the cipher |
|---|---|---|
| Entropy | randomness of the grey-level distribution | 8 bits |
| Chi-square | histogram flatness, 255 d.o.f. | < 293.25 (alpha = 0.05) |
| Correlation H / V / D | Pearson correlation of every adjacent pixel pair | ~0 |
| NPCR / UACI | cipher change when one plain pixel changes by 1 (same key and nonce), mean of 3 trials | 99.6094 % / 33.4635 % |
| PSNR / MSE / SSIM | decrypted vs original (should be infinite / 0 / 1) and cipher vs original (should be low) | - |
| Key sensitivity | NPCR between ciphers from keys that differ in one bit; PSNR of decrypting with that key | ~99.6 % / ~8 dB |
| Key space | 2^256 keys | > 2^100 |

## 3. Attack tests (F4)

The cipher image is damaged and then decrypted with the right key: salt-and-pepper noise at 0.1 / 1 / 5 %,
Gaussian noise (sigma 2 and 10), and a blacked-out centre block covering 6.25 % or 25 % of the area. The report
gives recovered PSNR, SSIM, the share of pixels recovered exactly and the PSNR after a 3x3 median filter.
Gaussian noise changes almost every cipher byte, so the image does not recover - the expected trade-off of a
cipher with full diffusion.

## 4. Live UAV link (F5)

```
UAV sender (sample flight or webcam) --encrypt, fresh nonce--> packet = [header len | JSON header | cipher bytes]
      --WebSocket /api/live/uplink--> hub (per operator) --queue, drops stale frames-->
      ground station --decrypt with its own key--> browser (JPEG of the frame + stats) over /api/live/ground
```

The header carries the frame number, nonce, shape, capture time, on-board encryption time and a key
fingerprint (a hash of the key, so the ground station can tell a wrong key without the key being sent).
Latency is capture time -> decrypted. FPS and throughput are measured over a 2-second window.

## 5. Benchmark (F6)

The same drone images, resized to 256 / 512 / 1024 px squares, are encrypted and decrypted by SkyCipher,
AES-256-CTR and ChaCha20 (`cryptography` package, OpenSSL). The median of the repeats is reported with
throughput, the frames per second each cipher could sustain, cipher entropy and residual correlation.
AES and ChaCha20 are native code with hardware support; SkyCipher is pure NumPy, so they are faster.
SkyCipher's goal is enough speed for a live link on a small computer plus image-aware analysis.

## 6. Data

| Source | Licence | What is committed |
|---|---|---|
| VisDrone (Kaggle mirror) - https://www.kaggle.com/datasets/banuprasadb/visdrone-dataset | CC BY-NC-SA 3.0 IGO (non-commercial) | `data/sample/visdrone/images/` - 60 images from the validation split, evenly spread across clips, scaled to at most 1024 px. `data/sample/visdrone/sequences/` - 2 x 40 frames from two flights (clips 9999938 and 9999952 of the test-dev split), 640 px wide. The Kaggle mirror has only the still-image split, so these sequences are frames from one flight each, not continuous video. |
| USC-SIPI image database - https://sipi.usc.edu/database/ | Provided for research use; see the database's copyright notes | `data/sample/sipi/` - 6 standard test images from the "Miscellaneous" volume (4.2.03 mandrill, 4.2.05 F-16, 4.2.07 peppers, 5.1.12 clock, 5.2.10 stream and bridge, 7.1.02 aerial). |

`scripts/download_data.py` rebuilds the sample exactly (fixed selection; kagglehub downloads individual files).
`--full` downloads the complete 2.16 GB dataset into `data/raw/` (git-ignored). Nothing else in `data/` is
generated: `data/app.db` (SQLite) and `data/store/` (encrypted jobs) are created at run time and not committed.

## 7. Data model

| Table | Columns |
|---|---|
| users | id, email, name, password_hash (bcrypt), created_at |
| jobs | id, user_id, name, source, width, height, channels, nonce, key_fp, plain_sha256, cipher_sha256, enc_ms, plain_path, cipher_path, created_at - the key itself is never stored |
| reports | id, user_id, image_name, kind, data_json (all metrics, thumbnails, attack results), created_at |
| bench_runs | id, user_id, data_json, created_at |

## 8. API

| Method | Path | Purpose |
|---|---|---|
| POST | /api/auth/register, /api/auth/login | JWT sign-in |
| GET | /api/auth/me | current user |
| GET | /api/samples, /api/samples/file/{kind}/{name} | sample images |
| GET | /api/keys/new | random 256-bit key |
| POST | /api/studio/encrypt | encrypt upload / sample (multipart) |
| POST | /api/studio/decrypt | decrypt a job, or an uploaded cipher PNG + nonce |
| GET | /api/studio/jobs, /api/studio/jobs/{id}/cipher.png | history, cipher download |
| POST | /api/lab/analyze | full security analysis -> saved report |
| GET | /api/lab/reports, /api/lab/reports/{id}, /api/lab/reports/{id}/export?fmt=html|json | reports |
| POST | /api/attacks/run | attack suite (optionally attached to a report) |
| POST | /api/bench/run, GET /api/bench/runs | benchmark |
| GET | /api/live/sequences, /api/live/status | live link info |
| POST | /api/live/start, /api/live/stop | built-in UAV sender |
| WS | /api/live/uplink, /api/live/ground, /api/live/camera | ciphertext uplink, ground station, webcam sender |

Interactive API docs: http://localhost:8210/docs while the backend runs.
