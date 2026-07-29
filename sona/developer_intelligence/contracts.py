"""Serializable contracts for Sona's headless developer-intelligence backend."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .diagnostics import Diagnostic
from .redaction import redact


class StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class TaskType(StringEnum):
    COMPLETE = "complete"
    EXPLAIN = "explain"
    DIAGNOSE = "diagnose"
    SUGGEST = "suggest"
    REFACTOR = "refactor"
    EDIT = "edit"
    GENERATE_TESTS = "generate_tests"
    REVIEW = "review"
    FIX = "fix"
    DOCUMENT = "document"


class TaskStatus(StringEnum):
    OK = "ok"
    PROPOSED = "proposed"
    APPROVAL_REQUIRED = "approval_required"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))

    def to_json(self, *, canonical: bool = False) -> str:
        return json.dumps(
            redact(self.to_dict()),
            ensure_ascii=False,
            sort_keys=canonical,
            separators=(",", ":") if canonical else None,
            indent=None if canonical else 2,
        )


@dataclass(frozen=True, slots=True)
class ContextEnvelope(Serializable):
    active_file: str | None = None
    selected_text: str | None = None
    target_files: tuple[str, ...] = ()
    workspace_summary: str | None = None
    diagnostics: tuple[dict[str, Any], ...] = ()
    language_id: str | None = None
    maximum_context_tokens: int = 32000
    redacted_context: tuple[str, ...] = ()
    omitted_context: tuple[str, ...] = ()
    origin: str = "cli"


@dataclass(frozen=True, slots=True)
class TaskConstraints(Serializable):
    preserve_behavior: bool = True
    read_only: bool = True
    allow_file_writes: bool = False
    allow_shell: bool = False
    allow_network: bool = False
    maximum_files: int = 10
    maximum_patch_bytes: int = 100000
    maximum_context_tokens: int = 32000
    maximum_estimated_cost_usd: float | None = 0.25
    required_approval: bool = False

    def __post_init__(self) -> None:
        integer_fields = (
            self.maximum_files, self.maximum_patch_bytes,
            self.maximum_context_tokens,
        )
        if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in integer_fields):
            raise TypeError("task constraint limits must be positive integers")
        if self.maximum_estimated_cost_usd is not None and self.maximum_estimated_cost_usd < 0:
            raise ValueError("maximum_estimated_cost_usd cannot be negative")


@dataclass(frozen=True, slots=True)
class ProviderCapabilities(Serializable):
    completion: bool = False
    structured_output: bool = True
    code_editing: bool = False
    streaming: bool = False
    tool_use: bool = False
    local_execution: bool = True
    network_required: bool = False
    maximum_context_tokens: int | None = None
    cost_metadata_available: bool = False


@dataclass(frozen=True, slots=True)
class BudgetEstimate(Serializable):
    estimated_input_tokens: int | None = None
    maximum_output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    method: str = "unknown"


@dataclass(frozen=True, slots=True)
class TaskRequest(Serializable):
    task_type: TaskType
    instruction: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: int = 1
    target_files: tuple[str, ...] = ()
    provider_id: str | None = None
    model_id: str | None = None
    context: ContextEnvelope = field(default_factory=ContextEnvelope)
    constraints: TaskConstraints = field(default_factory=TaskConstraints)
    governance_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskRequest":
        if int(payload.get("schema_version", 1)) != 1:
            raise ValueError("task request requires schema_version 1")
        try:
            task_type = TaskType(str(payload["task_type"]))
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid task_type") from exc
        context = payload.get("context") or {}
        constraints = payload.get("constraints") or {}
        context = dict(context)
        for name in ("target_files", "diagnostics", "redacted_context", "omitted_context"):
            if name in context:
                context[name] = tuple(context[name] or ())
        return cls(
            schema_version=int(payload.get("schema_version", 1)),
            task_id=str(payload.get("task_id") or uuid.uuid4()),
            task_type=task_type,
            instruction=str(payload.get("instruction") or ""),
            target_files=tuple(payload.get("target_files") or ()),
            provider_id=payload.get("provider_id"),
            model_id=payload.get("model_id"),
            context=ContextEnvelope(**context),
            constraints=TaskConstraints(**constraints),
            governance_metadata=dict(payload.get("governance_metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class TaskPlan(Serializable):
    summary: str
    intended_files: tuple[str, ...] = ()
    intended_operations: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    validation_commands: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True, slots=True)
class PatchFile(Serializable):
    target_path: str
    original_hash: str | None
    proposed_hash: str
    unified_diff: str
    operation: str
    patch_size: int
    proposed_content: str | None = None
    applied: bool = False


@dataclass(frozen=True, slots=True)
class PatchSet(Serializable):
    files: tuple[PatchFile, ...] = ()
    total_size: int = 0

    def __post_init__(self) -> None:
        if self.total_size < 0:
            raise ValueError("patch total_size cannot be negative")


@dataclass(frozen=True, slots=True)
class ApprovalRecord(Serializable):
    required: bool
    status: str = "not_required"
    reason: str = ""
    approver: str | None = None
    approved_at: str | None = None
    scope: str | None = None
    task_id: str | None = None
    patch_hash: str | None = None


@dataclass(frozen=True, slots=True)
class VerificationPlan(Serializable):
    commands: tuple[tuple[str, ...], ...] = ()
    allowed_prefixes: tuple[tuple[str, ...], ...] = ()
    timeout_seconds: int = 30
    maximum_output_bytes: int = 1_000_000
    shell: bool = False

    def __post_init__(self) -> None:
        if self.shell is not False:
            raise ValueError("verification commands must use shell=False")
        if self.timeout_seconds <= 0 or self.maximum_output_bytes <= 0:
            raise ValueError("verification limits must be positive")


@dataclass(frozen=True, slots=True)
class VerificationResult(Serializable):
    commands: tuple[tuple[str, ...], ...] = ()
    allowed: tuple[bool, ...] = ()
    exit_statuses: tuple[int | None, ...] = ()
    output_summary: str = ""
    passed: bool | None = None
    rollback_recommended: bool = False


@dataclass(frozen=True, slots=True)
class ExecutionReceipt(Serializable):
    schema_version: int = 1
    task_id: str = ""
    receipt_hash: str | None = None
    prompt_hash: str | None = None
    response_hash: str | None = None
    context_hash: str | None = None
    policy_hash: str | None = None
    patch_hash: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int = 0
    status: TaskStatus = TaskStatus.OK
    provider_id: str | None = None
    model_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskResult(Serializable):
    task_id: str
    task_type: TaskType
    status: TaskStatus
    summary: str
    schema_version: int = 1
    diagnostics: tuple[Diagnostic, ...] = ()
    plan: TaskPlan | None = None
    patch_set: PatchSet | None = None
    provider_id: str | None = None
    model_id: str | None = None
    governance_decisions: tuple[dict[str, Any], ...] = ()
    budget: BudgetEstimate | None = None
    approval: ApprovalRecord | None = None
    verification_plan: VerificationPlan | None = None
    verification: VerificationResult | None = None
    execution_receipt: ExecutionReceipt | None = None
    receipt_path: str | None = None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = Serializable.to_dict(self)
        # Diagnostic.to_dict() is the canonical flat schema consumed by the
        # CLI and LSP. dataclasses.asdict() would otherwise nest SourceSpan.
        payload["diagnostics"] = [item.to_dict() for item in self.diagnostics]
        return payload
