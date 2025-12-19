def make_empty_numeric_board():
    """Helper: empty numeric Board (no checkers, no bar, no borne off)."""
    import numpy as np
    from src.game.board import Board

    points = np.zeros(24, dtype=int)
    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    return Board(points=points, bar=bar, borne_off=borne_off)


def test_evaluate_board_rewards_borne_off_and_penalizes_bar():
    """
    Heuristic evaluation should:
      - increase when we have more borne-off checkers
      - decrease when we have more checkers on the bar.
    """
    import copy
    from src.game.board import PLAYER_1, player_index
    from src.ai.heuristics import evaluate_board

    base_board = make_empty_numeric_board()

    # Baseline score (no checkers anywhere)
    base_score = evaluate_board(base_board, PLAYER_1)

    # Scenario 1: we have 3 borne-off checkers
    board_borne = copy.deepcopy(base_board)
    board_borne.borne_off[player_index(PLAYER_1)] = 3
    score_borne = evaluate_board(board_borne, PLAYER_1)

    # Scenario 2: we have 2 checkers on the bar
    board_bar = copy.deepcopy(base_board)
    board_bar.bar[player_index(PLAYER_1)] = 2
    score_bar = evaluate_board(board_bar, PLAYER_1)

    assert score_borne > base_score, "Borne-off checkers should increase the evaluation."
    assert score_bar < base_score, "Checkers on our bar should decrease the evaluation."


def test_heuristic_agent_returns_legal_action():
    """
    HeuristicAgent.choose_action should return an action that is in the
    rules.legal_actions list (or None if no moves are possible).
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import legal_actions
    from src.ai.heuristics import HeuristicAgent

    # Simple position: one checker on point 5, easy dice.
    points = np.zeros(24, dtype=int)
    points[5] = 1
    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    dice = (1, 2)
    legal = legal_actions(state, dice)

    agent = HeuristicAgent()
    action = agent.choose_action(state, dice)

    # If there are legal moves, the chosen action must be one of them.
    if legal:
        assert action in legal
    else:
        assert action is None


def test_expectimax_agent_returns_legal_action_depth1():
    """
    ExpectimaxAgent (depth=1) should run without crashing and return
    a legal action for a simple position.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import legal_actions
    from src.ai.expectimax import ExpectimaxAgent, ExpectimaxConfig

    # Simple position: one checker on point 5, easy dice.
    points = np.zeros(24, dtype=int)
    points[5] = 1
    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    dice = (1, 2)
    legal = legal_actions(state, dice)

    agent = ExpectimaxAgent(player=PLAYER_1, config=ExpectimaxConfig(depth=1))
    action = agent.choose_action(state, dice)

    if legal:
        assert action in legal
    else:
        assert action is None

