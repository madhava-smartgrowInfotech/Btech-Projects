"""Small, local text corpus used by the offline demonstrator.

Each client owns its records. The coordinator receives only the clipped model
update created from those records, mirroring the data boundary in federated
learning.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClientDataset:
    client_id: str
    display_name: str
    domain: str
    records: tuple[str, ...]


CLIENTS: tuple[ClientDataset, ...] = (
    ClientDataset(
        "client_finance",
        "Client 01",
        "Finance",
        (
            "private banking records require careful access control.",
            "the customer reviewed a secure account statement.",
            "fraud monitoring protects every payment transaction.",
            "a savings account earns interest each month.",
            "financial privacy builds customer trust.",
        ),
    ),
    ClientDataset(
        "client_health",
        "Client 02",
        "Healthcare",
        (
            "patient records remain private during medical analysis.",
            "the clinic schedules a routine health assessment.",
            "a doctor reviews symptoms before suggesting treatment.",
            "secure systems protect sensitive medical information.",
            "preventive care supports a healthy community.",
        ),
    ),
    ClientDataset(
        "client_education",
        "Client 03",
        "Education",
        (
            "students learn data science through practical projects.",
            "the teacher explains a machine learning experiment.",
            "a library provides books for independent study.",
            "regular practice improves programming skills.",
            "education creates opportunities for every learner.",
        ),
    ),
    ClientDataset(
        "client_retail",
        "Client 04",
        "Retail",
        (
            "the store processes an online order securely.",
            "customers compare product quality and delivery time.",
            "inventory planning keeps popular items available.",
            "a digital receipt confirms the completed purchase.",
            "helpful service improves the shopping experience.",
        ),
    ),
    ClientDataset(
        "client_travel",
        "Client 05",
        "Travel",
        (
            "the traveler books a quiet hotel near the station.",
            "a morning train connects the city to the coast.",
            "the journey includes a guide and a local map.",
            "passengers receive updates about the flight schedule.",
            "careful planning makes travel safe and enjoyable.",
        ),
    ),
)


PUBLIC_EVALUATION: tuple[str, ...] = (
    "privacy controls protect people and their information.",
    "secure learning systems should preserve useful knowledge.",
    "the model predicts the next character in a sentence.",
    "careful evaluation measures quality after an update.",
    "federated training keeps source records on each client.",
)


NON_MEMBER_TEXTS: tuple[str, ...] = (
    "confidential information needs responsible handling.",
    "a useful system can explain its measured results.",
    "researchers compare a new model with a clean baseline.",
    "software testing detects errors before deployment.",
    "a transparent report supports an independent review.",
)

