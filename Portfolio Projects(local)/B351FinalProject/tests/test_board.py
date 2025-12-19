import pytest

from src.game.board import Board
from src.game.moves import (
    Move,
    BAR,
    BEAR_OFF,
    legal_moves_for_die,
    generate_legal_moves,
    apply_move_in_place,
)


def make_empty_board():
    """
    Helper to construct a minimal, valid Board instance.

    Assumptions:
    - board.points: list of length 24, each entry either None or (player, count)
    - board.bar:     {"X": int, "O": int}
    - board.borne_off: {"X": int, "O": int}
    """
    points = [None] * 24
    bar = {"X": 0, "O": 0}
    borne_off = {"X": 0, "O": 0}
    return Board(points, bar, borne_off)


@pytest.fixture
def empty_board():
    """Returns a fresh, empty board with 24 points and no checkers."""
    return make_empty_board()


def test_board_has_24_points(empty_board):
    """Board should have exactly 24 points."""
    assert hasattr(empty_board, "points"), "Board should have a 'points' attribute"
    assert len(empty_board.points) == 24


def test_bar_and_borne_off_structure(empty_board):
    """Board should track bar and borne-off checkers for X and O."""
    # Bar
    assert hasattr(empty_board, "bar")
    assert isinstance(empty_board.bar, dict)
    assert set(empty_board.bar.keys()) == {"X", "O"}
    assert empty_board.bar["X"] == 0
    assert empty_board.bar["O"] == 0

    # Borne off
    assert hasattr(empty_board, "borne_off")
    assert isinstance(empty_board.borne_off, dict)
    assert set(empty_board.borne_off.keys()) == {"X", "O"}
    assert empty_board.borne_off["X"] == 0
    assert empty_board.borne_off["O"] == 0


def test_points_start_empty(empty_board):
    """Our helper should start all points as empty."""
    for p in empty_board.points:
        assert p is None


# ---------------------------------------------------------------------------
# Move logic tests (using moves.py)
# ---------------------------------------------------------------------------

def test_simple_forward_move_no_hit():
    """
    X has one checker on point 0, die=3.
    Expect a legal move 0 -> 3, no hit, and applying it moves the checker.
    """
    board = make_empty_board()
    board.points[0] = ("X", 1)

    moves = legal_moves_for_die(board, "X", 3)
    assert Move(from_point=0, to_point=3, hit=False) in moves

    # Apply the move and verify board state
    move = Move(0, 3, False)
    apply_move_in_place(board, "X", move)

    assert board.points[0] is None
    assert board.points[3] == ("X", 1)
    assert board.bar["X"] == 0
    assert board.borne_off["X"] == 0


def test_hit_sends_opponent_to_bar():
    """
    X moves onto a point with exactly one O checker -> hit.
    That O checker should go to the bar.
    """
    board = make_empty_board()
    board.points[0] = ("X", 1)
    board.points[3] = ("O", 1)  # blot

    moves = legal_moves_for_die(board, "X", 3)
    assert Move(from_point=0, to_point=3, hit=True) in moves

    move = Move(0, 3, True)
    apply_move_in_place(board, "X", move)

    # Origin now empty
    assert board.points[0] is None
    # Destination now has X
    assert board.points[3] == ("X", 1)
    # O got sent to the bar
    assert board.bar["O"] == 1


def test_enter_from_bar():
    """
    X has a checker on the bar and rolls a die that allows entry.
    For die=3, X should enter on point index 2 (0-based).
    """
    board = make_empty_board()
    board.bar["X"] = 1

    moves = legal_moves_for_die(board, "X", 3)
    assert Move(from_point=BAR, to_point=2, hit=False) in moves

    move = Move(BAR, 2, False)
    apply_move_in_place(board, "X", move)

    assert board.bar["X"] == 0
    assert board.points[2] == ("X", 1)


def test_bear_off_when_all_in_home():
    """
    X has a checker in the home board and all X checkers are in home.
    A large die should allow bearing off from that point.
    """
    board = make_empty_board()

    # Put one X checker at point 18 (start of X home board: 18..23)
    board.points[18] = ("X", 1)

    # No other X checkers anywhere, no bar checkers => all X are in home
    moves = legal_moves_for_die(board, "X", 6)

    # Expect a bear-off move from 18 to BEAR_OFF
    assert Move(from_point=18, to_point=BEAR_OFF, hit=False) in moves

    move = Move(18, BEAR_OFF, False)
    apply_move_in_place(board, "X", move)

    assert board.points[18] is None
    assert board.borne_off["X"] == 1


def test_generate_legal_moves_aggregates_dice():
    """
    generate_legal_moves should combine moves from multiple dice.
    Here, X has one checker on 0; dice [1, 2] should allow moves to 1 and 2.
    """
    board = make_empty_board()
    board.points[0] = ("X", 1)

    moves = generate_legal_moves(board, "X", [1, 2])
    assert Move(0, 1, False) in moves
    assert Move(0, 2, False) in moves

