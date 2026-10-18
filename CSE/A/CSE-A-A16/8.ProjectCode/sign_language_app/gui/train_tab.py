"""Train Model tab: dataset summary, hyperparameters, background training
with a live-updating accuracy/loss chart.
"""

from __future__ import annotations

import queue
import threading

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .. import config
from ..dataset import class_counts
from ..train import train_model
from . import theme


class TrainFrame(ctk.CTkFrame):
    def __init__(self, parent, on_training_complete=None):
        super().__init__(parent, fg_color="transparent")
        self.on_training_complete = on_training_complete
        self._queue: "queue.Queue" = queue.Queue()
        self._training_thread = None
        self._stop_requested = False
        self._epochs_x = []
        self._acc_y = []
        self._val_acc_y = []

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self._build_settings_panel()
        self._build_chart_panel()
        self._poll_queue()

    # ------------------------------------------------------------------ UI
    def _build_settings_panel(self):
        card = theme.section_card(self)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Dataset", font=theme.font(16, "bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6)
        )
        self.dataset_box = ctk.CTkTextbox(
            card, height=170, fg_color=theme.BG, border_width=1, border_color=theme.BORDER,
            font=theme.font(12), wrap="none",
        )
        self.dataset_box.grid(row=1, column=0, sticky="ew", padx=16)
        theme.secondary_button(card, text="Refresh Counts", command=self.refresh_dataset_summary).grid(
            row=2, column=0, sticky="ew", padx=16, pady=(6, 14)
        )

        ctk.CTkLabel(card, text="Hyperparameters", font=theme.font(16, "bold")).grid(
            row=3, column=0, sticky="w", padx=16, pady=(0, 6)
        )

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=4, column=0, sticky="ew", padx=16)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Epochs").grid(row=0, column=0, sticky="w", pady=4)
        self.epochs_var = ctk.StringVar(value=str(config.DEFAULT_EPOCHS))
        ctk.CTkEntry(form, textvariable=self.epochs_var).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ctk.CTkLabel(form, text="Batch size").grid(row=1, column=0, sticky="w", pady=4)
        self.batch_var = ctk.StringVar(value=str(config.DEFAULT_BATCH_SIZE))
        ctk.CTkEntry(form, textvariable=self.batch_var).grid(row=1, column=1, sticky="ew", padx=(8, 0))

        ctk.CTkLabel(form, text="Learning rate").grid(row=2, column=0, sticky="w", pady=4)
        self.lr_var = ctk.StringVar(value=str(config.DEFAULT_LEARNING_RATE))
        ctk.CTkEntry(form, textvariable=self.lr_var).grid(row=2, column=1, sticky="ew", padx=(8, 0))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=5, column=0, sticky="ew", padx=16, pady=16)
        self.train_btn = theme.primary_button(btn_row, text="▶ Start Training", command=self.start_training)
        self.train_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.stop_btn = theme.danger_button(btn_row, text="Stop", command=self.stop_training, state="disabled")
        self.stop_btn.pack(side="left", padx=(6, 0))

        self.progress = ctk.CTkProgressBar(card, progress_color=theme.ACCENT)
        self.progress.set(0)
        self.progress.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 6))

        self.status_label = ctk.CTkLabel(
            card, text="Idle", font=theme.font(12), text_color=theme.TEXT_MUTED, wraplength=300
        )
        self.status_label.grid(row=7, column=0, sticky="w", padx=16, pady=(0, 16))

    def _build_chart_panel(self):
        card = theme.section_card(self)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Training Progress", font=theme.font(16, "bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6)
        )

        self.figure = Figure(figsize=(5, 4), dpi=100, facecolor=theme.SURFACE)
        self.ax = self.figure.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, master=card)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def _style_axes(self):
        self.ax.clear()
        self.ax.set_facecolor(theme.SURFACE)
        self.ax.tick_params(colors=theme.TEXT_MUTED)
        for spine in self.ax.spines.values():
            spine.set_color(theme.BORDER)
        self.ax.set_xlabel("Epoch", color=theme.TEXT_MUTED)
        self.ax.set_ylabel("Accuracy", color=theme.TEXT_MUTED)
        self.ax.set_ylim(0, 1)
        self.ax.grid(True, color=theme.BORDER, alpha=0.4)

    # -------------------------------------------------------- dataset info
    def refresh_dataset_summary(self):
        counts = class_counts()
        lines = [f"{cls:>7}: {n}" for cls, n in counts.items()]
        total = sum(counts.values())
        self.dataset_box.delete("1.0", "end")
        self.dataset_box.insert("1.0", "\n".join(lines) + f"\n\nTotal: {total} images")

    # ------------------------------------------------------------- training
    def start_training(self):
        if self._training_thread and self._training_thread.is_alive():
            return
        try:
            epochs = int(self.epochs_var.get())
            batch_size = int(self.batch_var.get())
            lr = float(self.lr_var.get())
        except ValueError:
            self.status_label.configure(text="Invalid hyperparameter values", text_color=theme.DANGER)
            return

        self._epochs_x, self._acc_y, self._val_acc_y = [], [], []
        self._stop_requested = False
        self.progress.set(0)
        self.status_label.configure(text="Loading & preprocessing dataset...", text_color=theme.TEXT_MUTED)
        self.train_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        def data_progress_cb(done, total):
            self._queue.put(("data_progress", done, total))

        def epoch_cb(epoch, total_epochs, logs):
            self._queue.put(("epoch", epoch, total_epochs, logs))

        def run():
            try:
                summary = train_model(
                    epochs=epochs,
                    batch_size=batch_size,
                    learning_rate=lr,
                    data_progress_cb=data_progress_cb,
                    epoch_cb=epoch_cb,
                    stop_flag=lambda: self._stop_requested,
                )
                self._queue.put(("done", summary))
            except Exception as exc:  # surface any failure to the UI thread
                self._queue.put(("error", str(exc)))

        self._training_thread = threading.Thread(target=run, daemon=True)
        self._training_thread.start()

    def stop_training(self):
        self._stop_requested = True
        self.status_label.configure(text="Stopping after current epoch...", text_color=theme.WARNING)

    def _poll_queue(self):
        try:
            while True:
                item = self._queue.get_nowait()
                kind = item[0]
                if kind == "data_progress":
                    _, done, total = item
                    self.status_label.configure(text=f"Preprocessing images: {done}/{total}")
                elif kind == "epoch":
                    _, epoch, total_epochs, logs = item
                    self.progress.set(epoch / max(1, total_epochs))
                    acc = logs.get("accuracy", 0)
                    val_acc = logs.get("val_accuracy", 0)
                    self.status_label.configure(
                        text=f"Epoch {epoch}/{total_epochs} — acc {acc:.2%} — val_acc {val_acc:.2%}",
                        text_color=theme.TEXT_MUTED,
                    )
                    self._epochs_x.append(epoch)
                    self._acc_y.append(acc)
                    self._val_acc_y.append(val_acc)
                    self._redraw_chart()
                elif kind == "done":
                    _, summary = item
                    self.progress.set(1.0)
                    self.status_label.configure(
                        text=f"Done. Test accuracy: {summary['test_accuracy']:.2%} "
                        f"(model saved to models/asl_cnn_model.keras)",
                        text_color=theme.SUCCESS,
                    )
                    self.train_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.refresh_dataset_summary()
                    if self.on_training_complete:
                        self.on_training_complete()
                elif kind == "error":
                    _, message = item
                    self.status_label.configure(text=f"Error: {message}", text_color=theme.DANGER)
                    self.train_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(200, self._poll_queue)

    def _redraw_chart(self):
        self._style_axes()
        self.ax.plot(self._epochs_x, self._acc_y, label="train accuracy", color=theme.ACCENT)
        self.ax.plot(self._epochs_x, self._val_acc_y, label="val accuracy", color=theme.SUCCESS)
        legend = self.ax.legend(facecolor=theme.SURFACE, labelcolor=theme.TEXT, loc="lower right")
        self.canvas.draw()

    def on_show(self):
        self.refresh_dataset_summary()

    def on_hide(self):
        pass
