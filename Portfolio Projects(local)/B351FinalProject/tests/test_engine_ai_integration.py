# tests/test_engine_ai_integration.py

from src.game.board import Board, PLAYER_1, PLAYER_2, player_index
from src.game.state import GameState
from src.game import rules
from src.game.game_loop import play_game
from src.ai.heuristics import evaluate_board, HeuristicAgent
from src.ai.expectimax import ExpectimaxAgent, ExpectimaxConfig


# ---------------------------------------------------------------------------
# Heuristic evaluation tests
# ---------------------------------------------------------------------------

def test_evaluate_board_returns_float():
    """evaluate_board should return a float without crashing."""
    board = Board.initial()
    score = evaluate_board(board, PLAYER_1)
    assert isinstance(score, float)


def test_evaluate_board_prefers_more_borne_off_for_player():
    """
    If we give PLAYER_1 more borne-off checkers (and change nothing else),
    the evaluation from PLAYER_1's perspective should increase.
    """
    board1 = Board.initial()
    board2 = board1.copy()

    idx_p1 = player_index(PLAYER_1)
    board2.borne_off[idx_p1] += 3  # pretend 3 more checkers are borne off

    s1 = evaluate_board(board1, PLAYER_1)
    s2 = evaluate_board(board2, PLAYER_1)

    assert s2 > s1


def test_evaluate_board_penalizes_own_bar_checkers():
    """
    If PLAYER_1 has more checkers on the bar, the evaluation from their
    perspective should decrease (since being on the bar is bad).
    """
    board1 = Board.initial()
    board2 = board1.copy()

    idx_p1 = player_index(PLAYER_1)
    board2.bar[idx_p1] += 2  # put 2 extra checkers on the bar

    s1 = evaluate_board(board1, PLAYER_1)
    s2 = evaluate_board(board2, PLAYER_1)

    assert s2 < s1


# ---------------------------------------------------------------------------
# Agent "choose_action" tests
# ---------------------------------------------------------------------------

def test_heuristic_agent_returns_legal_action():
    """
    HeuristicAgent.choose_action should either:
      - return None if there are no legal actions, or
      - return an Action that is in rules.legal_actions(state, dice).
    """
    state = GameState.initial()
    dice = (3, 4)
    agent = HeuristicAgent()

    action = agent.choose_action(state, dice)
    legal = rules.legal_actions(state, dice)

    assert action is None or action in legal


def test_expectimax_agent_returns_legal_action():
    """
    ExpectimaxAgent.choose_action should also only ever return legal actions.
    """
    state = GameState.initial()
    dice = (2, 5)
    agent = ExpectimaxAgent(player=PLAYER_1, config=ExpectimaxConfig(depth=1))

    action = agent.choose_action(state, dice)
    legal = rules.legal_actions(state, dice)

    assert action is None or action in legal


# ---------------------------------------------------------------------------
# Game loop integration tests
# ---------------------------------------------------------------------------

def test_play_game_heuristic_vs_heuristic_completes():
    """
    Running a game between two HeuristicAgents should complete within max_turns
    and produce a sensible winner (PLAYER_1, PLAYER_2, or None for draw).
    """
    p1 = HeuristicAgent()
    p2 = HeuristicAgent()

    result = play_game(p1, p2, max_turns=80, seed=0)

    assert result.turns_played <= 80
    assert result.winner in (None, PLAYER_1, PLAYER_2)


def test_play_game_expectimax_vs_heuristic_completes():
    """
    Running a game between Expectimax (P1) and Heuristic (P2) should also
    complete within max_turns without crashing.
    """
    p1 = ExpectimaxAgent(player=PLAYER_1, config=ExpectimaxConfig(depth=1))
    p2 = HeuristicAgent()

    result = play_game(p1, p2, max_turns=80, seed=0)

    assert result.turns_played <= 80
    assert result.winner in (None, PLAYER_1, PLAYER_2)

