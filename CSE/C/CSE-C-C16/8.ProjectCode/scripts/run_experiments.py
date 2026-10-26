"""Real measurements for the AgriVision documentation: every number in docs/REPORT_FACTS.md comes from here.

The shipped product has no trained network (agrivision/models/ is empty) and answers with a colour/texture heuristic,
so there are two separate things to measure on the PlantDoc test split (236 field photos):

    heuristic   the engine the web app actually runs (agrivision/inference.py), 5 PYTHONHASHSEED values
    cnn         the compact CNN of agrivision/train.py, trained here (3 seeds; validation split carved from train,
                plus one run with the shipped protocol that selects the checkpoint on the test split)
    mobilenet   ImageNet MobileNetV2 transfer learning (not in the product; shows what the same data can give)
    baseline    hand-made colour/texture features + random forest / logistic regression

Usage (system python; TensorFlow must be imported before scikit-learn here, so every TF command is its own process):
    python scripts/run_experiments.py data
    set PYTHONHASHSEED=0 && python scripts/run_experiments.py heuristic
    python scripts/run_experiments.py cnn --seed 42 [--protocol shipped]
    python scripts/run_experiments.py mobilenet --seed 42
    python scripts/run_experiments.py baseline
    python scripts/run_experiments.py aggregate
Outputs: experiments/plantdoc/*.json (+ cache224.npz, models; git-ignored).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "datasets" / "plantdoc-images"
OUT = ROOT / "experiments" / "plantdoc"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "cache224.npz"
sys.path.insert(0, str(ROOT / "agrivision"))

HEALTHY = {"Apple_leaf", "Bell_pepper_leaf", "Blueberry_leaf", "Cherry_leaf", "Peach_leaf", "Raspberry_leaf",
           "Soyabean_leaf", "Strawberry_leaf", "Tomato_leaf", "grape_leaf"}
CROP_HINT = {"Apple": "apple", "Bell": "pepper", "Blueberry": "blueberry", "Cherry": "cherry", "Corn": "corn", "Peach": "peach",
             "Potato": "potato", "Raspberry": "raspberry", "Soyabean": "soybean", "Squash": "squash", "Strawberry": "strawberry",
             "Tomato": "tomato", "grape": "grape"}


def crop_of_folder(name: str) -> str:
    return CROP_HINT[name.split("_")[0]]


def classes() -> list[str]:
    return sorted(p.name for p in (DATA / "train").iterdir() if p.is_dir())


def list_split(split: str):
    cl = classes()
    items = []
    for ci, c in enumerate(cl):
        for f in (sorted((DATA / split / c).iterdir()) if (DATA / split / c).exists() else []):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                items.append((f, ci))
    return items


def metrics_from_preds(y_true, y_pred, probs=None, names=None):
    """accuracy, macro/weighted F1, per-class P/R/F1, confusion matrix, top-3 (if probs)."""
    import numpy as np
    n = len(names)
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    cm = np.zeros((n, n), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    per = {}
    f1s, ws, present = [], [], []
    for i in range(n):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        sup = int(cm[i, :].sum())
        per[names[i]] = dict(precision=pr, recall=rc, f1=f1, support=sup)
        if sup:
            f1s.append(f1)
            ws.append(sup)
            present.append(i)
    out = dict(n=int(len(y_true)), accuracy=float((y_true == y_pred).mean()),
               macro_f1=float(np.mean(f1s)), weighted_f1=float(np.average(f1s, weights=ws)),
               macro_precision=float(np.mean([per[names[i]]["precision"] for i in present])),
               macro_recall=float(np.mean([per[names[i]]["recall"] for i in present])),
               per_class=per, confusion=cm.tolist(), classes=list(names))
    if probs is not None:
        top3 = np.argsort(-np.asarray(probs), axis=1)[:, :3]
        out["top3_accuracy"] = float(np.mean([t in row for t, row in zip(y_true, top3)]))
    return out


def derived(names, y_true, y_pred):
    """crop-level and healthy-vs-diseased accuracy from folder names."""
    import numpy as np
    crop = [crop_of_folder(n) for n in names]
    hl = [n in HEALTHY for n in names]
    yt, yp = np.asarray(y_true), np.asarray(y_pred)
    return dict(crop_accuracy=float(np.mean([crop[t] == crop[p] for t, p in zip(yt, yp)])),
                healthy_vs_diseased_accuracy=float(np.mean([hl[t] == hl[p] for t, p in zip(yt, yp)])),
                diseased_recall=float(np.mean([not hl[p] for t, p in zip(yt, yp) if not hl[t]])),
                healthy_recall=float(np.mean([hl[p] for t, p in zip(yt, yp) if hl[t]])))


# ----------------------------------------------------------------------------------------------- data
def cmd_data(_a):
    import numpy as np
    from PIL import Image
    names = classes()
    out = {"classes": np.array(names)}
    for split in ("train", "test"):
        items = list_split(split)
        X = np.zeros((len(items), 224, 224, 3), dtype=np.uint8)
        y = np.zeros(len(items), dtype=np.int64)
        for i, (f, c) in enumerate(items):
            with Image.open(f) as im:
                im.draft("RGB", (448, 448))
                X[i] = np.asarray(im.convert("RGB").resize((224, 224), Image.BILINEAR))
            y[i] = c
        out[f"X_{split}"], out[f"y_{split}"] = X, y
        print(split, X.shape, flush=True)
    np.savez(CACHE, **out)
    sizes = {}
    for split in ("train", "test"):
        cnt = {n: 0 for n in names}
        for f, c in list_split(split):
            cnt[names[c]] += 1
        sizes[split] = cnt
    (OUT / "dataset.json").write_text(json.dumps(dict(classes=names, counts=sizes, n_train=sum(sizes["train"].values()),
                                                      n_test=sum(sizes["test"].values())), indent=1))


def load_cache():
    import numpy as np
    z = np.load(CACHE)
    return z["X_train"], z["y_train"], z["X_test"], z["y_test"], [str(s) for s in z["classes"]]


# ----------------------------------------------------------------------------------------------- heuristic
def cmd_heuristic(a):
    import numpy as np
    import inference
    from disease_db import CLASSES, _crop_of
    names = classes()
    canon = [inference.PLANTDOC_MAP[n] for n in names]
    assert all(c in CLASSES for c in canon)
    canon_idx = {c: i for i, c in enumerate(CLASSES)}
    seed = os.environ.get("PYTHONHASHSEED", "random")
    res = {"hashseed": seed}
    for split in ("test", "train"):
        items = list_split(split)
        for mode in ("crop_hint", "general"):
            yt, yp, top3, failed = [], [], [], 0
            t0 = time.perf_counter()
            for f, c in items:
                hint = crop_of_folder(names[c]) if mode == "crop_hint" else "general"
                try:
                    preds = [x[0] for x in inference._heuristic_predict(f.read_bytes(), hint)[0]]
                except IndexError:       # crops with fewer than 3 candidate classes: the product returns HTTP 400
                    failed += 1
                    preds = [-1, -1, -1]
                yt.append(canon_idx[canon[c]])
                yp.append(canon_idx[preds[0]] if preds[0] != -1 else -1)
                top3.append([canon_idx[p] if p != -1 else -1 for p in preds])
            dt = (time.perf_counter() - t0) / len(items) * 1000
            yt, yp = np.array(yt), np.array(yp)
            hl = [("healthy" in CLASSES[i].lower()) for i in range(len(CLASSES))] + [False]   # index -1 = no answer
            crop = [_crop_of(c) for c in CLASSES] + ["<none>"]
            ok = yp != -1
            res[f"{split}_{mode}"] = dict(
                n=len(items), failed_share=failed / len(items), accuracy_on_answered=float((yt[ok] == yp[ok]).mean()) if ok.any() else 0.0,
                accuracy=float((yt == yp).mean()),
                top3_accuracy=float(np.mean([t in r for t, r in zip(yt, top3)])),
                crop_accuracy=float(np.mean([crop[t] == crop[p] for t, p in zip(yt, yp)])),
                healthy_vs_diseased_accuracy=float(np.mean([hl[t] == hl[p] for t, p in zip(yt, yp)])),
                diseased_recall=float(np.mean([not hl[p] for t, p in zip(yt, yp) if not hl[t]])),
                healthy_recall=float(np.mean([hl[p] for t, p in zip(yt, yp) if hl[t]])),
                predicted_healthy_share=float(np.mean([hl[p] for p in yp])),
                macro_f1=metrics_from_preds(yt, np.where(ok, yp, len(CLASSES)), None, CLASSES + ["<none>"])["macro_f1"],
                ms_per_image_in_process=dt)
            if split == "test" and mode == "crop_hint":
                cm = metrics_from_preds(yt, np.where(ok, yp, len(CLASSES)), None, CLASSES + ["<none>"])
                res["test_crop_hint_per_class"] = {k: v for k, v in cm["per_class"].items() if v["support"]}
    # chance levels
    cnt = json.loads((OUT / "dataset.json").read_text())["counts"]["test"]
    cands = []
    for n, k in cnt.items():
        if k:
            hint = crop_of_folder(n)
            cands += [len(inference._candidates(hint))] * k
    res["chance_with_crop_hint"] = float(np.mean([1 / c for c in cands]))
    res["chance_general"] = 1 / len(CLASSES)
    res["majority_class_test"] = max(cnt.values()) / sum(cnt.values())
    (OUT / f"heuristic_hashseed_{seed}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k.startswith("test_") and not k.endswith("per_class")}, indent=1))


# ----------------------------------------------------------------------------------------------- cnn
def stratified_val(y, frac, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    val = []
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        k = int(round(len(idx) * frac)) if len(idx) >= 5 else 0
        val += list(idx[:k])
    val = np.array(sorted(val))
    tr = np.setdiff1d(np.arange(len(y)), val)
    return tr, val


def cmd_cnn(a):
    import tensorflow as tf  # first import, see module docstring
    import numpy as np
    import importlib.util
    spec = importlib.util.spec_from_file_location("train_mod", ROOT / "agrivision" / "train.py")
    tm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tm)
    Xtr, ytr, Xte, yte, names = load_cache()
    tf.keras.utils.set_random_seed(a.seed)
    if a.protocol == "shipped":
        Xt, yt, Xv, yv = Xtr, ytr, Xte, yte                       # train.py: validation = test split
    else:
        tr, va = stratified_val(ytr, 0.10, a.seed)
        Xt, yt, Xv, yv = Xtr[tr], ytr[tr], Xtr[va], ytr[va]
    model = tm.build_model(len(names), 224)
    cbs = [tf.keras.callbacks.EarlyStopping(patience=a.patience, restore_best_weights=True, monitor="val_accuracy")]
    if not a.no_lr_decay:
        cbs.append(tf.keras.callbacks.ReduceLROnPlateau(patience=2, factor=0.5, monitor="val_loss"))
    t0 = time.time()
    h = model.fit(Xt.astype("float32"), yt, validation_data=(Xv.astype("float32"), yv), epochs=a.epochs, batch_size=32,
                  callbacks=cbs, verbose=2)
    train_s = time.time() - t0
    probs = model.predict(Xte.astype("float32"), batch_size=32, verbose=0)
    pred = probs.argmax(1)
    m = metrics_from_preds(yte, pred, probs, names)
    m.update(derived(names, yte, pred))
    # train accuracy (clean pass, no augmentation) for the generalisation gap
    ptr = model.predict(Xt.astype("float32"), batch_size=64, verbose=0).argmax(1)
    # single-image latency on CPU (batch of 1, after warm-up)
    lat = []
    for i in range(8):
        model.predict(Xte[i:i + 1].astype("float32"), verbose=0)
    for i in range(min(100, len(Xte))):
        t = time.perf_counter()
        model.predict(Xte[i:i + 1].astype("float32"), verbose=0)
        lat.append((time.perf_counter() - t) * 1000)
    m.update(seed=a.seed, protocol=a.protocol, params=int(model.count_params()), epochs_run=len(h.history["loss"]),
             best_val_accuracy=float(max(h.history["val_accuracy"])), train_accuracy=float((ptr == yt).mean()),
             n_train=int(len(yt)), n_val=int(len(yv)), train_seconds=train_s,
             latency_ms_median=float(np.median(lat)), latency_ms_p95=float(np.percentile(lat, 95)),
             history={k: [float(x) for x in v] for k, v in h.history.items()})
    tag = f"cnn_{a.tag or a.protocol}_seed{a.seed}"
    (OUT / f"{tag}.json").write_text(json.dumps(m, indent=1))
    if a.seed == 42 and a.protocol == "heldout" and not a.tag:
        model.save(OUT / "cnn_seed42.keras")
        np.save(OUT / "cnn_seed42_probs.npy", probs)
    print(tag, "test acc %.4f macroF1 %.4f top3 %.4f epochs %d %.0fs params %d" % (
        m["accuracy"], m["macro_f1"], m["top3_accuracy"], m["epochs_run"], train_s, m["params"]))


# ----------------------------------------------------------------------------------------------- mobilenet
def cmd_mobilenet(a):
    import tensorflow as tf
    import numpy as np
    Xtr, ytr, Xte, yte, names = load_cache()
    tf.keras.utils.set_random_seed(a.seed)
    tr, va = stratified_val(ytr, 0.10, a.seed)
    base = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
    base.trainable = False
    aug = tf.keras.Sequential([tf.keras.layers.RandomFlip("horizontal"), tf.keras.layers.RandomRotation(0.08),
                               tf.keras.layers.RandomZoom(0.1)])
    inp = tf.keras.Input((224, 224, 3))
    x = aug(inp)
    x = tf.keras.layers.Rescaling(1 / 127.5, offset=-1.0)(x)          # same scaling as mobilenet_v2.preprocess_input
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    out = tf.keras.layers.Dense(len(names), activation="softmax")(x)
    model = tf.keras.Model(inp, out)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    cbs = [tf.keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True, monitor="val_accuracy")]
    t0 = time.time()
    f32 = lambda z: z.astype("float32")
    h1 = model.fit(f32(Xtr[tr]), ytr[tr], validation_data=(f32(Xtr[va]), ytr[va]), epochs=a.epochs, batch_size=32, callbacks=cbs, verbose=2)
    head_s = time.time() - t0
    head_probs = model.predict(f32(Xte), batch_size=32, verbose=0)
    head = metrics_from_preds(yte, head_probs.argmax(1), head_probs, names)
    # fine-tune the top of the backbone at a low learning rate
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-4), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    cbs = [tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True, monitor="val_accuracy")]
    h2 = model.fit(f32(Xtr[tr]), ytr[tr], validation_data=(f32(Xtr[va]), ytr[va]), epochs=a.ft_epochs, batch_size=32, callbacks=cbs, verbose=2)
    total_s = time.time() - t0
    probs = model.predict(f32(Xte), batch_size=32, verbose=0)
    pred = probs.argmax(1)
    m = metrics_from_preds(yte, pred, probs, names)
    m.update(derived(names, yte, pred))
    lat = []
    for i in range(5):
        model.predict(f32(Xte[i:i + 1]), verbose=0)
    for i in range(60):
        t = time.perf_counter()
        model.predict(f32(Xte[i:i + 1]), verbose=0)
        lat.append((time.perf_counter() - t) * 1000)
    m.update(seed=a.seed, params=int(model.count_params()), head_only=dict(accuracy=head["accuracy"], macro_f1=head["macro_f1"], top3_accuracy=head["top3_accuracy"]),
             head_epochs=len(h1.history["loss"]), ft_epochs=len(h2.history["loss"]), train_seconds=total_s, head_seconds=head_s,
             latency_ms_median=float(np.median(lat)), latency_ms_p95=float(np.percentile(lat, 95)),
             best_val_accuracy=float(max(h2.history["val_accuracy"])))
    (OUT / f"mobilenet_seed{a.seed}.json").write_text(json.dumps(m, indent=1))
    print("mobilenet seed", a.seed, "head acc %.4f -> fine-tuned acc %.4f macroF1 %.4f top3 %.4f %.0fs" % (
        head["accuracy"], m["accuracy"], m["macro_f1"], m["top3_accuracy"], total_s))


# ----------------------------------------------------------------------------------------------- classical baseline
def hand_features(X):
    import numpy as np
    import cv2
    out = []
    for im in X:
        hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
        f = []
        for ch, bins, rng in ((0, 16, 180), (1, 8, 256), (2, 8, 256)):
            h = cv2.calcHist([hsv], [ch], None, [bins], [0, rng]).ravel()
            f += list(h / h.sum())
        gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        gx, gy = cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1)
        mag = np.sqrt(gx ** 2 + gy ** 2)
        f += [gray.mean() / 255, gray.std() / 255, mag.mean() / 255, mag.std() / 255, (mag > 60).mean()]
        f += list((im.reshape(-1, 3).mean(0) / 255)) + list((im.reshape(-1, 3).std(0) / 255))
        out.append(f)
    return np.array(out, dtype=np.float32)


def cmd_baseline(a):
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    Xtr, ytr, Xte, yte, names = load_cache()
    Ftr, Fte = hand_features(Xtr), hand_features(Xte)
    res = {}
    for name, clf in (("random_forest", RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=4, class_weight="balanced")),
                      ("logistic_regression", make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0)))):
        clf.fit(Ftr, ytr)
        probs = clf.predict_proba(Fte)
        full = np.zeros((len(Fte), len(names)))
        full[:, clf.classes_ if hasattr(clf, "classes_") else clf[-1].classes_] = probs
        pred = full.argmax(1)
        m = metrics_from_preds(yte, pred, full, names)
        m.update(derived(names, yte, pred))
        m.pop("confusion")
        res[name] = m
        print(name, "acc %.4f macroF1 %.4f" % (m["accuracy"], m["macro_f1"]))
    (OUT / "baseline.json").write_text(json.dumps(res, indent=1))


# ----------------------------------------------------------------------------------------------- aggregate
def agg(vals):
    import numpy as np
    v = np.array(vals, dtype=float)
    return dict(mean=float(v.mean()), std=float(v.std(ddof=0)), values=[float(x) for x in v])


def cmd_aggregate(_a):
    import glob
    out = {}
    hs = [json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(OUT / "heuristic_hashseed_*.json")))]
    if hs:
        out["heuristic"] = {"n_hashseeds": len(hs), "chance_with_crop_hint": hs[0]["chance_with_crop_hint"], "chance_general": hs[0]["chance_general"],
                            "majority_class_test": hs[0]["majority_class_test"]}
        for key in ("test_crop_hint", "test_general", "train_crop_hint", "train_general"):
            out["heuristic"][key] = {k: agg([h[key][k] for h in hs]) for k in hs[0][key] if k != "n"}
            out["heuristic"][key]["n"] = hs[0][key]["n"]
        shipped = [h for h in hs if h["hashseed"] == "0"]
        if shipped:
            out["heuristic"]["shipped_hashseed0"] = {k: shipped[0][k] for k in ("test_crop_hint", "test_general")}
            out["heuristic"]["per_class_hashseed0"] = shipped[0]["test_crop_hint_per_class"]
    for tag, pat in (("cnn", "cnn_heldout_seed*.json"), ("cnn_shipped_protocol", "cnn_shipped_seed*.json"), ("cnn_tuned", "cnn_tuned_seed*.json"), ("mobilenet", "mobilenet_seed*.json")):
        runs = [json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(OUT / pat)))]
        if not runs:
            continue
        block = {"seeds": [r["seed"] for r in runs]}
        for k in ("accuracy", "macro_f1", "weighted_f1", "top3_accuracy", "crop_accuracy", "healthy_vs_diseased_accuracy", "diseased_recall",
                  "healthy_recall", "macro_precision", "macro_recall", "params", "epochs_run", "train_seconds", "latency_ms_median",
                  "latency_ms_p95", "best_val_accuracy", "train_accuracy"):
            if k in runs[0]:
                block[k] = agg([r[k] for r in runs])
        if tag == "mobilenet":
            block["head_only_accuracy"] = agg([r["head_only"]["accuracy"] for r in runs])
            block["head_only_macro_f1"] = agg([r["head_only"]["macro_f1"] for r in runs])
        block["first_run"] = {k: runs[0][k] for k in ("per_class", "confusion", "classes", "seed") if k in runs[0]}
        if "history" in runs[0]:
            block["first_run"]["history"] = runs[0]["history"]
        out[tag] = block
    if (OUT / "baseline.json").exists():
        out["baseline"] = {k: {x: v[x] for x in v if x not in ("per_class", "classes")}
                           for k, v in json.loads((OUT / "baseline.json").read_text()).items()}
    out["dataset"] = json.loads((OUT / "dataset.json").read_text())
    (OUT / "metrics.json").write_text(json.dumps(out, indent=1))
    print("wrote", OUT / "metrics.json", list(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("data")
    sub.add_parser("heuristic")
    sub.add_parser("baseline")
    sub.add_parser("aggregate")
    c = sub.add_parser("cnn")
    c.add_argument("--seed", type=int, default=42)
    c.add_argument("--protocol", choices=["heldout", "shipped"], default="heldout")
    c.add_argument("--epochs", type=int, default=60)
    c.add_argument("--patience", type=int, default=8)
    c.add_argument("--no-lr-decay", action="store_true", dest="no_lr_decay", help="keep Adam at 1e-3 (ReduceLROnPlateau off)")
    c.add_argument("--tag", default="", help="output name, e.g. 'tuned'")
    m = sub.add_parser("mobilenet")
    m.add_argument("--seed", type=int, default=42)
    m.add_argument("--epochs", type=int, default=20)
    m.add_argument("--ft-epochs", type=int, default=12, dest="ft_epochs")
    args = ap.parse_args()
    globals()["cmd_" + args.cmd](args)
