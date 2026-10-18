"""Recognize tab: live webcam feed, real-time CNN prediction, sentence
building and text-to-speech playback.
"""

from __future__ import annotations

import cv2
import customtkinter as ctk
from PIL import Image

from .. import config, tts
from ..preprocessing import get_roi_box, crop_roi
from . import theme


class RecognizeFrame(ctk.CTkFrame):
    def __init__(self, parent, camera, recognizer):
        super().__init__(parent, fg_color="transparent")
        self.camera = camera
        self.recognizer = recognizer
        self.sentence = ""
        self._running = False
        self._frame_count = 0

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_video_panel()
        self._build_side_panel()

    # ------------------------------------------------------------------ UI
    def _build_video_panel(self):
        card = theme.section_card(self)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            card, text="Live Camera", font=theme.font(16, "bold"), text_color=theme.TEXT
        )
        header.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self.video_label = ctk.CTkLabel(card, text="", fg_color=theme.BG, corner_radius=10)
        self.video_label.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))

        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))

        self.toggle_btn = theme.primary_button(
            controls, text="Start Camera", command=self.toggle_camera, width=160
        )
        self.toggle_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            controls, text="Camera stopped", text_color=theme.TEXT_MUTED, font=theme.font(12)
        )
        self.status_label.pack(side="left", padx=14)

    def _build_side_panel(self):
        card = theme.section_card(self)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(card, text="Prediction", font=theme.font(16, "bold"))
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self.mask_label = ctk.CTkLabel(card, text="", fg_color=theme.BG, corner_radius=10)
        self.mask_label.configure(width=160, height=160)
        self.mask_label.grid(row=1, column=0, pady=6)

        self.letter_label = ctk.CTkLabel(
            card, text="—", font=theme.font(56, "bold"), text_color=theme.ACCENT
        )
        self.letter_label.grid(row=2, column=0, pady=(4, 0))

        self.confidence_bar = ctk.CTkProgressBar(card, progress_color=theme.ACCENT, width=220)
        self.confidence_bar.set(0)
        self.confidence_bar.grid(row=3, column=0, pady=(10, 2))

        self.confidence_label = ctk.CTkLabel(
            card, text="confidence: 0%", text_color=theme.TEXT_MUTED, font=theme.font(12)
        )
        self.confidence_label.grid(row=4, column=0, pady=(0, 12))

        self.model_status = ctk.CTkLabel(
            card, text="", font=theme.font(12), text_color=theme.WARNING, wraplength=260
        )
        self.model_status.grid(row=5, column=0, padx=16, pady=(0, 6))

        sep = ctk.CTkFrame(card, height=1, fg_color=theme.BORDER)
        sep.grid(row=6, column=0, sticky="ew", padx=16, pady=10)

        sentence_title = ctk.CTkLabel(card, text="Sentence", font=theme.font(14, "bold"))
        sentence_title.grid(row=7, column=0, sticky="w", padx=16)

        self.sentence_box = ctk.CTkTextbox(
            card, height=90, fg_color=theme.BG, border_width=1, border_color=theme.BORDER,
            font=theme.font(16), wrap="word",
        )
        self.sentence_box.grid(row=8, column=0, sticky="ew", padx=16, pady=(6, 10))

        btn_row1 = ctk.CTkFrame(card, fg_color="transparent")
        btn_row1.grid(row=9, column=0, sticky="ew", padx=16)
        theme.secondary_button(btn_row1, text="Space", width=80, command=self.add_space).pack(side="left", padx=(0, 6))
        theme.secondary_button(btn_row1, text="⌫ Back", width=80, command=self.backspace).pack(side="left", padx=6)
        theme.danger_button(btn_row1, text="Clear", width=80, command=self.clear_sentence).pack(side="left", padx=6)

        self.speak_btn = theme.primary_button(
            card, text="🔊 Speak Sentence", command=self.speak_sentence
        )
        self.speak_btn.grid(row=10, column=0, sticky="ew", padx=16, pady=(10, 16))

    # ------------------------------------------------------------- camera
    def toggle_camera(self):
        if self._running:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        if not self.recognizer.is_loaded:
            loaded = self.recognizer.load()
            if not loaded:
                self.model_status.configure(
                    text="⚠ No trained model found yet. Train one in the "
                    "'Train Model' tab, then come back here."
                )
            else:
                self.model_status.configure(text="")

        if not self.camera.is_running:
            ok = self.camera.start()
            if not ok:
                self.status_label.configure(text="Could not open webcam", text_color=theme.DANGER)
                return

        self._running = True
        self.toggle_btn.configure(text="Stop Camera")
        self.status_label.configure(text="Camera running", text_color=theme.SUCCESS)
        self._update_frame()

    def stop_camera(self):
        self._running = False
        self.toggle_btn.configure(text="Start Camera")
        self.status_label.configure(text="Camera stopped", text_color=theme.TEXT_MUTED)

    # ------------------------------------------------------------- loop
    def _update_frame(self):
        if not self._running:
            return

        frame = self.camera.read()
        if frame is not None:
            h, w = frame.shape[:2]
            box = get_roi_box(w, h)
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (34, 211, 238), 2)

            self._frame_count += 1
            if self.recognizer.is_loaded and self._frame_count % 2 == 0:
                roi = crop_roi(frame, box)
                result = self.recognizer.predict_frame(roi)
                if result:
                    self._render_prediction(result)

            self._render_video(frame)

        self.after(15, self._update_frame)

    def _render_video(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        target_w = 620
        scale = target_w / img.width
        target_h = int(img.height * scale)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(target_w, target_h))
        self.video_label.configure(image=ctk_img, text="")
        self.video_label.image = ctk_img

    def _render_prediction(self, result):
        mask_img = Image.fromarray(result["mask"]).convert("L")
        ctk_mask = ctk.CTkImage(light_image=mask_img, dark_image=mask_img, size=(150, 150))
        self.mask_label.configure(image=ctk_mask, text="")
        self.mask_label.image = ctk_mask

        display_label = result["stable_label"]
        shown = "—" if display_label == "nothing" else display_label
        self.letter_label.configure(text=shown)
        self.confidence_bar.set(result["confidence"])
        self.confidence_label.configure(text=f"confidence: {result['confidence']*100:.0f}%")

        if result["committed"]:
            self._commit_letter(result["committed"])

    # ---------------------------------------------------------- sentence
    def _commit_letter(self, letter: str):
        if letter == "space":
            self.sentence += " "
        elif letter == "del":
            self.sentence = self.sentence[:-1]
        else:
            self.sentence += letter
        self._refresh_sentence_box()

    def add_space(self):
        self.sentence += " "
        self._refresh_sentence_box()

    def backspace(self):
        self.sentence = self.sentence[:-1]
        self._refresh_sentence_box()

    def clear_sentence(self):
        self.sentence = ""
        self._refresh_sentence_box()

    def speak_sentence(self):
        tts.speak_async(self.sentence)

    def _refresh_sentence_box(self):
        self.sentence_box.delete("1.0", "end")
        self.sentence_box.insert("1.0", self.sentence)

    def on_show(self):
        """Called by the app when this tab becomes visible."""
        if config.MODEL_PATH.exists() and not self.recognizer.is_loaded:
            self.recognizer.load()
            self.model_status.configure(text="")

    def on_hide(self):
        pass
