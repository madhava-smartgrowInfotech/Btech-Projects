"""Seating engine: graph colouring, roll rules, solver properties and the independent validator."""
from __future__ import annotations

from dataclasses import replace

import pytest

from app.services.engine import EngineCandidate, EngineHall, Placement, Rules, solve, validate
from app.services.engine.baselines import sequential
from app.services.engine.graph import parse_seat_label, seat_classes, seat_label, seat_neighbours
from app.services.engine.rolls import close_pairs, parse_roll, roll_distance, violates_gap


def make_hall(key="H1", rows=6, cols=8, blocked=(), accessible=((0, 0), (0, 1)), aisles=(4,)):
    return EngineHall(key=key, rows=rows, cols=cols, blocked=frozenset(blocked), accessible=frozenset(accessible),
                      aisles_after=frozenset(aisles))


def make_candidates(spec: dict[str, int], dept_of=lambda paper: paper[:2], accessible=()) -> list[EngineCandidate]:
    """spec: paper -> count. Roll numbers are serial per department, interleaved across its papers."""
    out, serial = [], {}
    for paper, count in spec.items():
        dept = dept_of(paper)
        for _ in range(count):
            serial[dept] = serial.get(dept, 100) + 1
            roll = f"{dept}24{serial[dept]:04d}"
            out.append(EngineCandidate(key=roll, roll_no=roll, paper=paper, course=paper, department=dept,
                                       needs_accessible=roll in accessible))
    return out


# ---------------------------------------------------------------- graph

def test_seat_labels_round_trip():
    assert seat_label(0, 0) == "A1"
    assert seat_label(2, 3) == "C4"
    assert seat_label(26, 0) == "AA1"
    for r in range(30):
        for c in range(12):
            assert parse_seat_label(seat_label(r, c)) == (r, c)
    assert parse_seat_label("4C") is None


def test_neighbours_respect_aisles_and_blocked_seats():
    hall = make_hall(blocked={(1, 1)})
    around = set(seat_neighbours(hall, 8)[(0, 3)])
    assert (0, 4) not in around and (1, 4) not in around      # across the aisle after column 4
    assert (0, 2) in around and (1, 3) in around
    assert (1, 1) not in seat_neighbours(hall, 8)[(0, 0)]      # blocked seat
    assert set(seat_neighbours(hall, 4)[(2, 2)]) == {(1, 2), (3, 2), (2, 1), (2, 3)}


@pytest.mark.parametrize("adjacency", [4, 8])
def test_colour_classes_never_touch(adjacency):
    hall = make_hall(rows=9, cols=11, blocked={(3, 3)}, aisles=(3, 7))
    neighbours = seat_neighbours(hall, adjacency)
    for seats in seat_classes(hall, adjacency).values():
        members = set(seats)
        for seat in seats:
            assert not members.intersection(neighbours[seat])
    assert sum(len(v) for v in seat_classes(hall, adjacency).values()) == hall.capacity


# ---------------------------------------------------------------- rolls

def test_roll_parsing_and_gap():
    assert parse_roll("acf24017") == ("ACF", 24017)
    assert roll_distance("ACF24017", "ACF24021") == 4
    assert roll_distance("ACF24017", "SWE24017") is None
    assert violates_gap("ACF24017", "ACF24021", 5)
    assert not violates_gap("ACF24017", "ACF24022", 5)
    assert not violates_gap("ACF24017", "ACF24018", 0)
    assert close_pairs(["A1", "A3", "A9", "B2"], 3) == [(0, 1)]


# ---------------------------------------------------------------- solver

@pytest.fixture(scope="module")
def session():
    halls = [make_hall("H1", 6, 8), make_hall("H2", 8, 8), make_hall("H3", 6, 6, aisles=())]
    cands = make_candidates({"AA-101": 30, "AA-102": 22, "BB-201": 28, "BB-202": 18, "CC-301": 26},
                            accessible={"AA240105", "CC240103"})
    return cands, halls


def test_plan_satisfies_every_hard_rule(session):
    cands, halls = session
    rules = Rules()
    result = solve(cands, halls, rules, seed=42)
    assert result.ok, result.reasons
    card = validate(cands, halls, result.placements, rules)
    assert card.hard_ok
    assert card.placed == len(cands)
    assert card.same_paper_pairs == 0
    assert card.roll_gap_violations == 0
    assert card.accessible_violations == 0


def test_same_seed_reproduces_the_plan(session):
    cands, halls = session
    first = solve(cands, halls, Rules(), seed=7)
    second = solve(list(reversed(cands)), halls, Rules(), seed=7)
    assert first.ok and second.ok
    assert sorted(first.placements, key=lambda p: p.candidate) == sorted(second.placements, key=lambda p: p.candidate)


def test_different_seeds_give_different_plans(session):
    cands, halls = session
    a = {p.candidate: (p.hall, p.row, p.col) for p in solve(cands, halls, Rules(), seed=1).placements}
    b = {p.candidate: (p.hall, p.row, p.col) for p in solve(cands, halls, Rules(), seed=2).placements}
    moved = sum(a[k] != b[k] for k in a)
    assert moved > len(a) * 0.5


def test_four_neighbour_rules_and_balanced_fill(session):
    cands, halls = session
    rules = Rules(adjacency=4, fill_strategy="balanced")
    result = solve(cands, halls, rules, seed=3)
    assert result.ok, result.reasons
    card = validate(cands, halls, result.placements, rules)
    assert card.hard_ok
    assert card.halls_used == len(halls)


def test_compact_strategy_uses_fewer_halls():
    halls = [make_hall(f"H{i}", 8, 8) for i in range(1, 7)]
    cands = make_candidates({"AA-1": 20, "BB-1": 20, "CC-1": 20, "DD-1": 20})
    result = solve(cands, halls, Rules(), seed=5)
    assert result.ok
    assert validate(cands, halls, result.placements, Rules()).halls_used < len(halls)


def test_impossible_inputs_explain_why():
    hall = make_hall("H1", 4, 4, aisles=())
    too_many = make_candidates({"AA-1": 10, "BB-1": 10})
    result = solve(too_many, [hall], Rules(), seed=1)
    assert not result.ok
    assert "usable seats" in result.reasons[0]

    one_paper = make_candidates({"AA-1": 9})
    result = solve(one_paper, [hall], Rules(), seed=1)
    assert not result.ok
    assert any("without two neighbours" in r for r in result.reasons)

    accessible = make_candidates({"AA-1": 3}, accessible={"AA240101", "AA240102", "AA240103"})
    result = solve(accessible, [hall], Rules(), seed=1)
    assert not result.ok
    assert any("accessible" in r for r in result.reasons)


# ---------------------------------------------------------------- validator

def test_validator_flags_every_kind_of_problem():
    hall = make_hall("H1", 3, 3, accessible={(0, 0)}, aisles=())
    cands = [
        EngineCandidate("A1", "AA240001", "P1", "P1", "AA"),
        EngineCandidate("A2", "AA240002", "P1", "P1", "AA"),
        EngineCandidate("A3", "AA240003", "P2", "P2", "AA", needs_accessible=True),
        EngineCandidate("A4", "AA240050", "P3", "P3", "BB"),
    ]
    placements = [
        Placement("A1", "H1", 1, 1),
        Placement("A2", "H1", 1, 2),   # same paper next to A1, roll gap 1
        Placement("A3", "H1", 2, 2),   # not an accessible seat
        Placement("A4", "H1", 1, 1),   # seat already taken
    ]
    card = validate(cands, [hall], placements, Rules())
    assert card.same_paper_pairs == 1
    assert card.roll_gap_violations >= 1
    assert card.accessible_violations == 1
    assert card.capacity_violations == 2   # double-booked seat + A4 left without a seat
    assert not card.hard_ok
    kinds = {v["type"] for v in card.violations}
    assert {"same_paper", "roll_gap", "accessible", "capacity"} <= kinds


def test_sequential_baseline_creates_conflicts_the_engine_avoids(session):
    cands, halls = session
    rules = Rules()
    baseline = validate(cands, halls, sequential(cands, halls, rules), rules)
    engine = validate(cands, halls, solve(cands, halls, rules, seed=9).placements, rules)
    assert baseline.same_paper_pairs > 0
    assert engine.same_paper_pairs == 0


def test_rules_are_used_as_given(session):
    cands, halls = session
    strict = replace(Rules(), roll_gap=12)
    result = solve(cands, halls, strict, seed=11)
    assert result.ok, result.reasons
    assert validate(cands, halls, result.placements, strict).roll_gap_violations == 0
