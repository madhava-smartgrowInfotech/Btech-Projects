"""Collect Data tab: capture labeled hand-gesture images via webcam to
build (or extend) the training dataset.
"""

from __future__ import annotations

import time

import cv2
import customtkinter as ctk
from PIL import Image

from .. import config
from ..dataset import class_counts
from ..preprocessing import get_roi_box, crop_roi, segment_hand
from . import theme


class CollectFrame(ctk.CTkFrame):
    def __init__(self, parent, camera):
        super().__init__(parent, fg_color="transparent")
        self.camera = camera
        self._running = False
        self._burst_remaining = 0
        self._burst_target = 0
        self._last_capture_time = 0.0

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_video_panel()
        self._build_control_panel()
        self._refresh_counts()

    # ------------------------------------------------------------------ UI
    def _build_video_panel(self):
        card = theme.section_card(self)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(card, text="Camera", font=theme.font(16, "bold"))
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

    def _build_control_panel(self):
        card = theme.section_card(self)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(card, text="Capture Settings", font=theme.font(16, "bold"))
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))

        ctk.CTkLabel(card, text="Class", font=theme.font(13)).grid(
            row=1, column=0, sticky="w", padx=16
        )
        self.class_var = ctk.StringVar(value=config.CLASSES[0])
        self.class_menu = ctk.CTkOptionMenu(
            card, values=config.CLASSES, variable=self.class_var,
            fg_color=theme.SURFACE_ALT, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, command=self._on_class_change,
        )
        self.class_menu.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 12))

        self.count_label = ctk.CTkLabel(
            card, text="0 images collected", font=theme.font(13), text_color=theme.TEXT_MUTED
        )
        self.count_label.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 12))

        preview_title = ctk.CTkLabel(card, text="Segmentation preview", font=theme.font(13))
        preview_title.grid(row=4, column=0, sticky="w", padx=16)
        self.mask_label = ctk.CTkLabel(card, text="", fg_color=theme.BG, corner_radius=10)
        self.mask_label.configure(width=140, height=140)
        self.mask_label.grid(row=5, column=0, pady=8)

        theme.primary_button(card, text="📸 Capture 1 Image", command=self.capture_one).grid(
            row=6, column=0, sticky="ew", padx=16, pady=(8, 6)
        )

        burst_row = ctk.CTkFrame(card, fg_color="transparent")
        burst_row.grid(row=7, column=0, sticky="ew", padx=16, pady=(0, 6))
        self.burst_count_var = ctk.StringVar(value="60")
        burst_entry = ctk.CTkEntry(burst_row, textvariable=self.burst_count_var, width=60)
        burst_entry.pack(side="left")
        theme.secondary_button(
            burst_row, text="🎞 Burst Capture", command=self.start_burst
        ).pack(side="left", padx=8, fill="x", expand=True)

        self.burst_progress = ctk.CTkProgressBar(card, progress_color=theme.ACCENT)
        self.burst_progress.set(0)
        self.burst_progress.grid(row=8, column=0, sticky="ew", padx=16, pady=(6, 4))

        self.burst_status = ctk.CTkLabel(
            card, text="", font=theme.font(12), text_color=theme.TEXT_MUTED
        )
        self.burst_status.grid(row=9, column=0, sticky="w", padx=16, pady=(0, 12))

        hint = ctk.CTkLabel(
            card,
            text=(
                "Tip: keep a plain, uncluttered background and good, even "
                "lighting behind your hand for cleaner segmentation. "
                "Collect ~150-250 images per class from slightly varied "
                "angles and distances."
            ),
            font=theme.font(11), text_color=theme.TEXT_MUTED, wraplength=260, justify="left",
        )
        hint.grid(row=10, column=0, sticky="w", padx=16, pady=(4, 16))

    # ------------------------------------------------------------- camera
    def toggle_camera(self):
        if self._running:
            self._running = False
            self.toggle_btn.configure(text="Start Camera")
            self.status_label.configure(text="Camera stopped", text_color=theme.TEXT_MUTED)
            return

        if not self.camera.is_running:
            ok = self.camera.start()
            if not ok:
                self.status_label.configure(text="Could not open webcam", text_color=theme.DANGER)
                return
        self._running = True
        self.toggle_btn.configure(text="Stop Camera")
        self.status_label.configure(text="Camera running", text_color=theme.SUCCESS)
        self._update_frame()

    def _update_frame(self):
        if not self._running:
            return
        frame = self.camera.read()
        if frame is not None:
            h, w = frame.shape[:2]
            box = get_roi_box(w, h)
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (34, 211, 238), 2)

            roi = crop_roi(frame, box)
            self._last_roi = roi
            mask = segment_hand(roi)
            mask_img = Image.fromarray(mask).convert("L")
            ctk_mask = ctk.CTkImage(light_image=mask_img, dark_image=mask_img, size=(130, 130))
            self.mask_label.configure(image=ctk_mask, text="")
            self.mask_label.image = ctk_mask

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            target_w = 620
            scale = target_w / img.width
            ctk_img = ctk.CTkImage(
                light_image=img, dark_image=img, size=(target_w, int(img.height * scale))
            )
            self.video_label.configure(image=ctk_img, text="")
            self.video_label.image = ctk_img

            if self._burst_remaining > 0:
                now = time.time()
                if (now - self._last_capture_time) * 1000 >= config.CAPTURE_DELAY_MS:
                    self._save_image(roi)
                    self._burst_remaining -= 1
                    self._last_capture_time = now
                    done = self._burst_target - self._burst_remaining
                    self.burst_progress.set(done / max(1, self._burst_target))
                    self.burst_status.configure(
                        text=f"Capturing... {done}/{self._burst_target}"
                    )
                    if self._burst_remaining == 0:
                        self.burst_status.configure(text="Done!", text_color=theme.SUCCESS)
                        self._refresh_counts()

        self.after(15, self._update_frame)

    # ---------------------------------------------------------- capture
    def capture_one(self):
        roi = getattr(self, "_last_roi", None)
        if roi is None:
            self.status_label.configure(text="Start the camera first", text_color=theme.WARNING)
            return
        self._save_image(roi)
        self._refresh_counts()

    def start_burst(self):
        if not self._running:
            self.status_label.configure(text="Start the camera first", text_color=theme.WARNING)
            return
        try:
            n = max(1, min(1000, int(self.burst_count_var.get())))
        except ValueError:
            n = 60
        self._burst_target = n
        self._burst_remaining = n
        self._last_capture_time = 0.0

    def _save_image(self, roi_bgr):
        cls = self.class_var.get()
        folder = config.DATA_DIR / cls
        folder.mkdir(parents=True, exist_ok=True)
        resized = cv2.resize(
            roi_bgr, (config.RAW_SAVE_SIZE, config.RAW_SAVE_SIZE), interpolation=cv2.INTER_AREA
        )
        filename = folder / f"{cls}_{int(time.time() * 1000)}.png"
        cv2.imwrite(str(filename), resized)

    def _on_class_change(self, *_):
        self._refresh_counts()

    def _refresh_counts(self):
        counts = class_counts()
        cls = self.class_var.get()
        self.count_label.configure(text=f"{counts.get(cls, 0)} images collected for '{cls}'")

    def on_show(self):
        self._refresh_counts()

    def on_hide(self):
        pass
