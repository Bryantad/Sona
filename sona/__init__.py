"""
Sona Programming Language v0.6.0
AI-Assisted Language Development Milestone

SonaCore AI Model: v1.0-production
"""

__version__ = "0.6.0"
__sona_core_version__ = "1.0-production"
__description__ = "Sona Programming Language with AI Assistance"

from .interpreter import SonaInterpreter, run_code
from .repl import run_repl

__all__ = ['SonaInterpreter', 'run_code', 'run_repl', '__version__']
