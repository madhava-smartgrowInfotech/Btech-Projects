"""Common manual seating methods used as baselines.

The implementations live in the product engine (``app.services.engine.baselines``)
so the in-product "conflicts avoided" figure and this benchmark use the same code.
"""
import ml  # noqa: F401
from app.services.engine.baselines import BASELINES, random_shuffle, round_robin, seat_order, sequential
from app.services.engine.rolls import roll_sort_key

__all__ = ["BASELINES", "random_shuffle", "roll_sort_key", "round_robin", "seat_order", "sequential"]
