# Backgammon AI Project

A Python implementation of Backgammon with multiple AI agents and a graphical user interface built with Pygame.

## Features

- **Graphical UI**: Beautiful, interactive backgammon board with click-and-play mechanics
- **Multiple AI Agents**: Play against Random, Heuristic, or Expectimax AI opponents
- **Realistic Graphics**: 3D-styled checkers and authentic backgammon board appearance
- **Full Game Rules**: Complete implementation of backgammon rules including bearing off, hitting, and bar entry

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

The required packages are:
- `pygame>=2.5.0` - For the graphical user interface
- `numpy>=1.24.0` - For board state management

## Usage

### Graphical UI - Human vs AI

Play against an AI opponent with a visual interface:

```bash
# Play against Heuristic AI (default)
python3 src/ui/graphical_human_vs_ai.py

# Play against Random AI
python3 src/ui/graphical_human_vs_ai.py --ai random

# Play against Expectimax AI with depth 1 (default, fast)
python3 src/ui/graphical_human_vs_ai.py --ai expectimax --depth 1

# Play against Expectimax AI with depth 2 (smarter but VERY slow - 60+ seconds per move)
python3 src/ui/graphical_human_vs_ai.py --ai expectimax --depth 2

# Play as Player 2 instead of Player 1
python3 src/ui/graphical_human_vs_ai.py --human-player 2
```

**Command-line options:**
- `--ai {random,heuristic,expectimax}` - Choose AI opponent type (default: heuristic)
- `--depth N` - Set search depth for Expectimax AI (default: 1). **Warning:** Depth 2 takes 60+ seconds per move, depth 3+ is impractical
- `--human-player {1,2}` - Choose which player you want to be (default: 1)

### Graphical UI - Human vs Human

Play a local two-player game:

```bash
python3 src/ui/graphical_main.py
```


### Testing AI Agents

Compare different AI agents:

```bash
python3 src/main.py
```

## How to Play (Graphical UI)

1. **Start the game**: Run one of the graphical UI scripts
2. **Roll dice**: Click the "Roll Dice" button in the center of the board
3. **Select a checker**: Click on one of your checkers (white for Player 1, dark for Player 2)
4. **Make a move**: Click on a highlighted green point to move your checker there
5. **Bearing off**: When all your checkers are in your home board, you can click the bearing-off area to remove checkers
6. **Bar entry**: If you have checkers on the bar, click the bar area first, then select an entry point

The game will automatically:
- Highlight valid move destinations in green
- Show which player's turn it is
- Display dice rolls
- Advance turns when moves are complete

## AI Agents

### Random AI
- Makes random legal moves
- Easiest opponent
- Good for testing and learning

### Heuristic AI
- Uses position-based evaluation
- Considers checker positions, safety, and progress
- Moderate difficulty
- Fast decision-making

### Expectimax AI
- Uses expectimax search algorithm
- Looks ahead multiple moves
- Configurable search depth
- Strongest opponent, but **very slow** at higher depths
- **Performance warning:** Depth 1 is fast (~1 second), depth 2 takes 60+ seconds per move, depth 3+ is impractical

## Project Structure

```
B351FinalProject/
├── src/
│   ├── ai/              # AI agent implementations
│   │   ├── heuristics.py      # Heuristic evaluation and agent
│   │   ├── expectimax.py      # Expectimax search agent
│   │   └── human_agent.py     # Terminal-based human player
│   ├── game/            # Core game logic
│   │   ├── board.py          # Board representation
│   │   ├── state.py          # Game state management
│   │   ├── rules.py          # Move generation and validation
│   │   ├── dice.py           # Dice rolling
│   │   └── game_loop.py      # Main game loop
│   └── ui/              # User interfaces
│       ├── graphical.py           # Base graphical UI
│       ├── graphical_main.py      # Human vs Human UI
│       └── graphical_human_vs_ai.py  # Human vs AI UI
├── docs/                # Documentation
├── tests/               # Unit tests
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Development

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 tests/test_board.py
```

### Code Structure

- **Board representation**: Uses NumPy arrays for efficient state management
- **Move generation**: Complete implementation of backgammon rules
- **AI evaluation**: Position-based heuristics with configurable weights
- **UI rendering**: Pygame-based with sprite rendering for checkers

## Acknowledgments

This project uses the following libraries and tools:

### Third-Party Libraries

- **[Pygame](https://www.pygame.org/)** (>=2.5.0) - Cross-platform set of Python modules for creating video games and multimedia applications. Used for the graphical user interface, rendering the backgammon board, checkers, and handling user input.

- **[NumPy](https://numpy.org/)** (>=1.24.0) - Fundamental package for scientific computing in Python. Used for efficient board state representation and array operations.

- **[Pandas](https://pandas.pydata.org/)** - Data analysis and manipulation library. Used in `run_matchups.py` for collecting and analyzing game statistics.

- **[Pytest](https://pytest.org/)** - Testing framework for Python. Used for running unit tests.

### Python Standard Library

The project also uses the following Python standard library modules:
- `sys` - System-specific parameters and functions
- `os` - Operating system interface
- `pathlib` - Object-oriented filesystem paths
- `argparse` - Command-line argument parsing
- `random` - Generate pseudo-random numbers
- `dataclasses` - Decorator for creating data classes
- `typing` - Type hints support
- `json` - JSON encoder and decoder (for debugging)
- `time` - Time-related functions (for debugging)
- `traceback` - Print or retrieve stack traces (for error handling)

### Special Thanks

- The backgammon rules implementation follows standard backgammon rules
- AI algorithms inspired by classic game AI techniques (expectimax, heuristic evaluation)

