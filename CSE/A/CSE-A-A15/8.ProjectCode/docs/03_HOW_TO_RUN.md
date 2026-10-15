# CipherVeil - how to run

Needs Windows with Python 3.11+, Node.js LTS and Git. No API keys, datasets or hardware; it runs offline.

## First time

```
setup.bat
```

`setup.bat` creates `.env` from `.env.example` if it is missing. `.env` is git-ignored and stays on your machine: set a real `JWT_SECRET` (16+ characters) in it. Ports are `BACKEND_PORT=8315` and `FRONTEND_PORT=5315`.

Creates `venv`, installs the Python packages, regenerates the sample covers if `data\covers` is missing, and runs `npm install` in `frontend`.

## Start

```
run.bat
```

Opens two windows (backend on **8315**, frontend on **5315**) and the browser at http://localhost:5315. Ports are set in `.env`.

Demo login: **demo / Demo@12345** (created automatically on first start). You can also register your own account.

## Try it

1. **Keys** - generate a keypair.
2. **Send** - pick the key, a sample file (for example `confidential_memo.pdf`) and a cover; press *Encrypt and hide*. Download the PNG.
3. **Analysis** - PSNR above 50 dB, SSIM near 1, near-identical histograms.
4. **Receive** - choose the key and the stego image; the two SHA-256 values match and the file downloads.
5. **Robustness** - run the tests; JPEG recompression loses the payload, which is why the image must stay a PNG.
6. **Log** - every step with sizes, timings and metrics.

## Checks

With the backend running:

```
venv\Scripts\python scripts\smoke_test.py
venv\Scripts\python ml\eval.py
cd frontend && npm run build
```

`ml\eval.py` writes `experiments/eval/metrics.json` and `summary.md`.

## Troubleshooting

- *Port already in use*: another program holds 8315 or 5315; close it or change the ports in `.env`.
- *Blank page or 502*: the backend window did not start; read its output.
- *"This cover holds only N bytes"*: choose a larger image or a smaller file.
- *Recipient cannot open the image*: it was probably re-encoded by a messaging app; send it as a file or archive.
