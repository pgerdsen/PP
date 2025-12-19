#!/usr/bin/env python3
"""Test script to diagnose compilation/runtime errors."""

import sys
from pathlib import Path

# Add project root to path (go up one level from tests/)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Testing imports...")

try:
    from src.game.state import GameState
    print("✓ GameState imported")
except Exception as e:
    print(f"✗ Failed to import GameState: {e}")
    sys.exit(1)

try:
    from src.game.board import PLAYER_1, PLAYER_2
    print("✓ Board constants imported")
except Exception as e:
    print(f"✗ Failed to import board constants: {e}")
    sys.exit(1)

try:
    from src.game import rules
    print("✓ Rules imported")
except Exception as e:
    print(f"✗ Failed to import rules: {e}")
    sys.exit(1)

try:
    from src.ai.expectimax import ExpectimaxAgent, ExpectimaxConfig
    print("✓ ExpectimaxAgent imported")
except Exception as e:
    print(f"✗ Failed to import ExpectimaxAgent: {e}")
    sys.exit(1)

try:
    from src.ui.graphical import GraphicalUI
    print("✓ GraphicalUI imported")
except Exception as e:
    print(f"✗ Failed to import GraphicalUI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from src.ui.graphical_human_vs_ai import HumanVsAIGraphicalUI, main
    print("✓ HumanVsAIGraphicalUI imported")
except Exception as e:
    print(f"✗ Failed to import HumanVsAIGraphicalUI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All imports successful!")
print("\nTesting object creation...")

try:
    state = GameState.initial()
    print("✓ GameState created")
except Exception as e:
    print(f"✗ Failed to create GameState: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    ai = ExpectimaxAgent(player=PLAYER_2, config=ExpectimaxConfig(depth=2))
    print("✓ AI agent created")
except Exception as e:
    print(f"✗ Failed to create AI agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed! Code compiles correctly.")
print("\nTo run the game, use:")
print("  python3 -m src.ui.graphical_human_vs_ai")
print("  or")
print("  python3 src/ui/graphical_human_vs_ai.py")

