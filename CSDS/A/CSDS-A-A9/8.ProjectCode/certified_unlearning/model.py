"""A compact character language model and its federated parameter updates."""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass
from typing import Iterable, Sequence


ALPHABET = "^$ abcdefghijklmnopqrstuvwxyz.,?!"
INDEX = {character: position for position, character in enumerate(ALPHABET)}
DIMENSION = len(ALPHABET) * len(ALPHABET)


def normalize_text(text: str) -> str:
    cleaned = "".join(character if character in INDEX else " " for character in text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _offset(left: str, right: str) -> int:
    return INDEX[left] * len(ALPHABET) + INDEX[right]


def raw_update(records: Iterable[str]) -> list[float]:
    counts = [0.0] * DIMENSION
    for record in records:
        text = normalize_text(record)
        sequence = f"^{text}$"
        for left, right in zip(sequence, sequence[1:]):
            counts[_offset(left, right)] += 1.0
    return counts


def l2_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def clipped_update(records: Iterable[str], clip_norm: float) -> tuple[list[float], float, float]:
    update = raw_update(records)
    original_norm = l2_norm(update)
    scale = min(1.0, clip_norm / original_norm) if original_norm else 1.0
    return [value * scale for value in update], original_norm, scale


@dataclass
class CharacterLanguageModel:
    """Bigram language model backed by a flat parameter vector."""

    parameters: list[float]
    smoothing: float = 0.15

    def _row_probabilities(self, character: str) -> list[float]:
        character = character if character in INDEX else " "
        start = INDEX[character] * len(ALPHABET)
        values = [max(0.0, self.parameters[start + i]) + self.smoothing for i in range(len(ALPHABET))]
        # Do not generate a second start marker.
        values[INDEX["^"]] = 0.0
        total = sum(values)
        return [value / total for value in values]

    def negative_log_likelihood(self, text: str) -> float:
        sequence = f"^{normalize_text(text)}$"
        if len(sequence) < 2:
            return 0.0
        loss = 0.0
        for left, right in zip(sequence, sequence[1:]):
            probability = self._row_probabilities(left)[INDEX[right]]
            loss -= math.log(max(probability, 1e-12))
        return loss / (len(sequence) - 1)

    def perplexity(self, records: Iterable[str]) -> float:
        losses = [self.negative_log_likelihood(record) for record in records]
        return math.exp(sum(losses) / len(losses)) if losses else float("inf")

    def next_character_accuracy(self, records: Iterable[str]) -> float:
        correct = 0
        total = 0
        for record in records:
            sequence = f"^{normalize_text(record)}$"
            for left, right in zip(sequence, sequence[1:]):
                probabilities = self._row_probabilities(left)
                prediction = max(range(len(probabilities)), key=probabilities.__getitem__)
                correct += int(prediction == INDEX[right])
                total += 1
        return correct / total if total else 0.0

    def generate(self, seed_text: str = "privacy", length: int = 120, random_seed: int = 7) -> str:
        rng = random.Random(random_seed)
        output = normalize_text(seed_text) or "privacy"
        current = output[-1]
        for _ in range(max(1, length)):
            probabilities = self._row_probabilities(current)
            choice = rng.choices(range(len(ALPHABET)), weights=probabilities, k=1)[0]
            character = ALPHABET[choice]
            if character == "$":
                if len(output) >= 20:
                    break
                current = "^"
                continue
            output += character
            current = character
        return output


def membership_auc(model: CharacterLanguageModel, members: Iterable[str], non_members: Iterable[str]) -> float:
    """Return attack AUC where lower language-model loss predicts membership."""

    member_scores = [-model.negative_log_likelihood(text) for text in members]
    non_member_scores = [-model.negative_log_likelihood(text) for text in non_members]
    if not member_scores or not non_member_scores:
        return 0.5
    wins = 0.0
    for member in member_scores:
        for non_member in non_member_scores:
            if member > non_member:
                wins += 1.0
            elif member == non_member:
                wins += 0.5
    return wins / (len(member_scores) * len(non_member_scores))

