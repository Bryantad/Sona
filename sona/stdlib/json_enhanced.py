# Sona JSON Module - JSON parsing and generation
# Provides comprehensive JSON handling for Sona applications

import json
import os

class SonaJSONModule:
    """JSON module for Sona applications"""
    
    def __init__(self):
        self.pretty_print = True
        self.indent_size = 2
    
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
    
    def stringify(self, obj, pretty=None, indent=None):
        """Convert object to JSON string"""
        try:
            if pretty is None:
                pretty = self.pretty_print
            if indent is None:
                indent = self.indent_size if pretty else None
            
            if pretty:
                return json.dumps(obj, indent=indent, ensure_ascii=False, separators=(',', ': '))
            else:
                return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            print(f"Error stringifying JSON: {e}")
            return None
    
    def load_file(self, file_path, encoding="utf-8"):
        """Load JSON from file"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON parse error in {file_path}: {e}")
            return None
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except Exception as e:
            print(f"Error loading JSON file {file_path}: {e}")
            return None
    
    def save_file(self, file_path, obj, encoding="utf-8", pretty=None, indent=None):
        """Save object to JSON file"""
        try:
            if pretty is None:
                pretty = self.pretty_print
            if indent is None:
                indent = self.indent_size if pretty else None
            
            with open(file_path, 'w', encoding=encoding) as f:
                if pretty:
                    json.dump(obj, f, indent=indent, ensure_ascii=False, separators=(',', ': '))
                else:
                    json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
            return True
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {e}")
            return False
    
    def create_object(self):
        """Create empty JSON object (dictionary)"""
        return {}
    
    def create_array(self):
        """Create empty JSON array (list)"""
        return []
    
    def get_value(self, obj, key, default=None):
        """Get value from JSON object with optional default"""
        if isinstance(obj, dict):
            return obj.get(key, default)
        elif isinstance(obj, list) and isinstance(key, int):
            try:
                return obj[key]
            except IndexError:
                return default
        return default
    
    def set_value(self, obj, key, value):
        """Set value in JSON object"""
        if isinstance(obj, dict):
            obj[key] = value
            return True
        elif isinstance(obj, list) and isinstance(key, int):
            try:
                if key >= len(obj):
                    # Extend list if necessary
                    obj.extend([None] * (key + 1 - len(obj)))
                obj[key] = value
                return True
            except Exception as e:
                print(f"Error setting array value: {e}")
                return False
        return False
    
    def has_key(self, obj, key):
        """Check if object has key"""
        if isinstance(obj, dict):
            return key in obj
        elif isinstance(obj, list) and isinstance(key, int):
            return 0 <= key < len(obj)
        return False
    
    def remove_key(self, obj, key):
        """Remove key from object"""
        if isinstance(obj, dict) and key in obj:
            del obj[key]
            return True
        elif isinstance(obj, list) and isinstance(key, int):
            try:
                obj.pop(key)
                return True
            except IndexError:
                return False
        return False
    
    def get_keys(self, obj):
        """Get all keys from object"""
        if isinstance(obj, dict):
            return list(obj.keys())
        elif isinstance(obj, list):
            return list(range(len(obj)))
        return []
    
    def get_values(self, obj):
        """Get all values from object"""
        if isinstance(obj, dict):
            return list(obj.values())
        elif isinstance(obj, list):
            return obj.copy()
        return []
    
    def get_size(self, obj):
        """Get size of object"""
        if isinstance(obj, (dict, list)):
            return len(obj)
        return 0
    
    def merge_objects(self, obj1, obj2):
        """Merge two JSON objects"""
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            result = obj1.copy()
            result.update(obj2)
            return result
        elif isinstance(obj1, list) and isinstance(obj2, list):
            return obj1 + obj2
        return None
    
    def deep_copy(self, obj):
        """Create deep copy of JSON object"""
        try:
            import copy
            return copy.deepcopy(obj)
        except Exception as e:
            print(f"Error creating deep copy: {e}")
            return None
    
    def validate_json(self, json_string):
        """Validate if string is valid JSON"""
        try:
            json.loads(json_string)
            return True
        except json.JSONDecodeError:
            return False
        except Exception:
            return False
    
    def minify(self, json_string):
        """Minify JSON string (remove whitespace)"""
        try:
            obj = json.loads(json_string)
            return json.dumps(obj, separators=(',', ':'))
        except Exception as e:
            print(f"Error minifying JSON: {e}")
            return None
    
    def prettify(self, json_string, indent=None):
        """Prettify JSON string"""
        try:
            if indent is None:
                indent = self.indent_size
            obj = json.loads(json_string)
            return json.dumps(obj, indent=indent, separators=(',', ': '))
        except Exception as e:
            print(f"Error prettifying JSON: {e}")
            return None
    
    def get_path(self, obj, path, default=None):
        """Get value using dot notation path (e.g., 'user.name')"""
        try:
            current = obj
            for key in path.split('.'):
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list):
                    try:
                        current = current[int(key)]
                    except (ValueError, IndexError):
                        return default
                else:
                    return default
                
                if current is None:
                    return default
            
            return current
        except Exception as e:
            print(f"Error getting path {path}: {e}")
            return default
    
    def set_path(self, obj, path, value):
        """Set value using dot notation path"""
        try:
            keys = path.split('.')
            current = obj
            
            for key in keys[:-1]:
                if isinstance(current, dict):
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                elif isinstance(current, list):
                    try:
                        index = int(key)
                        while len(current) <= index:
                            current.append({})
                        current = current[index]
                    except ValueError:
                        return False
                else:
                    return False
            
            # Set the final value
            final_key = keys[-1]
            if isinstance(current, dict):
                current[final_key] = value
                return True
            elif isinstance(current, list):
                try:
                    index = int(final_key)
                    while len(current) <= index:
                        current.append(None)
                    current[index] = value
                    return True
                except ValueError:
                    return False
            
            return False
        except Exception as e:
            print(f"Error setting path {path}: {e}")
            return False
    
    def to_csv_rows(self, obj):
        """Convert JSON array to CSV-style rows"""
        if not isinstance(obj, list) or not obj:
            return []
        
        try:
            # Get all unique keys from all objects
            all_keys = set()
            for item in obj:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            headers = list(all_keys)
            rows = [headers]
            
            for item in obj:
                if isinstance(item, dict):
                    row = [item.get(key, '') for key in headers]
                    rows.append(row)
            
            return rows
        except Exception as e:
            print(f"Error converting to CSV rows: {e}")
            return []

# Create the module instance
json_module = SonaJSONModule()

# Export for compatibility
__all__ = ['json_module']
