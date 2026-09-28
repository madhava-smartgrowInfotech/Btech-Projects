# BioSight - How it works

## 1. Data

| Dataset | Source | Licence | What is committed |
|---------|--------|---------|-------------------|
| Brain MRI segmentation (LGG), 110 patients, 3,929 FLAIR-based RGB slices with expert masks | Kaggle `mateuszbuda/lgg-mri-segmentation` (TCGA / TCIA) | CC BY-NC-SA 4.0 | `data/sample/lgg/`: 200 slices (140 with tumour, 60 without) from **test** patients, as 256×256 PNGs plus masks and `manifest.csv`. The full ~1 GB set comes from `scripts/download_data.py`. |
| DNA classification dataset, 3,000 sequences of 100 bp with 4 class labels | Kaggle `miadul/dna-classification-dataset` | As published on Kaggle | Full CSV: `data/dna/synthetic_dna_dataset.csv` |
| STR repeat reads, 5,000 sequences of 100 bp, 5 classes | Seeded generator `scripts/gen_repeat_sequences.py` (seed 7) | Generated | `data/dna/repeat_sequences.csv` |
| STR allele frequencies, 29 loci | NIST U.S. population dataset (N = 1,036, 2017 revision; Steffen et al.), CSV from the PODFRIDGE repository | Public (NIST data) | `data/str/nist1036_allele_freqs.csv`, plus `codis20_frequencies.json` for the 20 CODIS core loci |
| STR reference database, 1,000 profiles | Seeded generator `scripts/gen_str_db.py` (seed 2026). Hardy-Weinberg draws from the NIST frequencies. | Generated (sample data) | `data/str/str_database.json` |

**Splits.** MRI is split by patient (seed 42): 88 training patients (3,169 slices) and 22 test patients (760 slices), so no test patient is ever seen in training. Each DNA task gets a seeded 80/20 random split.

**A note on the DNA classification dataset.** Its sequences are random with respect to their labels. A k-mer logistic regression, the scratch model, the MLM model and the JEPA model all score at chance (about 25% for 4 classes) on held-out data. BioSight trains on it and reports this honestly. To show that the DNA encoder captures STR patterns (the forensic objective), it also learns the seeded STR repeat-type task.

## 2. Models

### 2.1 JEPA core (F1, `ml/nets.py`, `ml/train_mri.py`)
- **Tokenisation.** Images: 128×128×3 slices cut into 8×8 ViT patches, giving a 16×16 grid of 256 tokens (timm `PatchEmbed` and `Block`). DNA: overlapping 4-mers over a 99 bp window, giving 96 tokens from a vocabulary of 256 plus PAD and MASK.
- **Encoders.** The same `TokenEncoder` class serves both domains, with fixed sin-cos position embeddings. Images use dim 128, depth 6 and 4 heads (1.2 M parameters). DNA uses dim 128 and depth 4.
- **Context and target encoders.** The context encoder sees only the visible tokens. The target encoder is an EMA copy (momentum 0.996 rising to 1.0) that sees the whole input. Its layer-normalised outputs at the masked positions are the targets.
- **Masking.** Images use I-JEPA multi-block masking: 4 target blocks, each 15-20% of the grid with aspect ratio 0.75-1.5, and a context block of 85-100% minus the targets. DNA uses 3 contiguous target spans of 10-15% of the tokens each.
- **Multi-scale cross-attention predictor.** Queries are a learned mask token plus the positional embedding of each target position. Each layer cross-attends to the context at two scales: the fine context tokens, and coarse tokens made by average-pooling the context over 2×2 patch cells (images) or 4-token cells (DNA). A self-attention block follows. The loss is smooth-L1 in latent space, so there is no pixel or token reconstruction.
- **Budget (CPU).** 10 epochs over 3,169 unlabelled slices, batch 32, AdamW at 5e-4 with cosine decay. The kept encoder is the EMA target encoder.

### 2.2 Few-label segmentation (F2)
- **Decoder.** A light decoder turns the 16×16 token map into mask logits: a 1×1 projection to 96 channels, then three stages of ×2 bilinear upsampling with 3×3 conv, BN and ReLU (64, 32, 16 channels), giving 128×128 logits.
- **Fine-tuning.** The whole network is fine-tuned with BCE plus Dice loss, horizontal-flip augmentation, encoder learning rate 2e-4 and decoder learning rate 1e-3. It runs 300 steps on the 10% label budget (317 slices) and 500 steps on 100%.
- **Inference.** The slice is resized to 128×128, and the probability map is upsampled back to the original size and thresholded at 0.5. From the mask the API computes area (pixels, and mm² using the pixel spacing the user supplies), share of brain area (pixels above an intensity floor), bounding box, centroid, image quadrant, maximum extent and mean confidence.

### 2.3 Baselines and label-efficiency runs (F3)
| Run | Encoder initialisation |
|-----|------------------------|
| `jepa_{10,100}` | JEPA pre-trained ViT (BioSight) |
| `mae_{10,100}` | ViT pre-trained as a masked autoencoder (75% masking, pixel reconstruction, same epochs). This is the reconstruction-based baseline. |
| `scratch_{10,100}` | Randomly initialised ViT with the same decoder |
| `unet_{10,100}` | Supervised U-Net (16-32-64-128 channels, 1.9 M parameters) |

Metrics come from all 760 test slices of unseen patients. Dice and IoU are pooled over pixels. The mean Dice over tumour-bearing slices is also reported.

### 2.4 DNA encoder and classification (F4, `ml/train_dna.py`)
- **Pre-training.** JEPA and MLM (the reconstruction baseline: predict the masked 4-mer ids) pre-train on 6,400 unlabelled training sequences from both DNA sets, for 15 epochs each.
- **Classification.** A mean-pooled classification head is fine-tuned with 10% or 100% of the labels. The runs cover JEPA, MLM and scratch initialisation, plus a frozen JEPA linear probe.
- **Inference.** A sequence longer than 99 bp is cut into windows with stride 50. Repeat type is taken from the window with the strongest repeat signal. Organism class uses the mean probability over windows and comes with a low-reliability note.
- **Parsing and statistics.** Biopython handles FASTA parsing, GC fraction and reverse complement. A regex scan also lists exact tandem repeats (period 2-6, at least 4 copies).

### 2.5 STR matching (F5, `backend/app/services/str_match.py`)
For every locus typed in both the query and a reference:

- LR = P(query | same source) / P(query | unrelated person)
- P(query | same source) uses an allele-typing error model with e = 0.001: (1-e)² if both alleles are shared, e(1-e) if one is shared, e² if none.
- P(query | unrelated person) is the NRC II 4.10 genotype probability with θ = 0.01. Unseen alleles get a minimum frequency of 5/2N.
- The combined LR is the product over loci. Candidates are ranked by log10 LR and labelled with a verbal scale: <0 favours unrelated, <1 weak, <2 moderate, <4 moderately strong, <6 strong, ≥6 very strong.
- The random match probability of the query is also reported.

### 2.6 Structured reports (F6, `backend/app/services/reports.py`)
- **Input.** The compact model output (never the images) goes to Gemini's REST API with `responseMimeType: application/json`. The output schema is title, summary, findings, measurements, interpretation, limitations and recommendation.
- **Prompts.** Each is domain-specific (radiology, forensic or bioinformatics) and tells the model to use only the numbers it is given.
- **Models.** `GEMINI_MODEL` (gemini-flash-latest) is tried first, then `GEMINI_FALLBACK_MODELS`. The model that last succeeded is tried first for 10 minutes.
- **Fallback.** If every model fails, the UI shows a plain summary built from the same numbers, clearly labelled as such.

## 3. API
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register`, `/api/auth/login` | JWT sign-in (bcrypt password hashes) |
| GET | `/api/auth/me` | Current user |
| GET | `/api/mri/models`, `/api/mri/samples`, `/api/mri/samples/{file}` | Model list and sample slices |
| POST | `/api/mri/segment` (multipart) and `/api/mri/segment-sample` | Segmentation, measurements and report |
| GET | `/api/metrics/label-efficiency`, `/api/metrics/all`, `/api/metrics/plot/{name}` | Evaluation results |
| GET | `/api/dna/samples` | Sample sequences |
| POST | `/api/dna/classify` | DNA analysis and report |
| GET | `/api/str/loci`, `/api/str/sample-query` | Loci, alleles and a sample query |
| POST | `/api/str/match` | Ranked matches and report |
| GET | `/api/history`, `/api/history/{id}` | Saved analyses |

**Tables.** `users(id, email, name, password_hash, created_at)` and `analyses(id, user_id, kind, title, summary JSON, report JSON, created_at)`.

## 4. Evaluation
`ml/eval.py` gathers the MRI and DNA results. It also re-scores the saved MRI models on the committed sample slices on CPU, and evaluates STR matching on 200 simulated true-source queries (10-20 typed loci, 3% typing errors) and 200 non-contributor queries compared against all 1,000 references. Everything is written to `experiments/eval/metrics.json`. The numbers are listed in the README.
