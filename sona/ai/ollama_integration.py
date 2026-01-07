"""
Ollama integration for Sona AI features.

Provides a GPT-2 compatible interface backed by local Ollama models.
"""

from __future__ import annotations

import os
from typing import Any

from .local_models import (
    DEFAULT_OLLAMA_MODEL,
    ensure_local_model,
    normalize_ollama_host,
    request_ollama_json,
)


class OllamaIntegration:
    """Local Ollama integration that mirrors the GPT-2 helper API."""

    def __init__(self, model: str | None = None, host: str | None = None, timeout: float = 30.0):
        self.model = model or os.getenv("SONA_OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
        self.host = normalize_ollama_host(host)
        self.timeout = timeout
        self.is_loaded = False
        self.last_error: str | None = None
        self.device = "ollama"
        self.max_length = None

    def _ensure_ready(self) -> bool:
        status = ensure_local_model(self.model, quiet=True, host=self.host)
        self.is_loaded = bool(status.get("installed"))
        if status.get("status") == "error":
            self.last_error = status.get("error") or "Ollama check failed"
            return False
        if not status.get("ollama_running"):
            self.last_error = status.get("error") or "Ollama is not running"
            return False
        if not status.get("installed"):
            self.last_error = f"Model '{self.model}' is not installed"
            return False
        self.last_error = None
        return True

    def load_model(self) -> bool:
        """Validate that the Ollama model is available."""
        status = ensure_local_model(self.model, quiet=True, host=self.host)
        self.is_loaded = bool(status.get("installed"))
        self.last_error = status.get("error")
        return self.is_loaded

    def _generate(self, prompt: str, max_new_tokens: int, temperature: float) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(temperature),
                "num_predict": int(max_new_tokens),
            },
        }
        try:
            response = request_ollama_json(
                self.host,
                "/api/generate",
                payload,
                timeout=self.timeout,
            )
        except Exception as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        return str(response.get("response", ""))

    def generate_completion(
        self,
        prompt: str,
        max_new_tokens: int = 50,
        temperature: float = 0.7,
        do_sample: bool = True,
        num_return_sequences: int = 1,
    ) -> list[str]:
        """Generate text completion using Ollama."""
        _ = do_sample  # Ollama handles sampling via temperature
        if not self._ensure_ready():
            return [f"Error: {self.last_error or 'Ollama not ready'}"]

        results = []
        count = max(1, int(num_return_sequences))
        for _ in range(count):
            try:
                text = self._generate(prompt, max_new_tokens, temperature)
            except Exception as exc:
                return [f"Error: {exc}"]
            results.append(text.strip())
        return results

    def generate_sona_completion(self, prompt: str, max_new_tokens: int = 50) -> str:
        """Generate Sona-specific code completion."""
        completion = self.generate_completion(
            f"Complete this Sona code:\n{prompt}\nCompletion:",
            max_new_tokens=max_new_tokens,
            temperature=0.3,
        )
        return completion[0] if completion else "// Completion not available"

    def generate_code_completion(self, code: str, max_new_tokens: int = 50) -> str:
        """Generate code completion for given code context."""
        completion = self.generate_completion(
            f"Complete this code:\n{code}\nCompletion:",
            max_new_tokens=max_new_tokens,
            temperature=0.3,
        )
        return completion[0] if completion else ""

    def explain_code(self, code: str) -> str:
        """Generate natural language explanation of code."""
        prompt = f"Explain this code in simple terms:\n\n{code}\n\nExplanation:"
        explanations = self.generate_completion(prompt, max_new_tokens=120, temperature=0.4)
        if explanations and explanations[0]:
            return explanations[0].strip()
        return "Unable to generate explanation."

    def suggest_improvements(self, code: str) -> str:
        """Suggest code improvements."""
        prompt = f"Suggest improvements for this code:\n\n{code}\n\nSuggestions:"
        suggestions = self.generate_completion(prompt, max_new_tokens=150, temperature=0.6)
        if suggestions and suggestions[0]:
            return suggestions[0].strip()
        return "No suggestions available."

    def natural_language_to_code(self, description: str, language: str = "python") -> str:
        """Convert natural language description to code."""
        prompt = f"Convert this description to {language} code:\n\n{description}\n\nCode:\n"
        code_generations = self.generate_completion(prompt, max_new_tokens=120, temperature=0.4)
        if code_generations and code_generations[0]:
            return code_generations[0].strip()
        return f"# Unable to generate {language} code for: {description}"

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the configured Ollama model."""
        status = ensure_local_model(self.model, quiet=True, host=self.host)
        return {
            "model": self.model,
            "ollama_host": self.host,
            "is_loaded": self.is_loaded,
            "ollama_running": status.get("ollama_running"),
            "installed": status.get("installed"),
            "last_error": status.get("error"),
        }

    def unload_model(self) -> None:
        """Reset the loaded state (Ollama runs separately)."""
        self.is_loaded = False
