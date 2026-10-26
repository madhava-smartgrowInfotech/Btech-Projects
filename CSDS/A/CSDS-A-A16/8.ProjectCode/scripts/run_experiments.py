"""Measurement suite for the documentation run. Run from 8.ProjectCode with system python:

    python scripts/run_experiments.py eval              # shipped models: baseline, final, GAN fidelity, detection
    python scripts/run_experiments.py ablate real_only 1 # one retraining run (variant, seed)
    python scripts/run_experiments.py ablate synth 1 200 # synthetic images per compound class

Everything is written to experiments/**/metrics.json. torch is imported before sklearn/cv2 on purpose.
"""
import io
import json
import sys
import time
from pathlib import Path

import torch  # noqa: F401  (import first, see docs-prompt tooling note)
import numpy as np
import cv2
from PIL import Image
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import CHECKPOINT_DIR, CLASSIFIER_CHECKPOINT  # noqa: E402
from app.ml.classifier_model import EmotionCNN, IMG_SIZE  # noqa: E402
from app.ml.dataset import load_split  # noqa: E402
from app.ml.face import detect_largest_face  # noqa: E402
from app.ml.gan_model import NOISE_DIM  # noqa: E402
from app.ml.synthesize_compound import load_generator, synthesize  # noqa: E402
from app.ml.taxonomy import (ALL_LABELS, BASIC_EMOTIONS, BASIC_INDEX, COMPOUND_COMPONENTS,  # noqa: E402
                             COMPOUND_EMOTIONS, LABEL_INDEX, NUM_BASIC, NUM_LABELS)

EXP = ROOT / "experiments"
torch.set_num_threads(4)


def to_tensor(images):
    x = images.astype(np.float32) / 255.0
    return torch.from_numpy((x - 0.5) / 0.5).unsqueeze(1)


def save(path, obj):
    path = EXP / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))
    print("wrote", path)


def load_model(path, out_dim):
    m = EmotionCNN(out_dim=out_dim)
    m.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    return m.eval()


@torch.no_grad()
def predict(model, images, sigmoid):
    outs = []
    for i in range(0, len(images), 512):
        o = model(to_tensor(images[i:i + 512]))
        outs.append(torch.sigmoid(o) if sigmoid else torch.softmax(o, 1))
    return torch.cat(outs).numpy()


def basic_report(y_true, y_pred):
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=list(range(NUM_BASIC)), zero_division=0)
    return {
        "accuracy": float((y_true == y_pred).mean()),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "per_class": {BASIC_EMOTIONS[i]: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]),
                                          "support": int(s[i])} for i in range(NUM_BASIC)},
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(range(NUM_BASIC))).tolist(),
        "labels": BASIC_EMOTIONS,
    }


def compound_on_real(probs, y_true):
    """Behaviour of the 11 compound outputs on real FER2013 test faces (no compound ground truth exists)."""
    cp = probs[:, NUM_BASIC:]
    out = {"n": int(len(probs))}
    top = cp.argmax(1)
    comp_has_true = np.array([BASIC_EMOTIONS[y_true[i]] in COMPOUND_COMPONENTS[COMPOUND_EMOTIONS[top[i]]]
                              for i in range(len(top))])
    out["top_compound_contains_true_basic"] = float(comp_has_true.mean())
    # chance level: fraction of compounds containing each basic label, weighted by test support
    chance = np.mean([np.mean([BASIC_EMOTIONS[y_true[i]] in COMPOUND_COMPONENTS[c] for c in COMPOUND_EMOTIONS])
                      for i in range(len(y_true))])
    out["chance_top_compound_contains_true_basic"] = float(chance)
    out["any_compound_ge_0.5"] = float((cp.max(1) >= 0.5).mean())
    out["any_compound_ge_0.3"] = float((cp.max(1) >= 0.3).mean())
    dom = probs.argmax(1)
    out["dominant_is_compound"] = float((dom >= NUM_BASIC).mean())
    out["mean_top_compound_confidence"] = float(cp.max(1).mean())
    # in-pair vs out-of-pair mean score
    inn, outn = [], []
    for ci, c in enumerate(COMPOUND_EMOTIONS):
        a, b = COMPOUND_COMPONENTS[c]
        for k in BASIC_EMOTIONS:
            m = y_true == BASIC_INDEX[k]
            if not m.any():
                continue
            (inn if k in (a, b) else outn).append(cp[m, ci].mean())
    out["mean_score_true_basic_is_component"] = float(np.mean(inn))
    out["mean_score_true_basic_not_component"] = float(np.mean(outn))
    return out


def multilabel_report(probs, truth, thr=0.5):
    pred = (probs >= thr).astype(int)
    emr = float((pred == truth).all(1).mean())
    from sklearn.metrics import roc_auc_score
    aucs = [roc_auc_score(truth[:, j], probs[:, j]) for j in range(NUM_BASIC, NUM_LABELS) if 0 < truth[:, j].sum() < len(truth)]
    return {
        "threshold": thr,
        "compound_roc_auc_macro": float(np.mean(aucs)) if aucs else None,
        "mean_compound_prob_on_true_compound": float(probs[:, NUM_BASIC:][truth[:, NUM_BASIC:] == 1].mean()),
        "dominant_is_correct_compound": float(np.mean([probs[i].argmax() == truth[i, NUM_BASIC:].argmax() + NUM_BASIC for i in range(len(probs))])),
        "micro_f1": float(f1_score(truth, pred, average="micro", zero_division=0)),
        "macro_f1": float(f1_score(truth, pred, average="macro", zero_division=0)),
        "exact_match_ratio": emr,
        "compound_recall": float(((pred[:, NUM_BASIC:] == 1) & (truth[:, NUM_BASIC:] == 1)).sum()
                                 / truth[:, NUM_BASIC:].sum()),
    }


def synth_holdout(generator, n_per_class=100, seed=12345):
    torch.manual_seed(seed)
    return synthesize(generator, n_per_class=n_per_class)


@torch.no_grad()
def features(model, images):
    outs = []
    for i in range(0, len(images), 512):
        x = to_tensor(images[i:i + 512])
        h = model.features(x)
        h = model.classifier[:3](h)  # flatten, linear, relu -> 256-d
        outs.append(h)
    return torch.cat(outs).numpy()


def frechet(a, b):
    from scipy import linalg
    mu1, mu2 = a.mean(0), b.mean(0)
    s1, s2 = np.cov(a, rowvar=False), np.cov(b, rowvar=False)
    covmean, _ = linalg.sqrtm(s1.dot(s2), disp=False)
    covmean = covmean.real
    return float(((mu1 - mu2) ** 2).sum() + np.trace(s1) + np.trace(s2) - 2 * np.trace(covmean))


# --------------------------------------------------------------------------- eval
def cmd_eval():
    t0 = time.time()
    te_x, te_y = load_split("test.pt")
    tr_x, tr_y = load_split("train.pt")
    counts = {"train": {BASIC_EMOTIONS[i]: int((tr_y == i).sum()) for i in range(NUM_BASIC)},
              "test": {BASIC_EMOTIONS[i]: int((te_y == i).sum()) for i in range(NUM_BASIC)}}
    save("dataset/metrics.json", {"source": "Hugging Face Jeneral/fer-2013 (FER2013 pickles)", "image_size_native": 48,
                                  "model_input": IMG_SIZE, "n_train": len(tr_x), "n_test": len(te_x), "class_counts": counts,
                                  "test_majority_baseline": float(np.bincount(te_y).max() / len(te_y))})

    # baseline: single-label softmax backbone (stage 1)
    base = load_model(CHECKPOINT_DIR / "stage1_backbone.pt", NUM_BASIC)
    pb = predict(base, te_x, sigmoid=False)
    rb = basic_report(te_y, pb.argmax(1))
    save("baseline_stage1/metrics.json", rb)

    # final multi-label model
    fin = load_model(CLASSIFIER_CHECKPOINT, NUM_LABELS)
    pf = predict(fin, te_x, sigmoid=True)
    rf = basic_report(te_y, pf[:, :NUM_BASIC].argmax(1))
    rf["compound_on_real_test"] = compound_on_real(pf, te_y)
    rf["parameters"] = int(sum(p.numel() for p in fin.parameters()))
    save("final_shipped/metrics.json", rf)
    print("baseline acc", rb["accuracy"], "final acc", rf["accuracy"])

    # GAN fidelity
    gen = load_generator()
    torch.manual_seed(7)
    fid = {"basic": {}, "compound": {}}
    gen_basic_imgs = []
    with torch.no_grad():
        for k in BASIC_EMOTIONS:
            cond = torch.zeros(500, NUM_BASIC)
            cond[:, BASIC_INDEX[k]] = 1.0
            im = gen(torch.randn(500, NOISE_DIM), cond)
            u8 = ((im.squeeze(1).numpy() * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
            gen_basic_imgs.append(u8)
            pr = predict(base, u8, sigmoid=False)
            fid["basic"][k] = {"stage1_accuracy_on_generated": float((pr.argmax(1) == BASIC_INDEX[k]).mean())}
        comp_imgs = []
        for c in COMPOUND_EMOTIONS:
            a, b = COMPOUND_COMPONENTS[c]
            cond = torch.zeros(500, NUM_BASIC)
            cond[:, BASIC_INDEX[a]] = 0.5
            cond[:, BASIC_INDEX[b]] = 0.5
            im = gen(torch.randn(500, NOISE_DIM), cond)
            u8 = ((im.squeeze(1).numpy() * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
            comp_imgs.append(u8)
            pr = predict(base, u8, sigmoid=False)
            top2 = np.argsort(-pr, 1)[:, :2]
            want = {BASIC_INDEX[a], BASIC_INDEX[b]}
            fid["compound"][c] = {
                "stage1_top1_in_pair": float(np.mean([t[0] in want for t in top2])),
                "stage1_top2_equals_pair": float(np.mean([set(t) == want for t in top2])),
            }
    fid["mean_basic_conditional_accuracy"] = float(np.mean([v["stage1_accuracy_on_generated"] for v in fid["basic"].values()]))
    fid["mean_compound_top1_in_pair"] = float(np.mean([v["stage1_top1_in_pair"] for v in fid["compound"].values()]))
    fid["mean_compound_top2_equals_pair"] = float(np.mean([v["stage1_top2_equals_pair"] for v in fid["compound"].values()]))
    fid["chance_top1_in_pair"] = 2 / 7
    fid["chance_top2_equals_pair"] = 1 / 21
    # Frechet distance in the stage-1 CNN feature space (not Inception FID)
    rng = np.random.default_rng(0)
    idx = []
    for k in range(NUM_BASIC):
        ii = np.where(tr_y == k)[0]
        idx.extend(rng.choice(ii, 400, replace=False))
    real_sub = tr_x[idx]
    gen_all = np.concatenate(gen_basic_imgs)
    fr_real = features(base, real_sub)
    fid["frechet_distance_stage1_features"] = {
        "generated_basic_vs_real_train_subset": frechet(features(base, gen_all[:2800]), fr_real),
        "real_test_vs_real_train_subset": frechet(features(base, te_x[rng.choice(len(te_x), 2800, replace=False)]), fr_real),
        "generated_compound_vs_real_train_subset": frechet(features(base, np.concatenate(comp_imgs)[:2800]), fr_real),
        "note": "256-d penultimate features of the stage-1 CNN, not Inception features; values are not comparable with published FID",
    }
    # diversity: mean pixel std across samples within a class
    div_gen = float(np.mean([g.astype(np.float32).std(0).mean() for g in gen_basic_imgs]))
    div_real = float(np.mean([tr_x[tr_y == k][:500].astype(np.float32).std(0).mean() for k in range(NUM_BASIC)]))
    fid["pixelwise_std_within_class"] = {"generated": div_gen, "real": div_real}
    fid["generator_parameters"] = int(sum(p.numel() for p in gen.parameters()))
    save("gan_fidelity/metrics.json", fid)

    # sample grids for figures
    def grid(rows, n=10):
        return np.concatenate([np.concatenate(list(r[:n]), 1) for r in rows], 0)
    figs = EXP / "gan_fidelity"
    cv2.imwrite(str(figs / "grid_generated_basic.png"), grid(gen_basic_imgs))
    cv2.imwrite(str(figs / "grid_generated_compound.png"), grid(comp_imgs))
    cv2.imwrite(str(figs / "grid_real_basic.png"), grid([tr_x[tr_y == k][:10] for k in range(NUM_BASIC)]))

    # synthetic hold-out
    hx, hy = synth_holdout(gen)
    ph = predict(fin, hx, sigmoid=True)
    rep = {"n": len(hx), "per_compound_class": 100,
           "final_model": {str(t): multilabel_report(ph, hy, t) for t in (0.05, 0.1, 0.2, 0.3, 0.5)}}
    if (EXP / "ablation" / "real_only_s1" / "model.pt").exists():
        ro = load_model(EXP / "ablation" / "real_only_s1" / "model.pt", NUM_LABELS)
        rep["real_only_control"] = multilabel_report(predict(ro, hx, sigmoid=True), hy, 0.5)
    save("synthetic_holdout/metrics.json", rep)

    # detection and pipeline domain shift (raw 48x48 FER2013 pixels, upscaled with bicubic interpolation)
    import pickle
    raw = pickle.load((BACKEND / "data" / "test.pt").open("rb"))
    det = {"n_images": 1000, "note": "scale 1x = native 48x48 FER2013 pixels"}
    sel = np.random.default_rng(1).choice(len(raw), 1000, replace=False)

    def raw48(i):
        return np.array(Image.open(io.BytesIO(raw[i]["img_bytes"])).convert("L"))
    for sc in (1, 2, 3, 4, 6):
        ok = 0
        for i in sel:
            a_ = raw48(i)
            a_ = cv2.resize(a_, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC) if sc > 1 else a_
            ok += detect_largest_face(cv2.cvtColor(a_, cv2.COLOR_GRAY2BGR)) is not None
        det[f"haar_detection_rate_scale_{sc}x"] = ok / len(sel)
    # accuracy on the detected subset via the real inference path (Haar crop -> 64x64) vs direct 64x64 resize
    correct_pipe = correct_direct = n_det = 0
    labels_by_name = {k: v for k, v in BASIC_INDEX.items()}
    for i in sel:
        a_ = cv2.resize(raw48(i), None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        crop = detect_largest_face(cv2.cvtColor(a_, cv2.COLOR_GRAY2BGR))
        if crop is None:
            continue
        n_det += 1
        y = labels_by_name[raw[i]["labels"]]
        c = cv2.resize(crop, (IMG_SIZE, IMG_SIZE))
        pr = predict(fin, c[None], sigmoid=True)[0]
        correct_pipe += int(pr[:NUM_BASIC].argmax() == y)
        d64 = cv2.resize(raw48(i), (IMG_SIZE, IMG_SIZE))
        correct_direct += int(predict(fin, d64[None], sigmoid=True)[0][:NUM_BASIC].argmax() == y)
    det["detected_at_3x"] = n_det
    det["accuracy_via_haar_crop_on_detected"] = correct_pipe / max(n_det, 1)
    det["accuracy_direct_64px_on_same_images"] = correct_direct / max(n_det, 1)
    save("detection/metrics.json", det)
    print("eval done in %.1f min" % ((time.time() - t0) / 60))


# --------------------------------------------------------------------------- ablation
def cmd_ablate(variant, seed, synth_n=200, epochs=5, save_model=False):
    t0 = time.time()
    torch.manual_seed(seed)
    np.random.seed(seed)
    tr_x, tr_y = load_split("train.pt")
    te_x, te_y = load_split("test.pt")
    n_synth = 0 if variant == "real_only" else synth_n
    gen = load_generator()
    real_mh = np.zeros((len(tr_y), NUM_LABELS), np.float32)
    real_mh[np.arange(len(tr_y)), tr_y] = 1
    if n_synth:
        sx, sy = synthesize(gen, n_per_class=n_synth)
        X, Y = np.concatenate([tr_x, sx]), np.concatenate([real_mh, sy])
    else:
        X, Y = tr_x, real_mh
    ds = torch.utils.data.TensorDataset(to_tensor(X), torch.from_numpy(Y))
    loader = torch.utils.data.DataLoader(ds, batch_size=256, shuffle=True)
    model = EmotionCNN(out_dim=NUM_LABELS)
    bb = torch.load(CHECKPOINT_DIR / "stage1_backbone.pt", map_location="cpu", weights_only=True)
    model.load_state_dict({k: v for k, v in bb.items() if k.startswith("features.")}, strict=False)
    opt = torch.optim.Adam(model.parameters(), lr=5e-4)
    crit = torch.nn.BCEWithLogitsLoss()
    hist = []
    for ep in range(epochs):
        model.train()
        tot = 0.0
        for xb, yb in loader:
            opt.zero_grad()
            loss = crit(model(xb), yb)
            loss.backward()
            opt.step()
            tot += loss.item() * len(xb)
        hist.append(tot / len(ds))
        print(variant, seed, "epoch", ep + 1, hist[-1], flush=True)
    model.eval()
    pt = predict(model, te_x, sigmoid=True)
    rep = basic_report(te_y, pt[:, :NUM_BASIC].argmax(1))
    rep["compound_on_real_test"] = compound_on_real(pt, te_y)
    hx, hy = synth_holdout(gen)
    rep["synthetic_holdout_thr0.5"] = multilabel_report(predict(model, hx, sigmoid=True), hy, 0.5)
    rep["config"] = {"variant": variant, "seed": seed, "synthetic_per_compound_class": n_synth, "epochs": epochs,
                     "train_images": int(len(X)), "loss_history": hist, "minutes": (time.time() - t0) / 60}
    name = f"{variant}_s{seed}" if variant == "real_only" or synth_n == 200 else f"{variant}{synth_n}_s{seed}"
    save(f"ablation/{name}/metrics.json", rep)
    if save_model:
        torch.save(model.state_dict(), EXP / "ablation" / name / "model.pt")


if __name__ == "__main__":
    if sys.argv[1] == "eval":
        cmd_eval()
    elif sys.argv[1] == "ablate":
        pos = [a for a in sys.argv[2:] if not a.startswith("--")]
        cmd_ablate(pos[0], int(pos[1]), int(pos[2]) if len(pos) > 2 else 200, save_model=("--save" in sys.argv))
