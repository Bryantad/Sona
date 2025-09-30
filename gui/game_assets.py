"""
Sona Game Assets Module

This module provides shared functionality and resources for all embedded games
in the Sona Application Launcher, including:
- Sound effect helpers
- Color schemes and themes
- Shared sprite utilities
- Level generation helpers
- Score tracking
"""

import json
import math
import os
import random
from pathlib import Path


class SoundManager:
    """Basic sound effect manager for games"""
    def __init__(self):
        self.sounds = {}
        self.sound_enabled = True
        
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled
    
    def play_sound(self, sound_name):
        """Play a sound effect if enabled"""
        if not self.sound_enabled or sound_name not in self.sounds:
            return
        
        # This would use a real sound library in a full implementation
        # For now, we just print to console for demonstration
        print(f"Playing sound: {sound_name}")


class LevelGenerator:
    """Procedural level generator for games"""
    def __init__(self, width=500, height=300):
        self.width = width
        self.height = height
    
    def generate_platforms(self, difficulty=0.5, platform_count=5):
        """Generate a set of platforms for a level"""
        platforms = []
        
        # Always add a ground platform
        ground = {
            "x": 0, 
            "y": self.height - 30, 
            "width": self.width, 
            "height": 30
        }
        platforms.append(ground)
        
        # Generate additional platforms
        min_width = int(100 - difficulty * 50)  # Narrower platforms at higher difficulty
        for i in range(platform_count):
            # Platform gets higher as i increases
            y_position = self.height - 80 - (i * 50)
            
            # Randomly position platform horizontally
            platform_width = random.randint(min_width, 150)
            x_position = random.randint(0, self.width - platform_width)
            
            platform = {
                "x": x_position,
                "y": y_position,
                "width": platform_width,
                "height": 15
            }
            platforms.append(platform)
            
        return platforms
    
    def generate_coins(self, platforms, coin_count=10):
        """Generate coins, usually placed above platforms"""
        coins = []
        
        for platform in platforms[1:]:  # Skip ground platform
            # 70% chance to add a coin above this platform
            if random.random() < 0.7:
                coin_x = platform["x"] + platform["width"] // 2
                coin_y = platform["y"] - 20
                
                coins.append({
                    "x": coin_x,
                    "y": coin_y
                })
        
        # Add more random coins to reach desired count
        while len(coins) < coin_count:
            coin_x = random.randint(50, self.width - 50)
            coin_y = random.randint(50, self.height - 100)
            
            coins.append({
                "x": coin_x,
                "y": coin_y
            })
            
        return coins
    
    def generate_enemies(self, platforms, difficulty=0.5, enemy_count=3):
        """Generate enemies on platforms"""
        enemies = []
        
        # Generate enemies on some platforms
        for platform in platforms:
            # Skip some platforms and don't always add enemies
            if platform["width"] < 60 or random.random() > 0.4:
                continue
                
            # Create enemy patrolling this platform
            enemy_width = 20
            enemy_height = 20
            enemy = {
                "x": platform["x"] + 10,
                "y": platform["y"] - enemy_height,
                "width": enemy_width,
                "height": enemy_height,
                "speed": 1 + difficulty * 2,
                "patrol_start": platform["x"],
                "patrol_end": platform["x"] + platform["width"]
            }
            
            enemies.append(enemy)
            
            if len(enemies) >= enemy_count:
                break
                
        return enemies


class ColorThemes:
    """Color themes for games"""
    
    THEMES = {
        "default": {
            "background": "#202020",
            "text": "#FFFFFF",
            "highlight": "#4CAF50",
            "accent": "#2196F3",
            "warning": "#FFC107",
            "danger": "#F44336",
            "success": "#8BC34A"
        },
        "retro": {
            "background": "#000000",
            "text": "#00FF00",
            "highlight": "#00FFFF",
            "accent": "#FF00FF",
            "warning": "#FFFF00",
            "danger": "#FF0000",
            "success": "#00FF00"
        },
        "pastel": {
            "background": "#F5F5F5",
            "text": "#333333",
            "highlight": "#95E1D3",
            "accent": "#EAFFD0",
            "warning": "#FCE38A",
            "danger": "#F38181",
            "success": "#A8D8EA"
        },
        "dark": {
            "background": "#121212",
            "text": "#EEEEEE",
            "highlight": "#BB86FC",
            "accent": "#03DAC6",
            "warning": "#FFB74D",
            "danger": "#CF6679",
            "success": "#81C784"
        }
    }
    
    @classmethod
    def get_theme(cls, theme_name="default"):
        """Get a color theme by name"""
        return cls.THEMES.get(theme_name, cls.THEMES["default"])
        

class ScoreManager:
    """Manages and persists game scores"""
    def __init__(self, game_name):
        self.game_name = game_name
        self.save_dir = Path(os.path.expanduser("~/.sona/game_data"))
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = self.save_dir / f"{game_name}_scores.json"
        
        # Load existing scores
        self.high_score = 0
        self.scores = []
        self.load_scores()
    
    def save_score(self, score, player_name="Player"):
        """Save a new score"""
        # Update high score if needed
        if score > self.high_score:
            self.high_score = score
            
        # Add to scores list
        self.scores.append({
            "score": score,
            "player": player_name,
            "timestamp": str(datetime.now())
        })
        
        # Keep only top 10 scores
        self.scores = sorted(self.scores, key=lambda x: x["score"], reverse=True)[:10]
        
        # Save to file
        self.save_scores()
        
    def load_scores(self):
        """Load scores from file"""
        try:
            if self.save_file.exists():
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                    self.high_score = data.get("high_score", 0)
                    self.scores = data.get("scores", [])
        except Exception as e:
            print(f"Error loading scores: {e}")
    
    def save_scores(self):
        """Save scores to file"""
        try:
            with open(self.save_file, 'w') as f:
                json.dump({
                    "high_score": self.high_score,
                    "scores": self.scores
                }, f)
        except Exception as e:
            print(f"Error saving scores: {e}")
    
    def get_high_score(self):
        """Get the high score"""
        return self.high_score
    
    def get_top_scores(self, limit=5):
        """Get the top N scores"""
        return sorted(self.scores, key=lambda x: x["score"], reverse=True)[:limit]


class ParticleSystem:
    """Simple particle effect system for games"""
    def __init__(self, canvas):
        self.canvas = canvas
        self.particles = []
        
    def create_explosion(self, x, y, color="#FFFF00", count=10, speed=3, lifetime=20):
        """Create an explosion of particles at position"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            velocity = [
                math.cos(angle) * random.uniform(1, speed),
                math.sin(angle) * random.uniform(1, speed)
            ]
            
            size = random.randint(2, 5)
            
            particle = {
                "id": self.canvas.create_oval(
                    x-size, y-size, x+size, y+size, 
                    fill=color, outline=""
                ),
                "velocity": velocity,
                "lifetime": lifetime,
                "remaining": lifetime
            }
            self.particles.append(particle)
    
    def create_trail(self, x, y, color="#3498db", count=1):
        """Create trail particles behind an object"""
        for _ in range(count):
            size = random.randint(1, 3)
            particle = {
                "id": self.canvas.create_oval(
                    x-size, y-size, x+size, y+size, 
                    fill=color, outline=""
                ),
                "velocity": [0, 0],
                "lifetime": 10,
                "remaining": 10
            }
            self.particles.append(particle)
    
    def update(self):
        """Update all particles"""
        expired = []
        
        for particle in self.particles:
            # Update position
            self.canvas.move(
                particle["id"], 
                particle["velocity"][0], 
                particle["velocity"][1]
            )
            
            # Update lifetime
            particle["remaining"] -= 1
            
            # Fade out
            opacity = particle["remaining"] / particle["lifetime"]
            if opacity < 1:
                # This would set opacity in a real implementation
                pass
            
            # Mark for removal if expired
            if particle["remaining"] <= 0:
                expired.append(particle)
        
        # Remove expired particles
        for particle in expired:
            if particle in self.particles:
                try:
                    self.canvas.delete(particle["id"])
                    self.particles.remove(particle)
                except:
                    pass
