"""Roll numbers: natural ordering and the roll-gap rule.

A roll number is split into a prefix and its trailing number
(``ACF24017`` -> ``("ACF", 24017)``). Only roll numbers with the same prefix
are compared; the distance is the difference of the numbers.
"""
from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence

_ROLL = re.compile(r"^(.*?)(\d+)$")


def parse_roll(roll_no: str) -> tuple[str, int | None]:
    text = roll_no.strip().upper()
    match = _ROLL.match(text)
    return (match.group(1), int(match.group(2))) if match else (text, None)


def roll_sort_key(roll_no: str) -> tuple[str, int, str]:
    prefix, number = parse_roll(roll_no)
    return prefix, -1 if number is None else number, roll_no


def roll_distance(a: str, b: str) -> int | None:
    """Distance between two roll numbers, or None when they cannot be compared."""
    pa, na = parse_roll(a)
    pb, nb = parse_roll(b)
    if pa != pb or na is None or nb is None:
        return None
    return abs(na - nb)


def violates_gap(a: str, b: str, gap: int) -> bool:
    if gap <= 1:
        return False
    distance = roll_distance(a, b)
    return distance is not None and distance < gap


def close_pairs(roll_numbers: Sequence[str], gap: int) -> list[tuple[int, int]]:
    """Index pairs (i, j), i < j, whose roll numbers are closer than ``gap``."""
    if gap <= 1:
        return []
    by_prefix: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for index, roll in enumerate(roll_numbers):
        prefix, number = parse_roll(roll)
        if number is not None:
            by_prefix[prefix].append((number, index))
    pairs: list[tuple[int, int]] = []
    for items in by_prefix.values():
        items.sort()
        for pos, (number, index) in enumerate(items):
            nxt = pos + 1
            while nxt < len(items) and items[nxt][0] - number < gap:
                other = items[nxt][1]
                pairs.append((min(index, other), max(index, other)))
                nxt += 1
    return sorted(pairs)
