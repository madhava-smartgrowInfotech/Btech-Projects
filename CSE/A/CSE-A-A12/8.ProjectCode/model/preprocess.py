"""
preprocess.py
--------------
Image preprocessing pipeline for the Pneumonia Detection system.

Implements the preprocessing steps described in the project proposal:
    1. Resizing to a fixed input shape (224 x 224)
    2. Grayscale -> 3-channel conversion (for CNN compatibility)
    3. CLAHE (Contrast Limited Adaptive Histogram Equalization) to enhance
       lung markings, matching the "enhancement" step in the abstract.
    4. Normalization of pixel values to [0, 1]
    5. Data augmentation helpers used during training (rotation, zoom,
       flips, shifts) to improve model generalization.
"""

import cv2
import numpy as np

IMG_SIZE = (224, 224)


def apply_clahe(gray_image: np.ndarray) -> np.ndarray:
    """Apply CLAHE to a single-channel (grayscale) image."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray_image)


def load_and_preprocess_image(path_or_bytes, apply_enhancement: bool = True) -> np.ndarray:
    """
    Load an image from a file path (or raw bytes buffer), preprocess it,
    and return a float32 array of shape (224, 224, 3) normalized to [0, 1].
    """
    if isinstance(path_or_bytes, (bytes, bytearray)):
        arr = np.frombuffer(path_or_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    else:
        img = cv2.imread(str(path_or_bytes), cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError(f"Could not read image: {path_or_bytes}")

    # Resize to model input size
    img = cv2.resize(img, IMG_SIZE, interpolation=cv2.INTER_AREA)

    # Contrast Limited Adaptive Histogram Equalization
    if apply_enhancement:
        img = apply_clahe(img)

    # Mild denoising (helps with scanner/JPEG artefact noise)
    img = cv2.GaussianBlur(img, (3, 3), 0)

    # Grayscale -> 3-channel so it can feed either a custom CNN or a
    # transfer-learning backbone (DenseNet/ResNet/EfficientNet all expect 3ch)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # Normalize to [0, 1]
    img_norm = img_rgb.astype("float32") / 255.0

    return img_norm


def preprocess_for_display(path_or_bytes) -> np.ndarray:
    """Return an RGB uint8 image (224x224x3) suitable for overlaying a heatmap on."""
    normed = load_and_preprocess_image(path_or_bytes, apply_enhancement=True)
    return (normed * 255).astype("uint8")


def get_train_augmentor():
    """
    Returns a tf.keras ImageDataGenerator configured with the augmentation
    strategy referenced in the project abstract (rotation, zoom, shifts,
    horizontal flip). Only imported when training, so `preprocess.py` has
    no hard TensorFlow dependency for pure inference use.
    """
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    return ImageDataGenerator(
        rescale=1.0 / 255.0,
        rotation_range=12,
        width_shift_range=0.08,
        height_shift_range=0.08,
        shear_range=0.08,
        zoom_range=0.12,
        horizontal_flip=True,
        fill_mode="nearest",
    )


def get_val_augmentor():
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    return ImageDataGenerator(rescale=1.0 / 255.0)
