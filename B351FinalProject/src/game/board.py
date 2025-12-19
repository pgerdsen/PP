# src/backgammon/game/board.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

# Player representation: +1 for player 1, -1 for player 2
Player = Literal[1, -1]

PLAYER_1: Player = 1
PLAYER_2: Player = -1

N_POINTS = 24
N_CHECKERS_PER_PLAYER = 15


def player_index(player: Player) -> int:
    """Map player (+1 or -1) to index 0 or 1 for arrays like bar/borne_off."""
    return 0 if player == PLAYER_1 else 1


@dataclass
class Board:
    """
    Backgammon board representation.

    points[i] = signed integer on point (i+1):
      > 0  -> that many checkers for PLAYER_1
      < 0  -> abs(value) checkers for PLAYER_2

    bar[0]      = number of PLAYER_1 checkers on the bar
    bar[1]      = number of PLAYER_2 checkers on the bar
    borne_off[0] = number of PLAYER_1 checkers borne off
    borne_off[1] = number of PLAYER_2 checkers borne off
    """

    points: np.ndarray  # shape (24,)
    bar: np.ndarray     # shape (2,)
    borne_off: np.ndarray  # shape (2,)

    @classmethod
    def initial(cls) -> "Board":
        """
        Construct the standard starting position.

        Convention:
          index 0  = point 1
          index 23 = point 24

        Standard setup (from Player 1's perspective):
          - Player 1: 2 on 24, 5 on 13, 3 on 8, 5 on 6
          - Player 2: 2 on 1, 5 on 12, 3 on 17, 5 on 19
        """
        points = np.zeros(N_POINTS, dtype=int)

        # Player 1 (positive)
        points[23] = 2 * PLAYER_1  # point 24
        points[12] = 5 * PLAYER_1  # point 13
        points[7]  = 3 * PLAYER_1  # point 8
        points[5]  = 5 * PLAYER_1  # point 6

        # Player 2 (negative)
        points[0]  = 2 * PLAYER_2  # point 1
        points[11] = 5 * PLAYER_2  # point 12
        points[16] = 3 * PLAYER_2  # point 17
        points[18] = 5 * PLAYER_2  # point 19

        bar = np.zeros(2, dtype=int)
        borne_off = np.zeros(2, dtype=int)

        return cls(points=points, bar=bar, borne_off=borne_off)

    def copy(self) -> "Board":
        """Deep copy so game states don't share mutable arrays."""
        return Board(
            points=self.points.copy(),
            bar=self.bar.copy(),
            borne_off=self.borne_off.copy(),
        )

    # ----- Basic queries -----

    def owner_of_point(self, index: int) -> int:
        """Return +1, -1 or 0 depending on who owns point index (0-based)."""
        val = self.points[index]
        if val > 0:
            return PLAYER_1
        elif val < 0:
            return PLAYER_2
        else:
            return 0  # empty

    def count_on_point(self, index: int) -> int:
        """Return the number of checkers on this point (0-based index)."""
        return abs(int(self.points[index]))

    def total_checkers_for(self, player: Player) -> int:
        """Total checkers belonging to `player` anywhere (board + bar + borne off)."""
        idx = player_index(player)
        on_board = int(np.sum(self.points[self.points * player > 0] * player))
        return on_board + int(self.bar[idx]) + int(self.borne_off[idx])

    # ----- Mutations (used by rules.py) -----

    def move_checker(self, player: Player, from_idx: int | None, to_idx: int | None) -> None:
        """
        Move a single checker belonging to `player`.

        - from_idx is 0-23 for a point, or None for bar.
        - to_idx   is 0-23 for a point, or None for bearing off.

        This function does NOT check legality. That belongs in rules.py.
        """
        p_idx = player_index(player)

        # Remove from source
        if from_idx is None:
            # from bar
            if self.bar[p_idx] <= 0:
                raise ValueError("No checker for player on bar to move.")
            self.bar[p_idx] -= 1
        else:
            if self.owner_of_point(from_idx) != player:
                raise ValueError("Source point does not belong to player.")
            # decrement magnitude at from_idx
            self.points[from_idx] -= player

        # Add to destination
        if to_idx is None:
            # bearing off
            self.borne_off[p_idx] += 1
            return

        # Possibly hitting opponent blot is handled in rules.py
        self.points[to_idx] += player

    def hit_checker_at(self, victim_player: Player, index: int) -> None:
        """
        Send a single checker from `index` to the bar for victim_player.
        Called from rules.py when applying a hitting move.
        """
        v_idx = player_index(victim_player)
        if self.owner_of_point(index) != victim_player:
            raise ValueError("Cannot hit: point not owned by victim_player.")
        # remove one checker from that point
        self.points[index] += (-victim_player)  # subtract sign
        self.bar[v_idx] += 1

    # ----- Utilities helpful for agents/evaluation -----

    def as_array(self) -> np.ndarray:
        """
        Return a copy of the points array. Agents can use this
        to build feature vectors without mutating the board.
        """
        return self.points.copy()

    def mirrored_for(self, player: Player) -> "Board":
        """
        Return a view of the board from `player`'s perspective.

        For convenience in evaluation:
          - Player 1 sees points 0..23
          - Player 2 can see the board flipped so that "forward"
            is always the same direction for both players.

        NOTE: this returns a NEW Board; it does not modify self.
        """
        if player == PLAYER_1:
            return self.copy()

        # For PLAYER_2, flip points and swap player signs
        flipped_points = np.flip(self.points) * -1
        # Swap bar and borne_off counts between players
        swapped_bar = self.bar[::-1].copy()
        swapped_borne_off = self.borne_off[::-1].copy()
        return Board(points=flipped_points, bar=swapped_bar, borne_off=swapped_borne_off)

