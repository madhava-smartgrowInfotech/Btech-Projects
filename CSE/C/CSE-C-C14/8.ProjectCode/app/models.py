"""Model definitions and checkpoint loading for the heterogeneous ensemble.

Routes:
  A1/A2 - EfficientNet-B0, 224x224, binary head (different augmentation regimes)
  B     - ResNet50, 320x320, binary head, horizontal-flip TTA
  C     - MobileNetV3-Large, 224x224, binary head, trained with focal loss
"""
import os

import torch
import torch.nn as nn
from torchvision import models

from . import config


def build_efficientnet_b0(num_classes=2):
    try:
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        model = models.efficientnet_b0(weights=weights)
    except Exception:
        model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, num_classes),
    )
    return model


def build_resnet50(num_classes=2):
    try:
        weights = models.ResNet50_Weights.IMAGENET1K_V1
        model = models.resnet50(weights=weights)
    except Exception:
        model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def build_mobilenetv3_large(num_classes=2):
    try:
        weights = models.MobileNet_V3_Large_Weights.IMAGENET1K_V1
        model = models.mobilenet_v3_large(weights=weights)
    except Exception:
        model = models.mobilenet_v3_large(weights=None)
    in_features = model.classifier[0].in_features
    model.classifier = nn.Sequential(
        nn.Linear(in_features, 1280),
        nn.Hardswish(),
        nn.Dropout(0.2),
        nn.Linear(1280, num_classes),
    )
    return model


BUILDERS = {
    "a1": build_efficientnet_b0,
    "a2": build_efficientnet_b0,
    "b": build_resnet50,
    "c": build_mobilenetv3_large,
}


def load_branch_model(branch, device):
    """Build the architecture for a branch and load its checkpoint."""
    if branch not in BUILDERS:
        raise ValueError(f"Unknown branch: {branch}")
    model = BUILDERS[branch]()
    ckpt_path = config.MODEL_FILES[branch]
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Model artifact missing for branch '{branch}': {ckpt_path}")
    state = torch.load(ckpt_path, map_location=device)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


def missing_artifacts():
    return {k: p for k, p in config.MODEL_FILES.items() if not os.path.exists(p)}
