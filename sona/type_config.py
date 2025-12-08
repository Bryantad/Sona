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

    def should_fail_on_error(self):
        """Return True when type errors should abort execution."""
        return self.get_effective_mode() == TypeCheckMode.ON

    def should_exit_with_error(self):
        """Determine if CLI should exit with failure after logging."""
        return self.should_fail_on_error()


class TypeLogger:
    """Collects runtime type checking events for CLI summaries."""

    def __init__(self, config: TypeConfig):
        self._config = config
        self.reset()

    def reset(self):
        self._events = []
        self._stats = {'errors': 0, 'warnings': 0, 'info': 0}

    def log_type_error(self, **payload):
        severity = 'error' if payload.get('mode') == 'on' else 'warning'
        entry = {
            'severity': severity,
            'code': payload.get('code', 'S-2000'),
            'fn_name': payload.get('fn_name', 'unknown'),
            'param_name': payload.get('param_name', 'value'),
            'spec': payload.get('spec', 'unknown'),
            'value_type': payload.get('value_type', 'unknown'),
            'fix_tip': payload.get('fix_tip') or 'Align argument type with specification.'
        }
        self._events.append(entry)
        key = 'errors' if severity == 'error' else 'warnings'
        self._stats[key] = self._stats.get(key, 0) + 1

    def get_summary(self) -> str:
        if not self._events:
            return '[Types] No issues detected.'

        lines = ['[Types] Runtime type checker summary:']
        for event in self._events[:10]:
            lines.append(
                f" - {event['severity'].upper()} {event['code']} "
                f"{event['fn_name']}::{event['param_name']} expected {event['spec']} "
                f"but saw {event['value_type']}. Fix: {event['fix_tip']}"
            )

        remaining = len(self._events) - 10
        if remaining > 0:
            lines.append(f" - ... {remaining} more issue(s) hidden ...")

        return '\n'.join(lines)

    def should_exit_with_error(self) -> bool:
        return self._config.should_exit_with_error() and self._stats.get('errors', 0) > 0


# Global configuration + logger instances
global_type_config = TypeConfig()
type_logger = TypeLogger(global_type_config)

def configure_types(cli_mode=None):
    """Configure type checking mode from CLI"""
    global global_type_config, type_logger
    if cli_mode:
        global_type_config.set_cli_mode(cli_mode)
    type_logger.reset()

def get_type_config():
    """Get the global type configuration instance"""
    return global_type_config

def get_type_logger():
    """Get type system logger instance"""
    return type_logger


def create_fix_tip(error_code: str, expected_type: str, actual_type: str) -> str:
    """Generate a concise fix tip for type checker errors."""
    expected = (expected_type or '').strip()
    actual = (actual_type or '').strip()

    # Specific guidance for common numeric/string issues
    if expected.lower() == 'int' and actual.lower() == 'str':
        return 'Convert the value to int before passing it (int(value))'
    if expected.lower() == 'str' and actual.lower() in {'int', 'float', 'bool'}:
        return 'Cast to string before use (str(value))'
    if expected.lower() == 'bool' and actual.lower() in {'int', 'str'}:
        return 'Normalize to True/False before calling this function'

    # Collection hints
    if expected.lower().startswith('list[') and actual.lower() == 'list':
        return 'Ensure every list element matches the declared inner type'
    if expected.lower().startswith('dict[') and actual.lower() == 'dict':
        return 'Verify both keys and values conform to the declared schema'

    # Fallback generic suggestion referencing error code
    tip_parts = ['Ensure the value matches the expected type']
    if expected:
        tip_parts.append(f"({expected})")
    if error_code:
        tip_parts.append(f"[{error_code}]")
    return ' '.join(tip_parts).strip()
