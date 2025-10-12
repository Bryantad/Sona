"""
Sona Language Type System - Simple Type Checker

This module provides a simple type checker for basic validation.
Minimal implementation for v0.9.4.

Author: Sona Development Team
Version: 0.9.4
"""

from typing import Any


class SimpleTypeChecker:
    """Simple type checker for basic validation"""
    
    @staticmethod
    def check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'int': int,
            'str': str,
            'bool': bool,
            'float': float,
        }
        
        if expected_type not in type_map:
            return True  # Unknown types pass validation
        
        return isinstance(value, type_map[expected_type])


def check_type(value: Any, expected_type: str) -> bool:
    """Convenience function for type checking"""
    return SimpleTypeChecker.check_type(value, expected_type)
