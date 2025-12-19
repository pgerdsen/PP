"""
Main entry point for graphical backgammon UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure we can import as a package
# Add the project root (parent of src) to path so package imports work
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.game.state import GameState
from src.ui.graphical import GraphicalUI


def main():
    """Start the graphical backgammon game."""
    state = GameState.initial()
    ui = GraphicalUI(state)
    ui.run()


if __name__ == "__main__":
    main()

