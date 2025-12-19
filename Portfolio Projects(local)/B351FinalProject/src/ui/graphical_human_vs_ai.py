"""
Graphical UI for Human vs AI Backgammon game.
"""

from __future__ import annotations

import sys
import pygame
from pathlib import Path

# Ensure we can import as a package
# Add the project root (parent of src) to path so package imports work
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import using package structure
import argparse

from src.game.state import GameState
from src.game.board import PLAYER_1, PLAYER_2
from src.game import rules
from src.game.dice import roll_dice
from src.game.game_loop import RandomAgent
from src.ui.graphical import GraphicalUI, BACKGROUND_COLOR, BOARD_WIDTH, BOARD_HEIGHT
from src.ai.heuristics import HeuristicAgent
from src.ai.expectimax import ExpectimaxAgent, ExpectimaxConfig


class HumanVsAIGraphicalUI(GraphicalUI):
    """Extended UI that supports AI opponents."""
    
    def __init__(self, state: GameState, ai_agent, human_player: int = PLAYER_1, ai_name: str = "AI"):
        super().__init__(state)
        self.ai_agent = ai_agent
        self.human_player = human_player
        self.ai_thinking = False
        self.ai_name = ai_name  # Name/type of AI for display
    
    def _handle_ai_turn(self):
        """Handle AI's turn automatically."""
        try:
            if self.state.current_player != self.human_player and not self.ai_thinking:
                self.ai_thinking = True
                
                # Roll dice for AI
                if not self.current_dice:
                    self.current_dice = roll_dice()
                    self.state.set_dice(*self.current_dice)
                    # Small delay to show dice roll
                    pygame.time.wait(500)
                
                # Get AI's action
                try:
                    # Test legal_actions first
                    test_legal = rules.legal_actions(self.state, self.current_dice)
                except Exception as e:
                    raise
                try:
                    # Show "thinking" message for slow AIs (like expectimax)
                    if "expectimax" in self.ai_name.lower():
                        print(f"{self.ai_name} is thinking... (this may take a while)")
                        # Redraw to show the message
                        self.draw()
                        pygame.display.flip()
                    
                    action = self.ai_agent.choose_action(self.state, self.current_dice)
                except Exception as e:
                    print(f"Error in choose_action: {e}")
                    import traceback
                    traceback.print_exc()
                    action = None
                
                if action:
                    try:
                        # Apply AI's move
                        old_state = self.state
                        self.state = rules.apply_action(self.state, action)
                        
                        # Check how many steps (dice) were used
                        steps_used = len(action.steps)
                        d1, d2 = self.current_dice
                        
                        # If we used both dice (2 steps), the turn is complete
                        # If we only used one die (1 step), we need to update dice and continue
                        if steps_used >= 2:
                            # Used both dice - turn is complete
                            if hasattr(self.state, 'record_turn'):
                                self.state.record_turn(self.current_dice, action)
                            # Advance turn
                            self.state.next_turn()
                            self._reset_selection()
                            print("DEBUG: AI move completed - both dice used")
                        else:
                            # Only used one die - determine which one and keep the other
                            step = action.steps[0]
                            remaining_die = None
                            
                            # Try to determine which die was used
                            if step.to_point is not None:
                                # Check if this was a bar entry
                                if step.from_point is None:
                                    # Moving from bar - calculate which die was used
                                    if self.state.current_player == PLAYER_1:
                                        entry_die = 24 - step.to_point
                                    else:
                                        entry_die = step.to_point + 1
                                    if entry_die == d1:
                                        remaining_die = d2
                                    elif entry_die == d2:
                                        remaining_die = d1
                                else:
                                    # Normal move - calculate distance
                                    distance = abs(step.to_point - step.from_point)
                                    if distance == d1:
                                        remaining_die = d2
                                    elif distance == d2:
                                        remaining_die = d1
                            
                            # If we couldn't determine, check which die can still be used
                            # Use single_die_moves to check for moves with just one die (not as doubles)
                            if remaining_die is None:
                                for test_die in [d1, d2]:
                                    try:
                                        test_steps = rules.single_die_moves(self.state, test_die)
                                        if test_steps:
                                            remaining_die = test_die
                                            break
                                    except:
                                        continue
                            
                            # Check if there are any legal moves with the remaining die
                            # Use single_die_moves instead of legal_actions to avoid treating it as doubles
                            if remaining_die is not None:
                                try:
                                    remaining_steps = rules.single_die_moves(self.state, remaining_die)
                                    if not remaining_steps:
                                        # No more legal moves - turn is over
                                        if hasattr(self.state, 'record_turn'):
                                            self.state.record_turn(self.current_dice, action)
                                        self.state.next_turn()
                                        self._reset_selection()
                                        print("DEBUG: AI - no more legal moves with remaining die, turn ended")
                                    else:
                                        # Continue with remaining die
                                        # Store as tuple for consistency, but we'll use single_die_moves for checking
                                        self.current_dice = (remaining_die, remaining_die)
                                        print(f"DEBUG: AI - one die used, continuing with die {remaining_die}")
                                        # Don't advance turn or reset - let AI continue with remaining die
                                except Exception as e:
                                    print(f"Error checking remaining moves: {e}")
                                    # If we can't check, assume turn is over to be safe
                                    if hasattr(self.state, 'record_turn'):
                                        self.state.record_turn(self.current_dice, action)
                                    self.state.next_turn()
                                    self._reset_selection()
                            else:
                                # Couldn't determine remaining die - end turn to be safe
                                if hasattr(self.state, 'record_turn'):
                                    self.state.record_turn(self.current_dice, action)
                                self.state.next_turn()
                                self._reset_selection()
                                print("DEBUG: AI - couldn't determine remaining die, ending turn")
                        
                        # Small delay to show the move
                        pygame.time.wait(500)
                    except Exception as e:
                        print(f"Error applying AI action: {e}")
                        import traceback
                        traceback.print_exc()
                        # On error, advance turn to avoid getting stuck
                        self.state.next_turn()
                        self._reset_selection()
                else:
                    # No legal moves - record the pass before advancing turn
                    print("AI has no legal moves, passing turn")
                    if hasattr(self.state, 'record_turn'):
                        self.state.record_turn(self.current_dice, action=None)
                    # Advance turn
                    self.state.next_turn()
                    self._reset_selection()
                
                self.ai_thinking = False
        except Exception as e:
            print(f"Error in AI turn handler: {e}")
            import traceback
            traceback.print_exc()
            self.ai_thinking = False
    
    def _handle_click(self, pos):
        """Override to only allow human clicks on human's turn."""
        if self.state.current_player != self.human_player:
            return False
        
        return super()._handle_click(pos)
    
    def draw(self):
        """Override draw to show AI status."""
        # Call parent's draw method which handles the main rendering
        super().draw()
        
        # Add AI-specific status on top
        if self.ai_thinking:
            thinking_text = f"{self.ai_name} is thinking..."
            text = self.font.render(thinking_text, True, (255, 255, 0))
            # Draw with background for visibility
            text_rect = text.get_rect()
            bg_rect = pygame.Rect(BOARD_WIDTH - 220, 8, text_rect.width + 10, text_rect.height + 4)
            pygame.draw.rect(self.screen, (40, 40, 40), bg_rect)
            pygame.draw.rect(self.screen, (255, 255, 0), bg_rect, 2)
            self.screen.blit(text, (BOARD_WIDTH - 210, 10))
        
        if self.state.current_player != self.human_player and not self.ai_thinking:
            ai_turn_text = f"{self.ai_name}'s turn - waiting for move..."
            text = self.font.render(ai_turn_text, True, (255, 200, 0))
            # Draw with background for visibility
            text_rect = text.get_rect()
            bg_rect = pygame.Rect(BOARD_WIDTH - 270, 8, text_rect.width + 10, text_rect.height + 4)
            pygame.draw.rect(self.screen, (40, 40, 40), bg_rect)
            pygame.draw.rect(self.screen, (255, 200, 0), bg_rect, 2)
            self.screen.blit(text, (BOARD_WIDTH - 260, 10))
        
        # Show AI type in top-left corner
        ai_type_text = f"Opponent: {self.ai_name}"
        text = self.small_font.render(ai_type_text, True, (200, 200, 200))
        self.screen.blit(text, (10, BOARD_HEIGHT - 30))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop with AI support."""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        try:
                            self._handle_click(event.pos)
                        except Exception as e:
                            print(f"Error handling click: {e}")
                            import traceback
                            traceback.print_exc()
            
            # Check if human player has dice but no legal moves - auto-pass
            # Only check once per turn (when dice are set but no selection made)
            if (self.state.current_player == self.human_player and 
                self.current_dice and 
                not self.selected_point and 
                not self.selected_bar and
                not hasattr(self, '_checked_no_moves_this_turn')):
                try:
                    legal_actions_list = rules.legal_actions(self.state, self.current_dice)
                    if not legal_actions_list:
                        # No legal moves - automatically pass turn
                        print("DEBUG: No legal moves for human player, auto-passing")
                        if hasattr(self.state, 'record_turn'):
                            self.state.record_turn(self.current_dice, action=None)
                        if hasattr(self.state, 'next_turn'):
                            self.state.next_turn()
                        self._reset_selection()
                        # Delete the flag so it can be checked again next turn
                        if hasattr(self, '_checked_no_moves_this_turn'):
                            delattr(self, '_checked_no_moves_this_turn')
                    else:
                        # Mark that we've checked this turn
                        self._checked_no_moves_this_turn = True
                except Exception as e:
                    # If we can't check, continue - don't block the game
                    pass
            elif not self.current_dice:
                # Clear flag when dice are cleared (new turn) - delete the attribute
                if hasattr(self, '_checked_no_moves_this_turn'):
                    delattr(self, '_checked_no_moves_this_turn')
            
            # Handle AI turn
            self._handle_ai_turn()
            
            # Check for game over
            if self.state.is_game_over():
                winner = self.state.winner()
                winner_text = f"Player {1 if winner == PLAYER_1 else 2} wins!"
                print(winner_text)
                
                # Display winner message on screen for a few seconds
                self.draw()
                winner_surface = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
                winner_surface.set_alpha(200)
                winner_surface.fill((0, 0, 0))
                self.screen.blit(winner_surface, (0, 0))
                
                winner_display = self.font.render(winner_text, True, (255, 255, 0))
                winner_rect = winner_display.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2))
                self.screen.blit(winner_display, winner_rect)
                
                pygame.display.flip()
                
                # Wait a few seconds to show the winner, then exit
                pygame.time.wait(3000)
                running = False
                break
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()


def create_ai_agent(ai_type: str, depth: int = 2):
    """Create an AI agent based on the specified type.
    
    Returns:
        tuple: (agent, name) where name is a display name for the AI
    """
    ai_type_lower = ai_type.lower()
    if ai_type_lower == "random":
        return RandomAgent(), "Random AI"
    elif ai_type_lower == "heuristic":
        return HeuristicAgent(), "Heuristic AI"
    elif ai_type_lower == "expectimax":
        return ExpectimaxAgent(player=PLAYER_2, config=ExpectimaxConfig(depth=depth)), f"Expectimax AI (depth {depth})"
    else:
        raise ValueError(f"Unknown AI type: {ai_type}. Choose from: random, heuristic, expectimax")


def main():
    """Start a human vs AI game."""
    parser = argparse.ArgumentParser(description="Play Backgammon against an AI opponent")
    parser.add_argument(
        "--ai",
        type=str,
        default="heuristic",
        choices=["random", "heuristic", "expectimax"],
        help="Type of AI opponent (default: heuristic)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Depth for expectimax AI (default: 1, higher = smarter but MUCH slower - depth 2 can take 60+ seconds per move)"
    )
    parser.add_argument(
        "--human-player",
        type=int,
        default=1,
        choices=[1, 2],
        help="Which player you want to be (1 or 2, default: 1)"
    )
    
    args = parser.parse_args()
    
    state = GameState.initial()
    
    # Create AI agent
    try:
        ai, ai_name = create_ai_agent(args.ai, args.depth)
        print(f"Playing against {ai_name}")
    except Exception as e:
        print(f"Error creating AI agent: {e}")
        print("Falling back to HeuristicAgent")
        ai = HeuristicAgent()
        ai_name = "Heuristic AI"
    
    human_player = PLAYER_1 if args.human_player == 1 else PLAYER_2
    
    ui = HumanVsAIGraphicalUI(state, ai, human_player=human_player, ai_name=ai_name)
    ui.run()


if __name__ == "__main__":
    main()

