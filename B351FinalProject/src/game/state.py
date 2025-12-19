# src/backgammon/game/state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence, Any

import numpy as np

from .board import (
    Board,
    Player,
    PLAYER_1,
    PLAYER_2,
    N_CHECKERS_PER_PLAYER,
    player_index,
)

# You can use this type alias if you want to store dice as (d1, d2)
Dice = Optional[tuple[int, int]]


@dataclass
class GameState:
    """
    Full game state for a backgammon position.

    This wraps:
      - Board (checkers on points, bar, borne off)
      - current_player: whose turn it is (+1 or -1)
      - dice: current dice roll (if any)
      - turn_number: how many turns have been played
      - history: optional list of turn records (for logging/analysis)

    Rules (legal move generation, applying actions) live in rules.py.
    """

    board: Board
    current_player: Player
    dice: Dice = None
    turn_number: int = 0

    # Each entry in history can be a dict like:
    # {"turn": int, "player": int, "dice": (d1, d2), "action": <whatever>}
    history: list[dict[str, Any]] = field(default_factory=list)

    # ----- Constructors -----

    @classmethod
    def initial(cls) -> "GameState":
        """
        Create the standard starting state:
          - initial board setup
          - PLAYER_1 to move
          - no dice yet
          - turn_number = 0
        """
        board = Board.initial()
        return cls(board=board, current_player=PLAYER_1, dice=None, turn_number=0)

    def copy(self, copy_history: bool = False) -> "GameState":
        """
        Deep copy of the game state.

        For AI search and simulation you usually want:
          - a fresh Board (so mutations don't leak)
          - same current_player, dice, turn_number
          - optional history copy (often you don't need it in search)

        Parameters
        ----------
        copy_history : bool
            If True, copy history list as well. For fast search/rollouts,
            you can leave this False (default) to avoid overhead.
        """
        new_history = self.history.copy() if copy_history else []
        return GameState(
            board=self.board.copy(),
            current_player=self.current_player,
            dice=self.dice,
            turn_number=self.turn_number,
            history=new_history,
        )

    # ----- Query helpers -----

    def is_game_over(self) -> bool:
        """
        Return True if either player has borne off all their checkers.

        We use the Board's borne_off array and the constant
        N_CHECKERS_PER_PLAYER defined in board.py.
        """
        p1_off = int(self.board.borne_off[player_index(PLAYER_1)])
        p2_off = int(self.board.borne_off[player_index(PLAYER_2)])
        return (p1_off >= N_CHECKERS_PER_PLAYER) or (p2_off >= N_CHECKERS_PER_PLAYER)

    def winner(self) -> Optional[Player]:
        """
        Return the winner (+1 or -1) if the game is over, otherwise None.

        Note: this just checks borne_off counts. If you later implement
        gammons/backgammons with different scoring, you can still use this
        as the base "who won" method.
        """
        if not self.is_game_over():
            return None

        p1_off = int(self.board.borne_off[player_index(PLAYER_1)])
        p2_off = int(self.board.borne_off[player_index(PLAYER_2)])

        if p1_off >= N_CHECKERS_PER_PLAYER and p2_off >= N_CHECKERS_PER_PLAYER:
            # Extremely unlikely / tie case; you can choose a convention here.
            # For now, just say no winner.
            return None
        elif p1_off >= N_CHECKERS_PER_PLAYER:
            return PLAYER_1
        elif p2_off >= N_CHECKERS_PER_PLAYER:
            return PLAYER_2
        else:
            return None

    def current_player_index(self) -> int:
        """Return 0 for PLAYER_1, 1 for PLAYER_2 (matches Board.bar / borne_off)."""
        return player_index(self.current_player)

    # ----- Turn / dice management -----

    def set_dice(self, d1: int, d2: int) -> None:
        """
        Set the current dice roll for the state.

        rules.py can use this along with turn_number to generate legal actions.
        """
        self.dice = (int(d1), int(d2))

    def clear_dice(self) -> None:
        """Clear dice after a turn is complete."""
        self.dice = None

    def next_turn(self) -> None:
        """
        Advance to the next turn:
          - switch current player
          - increment turn_number
          - clear dice (they must be re-rolled)
        """
        self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2
        self.turn_number += 1
        self.dice = None

    # ----- History / logging helpers -----

    def record_turn(self, dice: tuple[int, int], action: Any) -> None:
        """
        Append a single turn record to history.

        This is deliberately generic so that experiments and logging
        can easily convert history -> pandas.DataFrame.

        Example structure for 'action' (defined in rules.py):
          - a tuple of (from_point, to_point, was_hit, ...), or
          - a custom Action class

        For now, we just store it as-is.
        """
        self.history.append(
            {
                "turn": self.turn_number,
                "player": int(self.current_player),
                "dice": (int(dice[0]), int(dice[1])),
                "action": action,
            }
        )

    def history_as_array(self) -> np.ndarray:
        """
        Optional helper: return a NumPy array view of the history turn numbers & players.

        This can be useful for quick numeric analysis, and it showcases how the
        package choices (NumPy + later Pandas) fit the design.
        """
        if not self.history:
            return np.empty((0, 2), dtype=int)

        turns = [h["turn"] for h in self.history]
        players = [h["player"] for h in self.history]
        return np.stack([turns, players], axis=1)

