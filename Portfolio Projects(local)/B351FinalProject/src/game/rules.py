# src/backgammon/game/rules.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .board import Board, Player, PLAYER_1, PLAYER_2, N_POINTS, player_index
from .state import GameState
from .dice import expand_dice


def other_player(player: Player) -> Player:
    """Return the opponent of `player`."""
    return PLAYER_1 if player == PLAYER_2 else PLAYER_2


@dataclass(frozen=True)
class Step:
    """A single checker move.

    from_point and to_point are 0-based indices into Board.points, or None.
      - from_point = None means from the bar.
      - to_point   = None means bearing off.
    hit_index is the index of a hit checker (0-23) or None if no hit.
    """
    from_point: Optional[int]
    to_point: Optional[int]
    hit_index: Optional[int] = None


@dataclass(frozen=True)
class Action:
    """A full turn: a sequence of Steps using some or all dice pips."""
    steps: Tuple[Step, ...]


# ----- Helper functions for geometry / direction -----


def direction_for(player: Player) -> int:
    """Return +1 or -1 step direction on the points array for the given player.

    Convention:
      - PLAYER_1 moves from higher indices to lower (23 -> 0): direction = -1
      - PLAYER_2 moves from lower indices to higher (0 -> 23): direction = +1
    """
    return -1 if player == PLAYER_1 else 1


def home_board_range(player: Player) -> range:
    """Return range of indices representing the player's home board.

    Using the convention above:
      - PLAYER_1 home board = points 1..6 -> indices 0..5
      - PLAYER_2 home board = points 19..24 -> indices 18..23
    """
    if player == PLAYER_1:
        return range(0, 6)
    else:
        return range(18, 24)


def entry_point_from_bar(player: Player, die: int) -> int:
    """Return index of entry point from bar for given player and die.

    From standard backgammon rules:
      - PLAYER_1 enters in PLAYER_2's home board: points 24..19
      - PLAYER_2 enters in PLAYER_1's home board: points 1..6
    """
    if player == PLAYER_1:
        # points 24..19 -> indices 23..18
        return 24 - die  # 24-die gives indices 23..18
    else:
        # points 1..6 -> indices 0..5
        return die - 1


def all_in_home(board: Board, player: Player) -> bool:
    """Return True if all of player's checkers are in their home board or borne off."""
    home = set(home_board_range(player))
    total = board.total_checkers_for(player)
    # Count borne-off checkers
    borne_off = int(board.borne_off[player_index(player)])
    if borne_off == total:
        return True

    # Count on-board checkers in home
    in_home = 0
    for idx in range(N_POINTS):
        if board.owner_of_point(idx) == player and idx in home:
            in_home += board.count_on_point(idx)

    return in_home + borne_off == total


# ----- Move generation helpers -----


def single_die_moves(state: GameState, die: int) -> List[Step]:
    """Generate all legal single-step moves for the current player using one die.

    This handles:
      - entering from bar (must move from bar if any checkers there)
      - normal moves
      - simple hitting of blots (single opposing checker)
      - simplified bearing off if all checkers are in home board

    It does NOT attempt to enforce "must use maximum number of dice" rules.
    That logic (for multi-step turns) can be layered on top of these steps.
    """
    board = state.board
    player = state.current_player
    dir_ = direction_for(player)

    moves: List[Step] = []

    # If there are checkers on the bar, they must be moved first.
    if board.bar[player_index(player)] > 0:
        dest = entry_point_from_bar(player, die)
        owner = board.owner_of_point(dest)
        count = board.count_on_point(dest)
        if owner == 0 or owner == player or (owner != player and count == 1):
            # legal: empty, own point, or blot (hit)
            hit_idx = dest if (owner != 0 and owner != player and count == 1) else None
            moves.append(Step(from_point=None, to_point=dest, hit_index=hit_idx))
        return moves

    # Otherwise, move any checker on the board.
    home = home_board_range(player)
    for idx in range(N_POINTS):
        if board.owner_of_point(idx) != player:
            continue
        target = idx + dir_ * die

        # Bearing off
        if target < 0 or target >= N_POINTS:
            # simplified bearing off: only allow if all checkers are in home
            if idx in home and all_in_home(board, player):
                moves.append(Step(from_point=idx, to_point=None, hit_index=None))
            continue

        owner = board.owner_of_point(target)
        count = board.count_on_point(target)

        # Blocked if 2+ opposing checkers
        if owner != 0 and owner != player and count > 1:
            continue

        hit_idx = target if (owner != 0 and owner != player and count == 1) else None
        moves.append(Step(from_point=idx, to_point=target, hit_index=hit_idx))

    return moves


def legal_actions(state: GameState, dice: Tuple[int, int]) -> List[Action]:
    """Generate (simplified) legal actions for the current player given dice.

    For now, each Action is just a single Step for one die, or a
    two-step sequence applying the dice in one order then the other
    if both steps are individually legal.

    This is a simplification of full backgammon move rules, but it
    provides a clean interface for agents and is enough to start
    playing valid games and building an AI on top.
    """
    d1, d2 = dice
    # Single-step actions
    steps_d1 = single_die_moves(state, d1)
    steps_d2 = single_die_moves(state, d2)

    actions: List[Action] = [Action(steps=(s,)) for s in steps_d1 + steps_d2]

    # Try composing two-step actions in both orders
    # Note: this is simplified and does not enforce maximum pip usage.
    for first_die, second_die, first_steps in [(d1, d2, steps_d1), (d2, d1, steps_d2)]:
        for step1 in first_steps:
            # Apply first step to a copy of the state
            tmp_state = apply_step(state, step1)
            second_steps = single_die_moves(tmp_state, second_die)
            for step2 in second_steps:
                actions.append(Action(steps=(step1, step2)))

    # Remove duplicates by using dataclass equality / hashing
    unique_actions = list({a: None for a in actions}.keys())
    return unique_actions

def _generate_action_candidates(
    state: GameState,
    remaining_dice: list[int],
) -> list[tuple[tuple[Step, ...], tuple[int, ...]]]:
    """
    Recursively generate all possible action sequences for the given list of dice.

    Each returned element is:
        (steps_tuple, dice_used_tuple)

    We do NOT enforce "max dice" or "higher die" rules here; we just
    enumerate everything and let legal_actions filter afterward.
    """
    candidates: list[tuple[tuple[Step, ...], tuple[int, ...]]] = []

    def _recurse(
        current_state: GameState,
        available: list[int],
        steps_so_far: list[Step],
        dice_used: list[int],
    ) -> None:
        any_move = False

        # Try using each remaining die once
        for i, die in enumerate(available):
            moves = single_die_moves(current_state, die)
            if not moves:
                continue

            any_move = True

            for step in moves:
                next_state = apply_step(current_state, step)
                next_available = available[:i] + available[i + 1 :]
                _recurse(
                    next_state,
                    next_available,
                    steps_so_far + [step],
                    dice_used + [die],
                )

        # If we couldn't move with any remaining die, record this sequence
        if not any_move:
            candidates.append((tuple(steps_so_far), tuple(dice_used)))

    _recurse(state, remaining_dice, [], [])
    return candidates


def legal_actions(state: GameState, dice: Tuple[int, int]) -> List[Action]:
    """
    Generate legal actions for the current player, respecting:

      - Doubles: up to 4 uses of the die (or fewer if blocked).
      - Non-doubles: up to 2 uses of the dice.
      - "Use as many dice as possible" rule.
      - If only one die can be used in a non-double roll, prefer the higher die.

    Each Action is a sequence of Steps applied in order.
    """
    d1, d2 = dice

    # Expand dice into a multiset of pips.
    # NOTE: We don't rely on expand_dice() here to avoid signature confusion.
    if d1 == d2:
        # Doubles: up to 4 uses
        remaining_dice = [d1, d1, d1, d1]
    else:
        remaining_dice = [d1, d2]

    # Enumerate all sequences we can play with these dice
    raw_candidates = _generate_action_candidates(state, remaining_dice)

    if not raw_candidates:
        return []

    # If *all* sequences are empty (no steps), there are no legal actions.
    max_len = max(len(steps) for steps, _used in raw_candidates)
    if max_len == 0:
        return []

    # Enforce "use as many dice as possible": keep only sequences with max_len steps.
    best_sequences = [
        (steps, used) for (steps, used) in raw_candidates if len(steps) == max_len
    ]

    # If we only used one die in a non-double roll, and multiple 1-step
    # sequences exist, prefer those that use the higher die if possible.
    if max_len == 1 and d1 != d2:
        high = max(d1, d2)
        with_high = [
            (steps, used) for (steps, used) in best_sequences if high in used
        ]
        if with_high:
            best_sequences = with_high

    # Convert to Action objects and deduplicate
    unique_actions: dict[Action, None] = {}
    for steps, _used in best_sequences:
        action = Action(steps=steps)
        unique_actions[action] = None

    return list(unique_actions.keys())


# ----- Applying moves -----


def apply_step(state: GameState, step: Step) -> GameState:
    """Return a new GameState with a single Step applied for the current player.

    This function:
      - moves or bears off a checker for the current player
      - handles hitting (if hit_index is set)
      - does not switch turns or modify dice/turn_number
    """
    new_state = state.copy(copy_history=False)
    board = new_state.board
    player = new_state.current_player

    # Handle hit first: send victim checker to bar.
    if step.hit_index is not None:
        victim = PLAYER_1 if player == PLAYER_2 else PLAYER_2
        board.hit_checker_at(victim_player=victim, index=step.hit_index)

    # Move the checker itself
    board.move_checker(player=player, from_idx=step.from_point, to_idx=step.to_point)

    return new_state


def apply_action(state: GameState, action: Action) -> GameState:
    """Apply a full Action (sequence of Steps) to a GameState.

    Returns a new GameState. Does NOT change current_player or turn_number;
    the caller (e.g., game loop) should call state.next_turn() when done.
    """
    new_state = state
    for step in action.steps:
        new_state = apply_step(new_state, step)
    return new_state

