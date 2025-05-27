# Sona JSON Module - Enhanced JSON processing
# Provides comprehensive JSON handling capabilities for Sona applications

import json
import os
from pathlib import Path

class SonaJSONModule:
    """Enhanced JSON module for Sona applications"""
    
    def __init__(self):
        self.indent_level = 2
        self.ensure_ascii = False
    
    def parse(self, json_string):
        """Parse JSON string and return object"""
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return None
    
    def stringify(self, obj, indent=None, compact=False):
        """Convert object to JSON string"""
        try:
            if compact:
                return json.dumps(obj, separators=(',', ':'), ensure_ascii=self.ensure_ascii)
            else:
                indent_val = indent if indent is not None else self.indent_level
                return json.dumps(obj, indent=indent_val, ensure_ascii=self.ensure_ascii)
        except Exception as e:
            print(f"Error stringifying JSON: {e}")
            return None
    
    def load_file(self, file_path, encoding="utf-8"):
        """Load JSON from file"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"JSON file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parse error in file {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Error loading JSON file {file_path}: {e}")
            return None
    
    def save_file(self, file_path, obj, encoding="utf-8", indent=None, backup=False):
        """Save object to JSON file"""
        try:
            # Create backup if requested
            if backup and os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                import shutil
                shutil.copy2(file_path, backup_path)
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                indent_val = indent if indent is not None else self.indent_level
                json.dump(obj, f, indent=indent_val, ensure_ascii=self.ensure_ascii)
            return True
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {e}")
            return False
    
    def validate(self, json_string):
        """Validate JSON string"""
        try:
            json.loads(json_string)
            return True
        except json.JSONDecodeError:
            return False
        except Exception:
            return False

# Create the module instance
json_enhanced = SonaJSONModule()

# Export for compatibility
__all__ = ['json_enhanced']
