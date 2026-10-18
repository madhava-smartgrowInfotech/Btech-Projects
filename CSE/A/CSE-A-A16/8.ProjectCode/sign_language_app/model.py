"""CNN architecture for ASL hand-gesture classification."""

from __future__ import annotations

from tensorflow.keras import layers, models, optimizers

from . import config


def build_cnn(
    num_classes: int,
    img_size: int = config.IMG_SIZE,
    channels: int = config.MODEL_CHANNELS,
    learning_rate: float = config.DEFAULT_LEARNING_RATE,
) -> models.Model:
    """Build and compile a compact CNN for real-time gesture classification."""

    model = models.Sequential(name="asl_cnn")
    model.add(layers.Input(shape=(img_size, img_size, channels)))

    # Block 1
    model.add(layers.Conv2D(32, (3, 3), padding="same", activation="relu"))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPooling2D((2, 2)))

    # Block 2
    model.add(layers.Conv2D(64, (3, 3), padding="same", activation="relu"))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Dropout(0.25))

    # Block 3
    model.add(layers.Conv2D(128, (3, 3), padding="same", activation="relu"))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Dropout(0.25))

    # Classifier head
    model.add(layers.Flatten())
    model.add(layers.Dense(256, activation="relu"))
    model.add(layers.BatchNormalization())
    model.add(layers.Dropout(0.4))
    model.add(layers.Dense(num_classes, activation="softmax"))

    model.compile(
        optimizer=optimizers.Adam(learning_rate=learning_rate),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model
