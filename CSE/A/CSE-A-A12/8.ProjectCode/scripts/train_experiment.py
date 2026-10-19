"""
Reproducible training / evaluation run for the pneumonia classifier.

It trains the project's own architecture (model.model_builder) on the public Kermany
chest X-ray data and evaluates on the official, untouched test split. Everything the
report quotes comes from the metrics.json this script writes.

Dataset layout expected (the Kaggle / Mendeley "chest_xray" folder):

    <data_root>/{train,val,test}/{NORMAL,PNEUMONIA}/*.jpeg

Pneumonia images carry the pathogen in the file name (person12_bacteria_34.jpeg,
person7_virus_21.jpeg), which gives the three project classes
Normal / Bacterial Pneumonia / Viral Pneumonia.

Usage:
    python scripts/train_experiment.py --data_root <chest_xray> --name exp01_custom_cnn
    python scripts/train_experiment.py --data_root <chest_xray> --name exp02_no_clahe --no_clahe

Differences from model/train.py (which is left untouched):
  * training images go through model.preprocess.load_and_preprocess_image, the same
    function the web app uses at inference time (CLAHE + blur), so there is no
    train/serve mismatch;
  * the 16-image official val folder is merged into train and a patient-level 10 %
    validation split is cut from it (several images belong to one patient);
  * class weights compensate for the Bacterial-heavy class balance;
  * metrics.json, a prediction CSV and figures are written to experiments/<name>/.
"""

import argparse
import csv
import glob
import json
import os
import platform
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from model.preprocess import load_and_preprocess_image, preprocess_for_display
from model.model_builder import CLASS_NAMES, build_custom_cnn, build_transfer_model, find_last_conv_layer
from model.gradcam import make_gradcam_heatmap, overlay_heatmap

SEED = 42


def label_of(path):
    """Class index from folder and file name: 0 Normal, 1 Bacterial, 2 Viral."""
    name = os.path.basename(path).lower()
    if os.sep + "normal" + os.sep in path.lower().replace("/", os.sep):
        return 0
    if "bacteria" in name:
        return 1
    if "virus" in name:
        return 2
    raise ValueError(f"cannot label {path}")


def group_of(path):
    """Patient id: personNNN for pneumonia files, IM-NNNN for normals."""
    name = os.path.basename(path)
    m = re.match(r"(person\d+)_", name)
    if m:
        return m.group(1)
    m = re.match(r"(.*)-\d+\.\w+$", name)
    return m.group(1) if m else name


def list_images(folder):
    out = []
    for ext in ("*.jpeg", "*.jpg", "*.png"):
        out += glob.glob(os.path.join(folder, "*", ext))
    return sorted(out)


def load_cached(paths, clahe, cache_file):
    if os.path.exists(cache_file):
        z = np.load(cache_file, allow_pickle=False)
        if z.shape[0] == len(paths):
            return z
    arr = np.zeros((len(paths), 224, 224), dtype=np.uint8)
    t0 = time.time()
    for i, p in enumerate(paths):
        img = load_and_preprocess_image(p, apply_enhancement=clahe)
        arr[i] = np.rint(img[..., 0] * 255).astype(np.uint8)
        if i % 500 == 0:
            print(f"  preprocessed {i}/{len(paths)} ({time.time() - t0:.0f}s)", flush=True)
    np.save(cache_file, arr)
    return arr


def to_input(gray_u8):
    """uint8 (N,224,224) -> float32 (N,224,224,3) in [0,1]."""
    x = gray_u8.astype("float32") / 255.0
    return np.repeat(x[..., None], 3, axis=-1)


def build_mobilenet_v3_small(learning_rate):
    """MobileNetV3Small (the backbone the base paper selects) with an ImageNet start and a 3-way softmax head.
    The project feeds tensors in [0, 1]; the backbone expects 0-255 and rescales internally, hence Rescaling(255)."""
    from tensorflow.keras import Input, layers, models
    from tensorflow.keras.applications import MobileNetV3Small
    from tensorflow.keras.optimizers import Adam

    base = MobileNetV3Small(include_top=False, weights="imagenet", input_shape=(224, 224, 3), include_preprocessing=True)
    inputs = Input(shape=(224, 224, 3))
    x = layers.Rescaling(255.0)(inputs)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D(name="last_conv_gap")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(3, activation="softmax")(x)
    model = models.Model(inputs, outputs, name="pneumonia_mobilenetv3small")
    model.compile(optimizer=Adam(learning_rate), loss="categorical_crossentropy",
                  metrics=["accuracy", "AUC", "Precision", "Recall"])
    return model, base


def expected_calibration_error(conf, correct, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--backbone", default="custom")
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--head_epochs", type=int, default=4, help="mobilenetv3small only: epochs with the backbone frozen")
    ap.add_argument("--no_clahe", action="store_true", help="skip CLAHE (ablation)")
    ap.add_argument("--no_class_weights", action="store_true")
    ap.add_argument("--protocol", choices=["official", "patient"], default="official",
                    help="official: Kermany train/val -> official test split; patient: merge everything and re-split at patient level (about 71/14/14)")
    ap.add_argument("--patience", type=int, default=6, help="early-stopping patience (epochs) on validation loss")
    ap.add_argument("--reduce_patience", type=int, default=3, help="epochs without improvement before the learning rate is halved")
    ap.add_argument("--smoke", action="store_true", help="debug run: 200 training images, 1 epoch")
    ap.add_argument("--cache_dir", default=None)
    ap.add_argument("--export_model", default=None, help="folder to write pneumonia_model.h5 + class_indices.json")
    args = ap.parse_args()

    import tensorflow as tf
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.utils.class_weight import compute_class_weight
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    np.random.seed(SEED)
    tf.random.set_seed(SEED)

    out = os.path.join(ROOT, "experiments", args.name)
    os.makedirs(out, exist_ok=True)
    cache_dir = args.cache_dir or os.path.join(args.data_root, "_cache")
    os.makedirs(cache_dir, exist_ok=True)
    clahe = not args.no_clahe

    # ---- data ----
    pool = list_images(os.path.join(args.data_root, "train")) + list_images(os.path.join(args.data_root, "val"))
    test_paths = list_images(os.path.join(args.data_root, "test"))
    y_pool = np.array([label_of(p) for p in pool])
    groups = np.array([group_of(p) for p in pool])
    y_test = np.array([label_of(p) for p in test_paths])

    tag = "clahe" if clahe else "noclahe"
    X_pool = load_cached(pool, clahe, os.path.join(cache_dir, f"pool_{tag}.npy"))
    X_test = load_cached(test_paths, clahe, os.path.join(cache_dir, f"test_{tag}.npy"))
    groups_test = np.array([group_of(p) for p in test_paths])

    if args.protocol == "official":
        sgkf = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=SEED)
        tr_idx, va_idx = next(sgkf.split(pool, y_pool, groups))
        assert not set(groups[tr_idx]) & set(groups[va_idx]), "patient leakage between train and validation"
        X_tr, y_tr, g_tr = X_pool[tr_idx], y_pool[tr_idx], groups[tr_idx]
        X_va, y_va, g_va = X_pool[va_idx], y_pool[va_idx], groups[va_idx]
    else:  # patient-disjoint re-partition of all 5,856 images
        all_paths = pool + test_paths
        X_all = np.concatenate([X_pool, X_test])
        y_all = np.concatenate([y_pool, y_test])
        g_all = np.concatenate([groups, groups_test])
        outer = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=SEED)
        rest_idx, te_idx = next(outer.split(all_paths, y_all, g_all))
        inner = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=SEED)
        tr_rel, va_rel = next(inner.split(rest_idx, y_all[rest_idx], g_all[rest_idx]))
        tr_idx, va_idx = rest_idx[tr_rel], rest_idx[va_rel]
        assert not (set(g_all[tr_idx]) & set(g_all[va_idx])) and not (set(g_all[tr_idx]) & set(g_all[te_idx]))             and not (set(g_all[va_idx]) & set(g_all[te_idx])), "patient leakage between splits"
        X_tr, y_tr, g_tr = X_all[tr_idx], y_all[tr_idx], g_all[tr_idx]
        X_va, y_va, g_va = X_all[va_idx], y_all[va_idx], g_all[va_idx]
        X_test, y_test = X_all[te_idx], y_all[te_idx]
        test_paths = [all_paths[i] for i in te_idx]
        groups_test = g_all[te_idx]

    if args.smoke:
        keep = np.random.RandomState(SEED).permutation(len(y_tr))[:200]
        X_tr, y_tr, g_tr = X_tr[keep], y_tr[keep], g_tr[keep]
        args.epochs, args.head_epochs = 1, 1

    # how many test images share a patient id with the training pool (potential leakage, see Shahi and Bagale 2025)
    train_ids = set(g_tr)
    shared = np.array([g in train_ids for g in groups_test])

    split = {
        "protocol": args.protocol,
        "train": int(len(y_tr)), "validation": int(len(y_va)), "test": int(len(test_paths)),
        "train_by_class": [int((y_tr == c).sum()) for c in range(3)],
        "validation_by_class": [int((y_va == c).sum()) for c in range(3)],
        "test_by_class": [int((y_test == c).sum()) for c in range(3)],
        "train_patients": int(len(set(g_tr))), "validation_patients": int(len(set(g_va))), "test_patients": int(len(set(groups_test))),
        "test_images_sharing_patient_id_with_training": int(shared.sum()),
    }
    print("split", split, flush=True)

    # ---- model ----
    base = None
    if args.backbone == "custom":
        model = build_custom_cnn(num_classes=3, learning_rate=args.lr)
    elif args.backbone == "mobilenetv3small":
        model, base = build_mobilenet_v3_small(args.lr)
    else:
        model = build_transfer_model(num_classes=3, backbone=args.backbone, learning_rate=args.lr)
    n_params = int(model.count_params())

    cw = None
    if not args.no_class_weights:
        w = compute_class_weight("balanced", classes=np.arange(3), y=y_tr)
        cw = {i: float(v) for i, v in enumerate(w)}
    print("class weights", cw, flush=True)

    aug = ImageDataGenerator(
        rotation_range=12, width_shift_range=0.08, height_shift_range=0.08,
        shear_range=0.08, zoom_range=0.12, horizontal_flip=True, fill_mode="nearest",
    )  # same ranges as model.preprocess.get_train_augmentor, minus the rescale (images are already in [0,1])

    def train_batches():
        gen = aug.flow((X_tr.astype("float32")[..., None] / 255.0), tf.keras.utils.to_categorical(y_tr, 3),
                       batch_size=args.batch_size, shuffle=True, seed=SEED)
        for xb, yb in gen:
            yield np.repeat(xb, 3, axis=-1), yb

    steps = int(np.ceil(len(X_tr) / args.batch_size))
    train_ds = tf.data.Dataset.from_generator(
        train_batches,
        output_signature=(tf.TensorSpec((None, 224, 224, 3), tf.float32), tf.TensorSpec((None, 3), tf.float32)),
    ).repeat().prefetch(2)  # the augmentation generator runs while the previous batch trains

    Xv = to_input(X_va)
    yv = tf.keras.utils.to_categorical(y_va, 3)

    ckpt = os.path.join(out, "best_model.h5")
    callbacks = [
        ModelCheckpoint(ckpt, monitor="val_loss", save_best_only=True, verbose=0),
        EarlyStopping(monitor="val_loss", patience=args.patience, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=args.reduce_patience, min_lr=1e-7),
    ]

    t0 = time.time()
    head_hist = {}
    if base is not None:  # stage 1: train the new head with the backbone frozen
        base.trainable = False
        model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="categorical_crossentropy",
                      metrics=["accuracy", "AUC", "Precision", "Recall"])
        h1 = model.fit(train_ds, steps_per_epoch=steps, epochs=args.head_epochs, validation_data=(Xv, yv),
                       class_weight=cw, verbose=2)
        head_hist = h1.history
        base.trainable = True  # stage 2: fine-tune everything (the backbone is called with training=False, so BN stays in inference mode)
        model.compile(optimizer=tf.keras.optimizers.Adam(args.lr), loss="categorical_crossentropy",
                      metrics=["accuracy", "AUC", "Precision", "Recall"])
    hist = model.fit(
        train_ds, steps_per_epoch=steps, epochs=args.epochs, validation_data=(Xv, yv),
        class_weight=cw, callbacks=callbacks, verbose=2,
    )
    train_seconds = time.time() - t0
    merged = {k: list(head_hist.get(k, [])) + list(v) for k, v in hist.history.items()}
    stage1_epochs = len(head_hist.get("loss", []))
    epochs_run = len(merged["loss"])
    best_epoch = stage1_epochs + int(np.argmin(hist.history["val_loss"])) + 1
    history = {k: [float(v) for v in vs] for k, vs in merged.items()}
    json.dump(history, open(os.path.join(out, "history.json"), "w"), indent=1)

    # ---- evaluation on the official test split (model has restored the best weights) ----
    Xt = to_input(X_test)
    t1 = time.time()
    probs = model.predict(Xt, batch_size=64, verbose=0)
    batch_seconds = time.time() - t1
    pred = probs.argmax(1)
    val_probs = model.predict(Xv, batch_size=64, verbose=0)
    val_acc = float((val_probs.argmax(1) == y_va).mean())

    rep = classification_report(y_test, pred, target_names=CLASS_NAMES, output_dict=True, digits=4)
    rep_txt = classification_report(y_test, pred, target_names=CLASS_NAMES, digits=4)
    cm = confusion_matrix(y_test, pred, labels=[0, 1, 2])
    open(os.path.join(out, "classification_report.txt"), "w").write(rep_txt)

    # binary view: Normal vs any pneumonia
    y_bin = (y_test > 0).astype(int)
    p_bin = (pred > 0).astype(int)
    tp = int(((p_bin == 1) & (y_bin == 1)).sum()); tn = int(((p_bin == 0) & (y_bin == 0)).sum())
    fp = int(((p_bin == 1) & (y_bin == 0)).sum()); fn = int(((p_bin == 0) & (y_bin == 1)).sum())
    sens = tp / (tp + fn); spec = tn / (tn + fp); prec = tp / max(tp + fp, 1)
    f1_bin = 2 * prec * sens / max(prec + sens, 1e-9)
    auc_bin = float(roc_auc_score(y_bin, 1.0 - probs[:, 0]))
    try:
        auc_ovr = float(roc_auc_score(y_test, probs, multi_class="ovr"))
    except ValueError:
        auc_ovr = None

    conf = probs.max(1)
    correct = (pred == y_test).astype(float)
    ece = expected_calibration_error(conf, correct)

    # confidence-threshold analysis (selective prediction)
    thresholds = []
    for t in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
        keep = conf >= t
        thresholds.append({
            "threshold": t, "coverage": float(keep.mean()),
            "accuracy_on_kept": float(correct[keep].mean()) if keep.any() else None,
            "kept": int(keep.sum()),
        })

    # decision-threshold sweep for "pneumonia" (1 - P(normal)) -> sensitivity / specificity trade-off
    sweep = []
    score = 1.0 - probs[:, 0]
    for t in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        pb = (score >= t).astype(int)
        s_tp = int(((pb == 1) & (y_bin == 1)).sum()); s_fn = int(((pb == 0) & (y_bin == 1)).sum())
        s_tn = int(((pb == 0) & (y_bin == 0)).sum()); s_fp = int(((pb == 1) & (y_bin == 0)).sum())
        sweep.append({"threshold": t, "sensitivity": s_tp / (s_tp + s_fn), "specificity": s_tn / (s_tn + s_fp),
                      "accuracy": (s_tp + s_tn) / len(y_bin)})

    # ---- latency on this machine (project pipeline, one image at a time) ----
    sample = test_paths[0]
    last_conv = find_last_conv_layer(model)
    cam_ok = True
    for _ in range(3):  # warm-up
        bb = np.expand_dims(load_and_preprocess_image(sample), 0)
        model.predict(bb, verbose=0)
        try:
            make_gradcam_heatmap(bb, model, last_conv)
        except Exception as exc:  # the shipped gradcam.py cannot reach inside a nested transfer-learning backbone
            cam_ok = False
            cam_error = f"{type(exc).__name__}: {exc}"
    t_pre, t_pred, t_cam, t_all = [], [], [], []
    for p in test_paths[:60]:
        a = time.perf_counter()
        bb = np.expand_dims(load_and_preprocess_image(p), 0)
        disp = preprocess_for_display(p)
        b_ = time.perf_counter()
        pr = model.predict(bb, verbose=0)[0]
        c_ = time.perf_counter()
        if cam_ok:
            hm, _ = make_gradcam_heatmap(bb, model, last_conv, pred_index=int(pr.argmax()))
            overlay_heatmap(disp, hm)
        d_ = time.perf_counter()
        t_pre.append(b_ - a); t_pred.append(c_ - b_); t_cam.append(d_ - c_); t_all.append(d_ - a)
    ms = lambda v: float(np.mean(v) * 1000)

    metrics = {
        "name": args.name,
        "backbone": args.backbone,
        "preprocessing": "resize 224 + CLAHE(clip 2.5, 8x8) + Gaussian 3x3 + /255" if clahe else "resize 224 + Gaussian 3x3 + /255 (no CLAHE)",
        "class_weights": cw,
        "hyperparameters": {"epochs_max": args.epochs, "batch_size": args.batch_size, "learning_rate": args.lr,
                            "optimizer": "Adam", "loss": "categorical_crossentropy", "seed": SEED,
                            "early_stopping_patience": args.patience, "reduce_lr_patience": args.reduce_patience},
        "dataset": {"source": "Kermany et al., Mendeley Data v3 (Chest X-Ray Images (Pneumonia)), CC BY 4.0", **split},
        "training": {"epochs_run": epochs_run, "stage1_frozen_head_epochs": stage1_epochs, "best_epoch": best_epoch, "seconds_total": round(train_seconds, 1),
                     "seconds_per_epoch": round(train_seconds / epochs_run, 1),
                     "final_train_accuracy": history["accuracy"][-1], "best_val_accuracy_at_best_epoch": history["val_accuracy"][best_epoch - 1],
                     "val_accuracy_restored_model": val_acc, "parameters": n_params},
        "test": {
            "n": int(len(y_test)),
            "accuracy": float((pred == y_test).mean()),
            "macro_precision": rep["macro avg"]["precision"], "macro_recall": rep["macro avg"]["recall"], "macro_f1": rep["macro avg"]["f1-score"],
            "weighted_f1": rep["weighted avg"]["f1-score"],
            "per_class": {c: {"precision": rep[c]["precision"], "recall": rep[c]["recall"], "f1": rep[c]["f1-score"], "support": int(rep[c]["support"])} for c in CLASS_NAMES},
            "confusion_matrix": cm.tolist(), "class_order": CLASS_NAMES,
            "auc_ovr_macro": auc_ovr,
            "binary_normal_vs_pneumonia": {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "accuracy": (tp + tn) / len(y_bin),
                                           "sensitivity": sens, "specificity": spec, "precision": prec, "f1": f1_bin, "auc": auc_bin},
            "expected_calibration_error": ece,
            "mean_confidence": float(conf.mean()),
            "confidence_threshold_analysis": thresholds,
            "pneumonia_decision_threshold_sweep": sweep,
        },
        "latency_ms_mean_cpu": {"preprocess": ms(t_pre), "predict": ms(t_pred), "gradcam_overlay": ms(t_cam) if cam_ok else None,
                                "gradcam_supported_by_shipped_gradcam_py": cam_ok, "total_pipeline": ms(t_all),
                                "images_timed": len(t_all), "batch_predict_624_images_seconds": round(batch_seconds, 2)},
        "model_file_mb": round(os.path.getsize(ckpt) / 1e6, 2),
        "environment": {"python": platform.python_version(), "tensorflow": tf.__version__, "numpy": np.__version__,
                        "cpu": platform.processor(), "os": platform.platform(), "gpu": "none (CPU only)"},
    }
    json.dump(metrics, open(os.path.join(out, "metrics.json"), "w"), indent=2)

    with open(os.path.join(out, "test_predictions.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "true", "pred", "confidence"] + [f"p_{c}" for c in CLASS_NAMES])
        for p, t, pr, pb in zip(test_paths, y_test, pred, probs):
            w.writerow([os.path.relpath(p, args.data_root), CLASS_NAMES[t], CLASS_NAMES[pr], f"{pb.max():.4f}"] + [f"{v:.4f}" for v in pb])

    # ---- figures ----
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(history["accuracy"], label="train"); ax[0].plot(history["val_accuracy"], label="validation")
    ax[0].axvline(best_epoch - 1, color="grey", ls=":"); ax[0].set_title("Accuracy"); ax[0].set_xlabel("epoch"); ax[0].legend()
    ax[1].plot(history["loss"], label="train"); ax[1].plot(history["val_loss"], label="validation")
    ax[1].axvline(best_epoch - 1, color="grey", ls=":"); ax[1].set_title("Loss"); ax[1].set_xlabel("epoch"); ax[1].legend()
    fig.tight_layout(); fig.savefig(os.path.join(out, "training_curves.png"), dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3)); ax.set_yticks(range(3))
    ax.set_xticklabels(["Normal", "Bacterial", "Viral"]); ax.set_yticklabels(["Normal", "Bacterial", "Viral"])
    for i in range(3):
        for j in range(3):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=13)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title(f"Confusion matrix, test n={len(y_test)}")
    fig.tight_layout(); fig.savefig(os.path.join(out, "confusion_matrix.png"), dpi=150); plt.close(fig)

    if args.export_model:
        os.makedirs(args.export_model, exist_ok=True)
        model.save(os.path.join(args.export_model, "pneumonia_model.h5"))
        json.dump({str(i): n for i, n in enumerate(CLASS_NAMES)}, open(os.path.join(args.export_model, "class_indices.json"), "w"))

    print(json.dumps({k: metrics["test"][k] for k in ("accuracy", "macro_f1")}, indent=1))
    print(rep_txt)
    print("confusion", cm.tolist())
    print("done", out)


if __name__ == "__main__":
    main()
