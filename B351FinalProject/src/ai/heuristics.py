# src/ai/heuristics.py
"""
- Generate all legal moves for the current player.
- For each move, look at the resulting position.
- Use a short evaluation that:
    * rewards making points (>= 2 checkers on a point)
    * rewards hitting (opponent checkers on the bar)
    * rewards moving checkers toward home / bearing off
    * penalizes exposed blots (single checkers)
    * penalizes having checkers on the bar
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import random

from ..game.board import Board, Player, PLAYER_1, PLAYER_2, N_POINTS, player_index
from ..game.state import GameState
from ..game import rules


# ---------------------------------------------------------------------------
# Feature weights
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HeuristicWeights:
    """Weights for the linear evaluation."""

    made_point: float = 1.0           # any point with >= 2 of our checkers
    home_made_point: float = 0.5      # extra reward for made points in home board
    blot: float = -1.0                # exposed single checker
    our_bar: float = -2.0             # each of our checkers on the bar
    opp_bar: float = 1.5              # each opposing checker on the bar
    borne_off: float = 2.0            # each checker we have borne off
    opp_borne_off: float = -1.0       # each checker opponent has borne off
    pip_distance: float = -0.1        # total pip distance to bear off (smaller is better)


DEFAULT_WEIGHTS = HeuristicWeights()


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate_board(
    board: Board,
    player: Player,
    weights: HeuristicWeights = DEFAULT_WEIGHTS,
) -> float:
    """
    Evaluate a board position from the perspective of `player`.

    Higher scores are better for `player`.
    """

    # Re-orient so the evaluating player always sees the board the same way.
    # After mirrored_for, "our" checkers are positive and we treat ourselves as PLAYER_1.
    b = board.mirrored_for(player)
    me_idx = player_index(PLAYER_1)   # 0
    opp_idx = player_index(PLAYER_2)  # 1

    points = b.points

    # --- Feature 1: made points & blots -----------------------------------
    made_points = 0
    home_made_points = 0
    blots = 0

    home_range = rules.home_board_range(PLAYER_1)  # indices 0..5 in this orientation

    for idx in range(N_POINTS):
        val = int(points[idx])
        if val > 0:   # our checkers
            count = val
            if count >= 2:
                made_points += 1
                if idx in home_range:
                    home_made_points += 1
            elif count == 1:
                blots += 1

    # --- Feature 2: bar and borne-off info --------------------------------
    our_bar = int(b.bar[me_idx])
    opp_bar = int(b.bar[opp_idx])
    our_borne = int(b.borne_off[me_idx])
    opp_borne = int(b.borne_off[opp_idx])

    # --- Feature 3: pip distance ------------------------------------------
    # In this orientation, point index i is (i+1) pips from bearing off.
    pip_distance = 0
    for idx in range(N_POINTS):
        val = int(points[idx])
        if val > 0:
            pip_distance += val * (idx + 1)

    # Treat each checker on the bar as 25 pips away (standard backgammon convention).
    pip_distance += our_bar * 25

    # --- Combine features linearly ----------------------------------------
    score = 0.0
    score += weights.made_point * made_points
    score += weights.home_made_point * home_made_points
    score += weights.blot * blots
    score += weights.our_bar * our_bar
    score += weights.opp_bar * opp_bar
    score += weights.borne_off * our_borne
    score += weights.opp_borne_off * opp_borne
    score += weights.pip_distance * pip_distance

    return float(score)


def evaluate_state(
    state: GameState,
    perspective: Player,
    weights: HeuristicWeights = DEFAULT_WEIGHTS,
) -> float:
    """Convenience wrapper to evaluate a full GameState."""
    return evaluate_board(state.board, perspective, weights=weights)


# ---------------------------------------------------------------------------
# Simple heuristic agent
# ---------------------------------------------------------------------------

class HeuristicAgent:
    """
    One-ply agent that picks the move with the best heuristic value.

    Algorithm:
      1. Use rules.legal_actions to generate all legal actions for the dice.
      2. For each action, apply it (rules.apply_action) to get a successor state.
      3. Evaluate the successor from the current player's perspective.
      4. Pick an action with maximal score (break ties randomly).
    """

    def __init__(self, weights: HeuristicWeights | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS

    def choose_action(
        self,
        state: GameState,
        dice: Tuple[int, int],
    ) -> Optional[rules.Action]:
        """Return chosen Action for the current player, or None if no legal moves."""
        legal = rules.legal_actions(state, dice)
        if not legal:
            return None

        player = state.current_player

        best_actions: list[rules.Action] = []
        best_value: float | None = None

        for action in legal:
            next_state = rules.apply_action(state, action)
            value = evaluate_state(next_state, perspective=player, weights=self.weights)

            if best_value is None or value > best_value:
                best_value = value
                best_actions = [action]
            elif value == best_value:
                best_actions.append(action)

        # Random tie-break so games aren't completely deterministic.
        return random.choice(best_actions)
