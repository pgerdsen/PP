"""
Graphical UI for Backgammon using Pygame.

Features:
- Visual board with proper backgammon layout
- Clickable checkers and points
- Dice visualization
- Move validation and execution
"""

from __future__ import annotations

import pygame
import sys
from typing import Optional, Tuple, List
from dataclasses import dataclass

from ..game.state import GameState
from ..game.board import Player, PLAYER_1, PLAYER_2
from ..game import rules
from ..game.dice import roll_dice


# Colors - Realistic backgammon board colors
BOARD_COLOR = (210, 180, 140)  # Tan/beige board background
POINT_COLOR_LIGHT = (245, 222, 179)  # Light cream/tan
POINT_COLOR_DARK = (101, 67, 33)  # Dark brown (like real backgammon)
CHECKER_COLOR_P1 = (255, 255, 255)  # White/cream checkers
CHECKER_COLOR_P2 = (30, 30, 30)  # Dark brown/black checkers
CHECKER_OUTLINE_P1 = (200, 200, 200)  # Light gray outline for white
CHECKER_OUTLINE_P2 = (60, 60, 60)  # Dark outline for dark checkers
HIGHLIGHT_COLOR = (255, 215, 0)  # Gold highlight
VALID_MOVE_COLOR = (50, 205, 50)  # Green for valid moves
INVALID_MOVE_COLOR = (220, 20, 60)  # Red for invalid
TEXT_COLOR = (255, 255, 255)  # White text
BACKGROUND_COLOR = (40, 40, 40)  # Dark background
BAR_COLOR = (160, 130, 90)  # Slightly darker than board

# Board dimensions - larger for better visibility
BOARD_WIDTH = 900
BOARD_HEIGHT = 700
POINT_WIDTH = 35
POINT_HEIGHT = 280
BAR_WIDTH = 70
CHECKER_RADIUS = 14
CHECKER_SPACING = 3


@dataclass
class PointRect:
    """Represents a clickable point on the board."""
    index: int  # 0-23
    rect: pygame.Rect
    is_upper: bool  # True for upper half (points 13-24), False for lower (points 1-12)


class CheckerSprite:
    """Represents a checker sprite on the board."""
    def __init__(self, player: Player, point_index: int, stack_position: int):
        self.player = player
        self.point_index = point_index
        self.stack_position = stack_position
        self.selected = False


class GraphicalUI:
    """Main graphical UI class for backgammon."""
    
    def __init__(self, state: GameState):
        pygame.init()
        self.screen = pygame.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))
        pygame.display.set_caption("Backgammon")
        self.clock = pygame.time.Clock()
        self.state = state
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Selection state
        self.selected_point: Optional[int] = None
        self.selected_bar: Optional[Player] = None
        self.valid_targets: List[Optional[int]] = []  # None means bearing off
        self.current_dice: Optional[Tuple[int, int]] = None
        self.waiting_for_dice_roll = True
        self.can_bear_off = False
        
        # Calculate point positions
        self.point_rects: List[PointRect] = self._calculate_point_positions()
        
    def _calculate_point_positions(self) -> List[PointRect]:
        """Calculate the screen positions for all 24 points."""
        rects = []
        
        # Upper half (points 13-24, indices 12-23)
        # Points go from right to left
        for i in range(12):
            point_idx = 23 - i  # Reverse order: 23, 22, ..., 12
            x = BOARD_WIDTH - BAR_WIDTH - (i + 1) * POINT_WIDTH
            y = 0
            rect = pygame.Rect(x, y, POINT_WIDTH, POINT_HEIGHT)
            rects.append(PointRect(index=point_idx, rect=rect, is_upper=True))
        
        # Lower half (points 1-12, indices 0-11)
        # Points go from left to right
        for i in range(12):
            point_idx = i
            x = i * POINT_WIDTH
            y = BOARD_HEIGHT - POINT_HEIGHT
            rect = pygame.Rect(x, y, POINT_WIDTH, POINT_HEIGHT)
            rects.append(PointRect(index=point_idx, rect=rect, is_upper=False))
        
        return rects
    
    def _get_point_rect(self, point_index: int) -> Optional[PointRect]:
        """Get the PointRect for a given point index."""
        for pr in self.point_rects:
            if pr.index == point_index:
                return pr
        return None
    
    def _point_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """Return the point index at the given screen position, or None."""
        x, y = pos
        for pr in self.point_rects:
            if pr.rect.collidepoint(x, y):
                return pr.index
        return None
    
    def _draw_checker(self, surface: pygame.Surface, x: int, y: int, player: Player, selected: bool = False):
        """Draw a single checker at the given position with realistic appearance."""
        color = CHECKER_COLOR_P1 if player == PLAYER_1 else CHECKER_COLOR_P2
        default_outline = CHECKER_OUTLINE_P1 if player == PLAYER_1 else CHECKER_OUTLINE_P2
        outline_color = HIGHLIGHT_COLOR if selected else default_outline
        outline_width = 4 if selected else 2
        
        # Draw checker with a subtle 3D effect
        pygame.draw.circle(surface, color, (x, y), CHECKER_RADIUS)
        
        # Add a subtle highlight on top for 3D effect
        if player == PLAYER_1:
            # White checker - add light highlight
            pygame.draw.circle(surface, (255, 255, 255), (x - 3, y - 3), CHECKER_RADIUS - 5)
        else:
            # Dark checker - add subtle highlight
            pygame.draw.circle(surface, (80, 80, 80), (x - 3, y - 3), CHECKER_RADIUS - 5)
        
        # Draw outline
        pygame.draw.circle(surface, outline_color, (x, y), CHECKER_RADIUS, outline_width)
    
    def _draw_point(self, surface: pygame.Surface, point_rect: PointRect, point_value: int):
        """Draw a single point on the board with realistic backgammon appearance."""
        rect = point_rect.rect
        is_upper = point_rect.is_upper
        
        # Real backgammon boards alternate colors in a specific pattern
        # Points 1-6 and 13-18 are one color, 7-12 and 19-24 are the other
        # But we need to alternate within each quadrant too
        point_num = point_rect.index + 1  # Convert 0-23 to 1-24
        if point_num <= 6 or (point_num >= 13 and point_num <= 18):
            # First and third quadrants
            color = POINT_COLOR_DARK if (point_num % 2 == 1) else POINT_COLOR_LIGHT
        else:
            # Second and fourth quadrants
            color = POINT_COLOR_LIGHT if (point_num % 2 == 1) else POINT_COLOR_DARK
        
        # Draw the point triangle with more realistic shape
        if is_upper:
            # Upper points point downward
            points = [
                (rect.left + 2, rect.bottom),
                (rect.right - 2, rect.bottom),
                (rect.centerx, rect.top + 5)  # Slightly rounded tip
            ]
        else:
            # Lower points point upward
            points = [
                (rect.left + 2, rect.top),
                (rect.right - 2, rect.top),
                (rect.centerx, rect.bottom - 5)  # Slightly rounded tip
            ]
        
        # Draw triangle with subtle shadow effect
        pygame.draw.polygon(surface, color, points)
        # Draw outline with slight gradient effect
        pygame.draw.polygon(surface, (0, 0, 0), points, 2)
        
        # Draw checkers on this point
        owner = self.state.board.owner_of_point(point_rect.index)
        count = self.state.board.count_on_point(point_rect.index)
        
        if count > 0:
            # Calculate positions for stacked checkers
            center_x = rect.centerx
            if is_upper:
                # Upper points: checkers stack from bottom going up
                start_y = rect.bottom - CHECKER_RADIUS - 8
                direction = -1
            else:
                # Lower points: checkers stack from top going down
                start_y = rect.top + CHECKER_RADIUS + 8
                direction = 1
            
            # Stack checkers vertically with better spacing
            max_visible = min(count, 5)  # Show up to 5 checkers, then show count
            for i in range(max_visible):
                y = start_y + (i * (CHECKER_RADIUS * 2 + CHECKER_SPACING)) * direction
                is_selected = (self.selected_point == point_rect.index and i == 0)
                self._draw_checker(surface, center_x, y, owner, is_selected)
            
            # If more than 5 checkers, show count with better visibility
            if count > 5:
                count_text = self.small_font.render(str(count), True, (255, 255, 0))
                count_y = start_y + (5 * (CHECKER_RADIUS * 2 + CHECKER_SPACING)) * direction
                count_rect = count_text.get_rect(center=(center_x, count_y))
                # Draw semi-transparent background for better readability
                bg_rect = pygame.Rect(count_rect.x - 2, count_rect.y - 2, count_rect.width + 4, count_rect.height + 4)
                # Create a transparent surface for the background
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.set_alpha(180)  # Set transparency (0-255)
                pygame.draw.rect(bg_surface, (0, 0, 0), (0, 0, bg_rect.width, bg_rect.height))
                surface.blit(bg_surface, bg_rect.topleft)
                surface.blit(count_text, count_rect)
        
        # Highlight if this is a valid target with a subtle glow effect
        if point_rect.index in self.valid_targets:
            # Draw a subtle highlight around the point
            highlight_points = []
            if is_upper:
                highlight_points = [
                    (rect.left, rect.bottom + 3),
                    (rect.right, rect.bottom + 3),
                    (rect.centerx, rect.top - 3)
                ]
            else:
                highlight_points = [
                    (rect.left, rect.top - 3),
                    (rect.right, rect.top - 3),
                    (rect.centerx, rect.bottom + 3)
                ]
            pygame.draw.polygon(surface, VALID_MOVE_COLOR, highlight_points, 3)
        
        # Show bearing off area if valid
        if None in self.valid_targets and self.can_bear_off:
            # Draw bearing off indicator
            if is_upper:
                bear_off_rect = pygame.Rect(rect.x, rect.top - 25, rect.width, 25)
            else:
                bear_off_rect = pygame.Rect(rect.x, rect.bottom, rect.width, 25)
            pygame.draw.rect(surface, VALID_MOVE_COLOR, bear_off_rect, 2)
    
    def _draw_bar(self, surface: pygame.Surface):
        """Draw the bar area in the middle of the board with realistic appearance."""
        bar_rect = pygame.Rect(
            BOARD_WIDTH - BAR_WIDTH,
            POINT_HEIGHT,
            BAR_WIDTH,
            BOARD_HEIGHT - 2 * POINT_HEIGHT
        )
        
        # Draw bar with wood-like texture effect
        pygame.draw.rect(surface, BAR_COLOR, bar_rect)
        # Draw border with depth
        pygame.draw.rect(surface, (0, 0, 0), bar_rect, 4)
        # Add subtle inner border for 3D effect
        inner_rect = pygame.Rect(bar_rect.x + 3, bar_rect.y + 3, bar_rect.width - 6, bar_rect.height - 6)
        pygame.draw.rect(surface, (180, 150, 110), inner_rect, 2)
        
        # Draw checkers on bar
        bar_x = bar_rect.centerx
        
        # Player 1 checkers on bar (top half)
        p1_bar_count = int(self.state.board.bar[0])
        if p1_bar_count > 0:
            bar_y = bar_rect.top + CHECKER_RADIUS + 5
            for i in range(min(p1_bar_count, 5)):
                y = bar_y + i * (CHECKER_RADIUS * 2 + CHECKER_SPACING)
                is_selected = (self.selected_bar == PLAYER_1 and i == 0)
                self._draw_checker(surface, bar_x, y, PLAYER_1, is_selected)
            if p1_bar_count > 5:
                count_text = self.small_font.render(str(p1_bar_count), True, TEXT_COLOR)
                surface.blit(count_text, (bar_x - 10, bar_y + 5 * (CHECKER_RADIUS * 2 + CHECKER_SPACING)))
        
        # Player 2 checkers on bar (bottom half)
        p2_bar_count = int(self.state.board.bar[1])
        if p2_bar_count > 0:
            bar_y = bar_rect.bottom - CHECKER_RADIUS - 5
            for i in range(min(p2_bar_count, 5)):
                y = bar_y - i * (CHECKER_RADIUS * 2 + CHECKER_SPACING)
                is_selected = (self.selected_bar == PLAYER_2 and i == 0)
                self._draw_checker(surface, bar_x, y, PLAYER_2, is_selected)
            if p2_bar_count > 5:
                count_text = self.small_font.render(str(p2_bar_count), True, TEXT_COLOR)
                surface.blit(count_text, (bar_x - 10, bar_y - 5 * (CHECKER_RADIUS * 2 + CHECKER_SPACING)))
    
    def _draw_borne_off(self, surface: pygame.Surface):
        """Draw the borne-off areas on the sides."""
        # Player 1 borne off (right side)
        p1_off = int(self.state.board.borne_off[0])
        if p1_off > 0:
            text = self.font.render(f"P1 Off: {p1_off}", True, TEXT_COLOR)
            surface.blit(text, (BOARD_WIDTH - 100, 10))
        
        # Player 2 borne off (left side)
        p2_off = int(self.state.board.borne_off[1])
        if p2_off > 0:
            text = self.font.render(f"P2 Off: {p2_off}", True, TEXT_COLOR)
            surface.blit(text, (10, BOARD_HEIGHT - 30))
    
    def _draw_dice(self, surface: pygame.Surface):
        """Draw the dice and roll button."""
        dice_x = BOARD_WIDTH // 2 - 60
        dice_y = BOARD_HEIGHT // 2 - 20
        
        if self.current_dice:
            d1, d2 = self.current_dice
            # Draw dice
            dice1_rect = pygame.Rect(dice_x, dice_y, 40, 40)
            dice2_rect = pygame.Rect(dice_x + 50, dice_y, 40, 40)
            
            pygame.draw.rect(surface, (255, 255, 255), dice1_rect)
            pygame.draw.rect(surface, (0, 0, 0), dice1_rect, 2)
            pygame.draw.rect(surface, (255, 255, 255), dice2_rect)
            pygame.draw.rect(surface, (0, 0, 0), dice2_rect, 2)
            
            # Draw dots
            self._draw_die_dots(surface, dice1_rect, d1)
            self._draw_die_dots(surface, dice2_rect, d2)
        else:
            # Draw roll button
            roll_rect = pygame.Rect(dice_x, dice_y, 100, 40)
            pygame.draw.rect(surface, (100, 150, 255), roll_rect)
            pygame.draw.rect(surface, (0, 0, 0), roll_rect, 2)
            roll_text = self.font.render("Roll Dice", True, (255, 255, 255))
            text_rect = roll_text.get_rect(center=roll_rect.center)
            surface.blit(roll_text, text_rect)
    
    def _draw_die_dots(self, surface: pygame.Surface, rect: pygame.Rect, value: int):
        """Draw dots on a die face."""
        dot_radius = 3
        dot_positions = {
            1: [(rect.centerx, rect.centery)],
            2: [(rect.centerx - 8, rect.centery - 8), (rect.centerx + 8, rect.centery + 8)],
            3: [(rect.centerx - 8, rect.centery - 8), (rect.centerx, rect.centery), (rect.centerx + 8, rect.centery + 8)],
            4: [(rect.centerx - 8, rect.centery - 8), (rect.centerx + 8, rect.centery - 8),
                (rect.centerx - 8, rect.centery + 8), (rect.centerx + 8, rect.centery + 8)],
            5: [(rect.centerx - 8, rect.centery - 8), (rect.centerx + 8, rect.centery - 8),
                (rect.centerx, rect.centery),
                (rect.centerx - 8, rect.centery + 8), (rect.centerx + 8, rect.centery + 8)],
            6: [(rect.centerx - 8, rect.centery - 8), (rect.centerx + 8, rect.centery - 8),
                (rect.centerx - 8, rect.centery), (rect.centerx + 8, rect.centery),
                (rect.centerx - 8, rect.centery + 8), (rect.centerx + 8, rect.centery + 8)],
        }
        
        for pos in dot_positions.get(value, []):
            pygame.draw.circle(surface, (0, 0, 0), pos, dot_radius)
    
    def _draw_info(self, surface: pygame.Surface):
        """Draw game information."""
        player_text = f"Current Player: {'1 (White)' if self.state.current_player == PLAYER_1 else '2 (Black)'}"
        text = self.font.render(player_text, True, TEXT_COLOR)
        surface.blit(text, (10, 10))
        
        if self.selected_point is not None:
            info_text = f"Selected point: {self.selected_point + 1}"
            text = self.small_font.render(info_text, True, TEXT_COLOR)
            surface.blit(text, (10, 40))
        elif self.selected_bar is not None:
            info_text = f"Selected bar (Player {1 if self.selected_bar == PLAYER_1 else 2})"
            text = self.small_font.render(info_text, True, TEXT_COLOR)
            surface.blit(text, (10, 40))
        
        # Show instructions
        if not self.current_dice:
            inst_text = "Click 'Roll Dice' to start your turn"
            text = self.small_font.render(inst_text, True, (255, 255, 255))
            surface.blit(text, (10, BOARD_HEIGHT - 60))
        elif self.selected_point is None and self.selected_bar is None:
            inst_text = "Click on one of your checkers to select it"
            text = self.small_font.render(inst_text, True, (255, 255, 255))
            surface.blit(text, (10, BOARD_HEIGHT - 60))
        elif self.valid_targets:
            inst_text = "Click on a highlighted point to move"
            text = self.small_font.render(inst_text, True, (255, 255, 255))
            surface.blit(text, (10, BOARD_HEIGHT - 60))
    
    def _get_valid_targets(self) -> List[Optional[int]]:
        """Get valid target points for the currently selected checker.
        Returns list that may include None for bearing off."""
        if not self.current_dice:
            return []
        
        # Validate state
        if self.state is None or not hasattr(self.state, 'board') or not hasattr(self.state, 'current_player'):
            return []
        
        try:
            if self.selected_bar is not None:
                # Can only enter from bar
                player = self.selected_bar
                if player != self.state.current_player:
                    return []
                
                valid = []
                for die in self.current_dice:
                    try:
                        entry_point = rules.entry_point_from_bar(player, die)
                        if entry_point is not None and 0 <= entry_point < 24:
                            if hasattr(self.state.board, 'owner_of_point') and hasattr(self.state.board, 'count_on_point'):
                                owner = self.state.board.owner_of_point(entry_point)
                                count = self.state.board.count_on_point(entry_point)
                                if owner == 0 or owner == player or (owner != player and count == 1):
                                    valid.append(entry_point)
                    except Exception as e:
                        print(f"Error processing die {die} for bar entry: {e}")
                        continue
                return valid
            
            if self.selected_point is not None:
                # Validate point index
                if not (0 <= self.selected_point < 24):
                    return []
                
                # Check moves from this point
                player = self.state.current_player
                try:
                    if not hasattr(self.state.board, 'owner_of_point'):
                        return []
                    owner = self.state.board.owner_of_point(self.selected_point)
                    if owner != player:
                        return []
                except Exception as e:
                    print(f"Error checking point ownership: {e}")
                    return []
                
                valid = []
                try:
                    legal_actions_list = rules.legal_actions(self.state, self.current_dice)
                    if not legal_actions_list:
                        return []
                    
                    for action in legal_actions_list:
                        if not hasattr(action, 'steps') or not action.steps:
                            continue
                        try:
                            for step in action.steps:
                                if not hasattr(step, 'from_point') or not hasattr(step, 'to_point'):
                                    continue
                                if step.from_point == self.selected_point:
                                    valid.append(step.to_point)  # Can be None for bearing off
                        except Exception as e:
                            print(f"Error processing action steps: {e}")
                            continue
                except Exception as e:
                    print(f"Error getting legal actions in _get_valid_targets: {e}")
                    import traceback
                    traceback.print_exc()
                    return []
                
                return list(set(valid))  # Remove duplicates
            
            return []
        except Exception as e:
            print(f"Error getting valid targets: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle a mouse click. Returns True if a move was made."""
        try:
            x, y = pos
            
            # Validate state exists
            if self.state is None or not hasattr(self.state, 'board') or not hasattr(self.state, 'current_player'):
                print("Error: Invalid game state")
                return False
            
            # Check if clicking on roll dice button
            if not self.current_dice:
                dice_x = BOARD_WIDTH // 2 - 60
                dice_y = BOARD_HEIGHT // 2 - 20
                roll_rect = pygame.Rect(dice_x, dice_y, 100, 40)
                if roll_rect.collidepoint(x, y):
                    try:
                        self.current_dice = roll_dice()
                        self.state.set_dice(*self.current_dice)
                        
                        # Check if there are any legal moves with these dice
                        try:
                            legal_actions_list = rules.legal_actions(self.state, self.current_dice)
                            if not legal_actions_list:
                                # No legal moves - automatically pass turn
                                print("DEBUG: No legal moves available, passing turn")
                                if hasattr(self.state, 'record_turn'):
                                    self.state.record_turn(self.current_dice, action=None)
                                if hasattr(self.state, 'next_turn'):
                                    self.state.next_turn()
                                self._reset_selection()
                                return True
                        except Exception as e:
                            print(f"Error checking legal moves after dice roll: {e}")
                            # Continue anyway - let user try to make a move
                        
                        return False
                    except Exception as e:
                        print(f"Error rolling dice: {e}")
                        import traceback
                        traceback.print_exc()
                        return False
            
            # Check if clicking on bar
            bar_rect = pygame.Rect(
                BOARD_WIDTH - BAR_WIDTH,
                POINT_HEIGHT,
                BAR_WIDTH,
                BOARD_HEIGHT - 2 * POINT_HEIGHT
            )
            if bar_rect.collidepoint(x, y):
                try:
                    # Check which player's bar area was clicked
                    if y < bar_rect.centery:
                        # Upper half - Player 1
                        if hasattr(self.state.board, 'bar') and len(self.state.board.bar) > 0:
                            if self.state.board.bar[0] > 0 and self.state.current_player == PLAYER_1:
                                self.selected_bar = PLAYER_1
                                self.selected_point = None
                                self.valid_targets = self._get_valid_targets()
                                self.can_bear_off = False
                    else:
                        # Lower half - Player 2
                        if hasattr(self.state.board, 'bar') and len(self.state.board.bar) > 1:
                            if self.state.board.bar[1] > 0 and self.state.current_player == PLAYER_2:
                                self.selected_bar = PLAYER_2
                                self.selected_point = None
                                self.valid_targets = self._get_valid_targets()
                                self.can_bear_off = False
                except Exception as e:
                    print(f"Error handling bar click: {e}")
                    import traceback
                    traceback.print_exc()
                return False
            
            # Check if clicking on a point
            clicked_point = self._point_at_position(pos)
            if clicked_point is not None and 0 <= clicked_point < 24:
                try:
                    # If we have a selection, try to make a move
                    if self.selected_point is not None or self.selected_bar is not None:
                        if clicked_point in self.valid_targets:
                            # Make the move
                            result = self._make_move(clicked_point)
                            return result
                        else:
                            # Deselect and select new point
                            self.selected_point = clicked_point
                            self.selected_bar = None
                            self.valid_targets = self._get_valid_targets()
                            self.can_bear_off = None in self.valid_targets if self.valid_targets else False
                    else:
                        # Select this point if it belongs to current player
                        if hasattr(self.state.board, 'owner_of_point'):
                            owner = self.state.board.owner_of_point(clicked_point)
                            if owner == self.state.current_player:
                                self.selected_point = clicked_point
                                self.selected_bar = None
                                self.valid_targets = self._get_valid_targets()
                                self.can_bear_off = None in self.valid_targets if self.valid_targets else False
                except Exception as e:
                    print(f"Error handling point click: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            
            # Check for bearing off click (click outside board but in bearing off area)
            if (self.selected_point is not None or self.selected_bar is not None) and self.valid_targets and None in self.valid_targets:
                try:
                    # Check if click is in bearing off area
                    # Home boards are 6 points each: Player 1 = indices 0-5, Player 2 = indices 18-23
                    if self.state.current_player == PLAYER_1:
                        # Player 1 bears off from bottom (points 0-5, which is 6 points)
                        bear_off_rect = pygame.Rect(0, BOARD_HEIGHT - 20, 6 * POINT_WIDTH, 20)
                    else:
                        # Player 2 bears off from top (points 18-23, which is 6 points)
                        bear_off_rect = pygame.Rect(BOARD_WIDTH - BAR_WIDTH - 6 * POINT_WIDTH, 0, 6 * POINT_WIDTH, 20)
                    
                    if bear_off_rect.collidepoint(x, y):
                        return self._make_move(None)  # None means bearing off
                except Exception as e:
                    print(f"Error handling bear off click: {e}")
                    import traceback
                    traceback.print_exc()
            
            return False
        except Exception as e:
            print(f"Critical error in _handle_click: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _make_move(self, target_point: Optional[int]) -> bool:
        """Attempt to make a move to the target point (None for bearing off). Returns True if successful."""
        # Validate preconditions
        if not self.current_dice:
            return False
        
        if (self.selected_point is None and self.selected_bar is None):
            return False
        
        if self.state is None or not hasattr(self.state, 'current_player') or not hasattr(self.state, 'board'):
            print("Error: Invalid game state in _make_move")
            return False
        
        player = self.state.current_player
        
        # Find a legal action that matches our selection
        try:
            legal_actions_list = rules.legal_actions(self.state, self.current_dice)
            if not legal_actions_list:
                return False
        except Exception as e:
            print(f"Error getting legal actions: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Try to find a matching action
        # Look for actions that contain our desired move as the first step
        matching_action = None
        
        try:
            for action in legal_actions_list:
                # Check if this action matches our move
                if not hasattr(action, 'steps') or not action.steps or len(action.steps) == 0:
                    continue
                
                first_step = action.steps[0]
                if not hasattr(first_step, 'from_point') or not hasattr(first_step, 'to_point'):
                    continue
                    
                if self.selected_bar is not None:
                    # Moving from bar - check if first step matches
                    if first_step.from_point is None and first_step.to_point == target_point:
                        matching_action = action
                        break
                elif self.selected_point is not None:
                    # Validate point index
                    if not (0 <= self.selected_point < 24):
                        continue
                    # Moving from a point - check if first step matches
                    if first_step.from_point == self.selected_point and first_step.to_point == target_point:
                        matching_action = action
                        break
        except Exception as e:
            print(f"Error matching actions: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        if matching_action:
            try:
                print(f"DEBUG: Applying action with {len(matching_action.steps)} steps")
                print(f"DEBUG: Current player: {self.state.current_player}")
                print(f"DEBUG: Current dice: {self.current_dice}")
                
                # Apply this action
                new_state = rules.apply_action(self.state, matching_action)
                if new_state is None:
                    print("Error: apply_action returned None")
                    return False
                
                # Validate new state
                if not hasattr(new_state, 'board') or not hasattr(new_state, 'current_player'):
                    print("Error: Invalid state returned from apply_action")
                    return False
                
                print(f"DEBUG: New state created, player: {new_state.current_player}")
                
                # Update state safely
                old_state = self.state
                self.state = new_state
                
                # Check how many steps (dice) were used
                steps_used = len(matching_action.steps)
                d1, d2 = self.current_dice
                
                # If we used both dice (2 steps), the turn is over
                # If we only used one die (1 step), we need to update dice and continue
                if steps_used >= 2:
                    # Used both dice - turn is complete
                    try:
                        if hasattr(self.state, 'record_turn'):
                            self.state.record_turn(self.current_dice, matching_action)
                            print("DEBUG: Turn recorded")
                    except Exception as e:
                        print(f"Error recording turn: {e}")
                        import traceback
                        traceback.print_exc()
                        # Restore old state on error
                        self.state = old_state
                        return False
                    
                    # Advance turn
                    try:
                        if hasattr(self.state, 'next_turn'):
                            self.state.next_turn()
                            print(f"DEBUG: Turn advanced, new player: {self.state.current_player}")
                    except Exception as e:
                        print(f"Error advancing turn: {e}")
                        import traceback
                        traceback.print_exc()
                        # Restore old state on error
                        self.state = old_state
                        return False
                    
                    # Reset selection (this clears dice since turn is over)
                    self._reset_selection()
                    print("DEBUG: Move completed successfully - both dice used")
                else:
                    # Only used one die - determine which one and keep the other
                    step = matching_action.steps[0]
                    remaining_die = None
                    
                    if step.to_point is not None and self.selected_point is not None:
                        # Calculate distance moved from point
                        distance = abs(step.to_point - self.selected_point)
                        if distance == d1:
                            remaining_die = d2
                        elif distance == d2:
                            remaining_die = d1
                    elif step.to_point is not None and self.selected_bar is not None:
                        # Moving from bar - calculate which die was used
                        # Based on rules.entry_point_from_bar:
                        #   PLAYER_1: entry_point_index = 24 - die, so die = 24 - entry_point_index
                        #   PLAYER_2: entry_point_index = die - 1, so die = entry_point_index + 1
                        if self.state.current_player == PLAYER_1:
                            # PLAYER_1 enters on points 24-19 (indices 23-18)
                            entry_die = 24 - step.to_point
                        else:
                            # PLAYER_2 enters on points 1-6 (indices 0-5)
                            entry_die = step.to_point + 1
                        if entry_die == d1:
                            remaining_die = d2
                        elif entry_die == d2:
                            remaining_die = d1
                    
                    # If we couldn't determine, check which die can still be used
                    if remaining_die is None:
                        # Try each die to see which one still has legal moves
                        # Use single_die_moves to check for moves with just one die (not as doubles)
                        for test_die in [d1, d2]:
                            try:
                                test_steps = rules.single_die_moves(self.state, test_die)
                                if test_steps:
                                    remaining_die = test_die
                                    break
                            except:
                                continue
                        if remaining_die is None:
                            # No legal moves with either die - turn is over
                            remaining_die = d2  # Default, but we'll advance turn anyway
                    
                    # Check if there are any legal moves with the remaining die
                    # Use single_die_moves instead of legal_actions to avoid treating it as doubles
                    try:
                        remaining_steps = rules.single_die_moves(self.state, remaining_die)
                        if not remaining_steps:
                            # No more legal moves - turn is over
                            if hasattr(self.state, 'record_turn'):
                                self.state.record_turn(self.current_dice, matching_action)
                            if hasattr(self.state, 'next_turn'):
                                self.state.next_turn()
                            self._reset_selection()
                            print("DEBUG: No more legal moves, turn ended")
                            return True
                    except Exception as e:
                        print(f"Error checking remaining moves: {e}")
                        # If we can't check, assume turn is over to be safe
                        if hasattr(self.state, 'record_turn'):
                            self.state.record_turn(self.current_dice, matching_action)
                        if hasattr(self.state, 'next_turn'):
                            self.state.next_turn()
                        self._reset_selection()
                        return True
                    
                    # Update current dice to just the remaining die
                    # Store as tuple for consistency, but we'll use single_die_moves for checking
                    self.current_dice = (remaining_die, remaining_die)
                    # Clear selection so user can select a new checker for the remaining die
                    self.selected_point = None
                    self.selected_bar = None
                    self.valid_targets = []
                    print(f"DEBUG: One die used, remaining die: {remaining_die}, current_dice: {self.current_dice}")
                return True
            except Exception as e:
                print(f"Error applying move: {e}")
                import traceback
                traceback.print_exc()
                # Don't reset selection on error - let user try again
                return False
        
        return False
    
    def _reset_selection(self):
        """Reset the selection state."""
        self.selected_point = None
        self.selected_bar = None
        self.valid_targets = []
        self.current_dice = None
        self.waiting_for_dice_roll = True
        self.can_bear_off = False
        # Clear the no-moves check flag (delete attribute so hasattr works correctly)
        if hasattr(self, '_checked_no_moves_this_turn'):
            delattr(self, '_checked_no_moves_this_turn')
    
    def draw(self):
        """Draw the entire board with realistic backgammon appearance."""
        try:
            # Validate state
            if self.state is None or not hasattr(self.state, 'board'):
                # Draw error message
                self.screen.fill(BACKGROUND_COLOR)
                error_text = self.font.render("Error: Invalid game state", True, (255, 0, 0))
                self.screen.blit(error_text, (10, 10))
                pygame.display.flip()
                return
            
            # Draw background
            self.screen.fill(BACKGROUND_COLOR)
            
            # Draw board background (the playing surface)
            board_rect = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT)
            pygame.draw.rect(self.screen, BOARD_COLOR, board_rect)
            
            # Draw border around the board
            pygame.draw.rect(self.screen, (0, 0, 0), board_rect, 5)
            
            # Draw all points
            if hasattr(self.state.board, 'points') and self.point_rects:
                for point_rect in self.point_rects:
                    try:
                        if 0 <= point_rect.index < len(self.state.board.points):
                            point_value = int(self.state.board.points[point_rect.index])
                            self._draw_point(self.screen, point_rect, point_value)
                    except Exception as e:
                        print(f"Error drawing point {point_rect.index}: {e}")
                        continue
            
            # Draw bar
            try:
                self._draw_bar(self.screen)
            except Exception as e:
                print(f"Error drawing bar: {e}")
            
            # Draw borne off areas
            try:
                self._draw_borne_off(self.screen)
            except Exception as e:
                print(f"Error drawing borne off: {e}")
            
            # Draw dice
            try:
                self._draw_dice(self.screen)
            except Exception as e:
                print(f"Error drawing dice: {e}")
            
            # Draw info
            try:
                self._draw_info(self.screen)
            except Exception as e:
                print(f"Error drawing info: {e}")
            
            pygame.display.flip()
        except Exception as e:
            print(f"Critical error in draw: {e}")
            import traceback
            traceback.print_exc()
            # Try to at least show something
            try:
                self.screen.fill(BACKGROUND_COLOR)
                error_text = self.font.render(f"Draw Error: {str(e)}", True, (255, 0, 0))
                self.screen.blit(error_text, (10, 10))
                pygame.display.flip()
            except Exception:
                pass
    
    def run(self):
        """Main game loop."""
        running = True
        
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Left click
                            try:
                                self._handle_click(event.pos)
                            except Exception as e:
                                print(f"Error in click handler: {e}")
                                import traceback
                                traceback.print_exc()
                                # Continue running despite error
                
                try:
                    self.draw()
                except Exception as e:
                    print(f"Error in draw: {e}")
                    import traceback
                    traceback.print_exc()
                    # Try to show error on screen
                    try:
                        self.screen.fill((0, 0, 0))
                        error_text = self.font.render(f"Draw Error: {str(e)[:50]}", True, (255, 0, 0))
                        self.screen.blit(error_text, (10, 10))
                        pygame.display.flip()
                    except:
                        pass
                
                self.clock.tick(60)
            except KeyboardInterrupt:
                running = False
            except Exception as e:
                print(f"Critical error in game loop: {e}")
                import traceback
                traceback.print_exc()
                running = False
        
        pygame.quit()
        sys.exit()

