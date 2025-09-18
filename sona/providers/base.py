"""Provider plugin base abstraction.

Providers should subclass ``AIProvider`` and implement ``_raw_infer``.
Feature integrations (cache, breaker, perf logging, policy) are centrally
handled to keep provider implementations minimal.
"""
from __future__ import annotations

import abc
import hashlib
import time
from typing import Any

from ..ai.cache import get_cache
from ..ai.retry import get_breaker
from ..perf.logging import log_perf
from ..policy import deny_text, enforce_output, provider_allowed


def _hash_input(model: str, prompt: str) -> str:
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    h.update(b"::")
    h.update(prompt.encode("utf-8"))
    return h.hexdigest()


class AIProvider(abc.ABC):
    name: str = "base"

    def infer(self, model: str, prompt: str, **params: Any) -> str:
        if not provider_allowed(self.name):
            raise PermissionError(
                f"Provider '{self.name}' not allowed by policy"
            )
        deny = deny_text(prompt)
        if deny:
            raise ValueError(f"Prompt denied by policy pattern: {deny}")

        cache_key = _hash_input(model, prompt)
        cache = get_cache()
        if cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        breaker = get_breaker()
        if breaker and not breaker.allow():
            raise RuntimeError("Circuit breaker open for provider operations")

        start = time.time()
        success = False
        try:
            output = self._raw_infer(model, prompt, **params)
            enforce_output(output)
            success = True
            return output
        finally:
            duration_ms = int((time.time() - start) * 1000)
            if breaker:
                breaker.record(success)
            if success and cache:
                cache.set(cache_key, output)
            log_perf(
                "ai_infer",
                provider=self.name,
                model=model,
                success=success,
                ms=duration_ms,
            )

    @abc.abstractmethod
    def _raw_infer(
        self, model: str, prompt: str, **params: Any
    ) -> str:  # pragma: no cover
        raise NotImplementedError
