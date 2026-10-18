"""
gradcam.py
----------
Grad-CAM implementation used to generate the "heatmap-based visual
explanations" referenced in the project abstract -- highlighting the
lung regions that most influenced the model's prediction.
"""

import numpy as np
import cv2
import tensorflow as tf


def make_gradcam_heatmap(img_array, model, last_conv_layer_name, pred_index=None):
    """
    img_array: shape (1, H, W, 3), already preprocessed/normalized.
    Returns a 2D heatmap (values in [0, 1]) the same spatial size as the
    last convolutional feature map.
    """
    grad_model = tf.keras.models.Model(
        model.inputs, [model.get_layer(last_conv_layer_name).output, model.output]
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        if pred_index is None:
            pred_index = tf.argmax(predictions[0])
        class_channel = predictions[:, pred_index]

    grads = tape.gradient(class_channel, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy(), int(pred_index)


def overlay_heatmap(original_rgb_uint8, heatmap, alpha=0.4):
    """
    Overlay a Grad-CAM heatmap on top of the original (224,224,3) uint8
    RGB image. Returns a uint8 RGB image ready to save/display.
    """
    heatmap_resized = cv2.resize(heatmap, (original_rgb_uint8.shape[1], original_rgb_uint8.shape[0]))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

    overlaid = cv2.addWeighted(original_rgb_uint8, 1 - alpha, heatmap_color, alpha, 0)
    return overlaid
