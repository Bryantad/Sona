"""
Sona Programming Language v0.7.1
Performance & Type Foundation Release

SonaCore AI Model: v1.0-production
"""

__version__ = "0.7.1"
__sona_core_version__ = "1.0-production"
__description__ = "Sona Programming Language with OOP Support"

from .interpreter import SonaInterpreter
# from .repl import run_repl

__all__ = ['SonaInterpreter', '__version__']
