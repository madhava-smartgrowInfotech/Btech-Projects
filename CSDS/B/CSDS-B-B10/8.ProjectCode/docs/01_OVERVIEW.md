# SkyCipher - Overview

SkyCipher is lightweight, chaos-based image encryption for drone links. It decomposes each image with a
wavelet transform, scrambles it with chaotic key streams and diffuses it with XOR - fast enough for live
video - and ships with a security lab so auditors can verify the numbers themselves.

## The problem

- UAV images sent over wireless links can be intercepted or modified.
- Strong conventional ciphers are heavy for small on-board computers; weak image ciphers leave pixel
  correlation that attackers can exploit.
- Lightweight schemes are often published without a thorough security evaluation.

## Who uses it

| User | What they do in SkyCipher |
|---|---|
| Drone operators (survey, agriculture, inspection, disaster response) | Encrypt imagery before it leaves the aircraft; run the live link |
| Ground-station operators | Decrypt and view incoming frames, check latency and frame rate |
| Security auditors | Run the security lab and attack tests, export reports, compare speed with AES / ChaCha20 |

## Features

| # | Feature | Where |
|---|---|---|
| F1 | Encryption engine: integer Haar lifting DWT -> Henon permutation -> 2-D logistic key streams -> XOR diffusion (key-dependent S-box + chained add, 3 rounds), 256-bit key, bit-exact decryption | `backend/app/services/cipher.py` |
| F2 | Image studio: upload or pick an image, encrypt, view sub-bands / coefficient map / cipher / histograms, decrypt and compare SHA-256, download the cipher PNG and decrypt it later | Image studio screen |
| F3 | Security lab: entropy, chi-square histogram uniformity, correlation (H / V / D) with scatter plots, NPCR, UACI, PSNR, MSE, SSIM, key sensitivity, key space, timing; saved reports exported as HTML or JSON | Security lab screen |
| F4 | Attack tests: salt-and-pepper noise, Gaussian noise and cropping on the cipher image, recovered PSNR / SSIM / % pixels intact, with and without a median filter | Security lab screen |
| F5 | Live UAV link: a sender streams encrypted drone frames (sample flight or webcam) over a WebSocket; the ground station decrypts them and shows FPS, latency and throughput | Live link screen |
| F6 | Benchmark: encryption / decryption time and throughput vs AES-256-CTR and ChaCha20 on the same images | Benchmark screen |

## Screens

1. Landing - what SkyCipher does.
2. Login / register - demo account pre-filled.
3. Image studio - F1 + F2.
4. Security lab and report - F3 + F4, saved reports, HTML / JSON export.
5. Live link - UAV sender and ground station side by side.
6. Benchmark - speed comparison table and charts.

## Architecture

```
React + Vite (5210) --/api proxy--> FastAPI (8210) --> NumPy cipher engine, metrics, attacks, benchmark
                                          |                SQLite (users, jobs, reports, bench_runs)
UAV sender --WebSocket uplink (ciphertext only)--> hub --> ground station --WebSocket--> browser
```

Out of scope for this release: X25519 session-key exchange, per-frame HMAC tamper detection, batch folder
mode and a mission log.
