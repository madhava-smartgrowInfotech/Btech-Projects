"""Writes docs/REPORT_FACTS.md from the measured results (experiments/cifake/metrics.json, docs/metrics/*.json).

    python -m scripts.docs.make_report_facts
Everything the documents say must agree with this file.
"""

import os

from . import facts as F

BN = F.BRANCH_NAME


def row(*c):
    return "| " + " | ".join(str(x) for x in c) + " |"


def main():
    L = []
    a = L.append
    e, br, V = F.ENS, F.BR, F.VARIANTS
    a("# VeriVision AI (CSE-C-C14) - report facts")
    a("")
    a("Single source of truth for the documentation run (2026-10-22). Numbers come from `experiments/cifake/metrics.json` "
      "(`scripts/run_cifake_experiments.py`), `docs/metrics/latency.json` (`scripts/measure_latency.py`), `docs/metrics/tests.json` and the code.")
    a("")
    a("## 1. What the project is")
    a("")
    a("- Product: **VeriVision AI**, a local Flask + React web app that estimates whether an uploaded image is real or AI-generated.")
    a("- Four CNN routes: A1 EfficientNet-B0 224 px (cross-entropy, normal augmentation), A2 EfficientNet-B0 224 px (distortion-hardened augmentation), "
      "B ResNet50 320 px (horizontal-flip TTA), C MobileNetV3-Large 224 px (focal loss gamma 2). All start from ImageNet weights; only upper blocks are fine-tuned "
      "(trainable / total parameters: A1 1,131,954 / 4,010,110; A2 3,158,302 / 4,010,110; B 14,968,834 / 23,512,130; C 2,185,522 / 4,204,594).")
    a("- Fusion: weighted sum of raw logits (weights A1 0.35, A2 0.15, B 0.25, C 0.25), softmax, two deterministic gates (Gate 1 drops route B if its margin >= 2.5 and all three others disagree; "
      "Gate 2 nudges the fused logits by 0.75 toward the B+C class when B and C agree with margins >= 2.5 and the fused direction differs). Confidence words: >= 0.85 High, >= 0.60 Moderate, else Low.")
    a("- Grad-CAM (pytorch-grad-cam 1.5.7) on routes A1 (`features[-1]`), B (`layer4[-1]`), C (`features[-1]`), target = predicted class. Robustness check: original + JPEG q60 + 2x down/up-resize + Gaussian blur 5x5, consistency k/n.")
    a("- Design reference: the gating and heterogeneous-route design follows HEDGE (arXiv 2604.03555), whose own backbones are DINOv3 / MetaCLIP2; this project uses small CNNs. "
      "The batch's declared base paper is Larue et al., CTrue (IEEE Access 2026), a one-class face-deepfake detector; the project does not implement CTrue.")
    a("- Ports: API 8414, web 5414. Demo login `demo@verivision.ai` / `Demo@1234` (signed bearer token, 12 h). No database: persisted state is model checkpoints, `model_metadata.json`, evaluation JSON/PNG.")
    a("- Machine used for every measurement: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, no GPU, Windows 11, Python 3.11.9, torch 2.14.1+cpu, torchvision 0.29.1, Flask 3.1.3, scikit-learn 1.9.1, Node 24.")
    a("")
    a("## 2. Data")
    a("")
    a("- **Shipped models before this run** were trained on deterministic **synthetic demo images** (500 train / 100 val / 100 test per class; `data/FALLBACK_DATA_README.txt`): "
      "100 % on every metric, robustness JPEG 86.5 %, resize 49.5 %, blur 62.0 %, noise 100 %. Those numbers carry no real-world meaning and are kept in `docs/metrics/demo_data_metrics.json` and `models/demo_backup/`, `artifacts/demo_backup/` only.")
    a("- **Real data used in this run: CIFAKE** (Bird & Lotfi, IEEE Access 2024): 60,000 real CIFAR-10 images + 60,000 Stable Diffusion v1.4 images, 32x32 px; official split 100,000 train / 20,000 test. "
      "Copy used: Hugging Face `dragonintelligence/CIFAKE-image-dataset` (parquet, JPEG 32x32, mirror labels 0 = FAKE, 1 = REAL; the card has no licence field, the Kaggle original and other copies are tagged MIT).")
    a("- Subset (class-balanced, seed 42, `scripts/prepare_cifake.py`): train 3,000 + 3,000, validation 600 + 600 (both drawn without overlap from the official train split), "
      "test 1,000 + 1,000 (official test split). Labels: 0 REAL, 1 AI_GENERATED. Subset size is limited by CPU-only training time.")
    a("- Cross-domain probe (`scripts/prepare_xdomain.py`): 300 real photographs + 300 AI-generated images from Hugging Face `Parveshiiii/AI-vs-Real` (MIT): real = about 640 px photographs (shard 0), AI = 1024x1024 images (shard 1); generators not named by the card; re-saved as JPEG q95.")
    a("- Robustness subset: first 500 real + 500 AI images of the test subset (1,000 images), the same images in every condition.")
    a("")
    a("## 3. Training (`scripts/train_*.py`, `scripts/common.py`)")
    a("")
    a("- AdamW (weight decay 1e-4), cosine decay over the planned epochs, lr 3e-4 (B 2e-4), batch 32 (B 16), early stopping on validation F1 with patience 3, seeds A1 42, A2 43, B 44, C 45. Epochs run: A1 5, A2 5, C 5, B 3 (best validation F1 at epoch 2, 0.8902, kept).")
    a("- Per-route augmentation: A1 random-resized-crop (0.8-1), flip, colour jitter; A2 stronger crop, rotation, blur, noise, JPEG, down-up resize; B and C moderate hardening (blur, JPEG q50-95 at p 0.35).")
    a("- Best validation accuracy / F1: " + "; ".join(f"{F.BRANCH_SHORT[b]} {max(h['val_acc']):.4f} / {max(h['val_f1']):.4f}" for b, h in F.HIST.items()) + ".")
    a("- Training time on the CPU: A1 about 24 min, C about 13 min, A2 about 22 min, B about 53 min (wall clock from file timestamps; the PC was shared with other jobs, so these are upper bounds).")
    a("")
    a(f"## 4. Held-out results (n = {F.N_TEST}, single run, seed 42)")
    a("")
    a(row("Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "Balanced acc.", "TN", "FP", "FN", "TP", "95 % CI accuracy"))
    a(row(*["---"] * 12))
    for b in F.BRANCHES:
        m = br[b]
        cm = m["confusion_matrix"]
        a(row(BN[b], F.f4(m["accuracy"]), F.f4(m["precision"]), F.f4(m["recall"]), F.f4(m["f1"]), F.f4(m["roc_auc"]), F.f4(m["balanced_accuracy"]), cm[0][0], cm[0][1], cm[1][0], cm[1][1],
              f"{F.CI[b][0]:.3f}-{F.CI[b][1]:.3f}"))
    cm = e["confusion_matrix"]
    a(row("**Ensemble (deployed)**", F.f4(e["accuracy"]), F.f4(e["precision"]), F.f4(e["recall"]), F.f4(e["f1"]), F.f4(e["roc_auc"]), F.f4(e["balanced_accuracy"]), cm[0][0], cm[0][1], cm[1][0], cm[1][1],
          f"{F.CI['ensemble'][0]:.3f}-{F.CI['ensemble'][1]:.3f}"))
    a("")
    a(f"- Bootstrap (2,000 resamples) intervals of A1 and the ensemble overlap, so the ensemble's accuracy advantage over A1 ({(e['accuracy'] - br['a1']['accuracy']) * 100:.2f} percentage points) is **not statistically distinguishable** on this sample; its ROC-AUC (0.9865 vs 0.9749) is higher.")
    a(f"- False-positive rate {F.pct(e['fpr'])}, false-negative rate {F.pct(e['fnr'])}: the ensemble leans toward AI_GENERATED (predicts fake for {F.pct(e['predicted_fake_rate'])} of images; true share 50 %). Route B is most biased toward fake (recall 0.991, precision 0.793).")
    a(f"- Expected calibration error (15 bins): ensemble {F.ECE:.4f}; branches " + ", ".join(f"{F.BRANCH_SHORT[b]} {v:.3f}" for b, v in M_ECE().items()) + ".")
    a(f"- Mean |fused margin|: correct {F.ERR['mean_abs_margin_correct']:.2f}, wrong {F.ERR['mean_abs_margin_wrong']:.2f} (wrong answers sit near the decision boundary). Wrong images: {F.ERR['n_wrong']} of {F.N_TEST}.")
    a("- Branch agreement with the final label: " + ", ".join(f"{F.BRANCH_SHORT[b]} {F.pct(v)}" for b, v in F.AGREE.items()) + f"; all four routes unanimous on {F.pct(F.UNANIMOUS)} of images.")
    a("")
    a("### Fusion ablation (same logits, held-out test)")
    a("")
    a(row("Variant", "Accuracy", "F1", "ROC-AUC", "Gate 1 fired", "Gate 2 fired"))
    a(row(*["---"] * 6))
    names = {"full": "Deployed: weights + Gate 1 + Gate 2", "no_gates": "Weights only (no gates)", "gate1_only": "Gate 1 only", "gate2_only": "Gate 2 only",
             "equal_weights": "Equal weights + gates", "prob_avg": "Probability averaging (weights)", "majority": "Majority vote (ties -> weighted)"}
    for k, n in names.items():
        v = V[k]
        a(row(n, F.f4(v["accuracy"]), F.f4(v["f1"]), F.f4(v["roc_auc"]), v.get("gate1_fired", "-"), v.get("gate2_fired", "-")))
    a("")
    a("- Finding: the gates did not help here. Gate 1 fired on 7 of 2,000 images, Gate 2 on 0; removing the gates gave 92.45 % (+0.10 points, 2 images). Probability averaging scored 92.60 % accuracy but a lower ROC-AUC.")
    a("")
    a("### Threshold analysis (fused fake probability; chosen on the test subset, so optimistic)")
    a("")
    a(row("Threshold", "Accuracy", "Precision", "Recall", "F1", "FPR", "FNR"))
    a(row(*["---"] * 7))
    for s in F.SWEEP:
        a(row(s["threshold"], F.f4(s["accuracy"]), F.f4(s["precision"]), F.f4(s["recall"]), F.f4(s["f1"]), F.f4(s["fpr"]), F.f4(s["fnr"])))
    a("")
    a("- The deployed threshold is 0.5. Raising it to 0.7-0.8 lowers false positives (FPR 7.2 % / 4.5 %) at some cost in recall; accuracy peaks at 94.1-94.2 %. A threshold picked on the test set is optimistic: it would need a separate validation set.")
    a("")
    a("## 5. Robustness (1,000-image subset, accuracy)")
    a("")
    a(row("Condition", "A1", "A2", "B", "C", "Ensemble", "Ensemble predicted-fake rate"))
    a(row(*["---"] * 7))
    for c, lab in (("clean_subset", "Clean"), ("jpeg", "JPEG q=60"), ("resize", "Resize 1/2 then back"), ("blur", "Gaussian blur 5x5, sigma 1"), ("noise", "Gaussian noise sigma 6")):
        r = F.ROB[c]
        a(row(lab, *[F.pct(r["branches"][b]["accuracy"]) for b in F.BRANCHES], F.pct(r["ensemble"]["accuracy"]), F.pct(r["ensemble"]["predicted_fake_rate"])))
    a("")
    a("- Resize and blur wipe out the cue on 32 px images (accuracy 58-61 % for the ensemble, route B holds up best at 69 %); JPEG and noise cost about 4-5 points. Distortion-hardened training (A2) did not make A2 more robust to resize or blur than A1.")
    a("")
    a("## 6. Cross-domain probe (600 images, models trained on CIFAKE only)")
    a("")
    x = F.XD
    a(row("Model", "Accuracy", "ROC-AUC", "Real kept REAL", "AI found"))
    a(row(*["---"] * 5))
    for b in F.BRANCHES:
        m = x["branches"][b]
        c = m["confusion_matrix"]
        a(row(BN[b], F.pct(m["accuracy"]), F.f3(m["roc_auc"]), f"{c[0][0]}/300", f"{c[1][1]}/300"))
    m = x["ensemble"]
    c = m["confusion_matrix"]
    a(row("**Ensemble**", F.pct(m["accuracy"]), F.f3(m["roc_auc"]), f"{c[0][0]}/300", f"{c[1][1]}/300"))
    a("")
    a("- The ensemble is at chance (51.0 %, AUC 0.499) on full-resolution photographs and AI images from other sources: A2, B and C call almost everything AI-generated, A1 is a coin flip. "
      "Objective 4 (cross-generator generalisation) was measured and **not achieved**; the cause (resolution and content shift as much as generator shift) cannot be separated with this probe.")
    a("")
    a("## 7. Latency (`docs/metrics/latency.json`, 8 runs each, API on 127.0.0.1, idle machine)")
    a("")
    lt = F.LATENCY
    a(f"- `/health` {lt['health']['median'] * 1000:.0f} ms; `/api/insights` {lt['insights']['median'] * 1000:.0f} ms; `/api/predict` (four routes + fusion) median {lt['predict_cifake_32px']['median']:.2f} s on a 32 px image and {lt['predict_photo_1024px']['median']:.2f} s on a 1024 px image; "
      f"`/api/analyze` (adds three Grad-CAM overlays and three robustness variants) median {lt['analyze_cifake_32px']['median']:.2f} s and {lt['analyze_photo_1024px']['median']:.2f} s. The README's earlier '10-60 s' CPU estimate was pessimistic on this machine. Model loading happens once at start (not timed).")
    a(f"- Batched offline inference in the evaluation script: {F.M['inference_seconds_per_image_batched'] * 1000:.0f} ms per image for all four routes (batch 50).")
    a("")
    a("## 8. Tests")
    a("")
    a(f"- `python -m pytest tests`: {F.PYTEST_TOTAL} tests, {F.PYTEST_PASSED} passed in {F.PYTEST_SECONDS:.0f} s (preprocessing 2, weight normalisation, fusion, Gate 1 x2, Gate 2 x2, response structure with fixture models, health, bad upload, and 8 API tests: login, config, insights, analyze auth, bad upload, oversize).")
    a(f"- `python scripts/smoke_test.py` (API + Vite proxy): {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks passed (login, analyze a fake and a real image with votes, Grad-CAM, robustness, error cases, classic pages, `/api/predict` contract, proxy).")
    a("- `python scripts/capture_screens.py`: every screen walked in Chrome with a clean console (no console errors, no failed requests).")
    a("- Not done: unit tests of `explainability.py` and `robustness.py`, load testing, GPU run, user study.")
    a("")
    a("## 9. Endpoints")
    a("")
    for r in ("GET /health", "GET /api/config", "GET /api/insights", "GET /artifacts/confusion_matrix.png", "POST /api/auth/login", "GET /api/auth/me",
              "POST /api/analyze (token; verdict, branches, Grad-CAM, robustness)", "POST /api/predict (JSON verdict, no token)", "GET / , POST /predict, GET /insights (classic Jinja pages)"):
        a(f"- `{r}`")
    a("- Upload rules: png/jpg/jpeg/webp, up to 10 MB, must decode as RGB and be at least 8x8; errors are JSON on /api paths (400, 401, 413, 500, 503).")
    a("")
    a("## 10. Screenshots (`docs/screenshots/`, 1440x900, captured from the running app with the CIFAKE-trained models)")
    a("")
    shots = sorted(os.listdir(F.SHOTS))
    for s in shots:
        a(f"- `{s}`")
    a("")
    a("## 11. Figures and diagrams")
    a("")
    a("- Diagrams (`docs/diagrams/`): " + ", ".join(sorted(os.listdir(F.DIAG))))
    a("- Figures (`docs/figures/`): " + ", ".join(sorted(os.listdir(F.FIGS))))
    a("")
    a("## 12. Literature")
    a("")
    a("- Base paper (batch file): Larue et al., CTrue, IEEE Access vol. 14, 2026, doi 10.1109/ACCESS.2026.3702429. One-class, trained on 720 pristine FaceForensics++ videos with pseudo-fakes; EfficientNet-B4 (19.3 M parameters, 4.4 GFLOPs), 200 epochs on two V100 GPUs (about 16 h), 74 fps on an RTX 3060; "
      "reports AUC 98.9 % on FF++ and 77.0 % on DFDC (lambda = 1 ablation); cross-dataset Table 1 values are images in the PDF and are not quoted. Faces, not general images; AUC, not accuracy.")
    a("- HEDGE (arXiv 2604.03555): three routes (DINOv3 progressive training, higher-resolution route, MetaCLIP2 route), logit-space weighted fusion 7:3 and 7:3, dual gating (Gate 2 tau1 = 8, tau2 = 3, delta = 2.5), 4th place NTIRE 2026 robust AIGI detection challenge, "
      "average balanced accuracy 98.3 % on five standard benchmarks (JPEG 97.8 %, resize 98.4 %); ablation (competition set, robust F1): full 80.52, + gates 80.89; trained on 8 H800 GPUs.")
    a("- Empirical study (arXiv 2511.02791): ten forensic methods, seven GAN/diffusion datasets, accuracy / AP / AUC, Grad-CAM and confidence-curve analysis; reports strong in-distribution but weaker cross-model transfer.")
    a("- Batch survey items 4-7 could not be verified online; they are listed in the references marked [unverified] and no number from them is used.")
    a("")
    a("## 13. Comparison with the base paper (state plainly)")
    a("")
    a("- Different task (general images vs faces), different data (CIFAKE 32 px subset vs FF++/DFDC), different training regime (supervised, 6,000 images, 3-5 epochs, CPU vs one-class, 720 videos, 200 epochs, two V100), different metric emphasis (accuracy/F1 vs AUC). "
      "The only like-for-like metric is AUC: 98.65 % here on CIFAKE (in-domain) against 98.9 % on FF++ (in-domain) in the paper; cross-dataset, the paper's DFDC AUC is 77.0 % and this project's cross-domain AUC is 49.9 %. The numbers are not comparable evidence of one method being better.")
    a("")
    a("## 14. Honest gaps")
    a("")
    for g in ("Single training run per route (seed 42-45); no seed study, so the ranking of routes carries run-to-run uncertainty beyond the bootstrap interval.",
              "Training used 6,000 of the 100,000 CIFAKE training images and 3-5 epochs because of CPU-only hardware; a full-data run would probably score higher.",
              "CIFAKE images are 32x32 JPEG, so conclusions do not transfer to modern high-resolution generators; the cross-domain probe shows chance performance.",
              "One generator (Stable Diffusion 1.4) in the training data; no per-generator breakdown, no GAN or newer diffusion model.",
              "Gate thresholds (2.5, 2.5, 0.75) are the product's engineering defaults, not tuned; the gates did not improve results here.",
              "Threshold analysis and fusion-weight choices were evaluated on the test subset; no separate validation of the fused operating point.",
              "Grad-CAM maps were inspected qualitatively only; there is no quantitative faithfulness test (for example deletion/insertion).",
              "No user study, no GPU timing, no load test, no adversarial attack test.",
              "The deployed Insights page shows the CIFAKE-subset metrics; the shipped README still describes the older demo-data numbers unless updated."):
        a(f"- {g}")
    a("")
    out = os.path.join(F.DOCS, "REPORT_FACTS.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("wrote", out)


def M_ECE():
    return F.M["ece_branches"]


if __name__ == "__main__":
    main()
