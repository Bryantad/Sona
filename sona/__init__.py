"""
Sona Programming Language v0.8.1
Cognitive Accessibility Edition

SonaCore AI Model: v1.0-production
"""

__version__ = "0.8.1"
__sona_core_version__ = "1.0-production"
__description__ = "Sona Programming Language with OOP Support"

from .interpreter import SonaUnifiedInterpreter as SonaInterpreter

# from .repl import run_repl

__all__ = ["SonaInterpreter", "__version__"]
