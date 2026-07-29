"""Lazy public adapters for the historical :mod:`sona.ai` surface."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import ContextEnvelope, TaskRequest, TaskType
from .service import DeveloperIntelligenceService


class DeveloperIntelligenceCompatibilityAdapter:
    """Legacy-shaped methods backed by structured developer tasks only."""

    def __init__(self, workspace: str | Path | None = None, provider_id: str | None = None):
        self.workspace = Path(workspace or Path.cwd()).resolve()
        self.provider_id = provider_id

    def run_task(self, task_type: str | TaskType, instruction: str, *, context: str = ""):
        kind = task_type if isinstance(task_type, TaskType) else TaskType(str(task_type))
        request = TaskRequest(
            kind, instruction, provider_id=self.provider_id,
            context=ContextEnvelope(selected_text=context or None, origin="sona.ai-compat"),
        )
        return DeveloperIntelligenceService(self.workspace).execute(request)

    def generate_completion(self, prompt: str, max_new_tokens: int = 128, **_kwargs: Any) -> list[str]:
        result = self.run_task(TaskType.COMPLETE, "Complete the supplied developer code.", context=prompt)
        return [result.summary]

    def generate_code_completion(self, context: str, max_new_tokens: int = 64, **_kwargs: Any) -> list[str]:
        return self.generate_completion(context, max_new_tokens=max_new_tokens)

    def explain_code(self, code: str, style: str = "simple") -> str:
        result = self.run_task(TaskType.EXPLAIN, f"Explain this developer code in {style} style.", context=code)
        return result.summary

    def suggest_improvements(self, code: str, **_kwargs: Any) -> list[str]:
        result = self.run_task(TaskType.SUGGEST, "Suggest improvements to this developer code.", context=code)
        return [result.summary]


_BACKEND: DeveloperIntelligenceCompatibilityAdapter | None = None


def get_ai_backend(preferred: str | None = None):
    global _BACKEND
    if _BACKEND is None or (_BACKEND.provider_id != preferred and preferred is not None):
        provider = {"local": "deterministic", "offline": "deterministic"}.get(str(preferred or "").lower(), preferred)
        _BACKEND = DeveloperIntelligenceCompatibilityAdapter(provider_id=provider)
    return _BACKEND


class CodeCompletion:
    def __init__(self):
        self.backend = get_ai_backend()

    def get_completion(self, code_context: str, cursor_position: int = -1) -> list[str]:
        context = code_context if cursor_position < 0 else code_context[:cursor_position]
        return self.backend.generate_code_completion(context)


class NaturalLanguageProcessor:
    def __init__(self):
        self.backend = get_ai_backend()

    def explain_code(self, code: str, style: str = "simple") -> str:
        return self.backend.explain_code(code, style)

    def suggest_improvements(self, _description: str, current_code: str) -> list[str]:
        return self.backend.suggest_improvements(current_code)
