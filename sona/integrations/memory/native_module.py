from __future__ import annotations

from typing import Any

from .client import MemoryDisabledError, RuntimeMemoryClient


class MemoryNativeModuleBridge:
    def __init__(self, interpreter):
        self._interpreter = interpreter

    def memory_search(self, query: str, opts: dict[str, Any] | None = None) -> dict[str, Any]:
        context = self._require_context()
        options = opts or {}
        result = self._client().search_memories(
            self._interpreter,
            context,
            query=query,
            limit=int(options.get("limit", 25)),
            cursor=options.get("cursor"),
            subject=options.get("subject"),
            kind=options.get("kind"),
        )
        return {
            "items": result.get("items", []),
            "count": len(result.get("items", [])),
            "next_cursor": result.get("next_cursor"),
        }

    def memory_record(self, content: str, opts: dict[str, Any] | None = None) -> dict[str, Any]:
        context = self._require_context()
        options = opts or {}
        subject = options.get("subject") or context.default_subject
        return self._client().record_memory(
            self._interpreter,
            context,
            content=content,
            subject=subject,
            kind=options.get("kind", "semantic"),
            confidence=float(options.get("confidence", 0.5)),
            evidence=list(options.get("evidence", [])),
            metadata=dict(options.get("metadata", {})),
        )

    def memory_get_trace(self, trace_id: str) -> dict[str, Any]:
        context = self._require_context()
        return self._client().get_trace(self._interpreter, context, trace_id)

    def memory_reflect(
        self,
        input_text: str | None = None,
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        context = self._require_context()
        options = opts or {}
        reflection_input = input_text or self._default_reflection_input(context)
        response = self._client().run_reflection(
            self._interpreter,
            context,
            input_text=reflection_input,
            agent_id=options.get("agent_id"),
            metadata=dict(options.get("metadata", {})),
            best_effort=False,
        )
        context.auto_reflection_enqueued = response is not None
        return response

    def _default_reflection_input(self, context) -> str:
        parts = [context.input_text]
        if context.last_output_summary:
            parts.append(context.last_output_summary)
        return "\n".join(part for part in parts if part)

    def _client(self) -> RuntimeMemoryClient:
        client = getattr(self._interpreter, "_runtime_memory_client", None)
        if client is None:
            client = RuntimeMemoryClient()
            self._interpreter._runtime_memory_client = client
        return client

    def _require_context(self):
        context = self._interpreter.get_runtime_memory_context()
        if context is None:
            raise MemoryDisabledError("memory integration is unavailable for this run")
        return context
