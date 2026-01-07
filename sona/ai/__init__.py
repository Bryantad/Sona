"""
Sona AI Integration Module - v0.8.2

This module provides AI-powered features for cognitive programming including:
- GPT-2 based code completion
- Natural language to code conversion  
- Cognitive assistance and suggestions
- AI-powered debugging and optimization
"""

from .ai_backend import get_ai_backend
from .code_completion import CodeCompletion
from .cognitive_assistant import CognitiveAssistant
from .gpt2_integration import GPT2Integration
from .natural_language import NaturalLanguageProcessor
from .ollama_integration import OllamaIntegration


__version__ = "0.8.2"
__all__ = [
    "GPT2Integration",
    "OllamaIntegration",
    "get_ai_backend",
    "CodeCompletion", 
    "CognitiveAssistant",
    "NaturalLanguageProcessor"
]
