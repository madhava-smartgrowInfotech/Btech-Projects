"""
Trains the ResNet18 defect classifier on the processed NEU-CLS split
and writes the checkpoint + evaluation metrics used by the API.

Run:  python -m app.ml.train
"""
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from app.config import settings
from app.ml.labels import CLASS_NAMES
from app.ml.model import build_model

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "processed"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 18
LR = 3e-4

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_transforms():
    train_tf = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.Grayscale(num_output_channels=3),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    eval_tf = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.Grayscale(num_output_channels=3),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    return train_tf, eval_tf


def evaluate(model, loader) -> tuple[float, list[int], list[int]]:
    model.eval()
    correct, total = 0, 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
    return correct / total, all_preds, all_labels


def main():
    print(f"Device: {DEVICE}")
    train_tf, eval_tf = build_transforms()

    train_ds = datasets.ImageFolder(DATA_ROOT / "train", transform=train_tf)
    val_ds = datasets.ImageFolder(DATA_ROOT / "val", transform=eval_tf)
    test_ds = datasets.ImageFolder(DATA_ROOT / "test", transform=eval_tf)

    assert train_ds.classes == sorted(CLASS_NAMES), (
        f"Class order mismatch: {train_ds.classes} vs {sorted(CLASS_NAMES)}"
    )

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = build_model(num_classes=len(train_ds.classes)).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_val_acc = 0.0
    history = []
    t0 = time.time()

    for epoch in range(1, EPOCHS + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)

        scheduler.step()
        train_loss = running_loss / len(train_ds)
        val_acc, _, _ = evaluate(model, val_loader)
        history.append({"epoch": epoch, "train_loss": round(train_loss, 4), "val_accuracy": round(val_acc, 4)})
        print(f"Epoch {epoch:02d}/{EPOCHS}  loss={train_loss:.4f}  val_acc={val_acc:.4f}")

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            settings.model_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), settings.model_path)

    elapsed = time.time() - t0
    print(f"Training complete in {elapsed:.1f}s. Best val acc: {best_val_acc:.4f}")

    # Final evaluation on held-out test set using the best checkpoint
    model.load_state_dict(torch.load(settings.model_path, map_location=DEVICE))
    test_acc, preds, labels = evaluate(model, test_loader)
    report = classification_report(
        labels, preds, target_names=train_ds.classes, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(labels, preds).tolist()

    metrics = {
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "device": str(DEVICE),
        "epochs": EPOCHS,
        "best_val_accuracy": round(best_val_acc, 4),
        "test_accuracy": round(test_acc, 4),
        "classification_report": report,
        "confusion_matrix": cm,
        "class_names": train_ds.classes,
        "history": history,
        "dataset_sizes": {
            "train": len(train_ds),
            "val": len(val_ds),
            "test": len(test_ds),
        },
    }

    settings.metrics_path.write_text(json.dumps(metrics, indent=2))
    settings.class_names_path.write_text(json.dumps(train_ds.classes, indent=2))
    print(f"Test accuracy: {test_acc:.4f}")
    print(f"Saved model -> {settings.model_path}")
    print(f"Saved metrics -> {settings.metrics_path}")


if __name__ == "__main__":
    main()
