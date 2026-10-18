"""Static About-page content.

Copied verbatim from sign_language_app/gui/about_tab.py (that module imports customtkinter,
which the API process does not need).
"""

ABSTRACT_TEXT = (
    "Sign language serves as an essential medium of communication for "
    "individuals with hearing and speech impairments, enabling them to "
    "interact effectively with others. However, the lack of widespread "
    "understanding of sign language often creates communication barriers "
    "between deaf and hearing communities. To overcome this challenge, "
    "intelligent sign language recognition systems have emerged as an "
    "effective solution.\n\n"
    "This project presents a Sign Language Recognition System based on "
    "Convolutional Neural Networks (CNNs) for the accurate identification "
    "of hand gestures representing American Sign Language (ASL) alphabets. "
    "The system captures real-time hand gesture images through a webcam "
    "and processes them using image preprocessing techniques such as "
    "grayscale conversion, noise reduction, segmentation, and "
    "normalization. The region of interest containing the hand gesture is "
    "extracted to improve recognition performance. A deep learning-based "
    "CNN model is trained on a dataset of hand gesture images to "
    "automatically learn discriminative features and classify different "
    "sign language symbols."
)

PIPELINE_STEPS = [
    "Webcam captures the live video stream.",
    "A region of interest (ROI) containing the hand is cropped each frame.",
    "The ROI is converted to grayscale and Gaussian-blurred (noise reduction).",
    "Otsu thresholding segments the hand silhouette from the background.",
    "The mask is resized and normalized to [0, 1] for the CNN.",
    "The trained CNN classifies the gesture into an ASL letter / control class.",
    "Predictions are smoothed over consecutive frames and typed into a sentence.",
    "The sentence can be read aloud with offline text-to-speech.",
]

BASE_PAPER = {
    "Title": "MAG-KD: Mask-Guided Adaptive Gating Knowledge Distillation for "
             "Skeleton-Based Sign Language Recognition on Edge Devices",
    "Published In": "IEEE Access",
    "Year": "2026",
    "DOI": "10.1109/access.2026.3681176",
}

ADOPTION_NOTE = (
    "The base paper advances skeleton-based recognition and knowledge "
    "distillation for accuracy and efficiency on edge devices. This project "
    "adopts the same underlying goal - accessible, real-time sign "
    "recognition - but implements it as a lightweight, self-contained CNN "
    "pipeline over segmented hand-gesture images (rather than pose "
    "skeletons), and extends the base paper's scope by rendering the "
    "recognized signs live as both on-screen text and speech."
)
