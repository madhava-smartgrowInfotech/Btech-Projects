"""
train.py
--------
Training script for the Pneumonia Detection CNN.

Expected dataset folder layout (standard Kaggle "Chest X-Ray Images
(Pneumonia)" style, extended to 3 classes if you have bacterial/viral
sub-labels; falls back to 2-class NORMAL/PNEUMONIA if not):

    dataset/
        train/
            NORMAL/
            BACTERIA/      (or PNEUMONIA/ for 2-class)
            VIRUS/
        val/
            NORMAL/
            BACTERIA/
            VIRUS/
        test/
            NORMAL/
            BACTERIA/
            VIRUS/

Usage:
    python model/train.py --data_dir dataset --backbone custom --epochs 30
    python model/train.py --data_dir dataset --backbone densenet201 --epochs 20
"""

import argparse
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

from model.model_builder import build_custom_cnn, build_transfer_model, INPUT_SHAPE
from model.preprocess import get_train_augmentor, get_val_augmentor


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data_dir", type=str, required=True,
                    help="Path to dataset root containing train/ val/ test/")
    p.add_argument("--backbone", type=str, default="custom",
                    choices=["custom", "densenet201", "densenet121", "resnet152v2", "efficientnetb0"])
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--out_dir", type=str, default="saved_models")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    train_dir = os.path.join(args.data_dir, "train")
    val_dir = os.path.join(args.data_dir, "val")
    test_dir = os.path.join(args.data_dir, "test")

    train_gen = get_train_augmentor().flow_from_directory(
        train_dir, target_size=INPUT_SHAPE[:2], batch_size=args.batch_size,
        class_mode="categorical", color_mode="rgb",
    )
    val_gen = get_val_augmentor().flow_from_directory(
        val_dir, target_size=INPUT_SHAPE[:2], batch_size=args.batch_size,
        class_mode="categorical", color_mode="rgb", shuffle=False,
    )
    test_gen = get_val_augmentor().flow_from_directory(
        test_dir, target_size=INPUT_SHAPE[:2], batch_size=args.batch_size,
        class_mode="categorical", color_mode="rgb", shuffle=False,
    )

    num_classes = train_gen.num_classes
    class_indices = train_gen.class_indices  # e.g. {'BACTERIA':0,'NORMAL':1,'VIRUS':2}
    idx_to_class = {v: k for k, v in class_indices.items()}
    print("Detected classes:", class_indices)

    if args.backbone == "custom":
        model = build_custom_cnn(num_classes=num_classes, learning_rate=args.lr)
    else:
        model = build_transfer_model(num_classes=num_classes, backbone=args.backbone, learning_rate=args.lr)

    model.summary()

    from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

    ckpt_path = os.path.join(args.out_dir, "pneumonia_model.h5")
    callbacks = [
        ModelCheckpoint(ckpt_path, monitor="val_accuracy", save_best_only=True, verbose=1),
        EarlyStopping(monitor="val_loss", patience=6, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-7),
    ]

    history = model.fit(
        train_gen, validation_data=val_gen, epochs=args.epochs, callbacks=callbacks,
    )

    # Save class index mapping alongside the model so app.py can decode predictions
    with open(os.path.join(args.out_dir, "class_indices.json"), "w") as f:
        json.dump(idx_to_class, f)

    # --- Training curves ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history["accuracy"], label="train_acc")
    axes[0].plot(history.history["val_accuracy"], label="val_acc")
    axes[0].set_title("Accuracy")
    axes[0].legend()
    axes[1].plot(history.history["loss"], label="train_loss")
    axes[1].plot(history.history["val_loss"], label="val_loss")
    axes[1].set_title("Loss")
    axes[1].legend()
    fig.savefig(os.path.join(args.out_dir, "training_curves.png"))

    # --- Test set evaluation ---
    test_gen.reset()
    y_true = test_gen.classes
    y_pred_probs = model.predict(test_gen)
    y_pred = np.argmax(y_pred_probs, axis=1)

    report = classification_report(
        y_true, y_pred, target_names=[idx_to_class[i] for i in range(num_classes)]
    )
    print(report)
    with open(os.path.join(args.out_dir, "classification_report.txt"), "w") as f:
        f.write(report)

    cm = confusion_matrix(y_true, y_pred)
    fig2, ax2 = plt.subplots(figsize=(5, 5))
    im = ax2.imshow(cm, cmap="Blues")
    ax2.set_xticks(range(num_classes))
    ax2.set_yticks(range(num_classes))
    ax2.set_xticklabels([idx_to_class[i] for i in range(num_classes)], rotation=45)
    ax2.set_yticklabels([idx_to_class[i] for i in range(num_classes)])
    for i in range(num_classes):
        for j in range(num_classes):
            ax2.text(j, i, cm[i, j], ha="center", va="center")
    ax2.set_xlabel("Predicted")
    ax2.set_ylabel("True")
    fig2.colorbar(im)
    fig2.tight_layout()
    fig2.savefig(os.path.join(args.out_dir, "confusion_matrix.png"))

    print(f"\nModel saved to: {ckpt_path}")
    print(f"Class mapping saved to: {os.path.join(args.out_dir, 'class_indices.json')}")


if __name__ == "__main__":
    main()
