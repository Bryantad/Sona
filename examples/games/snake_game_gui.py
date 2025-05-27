#!/usr/bin/env python3
"""
Snake Game GUI - Fixed Version
A GUI version of the snake game that runs in its own window.
This complements the Sona implementation but uses Python with Tkinter
to provide a visual interface.
"""

import tkinter as tk
import random

# Game constants
BOARD_WIDTH = 20
BOARD_HEIGHT = 15
CELL_SIZE = 30
GAME_SPEED = 150  # milliseconds

class SnakeGameGUI:
    def __init__(self, master):
        self.master = master
        master.title("Snake Game - Sona v0.5.1 GUI")
        master.configure(bg="#333333")
        
        # Add a title label
        self.title_label = tk.Label(
            master,
            text="SNAKE GAME",
            font=("Arial", 20, "bold"),
            bg="#333333",
            fg="#22FF22"
        )
        self.title_label.pack(pady=10)
        
        # Frame for the canvas with a border
        self.frame = tk.Frame(master, bd=3, relief=tk.RIDGE, bg="#222222")
        self.frame.pack(pady=10)
        
        # Set up the canvas
        self.canvas = tk.Canvas(
            self.frame, 
            width=BOARD_WIDTH * CELL_SIZE, 
            height=BOARD_HEIGHT * CELL_SIZE,
            bg="black",
            bd=0
        )
        self.canvas.pack()
        
        # Score label with styling
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        self.score_label = tk.Label(
            master, 
            textvariable=self.score_var, 
            font=("Arial", 16, "bold"),
            bg="#333333",
            fg="#FFFFFF"
        )
        self.score_label.pack(pady=5)
        
        # Instructions label
        self.instructions = tk.Label(
            master,
            text="Use arrow keys to move, Space to restart",
            font=("Arial", 10),
            bg="#333333",
            fg="#CCCCCC"
        )
        self.instructions.pack(pady=5)
        
        # Game state
        self.snake = [[5, 5]]  # Starting position
        self.direction = [1, 0]  # Moving right
        self.food = self.spawn_food()
        self.score = 0
        self.game_over_flag = False
        
        # Bind arrow keys
        master.bind("<Up>", lambda _: self.change_direction(0, -1))
        master.bind("<Down>", lambda _: self.change_direction(0, 1))
        master.bind("<Left>", lambda _: self.change_direction(-1, 0))
        master.bind("<Right>", lambda _: self.change_direction(1, 0))
        master.bind("<space>", self.restart_game)
        master.focus_set()
        
        # Start the game with countdown
        self.start_countdown(3)
    
    def change_direction(self, dx, dy):
        # Prevent 180-degree turns
        if (dx != -self.direction[0] or dy != -self.direction[1]):
            self.direction = [dx, dy]
    
    def spawn_food(self):
        while True:
            x = random.randint(0, BOARD_WIDTH - 1)
            y = random.randint(0, BOARD_HEIGHT - 1)
            
            # Check if food position conflicts with snake
            conflict = False
            for segment in self.snake:
                if segment[0] == x and segment[1] == y:
                    conflict = True
                    break
            
            if not conflict:
                return [x, y]
    
    def start_game(self):
        self.canvas.delete("countdown")
        self.update_game()
    
    def update_game(self):
        if self.game_over_flag:
            return
        
        # Move snake head
        head = self.snake[0]
        new_head = [head[0] + self.direction[0], head[1] + self.direction[1]]
        
        # Check collisions
        if (new_head[0] < 0 or new_head[0] >= BOARD_WIDTH or
            new_head[1] < 0 or new_head[1] >= BOARD_HEIGHT or
            new_head in self.snake[1:]):
            self.game_over()
            return
            
        # Check food
        if new_head[0] == self.food[0] and new_head[1] == self.food[1]:
            # Food eaten - increase score
            self.score += 10
            self.score_var.set(f"Score: {self.score}")
            
            # Flash the score label to highlight score increase
            orig_bg = self.score_label.cget("bg")
            self.score_label.config(bg="#FFFF00", fg="#000000")
            self.master.after(200, lambda: self.score_label.config(bg=orig_bg, fg="#FFFFFF"))
            
            # Add to snake length
            self.snake.insert(0, new_head)
            
            # Speed up the game slightly (min 50ms)
            global GAME_SPEED
            GAME_SPEED = max(50, GAME_SPEED - 2)
            
            # Generate new food
            self.food = self.spawn_food()
        else:
            self.snake.insert(0, new_head)
            self.snake.pop()
        
        # Draw the game
        self.draw_game()
        # Schedule next update
        self.master.after(GAME_SPEED, self.update_game)
    
    def draw_game(self):
        self.canvas.delete("all")
        
        # Draw grid lines (subtle)
        for x in range(0, BOARD_WIDTH * CELL_SIZE, CELL_SIZE):
            self.canvas.create_line(x, 0, x, BOARD_HEIGHT * CELL_SIZE, fill="#111111")
        for y in range(0, BOARD_HEIGHT * CELL_SIZE, CELL_SIZE):
            self.canvas.create_line(0, y, BOARD_WIDTH * CELL_SIZE, y, fill="#111111")
        
        # Draw snake with gradient effect
        for i, segment in enumerate(self.snake):
            x, y = segment
            # Calculate color: gradient from bright green (head) to darker green (tail)
            intensity = max(80, 255 - (i * 10))  # Gradually gets darker
            color = f"#{0:02x}{intensity:02x}{0:02x}"
            
            # Draw with rounded corners for a smoother look
            self.canvas.create_rectangle(
                x * CELL_SIZE + 1, y * CELL_SIZE + 1,
                (x + 1) * CELL_SIZE - 1, (y + 1) * CELL_SIZE - 1,
                fill=color, outline="#004400", width=1, 
                tags="snake"
            )
            
            # Add eyes to the head
            if i == 0:
                # Determine eye positions based on direction
                dx, dy = self.direction
                # Left eye
                eye_l_x = x * CELL_SIZE + CELL_SIZE // 4
                eye_l_y = y * CELL_SIZE + CELL_SIZE // 4
                # Right eye
                eye_r_x = x * CELL_SIZE + 3 * CELL_SIZE // 4
                eye_r_y = y * CELL_SIZE + CELL_SIZE // 4
                
                # Adjust eyes based on direction
                if dy == 1:  # Down
                    eye_l_y = eye_r_y = y * CELL_SIZE + 3 * CELL_SIZE // 4
                elif dx == -1:  # Left
                    eye_l_x = eye_r_x = x * CELL_SIZE + CELL_SIZE // 4
                    eye_l_y = y * CELL_SIZE + CELL_SIZE // 4
                    eye_r_y = y * CELL_SIZE + 3 * CELL_SIZE // 4
                elif dx == 1:  # Right
                    eye_l_x = eye_r_x = x * CELL_SIZE + 3 * CELL_SIZE // 4
                    eye_l_y = y * CELL_SIZE + CELL_SIZE // 4
                    eye_r_y = y * CELL_SIZE + 3 * CELL_SIZE // 4
                
                # Draw the eyes
                self.canvas.create_oval(
                    eye_l_x - 2, eye_l_y - 2, 
                    eye_l_x + 2, eye_l_y + 2,
                    fill="white", outline="black", width=1
                )
                self.canvas.create_oval(
                    eye_r_x - 2, eye_r_y - 2, 
                    eye_r_x + 2, eye_r_y + 2,
                    fill="white", outline="black", width=1
                )
        
        # Draw food with a glow effect
        x, y = self.food
        # Outer glow
        self.canvas.create_oval(
            x * CELL_SIZE - 2, y * CELL_SIZE - 2,
            (x + 1) * CELL_SIZE + 2, (y + 1) * CELL_SIZE + 2,
            fill="", outline="#FF6600", width=2
        )
        # Food item
        self.canvas.create_oval(
            x * CELL_SIZE + 2, y * CELL_SIZE + 2,
            (x + 1) * CELL_SIZE - 2, (y + 1) * CELL_SIZE - 2,
            fill="#FF0000", outline="#AA0000"
        )
    
    def game_over(self):
        self.game_over_flag = True
        
        # Flash the screen red
        def flash_screen(count=0):
            if count >= 4:  # Flash 2 times (4 states)
                self.show_game_over_screen()
                return
            
            if count % 2 == 0:
                # Flash to red
                self.canvas.config(bg="#500")
            else:
                # Flash back to black
                self.canvas.config(bg="black")
            
            self.master.after(200, lambda: flash_screen(count + 1))
        
        flash_screen()
    
    def show_game_over_screen(self):
        # Reset canvas background
        self.canvas.config(bg="black")
        
        # Create semi-transparent overlay
        self.canvas.create_rectangle(
            0, 0, BOARD_WIDTH * CELL_SIZE, BOARD_HEIGHT * CELL_SIZE,
            fill="#000", stipple="gray50"
        )
        
        # Create a frame for the game over text
        self.canvas.create_rectangle(
            BOARD_WIDTH * CELL_SIZE // 2 - 150,
            BOARD_HEIGHT * CELL_SIZE // 2 - 70,
            BOARD_WIDTH * CELL_SIZE // 2 + 150,
            BOARD_HEIGHT * CELL_SIZE // 2 + 100,
            fill="#333", outline="#FFF", width=2
        )
        
        # Game Over text with shadow effect
        self.canvas.create_text(
            BOARD_WIDTH * CELL_SIZE // 2 + 2,
            BOARD_HEIGHT * CELL_SIZE // 2 - 40 + 2,
            text="GAME OVER!",
            fill="#500",
            font=("Arial", 28, "bold")
        )
        self.canvas.create_text(
            BOARD_WIDTH * CELL_SIZE // 2,
            BOARD_HEIGHT * CELL_SIZE // 2 - 40,
            text="GAME OVER!",
            fill="#F00",
            font=("Arial", 28, "bold")
        )
        
        # Score display
        self.canvas.create_text(
            BOARD_WIDTH * CELL_SIZE // 2,
            BOARD_HEIGHT * CELL_SIZE // 2 + 10,
            text=f"Final Score: {self.score}",
            fill="#FFF",
            font=("Arial", 18, "bold")
        )
        
        # Instructions with blinking effect
        self.blink_text(
            BOARD_WIDTH * CELL_SIZE // 2,
            BOARD_HEIGHT * CELL_SIZE // 2 + 60,
            "Press SPACE to play again",
            "#0F0",
            ("Arial", 14)
        )
    
    def blink_text(self, x, y, text, color, font, state=True):
        if self.game_over_flag:
            if state:
                self.canvas.create_text(
                    x, y, text=text, fill=color, font=font, tags="blink_text"
                )
            else:
                self.canvas.delete("blink_text")
            self.master.after(600, lambda: self.blink_text(x, y, text, color, font, not state))
    
    def restart_game(self, event=None):
        if self.game_over_flag:
            # Reset game variables
            self.snake = [[5, 5]]
            self.direction = [1, 0]
            self.food = self.spawn_food()
            self.score = 0
            self.score_var.set("Score: 0")
            self.game_over_flag = False
            
            # Reset game speed
            global GAME_SPEED
            GAME_SPEED = 150
            
            # Clear canvas and show countdown
            self.canvas.delete("all")
            self.canvas.config(bg="black")
            self.start_countdown(3)
    
    def start_countdown(self, count):
        if count > 0:
            self.canvas.delete("countdown")
            self.canvas.create_text(
                BOARD_WIDTH * CELL_SIZE // 2,
                BOARD_HEIGHT * CELL_SIZE // 2,
                text=str(count),
                fill="#FFFFFF",
                font=("Arial", 48, "bold"),
                tags="countdown"
            )
            self.master.after(1000, lambda: self.start_countdown(count - 1))
        else:
            self.canvas.delete("countdown")
            self.canvas.create_text(
                BOARD_WIDTH * CELL_SIZE // 2,
                BOARD_HEIGHT * CELL_SIZE // 2,
                text="GO!",
                fill="#00FF00",
                font=("Arial", 48, "bold"),
                tags="countdown"
            )
            self.master.after(1000, self.start_game)

def main():
    root = tk.Tk()
    root.resizable(False, False)
    game = SnakeGameGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
