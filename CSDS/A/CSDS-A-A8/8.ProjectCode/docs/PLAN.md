# BioSight - Build Plan

**Architecture:** React + Vite (5108, proxy `/api`) -> FastAPI (8108) -> SQLite (`data/app.db`) + PyTorch models (CPU) + Gemini (reports).

**ML pipeline (`ml/`)**
- `prepare_data.py` - LGG slices -> 128x128 grayscale-stack arrays; committed sample of ~200 slices in `data/sample/lgg/`.
- `train_mri.py` - F1 I-JEPA pre-training of a tiny ViT (timm, patch 16, dim 192, depth 6) with context/target encoders (EMA) and a cross-attention predictor on masked patch blocks; F2 light conv decoder fine-tuned on 10% / 100% of masks; F3 U-Net baseline at 10% / 100% (plus a random-init ViT baseline). Writes `models/*.pt`, `experiments/mri_metrics.json` and plots.
- `train_dna.py` - F4 k-mer (k=4) tokens -> small transformer, JEPA latent prediction of masked k-mer windows, then a classification head (linear-probe + fine-tune) vs a supervised-from-scratch baseline.
- `scripts/gen_str_db.py` - F5 seeded synthetic STR database (CODIS-20 loci, published allele frequencies), 1000 profiles.
- `ml/eval.py` - collects all metrics into `experiments/eval/metrics.json`.
- `notebooks/biosight_kaggle.ipynb` - same training for a GPU re-run on Kaggle.

**Endpoints:** `POST /api/auth/register|login`, `GET /api/auth/me`, `POST /api/mri/segment` (upload -> mask overlay PNG, area, report), `GET /api/mri/samples`, `GET /api/metrics/label-efficiency`, `GET /api/metrics/all`, `POST /api/dna/classify`, `GET /api/dna/samples`, `GET /api/str/loci`, `POST /api/str/match` (ranked LRs + report), `GET /api/history`, `GET /api/health`.

**Tables:** `users(id, email, name, password_hash, created_at)`, `analyses(id, user_id, kind, summary_json, report, created_at)`.

**Screens:** Landing, Login/Register, MRI analysis, Label efficiency (chart), DNA analysis, STR matching, Model performance.

**Data:** LGG brain MRI (Kaggle, CC BY-NC-SA 4.0, sample committed + `scripts/download_data.py`); DNA classification dataset (Kaggle, committed); synthetic STR profiles (seeded generator, committed).

**Reports:** Gemini (`gemini-flash-latest`, fallback `gemini-2.5-flash`) returns JSON-structured reports; a clearly labelled deterministic summary is shown only if Gemini is unreachable.
