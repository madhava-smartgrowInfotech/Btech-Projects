# VeriVision AI (CSE-C-C14) - report facts

Single source of truth for the documentation run (2026-10-22). Numbers come from `experiments/cifake/metrics.json` (`scripts/run_cifake_experiments.py`), `docs/metrics/latency.json` (`scripts/measure_latency.py`), `docs/metrics/tests.json` and the code.

## 1. What the project is

- Product: **VeriVision AI**, a local Flask + React web app that estimates whether an uploaded image is real or AI-generated.
- Four CNN routes: A1 EfficientNet-B0 224 px (cross-entropy, normal augmentation), A2 EfficientNet-B0 224 px (distortion-hardened augmentation), B ResNet50 320 px (horizontal-flip TTA), C MobileNetV3-Large 224 px (focal loss gamma 2). All start from ImageNet weights; only upper blocks are fine-tuned (trainable / total parameters: A1 1,131,954 / 4,010,110; A2 3,158,302 / 4,010,110; B 14,968,834 / 23,512,130; C 2,185,522 / 4,204,594).
- Fusion: weighted sum of raw logits (weights A1 0.35, A2 0.15, B 0.25, C 0.25), softmax, two deterministic gates (Gate 1 drops route B if its margin >= 2.5 and all three others disagree; Gate 2 nudges the fused logits by 0.75 toward the B+C class when B and C agree with margins >= 2.5 and the fused direction differs). Confidence words: >= 0.85 High, >= 0.60 Moderate, else Low.
- Grad-CAM (pytorch-grad-cam 1.5.7) on routes A1 (`features[-1]`), B (`layer4[-1]`), C (`features[-1]`), target = predicted class. Robustness check: original + JPEG q60 + 2x down/up-resize + Gaussian blur 5x5, consistency k/n.
- Design reference: the gating and heterogeneous-route design follows HEDGE (arXiv 2604.03555), whose own backbones are DINOv3 / MetaCLIP2; this project uses small CNNs. The batch's declared base paper is Larue et al., CTrue (IEEE Access 2026), a one-class face-deepfake detector; the project does not implement CTrue.
- Ports: API 8414, web 5414. Demo login `demo@verivision.ai` / `Demo@1234` (signed bearer token, 12 h). No database: persisted state is model checkpoints, `model_metadata.json`, evaluation JSON/PNG.
- Machine used for every measurement: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, no GPU, Windows 11, Python 3.11.9, torch 2.14.1+cpu, torchvision 0.29.1, Flask 3.1.3, scikit-learn 1.9.1, Node 24.

## 2. Data

- **Shipped models before this run** were trained on deterministic **synthetic demo images** (500 train / 100 val / 100 test per class; `data/FALLBACK_DATA_README.txt`): 100 % on every metric, robustness JPEG 86.5 %, resize 49.5 %, blur 62.0 %, noise 100 %. Those numbers carry no real-world meaning and are kept in `docs/metrics/demo_data_metrics.json` and `models/demo_backup/`, `artifacts/demo_backup/` only.
- **Real data used in this run: CIFAKE** (Bird & Lotfi, IEEE Access 2024): 60,000 real CIFAR-10 images + 60,000 Stable Diffusion v1.4 images, 32x32 px; official split 100,000 train / 20,000 test. Copy used: Hugging Face `dragonintelligence/CIFAKE-image-dataset` (parquet, JPEG 32x32, mirror labels 0 = FAKE, 1 = REAL; the card has no licence field, the Kaggle original and other copies are tagged MIT).
- Subset (class-balanced, seed 42, `scripts/prepare_cifake.py`): train 3,000 + 3,000, validation 600 + 600 (both drawn without overlap from the official train split), test 1,000 + 1,000 (official test split). Labels: 0 REAL, 1 AI_GENERATED. Subset size is limited by CPU-only training time.
- Cross-domain probe (`scripts/prepare_xdomain.py`): 300 real photographs + 300 AI-generated images from Hugging Face `Parveshiiii/AI-vs-Real` (MIT): real = about 640 px photographs (shard 0), AI = 1024x1024 images (shard 1); generators not named by the card; re-saved as JPEG q95.
- Robustness subset: first 500 real + 500 AI images of the test subset (1,000 images), the same images in every condition.

## 3. Training (`scripts/train_*.py`, `scripts/common.py`)

- AdamW (weight decay 1e-4), cosine decay over the planned epochs, lr 3e-4 (B 2e-4), batch 32 (B 16), early stopping on validation F1 with patience 3, seeds A1 42, A2 43, B 44, C 45. Epochs run: A1 5, A2 5, C 5, B 3 (best validation F1 at epoch 2, 0.8902, kept).
- Per-route augmentation: A1 random-resized-crop (0.8-1), flip, colour jitter; A2 stronger crop, rotation, blur, noise, JPEG, down-up resize; B and C moderate hardening (blur, JPEG q50-95 at p 0.35).
- Best validation accuracy / F1: A1 0.9258 / 0.9270; A2 0.8983 / 0.9047; B 0.8775 / 0.8902; C 0.9058 / 0.9110.
- Training time on the CPU: A1 about 24 min, C about 13 min, A2 about 22 min, B about 53 min (wall clock from file timestamps; the PC was shared with other jobs, so these are upper bounds).

## 4. Held-out results (n = 2000, single run, seed 42)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | Balanced acc. | TN | FP | FN | TP | 95 % CI accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EfficientNet-B0 A1 | 0.9180 | 0.8907 | 0.9530 | 0.9208 | 0.9749 | 0.9180 | 883 | 117 | 47 | 953 | 0.905-0.930 |
| EfficientNet-B0 A2 | 0.9020 | 0.8533 | 0.9710 | 0.9083 | 0.9769 | 0.9020 | 833 | 167 | 29 | 971 | 0.888-0.915 |
| ResNet50 B | 0.8660 | 0.7928 | 0.9910 | 0.8809 | 0.9828 | 0.8660 | 741 | 259 | 9 | 991 | 0.851-0.881 |
| MobileNetV3-Large C | 0.8995 | 0.8648 | 0.9470 | 0.9041 | 0.9670 | 0.8995 | 852 | 148 | 53 | 947 | 0.885-0.912 |
| **Ensemble (deployed)** | 0.9235 | 0.8819 | 0.9780 | 0.9275 | 0.9865 | 0.9235 | 869 | 131 | 22 | 978 | 0.911-0.934 |

- Bootstrap (2,000 resamples) intervals of A1 and the ensemble overlap, so the ensemble's accuracy advantage over A1 (0.55 percentage points) is **not statistically distinguishable** on this sample; its ROC-AUC (0.9865 vs 0.9749) is higher.
- False-positive rate 13.1%, false-negative rate 2.2%: the ensemble leans toward AI_GENERATED (predicts fake for 55.5% of images; true share 50 %). Route B is most biased toward fake (recall 0.991, precision 0.793).
- Expected calibration error (15 bins): ensemble 0.0217; branches A1 0.018, A2 0.018, B 0.058, C 0.122.
- Mean |fused margin|: correct 3.56, wrong 1.09 (wrong answers sit near the decision boundary). Wrong images: 153 of 2000.
- When all four routes agree (1,624 of 2,000 images) the fused label is right 96.2% of the time; on the other 376 images it is right 76.3% (weighted sum from cached logits, differs from the deployed rule on 2 images).
- Branch agreement with the final label: A1 96.5%, A2 94.7%, B 91.6%, C 92.9%; all four routes unanimous on 81.2% of images.

### Fusion ablation (same logits, held-out test)

| Variant | Accuracy | F1 | ROC-AUC | Gate 1 fired | Gate 2 fired |
| --- | --- | --- | --- | --- | --- |
| Deployed: weights + Gate 1 + Gate 2 | 0.9235 | 0.9275 | 0.9865 | 7 | 0 |
| Weights only (no gates) | 0.9245 | 0.9285 | 0.9868 | - | - |
| Gate 1 only | 0.9235 | 0.9275 | 0.9865 | - | - |
| Gate 2 only | 0.9245 | 0.9285 | 0.9868 | - | - |
| Equal weights + gates | 0.9215 | 0.9257 | 0.9867 | - | - |
| Probability averaging (weights) | 0.9260 | 0.9299 | 0.9846 | - | - |
| Majority vote (ties -> weighted) | 0.9230 | 0.9269 | 0.9383 | - | - |

- Finding: the gates did not help here. Gate 1 fired on 7 of 2,000 images, Gate 2 on 0; removing the gates gave 92.45 % (+0.10 points, 2 images). Probability averaging scored 92.60 % accuracy but a lower ROC-AUC.

### Threshold analysis (fused fake probability; chosen on the test subset, so optimistic)

| Threshold | Accuracy | Precision | Recall | F1 | FPR | FNR |
| --- | --- | --- | --- | --- | --- | --- |
| 0.1 | 0.7705 | 0.6862 | 0.9970 | 0.8129 | 0.4560 | 0.0030 |
| 0.2 | 0.8365 | 0.7547 | 0.9970 | 0.8591 | 0.3240 | 0.0030 |
| 0.3 | 0.8845 | 0.8149 | 0.9950 | 0.8960 | 0.2260 | 0.0050 |
| 0.4 | 0.9045 | 0.8502 | 0.9820 | 0.9114 | 0.1730 | 0.0180 |
| 0.5 | 0.9235 | 0.8819 | 0.9780 | 0.9275 | 0.1310 | 0.0220 |
| 0.6 | 0.9340 | 0.9064 | 0.9680 | 0.9362 | 0.1000 | 0.0320 |
| 0.7 | 0.9410 | 0.9298 | 0.9540 | 0.9418 | 0.0720 | 0.0460 |
| 0.8 | 0.9415 | 0.9538 | 0.9280 | 0.9407 | 0.0450 | 0.0720 |
| 0.9 | 0.9030 | 0.9844 | 0.8190 | 0.8941 | 0.0130 | 0.1810 |

- The deployed threshold is 0.5. Raising it to 0.7-0.8 lowers false positives (FPR 7.2 % / 4.5 %) at some cost in recall; accuracy peaks at 94.1-94.2 %. A threshold picked on the test set is optimistic: it would need a separate validation set.

## 5. Robustness (1,000-image subset, accuracy)

| Condition | A1 | A2 | B | C | Ensemble | Ensemble predicted-fake rate |
| --- | --- | --- | --- | --- | --- | --- |
| Clean | 92.2% | 90.0% | 86.5% | 89.9% | 92.4% | 55.0% |
| JPEG q=60 | 88.9% | 88.5% | 80.3% | 86.2% | 88.3% | 59.7% |
| Resize 1/2 then back | 59.1% | 53.3% | 68.6% | 52.3% | 61.0% | 12.2% |
| Gaussian blur 5x5, sigma 1 | 59.8% | 54.6% | 69.1% | 52.5% | 58.3% | 8.9% |
| Gaussian noise sigma 6 | 84.1% | 87.4% | 74.6% | 86.8% | 86.9% | 61.9% |

- Resize and blur wipe out the cue on 32 px images (accuracy 58-61 % for the ensemble, route B holds up best at 69 %); JPEG and noise cost about 4-5 points. Distortion-hardened training (A2) did not make A2 more robust to resize or blur than A1.

## 6. Cross-domain probe (600 images, models trained on CIFAKE only)

| Model | Accuracy | ROC-AUC | Real kept REAL | AI found |
| --- | --- | --- | --- | --- |
| EfficientNet-B0 A1 | 50.7% | 0.501 | 170/300 | 134/300 |
| EfficientNet-B0 A2 | 47.8% | 0.385 | 4/300 | 283/300 |
| ResNet50 B | 48.7% | 0.215 | 1/300 | 291/300 |
| MobileNetV3-Large C | 52.2% | 0.564 | 20/300 | 293/300 |
| **Ensemble** | 51.0% | 0.499 | 163/300 | 143/300 |

- The ensemble is at chance (51.0 %, AUC 0.499) on full-resolution photographs and AI images from other sources: A2, B and C call almost everything AI-generated, A1 is a coin flip. Objective 4 (cross-generator generalisation) was measured and **not achieved**; the cause (resolution and content shift as much as generator shift) cannot be separated with this probe.

## 7. Latency (`docs/metrics/latency.json`, 8 runs each, API on 127.0.0.1, idle machine)

- `/health` 16 ms; `/api/insights` 5 ms; `/api/predict` (four routes + fusion) median 0.25 s on a 32 px image and 0.28 s on a 1024 px image; `/api/analyze` (adds three Grad-CAM overlays and three robustness variants) median 1.70 s and 1.98 s. The README's earlier '10-60 s' CPU estimate was pessimistic on this machine. Model loading happens once at start (not timed).
- Batched offline inference in the evaluation script: 283 ms per image for all four routes (batch 50).

## 7b. Edge cases (`docs/metrics/edge_cases.json`, `scripts/edge_cases.py`)

- 14 odd uploads plus the oversize body, two token checks and a determinism check all behaved as the code specifies (400/401/413 where expected); a random-noise grayscale image was called REAL at 100% but kept that verdict in only 1 of 4 robustness variants; the same image sent twice gave an identical probability. Per-call seconds in that file were inflated by parallel jobs and are not quoted.

## 8. Tests

- `python -m pytest tests`: 19 tests, 19 passed in 35 s (preprocessing 2, weight normalisation, fusion, Gate 1 x2, Gate 2 x2, response structure with fixture models, health, bad upload, and 8 API tests: login, config, insights, analyze auth, bad upload, oversize).
- `python scripts/smoke_test.py` (API + Vite proxy): 29 of 29 checks passed (login, analyze a fake and a real image with votes, Grad-CAM, robustness, error cases, classic pages, `/api/predict` contract, proxy).
- `python scripts/capture_screens.py`: every screen walked in Chrome with a clean console (no console errors, no failed requests).
- Not done: unit tests of `explainability.py` and `robustness.py`, load testing, GPU run, user study.

## 9. Endpoints

- `GET /health`
- `GET /api/config`
- `GET /api/insights`
- `GET /artifacts/confusion_matrix.png`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/analyze (token; verdict, branches, Grad-CAM, robustness)`
- `POST /api/predict (JSON verdict, no token)`
- `GET / , POST /predict, GET /insights (classic Jinja pages)`
- Upload rules: png/jpg/jpeg/webp, up to 10 MB, must decode as RGB and be at least 8x8; errors are JSON on /api paths (400, 401, 413, 500, 503).

## 10. Screenshots (`docs/screenshots/`, 1440x900, captured from the running app with the CIFAKE-trained models)

- `01_landing_light.png`
- `02_landing_dark.png`
- `03_login.png`
- `04_analyze_empty.png`
- `05_analyze_ready.png`
- `06_analyze_running.png`
- `07_result_verdict.png`
- `08_result_votes_robustness.png`
- `09_result_gradcam.png`
- `10_result_gradcam_resnet.png`
- `11_insights.png`
- `12_models.png`
- `13_status.png`
- `14_insights_dark.png`
- `15_landing_features.png`
- `16_landing_numbers.png`
- `17_result_real.png`
- `18_result_hires_ai.png`
- `19_result_hires_real.png`

## 11. Figures and diagrams

- Diagrams (`docs/diagrams/`): 01_system_architecture.png, 02_high_level_workflow.png, 03_dfd_level0.png, 04_dfd_level1.png, 05_dfd_level2.png, 06_uml_class.png, 07_sequence_analyze.png, 08_use_case.png, 09_er_diagram.png, 10_flowchart_ensemble.png, 11_training_pipeline.png
- Figures (`docs/figures/`): f01_dataset_split.png, f02_branch_metrics.png, f03_confusion_matrix.png, f04_training_curves.png, f05_roc.png, f06_fusion_ablation.png, f07_threshold_sweep.png, f08_robustness.png, f09_cross_domain.png, f10_calibration.png, f11_margin_hist.png, f12_failure_cases.png, f13_route_agreement.png, f14_gradcam_examples.png, f15_gradcam_xdomain.png

## 12. Literature

- Base paper (batch file): Larue et al., CTrue, IEEE Access vol. 14, 2026, doi 10.1109/ACCESS.2026.3702429. One-class, trained on 720 pristine FaceForensics++ videos with pseudo-fakes; EfficientNet-B4 (19.3 M parameters, 4.4 GFLOPs), 200 epochs on two V100 GPUs (about 16 h), 74 fps on an RTX 3060; reports AUC 98.9 % on FF++ and 77.0 % on DFDC (lambda = 1 ablation); cross-dataset Table 1 values are images in the PDF and are not quoted. Faces, not general images; AUC, not accuracy.
- HEDGE (arXiv 2604.03555): three routes (DINOv3 progressive training, higher-resolution route, MetaCLIP2 route), logit-space weighted fusion 7:3 and 7:3, dual gating (Gate 2 tau1 = 8, tau2 = 3, delta = 2.5), 4th place NTIRE 2026 robust AIGI detection challenge, average balanced accuracy 98.3 % on five standard benchmarks (JPEG 97.8 %, resize 98.4 %); ablation (competition set, robust F1): full 80.52, + gates 80.89; trained on 8 H800 GPUs.
- Empirical study (arXiv 2511.02791): ten forensic methods, seven GAN/diffusion datasets, accuracy / AP / AUC, Grad-CAM and confidence-curve analysis; reports strong in-distribution but weaker cross-model transfer.
- Batch survey items 4-7 could not be verified online; they are listed in the references marked [unverified] and no number from them is used.

## 13. Comparison with the base paper (state plainly)

- Different task (general images vs faces), different data (CIFAKE 32 px subset vs FF++/DFDC), different training regime (supervised, 6,000 images, 3-5 epochs, CPU vs one-class, 720 videos, 200 epochs, two V100), different metric emphasis (accuracy/F1 vs AUC). The only like-for-like metric is AUC: 98.65 % here on CIFAKE (in-domain) against 98.9 % on FF++ (in-domain) in the paper; cross-dataset, the paper's DFDC AUC is 77.0 % and this project's cross-domain AUC is 49.9 %. The numbers are not comparable evidence of one method being better.

## 14. Honest gaps

- Single training run per route (seed 42-45); no seed study, so the ranking of routes carries run-to-run uncertainty beyond the bootstrap interval.
- Training used 6,000 of the 100,000 CIFAKE training images and 3-5 epochs because of CPU-only hardware; a full-data run would probably score higher.
- CIFAKE images are 32x32 JPEG, so conclusions do not transfer to modern high-resolution generators; the cross-domain probe shows chance performance.
- One generator (Stable Diffusion 1.4) in the training data; no per-generator breakdown, no GAN or newer diffusion model.
- Gate thresholds (2.5, 2.5, 0.75) are the product's engineering defaults, not tuned; the gates did not improve results here.
- Threshold analysis and fusion-weight choices were evaluated on the test subset; no separate validation of the fused operating point.
- Grad-CAM maps were inspected qualitatively only; there is no quantitative faithfulness test (for example deletion/insertion).
- No user study, no GPU timing, no load test, no adversarial attack test.
- The deployed Insights page shows the CIFAKE-subset metrics; the shipped README still describes the older demo-data numbers unless updated.
