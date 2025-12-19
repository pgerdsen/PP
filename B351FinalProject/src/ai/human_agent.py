# src/ai/human_agent.py

from __future__ import annotations

from typing import Optional, Tuple

from ..game.state import GameState
from ..game import rules


class HumanAgent:
    """
    Simple terminal-based human agent.

    On your turn, it:
      - shows basic board + bar/borne-off info
      - lists all legal actions as index: step1, step2, ...
      - prompts you to pick an index or pass
    """

    def __init__(self, name: str = "Human") -> None:
        self.name = name

    def _print_board_summary(self, state: GameState) -> None:
        b = state.board
        print("\n=== Board summary ===")
        print("Points (index: signed count; + = P1, - = P2)")
        print(" ".join(f"{i}:{int(v)}" for i, v in enumerate(b.points)))
        print(f"Bar: P1={int(b.bar[0])}, P2={int(b.bar[1])}")
        print(f"Borne off: P1={int(b.borne_off[0])}, P2={int(b.borne_off[1])}")
        print(f"Current player: {int(state.current_player)}")

    def _print_actions(self, actions) -> None:
        print("\nLegal actions:")
        for idx, action in enumerate(actions):
            step_strs = []
            for s in action.steps:
                frm = "BAR" if s.from_point is None else str(s.from_point)
                to = "OFF" if s.to_point is None else str(s.to_point)
                hit = " *hit*" if s.hit_index is not None else ""
                step_strs.append(f"{frm}->{to}{hit}")
            print(f"  [{idx}] " + ", ".join(step_strs))

    def choose_action(
        self,
        state: GameState,
        dice: Tuple[int, int],
    ) -> Optional[rules.Action]:
        """Prompt the user to choose an action; return None to pass."""
        actions = rules.legal_actions(state, dice)
        if not actions:
            print("\nNo legal moves. Passing turn.")
            return None

        self._print_board_summary(state)
        print(f"\nDice: {dice}")
        self._print_actions(actions)

        while True:
            choice = input("Choose action index (or 'p' to pass): ").strip()
            if choice.lower() in {"p", "pass"}:
                return None
            try:
                idx = int(choice)
                if 0 <= idx < len(actions):
                    return actions[idx]
                else:
                    print(f"Please enter a number between 0 and {len(actions)-1}, or 'p'.")
            except ValueError:
                print("Invalid input. Enter an integer index or 'p' to pass.")

