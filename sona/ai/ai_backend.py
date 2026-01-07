"""
AI backend selector for Sona.

Chooses between Ollama and GPT-2 based on environment and availability.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_AI_BACKEND: Any | None = None


def _normalize_choice(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in {"ollama", "local", "offline"}:
        return "ollama"
    if lowered in {"gpt2", "gpt-2", "gpt_2"}:
        return "gpt2"
    return None


def _gpt2_model_exists() -> bool:
    try:
        model_path = Path(__file__).resolve().parents[2] / "models" / "gpt2"
    except Exception:
        return False
    return model_path.exists()


def _init_ollama(model: str | None = None, host: str | None = None):
    from .ollama_integration import OllamaIntegration

    return OllamaIntegration(model=model, host=host)


def _init_gpt2():
    from .gpt2_integration import GPT2Integration

    return GPT2Integration()


def get_ai_backend(preferred: str | None = None):
    """Return the active AI backend instance (singleton)."""
    global _AI_BACKEND
    if _AI_BACKEND is not None:
        return _AI_BACKEND

    choice = _normalize_choice(preferred or os.getenv("SONA_AI_BACKEND"))
    if choice == "ollama":
        _AI_BACKEND = _init_ollama()
        return _AI_BACKEND
    if choice == "gpt2":
        _AI_BACKEND = _init_gpt2()
        return _AI_BACKEND

    model_env = os.getenv("SONA_OLLAMA_MODEL")
    status = None
    try:
        from .local_models import DEFAULT_OLLAMA_MODEL, ensure_local_model

        status = ensure_local_model(model_env or DEFAULT_OLLAMA_MODEL, quiet=True)
    except Exception:
        status = None

    if status and status.get("ollama_running") and status.get("installed"):
        _AI_BACKEND = _init_ollama(
            model=status.get("model") or model_env,
            host=status.get("ollama_host"),
        )
        return _AI_BACKEND

    if _gpt2_model_exists():
        _AI_BACKEND = _init_gpt2()
        return _AI_BACKEND

    if status and status.get("ollama_running"):
        _AI_BACKEND = _init_ollama(
            model=status.get("model") or model_env,
            host=status.get("ollama_host"),
        )
        return _AI_BACKEND

    _AI_BACKEND = _init_gpt2()
    return _AI_BACKEND


def reset_ai_backend() -> None:
    """Reset the cached backend instance."""
    global _AI_BACKEND
    _AI_BACKEND = None
