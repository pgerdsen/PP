"""
Move generation and application for Backgammon.

Conventions used here (adjust if your board is different):

- There are 24 points indexed 0..23.
- Each Board point is either:
    None                         # empty
    (player: str, count: int)    # e.g. ("X", 2) or ("O", 3)

- Players are represented by "X" and "O".
- board.bar[player] is an int: number of checkers on the bar.
- board.borne_off[player] is an int: number of borne-off checkers.

- Movement directions:
    "X" moves from low indices to high indices (0 -> 23).
    "O" moves from high indices to low indices (23 -> 0).

- Home boards (for bearing off):
    "X" home: points 18..23   (last 6 points)
    "O" home: points 0..5     (first 6 points)

We also use sentinel indices:
    BAR = -1          (origin index when moving from the bar)
    BEAR_OFF = 24     (destination index when bearing off)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple, Optional

from .board import Board

# Sentinel indices
BAR = -1
BEAR_OFF = 24


@dataclass(frozen=True)
class Move:
    """
    Represents a single checker move.

    from_point:
        - 0..23 for points on the board
        - BAR (-1) if moving a checker from the bar

    to_point:
        - 0..23 for points on the board
        - BEAR_OFF (24) if bearing off a checker

    hit:
        True if this move hits an opposing blot (a point with exactly 1 opponent checker).
    """
    from_point: int
    to_point: int
    hit: bool = False


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _opponent(player: str) -> str:
    return "O" if player == "X" else "X"


def _direction(player: str) -> int:
    """Movement direction along indices for the given player."""
    return 1 if player == "X" else -1


def _get_stack(board: Board, idx: int) -> Tuple[Optional[str], int]:
    """
    Returns (owner, count) for a board point.

    owner is "X" / "O" or None if empty.
    """
    value = board.points[idx]
    if value is None:
        return None, 0
    owner, count = value
    return owner, count


def _set_stack(board: Board, idx: int, owner: Optional[str], count: int) -> None:
    """
    Sets a board point to (owner, count) or None if count == 0 or owner is None.
    """
    if owner is None or count <= 0:
        board.points[idx] = None
    else:
        board.points[idx] = (owner, count)


def _in_home_board(idx: int, player: str) -> bool:
    """Return True if a point index is in the player's home board."""
    if player == "X":
        return 18 <= idx <= 23
    else:  # "O"
        return 0 <= idx <= 5


def _all_checkers_in_home(board: Board, player: str) -> bool:
    """
    Returns True if all of player's checkers not on the bar are in the home board.
    Assumes 15 checkers total per player.
    """
    total_on_board = 0

    for i in range(24):
        owner, count = _get_stack(board, i)
        if owner == player:
            if not _in_home_board(i, player):
                return False
            total_on_board += count

    # If any are on the bar, not all are in home.
    if board.bar[player] > 0:
        return False

    # If you want to be strict, you can also check borne_off + board == 15,
    # but it's not required for legality of bearing off.
    return True


# ---------------------------------------------------------------------------
# Move generation
# ---------------------------------------------------------------------------

def legal_moves_for_die(board: Board, player: str, die: int) -> List[Move]:
    """
    Generate all single-checker legal moves for a single die value
    without mutating the board.

    This handles:
    - Entering from the bar (if bar[player] > 0)
    - Normal moves on the board
    - Hits (moving onto a point with exactly 1 opponent checker)
    - Bearing off from the home board if allowed

    It does NOT combine multiple dice into sequences; that can be
    handled by GameState using this function repeatedly.
    """
    moves: List[Move] = []
    direction = _direction(player)
    opponent = _opponent(player)

    # -----------------------------------------------------------------------
    # 1. If the player has any checkers on the bar, they MUST enter from bar.
    # -----------------------------------------------------------------------
    if board.bar[player] > 0:
        if player == "X":
            dest = die - 1          # enter on points 0..5
        else:  # "O"
            dest = 24 - die         # enter on points 23..18

        # Check the destination point legality
        owner, count = _get_stack(board, dest)
        if owner is None or owner == player:
            # empty or own point
            moves.append(Move(BAR, dest, hit=False))
        elif owner == opponent and count == 1:
            # hit a blot
            moves.append(Move(BAR, dest, hit=True))
        # If opponent has 2+ checkers there, it's blocked; no move.
        return moves

    # -----------------------------------------------------------------------
    # 2. Otherwise, generate moves from all points with player's checkers.
    # -----------------------------------------------------------------------
    for idx in range(24):
        owner, count = _get_stack(board, idx)
        if owner != player or count == 0:
            continue

        dest = idx + direction * die

        # --- Case A: Bearing off or overshoot from home board ---
        if dest < 0 or dest > 23:
            # We only allow bearing off if all checkers are in the home board.
            if not _all_checkers_in_home(board, player):
                continue

            # Standard simplification:
            # - If die exactly matches distance to bear-off, allow.
            # - If no checker is behind this point in the home board, also allow.
            if _in_home_board(idx, player):
                # You can be more precise here, but this is a reasonable rule.
                moves.append(Move(idx, BEAR_OFF, hit=False))
            continue

        # --- Case B: Moving within the board (dest in 0..23) ---
        dest_owner, dest_count = _get_stack(board, dest)
        if dest_owner is None or dest_owner == player:
            # Empty or own stack
            moves.append(Move(idx, dest, hit=False))
        elif dest_owner == opponent and dest_count == 1:
            # Hit a blot
            moves.append(Move(idx, dest, hit=True))
        # If opponent has 2+ checkers, blocked. No move.

    return moves


def generate_legal_moves(board: Board, player: str, dice: Sequence[int]) -> List[Move]:
    """
    Convenience helper: generate all single-step moves available for
    any die in `dice`.

    This does NOT attempt to build full multi-move turn sequences,
    but is enough to:
      - show what moves are possible
      - let GameState loop over dice and apply moves one at a time
    """
    all_moves: List[Move] = []
    for d in dice:
        all_moves.extend(legal_moves_for_die(board, player, d))
    return all_moves


# ---------------------------------------------------------------------------
# Move application
# ---------------------------------------------------------------------------

def apply_move_in_place(board: Board, player: str, move: Move) -> None:
    """
    Applies a single Move to the board in-place.

    Handles:
    - Moving from a point on the board
    - Moving from the bar
    - Hitting an opponent checker (sending it to bar)
    - Bearing off

    Does NOT validate the move – you should call legal_moves_for_die
    or otherwise ensure the move is legal before applying.
    """
    opponent = _opponent(player)

    # 1. Remove checker from origin
    if move.from_point == BAR:
        # from bar
        if board.bar[player] <= 0:
            raise ValueError(f"No checkers for player {player} on bar to move.")
        board.bar[player] -= 1
    else:
        # from a normal point
        owner, count = _get_stack(board, move.from_point)
        if owner != player or count <= 0:
            raise ValueError(f"Cannot move from point {move.from_point}: not owned by {player}.")
        _set_stack(board, move.from_point, player, count - 1)

    # 2. Handle bearing off
    if move.to_point == BEAR_OFF:
        board.borne_off[player] += 1
        return

    # 3. Handle destination on the board
    dest_owner, dest_count = _get_stack(board, move.to_point)

    # If we are hitting, there should be exactly 1 opponent checker there
    if move.hit:
        if dest_owner != opponent or dest_count != 1:
            raise ValueError("Move marked as hit, but destination is not a single opponent checker.")
        # Send opponent checker to bar
        board.bar[opponent] += 1
        # Now destination is effectively empty for our checker
        dest_owner, dest_count = None, 0

    # Place our checker on destination
    if dest_owner is None:
        _set_stack(board, move.to_point, player, 1)
    elif dest_owner == player:
        _set_stack(board, move.to_point, player, dest_count + 1)
    else:
        # Should not occur if move legality is enforced
        raise ValueError("Trying to stack on opponent's point with 2+ checkers (blocked square).")

