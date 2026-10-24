"""Train a compact PD36-C-style CNN on datasets/plantdoc-images.

Usage:
    python train.py                  # full train (28 classes, ~15 epochs)
    python train.py --quick          # 2-epoch smoke test on a subset
    python train.py --epochs 30 --img-size 224 --batch 32

Outputs:
    models/plantdoc_cnn.h5     trained weights (auto-loaded by inference.py)
    models/labels.json         class index -> display name
    models/history.json        train/val curves
"""
from __future__ import annotations
import argparse, json, os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if False else os.getcwd(), "datasets", "plantdoc-images")
# resolve relative to project root (this file lives in agrivision/)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "datasets", "plantdoc-images")
MODEL_DIR = os.path.join(HERE, "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def build_model(num_classes: int, img_size: int = 224):
    """Compact CNN (~1.1M params): depthwise-separable blocks + GAP head."""
    import tensorflow as tf
    from tensorflow import keras
    inp = keras.Input(shape=(img_size, img_size, 3))
    x = keras.layers.Rescaling(1.0 / 255)(inp)
    # light on-model augmentation (train-time only effect via training=True)
    aug = keras.Sequential([
        keras.layers.RandomFlip("horizontal"),
        keras.layers.RandomRotation(0.08),
        keras.layers.RandomZoom(0.1),
        keras.layers.RandomContrast(0.1),
    ])
    x = aug(x)
    for filters, stride in [(32, 2), (64, 1), (128, 2), (256, 2), (256, 1)]:
        x = keras.layers.SeparableConv2D(filters, 3, strides=stride, padding="same", activation="relu")(x)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.MaxPooling2D(2, padding="same")(x)
        x = keras.layers.Dropout(0.15)(x)
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.Dropout(0.3)(x)
    x = keras.layers.Dense(256, activation="relu")(x)
    out = keras.layers.Dense(num_classes, activation="softmax")(x)
    model = keras.Model(inp, out, name="PD36-C-plantdoc")
    model.compile(optimizer=keras.optimizers.Adam(1e-3),
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--img-size", type=int, default=224)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--quick", action="store_true", help="2 epochs on 10%% data (pipeline check)")
    args = ap.parse_args()

    import tensorflow as tf
    train_ds = tf.keras.utils.image_dataset_from_directory(
        os.path.join(DATA, "train"), image_size=(args.img_size, args.img_size),
        batch_size=args.batch, shuffle=True, seed=42)
    test_ds = tf.keras.utils.image_dataset_from_directory(
        os.path.join(DATA, "test"), image_size=(args.img_size, args.img_size),
        batch_size=args.batch, shuffle=False)
    class_names = train_ds.class_names
    print(f"Classes ({len(class_names)}): {class_names}")

    if args.quick:
        args.epochs = 2
        train_ds = train_ds.take(8)
        test_ds = test_ds.take(3)

    train_ds = train_ds.prefetch(tf.data.AUTOTUNE)
    test_ds = test_ds.prefetch(tf.data.AUTOTUNE)

    model = build_model(len(class_names), args.img_size)
    model.summary()
    print(f"Params: {model.count_params():,}")

    ckpt = os.path.join(MODEL_DIR, "plantdoc_cnn.h5")
    cbs = [tf.keras.callbacks.ModelCheckpoint(ckpt, save_best_only=True, monitor="val_accuracy", mode="max"),
           tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_accuracy"),
           tf.keras.callbacks.ReduceLROnPlateau(patience=2, factor=0.5, monitor="val_loss")]
    hist = model.fit(train_ds, validation_data=test_ds, epochs=args.epochs, callbacks=cbs)
    model.save(ckpt)

    loss, acc = model.evaluate(test_ds, verbose=0)
    print(f"\nTEST accuracy: {acc * 100:.2f}%  loss: {loss:.4f}")

    with open(os.path.join(MODEL_DIR, "labels.json"), "w") as f:
        json.dump(class_names, f, indent=1)
    with open(os.path.join(MODEL_DIR, "history.json"), "w") as f:
        json.dump({k: [float(v) for v in vals] for k, vals in hist.history.items()}, f)
    print(f"Saved: {ckpt} + labels.json + history.json")


if __name__ == "__main__":
    main()
