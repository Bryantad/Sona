#!/usr/bin/env python3
"""
Sona Snake Game Application - Classic Snake Game
Part of the Sona Application Platform
"""

import random
import time
import tkinter as tk
from enum import Enum
from tkinter import ttk


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class SnakeGameApp:
    """Classic Snake Game with modern features"""
    
    def __init__(self, container: tk.Widget, instance, framework):
        self.container = container
        self.instance = instance
        self.framework = framework
        
        # Game settings
        self.grid_size = 20
        self.canvas_width = 600
        self.canvas_height = 400
        self.grid_width = self.canvas_width // self.grid_size
        self.grid_height = self.canvas_height // self.grid_size
        
        # Game state
        self.game_state = GameState.MENU
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = Direction.RIGHT
        self.food = self.generate_food()
        self.score = 0
        self.high_score = 0
        self.speed = 150  # milliseconds
        self.game_loop_id = None
        
        # UI setup
        self.create_interface()
        self.setup_keyboard_bindings()
        self.load_high_score()
        
        # Update framework heartbeat
        self.update_heartbeat()
    
    def create_interface(self):
        """Create the snake game interface"""
        main_frame = ttk.Frame(self.container, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Game info panel
        self.create_info_panel(main_frame)
        
        # Game canvas
        self.create_game_canvas(main_frame)
        
        # Control panel
        self.create_control_panel(main_frame)
        
        # Status bar
        if self.instance.capabilities.has_statusbar:
            self.create_status_bar(main_frame)
    
    def create_info_panel(self, parent):
        """Create game information panel"""
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Score display
        score_frame = ttk.LabelFrame(info_frame, text="Score", padding=5)
        score_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.score_var = tk.StringVar(value="0")
        score_label = ttk.Label(score_frame, textvariable=self.score_var,
                              font=('Arial', 16, 'bold'))
        score_label.pack()
        
        # High score display
        high_score_frame = ttk.LabelFrame(info_frame, text="High Score", padding=5)
        high_score_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        self.high_score_var = tk.StringVar(value="0")
        high_score_label = ttk.Label(high_score_frame, textvariable=self.high_score_var,
                                   font=('Arial', 16, 'bold'), foreground='gold')
        high_score_label.pack()
        
        # Level/Speed display
        level_frame = ttk.LabelFrame(info_frame, text="Level", padding=5)
        level_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        self.level_var = tk.StringVar(value="1")
        level_label = ttk.Label(level_frame, textvariable=self.level_var,
                              font=('Arial', 16, 'bold'))
        level_label.pack()
    
    def create_game_canvas(self, parent):
        """Create the game playing area"""
        canvas_frame = ttk.LabelFrame(parent, text="Game Area", padding=5)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Game canvas
        self.canvas = tk.Canvas(canvas_frame, 
                              width=self.canvas_width, 
                              height=self.canvas_height,
                              bg='black', highlightthickness=0)
        self.canvas.pack()
        
        # Initial menu display
        self.show_menu()
    
    def create_control_panel(self, parent):
        """Create game control buttons"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Game control buttons
        self.start_button = ttk.Button(control_frame, text="Start Game",
                                     command=self.start_game)
        self.start_button.pack(side=tk.LEFT)
        
        self.pause_button = ttk.Button(control_frame, text="Pause",
                                     command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=(5, 0))
        
        self.reset_button = ttk.Button(control_frame, text="Reset",
                                     command=self.reset_game)
        self.reset_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Difficulty selector
        ttk.Label(control_frame, text="Difficulty:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.difficulty_var = tk.StringVar(value="Normal")
        difficulty_combo = ttk.Combobox(control_frame, textvariable=self.difficulty_var,
                                      values=["Easy", "Normal", "Hard", "Expert"],
                                      state="readonly", width=10)
        difficulty_combo.pack(side=tk.LEFT)
        difficulty_combo.bind('<<ComboboxSelected>>', self.on_difficulty_change)
        
        # Direction buttons (for mobile-like experience)
        direction_frame = ttk.LabelFrame(control_frame, text="Controls", padding=5)
        direction_frame.pack(side=tk.RIGHT)
        
        # Arrow button layout
        ttk.Button(direction_frame, text="↑", width=3,
                  command=lambda: self.change_direction(Direction.UP)).grid(row=0, column=1)
        ttk.Button(direction_frame, text="←", width=3,
                  command=lambda: self.change_direction(Direction.LEFT)).grid(row=1, column=0)
        ttk.Button(direction_frame, text="→", width=3,
                  command=lambda: self.change_direction(Direction.RIGHT)).grid(row=1, column=2)
        ttk.Button(direction_frame, text="↓", width=3,
                  command=lambda: self.change_direction(Direction.DOWN)).grid(row=2, column=1)
    
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Press Start to begin")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Game state indicator
        self.state_var = tk.StringVar(value="Menu")
        ttk.Label(status_frame, textvariable=self.state_var).pack(side=tk.RIGHT)
    
    def setup_keyboard_bindings(self):
        """Setup keyboard controls"""
        # Get the main window for key bindings
        widget = self.container
        while widget.master:
            widget = widget.master
        
        widget.bind('<Key-Up>', lambda e: self.change_direction(Direction.UP))
        widget.bind('<Key-Down>', lambda e: self.change_direction(Direction.DOWN))
        widget.bind('<Key-Left>', lambda e: self.change_direction(Direction.LEFT))
        widget.bind('<Key-Right>', lambda e: self.change_direction(Direction.RIGHT))
        
        # Alternative keys
        widget.bind('<Key-w>', lambda e: self.change_direction(Direction.UP))
        widget.bind('<Key-s>', lambda e: self.change_direction(Direction.DOWN))
        widget.bind('<Key-a>', lambda e: self.change_direction(Direction.LEFT))
        widget.bind('<Key-d>', lambda e: self.change_direction(Direction.RIGHT))
        
        # Game controls
        widget.bind('<Key-space>', lambda e: self.toggle_pause())
        widget.bind('<Key-Return>', lambda e: self.start_game())
        widget.bind('<Key-Escape>', lambda e: self.reset_game())
        
        # Focus the widget to receive key events
        widget.focus_set()
    
    def show_menu(self):
        """Display the game menu"""
        self.canvas.delete("all")
        
        # Title
        self.canvas.create_text(self.canvas_width // 2, 100,
                              text="SNAKE GAME", fill="white",
                              font=('Arial', 24, 'bold'))
        
        # Instructions
        instructions = [
            "Use arrow keys or WASD to move",
            "Press SPACE to pause",
            "Press ENTER to start",
            "Eat the red food to grow and score points!"
        ]
        
        for i, instruction in enumerate(instructions):
            self.canvas.create_text(self.canvas_width // 2, 180 + i * 25,
                                  text=instruction, fill="lightgray",
                                  font=('Arial', 12))
        
        # High score display
        if self.high_score > 0:
            self.canvas.create_text(self.canvas_width // 2, 320,
                                  text=f"High Score: {self.high_score}",
                                  fill="gold", font=('Arial', 16, 'bold'))
    
    def start_game(self):
        """Start a new game"""
        self.game_state = GameState.PLAYING
        self.reset_snake()
        self.score = 0
        self.update_displays()
        
        # Enable/disable buttons
        self.start_button.configure(state=tk.DISABLED)
        self.pause_button.configure(state=tk.NORMAL)
        
        self.status_var.set("Game in progress - Use arrow keys to move")
        self.state_var.set("Playing")
        
        # Start game loop
        self.game_loop()
        self.update_heartbeat()
    
    def toggle_pause(self):
        """Toggle game pause"""
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            self.pause_button.configure(text="Resume")
            self.status_var.set("Game paused - Press SPACE or Resume to continue")
            self.state_var.set("Paused")
            
            if self.game_loop_id:
                self.container.after_cancel(self.game_loop_id)
                
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            self.pause_button.configure(text="Pause")
            self.status_var.set("Game resumed")
            self.state_var.set("Playing")
            self.game_loop()
        
        self.update_heartbeat()
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.game_state = GameState.MENU
        
        if self.game_loop_id:
            self.container.after_cancel(self.game_loop_id)
        
        self.reset_snake()
        self.score = 0
        self.update_displays()
        self.show_menu()
        
        # Reset buttons
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.DISABLED, text="Pause")
        
        self.status_var.set("Game reset - Press Start to begin")
        self.state_var.set("Menu")
        self.update_heartbeat()
    
    def game_over(self):
        """Handle game over"""
        self.game_state = GameState.GAME_OVER
        
        if self.game_loop_id:
            self.container.after_cancel(self.game_loop_id)
        
        # Check for high score
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
            self.status_var.set("NEW HIGH SCORE!")
        else:
            self.status_var.set("Game Over")
        
        self.state_var.set("Game Over")
        
        # Reset buttons
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.DISABLED)
        
        # Show game over screen
        self.show_game_over()
        self.update_displays()
        self.update_heartbeat()
    
    def show_game_over(self):
        """Display game over screen"""
        # Game over text
        self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2 - 40,
                              text="GAME OVER", fill="red",
                              font=('Arial', 20, 'bold'))
        
        self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                              text=f"Score: {self.score}", fill="white",
                              font=('Arial', 16))
        
        if self.score == self.high_score:
            self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2 + 30,
                                  text="NEW HIGH SCORE!", fill="gold",
                                  font=('Arial', 14, 'bold'))
        
        self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2 + 60,
                              text="Press ENTER to play again", fill="lightgray",
                              font=('Arial', 12))
    
    def game_loop(self):
        """Main game loop"""
        if self.game_state != GameState.PLAYING:
            return
        
        # Move snake
        head = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head[0] + dx, head[1] + dy)
        
        # Check collisions
        if self.check_collision(new_head):
            self.game_over()
            return
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check food collision
        if new_head == self.food:
            self.score += 10
            self.food = self.generate_food()
            self.update_level()
        else:
            # Remove tail if no food eaten
            self.snake.pop()
        
        # Update display
        self.draw_game()
        self.update_displays()
        
        # Schedule next frame
        self.game_loop_id = self.container.after(self.speed, self.game_loop)
        self.update_heartbeat()
    
    def change_direction(self, new_direction: Direction):
        """Change snake direction"""
        if self.game_state != GameState.PLAYING:
            return
        
        # Prevent reversing into self
        current_dx, current_dy = self.direction.value
        new_dx, new_dy = new_direction.value
        
        if (current_dx, current_dy) != (-new_dx, -new_dy):
            self.direction = new_direction
    
    def check_collision(self, position):
        """Check if position collides with walls or snake"""
        x, y = position
        
        # Wall collision
        if x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height:
            return True
        
        # Self collision
        if position in self.snake:
            return True
        
        return False
    
    def generate_food(self):
        """Generate food at random position"""
        while True:
            food_pos = (random.randint(0, self.grid_width - 1),
                       random.randint(0, self.grid_height - 1))
            if food_pos not in self.snake:
                return food_pos
    
    def draw_game(self):
        """Draw the current game state"""
        self.canvas.delete("all")
        
        # Draw snake
        for i, (x, y) in enumerate(self.snake):
            x1 = x * self.grid_size
            y1 = y * self.grid_size
            x2 = x1 + self.grid_size
            y2 = y1 + self.grid_size
            
            # Head is different color
            color = "lime" if i == 0 else "green"
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="darkgreen")
        
        # Draw food
        fx, fy = self.food
        fx1 = fx * self.grid_size
        fy1 = fy * self.grid_size
        fx2 = fx1 + self.grid_size
        fy2 = fy1 + self.grid_size
        self.canvas.create_oval(fx1, fy1, fx2, fy2, fill="red", outline="darkred")
        
        # Draw grid (optional)
        self.draw_grid()
    
    def draw_grid(self):
        """Draw grid lines"""
        # Vertical lines
        for i in range(0, self.canvas_width, self.grid_size):
            self.canvas.create_line(i, 0, i, self.canvas_height, fill="gray", width=1)
        
        # Horizontal lines
        for i in range(0, self.canvas_height, self.grid_size):
            self.canvas.create_line(0, i, self.canvas_width, i, fill="gray", width=1)
    
    def reset_snake(self):
        """Reset snake to initial position"""
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = Direction.RIGHT
        self.food = self.generate_food()
    
    def update_displays(self):
        """Update all display elements"""
        self.score_var.set(str(self.score))
        self.high_score_var.set(str(self.high_score))
        self.level_var.set(str(self.get_level()))
    
    def update_level(self):
        """Update game speed based on score"""
        level = self.get_level()
        base_speed = {"Easy": 200, "Normal": 150, "Hard": 100, "Expert": 50}
        difficulty = self.difficulty_var.get()
        
        self.speed = max(50, base_speed[difficulty] - (level - 1) * 10)
    
    def get_level(self):
        """Calculate current level based on score"""
        return (self.score // 50) + 1
    
    def on_difficulty_change(self, event):
        """Handle difficulty change"""
        self.update_level()
        if self.game_state == GameState.PLAYING:
            self.status_var.set(f"Difficulty changed to {self.difficulty_var.get()}")
    
    def load_high_score(self):
        """Load high score from file"""
        try:
            with open("snake_high_score.txt", "r") as f:
                self.high_score = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            self.high_score = 0
    
    def save_high_score(self):
        """Save high score to file"""
        try:
            with open("snake_high_score.txt", "w") as f:
                f.write(str(self.high_score))
        except Exception as e:
            print(f"Could not save high score: {e}")
    
    def update_heartbeat(self):
        """Update framework heartbeat"""
        if self.instance:
            self.instance.last_heartbeat = time.time()


# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Snake Game Test")
    root.geometry("700x600")
    
    # Mock instance
    class MockInstance:
        def __init__(self):
            self.last_heartbeat = time.time()
            self.capabilities = type('obj', (object,), {
                'has_statusbar': True
            })()
    
    instance = MockInstance()
    app = SnakeGameApp(root, instance, None)
    
    root.mainloop()
