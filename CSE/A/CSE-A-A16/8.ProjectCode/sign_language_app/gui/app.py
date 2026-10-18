"""Main application window: sidebar navigation over the four tabs."""

from __future__ import annotations

import customtkinter as ctk

from ..camera import Camera
from ..recognizer import SignRecognizer
from . import theme
from .about_tab import AboutFrame
from .collect_tab import CollectFrame
from .recognize_tab import RecognizeFrame
from .train_tab import TrainFrame

NAV_ITEMS = [
    ("recognize", "🖐  Recognize"),
    ("collect", "📸  Collect Data"),
    ("train", "🧠  Train Model"),
    ("about", "ℹ️  About"),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        theme.apply_appearance()
        self.configure(fg_color=theme.BG)
        self.title("Sign Language Recognition System — CNN")
        self.geometry("1180x760")
        self.minsize(1000, 660)

        self.camera = Camera()
        self.recognizer = SignRecognizer()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

        self._frames = {}
        self._active = None
        self._build_frames()
        self.show_frame("recognize")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=theme.SURFACE, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        brand = ctk.CTkLabel(
            sidebar, text="🤟 SignSpeak", font=theme.font(20, "bold"), text_color=theme.ACCENT
        )
        brand.pack(anchor="w", padx=20, pady=(24, 2))
        subtitle = ctk.CTkLabel(
            sidebar, text="CNN Sign Language\nRecognition", font=theme.font(11),
            text_color=theme.TEXT_MUTED, justify="left",
        )
        subtitle.pack(anchor="w", padx=20, pady=(0, 24))

        self._nav_buttons = {}
        for key, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w", font=theme.font(14),
                fg_color="transparent", hover_color=theme.SURFACE_ALT,
                text_color=theme.TEXT, corner_radius=8, height=42,
                command=lambda k=key: self.show_frame(k),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_buttons[key] = btn

        footer = ctk.CTkLabel(
            sidebar, text="CSE-A · Batch 16", font=theme.font(10), text_color=theme.TEXT_MUTED
        )
        footer.pack(side="bottom", pady=16)

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _build_frames(self):
        self._frames["recognize"] = RecognizeFrame(self.content, self.camera, self.recognizer)
        self._frames["collect"] = CollectFrame(self.content, self.camera)
        self._frames["train"] = TrainFrame(
            self.content, on_training_complete=self._on_training_complete
        )
        self._frames["about"] = AboutFrame(self.content)
        for frame in self._frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def _on_training_complete(self):
        # Force the recognizer to pick up the freshly trained model next
        # time the Recognize tab is shown.
        self.recognizer.model = None
        self.recognizer.labels = []

    def show_frame(self, key: str):
        if self._active == key:
            return
        if self._active and hasattr(self._frames[self._active], "on_hide"):
            self._frames[self._active].on_hide()
        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color=theme.ACCENT_SOFT if k == key else "transparent")
        frame = self._frames[key]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()
        self._active = key

    def _on_close(self):
        try:
            self.camera.stop()
        except Exception:
            pass
        self.destroy()


def run():
    app = App()
    app.mainloop()
