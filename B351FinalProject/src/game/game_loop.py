# src/game/game_loop.py

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol, Optional, Tuple

from .state import GameState
from .board import Player, PLAYER_1, PLAYER_2
from .rules import Action, legal_actions, apply_action


class Agent(Protocol):
    """
    Minimal protocol that any agent must satisfy to work with play_game.

    Your agents (random, heuristic, expectimax, etc.) just need to implement:
        choose_action(self, state, dice) -> Optional[Action]
    """

    def choose_action(self, state: GameState, dice: Tuple[int, int]) -> Optional[Action]:
        ...


@dataclass
class GameResult:
    """Convenience container for the outcome of a single game."""
    winner: Optional[Player]          # +1, -1, or None (draw / no winner)
    final_state: GameState
    turns_played: int


def roll_dice() -> Tuple[int, int]:
    """Roll a pair of fair six-sided dice."""
    return random.randint(1, 6), random.randint(1, 6)


def play_turn(
    state: GameState,
    agent: Agent,
    dice: Optional[Tuple[int, int]] = None,
) -> GameState:
    """
    Play a single turn for the current player using the given agent.

    - Rolls dice (unless provided)
    - Sets dice on the state
    - Lets the agent pick an action given (state, dice)
    - If agent returns an action, applies it
    - Records the turn in history
    - Advances to the next turn (switches player, increments turn_number)

    Returns the *new* GameState after the turn.
    """
    # Work from a copy to avoid surprising external callers
    state = state.copy(copy_history=True)

    # Roll dice if not given
    if dice is None:
        dice = roll_dice()

    d1, d2 = dice
    state.set_dice(d1, d2)

    # Ask agent to choose an action
    chosen: Optional[Action] = agent.choose_action(state, dice)

    if chosen is None:
        # Pass / no-move turn: just record and advance
        state.record_turn(dice, action=None)
        state.next_turn()
        return state

    # Apply the action to get a new state
    new_state = apply_action(state, chosen)

    # Copy history over so we can append this move
    new_state.history = state.history.copy()
    new_state.record_turn(dice, chosen)

    # Advance to next turn (switch player, increment turn_number, clear dice)
    new_state.next_turn()
    return new_state


def play_game(
    agent_p1: Agent,
    agent_p2: Agent,
    max_turns: int = 200,
    seed: Optional[int] = None,
) -> GameResult:
    """
    Play a full game between two agents.

    Parameters
    ----------
    agent_p1 : Agent
        Agent controlling PLAYER_1 (+1).
    agent_p2 : Agent
        Agent controlling PLAYER_2 (-1).
    max_turns : int
        Safety cap on the number of turns (to avoid endless games).
    seed : Optional[int]
        If provided, seeds Python's random module for reproducibility.

    Returns
    -------
    GameResult
        Contains winner (+1 / -1 / None), final_state, and turns_played.
    """
    if seed is not None:
        random.seed(seed)

    state = GameState.initial()

    # Main loop
    while not state.is_game_over() and state.turn_number < max_turns:
        current_player = state.current_player
        agent = agent_p1 if current_player == PLAYER_1 else agent_p2
        state = play_turn(state, agent)

    winner = state.winner()
    return GameResult(winner=winner, final_state=state, turns_played=state.turn_number)


# ---------------------------------------------------------------------------
# Simple random agent for quick demos / smoke tests
# ---------------------------------------------------------------------------

class RandomAgent:
    """Simple random agent compatible with the game loop."""

    def choose_action(self, state: GameState, dice: Tuple[int, int]) -> Optional[Action]:
        legal = legal_actions(state, dice)
        if not legal:
            return None
        return random.choice(list(legal))


if __name__ == "__main__":
    # Quick manual test: random vs random
    p1 = RandomAgent()
    p2 = RandomAgent()
    result = play_game(p1, p2, max_turns=200, seed=0)
    if result.winner is None:
        print(f"Game finished without a winner after {result.turns_played} turns.")
    else:
        print(f"Winner: {result.winner} in {result.turns_played} turns.")

