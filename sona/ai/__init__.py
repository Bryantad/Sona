"""Sona AI integration package.

AI backends are imported lazily so normal interpreter startup does not load
model libraries such as transformers or probe local model servers.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


__version__ = "0.8.2"
_LAZY_SYMBOLS = {
    "get_ai_backend": ".ai_backend",
    "CodeCompletion": ".code_completion",
    "CognitiveAssistant": ".cognitive_assistant",
    "GPT2Integration": ".gpt2_integration",
    "NaturalLanguageProcessor": ".natural_language",
    "OllamaIntegration": ".ollama_integration",
}

__all__ = [
    "GPT2Integration",
    "OllamaIntegration",
    "get_ai_backend",
    "CodeCompletion", 
    "CognitiveAssistant",
    "NaturalLanguageProcessor"
]


def __getattr__(name: str) -> Any:
    module_name = _LAZY_SYMBOLS.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
