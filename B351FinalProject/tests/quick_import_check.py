# quick_import_check.py

from backgammon.game.board import Board
from backgammon.game.state import GameState
from backgammon.game.dice import roll_dice, expand_dice
from backgammon.game.rules import Step, Action, legal_actions, apply_action

print("Imports OK ✅")

s = GameState.initial()
d = (3, 4)
acts = legal_actions(s, d)
print(f"Initial state, dice {d}, number of actions: {len(acts)}")

