"""Tkinter desktop interface for the federated-unlearning workflow."""

from __future__ import annotations

import json
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .engine import FederatedUnlearningEngine, TrainingMetrics, UnlearningCertificate


NAVY = "#14213d"
BLUE = "#2563eb"
PALE = "#eef4ff"
GREEN = "#15803d"
RED = "#b91c1c"
TEXT = "#172033"
MUTED = "#5f6b7a"


class UnlearningApp(tk.Tk):
    def __init__(self, audit_path: str | Path = "data/audit_log.jsonl") -> None:
        super().__init__()
        self.title("Certified Federated Unlearning Lab")
        self.geometry("1120x740")
        self.minsize(940, 650)
        self.configure(bg="#f5f7fb")
        self.engine = FederatedUnlearningEngine(audit_path=audit_path)
        self.latest_certificate: UnlearningCertificate | None = None
        self._configure_style()
        self._build_header()
        self._build_tabs()
        self._set_status("Ready — train the federated model to begin", "ready")
        self._refresh_clients()
        self._refresh_audit()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("Card.TFrame", background="white")
        style.configure("TLabel", background="#f5f7fb", foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="white", foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=NAVY, foreground="white", font=("Segoe UI Semibold", 20))
        style.configure("Subtitle.TLabel", background=NAVY, foreground="#cad5ed", font=("Segoe UI", 10))
        style.configure("Heading.TLabel", background="#f5f7fb", foreground=NAVY, font=("Segoe UI Semibold", 15))
        style.configure("Metric.TLabel", background="white", foreground=NAVY, font=("Segoe UI Semibold", 18))
        style.configure("MetricName.TLabel", background="white", foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Primary.TButton", background=BLUE, foreground="white", padding=(14, 9), font=("Segoe UI Semibold", 10))
        style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#9aa8c1")])
        style.configure("TNotebook", background="#f5f7fb", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI Semibold", 9))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9))

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=NAVY, height=92)
        header.pack(fill="x")
        header.pack_propagate(False)
        block = tk.Frame(header, bg=NAVY)
        block.pack(fill="both", expand=True, padx=26, pady=15)
        ttk.Label(block, text="Certified Federated Unlearning Lab", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            block,
            text="Privacy-preserving client removal • differential-privacy bounds • verifiable audit records",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

    def _build_tabs(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=(16, 8))
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True)
        self.training_tab = ttk.Frame(self.notebook, padding=18)
        self.unlearning_tab = ttk.Frame(self.notebook, padding=18)
        self.explorer_tab = ttk.Frame(self.notebook, padding=18)
        self.audit_tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.training_tab, text="Federated Training")
        self.notebook.add(self.unlearning_tab, text="Certified Unlearning")
        self.notebook.add(self.explorer_tab, text="Model Explorer")
        self.notebook.add(self.audit_tab, text="Compliance Audit")
        self._build_training_tab()
        self._build_unlearning_tab()
        self._build_explorer_tab()
        self._build_audit_tab()
        self.status_label = tk.Label(self, bg="#e8edf6", fg=MUTED, anchor="w", padx=20, pady=8, font=("Segoe UI", 9))
        self.status_label.pack(fill="x", side="bottom")

    def _build_training_tab(self) -> None:
        ttk.Label(self.training_tab, text="Federated training overview", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            self.training_tab,
            text="Client records stay local. Only clipped parameter updates enter the noisy global aggregate.",
        ).pack(anchor="w", pady=(3, 14))
        actions = ttk.Frame(self.training_tab)
        actions.pack(fill="x", pady=(0, 12))
        self.train_button = ttk.Button(actions, text="Train Global Model", style="Primary.TButton", command=self._train)
        self.train_button.pack(side="left")
        ttk.Button(actions, text="New Session", command=self._new_session).pack(side="left", padx=8)
        self.metric_frame = ttk.Frame(self.training_tab)
        self.metric_frame.pack(fill="x", pady=(0, 14))
        self.metric_values: dict[str, ttk.Label] = {}
        for column, (key, label) in enumerate(
            (("clients", "ACTIVE CLIENTS"), ("epsilon", "DP EPSILON"), ("perplexity", "PERPLEXITY"), ("accuracy", "NEXT-CHAR ACCURACY"))
        ):
            card = ttk.Frame(self.metric_frame, style="Card.TFrame", padding=14)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            self.metric_frame.columnconfigure(column, weight=1)
            value = ttk.Label(card, text="—", style="Metric.TLabel")
            value.pack(anchor="w")
            ttk.Label(card, text=label, style="MetricName.TLabel").pack(anchor="w", pady=(4, 0))
            self.metric_values[key] = value
        columns = ("client", "domain", "records", "norm", "scale", "state")
        self.client_tree = ttk.Treeview(self.training_tab, columns=columns, show="headings", height=10)
        headings = {"client": "Client", "domain": "Data domain", "records": "Records", "norm": "Clipped L2", "scale": "Clip scale", "state": "State"}
        for column in columns:
            self.client_tree.heading(column, text=headings[column])
            self.client_tree.column(column, width=130, anchor="center")
        self.client_tree.column("client", width=150, anchor="w")
        self.client_tree.column("domain", width=140, anchor="w")
        self.client_tree.pack(fill="both", expand=True)

    def _build_unlearning_tab(self) -> None:
        ttk.Label(self.unlearning_tab, text="Right-to-be-forgotten request", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            self.unlearning_tab,
            text="Select an active client. The tracked update is removed, then compared with a retained-client recomputation.",
        ).pack(anchor="w", pady=(3, 14))
        form = ttk.Frame(self.unlearning_tab)
        form.pack(fill="x", pady=(0, 12))
        ttk.Label(form, text="Client to remove:").pack(side="left")
        self.client_choice = ttk.Combobox(form, state="readonly", width=34)
        self.client_choice.pack(side="left", padx=10)
        self.unlearn_button = ttk.Button(form, text="Execute & Certify", style="Primary.TButton", command=self._unlearn, state="disabled")
        self.unlearn_button.pack(side="left")
        self.export_button = ttk.Button(form, text="Export Certificate", command=self._export_certificate, state="disabled")
        self.export_button.pack(side="left", padx=8)
        self.certificate_text = tk.Text(
            self.unlearning_tab,
            wrap="word",
            font=("Consolas", 10),
            bg="white",
            fg=TEXT,
            relief="flat",
            padx=16,
            pady=14,
        )
        self.certificate_text.pack(fill="both", expand=True)
        self.certificate_text.insert("1.0", "A verification certificate will appear here after unlearning.")
        self.certificate_text.configure(state="disabled")

    def _build_explorer_tab(self) -> None:
        ttk.Label(self.explorer_tab, text="Model explorer", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            self.explorer_tab,
            text="Generate a sample from the current global character-language model and inspect how the model changes.",
        ).pack(anchor="w", pady=(3, 14))
        controls = ttk.Frame(self.explorer_tab)
        controls.pack(fill="x")
        ttk.Label(controls, text="Seed text:").pack(side="left")
        self.seed_entry = ttk.Entry(controls, width=30)
        self.seed_entry.insert(0, "privacy")
        self.seed_entry.pack(side="left", padx=10)
        self.generate_button = ttk.Button(controls, text="Generate Sample", command=self._generate, state="disabled")
        self.generate_button.pack(side="left")
        self.sample_text = tk.Text(self.explorer_tab, height=9, wrap="word", font=("Georgia", 12), bg="white", relief="flat", padx=16, pady=14)
        self.sample_text.pack(fill="x", pady=(12, 16))
        ttk.Label(self.explorer_tab, text="Method notes", style="Heading.TLabel").pack(anchor="w")
        notes = (
            "• Fixed character vocabulary prevents raw client vocabulary from being uploaded.\n"
            "• Each client update is L2-clipped before aggregation.\n"
            "• Gaussian noise gives a quantified one-shot (epsilon, delta) release bound.\n"
            "• Unlearning subtracts the exact tracked update and renormalizes retained clients.\n"
            "• Membership AUC is empirical evidence; the DP bound and algebraic recomputation are the certificate evidence."
        )
        ttk.Label(self.explorer_tab, text=notes, justify="left").pack(anchor="w")

    def _build_audit_tab(self) -> None:
        heading = ttk.Frame(self.audit_tab)
        heading.pack(fill="x", pady=(0, 12))
        left = ttk.Frame(heading)
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="Compliance audit ledger", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(left, text="Every training and deletion event is linked to the previous record by SHA-256.").pack(anchor="w", pady=(3, 0))
        ttk.Button(heading, text="Verify Hash Chain", command=self._verify_audit).pack(side="right")
        columns = ("sequence", "type", "time", "client", "status", "hash")
        self.audit_tree = ttk.Treeview(self.audit_tab, columns=columns, show="headings", height=14)
        widths = {"sequence": 65, "type": 150, "time": 180, "client": 160, "status": 110, "hash": 250}
        for column in columns:
            self.audit_tree.heading(column, text=column.replace("_", " ").title())
            self.audit_tree.column(column, width=widths[column], anchor="w")
        self.audit_tree.pack(fill="both", expand=True)

    def _set_status(self, text: str, kind: str = "ready") -> None:
        colors = {"ready": MUTED, "success": GREEN, "error": RED}
        self.status_label.configure(text=text, fg=colors.get(kind, MUTED))

    def _train(self) -> None:
        try:
            self._set_status("Training local client models and aggregating clipped updates…")
            self.update_idletasks()
            metrics = self.engine.train()
            self.latest_certificate = None
            self._show_metrics(metrics)
            self._refresh_clients()
            self._refresh_choices()
            self._refresh_audit()
            self.unlearn_button.configure(state="normal")
            self.generate_button.configure(state="normal")
            self.export_button.configure(state="disabled")
            self._set_status(f"Training complete — model {metrics.model_hash[:12]}…", "success")
        except Exception as error:
            self._show_error("Training failed", error)

    def _new_session(self) -> None:
        self.engine = FederatedUnlearningEngine(audit_path=self.engine.audit.path)
        self.latest_certificate = None
        for label in self.metric_values.values():
            label.configure(text="—")
        self.unlearn_button.configure(state="disabled")
        self.generate_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self._refresh_clients()
        self._refresh_choices()
        self._set_status("New session ready — prior audit records are preserved", "ready")

    def _show_metrics(self, metrics: TrainingMetrics) -> None:
        self.metric_values["clients"].configure(text=str(metrics.active_clients))
        self.metric_values["epsilon"].configure(text=f"{metrics.epsilon:.3f}")
        self.metric_values["perplexity"].configure(text=f"{metrics.perplexity:.2f}")
        self.metric_values["accuracy"].configure(text=f"{metrics.next_character_accuracy * 100:.1f}%")

    def _refresh_clients(self) -> None:
        self.client_tree.delete(*self.client_tree.get_children())
        for contribution in self.engine.contributions():
            self.client_tree.insert(
                "",
                "end",
                values=(
                    contribution.display_name,
                    contribution.domain,
                    contribution.record_count,
                    f"{contribution.clipped_norm:.3f}" if self.engine.trained else "—",
                    f"{contribution.clip_scale:.3f}" if self.engine.trained else "—",
                    "Active" if contribution.active and self.engine.trained else ("Removed" if self.engine.trained else "Not trained"),
                ),
            )

    def _refresh_choices(self) -> None:
        choices = [
            f"{client_id} — {self.engine.clients[client_id].domain}"
            for client_id in self.engine.active_client_ids
        ]
        self.client_choice["values"] = choices
        if choices:
            self.client_choice.current(0)

    def _unlearn(self) -> None:
        selection = self.client_choice.get()
        if not selection:
            messagebox.showinfo("Select a client", "Choose an active client to unlearn.")
            return
        client_id = selection.split(" — ", 1)[0]
        try:
            self._set_status(f"Removing {client_id} and running verification…")
            self.update_idletasks()
            certificate = self.engine.unlearn(client_id)
            self.latest_certificate = certificate
            self._display_certificate(certificate)
            self._show_metrics(self.engine.metrics())
            self._refresh_clients()
            self._refresh_choices()
            self._refresh_audit()
            self.export_button.configure(state="normal")
            if len(self.engine.active_client_ids) <= 1:
                self.unlearn_button.configure(state="disabled")
            self._set_status(f"{certificate.status}: {certificate.certificate_id}", "success" if certificate.status == "CERTIFIED" else "error")
        except Exception as error:
            self._show_error("Unlearning failed", error)

    def _display_certificate(self, certificate: UnlearningCertificate) -> None:
        lines = [
            "CERTIFIED RIGHT-TO-BE-FORGOTTEN REPORT",
            "=" * 57,
            f"Certificate         : {certificate.certificate_id}",
            f"Status              : {certificate.status}",
            f"Issued (UTC)        : {certificate.issued_at_utc}",
            f"Data subject        : {certificate.client_name}",
            f"Method              : {certificate.method}",
            "",
            "FORMAL / DETERMINISTIC CHECKS",
            f"DP guarantee        : epsilon={certificate.epsilon:.4f}, delta={certificate.delta:g}",
            f"Residual influence  : {certificate.residual_influence_l2:.3e}",
            f"Reference distance  : {certificate.reference_retrain_l2:.3e}",
            f"Clients             : {certificate.clients_before} before → {certificate.clients_after} after",
            "",
            "EMPIRICAL VERIFICATION",
            f"Membership AUC      : {certificate.membership_auc_before:.3f} before → {certificate.membership_auc_after:.3f} after",
            f"Perplexity          : {certificate.perplexity_before:.3f} before → {certificate.perplexity_after:.3f} after",
            f"Next-char accuracy  : {certificate.accuracy_before * 100:.2f}% before → {certificate.accuracy_after * 100:.2f}% after",
            f"Utility retained    : {certificate.utility_retention_percent:.2f}%",
            "",
            f"Model hash before   : {certificate.model_hash_before}",
            f"Model hash after    : {certificate.model_hash_after}",
            f"Audit record hash   : {certificate.audit_record_hash}",
        ]
        self.certificate_text.configure(state="normal")
        self.certificate_text.delete("1.0", "end")
        self.certificate_text.insert("1.0", "\n".join(lines))
        self.certificate_text.configure(state="disabled")

    def _generate(self) -> None:
        try:
            sample = self.engine.generate(self.seed_entry.get(), length=180)
            self.sample_text.delete("1.0", "end")
            self.sample_text.insert("1.0", sample)
            self._set_status("Generated a sample from the current model", "success")
        except Exception as error:
            self._show_error("Generation failed", error)

    def _refresh_audit(self) -> None:
        self.audit_tree.delete(*self.audit_tree.get_children())
        try:
            records = self.engine.audit.read_all()
        except ValueError as error:
            self._set_status(str(error), "error")
            return
        for record in records:
            self.audit_tree.insert(
                "",
                "end",
                values=(
                    record.get("sequence", ""),
                    record.get("event_type", ""),
                    record.get("timestamp_utc", record.get("issued_at_utc", "")),
                    record.get("client_id", "—"),
                    record.get("status", "—"),
                    f"{record.get('record_hash', '')[:24]}…",
                ),
            )

    def _verify_audit(self) -> None:
        valid, detail = self.engine.audit.verify()
        if valid:
            messagebox.showinfo("Audit verified", detail)
            self._set_status(detail, "success")
        else:
            messagebox.showerror("Audit verification failed", detail)
            self._set_status(detail, "error")

    def _export_certificate(self) -> None:
        if self.latest_certificate is None:
            return
        default_name = f"{self.latest_certificate.certificate_id}.json"
        path = filedialog.asksaveasfilename(
            title="Export unlearning certificate",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=(("JSON certificate", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            self.engine.export_certificate(self.latest_certificate, path)
            self._set_status(f"Certificate exported to {path}", "success")
        except Exception as error:
            self._show_error("Export failed", error)

    def _show_error(self, title: str, error: Exception) -> None:
        messagebox.showerror(title, str(error))
        self._set_status(str(error), "error")


def run_gui() -> None:
    app = UnlearningApp()
    app.mainloop()

