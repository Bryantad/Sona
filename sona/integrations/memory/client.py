from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .context import RuntimeMemoryContext, sanitize_value


class MemoryDisabledError(RuntimeError):
    """Raised when memory integration is unavailable for the current call."""


class EventKind(StrEnum):
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    TRACE_OPENED = "trace.opened"
    TRACE_CLOSED = "trace.closed"
    MESSAGE_USER_RECEIVED = "message.user_received"
    MESSAGE_MODEL_EMITTED = "message.model_emitted"
    TOOL_CALL_REQUESTED = "tool.call_requested"
    TOOL_CALL_SUCCEEDED = "tool.call_succeeded"
    TOOL_CALL_FAILED = "tool.call_failed"
    MEMORY_RECORDED = "memory.recorded"
    REFLECTION_RUN_REQUESTED = "reflection.run_requested"


@dataclass(frozen=True)
class MemoryClientConfig:
    enabled: bool
    base_url: str | None
    token: str | None
    timeout_seconds: float
    auto_reflect: bool
    disabled_reason: str | None = None

    @classmethod
    def from_environment(cls) -> MemoryClientConfig:
        enabled = os.getenv("SONA_MEMORY_ENABLED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        timeout_raw = os.getenv("SONA_MEMORY_TIMEOUT_SECONDS", "10").strip() or "10"
        auto_reflect = os.getenv("SONA_MEMORY_AUTO_REFLECT", "true").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError:
            timeout_seconds = 10.0
        base_url = os.getenv("SONA_MEMORY_BASE_URL", "").strip() or None
        token = os.getenv("SONA_MEMORY_TOKEN", "").strip() or None
        disabled_reason = None
        if enabled and not base_url:
            enabled = False
            disabled_reason = "SONA_MEMORY_BASE_URL is required when SONA_MEMORY_ENABLED=true"
        elif enabled and not token:
            enabled = False
            disabled_reason = "SONA_MEMORY_TOKEN is required when SONA_MEMORY_ENABLED=true"
        return cls(
            enabled=enabled,
            base_url=base_url,
            token=token,
            timeout_seconds=max(timeout_seconds, 0.1),
            auto_reflect=auto_reflect,
            disabled_reason=disabled_reason,
        )


@dataclass(frozen=True)
class AppendAttempt:
    response: dict[str, Any] | None
    sequence_no: int | None
    idempotency_key: str | None
    invoked: bool


class RuntimeMemoryClient:
    def __init__(self, config: MemoryClientConfig | None = None):
        self._config = config or MemoryClientConfig.from_environment()

    @property
    def config(self) -> MemoryClientConfig:
        return self._config

    def append_event(
        self,
        interpreter,
        context: RuntimeMemoryContext,
        *,
        event_kind: EventKind | str,
        payload: dict[str, Any],
        best_effort: bool = False,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> AppendAttempt:
        if not self._config.enabled or not context.memory_enabled:
            if best_effort:
                if self._config.disabled_reason and context.memory_enabled:
                    context.disable_memory(self._config.disabled_reason)
                return AppendAttempt(response=None, sequence_no=None, idempotency_key=None, invoked=False)
            raise MemoryDisabledError(self._disabled_message(context))

        event_kind_value = event_kind.value if isinstance(event_kind, EventKind) else str(event_kind)
        sequence_no, idempotency_key = context.next_event_attempt(event_kind_value)
        request_payload = {
            "namespace": context.namespace,
            "event": {
                "namespace": context.namespace,
                "event_kind": event_kind_value,
                "actor": context.actor.as_dict(),
                "session_id": context.session_id,
                "trace_id": context.trace_id,
                "causation_id": causation_id,
                "correlation_id": correlation_id,
                "provenance": {
                    "sona_runtime": {
                        "sequence_no": sequence_no,
                        "program_path": context.program_path,
                        "entrypoint": context.entrypoint,
                        "input_kind": context.input_kind.value,
                    },
                    **(provenance or {}),
                },
                "payload": sanitize_value(payload),
            },
        }
        try:
            response = self._request_json(
                interpreter,
                method="POST",
                path="/v1/events",
                payload=request_payload,
                idempotency_key=idempotency_key,
            )
            return AppendAttempt(
                response=response,
                sequence_no=sequence_no,
                idempotency_key=idempotency_key,
                invoked=True,
            )
        except Exception as exc:
            if best_effort:
                context.disable_memory(str(exc))
                return AppendAttempt(
                    response=None,
                    sequence_no=sequence_no,
                    idempotency_key=idempotency_key,
                    invoked=True,
                )
            context.disable_memory(str(exc))
            raise

    def record_memory(
        self,
        interpreter,
        context: RuntimeMemoryContext,
        *,
        content: str,
        subject: str,
        kind: str = "semantic",
        confidence: float = 0.5,
        evidence: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._require_available(context)
        sequence_no, idempotency_key = context.next_event_attempt(EventKind.MEMORY_RECORDED.value)
        payload = {
            "namespace": context.namespace,
            "actor": context.actor.as_dict(),
            "session_id": context.session_id,
            "trace_id": context.trace_id,
            "subject": subject,
            "content": content,
            "kind": kind,
            "confidence": confidence,
            "evidence": list(evidence or []),
            "metadata": {
                **sanitize_value(metadata or {}),
                "_sona_runtime": {
                    "sequence_no": sequence_no,
                    "program_path": context.program_path,
                    "entrypoint": context.entrypoint,
                    "input_kind": context.input_kind.value,
                },
            },
        }
        try:
            return self._request_json(
                interpreter,
                method="POST",
                path="/v1/memories",
                payload=payload,
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            context.disable_memory(str(exc))
            raise

    def search_memories(
        self,
        interpreter,
        context: RuntimeMemoryContext,
        *,
        query: str,
        limit: int = 25,
        cursor: str | None = None,
        subject: str | None = None,
        kind: str | None = None,
    ) -> dict[str, Any]:
        self._require_available(context)
        return self._request_json(
            interpreter,
            method="POST",
            path="/v1/memories/search",
            payload={
                "namespace": context.namespace,
                "query": query,
                "limit": limit,
                "cursor": cursor,
                "subject": subject,
                "kind": kind,
            },
        )

    def get_trace(self, interpreter, context: RuntimeMemoryContext, trace_id: str) -> dict[str, Any]:
        self._require_available(context)
        return self._request_json(
            interpreter,
            method="GET",
            path=f"/v1/traces/{trace_id}",
            query={"namespace": context.namespace},
        )

    def run_reflection(
        self,
        interpreter,
        context: RuntimeMemoryContext,
        *,
        input_text: str,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        best_effort: bool = False,
    ) -> dict[str, Any] | None:
        if not self._config.enabled or not context.memory_enabled:
            if best_effort:
                if self._config.disabled_reason and context.memory_enabled:
                    context.disable_memory(self._config.disabled_reason)
                return None
            raise MemoryDisabledError(self._disabled_message(context))

        sequence_no, idempotency_key = context.next_event_attempt(EventKind.REFLECTION_RUN_REQUESTED.value)
        payload = {
            "namespace": context.namespace,
            "actor": context.actor.as_dict(),
            "agent_id": agent_id or context.agent_id or "sona.interpreter.default",
            "session_id": context.session_id,
            "trace_id": context.trace_id,
            "input_text": input_text,
            "metadata": {
                **sanitize_value(metadata or {}),
                "_sona_runtime": {
                    "sequence_no": sequence_no,
                    "program_path": context.program_path,
                    "entrypoint": context.entrypoint,
                    "input_kind": context.input_kind.value,
                },
            },
        }
        try:
            return self._request_json(
                interpreter,
                method="POST",
                path="/v1/reflections:run",
                payload=payload,
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            if best_effort:
                context.disable_memory(str(exc))
                return None
            context.disable_memory(str(exc))
            raise

    def _request_json(
        self,
        interpreter,
        *,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self._config.base_url or not self._config.token:
            raise MemoryDisabledError(self._config.disabled_reason or "memory integration is not configured")

        base_url = self._config.base_url.rstrip("/")
        url = f"{base_url}{path}"
        if query:
            query_text = urlencode({key: value for key, value in query.items() if value is not None})
            if query_text:
                url = f"{url}?{query_text}"

        data = None
        headers = {
            "Authorization": f"Bearer {self._config.token}",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        request = Request(url, data=data, headers=headers, method=method)
        with self._transport_guard(interpreter):
            try:
                with urlopen(request, timeout=self._config.timeout_seconds) as response:
                    raw = response.read()
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"memory server HTTP {exc.code}: {detail}") from exc
            except URLError as exc:
                raise RuntimeError(f"memory transport error: {exc}") from exc
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    @contextmanager
    def _transport_guard(self, interpreter):
        if interpreter is None:
            yield
            return
        interpreter._runtime_memory_transport_guard_depth += 1
        try:
            yield
        finally:
            interpreter._runtime_memory_transport_guard_depth = max(
                0,
                interpreter._runtime_memory_transport_guard_depth - 1,
            )

    def _require_available(self, context: RuntimeMemoryContext) -> None:
        if not self._config.enabled or not context.memory_enabled:
            raise MemoryDisabledError(self._disabled_message(context))

    def _disabled_message(self, context: RuntimeMemoryContext) -> str:
        if self._config.disabled_reason:
            return self._config.disabled_reason
        if not context.memory_enabled and context.lifecycle_failures:
            return context.lifecycle_failures[-1]
        return "memory integration is unavailable for this run"
