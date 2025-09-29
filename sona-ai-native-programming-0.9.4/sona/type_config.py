#!/usr/bin/env python3
"""Sona Type System Configuration Manager"""

import os
import json
import logging
import time
import fnmatch
from pathlib import Path
from typing import Optional, List
from enum import Enum

class TypeCheckMode(Enum):
    """Type checking modes"""
    OFF = "off"
    ON = "on"
    WARN = "warn"

class TypeConfig:
    """Global configuration manager for Sona type system"""
    
    def __init__(self):
        # Core configuration state
        self.cli_mode = None  # CLI override mode
        self.env_mode = None  # Environment variable mode
        self.config_mode = None  # Config file mode
        
        # Operational state
        self.current_file = None
        self.excluded_files = set()
        self.correlation_id = None
        
        # Logging configuration
        self.log_level = "errors"  # all, errors, silent
        self.logger = None
        
        # Load environment and config on init
        self._load_env_config()
        self._load_config_file()
    
    def _load_env_config(self):
        """Load configuration from environment variables"""
        env_mode = os.getenv('SONA_TYPES')
        if env_mode and env_mode.lower() in ['off', 'on', 'warn']:
            self.env_mode = TypeCheckMode(env_mode.lower())
    
    def _load_config_file(self):
        """Load configuration from sona.config.json if present"""
        config_path = Path('sona.config.json')
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if 'type_checking' in config_data:
                        mode_str = config_data['type_checking'].get('mode', 'off')
                        if mode_str in ['off', 'on', 'warn']:
                            self.config_mode = TypeCheckMode(mode_str)
                        
                        # Load exclusions
                        exclusions = config_data['type_checking'].get('exclude', [])
                        for pattern in exclusions:
                            self.excluded_files.add(pattern)
            except (json.JSONDecodeError, KeyError):
                pass  # Ignore malformed config files
    
    def get_effective_mode(self):
        """Get the effective mode using precedence: CLI > ENV > Config > OFF"""
        if self.cli_mode is not None:
            return self.cli_mode
        elif self.env_mode is not None:
            return self.env_mode
        elif self.config_mode is not None:
            return self.config_mode
        else:
            return TypeCheckMode.OFF
    
    def set_cli_mode(self, mode):
        """Set CLI override mode"""
        if isinstance(mode, str):
            mode = TypeCheckMode(mode.lower())
        self.cli_mode = mode
    
    def set_current_file(self, file_path):
        """Set the current file being processed"""
        self.current_file = file_path
    
    def is_file_excluded(self, file_path):
        """Check if a file should be excluded from type checking"""
        if not file_path:
            return False
        
        file_path = Path(file_path).resolve()
        for pattern in self.excluded_files:
            if fnmatch.fnmatch(str(file_path), pattern):
                return True
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        return False
    
    def should_check_types(self):
        """Determine if type checking should be active"""
        mode = self.get_effective_mode()
        return mode in [TypeCheckMode.ON, TypeCheckMode.WARN]
    
    def should_exit_with_error(self):
        """Determine if type errors should cause program exit"""
        mode = self.get_effective_mode()
        return mode == TypeCheckMode.ON  # Only exit on ON mode, not WARN
    
    def set_correlation_id(self, correlation_id):
        """Set correlation ID for request tracking"""
        self.correlation_id = correlation_id
    
    def set_log_level(self, level):
        """Set logging level: all, errors, silent"""
        if level in ['all', 'errors', 'silent']:
            self.log_level = level

# Global configuration instance
global_type_config = TypeConfig()

def configure_types(cli_mode=None):
    """Configure type checking mode from CLI"""
    global global_type_config
    if cli_mode:
        global_type_config.set_cli_mode(cli_mode)

def get_type_config():
    """Get the global type configuration instance"""
    return global_type_config

def get_type_logger():
    """Get type system logger instance"""
    return global_type_config
