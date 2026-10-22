# VeriVision AI

VeriVision AI is a professional web application that estimates whether an uploaded
image is likely **real** or **AI-generated**, and visually explains its decision with
Grad-CAM heatmaps, per-model votes and a robustness consistency check.

## Key capabilities

- **Heterogeneous CNN ensemble** — EfficientNet-B0 (x2 with different training
  conditions), ResNet50 at higher resolution, MobileNetV3-Large with focal loss.
- **Logit-space weighted fusion** with transparent, configurable weights
  (A1 0.35 / A2 0.15 / B 0.25 / C 0.25) plus a two-rule disagreement gating mechanism.
- **Grad-CAM explanations** generated from real model gradients, with a branch selector.
- **Robustness check** — every upload is re-tested under JPEG, resize and blur variants.
- **Model Insights page** showing measured held-out metrics, per-model comparison,
  clean-vs-degraded performance and the confusion matrix.
- **Local-first Flask app** bound to `127.0.0.1`, CPU/GPU auto-detect, no cloud inference.
- **React web app** (Vite, kit V4 "Soft Pastel Calm") with a demo login, analyzer, Grad-CAM tabs,
  insights charts, model explainer and live system status. The classic Flask pages still work.

## Architecture

| Route | Backbone | Resolution | Loss | Role |
|---|---|---|---|---|
| A1 | EfficientNet-B0 | 224×224 | CrossEntropy | Standard detector, normal augmentation |
| A2 | EfficientNet-B0 | 224×224 | CrossEntropy | Distortion-hardened twin (blur, noise, JPEG, resampling) |
| B | ResNet50 | 320×320 | CrossEntropy | Higher-resolution route with flip TTA |
| C | MobileNetV3-Large | 224×224 | Focal (γ=2) | Lightweight heterogeneous route |

Fusion: raw logits → weighted sum → softmax. Gate 1 suppresses a strongly
disagreeing Route-B outlier; Gate 2 nudges the fused logits toward a confident
B+C consensus. See `app/ensemble.py` for the deterministic implementation.

## Dataset

Primary dataset: **CIFAKE — Real and AI-Generated Synthetic Images** (via Kaggle),
organized into deterministic stratified splits (70% train / 15% val / 15% test) as
`data/{train,val,test}/{real,fake}` with class mapping `0 = REAL, 1 = AI_GENERATED`.

If the Kaggle download is unavailable (no network or credentials),
`scripts/prepare_dataset.py` generates deterministic synthetic **demo** data with the
identical schema, clearly labelled as demo data. Demo metrics are not presented as
real-world performance.

## Training workflow

```text
python scripts/prepare_dataset.py
python scripts/train_a1.py   # --epochs N --batch-size B supported
python scripts/train_a2.py
python scripts/train_b.py
python scripts/train_c.py
python scripts/evaluate.py
```

Shared logic (augmentation, focal loss, early stopping on validation F1,
CPU/GPU auto-detect, DataLoader streaming) lives in `scripts/common.py`.
Checkpoints land in `models/*.pt` with histories and `models/model_metadata.json`.

## Ensemble logic

`fused_logit = Σ weight_i × logit_i`, then softmax. B uses horizontal-flip TTA
(logit averaging). Gate parameters (`tau_b = 2.5`, `tau_c = 2.5`,
`correction = 0.75`) are engineering defaults in `app/config.py`, tunable via
`VERIVISION_GATE_*` environment variables.

## Grad-CAM explanation

Target layers: EfficientNet-B0 final conv block, ResNet50 `layer4[-1]`,
MobileNetV3-Large final feature conv. The predicted class drives gradient
computation; the heatmap is overlaid on the uploaded image. The UI states that
highlighted regions are an explanation aid, not proof of authenticity.

## Evaluation methodology

`scripts/evaluate.py` measures Accuracy, Precision, Recall, F1, ROC-AUC, Balanced
Accuracy and the confusion matrix for each branch and the ensemble on the held-out
test split, plus degraded variants (JPEG q=60, 2× resample, Gaussian blur, noise).
Results are saved to `artifacts/metrics/*.json` (+ `confusion_matrix.png`) and the
UI loads them from those files — or shows an "evaluation unavailable" state.

### Measured results (held-out test, 200 images)

> Training ran on deterministic local demo data (the public CIFAKE download was
> unreachable in the build environment), so these numbers describe demo-data
> performance only — not real-world accuracy. Robustness rows show honest
> degradation under distortion.

| Model | Accuracy | F1 | ROC-AUC |
|---|---|---|---|
| EfficientNet-B0 A1 | 100.00% | 100.00% | 100.00% |
| EfficientNet-B0 A2 | 100.00% | 100.00% | 100.00% |
| ResNet50 B | 100.00% | 100.00% | 100.00% |
| MobileNetV3-Large C | 100.00% | 100.00% | 100.00% |
| **Heterogeneous ensemble** | **100.00%** | **100.00%** | **100.00%** |

Ensemble robustness (accuracy): clean 100.0% · JPEG 86.5% · resize 49.5% ·
blur 62.0% · noise 100.0%.

Open `/insights` in the app for the live numbers loaded from `artifacts/metrics/`.

## Project structure

```text
VeriVision-AI/
├── app/               # Flask app (routes, api.py JSON API, inference, ensemble, Grad-CAM, preprocessing)
├── frontend/          # React + Vite web app (port 5414) - kit V4 copied into frontend/src
├── docs/              # FRONTEND_PLAN.md and docs/screenshots/ (captured from the running app)
├── scripts/           # prepare_dataset, train_a1/a2/b/c, evaluate, smoke_test, capture_screens
├── tests/             # pytest suite
├── models/            # checkpoints + model_metadata.json (generated)
├── artifacts/metrics/ # evaluation JSON + confusion matrix (generated)
├── data/              # train/val/test splits (generated, not committed)
├── screenshots/       # real UI screenshots
├── run.py run.bat run-docker.bat Dockerfile docker-compose.yml
├── HOW_TO_RUN.md README.md requirements.txt
└── VeriVision_AI_Documentation.pdf
```

## How to run

See **[HOW_TO_RUN.md](HOW_TO_RUN.md)**. Quickest path: double-click `run.bat`; the web app opens at
**http://localhost:5414** (API on **8414**). Demo login: `demo@verivision.ai` / `Demo@1234`.

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | status, models loaded, device |
| POST | `/api/predict` | original lightweight JSON verdict (unchanged) |
| POST | `/api/auth/login`, GET `/api/auth/me` | demo sign-in, signed bearer token |
| POST | `/api/analyze` | full analysis as JSON (verdict, branches, Grad-CAM, robustness); needs the token |
| GET | `/api/config` | ensemble weights, gates, limits, model metadata |
| GET | `/api/insights` | evaluation metrics from `artifacts/metrics/*.json` |
| GET | `/`, `/predict`, `/insights` | classic server-rendered pages (unchanged) |

Checks: `python scripts/smoke_test.py` (API + frontend proxy) and `python -m pytest tests`.

## Limitations

- AI-based assessment only — the product estimates statistical likelihood, it does
  not prove image origin or detect every generator.
- Accuracy drops on heavily compressed, tiny or out-of-distribution images; use the
  robustness consistency score as a caution signal.
- Demo fallback data (when Kaggle is unreachable) yields metrics that do not
  transfer to real photography vs. modern generators.
- CPU inference takes ~10–60 s per image (4 models + Grad-CAM + robustness variants).

## Privacy / security

- Uploads are validated (extension, size ≤ 10 MB default, successful RGB decode),
  stored only as temporary processing buffers and never executed.
- Filenames are never used as filesystem paths; no shell commands touch uploads.
- Inference runs locally; images are not sent to any external API.
- Debug mode is off; stack traces are logged server-side, users see friendly errors.

## Troubleshooting

See the Troubleshooting section of **[HOW_TO_RUN.md](HOW_TO_RUN.md)**.
