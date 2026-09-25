"""Federated training, certified unlearning, verification, and reporting."""

from __future__ import annotations

import hashlib
import json
import math
import random
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .audit import AuditLedger
from .dataset import CLIENTS, NON_MEMBER_TEXTS, PUBLIC_EVALUATION, ClientDataset
from .model import (
    DIMENSION,
    CharacterLanguageModel,
    clipped_update,
    l2_norm,
    membership_auc,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _vector_hash(vector: Iterable[float]) -> str:
    encoded = json.dumps([round(value, 12) for value in vector], separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class TrainingMetrics:
    active_clients: int
    epsilon: float
    delta: float
    perplexity: float
    next_character_accuracy: float
    utility_score: float
    model_hash: str


@dataclass(frozen=True)
class ClientContribution:
    client_id: str
    display_name: str
    domain: str
    record_count: int
    original_norm: float
    clipped_norm: float
    clip_scale: float
    active: bool


@dataclass(frozen=True)
class UnlearningCertificate:
    certificate_id: str
    session_id: str
    client_id: str
    client_name: str
    issued_at_utc: str
    status: str
    method: str
    epsilon: float
    delta: float
    clip_norm: float
    noise_multiplier: float
    residual_influence_l2: float
    reference_retrain_l2: float
    membership_auc_before: float
    membership_auc_after: float
    perplexity_before: float
    perplexity_after: float
    accuracy_before: float
    accuracy_after: float
    utility_retention_percent: float
    clients_before: int
    clients_after: int
    model_hash_before: str
    model_hash_after: str
    audit_record_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FederatedUnlearningEngine:
    """Coordinates the complete demonstrator lifecycle."""

    def __init__(
        self,
        clients: tuple[ClientDataset, ...] = CLIENTS,
        audit_path: str | Path = "data/audit_log.jsonl",
        clip_norm: float = 25.0,
        noise_multiplier: float = 3.0,
        delta: float = 1e-5,
        random_seed: int = 2026,
    ) -> None:
        if len(clients) < 2:
            raise ValueError("Federated training requires at least two clients")
        if clip_norm <= 0 or noise_multiplier <= 0:
            raise ValueError("clip_norm and noise_multiplier must be positive")
        if not 0 < delta < 1:
            raise ValueError("delta must be between zero and one")
        self.clients = {client.client_id: client for client in clients}
        self.audit = AuditLedger(audit_path)
        self.clip_norm = float(clip_norm)
        self.noise_multiplier = float(noise_multiplier)
        self.delta = float(delta)
        self.random_seed = int(random_seed)
        self.session_id = str(uuid.uuid4())
        self.updates: dict[str, list[float]] = {}
        self.update_metadata: dict[str, tuple[float, float]] = {}
        self.active_client_ids: list[str] = []
        self.noise: list[float] = []
        self.noisy_sum: list[float] = []
        self.model: CharacterLanguageModel | None = None
        self.certificates: list[UnlearningCertificate] = []

    @property
    def trained(self) -> bool:
        return self.model is not None

    @property
    def epsilon(self) -> float:
        return math.sqrt(2.0 * math.log(1.25 / self.delta)) / self.noise_multiplier

    def train(self) -> TrainingMetrics:
        rng = random.Random(self.random_seed)
        self.updates.clear()
        self.update_metadata.clear()
        self.active_client_ids = list(self.clients)
        clean_sum = [0.0] * DIMENSION
        for client_id, client in self.clients.items():
            update, original_norm, scale = clipped_update(client.records, self.clip_norm)
            self.updates[client_id] = update
            self.update_metadata[client_id] = (original_norm, scale)
            for index, value in enumerate(update):
                clean_sum[index] += value

        noise_stddev = self.noise_multiplier * self.clip_norm
        self.noise = [rng.gauss(0.0, noise_stddev) for _ in range(DIMENSION)]
        self.noisy_sum = [value + noise for value, noise in zip(clean_sum, self.noise)]
        self._rebuild_model()
        self.certificates.clear()
        metrics = self.metrics()
        self.audit.append(
            {
                "event_type": "FEDERATED_TRAINING",
                "timestamp_utc": _utc_now(),
                "session_id": self.session_id,
                "active_clients": metrics.active_clients,
                "epsilon": round(metrics.epsilon, 8),
                "delta": metrics.delta,
                "clip_norm": self.clip_norm,
                "noise_multiplier": self.noise_multiplier,
                "model_hash": metrics.model_hash,
            }
        )
        return metrics

    def _rebuild_model(self) -> None:
        count = len(self.active_client_ids)
        if count == 0:
            raise RuntimeError("Cannot build a model with no active clients")
        parameters = [value / count for value in self.noisy_sum]
        self.model = CharacterLanguageModel(parameters)

    def metrics(self) -> TrainingMetrics:
        if self.model is None:
            raise RuntimeError("Train the federated model first")
        perplexity = self.model.perplexity(PUBLIC_EVALUATION)
        accuracy = self.model.next_character_accuracy(PUBLIC_EVALUATION)
        # A bounded composite indicator for a concise dashboard comparison.
        utility = 0.65 * accuracy + 0.35 * (1.0 / (1.0 + math.log1p(perplexity)))
        return TrainingMetrics(
            active_clients=len(self.active_client_ids),
            epsilon=self.epsilon,
            delta=self.delta,
            perplexity=perplexity,
            next_character_accuracy=accuracy,
            utility_score=utility,
            model_hash=_vector_hash(self.model.parameters),
        )

    def contributions(self) -> list[ClientContribution]:
        result: list[ClientContribution] = []
        for client_id, client in self.clients.items():
            original_norm, scale = self.update_metadata.get(client_id, (0.0, 0.0))
            update = self.updates.get(client_id, [])
            result.append(
                ClientContribution(
                    client_id=client_id,
                    display_name=client.display_name,
                    domain=client.domain,
                    record_count=len(client.records),
                    original_norm=original_norm,
                    clipped_norm=l2_norm(update) if update else 0.0,
                    clip_scale=scale,
                    active=client_id in self.active_client_ids,
                )
            )
        return result

    def _reference_parameters(self, retained_ids: list[str]) -> list[float]:
        reference_sum = list(self.noise)
        for client_id in retained_ids:
            for index, value in enumerate(self.updates[client_id]):
                reference_sum[index] += value
        return [value / len(retained_ids) for value in reference_sum]

    @staticmethod
    def _utility_retention(before: TrainingMetrics, after: TrainingMetrics) -> float:
        if before.utility_score <= 0:
            return 100.0
        return min(100.0, 100.0 * after.utility_score / before.utility_score)

    def unlearn(self, client_id: str) -> UnlearningCertificate:
        if self.model is None:
            raise RuntimeError("Train the federated model before requesting unlearning")
        if client_id not in self.clients:
            raise KeyError(f"Unknown client: {client_id}")
        if client_id not in self.active_client_ids:
            raise ValueError(f"{client_id} has already been unlearned")
        if len(self.active_client_ids) <= 1:
            raise ValueError("At least one client must remain in the model")

        client = self.clients[client_id]
        before = self.metrics()
        auc_before = membership_auc(self.model, client.records, NON_MEMBER_TEXTS)
        model_hash_before = before.model_hash

        target_update = self.updates[client_id]
        self.noisy_sum = [aggregate - value for aggregate, value in zip(self.noisy_sum, target_update)]
        self.active_client_ids.remove(client_id)
        self._rebuild_model()

        after = self.metrics()
        auc_after = membership_auc(self.model, client.records, NON_MEMBER_TEXTS)
        reference = self._reference_parameters(self.active_client_ids)
        difference = [actual - expected for actual, expected in zip(self.model.parameters, reference)]
        reference_distance = l2_norm(difference)
        # Because the stored update is subtracted algebraically, its coefficient
        # in the retained aggregate is exactly zero (within floating-point error).
        residual_influence = reference_distance
        retention = self._utility_retention(before, after)
        status = "CERTIFIED" if reference_distance <= 1e-10 and retention >= 70.0 else "REVIEW_REQUIRED"

        certificate = UnlearningCertificate(
            certificate_id=f"CERT-{uuid.uuid4().hex[:12].upper()}",
            session_id=self.session_id,
            client_id=client_id,
            client_name=f"{client.display_name} ({client.domain})",
            issued_at_utc=_utc_now(),
            status=status,
            method="Tracked clipped-update subtraction with retained-client renormalization",
            epsilon=self.epsilon,
            delta=self.delta,
            clip_norm=self.clip_norm,
            noise_multiplier=self.noise_multiplier,
            residual_influence_l2=residual_influence,
            reference_retrain_l2=reference_distance,
            membership_auc_before=auc_before,
            membership_auc_after=auc_after,
            perplexity_before=before.perplexity,
            perplexity_after=after.perplexity,
            accuracy_before=before.next_character_accuracy,
            accuracy_after=after.next_character_accuracy,
            utility_retention_percent=retention,
            clients_before=before.active_clients,
            clients_after=after.active_clients,
            model_hash_before=model_hash_before,
            model_hash_after=after.model_hash,
        )
        audit_event = {"event_type": "CLIENT_UNLEARNING", **certificate.to_dict()}
        record = self.audit.append(audit_event)
        certificate = UnlearningCertificate(
            **{**certificate.to_dict(), "audit_record_hash": record["record_hash"]}
        )
        self.certificates.append(certificate)
        return certificate

    def generate(self, seed_text: str, length: int = 120) -> str:
        if self.model is None:
            raise RuntimeError("Train the federated model first")
        return self.model.generate(seed_text, length=length, random_seed=self.random_seed)

    def export_certificate(self, certificate: UnlearningCertificate, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = certificate.to_dict()
        payload["audit_verification"] = self.audit.verify()[1]
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

