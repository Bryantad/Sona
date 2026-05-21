from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|authorization)",
    re.IGNORECASE,
)
SENSITIVE_INLINE_PATTERN = re.compile(
    r"(?i)(password|secret|token|api[_-]?key|authorization)\s*[:=]\s*([^\s,;]+)"
)


class TopLevelInputKind(StrEnum):
    CHAT_PROMPT = "chat_prompt"
    CLI_PROGRAM_RUN = "cli_program_run"
    REPL_EVAL = "repl_eval"
    API_EXECUTE = "api_execute"


@dataclass(frozen=True)
class RuntimeActorRef:
    actor_type: str
    actor_id: str

    def as_dict(self) -> dict[str, str]:
        return {
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
        }


def sanitize_text(text: str) -> str:
    return SENSITIVE_INLINE_PATTERN.sub(
        lambda match: f"{match.group(1)}=[REDACTED]",
        text,
    )


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_KEY_PATTERN.search(str(key)):
                sanitized[str(key)] = "[REDACTED]"
            else:
                sanitized[str(key)] = sanitize_value(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_value(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def summarize_value(value: Any, *, limit: int = 240) -> str:
    sanitized = sanitize_value(value)
    if isinstance(sanitized, (dict, list)):
        text = json.dumps(sanitized, sort_keys=True)
    else:
        text = str(sanitized)
    return text[:limit]


def resolve_project_name(project_root: str | Path | None) -> str:
    if project_root is None:
        return "default"
    path = Path(project_root)
    name = path.name.strip()
    if name:
        return name
    return "default"


def resolve_namespace(project_root: str | Path | None) -> str:
    explicit = os.getenv("SONA_MEMORY_NAMESPACE", "").strip()
    if explicit:
        return explicit
    project_name = resolve_project_name(project_root)
    return f"/projects/{project_name or 'default'}"


def resolve_agent_id(project_root: str | Path | None) -> str:
    explicit = os.getenv("SONA_MEMORY_AGENT_ID", "").strip()
    if explicit:
        return explicit
    project_name = resolve_project_name(project_root)
    return f"sona.interpreter.{project_name or 'default'}"


def build_invocation_summary(
    *,
    program_path: str,
    entrypoint: str,
    argv: list[str] | None = None,
) -> str:
    program_name = Path(program_path).name if program_path else entrypoint
    flags = [
        token.split("=", maxsplit=1)[0]
        for token in (argv or [])
        if isinstance(token, str) and token.startswith("-")
    ]
    positional_count = sum(
        1
        for token in (argv or [])
        if isinstance(token, str) and token and not token.startswith("-")
    )
    return (
        f"cli_program_run program={program_name} entrypoint={entrypoint} "
        f"flags={flags} positional_count={positional_count}"
    )


@dataclass
class RuntimeMemoryContext:
    namespace: str
    actor: RuntimeActorRef
    session_id: str
    trace_id: str
    program_path: str
    entrypoint: str
    input_kind: TopLevelInputKind
    invocation_summary: str
    input_text: str
    memory_enabled: bool = True
    sequence_no: int = 0
    agent_id: str | None = None
    last_output_summary: str | None = None
    last_output_kind: str | None = None
    last_trace_closed_attempted: bool = False
    auto_reflection_enqueued: bool = False
    lifecycle_failures: list[str] = field(default_factory=list)
    tool_call_count: int = 0

    @classmethod
    def create_for_cli_run(
        cls,
        *,
        project_root: str | Path | None,
        program_path: str,
        entrypoint: str,
        argv: list[str] | None = None,
        actor_type: str = "service",
        actor_id: str = "sona.cli",
    ) -> RuntimeMemoryContext:
        namespace = resolve_namespace(project_root)
        agent_id = resolve_agent_id(project_root)
        invocation_summary = build_invocation_summary(
            program_path=program_path,
            entrypoint=entrypoint,
            argv=argv,
        )
        return cls(
            namespace=namespace,
            actor=RuntimeActorRef(actor_type=actor_type, actor_id=actor_id),
            session_id=f"sess_{uuid4().hex}",
            trace_id=f"trace_{uuid4().hex}",
            program_path=program_path,
            entrypoint=entrypoint,
            input_kind=TopLevelInputKind.CLI_PROGRAM_RUN,
            invocation_summary=invocation_summary,
            input_text=invocation_summary,
            agent_id=agent_id,
        )

    def next_event_attempt(self, event_kind: str) -> tuple[int, str]:
        self.sequence_no += 1
        return self.sequence_no, f"{self.session_id}:{self.sequence_no}:{event_kind}"

    def disable_memory(self, reason: str) -> None:
        self.memory_enabled = False
        self.lifecycle_failures.append(reason)

    @property
    def default_subject(self) -> str:
        return self.agent_id or Path(self.program_path or self.entrypoint).stem or self.entrypoint
