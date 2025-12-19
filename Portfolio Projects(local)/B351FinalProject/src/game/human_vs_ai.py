# src/game/human_vs_ai.py

from __future__ import annotations

from .game_loop import play_game
from ..ai.human_agent import HumanAgent
from ..ai.heuristics import HeuristicAgent
from .board import PLAYER_1, PLAYER_2


def main() -> None:
    human = HumanAgent(name="You")
    ai = HeuristicAgent()

    print("Starting game: You (PLAYER_1 = +1) vs Heuristic AI (PLAYER_2 = -1)")
    result = play_game(human, ai, max_turns=200, seed=None)
    print("\nGame over.")
    print("Winner:", result.winner, "Turns:", result.turns_played)


if __name__ == "__main__":
    main()

