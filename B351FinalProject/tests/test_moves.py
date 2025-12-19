def test_higher_die_is_preferred_when_only_one_die_can_be_played():
    """
    For non-doubles (2,3) in this position, only one die can be used.
    Rules say: use the higher die -> we should see the 3-pip move 9->6, not 9->7.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import legal_actions

    # Board configuration:
    # index:  0  1  2  3  4   5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
    # value:  1  1  0  0  -2  0  0  0  0  1  0  0  0  0  0  0  0 -1  0  0  0  0  0  0
    #
    # +1 = PLAYER_1, -1 = PLAYER_2
    points = np.array(
        [ 1, 1, 0, 0, -2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0 ],
        dtype=int,
    )
    bar = np.array([0, 0], dtype=int)
    borne_off = np.array([0, 0], dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)

    state = GameState(board=board, current_player=PLAYER_1)

    actions = legal_actions(state, (2, 3))

    # There should be exactly one legal action in this scenario
    assert len(actions) == 1, f"Expected exactly one legal action for dice (2,3), got {len(actions)}"

    action = actions[0]
    assert len(action.steps) == 1, f"Expected a single-step action, got {len(action.steps)} steps."

    step = action.steps[0]

    # We specifically expect the 3-pip move 9->6 (higher die), not the 2-pip move 9->7.
    assert step.from_point == 9, f"Expected move to start from point 9, got {step.from_point}"
    assert step.to_point == 6, f"Expected higher-die move 9->6 (using 3), got {step.to_point}"

def test_double_six_uses_three_moves_when_fourth_blocked():
    """For a 6-6 roll, only 3 moves should be used if the 4th is blocked."""
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import legal_actions

    # Board configuration found by search:
    # index:  0  1  2  3  4  5   6  7  8  9 10 11  12 13 14 15 16 17 18 19 20 21 22 23
    points = np.array(
        [ 0, 1, 1, 0, 1, 0, -1, 0, 0, 0, 0, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
        dtype=int,
    )
    bar = np.array([0, 0], dtype=int)
    borne_off = np.array([0, 0], dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)

    state = GameState(board=board, current_player=PLAYER_1)

    actions = legal_actions(state, (6, 6))

    # We should have at least one legal action
    assert actions, "Expected at least one legal action for 6-6 in this position."

    # All actions should use exactly 3 steps (3 dice), never 4.
    lengths = {len(a.steps) for a in actions}
    assert lengths == {3}, f"Expected all actions to use exactly 3 dice for 6-6, got lengths={lengths}"

def test_must_enter_from_bar_when_checker_on_bar():
    """
    If the current player has checkers on the bar, all single-die moves
    must originate from the bar (from_point=None).
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1, player_index
    from src.game.state import GameState
    from src.game.rules import single_die_moves

    # Empty board, one P1 checker on the bar.
    points = np.zeros(24, dtype=int)
    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)

    bar[player_index(PLAYER_1)] = 1
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    moves = single_die_moves(state, die=3)

    # There should be at least one legal move
    assert moves, "Expected at least one legal move when entering from bar."

    # Every move must come from the bar
    assert all(m.from_point is None for m in moves), (
        "All moves should originate from the bar when a checker is on the bar."
    )

def test_cannot_land_on_blocked_point_two_or_more_opponents():
    """
    A point with two or more opposing checkers is blocked and cannot be entered.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import single_die_moves

    points = np.zeros(24, dtype=int)
    # P1 checker at index 10
    points[10] = 1
    # P2 has two checkers at index 8 (blocked)
    points[8] = -2

    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    moves = single_die_moves(state, die=2)  # 10 -> 8 would be natural, but blocked

    # No move should land on index 8
    assert all(m.to_point != 8 for m in moves), "Should not be able to move onto a blocked point with 2+ enemy checkers."

def test_hit_sends_victim_to_bar_via_rules_apply_step():
    """
    Moving onto a point with exactly one enemy checker should hit it and send to the bar,
    without changing the total number of checkers for either player.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1, PLAYER_2, player_index
    from src.game.state import GameState
    from src.game.rules import single_die_moves, apply_step

    points = np.zeros(24, dtype=int)
    # P1 checker at index 10
    points[10] = 1
    # Single P2 checker (blot) at index 8
    points[8] = -1

    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    # Record totals before the hit
    before_p1 = board.total_checkers_for(PLAYER_1)
    before_p2 = board.total_checkers_for(PLAYER_2)

    moves = single_die_moves(state, die=2)  # 10 -> 8, should be a hit
    hitting_moves = [m for m in moves if m.from_point == 10 and m.to_point == 8]

    assert hitting_moves, "Expected a hitting move 10->8 with die=2."
    step = hitting_moves[0]

    # Sanity check: this should be marked as a hit
    assert step.hit_index == 8

    # Apply the step and check the board
    new_state = apply_step(state, step)
    new_board = new_state.board

    # 8 should now belong to P1
    assert new_board.owner_of_point(8) == PLAYER_1
    # P2 should have 1 checker on the bar
    assert new_board.bar[player_index(PLAYER_2)] == 1

    # Total checkers for each player should be preserved
    assert new_board.total_checkers_for(PLAYER_1) == before_p1
    assert new_board.total_checkers_for(PLAYER_2) == before_p2


def test_bearing_off_allowed_when_all_checkers_in_home():
    """
    If all of a player's checkers are in the home board (and none on bar),
    overshooting from home should allow bearing off (to_point=None).
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1, player_index
    from src.game.state import GameState
    from src.game.rules import single_die_moves

    points = np.zeros(24, dtype=int)
    # Put 3 P1 checkers inside home (indices 0..5); one of them on index 2
    points[2] = 3
    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)

    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    moves = single_die_moves(state, die=4)  # From 2 with die=4 overshoots (2 - 4 < 0)

    bearing_off_steps = [m for m in moves if m.from_point == 2 and m.to_point is None]
    assert bearing_off_steps, "Expected at least one bearing-off move from home when all checkers are in home board."
    # Sanity: bar must be 0 for P1
    assert board.bar[player_index(PLAYER_1)] == 0

def test_bearing_off_disallowed_when_checker_outside_home():
    """
    If any checker is outside the home board, bearing off should NOT be allowed.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import single_die_moves

    points = np.zeros(24, dtype=int)
    # One checker in home at index 2
    points[2] = 1
    # One checker outside home at index 10
    points[10] = 1

    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    moves = single_die_moves(state, die=4)  # 2->off would overshoot, but all_in_home is False

    # There should be at least one move (from index 10 -> 6)
    assert moves, "Expected at least one legal move even with checker outside home."

    # But NO bearing-off move should be present
    assert all(m.to_point is not None for m in moves), "Should not allow bearing off when not all checkers are in home board."

def test_legal_actions_builds_two_step_actions_for_two_dice():
    """
    With a single checker and two non-blocked dice, legal_actions should
    include at least one two-step action using both dice.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import legal_actions, apply_action

    points = np.zeros(24, dtype=int)
    # One P1 checker at index 5
    points[5] = 1

    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    dice = (1, 2)
    actions = legal_actions(state, dice)

    assert actions, "Expected at least one legal action for dice (1,2)."

    two_step_actions = [a for a in actions if len(a.steps) == 2]
    assert two_step_actions, "Expected at least one two-step action using both dice."

    # Pick one two-step action and ensure total checkers are preserved
    action = two_step_actions[0]
def test_legal_actions_builds_two_step_actions_for_two_dice():
    """
    With a single checker and two non-blocked dice, legal_actions should
    include at least one two-step action using both dice, and applying it
    should preserve the total number of checkers.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1
    from src.game.state import GameState
    from src.game.rules import legal_actions, apply_action

    points = np.zeros(24, dtype=int)
    # One P1 checker at index 5
    points[5] = 1

    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    dice = (1, 2)
    actions = legal_actions(state, dice)

    assert actions, "Expected at least one legal action for dice (1,2)."

    two_step_actions = [a for a in actions if len(a.steps) == 2]
    assert two_step_actions, "Expected at least one two-step action using both dice."

    # Record total before applying any action
    before_total = state.board.total_checkers_for(PLAYER_1)

    # Pick one two-step action and ensure total checkers are preserved
    action = two_step_actions[0]
    new_state = apply_action(state, action)

    after_total = new_state.board.total_checkers_for(PLAYER_1)
    assert after_total == before_total, (
        "Total number of checkers for P1 should be preserved after applying action."
    )

def test_no_legal_moves_when_all_bar_entry_points_blocked():
    """
    If a player has a checker on the bar and every entry point is blocked
    by 2+ opposing checkers, there should be no legal actions.
    """
    import numpy as np
    from src.game.board import Board, PLAYER_1, PLAYER_2, player_index
    from src.game.state import GameState
    from src.game.rules import legal_actions

    points = np.zeros(24, dtype=int)
    # For PLAYER_1, entry points for dice 1..6 are indices 23..18.
    # Block all of them with 2 P2 checkers each.
    for idx in range(18, 24):
        points[idx] = -2  # two checkers for PLAYER_2

    bar = np.zeros(2, dtype=int)
    borne_off = np.zeros(2, dtype=int)
    bar[player_index(PLAYER_1)] = 1  # P1 has a checker on the bar

    board = Board(points=points, bar=bar, borne_off=borne_off)
    state = GameState(board=board, current_player=PLAYER_1)

    actions = legal_actions(state, (3, 4))

    assert actions == [], "Expected no legal actions when all bar entry points are blocked."

