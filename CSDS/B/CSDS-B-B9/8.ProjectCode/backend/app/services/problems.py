"""Coding problem bank (data/problems.json, produced by scripts/gen_problems.py)."""
import json
from functools import lru_cache

from ..config import DATA


@lru_cache(maxsize=1)
def _all():
    items = json.loads((DATA / "problems.json").read_text(encoding="utf-8"))
    return {p["slug"]: p for p in items}


def get(slug):
    return _all().get(slug)


def all_problems():
    return list(_all().values())


def public(p, full=False):
    d = {"id": p["id"], "slug": p["slug"], "title": p["title"], "difficulty": p["difficulty"], "topic": p["topic"],
         "hidden_tests": len(p["hidden"])}
    if full:
        d["statement"] = p["statement"]
        d["samples"] = p["samples"]
    return d


def tests_for_submit(p):
    return p["samples"] + p["hidden"]
