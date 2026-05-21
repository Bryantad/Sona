from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .client import EventKind, RuntimeMemoryClient
from .context import RuntimeMemoryContext, summarize_value


class RuntimeMemoryInstrumentation:
    def __init__(self, interpreter, client: RuntimeMemoryClient | None = None):
        self._interpreter = interpreter
        self._client = client or RuntimeMemoryClient()

    @property
    def client(self) -> RuntimeMemoryClient:
        return self._client

    def create_context(self, *, file_path: str | None) -> RuntimeMemoryContext:
        project_root = getattr(self._interpreter, "project_root", None)
        argv = list(sys.argv[1:])
        resolved_path = file_path or "<string>"
        entrypoint = Path(resolved_path).stem or "main"
        return RuntimeMemoryContext.create_for_cli_run(
            project_root=project_root,
            program_path=resolved_path,
            entrypoint=entrypoint,
            argv=argv,
        )

    def attach_context(self, context: RuntimeMemoryContext) -> None:
        self._interpreter._runtime_memory_context = context
        self._interpreter._runtime_memory_client = self._client

    def clear_context(self) -> None:
        self._interpreter._runtime_memory_context = None
        self._interpreter._runtime_memory_client = None

    def on_run_start(self, context: RuntimeMemoryContext) -> None:
        self._client.append_event(
            self._interpreter,
            context,
            event_kind=EventKind.SESSION_STARTED,
            payload={
                "program_path": context.program_path,
                "entrypoint": context.entrypoint,
                "input_kind": context.input_kind.value,
            },
            best_effort=True,
        )
        self._client.append_event(
            self._interpreter,
            context,
            event_kind=EventKind.TRACE_OPENED,
            payload={
                "name": context.entrypoint,
                "program_path": context.program_path,
                "entrypoint": context.entrypoint,
                "input_kind": context.input_kind.value,
            },
            best_effort=True,
        )

    def on_input_bound(self, context: RuntimeMemoryContext) -> None:
        self._client.append_event(
            self._interpreter,
            context,
            event_kind=EventKind.MESSAGE_USER_RECEIVED,
            payload={
                "input_kind": context.input_kind.value,
                "input_text": context.input_text,
                "invocation_summary": context.invocation_summary,
            },
            best_effort=True,
        )

    def on_root_result(self, context: RuntimeMemoryContext, result: Any) -> None:
        output_summary = summarize_value(result).strip()
        if not output_summary:
            return
        context.last_output_summary = output_summary
        context.last_output_kind = type(result).__name__
        self._client.append_event(
            self._interpreter,
            context,
            event_kind=EventKind.MESSAGE_MODEL_EMITTED,
            payload={
                "output_preview": output_summary,
                "output_kind": context.last_output_kind,
                "return_type": type(result).__name__,
            },
            best_effort=True,
        )

    def on_run_finish(self, context: RuntimeMemoryContext, *, result: Any, error: Exception | None) -> None:
        trace_closed = self._client.append_event(
            self._interpreter,
            context,
            event_kind=EventKind.TRACE_CLOSED,
            payload={
                "status": "failed" if error else "succeeded",
                "result_summary": summarize_value(result) if error is None else None,
                "error_type": type(error).__name__ if error else None,
                "error_message": summarize_value(str(error)) if error else None,
                "tool_call_count": context.tool_call_count,
            },
            best_effort=True,
        )
        context.last_trace_closed_attempted = trace_closed.invoked
        self._client.append_event(
            self._interpreter,
            context,
            event_kind=EventKind.SESSION_ENDED,
            payload={"status": "failed" if error else "succeeded"},
            best_effort=True,
        )
        self._maybe_enqueue_reflection(context)

    def _maybe_enqueue_reflection(self, context: RuntimeMemoryContext) -> None:
        if not self._client.config.auto_reflect:
            return
        if context.auto_reflection_enqueued or not context.last_trace_closed_attempted:
            return
        if not context.input_text or not (context.last_output_summary or context.tool_call_count > 0):
            return
        context.auto_reflection_enqueued = True
        reflection_input = "\n".join(
            part for part in (context.input_text, context.last_output_summary) if part
        )
        self._client.run_reflection(
            self._interpreter,
            context,
            input_text=reflection_input,
            agent_id=context.agent_id,
            metadata={"trigger": "top_level_run"},
            best_effort=True,
        )
