# SkyCipher - build plan

**Architecture:** React + Vite (5210) -> `/api` proxy -> FastAPI (8210) -> NumPy cipher engine + SQLite.
Live link: UAV sender node -> WebSocket uplink (ciphertext only) -> ground-station node -> browser.

**Cipher path (F1):** image (uint8) -> integer Haar lifting DWT in Z_256 (exactly reversible, LL/HL/LH/HH
quadrants) -> key-driven Henon permutation -> 2-D logistic (sine-modulated) key streams -> XOR diffusion
chained with modular addition, forward + backward, 2 rounds. 256-bit key + public per-image/per-frame nonce.

**Endpoints:**
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/samples`, `GET /api/samples/file/{kind}/{name}`, `GET /api/keys/new`
- `POST /api/studio/encrypt`, `POST /api/studio/decrypt`, `GET /api/studio/jobs`, `GET /api/studio/jobs/{id}/cipher.png`
- `POST /api/lab/analyze`, `GET /api/lab/reports`, `GET /api/lab/reports/{id}`, `GET /api/lab/reports/{id}/export`
- `POST /api/attacks/run`
- `POST /api/bench/run`, `GET /api/bench/runs`
- `GET /api/live/sequences`, `POST /api/live/start`, `POST /api/live/stop`, `WS /api/live/uplink`, `WS /api/live/ground`, `WS /api/live/camera`

**Tables:** users, jobs (encryption jobs), reports (security lab), bench_runs.

**Screens:** Landing, Login/Register, Image studio, Security lab (+ attack tests + reports), Live link, Benchmark.

**Data:** VisDrone (Kaggle, via kagglehub) -> ~60 images + 2 short sequences in `data/sample/visdrone/`;
USC-SIPI standard test images in `data/sample/sipi/`. `scripts/download_data.py` rebuilds the sample.

**Evaluation:** `ml/eval.py` -> `experiments/eval/metrics.json` (entropy, correlation, NPCR, UACI, PSNR, MSE,
key sensitivity, timing, attack recovery, AES-CTR / ChaCha20 comparison).
