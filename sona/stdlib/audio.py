# Sona Audio Module - Cross-platform audio support
# Provides audio playback capabilities for Sona applications

import threading
import time
import os
from pathlib import Path

# Try different audio backends in order of preference
AUDIO_BACKEND = None

# Try pygame first (most reliable)
try:
    import pygame
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    AUDIO_BACKEND = "pygame"
except ImportError:
    pass

# Fallback to playsound
if AUDIO_BACKEND is None:
    try:
        import playsound
        AUDIO_BACKEND = "playsound"
    except ImportError:
        pass

# Fallback to basic OS commands
if AUDIO_BACKEND is None:
    AUDIO_BACKEND = "os"

class SonaAudioModule:
    """Audio module for Sona applications with multiple backend support"""
    
    def __init__(self):
        self.backend = AUDIO_BACKEND
        self.loaded_sounds = {}
        self.playing_sounds = {}
        self.volume = 0.7
        self.sound_counter = 0
        
    def get_backend(self):
        """Return current audio backend"""
        return self.backend
    
    def load_sound(self, file_path):
        """Load a sound file and return its ID"""
        if not os.path.exists(file_path):
            return None
            
        sound_id = f"sound_{self.sound_counter}"
        self.sound_counter += 1
        
        if self.backend == "pygame":
            try:
                sound = pygame.mixer.Sound(file_path)
                self.loaded_sounds[sound_id] = {
                    'path': file_path,
                    'sound': sound,
                    'type': 'pygame'
                }
                return sound_id
            except Exception as e:
                print(f"Error loading sound with pygame: {e}")
                return None
        else:
            # For other backends, just store the path
            self.loaded_sounds[sound_id] = {
                'path': file_path,
                'sound': None,
                'type': 'file'
            }
            return sound_id
    
    def play_sound(self, sound_id, loop=False):
        """Play a loaded sound"""
        if sound_id not in self.loaded_sounds:
            return False
            
        sound_data = self.loaded_sounds[sound_id]
        
        if self.backend == "pygame" and sound_data['type'] == 'pygame':
            try:
                if loop:
                    sound_data['sound'].play(-1)  # Loop indefinitely
                else:
                    sound_data['sound'].play()
                return True
            except Exception as e:
                print(f"Error playing sound with pygame: {e}")
                return False
                
        elif self.backend == "playsound":
            def play_async():
                try:
                    playsound.playsound(sound_data['path'], block=False)
                except Exception as e:
                    print(f"Error playing sound with playsound: {e}")
            
            thread = threading.Thread(target=play_async)
            thread.daemon = True
            thread.start()
            return True
            
        elif self.backend == "os":
            def play_async():
                try:
                    if os.name == 'nt':  # Windows
                        os.system(f'start /min wmplayer "{sound_data["path"]}"')
                    elif os.name == 'posix':  # Linux/Mac
                        os.system(f'aplay "{sound_data["path"]}" > /dev/null 2>&1 &')
                except Exception as e:
                    print(f"Error playing sound with OS: {e}")
            
            thread = threading.Thread(target=play_async)
            thread.daemon = True
            thread.start()
            return True
        
        return False
    
    def play_file(self, file_path, loop=False):
        """Load and play a sound file directly"""
        sound_id = self.load_sound(file_path)
        if sound_id:
            return self.play_sound(sound_id, loop)
        return False
    
    def stop_sound(self, sound_id):
        """Stop a playing sound"""
        if sound_id not in self.loaded_sounds:
            return False
            
        sound_data = self.loaded_sounds[sound_id]
        
        if self.backend == "pygame" and sound_data['type'] == 'pygame':
            try:
                sound_data['sound'].stop()
                return True
            except Exception as e:
                print(f"Error stopping sound: {e}")
                return False
        
        # For other backends, stopping is not easily supported
        return False
    
    def stop_all_sounds(self):
        """Stop all playing sounds"""
        if self.backend == "pygame":
            try:
                pygame.mixer.stop()
                return True
            except Exception as e:
                print(f"Error stopping all sounds: {e}")
                return False
        
        return False
    
    def set_volume(self, volume):
        """Set global volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        
        if self.backend == "pygame":
            try:
                pygame.mixer.music.set_volume(self.volume)
                # Also set volume for all loaded sounds
                for sound_data in self.loaded_sounds.values():
                    if sound_data['type'] == 'pygame' and sound_data['sound']:
                        sound_data['sound'].set_volume(self.volume)
                return True
            except Exception as e:
                print(f"Error setting volume: {e}")
                return False
        
        return True  # For other backends, just store the value
    
    def get_volume(self):
        """Get current volume"""
        return self.volume
    
    def play_music(self, file_path, loop=True):
        """Play background music"""
        if self.backend == "pygame":
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1 if loop else 0)
                return True
            except Exception as e:
                print(f"Error playing music: {e}")
                return False
        else:
            # Fallback to regular sound playing
            return self.play_file(file_path, loop)
    
    def stop_music(self):
        """Stop background music"""
        if self.backend == "pygame":
            try:
                pygame.mixer.music.stop()
                return True
            except Exception as e:
                print(f"Error stopping music: {e}")
                return False
        
        return self.stop_all_sounds()
    
    def pause_music(self):
        """Pause background music"""
        if self.backend == "pygame":
            try:
                pygame.mixer.music.pause()
                return True
            except Exception as e:
                print(f"Error pausing music: {e}")
                return False
        
        return False
    
    def resume_music(self):
        """Resume background music"""
        if self.backend == "pygame":
            try:
                pygame.mixer.music.unpause()
                return True
            except Exception as e:
                print(f"Error resuming music: {e}")
                return False
        
        return False
    
    def is_music_playing(self):
        """Check if music is currently playing"""
        if self.backend == "pygame":
            try:
                return pygame.mixer.music.get_busy()
            except Exception as e:
                print(f"Error checking music status: {e}")
                return False
        
        return False
    
    def create_tone(self, frequency, duration, volume=None):
        """Generate a simple tone (pygame only)"""
        if self.backend != "pygame":
            return False
            
        if volume is None:
            volume = self.volume
            
        try:
            import numpy as np
            
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                time_val = float(i) / sample_rate
                wave_val = np.sin(frequency * 2 * np.pi * time_val) * volume
                arr[i][0] = wave_val
                arr[i][1] = wave_val
            
            arr = (arr * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
            return True
            
        except ImportError:
            print("NumPy not available for tone generation")
            return False
        except Exception as e:
            print(f"Error generating tone: {e}")
            return False
    
    def get_supported_formats(self):
        """Get list of supported audio formats"""
        if self.backend == "pygame":
            return [".wav", ".ogg", ".mp3"]
        elif self.backend == "playsound":
            return [".wav", ".mp3"]
        else:
            return [".wav", ".mp3", ".wma"]

# Create the module instance
audio = SonaAudioModule()

# Export for compatibility
__all__ = ['audio']
