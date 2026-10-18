"""
model_builder.py
-----------------
Defines the CNN architectures used by the Pneumonia Detection system.

Two options are provided:

1. build_custom_cnn()
   A compact CNN trained from scratch. It has no external weight
   dependency, so it works fully offline -- useful in restricted /
   air-gapped environments and as a lightweight baseline.

2. build_transfer_model()
   A transfer-learning model using a pretrained ImageNet backbone
   (DenseNet201 by default, matching the best-performing configuration
   reported in the reference literature). Requires internet access the
   first time it runs (to download ImageNet weights).

Both models output a 3-way softmax: [Normal, Bacterial Pneumonia, Viral
Pneumonia], matching the proposed system's classification objective.
"""

from tensorflow.keras import layers, models, Input
from tensorflow.keras.optimizers import Adam

CLASS_NAMES = ["Normal", "Bacterial Pneumonia", "Viral Pneumonia"]
INPUT_SHAPE = (224, 224, 3)


def build_custom_cnn(input_shape=INPUT_SHAPE, num_classes=3, learning_rate=1e-4):
    """A from-scratch CNN classifier. No pretrained weights required."""
    inputs = Input(shape=input_shape)

    x = layers.Conv2D(32, 3, padding="same", activation="relu")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(128, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(256, 3, padding="same", activation="relu", name="last_conv")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.35)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="pneumonia_custom_cnn")
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss="categorical_crossentropy",
        metrics=["accuracy", "AUC", "Precision", "Recall"],
    )
    return model


def build_transfer_model(input_shape=INPUT_SHAPE, num_classes=3,
                          backbone="densenet201", learning_rate=1e-4,
                          fine_tune_last_n=80):
    """
    Transfer-learning model. backbone in {"densenet201", "resnet152v2",
    "efficientnetb0", "densenet121"} -- mirrors the feature extractors
    compared in the reference study.
    """
    from tensorflow.keras.applications import (
        DenseNet201, DenseNet121, ResNet152V2, EfficientNetB0,
    )

    backbones = {
        "densenet201": DenseNet201,
        "densenet121": DenseNet121,
        "resnet152v2": ResNet152V2,
        "efficientnetb0": EfficientNetB0,
    }
    if backbone not in backbones:
        raise ValueError(f"Unknown backbone '{backbone}'. Choose from {list(backbones)}")

    base = backbones[backbone](
        include_top=False, weights="imagenet", input_shape=input_shape
    )
    base.trainable = True
    for layer in base.layers[:-fine_tune_last_n]:
        layer.trainable = False

    inputs = Input(shape=input_shape)
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D(name="last_conv_gap")(x)
    x = layers.Dense(512)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs, name=f"pneumonia_{backbone}")
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss="categorical_crossentropy",
        metrics=["accuracy", "AUC", "Precision", "Recall"],
    )
    return model


def find_last_conv_layer(model):
    """
    Utility used by Grad-CAM to locate the last actual convolutional layer
    (not a pooling/batchnorm layer that merely has a 4D output) so the
    heatmap reflects genuine learned spatial features.
    """
    conv_layer = None
    fallback_4d = None
    for layer in model.layers:
        try:
            shape = layer.output.shape
        except AttributeError:
            continue
        if shape is not None and len(shape) == 4:
            fallback_4d = layer.name
            if "conv" in layer.__class__.__name__.lower():
                conv_layer = layer.name
    if conv_layer is not None:
        return conv_layer
    if fallback_4d is not None:
        return fallback_4d
    raise ValueError("No 4D (conv) layer found in model for Grad-CAM.")
