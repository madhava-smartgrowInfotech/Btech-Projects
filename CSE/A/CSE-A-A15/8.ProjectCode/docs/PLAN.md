# CipherVeil - build plan

**Product:** hybrid AES-GCM + RSA-OAEP encryption of a file, hidden by LSB substitution inside a PNG cover image.

## Architecture
- `backend/app` FastAPI (port 8315) + SQLAlchemy/SQLite (`data/app.db`). Services: `crypto` (AES-GCM, RSA-OAEP, bundle format), `lsb` (embed/extract/capacity), `metrics` (PSNR, SSIM, timings), `plots` (histogram, bit planes), `robustness` (JPEG, noise, crop, resize attacks), `benchmark`.
- `frontend` React + Vite + Tailwind (port 5315), `/api` proxied to the backend. JWT login.
- `ml/eval.py` writes `experiments/eval/metrics.json` (imperceptibility, capacity, speed, robustness).

## Tables
`users`(id, username, pw_hash) - `keypairs`(id, user_id, name, bits, fingerprint, public_pem, private_pem?) - `oplog`(id, user_id, op, ok, details json, created_at). No secrets in `oplog`.

## Endpoints (all under `/api`, JWT except auth)
- `auth/register`, `auth/login`, `auth/me`
- `keys` (list), `keys/generate`, `keys/import`, `keys/{id}/export?part=public|private`, `DELETE keys/{id}`
- `samples/covers`, `samples/payloads` (+ file download)
- `send` (key + payload + cover -> stego PNG, metrics, timings), `receive` (key + stego -> restored file, hashes)
- `ops/{id}/stego|cover|restored` downloads
- `analysis/{op}` metrics, `analysis/{op}/histogram.png`, `analysis/{op}/bitplanes.png`
- `robustness/{op}` (POST: run attacks), `benchmark/capacity`, `benchmark/run`
- `log`

## Screens
Landing, Login, Keys, Send, Receive, Analysis, Robustness + benchmark, Log.

## Data
No dataset. `scripts/make_samples.py` (seeded) writes cover images (public-domain / CC0 images shipped with scikit-image, resized, plus one procedurally generated landscape) to `data/covers/`, and synthetic sample payloads to `data/payloads/`.

## Defaults chosen
RSA 3072-bit, AES-256-GCM, 1 LSB per RGB channel value, sequential embedding, PNG output, 32-bit length prefix.
