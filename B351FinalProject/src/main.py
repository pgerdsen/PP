from __future__ import annotations

import sys
from pathlib import Path

# Ensure we can import as a package
# Add the project root (parent of src) to path so package imports work
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ai.heuristics import HeuristicAgent
from src.ai.expectimax import ExpectimaxAgent, ExpectimaxConfig
from src.game.state import GameState
from src.game.dice import roll_dice
from src.game import rules


def main() -> None:
    # Start from the standard initial backgammon position
    state = GameState.initial()

    print("Initial board:")
    print(state.board)
    print("Current player:", state.current_player)

    # Create both agents
    heuristic_agent = HeuristicAgent()
    expectimax_agent = ExpectimaxAgent(
        player=rules.PLAYER_1,                # assuming PLAYER_1 moves first
        config=ExpectimaxConfig(depth=2)
    )

    # Roll dice once and let both agents respond to the same roll
    d1, d2 = roll_dice()
    dice = (d1, d2)
    print(f"\nDice rolled: {d1}, {d2}")

    # Heuristic agent move
    h_action = heuristic_agent.choose_action(state, dice)
    print("\nHeuristic agent chose:")
    print(h_action)

    # Expectimax agent move
    e_action = expectimax_agent.choose_action(state, dice)
    print("\nExpectimax agent chose:")
    print(e_action)


if __name__ == "__main__":
    main()
