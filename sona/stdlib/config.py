"""
config - Configuration management for Sona stdlib

Provides utilities for loading and merging configuration from multiple sources:
- load: Load config from INI/TOML files and environment variables
- Supports profile overlays and environment variable prefixes
"""

import os
import configparser


def load(paths=None, env_prefix="SONA_", profile=None):
    """
    Load configuration from multiple sources with merging.
    
    Loads configuration in priority order (later sources override earlier):
    1. Config files (in order provided)
    2. Environment variables (with optional prefix)
    3. Profile-specific overrides
    
    Args:
        paths: List of config file paths (INI or TOML format)
               If None, looks for default files: config.ini, config.toml
        env_prefix: Prefix for environment variables (default "SONA_")
                   Example: SONA_DATABASE_HOST → database.host
        profile: Optional profile name for profile-specific overrides
    
    Returns:
        Dictionary with merged configuration
    
    Example:
        # Load from default files + env vars
        cfg = config.load()
        print(cfg["database"]["host"])
        
        # Load specific files with custom env prefix
        cfg = config.load(paths=["app.ini", "local.ini"], env_prefix="APP_")
        
        # Load with profile override
        cfg = config.load(profile="production")
    """
    config_data = {}
    
    # Default paths if none provided
    if paths is None:
        paths = []
        if os.path.exists('config.ini'):
            paths.append('config.ini')
        if os.path.exists('config.toml'):
            paths.append('config.toml')
    
    # Load config files
    for path in paths:
        if not os.path.exists(path):
            continue
        
        if path.endswith('.ini'):
            file_config = _load_ini(path)
        elif path.endswith('.toml'):
            file_config = _load_toml(path)
        else:
            # Try INI as default
            file_config = _load_ini(path)
        
        # Merge file config into main config
        config_data = _deep_merge(config_data, file_config)
    
    # Load environment variables
    env_config = _load_env(env_prefix)
    config_data = _deep_merge(config_data, env_config)
    
    # Apply profile overrides if specified
    if profile and 'profiles' in config_data:
        if profile in config_data['profiles']:
            profile_config = config_data['profiles'][profile]
            config_data = _deep_merge(config_data, profile_config)
    
    return config_data


def _load_ini(path):
    """Load configuration from INI file."""
    parser = configparser.ConfigParser()
    parser.read(path)
    
    config_data = {}
    for section in parser.sections():
        config_data[section] = dict(parser[section])
    
    return config_data


def _load_toml(path):
    """Load configuration from TOML file."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            raise RuntimeError(
                "TOML support requires tomllib (Python 3.11+) or tomli package"
            )
    
    with open(path, 'rb') as f:
        return tomllib.load(f)


def _load_env(prefix):
    """Load configuration from environment variables."""
    config_data = {}
    
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        
        # Remove prefix and convert to nested structure
        # Example: SONA_DATABASE_HOST → database.host
        config_key = key[len(prefix):].lower()
        parts = config_key.split('_')
        
        # Build nested dict
        current = config_data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set final value
        current[parts[-1]] = value
    
    return config_data


def _deep_merge(base, override):
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary with override values
    
    Returns:
        New merged dictionary
    """
    result = dict(base)
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = _deep_merge(result[key], value)
        else:
            # Override value
            result[key] = value
    
    return result


def get(config, key_path, default=None):
    """
    Get nested config value using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path (e.g., "database.host")
        default: Default value if not found
    
    Returns:
        Config value or default
    
    Example:
        host = config.get(cfg, "database.host", "localhost")
    """
    parts = key_path.split('.')
    current = config
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current


def set_value(config, key_path, value):
    """
    Set nested config value using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path
        value: Value to set
    
    Example:
        config.set_value(cfg, "database.port", 5432)
    """
    parts = key_path.split('.')
    current = config
    
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    current[parts[-1]] = value


def has(config, key_path):
    """
    Check if config key exists.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path
    
    Returns:
        True if exists
    
    Example:
        if config.has(cfg, "database.password"):
            print("Password configured")
    """
    parts = key_path.split('.')
    current = config
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False
    
    return True


def merge(base, *overrides):
    """
    Merge multiple config dictionaries.
    
    Args:
        base: Base configuration
        overrides: Additional configs to merge (later ones override)
    
    Returns:
        Merged configuration
    
    Example:
        merged = config.merge(defaults, user_config, env_overrides)
    """
    result = dict(base)
    for override in overrides:
        result = _deep_merge(result, override)
    return result


def from_dict(data):
    """
    Create config from dictionary.
    
    Args:
        data: Dictionary
    
    Returns:
        Configuration dictionary
    
    Example:
        cfg = config.from_dict({"debug": True, "port": 8080})
    """
    return dict(data)


__all__ = [
    'load',
    'get',
    'set_value',
    'has',
    'merge',
    'from_dict'
]
