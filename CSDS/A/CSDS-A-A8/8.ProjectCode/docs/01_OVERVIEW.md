# BioSight - Overview

BioSight does label-efficient medical-image segmentation and DNA profile analysis with joint-embedding predictive learning (JEPA), and writes a structured report for each result.

## The problem
- Tumour segmentation and DNA analysis both depend on expensive expert-labelled data.
- Reconstruction-based self-supervised methods spend capacity on pixel/token detail rather than meaning.
- Imaging and genomic workflows usually live in separate, unrelated pipelines.
- Raw model outputs (masks, probabilities, likelihood ratios) are hard for clinicians and forensic analysts to read.

## What BioSight does
| # | Feature | What the user sees |
|---|---------|--------------------|
| F1 | JEPA pre-training | A small ViT pre-trained on brain-MRI slices by predicting the *features* of masked patch blocks. No masks are used. |
| F2 | Few-label segmentation | A light decoder fine-tuned on only 10% of the masks. The app shows the tumour overlay, area (px and mm²), share of brain, location and confidence. |
| F3 | Label-efficiency comparison | Dice / IoU at 10% and 100% of the masks versus a supervised U-Net, an MAE (reconstruction) pre-trained ViT and a ViT from scratch, shown as a chart. |
| F4 | DNA encoder and classification | k-mer (4-mer) tokens with the same latent-prediction objective. Classifies STR repeat type (none/di/tri/tetra/penta) and organism class, plus an exact tandem-repeat scan. |
| F5 | STR profile matching | A query profile over the 20 CODIS core loci is ranked against 1,000 seeded synthetic references with theta-corrected likelihood ratios. |
| F6 | Structured reports | Gemini writes a JSON-structured report (summary, findings, measurements, interpretation, limitations, recommendation) from the real model output. |

## Users
- Radiology and research teams who need tumour segmentation with few annotations.
- Forensic DNA laboratories matching STR profiles.
- Bioinformatics researchers exploring learned representations.

## Screens
1. Landing
2. Sign in / register (a demo account is provided)
3. MRI analysis: upload or pick a sample slice to get the mask overlay, area and report
4. Label efficiency: the Dice / IoU chart and a table of all runs
5. DNA analysis: repeat type, organism class, repeat scan and report
6. STR matching: ranked candidates with LRs, per-locus comparison and report
7. Model performance: every held-out metric, the STR evaluation and your recent analyses

## Architecture
```
React + Vite + Tailwind (5108) --/api proxy--> FastAPI (8108) --> SQLite (users, analyses)
                                                   |--> PyTorch models on CPU (models/*.pt)
                                                   |--> STR database + NIST allele frequencies (data/str)
                                                   '--> Gemini API (structured reports)
```

Out of scope for this build: LoRA fine-tuning of a local LLM (Gemini writes the reports), an embedding explorer, and VNTR analysis beyond STRs.
