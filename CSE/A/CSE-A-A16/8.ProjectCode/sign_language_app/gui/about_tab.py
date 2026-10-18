"""About tab: project abstract, pipeline summary, and base-paper reference."""

from __future__ import annotations

import customtkinter as ctk

from . import theme

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
    "1. Webcam captures the live video stream.",
    "2. A region of interest (ROI) containing the hand is cropped each frame.",
    "3. The ROI is converted to grayscale and Gaussian-blurred (noise reduction).",
    "4. Otsu thresholding segments the hand silhouette from the background.",
    "5. The mask is resized and normalized to [0, 1] for the CNN.",
    "6. The trained CNN classifies the gesture into an ASL letter / control class.",
    "7. Predictions are smoothed over consecutive frames and typed into a sentence.",
    "8. The sentence can be read aloud with offline text-to-speech.",
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
    "adopts the same underlying goal — accessible, real-time sign "
    "recognition — but implements it as a lightweight, self-contained CNN "
    "pipeline over segmented hand-gesture images (rather than pose "
    "skeletons), and extends the base paper's scope by rendering the "
    "recognized signs live as both on-screen text and speech."
)


class AboutFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        title_card = theme.section_card(scroll)
        title_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(
            title_card,
            text="Sign Language Recognition System (CNN-based)",
            font=theme.font(20, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(
            title_card, text="CSE-A | Batch 16", font=theme.font(13), text_color=theme.TEXT_MUTED
        ).pack(anchor="w", padx=18, pady=(0, 16))

        abstract_card = theme.section_card(scroll)
        abstract_card.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(abstract_card, text="Abstract", font=theme.font(16, "bold")).pack(
            anchor="w", padx=18, pady=(16, 6)
        )
        ctk.CTkLabel(
            abstract_card, text=ABSTRACT_TEXT, font=theme.font(13), text_color=theme.TEXT,
            wraplength=760, justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 16))

        pipeline_card = theme.section_card(scroll)
        pipeline_card.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(pipeline_card, text="End-to-End Pipeline", font=theme.font(16, "bold")).pack(
            anchor="w", padx=18, pady=(16, 6)
        )
        for step in PIPELINE_STEPS:
            ctk.CTkLabel(
                pipeline_card, text=step, font=theme.font(13), text_color=theme.TEXT,
                wraplength=760, justify="left",
            ).pack(anchor="w", padx=18, pady=2)
        ctk.CTkLabel(pipeline_card, text="", height=8).pack()

        paper_card = theme.section_card(scroll)
        paper_card.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(paper_card, text="Base Paper", font=theme.font(16, "bold")).pack(
            anchor="w", padx=18, pady=(16, 6)
        )
        for key, value in BASE_PAPER.items():
            row = ctk.CTkFrame(paper_card, fg_color="transparent")
            row.pack(anchor="w", padx=18, pady=1, fill="x")
            ctk.CTkLabel(row, text=f"{key}:", font=theme.font(13, "bold"), width=110, anchor="w").pack(side="left")
            ctk.CTkLabel(
                row, text=value, font=theme.font(13), text_color=theme.TEXT_MUTED,
                wraplength=600, justify="left", anchor="w",
            ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            paper_card, text="How this project adopts it", font=theme.font(14, "bold")
        ).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(
            paper_card, text=ADOPTION_NOTE, font=theme.font(13), text_color=theme.TEXT,
            wraplength=760, justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 16))

    def on_show(self):
        pass

    def on_hide(self):
        pass
