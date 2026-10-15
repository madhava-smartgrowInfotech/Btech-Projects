"""Network definitions and class lists (shared by training and inference)."""
import segmentation_models_pytorch as smp
import timm

XRAY_CLASSES = ["COVID-19", "Viral Pneumonia", "Lung Opacity", "Tuberculosis", "Normal"]
CT_CLASSES = ["Adenocarcinoma", "Large-cell Carcinoma", "Squamous-cell Carcinoma", "Normal"]


def make_classifier(num_classes: int, pretrained: bool = False):
    return timm.create_model("efficientnet_b0", pretrained=pretrained, num_classes=num_classes)


def make_backbone(pretrained: bool = False):
    """ImageNet EfficientNet-B0 without its head: 1280-d embeddings for the modality check."""
    return timm.create_model("efficientnet_b0", pretrained=pretrained, num_classes=0)


def make_unet(pretrained: bool = False):
    return smp.Unet("mobilenet_v2", encoder_weights="imagenet" if pretrained else None, in_channels=1, classes=1)
