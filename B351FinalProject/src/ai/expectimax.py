# src/ai/expectimax.py
"""
Depth-limited expectimax agent for backgammon.

We treat dice as *chance nodes*:
    Player decision  ->  Chance (dice)  ->  Opponent decision  ->  Chance  -> ...

We always evaluate leaves from the root player's perspective using the
heuristic evaluation from ai.heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple
import random

from ..game.state import GameState
from ..game.board import Player
from ..game import rules

from .heuristics import HeuristicWeights, DEFAULT_WEIGHTS, evaluate_state


# ---------------------------------------------------------------------------
# Dice utilities
# ---------------------------------------------------------------------------

# All ordered outcomes of rolling two fair six-sided dice: 36 equiprobable.
DICE_OUTCOMES: Sequence[Tuple[int, int]] = [
    (d1, d2) for d1 in range(1, 7) for d2 in range(1, 7)
]
DICE_PROBABILITY: float = 1.0 / 36.0


@dataclass
class ExpectimaxConfig:
    """
    Configuration for the expectimax agent.

    depth: number of *decision* plies to look ahead.
           For example, depth=2 means:
               - current player's move (root)
               - opponent's reply
           Chance nodes (dice) do NOT reduce depth themselves.
    """
    depth: int = 2
    weights: HeuristicWeights = DEFAULT_WEIGHTS
    use_symmetry: bool = True  # compress (d1,d2) and (d2,d1) for d1 != d2


class ExpectimaxAgent:
    """
    Depth-limited expectimax agent.

    Usage:
        agent = ExpectimaxAgent(player=rules.PLAYER_1, config=ExpectimaxConfig(depth=2))
        action = agent.choose_action(state, (d1, d2))

    We assume:
        - state.current_player is the player whose turn it is.
        - rules.legal_actions(state, dice) -> list[Action]
        - rules.apply_action(state, action) -> GameState
        - rules.other_player(player) -> Player
        - state.is_game_over() -> bool
    """

    def __init__(self, player: Player, config: Optional[ExpectimaxConfig] = None) -> None:
        self.player: Player = player
        self.config: ExpectimaxConfig = config or ExpectimaxConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def choose_action(
        self,
        state: GameState,
        dice: Tuple[int, int],
    ):
        """
        Choose the best action for the current state and known dice roll.

        Returns None if there are no legal moves.
        """
        legal_actions = rules.legal_actions(state, dice)
        if not legal_actions:
            return None

        root_player = state.current_player
        depth = self.config.depth

        best_value: Optional[float] = None
        best_actions: List = []

        for action in legal_actions:
            # Apply our candidate move.
            next_state = rules.apply_action(state, action)

            # After we move, the opponent rolls dice -> chance node.
            value = self._chance_value(
                state=next_state,
                depth=depth - 1,  # we consumed one decision ply
                current_player=rules.other_player(root_player),
                root_player=root_player,
            )

            if best_value is None or value > best_value:
                best_value = value
                best_actions = [action]
            elif value == best_value:
                best_actions.append(action)

        # Random tie-break so games aren't completely deterministic.
        return random.choice(best_actions)

    # ------------------------------------------------------------------
    # Core expectimax recursion
    # ------------------------------------------------------------------

    def _decision_value(
        self,
        state: GameState,
        depth: int,
        current_player: Player,
        root_player: Player,
        dice: Tuple[int, int],
    ) -> float:
        """
        Decision node: current_player chooses a move given known dice.

        If current_player == root_player -> max node.
        Otherwise -> min node.
        """
        # BASE CASE
        if depth <= 0 or state.is_game_over():
            return evaluate_state(
                state,
                perspective=root_player,
                weights=self.config.weights,
            )

        legal_actions = rules.legal_actions(state, dice)

        # No legal actions: pass turn (or equivalent).
        if not legal_actions:
            next_state = state  # board unchanged
            next_player = rules.other_player(current_player)
            return self._chance_value(
                state=next_state,
                depth=depth - 1,
                current_player=next_player,
                root_player=root_player,
            )

        is_max = (current_player == root_player)
        best_value: Optional[float] = None

        for action in legal_actions:
            next_state = rules.apply_action(state, action)
            next_player = rules.other_player(current_player)

            value = self._chance_value(
                state=next_state,
                depth=depth - 1,
                current_player=next_player,
                root_player=root_player,
            )

            if best_value is None:
                best_value = value
            else:
                if is_max and value > best_value:
                    best_value = value
                elif not is_max and value < best_value:
                    best_value = value

        assert best_value is not None
        return best_value

    def _chance_value(
        self,
        state: GameState,
        depth: int,
        current_player: Player,
        root_player: Player,
    ) -> float:
        """
        Chance node: average over all dice outcomes for `current_player`.
        """
        # BASE CASE
        if depth <= 0 or state.is_game_over():
            return evaluate_state(
                state,
                perspective=root_player,
                weights=self.config.weights,
            )

        # Use symmetry to cut work if desired.
        if self.config.use_symmetry:
            outcomes_with_prob = self._symmetric_dice_outcomes()
        else:
            outcomes_with_prob = [(d, DICE_PROBABILITY) for d in DICE_OUTCOMES]

        total = 0.0

        for dice, prob in outcomes_with_prob:
            try:
                value = self._decision_value(
                    state=state,
                    depth=depth,
                    current_player=current_player,
                    root_player=root_player,
                    dice=dice,
                )
            except Exception as e:
                # Return a very bad value so this path is avoided
                value = float('-inf') if current_player == root_player else float('inf')
            total += prob * value

        return total

    # ------------------------------------------------------------------
    # Dice symmetry helper
    # ------------------------------------------------------------------

    def _symmetric_dice_outcomes(self) -> Iterable[Tuple[Tuple[int, int], float]]:
        """
        Compress (d1, d2) and (d2, d1) when d1 != d2.

        Example:
            - (1,1) has probability 1/36
            - non-doubles like {1,2} represent (1,2) & (2,1) with prob 2/36
        """
        # Doubles
        for d in range(1, 7):
            yield (d, d), 1.0 / 36.0

        # Non-doubles
        for d1 in range(1, 7):
            for d2 in range(d1 + 1, 7):
                # (d1,d2) and (d2,d1) -> 2/36
                yield (d1, d2), 2.0 / 36.0
