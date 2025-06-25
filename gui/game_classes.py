import tkinter as tk
from tkinter import ttk, messagebox, font
import random
import time
import math
import json
import os
from pathlib import Path
from datetime import datetime

# Import shared game assets if available
try:
    from gui.game_assets import (
        SoundManager, 
        LevelGenerator, 
        ColorThemes, 
        ScoreManager,
        ParticleSystem
    )
    ASSETS_AVAILABLE = True
except ImportError:
    ASSETS_AVAILABLE = False

# Base application class that all games will inherit from
class EmbeddedApplication:
    """Base class for embedded GUI applications"""
    def __init__(self, parent, example_name):
        self.parent = parent
        self.example_name = example_name
        
        # Common game state variables
        self.running = False
        self.paused = False
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.lives = 3
        self.frame = None
        self.canvas = None
        self.timer_id = None
        self.update_speed = 50  # milliseconds
        
        # Persistance settings
        self.save_dir = Path(os.path.expanduser("~/.sona/game_data"))
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize game systems if available
        self.initialize_game_systems()
        
        # Load high scores if available
        self.load_highscore()
        
    def initialize_game_systems(self):
        """Initialize shared game systems"""
        # Set default themes
        self.colors = {
            "background": "#202020",
            "text": "#FFFFFF", 
            "highlight": "#4CAF50",
            "accent": "#2196F3", 
            "warning": "#FFC107",
            "danger": "#F44336",
            "success": "#8BC34A"
        }
        
        # Initialize systems if available from game_assets
        if ASSETS_AVAILABLE:
            # Initialize sound system
            self.sound = SoundManager()
            
            # Initialize score manager
            game_id = self.example_name.replace('.sona', '')
            self.score_manager = ScoreManager(game_id)
            self.high_score = self.score_manager.get_high_score()
            
            # Get default theme
            self.colors = ColorThemes.get_theme("default")
            
            # These will be initialized when canvas is available
            self.particles = None
            self.level_generator = None
        else:
            self.sound = None
            self.score_manager = None
            self.particles = None
            self.level_generator = None
        
    def create_gui(self, container):
        """Create the GUI elements"""
        frame = ttk.Frame(container)
        ttk.Label(frame, text="Base Application").pack()
        return frame
    
    def start(self):
        """Start the application"""
        if not self.running:
            self.running = True
            self.schedule_update()
    
    def stop(self):
        """Stop the application"""
        self.running = False
        if self.timer_id:
            if self.frame:
                self.frame.after_cancel(self.timer_id)
            self.timer_id = None
        # Save high score when stopping
        self.save_highscore()
    
    def pause(self):
        """Pause the application"""
        self.paused = not self.paused
        return self.paused
    
    def schedule_update(self):
        """Schedule the next update"""
        if self.running and self.frame:
            self.timer_id = self.frame.after(self.update_speed, self.update_wrapper)
    
    def update_wrapper(self):
        """Wrapper for update method to handle scheduling and exceptions"""
        if not self.running:
            return
        
        if not self.paused:
            try:
                self.update()
            except Exception as e:
                print(f"Error in {self.__class__.__name__} update: {e}")
        
        self.schedule_update()
    
    def update(self):
        """Update the application state - to be overridden by subclasses"""
        pass
    
    def update_score(self, points):
        """Update the score by adding points"""
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
    
    def save_highscore(self):
        """Save the high score to a json file"""
        save_file = self.save_dir / f"{self.example_name.replace('.sona', '')}_data.json"
        try:
            data = {'high_score': self.high_score}
            with open(save_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save high score: {e}")
    
    def load_highscore(self):
        """Load the high score from a json file"""
        save_file = self.save_dir / f"{self.example_name.replace('.sona', '')}_data.json"
        try:
            if save_file.exists():
                with open(save_file, 'r') as f:
                    data = json.load(f)
                    self.high_score = data.get('high_score', 0)
        except Exception as e:
            print(f"Failed to load high score: {e}")
    
    def reset(self):
        """Reset the game state"""
        self.score = 0
        self.level = 1
        self.lives = 3
    
    def on_key_press(self, event):
        """Handle key press events - to be overridden by subclasses"""
        pass
    
    def on_key_release(self, event):
        """Handle key release events - to be overridden by subclasses"""
        pass
    
    def calculate_difficulty(self):
        """Calculate difficulty based on score and level"""
        # Higher difficulty means more challenging gameplay
        return min(0.1 + (self.level * 0.05) + (self.score / 1000) * 0.1, 1.0)


class VisualNovelApp(EmbeddedApplication):
    """Visual Novel style game with branching storylines"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.current_scene = 0
        self.character_stats = {
            "trust": 50,
            "affection": 50,
            "knowledge": 0
        }
        self.flags = {
            "met_professor": False,
            "found_clue": False,
            "solved_puzzle": False,
            "ending_path": "neutral"
        }
        self.background_images = {}
        self.character_images = {}
        
        # Story content - scenes, dialogues, choices
        self.story = [
            {
                "scene_id": 0,
                "title": "Mysterious Beginning",
                "background": "campus",
                "character": "protagonist",
                "text": "It's your first day at the Academy of Digital Arts & Sciences. " +
                        "The campus is buzzing with activity as students rush to their classes. " +
                        "You look down at your schedule, unsure where to go first.",
                "choices": [
                    {"text": "Head to the Computer Science building", "next_scene": 1},
                    {"text": "Check out the Library", "next_scene": 2}
                ]
            },
            {
                "scene_id": 1,
                "title": "The Professor",
                "background": "lab",
                "character": "professor",
                "text": "You enter the Computer Science building and find Professor Turing waiting. " +
                        "'Ah, you must be the new student! I've been expecting you. " +
                        "I have a special project that might interest someone with your skills.'",
                "choices": [
                    {"text": "Accept the project offer", "next_scene": 3, 
                     "effects": {"trust": 10, "flags": {"met_professor": True}}},
                    {"text": "Politely decline for now", "next_scene": 2,
                     "effects": {"trust": -5}}
                ]
            },
            {
                "scene_id": 2,
                "title": "The Library",
                "background": "library",
                "character": "librarian",
                "text": "The library is vast and quiet. As you browse the shelves, " +
                        "you notice a book that seems out of place. The librarian approaches you. " +
                        "'Interesting choice. That book contains secrets few students discover.'",
                "choices": [
                    {"text": "Ask about the book", "next_scene": 4,
                     "effects": {"knowledge": 10}},
                    {"text": "Thank her and head to class", "next_scene": 5}
                ]
            },
            # More scenes would be defined here
        ]
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        self.title_label = ttk.Label(title_frame, text="📖 Visual Novel",
                                     font=('Arial', 16, 'bold'))
        self.title_label.pack(side='left')
        
        # Status indicators
        status_frame = ttk.Frame(title_frame)
        status_frame.pack(side='right')
        
        self.trust_var = tk.StringVar(value="Trust: 50%")
        trust_label = ttk.Label(status_frame, textvariable=self.trust_var)
        trust_label.pack(side='top')
        
        self.affection_var = tk.StringVar(value="Affection: 50%")
        affection_label = ttk.Label(status_frame, textvariable=self.affection_var)
        affection_label.pack(side='top')
        
        # Canvas for visual elements
        self.canvas = tk.Canvas(self.frame, width=500, height=250, 
                               bg='#1a1a2e', highlightthickness=0)
        self.canvas.pack(pady=(0, 10))
        
        # Create character and background placeholders
        self.setup_visuals()
        
        # Text area for story
        self.text_area = tk.Text(self.frame, height=8, wrap=tk.WORD,
                                font=('Segoe UI', 11),
                                bg='#000022', fg='white',
                                padx=10, pady=10)
        self.text_area.pack(fill='x', pady=(0, 10))
        self.text_area.insert(tk.END, "Welcome to Sona Visual Novel!\n\n" +
                             "This is an interactive story where your choices " +
                             "affect the outcome.")
        self.text_area.config(state='disabled')
        
        # Choices buttons
        self.choices_frame = ttk.Frame(self.frame)
        self.choices_frame.pack(fill='x')
        
        self.choice_buttons = []
        for i in range(3):  # Support up to 3 choices
            btn = ttk.Button(self.choices_frame, text=f"Choice {i+1}")
            if i < 2:  # Only show the first two initially
                btn.pack(fill='x', pady=(0, 5))
            self.choice_buttons.append(btn)
        
        # Control buttons
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', pady=(10, 0))
        
        self.start_btn = ttk.Button(control_frame, text="Start Story",
                                   command=self.start_story)
        self.start_btn.pack(side='left', padx=(0, 5))
        
        self.reset_btn = ttk.Button(control_frame, text="Reset",
                                   command=self.reset_story)
        self.reset_btn.pack(side='left')
        
        return self.frame
    
    def setup_visuals(self):
        """Setup visual elements of the game"""
        # Background - campus scene
        self.canvas.create_rectangle(0, 0, 500, 250, fill="#87CEEB", outline="")  # Sky
        self.canvas.create_rectangle(0, 150, 500, 250, fill="#228B22", outline="")  # Grass
        
        # Building
        self.canvas.create_rectangle(50, 50, 200, 150, fill="#CD853F", outline="black")
        self.canvas.create_rectangle(90, 100, 120, 150, fill="#8B4513", outline="black")  # Door
        
        # Character - placeholder
        self.character_id = self.canvas.create_oval(350, 80, 400, 130, 
                                                  fill="#4682B4", outline='white')
        self.canvas.create_rectangle(360, 130, 390, 200, 
                                    fill="#4682B4", outline='white')
        self.character_name = self.canvas.create_text(375, 220, 
                                                     text="Character", 
                                                     fill='white',
                                                     font=('Arial', 12, 'bold'))
    
    def start_story(self):
        """Start the visual novel with intro scene"""
        super().start()
        self.reset_story()
        self.show_scene(0)
    
    def reset_story(self):
        """Reset the story to beginning"""
        super().reset()
        self.current_scene = 0
        self.character_stats = {
            "trust": 50,
            "affection": 50,
            "knowledge": 0
        }
        self.flags = {
            "met_professor": False,
            "found_clue": False,
            "solved_puzzle": False,
            "ending_path": "neutral"
        }
        self.update_stats_display()
    
    def show_scene(self, scene_id):
        """Display the specified scene"""
        # Find the scene by ID
        scene = next((s for s in self.story if s["scene_id"] == scene_id), None)
        if not scene:
            self.show_ending()
            return
            
        # Update scene title
        self.title_label.config(text=f"📖 {scene['title']}")
        
        # Update character and background
        self.update_visuals(scene)
        
        # Update text
        self.text_area.config(state='normal')
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, scene["text"])
        self.text_area.config(state='disabled')
        
        # Update choices
        self.update_choices(scene)
        
        # Save current scene
        self.current_scene = scene_id
    
    def update_visuals(self, scene):
        """Update the visual elements based on the scene"""
        # This would normally load proper images for backgrounds and characters
        # For now, we'll use simple color changes to represent different scenes
        
        # Change background based on scene
        if scene["background"] == "campus":
            self.canvas.itemconfig(self.canvas.find_withtag("all")[0], fill="#87CEEB")  # Blue sky
        elif scene["background"] == "lab":
            self.canvas.itemconfig(self.canvas.find_withtag("all")[0], fill="#696969")  # Dark lab
        elif scene["background"] == "library":
            self.canvas.itemconfig(self.canvas.find_withtag("all")[0], fill="#8B4513")  # Brown library
            
        # Change character based on scene
        if scene["character"] == "protagonist":
            self.canvas.itemconfig(self.character_id, fill="#4682B4")  # Blue
            self.canvas.itemconfig(self.character_name, text="You")
        elif scene["character"] == "professor":
            self.canvas.itemconfig(self.character_id, fill="#A0522D")  # Brown
            self.canvas.itemconfig(self.character_name, text="Professor")
        elif scene["character"] == "librarian":
            self.canvas.itemconfig(self.character_id, fill="#800080")  # Purple
            self.canvas.itemconfig(self.character_name, text="Librarian")
    
    def update_choices(self, scene):
        """Update the choice buttons"""
        # Hide all buttons first
        for btn in self.choice_buttons:
            btn.pack_forget()
        
        # Setup choices from scene
        choices = scene.get("choices", [])
        for i, choice in enumerate(choices):
            if i < len(self.choice_buttons):
                btn = self.choice_buttons[i]
                btn.config(text=choice["text"])
                btn.config(command=lambda c=choice: self.make_choice(c))
                btn.pack(fill='x', pady=(0, 5))
    
    def make_choice(self, choice):
        """Process player's choice"""
        # Apply effects from the choice
        effects = choice.get("effects", {})
        
        # Update character stats
        for stat, change in effects.items():
            if stat in self.character_stats:
                self.character_stats[stat] += change
                # Keep stats in range 0-100
                self.character_stats[stat] = max(0, min(100, self.character_stats[stat]))
        
        # Update flags
        flag_changes = effects.get("flags", {})
        for flag, value in flag_changes.items():
            self.flags[flag] = value
        
        # Update display
        self.update_stats_display()
        
        # Move to next scene
        next_scene = choice.get("next_scene")
        if next_scene is not None:
            self.show_scene(next_scene)
    
    def update_stats_display(self):
        """Update the displayed character stats"""
        self.trust_var.set(f"Trust: {self.character_stats['trust']}%")
        self.affection_var.set(f"Affection: {self.character_stats['affection']}%")
    
    def show_ending(self):
        """Show the appropriate ending based on player choices"""
        ending_text = "Thank you for playing!"
        
        # Determine ending based on stats and flags
        if self.character_stats["trust"] >= 75:
            ending = "You've earned everyone's trust and uncovered the academy's secrets."
            self.flags["ending_path"] = "trust"
        elif self.character_stats["affection"] >= 75:
            ending = "You've formed deep connections that will last a lifetime."
            self.flags["ending_path"] = "affection"
        elif self.character_stats["knowledge"] >= 75:
            ending = "Your pursuit of knowledge has led to amazing discoveries."
            self.flags["ending_path"] = "knowledge"
        else:
            ending = "You completed your first year with a typical student experience."
            self.flags["ending_path"] = "neutral"
        
        # Display ending
        self.text_area.config(state='normal')
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, f"{ending_text}\n\n{ending}")
        self.text_area.config(state='disabled')
        
        # Clear choices
        for btn in self.choice_buttons:
            btn.pack_forget()
        
        # Add replay option
        self.choice_buttons[0].config(text="Play Again", command=self.start_story)
        self.choice_buttons[0].pack(fill='x')
    
    def start(self):
        """Start the application"""
        super().start()
    
    def stop(self):
        """Stop the application"""
        super().stop()
    
    def update(self):
        """Update not needed for this app as it's event-driven"""
        pass


class EndlessRunnerApp(EmbeddedApplication):
    """Endless Runner Game with obstacles and score tracking"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.canvas = None
        self.player = None
        self.ground = None
        self.obstacles = []
        self.coins = []
        self.clouds = []
        self.background_elements = []
        self.score_text = None
        
        # Game physics
        self.gravity = 0.5
        self.jump_strength = -10
        self.obstacle_speed = 5
        self.player_velocity = 0
        self.player_y = 220
        self.is_jumping = False
        
        # Game settings
        self.spawn_rate = 1500  # ms between obstacle spawns
        self.next_spawn = 0
        self.next_coin_spawn = 0
        self.coin_spawn_rate = 2500  # ms between coin spawns
        self.distance = 0
        self.game_over = False
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="🏃 Endless Runner", 
                        font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        self.score_var = tk.StringVar(value="Score: 0")
        score_label = ttk.Label(title_frame, textvariable=self.score_var,
                            font=('Arial', 12))
        score_label.pack(side='right')
        
        self.highscore_var = tk.StringVar(value=f"Best: {self.high_score}")
        highscore_label = ttk.Label(title_frame, textvariable=self.highscore_var,
                                  font=('Arial', 12))
        highscore_label.pack(side='right', padx=(0, 10))
        
        # Game canvas
        self.canvas = tk.Canvas(self.frame, width=500, height=300, 
                            bg='#87CEEB', highlightthickness=2)
        self.canvas.pack(pady=(0, 10))
        
        # Initial game setup
        self.setup_game_elements()
        
        # Control buttons
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        self.start_btn = ttk.Button(control_frame, text="Start", 
                                   command=self.start_game)
        self.start_btn.pack(side='left', padx=(0, 5))
        
        self.reset_btn = ttk.Button(control_frame, text="Reset", 
                                   command=self.reset_game)
        self.reset_btn.pack(side='left')
        
        # Instructions
        instructions = ttk.Label(self.frame, 
                              text="Press SPACE to jump | Avoid obstacles and collect coins")
        instructions.pack(pady=(10, 0))
        
        # Bind keyboard events
        self.canvas.focus_set()
        self.canvas.bind("<space>", self.jump)
        self.canvas.bind("<KeyPress-space>", self.jump)
        
        return self.frame
    
    def setup_game_elements(self):
        """Initialize the game elements"""
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw background
        self.ground = self.canvas.create_rectangle(
            0, 250, 500, 300, fill='#8B4513', outline='')  # Ground
        self.canvas.create_rectangle(
            0, 250, 500, 255, fill='#32CD32', outline='')  # Grass top
        
        # Create clouds
        for i in range(3):
            x = random.randint(50, 450)
            y = random.randint(30, 100)
            cloud = self.create_cloud(x, y)
            self.clouds.append(cloud)
        
        # Create player
        self.player = self.canvas.create_rectangle(
            50, 220, 80, 250, fill='#4682B4', outline='black')
        
        # Create start message
        self.message_box = self.canvas.create_rectangle(
            100, 100, 400, 180, fill='#000033', outline='#4682B4', width=2)
        self.message_title = self.canvas.create_text(
            250, 130, text="Endless Runner", 
            fill='#FFD700', font=('Arial', 20, 'bold'))
        self.message_text = self.canvas.create_text(
            250, 160, text="Press START to begin\nSPACE to jump", 
            fill='white', font=('Arial', 12))
        
        # Score display on canvas
        self.score_text = self.canvas.create_text(
            250, 30, text="Score: 0", fill='black', font=('Arial', 14, 'bold'))
        
        # Initialize empty lists
        self.obstacles = []
        self.coins = []
        self.background_elements = []
    
    def create_cloud(self, x, y):
        """Create a cloud shape at the given position"""
        # Group of ovals to form a cloud
        cloud_parts = []
        cloud_parts.append(self.canvas.create_oval(
            x, y, x+40, y+20, fill='white', outline=''))
        cloud_parts.append(self.canvas.create_oval(
            x+15, y-10, x+55, y+15, fill='white', outline=''))
        cloud_parts.append(self.canvas.create_oval(
            x+30, y, x+70, y+20, fill='white', outline=''))
        return cloud_parts
    
    def start_game(self):
        """Start the game"""
        # Hide message
        self.canvas.itemconfig(self.message_box, state='hidden')
        self.canvas.itemconfig(self.message_title, state='hidden')
        self.canvas.itemconfig(self.message_text, state='hidden')
        
        # Reset game state
        self.reset_game()
        
        # Give focus to canvas and start game loop
        self.canvas.focus_set()
        super().start()
    
    def reset_game(self):
        """Reset the game to initial state"""
        # Clear obstacles and coins
        for obstacle in self.obstacles:
            self.canvas.delete(obstacle)
        for coin in self.coins:
            self.canvas.delete(coin)
            
        # Reset game variables
        self.obstacles = []
        self.coins = []
        self.player_velocity = 0
        self.player_y = 220
        self.is_jumping = False
        self.score = 0
        self.distance = 0
        self.game_over = False
        self.update_score_display()
        
        # Position player
        self.canvas.coords(self.player, 50, self.player_y, 80, self.player_y + 30)
        
        # Set initial spawn timers
        self.next_spawn = self.update_speed * 3
        self.next_coin_spawn = self.update_speed * 5
        
        # Reset difficulty
        self.obstacle_speed = 5
    
    def jump(self, event=None):
        """Make the player jump"""
        if not self.running:
            return
            
        if not self.is_jumping and not self.game_over:
            self.player_velocity = self.jump_strength
            self.is_jumping = True
    
    def update_score_display(self):
        """Update score displays"""
        self.score_var.set(f"Score: {self.score}")
        self.highscore_var.set(f"Best: {self.high_score}")
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
    
    def spawn_obstacle(self):
        """Spawn a new obstacle"""
        # Determine obstacle type based on random chance
        obstacle_type = random.choice(["cactus", "rock", "bird"])
        
        if obstacle_type == "cactus":
            height = random.randint(20, 40)
            obstacle = self.canvas.create_rectangle(
                500, 250-height, 520, 250,
                fill='#006400', outline='black', tags='obstacle')
        elif obstacle_type == "rock":
            obstacle = self.canvas.create_oval(
                500, 230, 520, 250,
                fill='#808080', outline='black', tags='obstacle')
        else:  # bird - flying obstacle
            y = random.randint(180, 220)
            obstacle = self.canvas.create_oval(
                500, y, 520, y+20,
                fill='#8B4513', outline='black', tags='obstacle')
            # Add wings
            self.canvas.create_line(510, y+10, 500, y-5, fill='black', width=2)
            self.canvas.create_line(510, y+10, 520, y-5, fill='black', width=2)
            
        self.obstacles.append(obstacle)
    
    def spawn_coin(self):
        """Spawn a new coin"""
        y = random.randint(150, 220)
        coin = self.canvas.create_oval(
            500, y, 520, y+20,
            fill='#FFD700', outline='#DAA520', tags='coin')
        self.coins.append(coin)
    
    def update_clouds(self):
        """Move the clouds slowly to the left"""
        for cloud_parts in self.clouds:
            for part in cloud_parts:
                self.canvas.move(part, -0.5, 0)
                # Check if cloud is off-screen
                x1, y1, x2, y2 = self.canvas.coords(part)
                if x2 < 0:
                    # Move cloud to right side
                    self.canvas.move(part, 550, 0)
    
    def check_collisions(self):
        """Check for collisions with obstacles and coins"""
        if self.game_over:
            return
            
        player_coords = self.canvas.coords(self.player)
        
        # Check obstacle collisions
        obstacles_to_remove = []
        for obstacle in self.obstacles:
            if self.canvas.type(obstacle) != "": # Check if item still exists
                obstacle_coords = self.canvas.coords(obstacle)
                
                # Check if obstacle is past the player (for scoring)
                if obstacle_coords[2] < player_coords[0] and obstacle not in obstacles_to_remove:
                    self.score += 10
                    self.update_score_display()
                    obstacles_to_remove.append(obstacle)
                    
                # Check for collision
                if (obstacle_coords[0] < player_coords[2] and
                    obstacle_coords[2] > player_coords[0] and
                    obstacle_coords[1] < player_coords[3] and
                    obstacle_coords[3] > player_coords[1]):
                    self.game_over = True
                    self.show_game_over()
                    break
        
        # Remove passed obstacles
        for obstacle in obstacles_to_remove:
            if obstacle in self.obstacles:
                self.obstacles.remove(obstacle)
                self.canvas.delete(obstacle)
        
        # Check coin collisions
        coins_to_remove = []
        for coin in self.coins:
            if self.canvas.type(coin) != "": # Check if item still exists
                coin_coords = self.canvas.coords(coin)
                
                # Check for collision with coin
                if (coin_coords[0] < player_coords[2] and
                    coin_coords[2] > player_coords[0] and
                    coin_coords[1] < player_coords[3] and
                    coin_coords[3] > player_coords[1]):
                    self.score += 50
                    self.update_score_display()
                    coins_to_remove.append(coin)
                
                # Check if coin is off-screen
                elif coin_coords[2] < 0:
                    coins_to_remove.append(coin)
        
        # Remove collected/passed coins
        for coin in coins_to_remove:
            if coin in self.coins:
                self.coins.remove(coin)
                self.canvas.delete(coin)
    
    def show_game_over(self):
        """Display game over message"""
        self.canvas.itemconfig(self.message_box, state='normal')
        self.canvas.itemconfig(self.message_title, state='normal')
        self.canvas.itemconfig(self.message_title, text="Game Over!")
        
        # Update high score if needed
        if self.score > self.high_score:
            self.high_score = self.score
            self.highscore_var.set(f"Best: {self.high_score}")
            high_score_text = f"New High Score: {self.high_score}!"
        else:
            high_score_text = f"Score: {self.score} (Best: {self.high_score})"
        
        self.canvas.itemconfig(self.message_text, state='normal')
        self.canvas.itemconfig(self.message_text, text=high_score_text+"\nPress RESET to try again")
        
        # Save high score
        self.save_highscore()
    
    def start(self):
        """Start the application"""
        super().start()
        
    def stop(self):
        """Stop the application"""
        super().stop()
    
    def update(self):
        """Update the game state"""
        if self.game_over:
            return
            
        # Update player position (gravity)
        self.player_velocity += self.gravity
        self.player_y += self.player_velocity
        
        # Keep player above ground
        if self.player_y > 220:
            self.player_y = 220
            self.player_velocity = 0
            self.is_jumping = False
        
        # Update player position
        self.canvas.coords(self.player, 50, self.player_y, 80, self.player_y + 30)
        
        # Move obstacles
        current_speed = self.obstacle_speed + (self.distance / 5000)
        for obstacle in self.obstacles:
            self.canvas.move(obstacle, -current_speed, 0)
        
        # Move coins
        for coin in self.coins:
            self.canvas.move(coin, -current_speed, 0)
        
        # Update clouds
        self.update_clouds()
        
        # Check for collisions
        self.check_collisions()
        
        # Spawn new obstacles
        self.next_spawn -= self.update_speed
        if self.next_spawn <= 0:
            self.spawn_obstacle()
            # Increase spawn rate as game progresses, but not too fast
            min_spawn_time = 600  # Minimum time between spawns in ms
            spawn_reduction = int(self.distance / 1000) * 50
            self.spawn_rate = max(min_spawn_time, 1500 - spawn_reduction)
            self.next_spawn = self.spawn_rate
        
        # Spawn new coins
        self.next_coin_spawn -= self.update_speed
        if self.next_coin_spawn <= 0:
            self.spawn_coin()
            self.next_coin_spawn = self.coin_spawn_rate
        
        # Increment distance and periodically update score
        self.distance += current_speed
        if self.distance % 100 < current_speed:
            self.score += 1
            self.update_score_display()


class PlatformerApp(EmbeddedApplication):
    """Simple 2D platformer game with levels"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.canvas = None
        
        # Game objects
        self.player = None
        self.player_rect = [0, 0, 0, 0]  # Cached player coordinates
        self.platforms = []
        self.coins = []
        self.enemies = []
        self.exit_door = None
        
        # Player state
        self.player_x = 50
        self.player_y = 240
        self.player_width = 20
        self.player_height = 30
        self.player_velocity_x = 0
        self.player_velocity_y = 0
        self.on_ground = False
        self.facing_right = True
        
        # Physics
        self.gravity = 0.5
        self.jump_strength = -12
        self.move_speed = 5
        self.terminal_velocity = 10
        
        # Game state
        self.keys_pressed = set()
        self.coins_collected = 0
        self.total_coins = 0
        self.enemies_defeated = 0
        self.game_over = False
        self.level_complete = False
        self.current_level_data = None
        
        # Game controller variables
        self.levels = self.generate_levels()
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="🎮 Platformer", 
                        font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        stats_frame = ttk.Frame(title_frame)
        stats_frame.pack(side='right')
        
        self.score_var = tk.StringVar(value="Score: 0")
        score_label = ttk.Label(stats_frame, textvariable=self.score_var,
                            font=('Arial', 12))
        score_label.pack(side='top')
        
        self.lives_var = tk.StringVar(value="Lives: 3")
        lives_label = ttk.Label(stats_frame, textvariable=self.lives_var,
                            font=('Arial', 12))
        lives_label.pack(side='top')
        
        self.level_var = tk.StringVar(value="Level: 1")
        level_label = ttk.Label(stats_frame, textvariable=self.level_var,
                            font=('Arial', 12))
        level_label.pack(side='top')
        
        # Game canvas
        self.canvas = tk.Canvas(self.frame, width=500, height=300, 
                            bg='#87CEFA', highlightthickness=2)
        self.canvas.pack(pady=(0, 10))
        
        # Initial game setup
        self.setup_level(1)
        
        # Control buttons
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        self.start_btn = ttk.Button(control_frame, text="Start", 
                                   command=self.start_game)
        self.start_btn.pack(side='left', padx=(0, 5))
        
        self.reset_btn = ttk.Button(control_frame, text="Reset", 
                                   command=self.reset_game)
        self.reset_btn.pack(side='left')
        
        # Instruction text
        self.instruction_var = tk.StringVar(
            value="Left/Right arrows to move, Up to jump | " +
                 "Collect coins, avoid enemies, reach exit")
        instructions = ttk.Label(self.frame, textvariable=self.instruction_var)
        instructions.pack(pady=(10, 0))
        
        # Bind keyboard events
        self.canvas.focus_set()
        self.canvas.bind("<KeyPress>", self.key_press)
        self.canvas.bind("<KeyRelease>", self.key_release)
        
        return self.frame
    
    def generate_levels(self):
        """Generate game levels data"""
        levels = [
            # Level 1 - Tutorial level
            {
                "platforms": [
                    {"x": 0, "y": 270, "width": 500, "height": 30},  # Ground
                    {"x": 120, "y": 200, "width": 100, "height": 20},  # Platform 1
                    {"x": 280, "y": 150, "width": 100, "height": 20},  # Platform 2
                ],
                "coins": [
                    {"x": 150, "y": 180},  # On platform 1
                    {"x": 320, "y": 130},  # On platform 2
                    {"x": 400, "y": 250},  # On ground
                ],
                "enemies": [
                    {"x": 300, "y": 250, "width": 20, "height": 20, "speed": 1,
                     "patrol_start": 250, "patrol_end": 350},  # Ground enemy
                ],
                "exit": {"x": 450, "y": 240},
                "player_start": {"x": 50, "y": 240},
                "background_color": "#87CEFA",  # Light blue sky
            },
            
            # Level 2 - More complex
            {
                "platforms": [
                    {"x": 0, "y": 270, "width": 150, "height": 30},  # Ground piece 1
                    {"x": 220, "y": 270, "width": 280, "height": 30},  # Ground piece 2
                    {"x": 100, "y": 180, "width": 80, "height": 15},  # Platform 1
                    {"x": 240, "y": 200, "width": 60, "height": 15},  # Platform 2
                    {"x": 350, "y": 160, "width": 100, "height": 15},  # Platform 3
                    {"x": 50, "y": 120, "width": 70, "height": 15},  # High platform
                ],
                "coins": [
                    {"x": 120, "y": 160},  # On platform 1
                    {"x": 260, "y": 180},  # On platform 2
                    {"x": 380, "y": 140},  # On platform 3
                    {"x": 60, "y": 100},   # On high platform
                    {"x": 300, "y": 250},  # On ground
                ],
                "enemies": [
                    {"x": 260, "y": 250, "width": 20, "height": 20, "speed": 2,
                     "patrol_start": 230, "patrol_end": 470},  # Ground enemy
                    {"x": 380, "y": 140, "width": 20, "height": 20, "speed": 1.5,
                     "patrol_start": 350, "patrol_end": 430},  # Platform enemy
                ],
                "exit": {"x": 450, "y": 240},
                "player_start": {"x": 30, "y": 240},
                "background_color": "#ADD8E6",  # Slightly darker blue
            },
            
            # Level 3 - Even more complex
            {
                "platforms": [
                    {"x": 0, "y": 270, "width": 100, "height": 30},  # Ground piece 1
                    {"x": 170, "y": 270, "width": 60, "height": 30},  # Ground piece 2
                    {"x": 300, "y": 270, "width": 200, "height": 30},  # Ground piece 3
                    {"x": 80, "y": 200, "width": 60, "height": 15},  # Platform 1
                    {"x": 190, "y": 180, "width": 50, "height": 15},  # Platform 2
                    {"x": 270, "y": 140, "width": 45, "height": 15},  # Platform 3
                    {"x": 370, "y": 110, "width": 100, "height": 15},  # Top platform
                ],
                "coins": [
                    {"x": 100, "y": 180},   # On platform 1
                    {"x": 210, "y": 160},   # On platform 2
                    {"x": 290, "y": 120},   # On platform 3
                    {"x": 400, "y": 90},    # On top platform
                    {"x": 320, "y": 250},   # On ground
                    {"x": 180, "y": 250},   # On middle ground
                ],
                "enemies": [
                    {"x": 320, "y": 250, "width": 20, "height": 20, "speed": 2.5,
                     "patrol_start": 310, "patrol_end": 470},  # Ground enemy
                    {"x": 390, "y": 90, "width": 20, "height": 20, "speed": 1.5,
                     "patrol_start": 370, "patrol_end": 450},  # Platform enemy
                    {"x": 270, "y": 120, "width": 20, "height": 20, "speed": 1,
                     "patrol_start": 270, "patrol_end": 315},  # Small patrol enemy
                ],
                "exit": {"x": 450, "y": 240},
                "player_start": {"x": 30, "y": 240},
                "background_color": "#B0C4DE",  # Even darker blue
            }
        ]
        return levels
    
    def setup_level(self, level_index):
        """Set up a level based on its index"""
        # Clear the canvas
        self.canvas.delete("all")
        
        # Make sure level index is valid
        if level_index < 1 or level_index > len(self.levels):
            level_index = 1
            
        # Get level data
        self.level = level_index
        self.current_level_data = self.levels[level_index - 1]
        
        # Set background
        bg_color = self.current_level_data.get("background_color", "#87CEFA")
        self.canvas.configure(bg=bg_color)
        
        # Initialize collections
        self.platforms = []
        self.coins = []
        self.enemies = []
        
        # Draw platforms
        for platform_data in self.current_level_data["platforms"]:
            platform = self.canvas.create_rectangle(
                platform_data["x"], platform_data["y"],
                platform_data["x"] + platform_data["width"],
                platform_data["y"] + platform_data["height"],
                fill='#8B4513', outline='')
                
            # Add grass on top of ground platforms
            if platform_data["y"] >= 270:
                self.canvas.create_rectangle(
                    platform_data["x"], platform_data["y"],
                    platform_data["x"] + platform_data["width"], 
                    platform_data["y"] + 5,
                    fill='#32CD32', outline='')
            
            self.platforms.append({
                "id": platform,
                "x": platform_data["x"],
                "y": platform_data["y"],
                "width": platform_data["width"],
                "height": platform_data["height"]
            })
        
        # Draw coins
        self.total_coins = len(self.current_level_data["coins"])
        for coin_data in self.current_level_data["coins"]:
            coin = self.canvas.create_oval(
                coin_data["x"] - 5, coin_data["y"] - 5,
                coin_data["x"] + 5, coin_data["y"] + 5,
                fill='#FFD700', outline='#DAA520')
            self.coins.append({
                "id": coin,
                "x": coin_data["x"],
                "y": coin_data["y"]
            })
        
        # Draw enemies
        for enemy_data in self.current_level_data["enemies"]:
            enemy = self.canvas.create_rectangle(
                enemy_data["x"], enemy_data["y"],
                enemy_data["x"] + enemy_data["width"], 
                enemy_data["y"] + enemy_data["height"],
                fill='#FF0000', outline='#8B0000')
            self.enemies.append({
                "id": enemy,
                "x": enemy_data["x"],
                "y": enemy_data["y"],
                "width": enemy_data["width"],
                "height": enemy_data["height"],
                "speed": enemy_data["speed"],
                "direction": 1,  # 1 for right, -1 for left
                "patrol_start": enemy_data["patrol_start"],
                "patrol_end": enemy_data["patrol_end"]
            })
        
        # Draw exit door
        exit_data = self.current_level_data["exit"]
        self.exit_door = self.canvas.create_rectangle(
            exit_data["x"] - 15, exit_data["y"] - 30,
            exit_data["x"] + 15, exit_data["y"],
            fill='#8B008B', outline='black')
        
        # Add exit sign
        self.canvas.create_rectangle(
            exit_data["x"] - 10, exit_data["y"] - 25,
            exit_data["x"] + 10, exit_data["y"] - 15,
            fill='#00FF00', outline='black')
        self.canvas.create_text(
            exit_data["x"], exit_data["y"] - 20,
            text="EXIT", fill='black', font=('Arial', 7, 'bold'))
        
        # Draw player
        player_start = self.current_level_data["player_start"]
        self.player_x = player_start["x"]
        self.player_y = player_start["y"]
        self.player = self.canvas.create_rectangle(
            self.player_x, self.player_y,
            self.player_x + self.player_width, 
            self.player_y + self.player_height,
            fill='#4169E1', outline='black')
        
        # Update player rect cache
        self.player_rect = [
            self.player_x, self.player_y,
            self.player_x + self.player_width, 
            self.player_y + self.player_height
        ]
        
        # Reset game state for this level
        self.coins_collected = 0
        self.game_over = False
        self.level_complete = False
        self.player_velocity_x = 0
        self.player_velocity_y = 0
        self.on_ground = False
        
        # Show level message
        self.message_box = self.canvas.create_rectangle(
            150, 100, 350, 180, fill='#000033', outline='#4682B4', width=2)
        self.message_title = self.canvas.create_text(
            250, 130, text=f"Level {level_index}", 
            fill='#FFD700', font=('Arial', 20, 'bold'))
        self.message_text = self.canvas.create_text(
            250, 160, text="Press START to begin\nArrow keys to move and jump", 
            fill='white', font=('Arial', 12))
        
        # Update display
        self.update_status_display()
    
    def update_status_display(self):
        """Update the status displays"""
        self.score_var.set(f"Score: {self.score}")
        self.lives_var.set(f"Lives: {self.lives}")
        self.level_var.set(f"Level: {self.level}")
        
        # Update instructions based on game state
        if self.game_over:
            self.instruction_var.set("Game Over! Press RESET to try again")
        elif self.level_complete:
            if self.level >= len(self.levels):
                self.instruction_var.set("Congratulations! You completed all levels!")
            else:
                self.instruction_var.set("Level Complete! Starting next level...")
        else:
            coins_left = self.total_coins - self.coins_collected
            self.instruction_var.set(
                f"Coins: {self.coins_collected}/{self.total_coins} | " +
                "Reach the exit door to complete the level")
    
    def start_game(self):
        """Start the game"""
        # Hide message
        self.canvas.itemconfig(self.message_box, state='hidden')
        self.canvas.itemconfig(self.message_title, state='hidden')
        self.canvas.itemconfig(self.message_text, state='hidden')
        
        # Give focus to canvas and start game loop
        self.canvas.focus_set()
        super().start()
    
    def reset_game(self):
        """Reset the game to level 1"""
        super().reset()
        self.setup_level(1)
    
    def key_press(self, event):
        """Handle key press events"""
        key = event.keysym.lower()
        self.keys_pressed.add(key)
    
    def key_release(self, event):
        """Handle key release events"""
        key = event.keysym.lower()
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
    
    def process_input(self):
        """Process user input"""
        if self.game_over or self.level_complete:
            return
        
        # Handle left/right movement
        self.player_velocity_x = 0
        if 'left' in self.keys_pressed:
            self.player_velocity_x = -self.move_speed
            self.facing_right = False
        if 'right' in self.keys_pressed:
            self.player_velocity_x = self.move_speed
            self.facing_right = True
            
        # Handle jumping
        if 'up' in self.keys_pressed and self.on_ground:
            self.player_velocity_y = self.jump_strength
            self.on_ground = False
    
    def update_player(self):
        """Update the player's position and state"""
        if self.game_over or self.level_complete:
            return
            
        # Apply gravity
        self.player_velocity_y += self.gravity
        
        # Cap fall speed
        if self.player_velocity_y > self.terminal_velocity:
            self.player_velocity_y = self.terminal_velocity
        
        # Update position
        self.player_x += self.player_velocity_x
        self.player_y += self.player_velocity_y
        
        # Check boundaries
        if self.player_x < 0:
            self.player_x = 0
        elif self.player_x > 500 - self.player_width:
            self.player_x = 500 - self.player_width
        
        # Falling off the bottom
        if self.player_y > 300:
            self.lose_life()
            return
            
        # Update canvas position
        self.canvas.coords(
            self.player,
            self.player_x, self.player_y,
            self.player_x + self.player_width, 
            self.player_y + self.player_height
        )
        
        # Update player rect cache for collision detection
        self.player_rect = [
            self.player_x, self.player_y,
            self.player_x + self.player_width, 
            self.player_y + self.player_height
        ]
        
    def check_platform_collisions(self):
        """Check for collisions with platforms"""
        # Reset ground state
        self.on_ground = False
        
        for platform in self.platforms:
            # Platform rectangle
            platform_rect = [
                platform["x"], platform["y"],
                platform["x"] + platform["width"], 
                platform["y"] + platform["height"]
            ]
            
            # Check for collision
            if (self.player_rect[2] > platform_rect[0] and  # Right > Left
                self.player_rect[0] < platform_rect[2] and  # Left < Right
                self.player_rect[3] > platform_rect[1] and  # Bottom > Top
                self.player_rect[1] < platform_rect[3]):    # Top < Bottom
                
                # Determine collision side
                previous_bottom = self.player_rect[3] - self.player_velocity_y
                
                # Coming from top
                if (previous_bottom <= platform_rect[1] and 
                    self.player_velocity_y > 0):
                    # Land on platform
                    self.player_y = platform_rect[1] - self.player_height
                    self.player_velocity_y = 0
                    self.on_ground = True
                    
                    # Update canvas and collision rect
                    self.canvas.coords(
                        self.player,
                        self.player_x, self.player_y,
                        self.player_x + self.player_width, 
                        self.player_y + self.player_height
                    )
                    self.player_rect[1] = self.player_y
                    self.player_rect[3] = self.player_y + self.player_height
                
                # Coming from below (hit head)
                elif (self.player_velocity_y < 0 and 
                      self.player_rect[1] <= platform_rect[3] and 
                      self.player_rect[1] > platform_rect[1]):
                    self.player_y = platform_rect[3]
                    self.player_velocity_y = 0
                    
                    # Update canvas and collision rect
                    self.canvas.coords(
                        self.player,
                        self.player_x, self.player_y,
                        self.player_x + self.player_width, 
                        self.player_y + self.player_height
                    )
                    self.player_rect[1] = self.player_y
                    self.player_rect[3] = self.player_y + self.player_height
    
    def check_coin_collisions(self):
        """Check for collisions with coins"""
        coins_to_remove = []
        
        for coin in self.coins:
            # Coin center and radius
            coin_x, coin_y = coin["x"], coin["y"]
            radius = 5
            
            # Check for collision with player
            if (self.player_rect[0] < coin_x + radius and
                self.player_rect[2] > coin_x - radius and
                self.player_rect[1] < coin_y + radius and
                self.player_rect[3] > coin_y - radius):
                coins_to_remove.append(coin)
                self.coins_collected += 1
                self.update_score(10)  # Award points
                self.update_status_display()
        
        # Remove collected coins
        for coin in coins_to_remove:
            self.canvas.delete(coin["id"])
            self.coins.remove(coin)
    
    def check_enemy_collisions(self):
        """Check for collisions with enemies"""
        if self.game_over:
            return
            
        for enemy in self.enemies:
            # Enemy rectangle
            enemy_rect = [
                enemy["x"], enemy["y"],
                enemy["x"] + enemy["width"], 
                enemy["y"] + enemy["height"]
            ]
            
            # Check for collision
            if (self.player_rect[2] > enemy_rect[0] and
                self.player_rect[0] < enemy_rect[2] and
                self.player_rect[3] > enemy_rect[1] and
                self.player_rect[1] < enemy_rect[3]):
                
                # Determine if player is jumping on the enemy
                previous_bottom = self.player_rect[3] - self.player_velocity_y
                
                if (previous_bottom <= enemy_rect[1] and 
                    self.player_velocity_y > 0):
                    # Defeated enemy by jumping on it
                    self.enemies.remove(enemy)
                    self.canvas.delete(enemy["id"])
                    self.enemies_defeated += 1
                    self.update_score(25)  # Award points
                    
                    # Bounce the player up a bit
                    self.player_velocity_y = self.jump_strength * 0.6
                    
                else:
                    # Player hit by enemy
                    self.lose_life()
                    break
    
    def check_exit_collision(self):
        """Check if the player has reached the exit door"""
        if self.level_complete or self.game_over:
            return
            
        exit_coords = self.canvas.coords(self.exit_door)
        exit_rect = exit_coords
        
        if (self.player_rect[2] > exit_rect[0] and
            self.player_rect[0] < exit_rect[2] and
            self.player_rect[3] > exit_rect[1] and
            self.player_rect[1] < exit_rect[3]):
            
            self.level_complete = True
            self.update_score(50)  # Base completion bonus
            
            # Bonus for collecting all coins
            if self.coins_collected >= self.total_coins:
                self.update_score(100)
            
            self.show_level_complete()
    
    def update_enemies(self):
        """Update enemy positions and behavior"""
        for enemy in self.enemies:
            # Move enemy based on patrol pattern
            enemy["x"] += enemy["speed"] * enemy["direction"]
            
            # Check patrol boundaries
            if enemy["x"] <= enemy["patrol_start"]:
                enemy["x"] = enemy["patrol_start"]
                enemy["direction"] = 1  # Change direction to right
            elif enemy["x"] >= enemy["patrol_end"] - enemy["width"]:
                enemy["x"] = enemy["patrol_end"] - enemy["width"]
                enemy["direction"] = -1  # Change direction to left
            
            # Update canvas position
            self.canvas.coords(
                enemy["id"],
                enemy["x"], enemy["y"],
                enemy["x"] + enemy["width"], enemy["y"] + enemy["height"]
            )
    
    def lose_life(self):
        """Handle player losing a life"""
        self.lives -= 1
        self.update_status_display()
        
        if self.lives <= 0:
            self.game_over = True
            self.show_game_over()
        else:
            # Reset player position to start
            player_start = self.current_level_data["player_start"]
            self.player_x = player_start["x"]
            self.player_y = player_start["y"]
            self.player_velocity_x = 0
            self.player_velocity_y = 0
            
            # Update canvas
            self.canvas.coords(
                self.player,
                self.player_x, self.player_y,
                self.player_x + self.player_width, 
                self.player_y + self.player_height
            )
            
            # Update player rect cache
            self.player_rect = [
                self.player_x, self.player_y,
                self.player_x + self.player_width, 
                self.player_y + self.player_height
            ]
    
    def show_game_over(self):
        """Show game over message"""
        self.canvas.itemconfig(self.message_box, state='normal')
        self.canvas.itemconfig(self.message_title, state='normal')
        self.canvas.itemconfig(self.message_title, text="Game Over!")
        
        # Update high score if needed
        if self.score > self.high_score:
            self.high_score = self.score
            high_score_text = f"New High Score: {self.high_score}!"
        else:
            high_score_text = f"Score: {self.score} (Best: {self.high_score})"
        
        self.canvas.itemconfig(self.message_text, state='normal')
        self.canvas.itemconfig(
            self.message_text,
            text=high_score_text+"\nPress RESET to try again"
        )
        
        # Save high score
        self.save_highscore()
    
    def show_level_complete(self):
        """Show level complete message"""
        self.canvas.itemconfig(self.message_box, state='normal')
        self.canvas.itemconfig(self.message_title, state='normal')
        self.canvas.itemconfig(self.message_title, text="Level Complete!")
        
        completion_text = f"Score: {self.score}"
        if self.coins_collected >= self.total_coins:
            completion_text += "\nAll coins collected! +100 bonus"
        
        self.canvas.itemconfig(self.message_text, state='normal')
        self.canvas.itemconfig(self.message_text, text=completion_text)
        
        # Check if there are more levels
        if self.level < len(self.levels):
            # Schedule next level
            self.frame.after(2000, self.next_level)
        else:
            # Game complete
            self.canvas.itemconfig(
                self.message_text, 
                text=completion_text + "\nCongratulations! You beat the game!"
            )
    
    def next_level(self):
        """Advance to the next level"""
        if self.level < len(self.levels):
            self.level += 1
            self.setup_level(self.level)
            self.start_game()
    
    def start(self):
        """Start the application"""
        super().start()
        
    def stop(self):
        """Stop the application"""
        super().stop()
    
    def update(self):
        """Update the game state"""
        if not self.running or self.game_over:
            return
            
        self.process_input()
        self.update_player()
        self.check_platform_collisions()
        self.update_enemies()
        self.check_coin_collisions()
        self.check_enemy_collisions()
        self.check_exit_collision()
