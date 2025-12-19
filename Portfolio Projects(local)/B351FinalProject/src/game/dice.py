# src/backgammon/game/dice.py
from __future__ import annotations

import random
from typing import List, Tuple


def roll_dice() -> Tuple[int, int]:
    """Roll two six-sided dice and return (d1, d2)."""
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    return d1, d2


def expand_dice(d1: int, d2: int) -> List[int]:
    """Return the list of pip values to play, handling doubles.

    Examples
    --------
    >>> expand_dice(3, 4)
    [3, 4]
    >>> expand_dice(5, 5)
    [5, 5, 5, 5]
    """
    d1 = int(d1)
    d2 = int(d2)
    if d1 == d2:
        return [d1, d1, d1, d1]
    return [d1, d2]


def all_dice_outcomes() -> List[Tuple[int, int]]:
    """Return all 36 ordered dice outcomes (1..6, 1..6).

    Useful for expectimax chance nodes.
    """
    return [(i, j) for i in range(1, 7) for j in range(1, 7)]

