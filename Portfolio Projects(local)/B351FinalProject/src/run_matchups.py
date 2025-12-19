"""
run_matchups.py

Run many games of Expectimax vs Heuristic and collect basic stats
(using pandas), so you can drop numbers/plots into your report.

Usage (from repo root):
    python3 -m src.run_matchups
or:
    python3 src/run_matchups.py

Requires:
    pip install pandas
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Optional, List

import pandas as pd

from src.game.board import PLAYER_1, PLAYER_2, Player
from src.game.game_loop import play_game
from src.ai.expectimax import ExpectimaxAgent, ExpectimaxConfig
from src.ai.heuristics import HeuristicAgent


@dataclass
class MatchConfig:
    n_games: int = 50
    depth: int = 1
    max_turns: int = 300
    seed_base: int = 0


@dataclass
class MatchResult:
    game_index: int
    seed: int
    winner: Optional[Player]  # 1 (P1), -1 (P2), or None
    turns_played: int

    # For convenience, store labels
    winner_label: str
    p1_agent: str
    p2_agent: str


def winner_to_label(w: Optional[Player]) -> str:
    if w == PLAYER_1:
        return "P1_expectimax"
    elif w == PLAYER_2:
        return "P2_heuristic"
    else:
        return "none_or_draw"


def run_expectimax_vs_heuristic(config: MatchConfig) -> pd.DataFrame:
    """
    Run n_games of:
        P1 = Expectimax(depth=config.depth)
        P2 = HeuristicAgent()

    Returns a pandas DataFrame with one row per game.
    """
    rows: List[MatchResult] = []

    for i in range(config.n_games):
        seed = config.seed_base + i

        p1 = ExpectimaxAgent(player=PLAYER_1, config=ExpectimaxConfig(depth=config.depth))
        p2 = HeuristicAgent()

        result = play_game(
            p1,
            p2,
            max_turns=config.max_turns,
            seed=seed,
        )

        label = winner_to_label(result.winner)

        rows.append(
            MatchResult(
                game_index=i,
                seed=seed,
                winner=result.winner,
                turns_played=result.turns_played,
                winner_label=label,
                p1_agent=f"Expectimax(d={config.depth})",
                p2_agent="Heuristic",
            )
        )

    # Convert dataclass list -> DataFrame
    df = pd.DataFrame([r.__dict__ for r in rows])
    return df


def summarize_results(df: pd.DataFrame) -> None:
    """
    Print a small text summary of the matchup results.
    """
    n_games = len(df)
    win_counts = df["winner_label"].value_counts()

    p1_wins = int(win_counts.get("P1_expectimax", 0))
    p2_wins = int(win_counts.get("P2_heuristic", 0))
    draws = int(win_counts.get("none_or_draw", 0))

    print("=== Expectimax (P1) vs Heuristic (P2) summary ===")
    print(f"Total games: {n_games}")
    print(f"Expectimax wins (P1): {p1_wins} ({p1_wins / n_games:.1%})")
    print(f"Heuristic wins (P2): {p2_wins} ({p2_wins / n_games:.1%})")
    print(f"No winner / max_turns reached: {draws} ({draws / n_games:.1%})")

    print()
    print("Average turns per game:", df["turns_played"].mean())
    print("Median turns per game:", df["turns_played"].median())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Expectimax vs Heuristic matchups and collect stats."
    )
    parser.add_argument("--games", type=int, default=50,
                        help="Number of games to run (default: 50).")
    parser.add_argument("--depth", type=int, default=1,
                        help="Expectimax search depth (default: 1).")
    parser.add_argument("--max-turns", type=int, default=300,
                        help="Max turns per game before stopping (default: 300).")
    parser.add_argument("--seed-base", type=int, default=0,
                        help="Base seed; each game uses seed_base + i (default: 0).")
    parser.add_argument("--output", type=str, default="data/experiments/expectimax_vs_heuristic.csv",
                        help="Path to CSV output (default: data/experiments/expectimax_vs_heuristic.csv).")

    args = parser.parse_args()

    cfg = MatchConfig(
        n_games=args.games,
        depth=args.depth,
        max_turns=args.max_turns,
        seed_base=args.seed_base,
    )

    print("Running Expectimax vs Heuristic matchups with config:")
    print(f"  games     = {cfg.n_games}")
    print(f"  depth     = {cfg.depth}")
    print(f"  max_turns = {cfg.max_turns}")
    print(f"  seed_base = {cfg.seed_base}")
    print()

    df = run_expectimax_vs_heuristic(cfg)
    summarize_results(df)

    # Save CSV
    out_path = args.output
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print()
    print(f"Saved detailed results to: {out_path}")


if __name__ == "__main__":
    main()

