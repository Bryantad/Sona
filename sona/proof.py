"""Proof Mode receipt verification and inspection helpers.

This module verifies the existing ``sona.native-proof.schema-1`` receipt
contract without requiring Guardian. Guardian-specific checks remain in the
Guardian module and build on top of this general verifier.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NATIVE_PROOF_SCHEMA_ID = "sona.native-proof.schema-1"
NATIVE_PROOF_RECEIPT_TYPE = "native_execution_proof"
NATIVE_PROOF_SCHEMA = 1

CAPABILITY_FIELDS = (
    "console",
    "filesystem_read",
    "filesystem_write",
    "network",
    "process",
    "environment",
)

EFFECT_OUTCOMES = {"allowed", "denied", "failed", "unavailable"}
EFFECT_SUPPORT_STATUSES = {"SUPPORTED", "PARTIAL", "UNOBSERVED", "UNAVAILABLE"}
EFFECT_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:\.[A-Z][A-Z0-9_]*)+$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HMAC_SHA256_RE = re.compile(r"^hmac-sha256:[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
GIT_REVISION_RE = re.compile(r"^git:[0-9a-f]{40}$")

EFFECT_CLASSIFICATIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("filesystem", "fs.read_text"): ("FS.READ", "SUPPORTED"),
    ("filesystem", "fs.exists"): ("FS.READ", "PARTIAL"),
    ("filesystem", "fs.is_file"): ("FS.READ", "PARTIAL"),
    ("filesystem", "fs.is_dir"): ("FS.READ", "PARTIAL"),
    ("filesystem", "fs.write_text"): ("FS.WRITE", "PARTIAL"),
    ("filesystem", "fs.append_text"): ("FS.APPEND", "SUPPORTED"),
    ("filesystem", "fs.create_dir"): ("FS.CREATE", "SUPPORTED"),
    ("filesystem", "fs.remove"): ("FS.DELETE", "SUPPORTED"),
    ("filesystem", "fs.rename.source"): ("FS.RENAME", "SUPPORTED"),
    ("filesystem", "fs.rename.destination"): ("FS.RENAME", "SUPPORTED"),
    ("filesystem", "fs.copy.source"): ("FS.READ", "SUPPORTED"),
    ("filesystem", "fs.copy.destination"): ("FS.WRITE", "PARTIAL"),
    ("filesystem", "fs.list_dir"): ("FS.LIST", "SUPPORTED"),
    ("console", "print"): ("STDOUT.WRITE", "PARTIAL"),
    ("console", "io.write_stdout"): ("STDOUT.WRITE", "PARTIAL"),
    ("console", "io.write_stderr"): ("STDERR.WRITE", "PARTIAL"),
    ("console", "io.flush"): ("CONSOLE.FLUSH", "PARTIAL"),
    ("stdin", "read"): ("STDIN.READ", "SUPPORTED"),
    ("network", "http.get"): ("NET.REQUEST", "UNAVAILABLE"),
    ("network", "http.post"): ("NET.REQUEST", "UNAVAILABLE"),
    ("network", "http.put"): ("NET.REQUEST", "UNAVAILABLE"),
    ("network", "http.patch"): ("NET.REQUEST", "UNAVAILABLE"),
    ("network", "http.delete"): ("NET.REQUEST", "UNAVAILABLE"),
    ("clock", "date.today"): ("CLOCK.READ", "SUPPORTED"),
    ("clock", "time.now"): ("CLOCK.READ", "SUPPORTED"),
    ("clock", "time.timestamp"): ("CLOCK.READ", "SUPPORTED"),
    ("clock", "time.monotonic"): ("CLOCK.READ", "SUPPORTED"),
    ("clock", "time.sleep"): ("CLOCK.SLEEP", "SUPPORTED"),
    ("random", "random.float"): ("RANDOM.READ", "SUPPORTED"),
    ("random", "random.integer"): ("RANDOM.READ", "SUPPORTED"),
    ("random", "random.choice"): ("RANDOM.READ", "SUPPORTED"),
    ("random", "random.shuffle"): ("RANDOM.READ", "SUPPORTED"),
    ("random", "random.seed"): ("RANDOM.SEED", "SUPPORTED"),
}


def classify_effect(scope: str, operation: str) -> tuple[str, str] | None:
    """Return the schema-1 normalized effect and observation support status."""

    return EFFECT_CLASSIFICATIONS.get((scope, operation))


@dataclass(frozen=True)
class ProofDiagnostic(Exception):
    """A safe, user-facing Proof verification diagnostic."""

    diagnostic_id: str
    code: str
    message: str
    hint: str

    def to_dict(self) -> dict[str, str]:
        return {
            "diagnostic_id": self.diagnostic_id,
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
        }

    def __str__(self) -> str:
        return (
            f"error[{self.code}] {self.diagnostic_id}: {self.message}\n"
            f"  --> <receipt>:1:1\n"
            f"  hint: {self.hint}"
        )


def _diagnostic(diagnostic_id: str, message: str, hint: str, code: str = "E0600") -> ProofDiagnostic:
    return ProofDiagnostic(diagnostic_id, code, message, hint)


def canonical_json_bytes(value: Any) -> bytes:
    """Return the schema-1 canonical JSON encoding.

    Schema-1 uses compact UTF-8 JSON with lexicographically sorted object keys
    and no trailing newline. Stored receipts may append exactly one LF after
    the canonical payload for command-line friendliness.
    """

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_label(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def is_sha256_label(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def is_hmac_sha256_label(value: Any) -> bool:
    return isinstance(value, str) and bool(HMAC_SHA256_RE.fullmatch(value))


def load_receipt(path: Any) -> tuple[dict[str, Any], bytes]:
    if path is None or not str(path).strip():
        raise _diagnostic(
            "PROOF-VERIFY-001",
            "Proof Mode receipt path is required.",
            "Use 'sona proof verify <receipt>' with a regular receipt file.",
            "E0001",
        )
    receipt_path = Path(str(path)).expanduser()
    try:
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise _diagnostic(
                "PROOF-VERIFY-002",
                "Proof Mode receipt could not be read safely.",
                "Provide a regular JSON receipt file.",
                "E0601",
            )
        raw = receipt_path.read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
    except ProofDiagnostic:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _diagnostic(
            "PROOF-VERIFY-002",
            "Proof Mode receipt could not be read safely.",
            "Provide a UTF-8 JSON receipt generated by Proof Mode.",
            "E0601",
        ) from exc
    if not isinstance(receipt, dict):
        raise _diagnostic(
            "PROOF-VERIFY-003",
            "Proof Mode receipt must contain a JSON object.",
            "Use an unmodified schema-1 Proof Mode receipt.",
        )
    return receipt, raw


def verify_receipt(path: Any) -> dict[str, Any]:
    receipt, raw = load_receipt(path)
    return verify_receipt_payload(receipt, raw)


def verify_receipt_payload(receipt: dict[str, Any], raw: bytes | None = None) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise _diagnostic(
            "PROOF-VERIFY-003",
            "Proof Mode receipt must contain a JSON object.",
            "Use an unmodified schema-1 Proof Mode receipt.",
        )

    canonical = canonical_json_bytes(receipt)
    if raw is not None and raw not in {canonical, canonical + b"\n"}:
        raise _diagnostic(
            "PROOF-VERIFY-004",
            "Proof Mode receipt is not stored in canonical form.",
            "Use the exact receipt emitted by Proof Mode.",
        )

    unsigned = dict(receipt)
    receipt_hash = unsigned.pop("receipt_hash", None)
    if not is_sha256_label(receipt_hash) or receipt_hash != sha256_label(canonical_json_bytes(unsigned)):
        raise _diagnostic(
            "PROOF-VERIFY-005",
            "Proof Mode receipt hash does not match its canonical contents.",
            "Do not trust this receipt; regenerate proof evidence from source.",
        )

    _validate_schema(receipt)
    engine = _validate_engine(receipt["engine"])
    capabilities = _validate_capabilities(receipt["capabilities"])
    execution = _validate_execution(receipt["execution"])
    effects = _validate_effects(receipt["effects"])
    program = _validate_program(receipt["program"])

    return {
        "schema_version": 1,
        "schema_id": receipt["schema_id"],
        "status": "valid",
        "receipt_hash": receipt_hash,
        "sona_version": receipt["sona_version"],
        "generated_at_utc": receipt["generated_at_utc"],
        "engine": engine,
        "program": program,
        "capabilities": capabilities,
        "execution": execution,
        "effects": effects,
        "guardian_bound": isinstance(receipt.get("guardian"), dict),
    }


def inspect_receipt(path: Any) -> dict[str, Any]:
    """Return safe receipt facts. Invalid receipts return a diagnostic packet."""

    try:
        return verify_receipt(path)
    except ProofDiagnostic as diagnostic:
        return {
            "schema_version": 1,
            "status": "invalid",
            "diagnostic": diagnostic.to_dict(),
        }


def _validate_schema(receipt: dict[str, Any]) -> None:
    required = {
        "schema_id",
        "schema",
        "receipt_type",
        "generated_at_utc",
        "sona_version",
        "engine",
        "program",
        "capabilities",
        "execution",
        "effects",
        "receipt_hash",
    }
    missing = sorted(required.difference(receipt))
    if missing:
        raise _diagnostic(
            "PROOF-VERIFY-006",
            "Proof Mode receipt is missing required schema fields.",
            "Use a complete schema-1 receipt generated by Proof Mode.",
        )
    if (
        receipt.get("schema_id") != NATIVE_PROOF_SCHEMA_ID
        or receipt.get("schema") != NATIVE_PROOF_SCHEMA
        or receipt.get("receipt_type") != NATIVE_PROOF_RECEIPT_TYPE
    ):
        raise _diagnostic(
            "PROOF-VERIFY-007",
            "Proof Mode receipt schema is not supported.",
            "Use a schema-1 Proof Mode receipt.",
        )
    if not isinstance(receipt.get("sona_version"), str) or not receipt["sona_version"].strip():
        raise _diagnostic(
            "PROOF-VERIFY-008",
            "Proof Mode receipt has an invalid Sona runtime identity.",
            "Regenerate the receipt with a supported Sona Native Core binary.",
        )
    if not isinstance(receipt.get("generated_at_utc"), str) or not UTC_RE.fullmatch(receipt["generated_at_utc"]):
        raise _diagnostic(
            "PROOF-VERIFY-009",
            "Proof Mode receipt has an invalid generation timestamp.",
            "Use a receipt with an ISO UTC generated_at_utc value.",
        )


def _validate_engine(engine: Any) -> dict[str, Any]:
    if not isinstance(engine, dict):
        raise _diagnostic("PROOF-VERIFY-010", "Proof Mode engine identity is invalid.", "Use a complete engine record.")
    if engine.get("name") != "native":
        raise _diagnostic("PROOF-VERIFY-011", "Proof Mode engine is not Native Core.", "Verify only Native Core Proof Mode receipts.")
    if engine.get("python_required") is not False or engine.get("python_embedded") is not False:
        raise _diagnostic("PROOF-VERIFY-012", "Proof Mode receipt is not Python-free.", "Regenerate with the Native Core engine.")
    if engine.get("fallback_used") is not False:
        raise _diagnostic("PROOF-VERIFY-013", "Proof Mode receipt used fallback execution.", "Fallback receipts are rejected by Proof Mode verification.")
    result = {
        "name": "native",
        "label": "Native Core",
        "python_required": False,
        "python_embedded": False,
        "fallback_used": False,
    }
    runtime_identity = engine.get("runtime_identity")
    if runtime_identity is None:
        return result
    if not isinstance(runtime_identity, dict) or not set(runtime_identity).issubset(
        {"native_binary", "source_revision"}
    ):
        raise _diagnostic(
            "PROOF-VERIFY-038",
            "Proof Mode Native runtime identity is invalid.",
            "Use a runtime identity emitted by a supported Native Core producer.",
        )
    native_binary = runtime_identity.get("native_binary")
    if (
        not isinstance(native_binary, dict)
        or set(native_binary) != {"sha256", "bytes"}
        or not is_sha256_label(native_binary.get("sha256"))
        or not isinstance(native_binary.get("bytes"), int)
        or isinstance(native_binary.get("bytes"), bool)
        or native_binary["bytes"] < 0
    ):
        raise _diagnostic(
            "PROOF-VERIFY-038",
            "Proof Mode Native binary identity is invalid.",
            "Use a Native binary identity with a SHA-256 label and byte count.",
        )
    source_revision = runtime_identity.get("source_revision")
    if source_revision is not None and (
        not isinstance(source_revision, str)
        or not GIT_REVISION_RE.fullmatch(source_revision)
    ):
        raise _diagnostic(
            "PROOF-VERIFY-039",
            "Proof Mode source revision identity is invalid.",
            "Use a full lowercase git:<40-hex> revision or omit the field.",
        )
    normalized_identity: dict[str, Any] = {
        "native_binary": {
            "sha256": native_binary["sha256"],
            "bytes": native_binary["bytes"],
        }
    }
    if source_revision is not None:
        normalized_identity["source_revision"] = source_revision
    result["runtime_identity"] = normalized_identity
    return result


def _validate_capabilities(capabilities: Any) -> dict[str, bool]:
    if not isinstance(capabilities, dict):
        raise _diagnostic("PROOF-VERIFY-014", "Proof Mode capability record is invalid.", "Use a complete capability record.")
    result: dict[str, bool] = {}
    for field in CAPABILITY_FIELDS:
        value = capabilities.get(field)
        if not isinstance(value, bool):
            raise _diagnostic("PROOF-VERIFY-015", "Proof Mode capability value is invalid.", "Capabilities must be explicit booleans.")
        result[field] = value
    return result


def _validate_execution(execution: Any) -> dict[str, Any]:
    if not isinstance(execution, dict):
        raise _diagnostic("PROOF-VERIFY-016", "Proof Mode execution record is invalid.", "Use a complete execution record.")
    status = execution.get("status")
    exit_code = execution.get("exit_code")
    duration_ms = execution.get("duration_ms")
    if status not in {"ok", "failed"}:
        raise _diagnostic("PROOF-VERIFY-017", "Proof Mode execution status is invalid.", "Execution status must be ok or failed.")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise _diagnostic("PROOF-VERIFY-018", "Proof Mode exit code is invalid.", "Execution exit_code must be an integer.")
    if (status == "ok" and exit_code != 0) or (status == "failed" and exit_code != 1):
        raise _diagnostic("PROOF-VERIFY-019", "Proof Mode execution record is inconsistent.", "Match status and exit_code before verifying.")
    if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or duration_ms < 0:
        raise _diagnostic("PROOF-VERIFY-020", "Proof Mode duration is invalid.", "Execution duration_ms must be a non-negative integer.")
    for stream in ("stdout", "stderr"):
        value = execution.get(stream)
        if not isinstance(value, dict) or not is_sha256_label(value.get("sha256")):
            raise _diagnostic("PROOF-VERIFY-021", "Proof Mode output digest is invalid.", "Output records must include SHA-256 labels.")
        byte_count = value.get("bytes")
        if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
            raise _diagnostic("PROOF-VERIFY-022", "Proof Mode output byte count is invalid.", "Output byte counts must be non-negative integers.")
    return {
        "status": status,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "stdout": execution["stdout"],
        "stderr": execution["stderr"],
        "diagnostic": execution.get("diagnostic"),
    }


def _validate_effects(effects: Any) -> list[dict[str, Any]]:
    if not isinstance(effects, list):
        raise _diagnostic("PROOF-VERIFY-023", "Proof Mode effect records are invalid.", "Effects must be a list.")
    normalized: list[dict[str, Any]] = []
    for index, effect in enumerate(effects, start=1):
        if not isinstance(effect, dict):
            raise _diagnostic("PROOF-VERIFY-024", "Proof Mode effect record is invalid.", "Each effect must be an object.")
        if effect.get("sequence") != index:
            raise _diagnostic("PROOF-VERIFY-025", "Proof Mode effect sequence is invalid.", "Effect sequence numbers must be contiguous.")
        scope = effect.get("scope")
        operation = effect.get("operation")
        outcome = effect.get("outcome")
        if not isinstance(scope, str) or not scope:
            raise _diagnostic("PROOF-VERIFY-026", "Proof Mode effect scope is invalid.", "Each effect needs a non-empty scope.")
        if not isinstance(operation, str) or not operation:
            raise _diagnostic("PROOF-VERIFY-027", "Proof Mode effect operation is invalid.", "Each effect needs a non-empty operation.")
        if outcome not in EFFECT_OUTCOMES:
            raise _diagnostic("PROOF-VERIFY-028", "Proof Mode effect outcome is invalid.", "Use allowed, denied, failed, or unavailable.")
        target = effect.get("target")
        if target is not None and not is_hmac_sha256_label(target):
            raise _diagnostic("PROOF-VERIFY-029", "Proof Mode effect target fingerprint is invalid.", "Targets must be redacted HMAC-SHA256 labels.")
        has_effect = "effect" in effect
        has_support = "support" in effect
        if has_effect != has_support:
            raise _diagnostic(
                "PROOF-VERIFY-035",
                "Proof Mode normalized effect record is incomplete.",
                "Provide both effect and support, or omit both for a legacy record.",
            )
        declared_effect = effect.get("effect")
        declared_support = effect.get("support")
        if has_effect and (
            not isinstance(declared_effect, str)
            or not EFFECT_ID_RE.fullmatch(declared_effect)
            or declared_support not in EFFECT_SUPPORT_STATUSES
        ):
            raise _diagnostic(
                "PROOF-VERIFY-036",
                "Proof Mode normalized effect fields are invalid.",
                "Use a registered uppercase effect identifier and support status.",
            )
        classification = classify_effect(scope, operation)
        if has_effect and classification != (declared_effect, declared_support):
            raise _diagnostic(
                "PROOF-VERIFY-037",
                "Proof Mode normalized effect does not match its observed operation.",
                "Use the registered effect mapping for this low-level operation.",
            )
        normalized_effect = classification or (
            (declared_effect, declared_support) if has_effect else None
        )
        record = {
            "sequence": index,
            "scope": scope,
            "operation": operation,
            "outcome": outcome,
            **({"target": target} if target is not None else {}),
        }
        if normalized_effect is not None:
            record["effect"], record["support"] = normalized_effect
        normalized.append(record)
    return normalized


def _validate_program(program: Any) -> dict[str, Any]:
    if not isinstance(program, dict) or program.get("kind") not in {"source", "sbc"}:
        raise _diagnostic("PROOF-VERIFY-030", "Proof Mode program identity is invalid.", "Use a source or source-backed bytecode receipt.")
    source = program.get("source")
    if not isinstance(source, dict) or not is_sha256_label(source.get("sha256")):
        raise _diagnostic("PROOF-VERIFY-031", "Proof Mode source identity is invalid.", "Program source must include a SHA-256 label.")
    if not _valid_byte_count(source.get("bytes")):
        raise _diagnostic("PROOF-VERIFY-032", "Proof Mode source byte count is invalid.", "Program source bytes must be a non-negative integer.")
    result = {"kind": program["kind"], "source": source}
    if program["kind"] == "sbc":
        container = program.get("container")
        if not isinstance(container, dict) or not is_sha256_label(container.get("sha256")):
            raise _diagnostic("PROOF-VERIFY-033", "Proof Mode container identity is invalid.", "SBC receipts must include a container SHA-256 label.")
        if not _valid_byte_count(container.get("bytes")):
            raise _diagnostic("PROOF-VERIFY-034", "Proof Mode container byte count is invalid.", "Container bytes must be a non-negative integer.")
        result["container"] = container
    return result


def _valid_byte_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def render_verification(result: dict[str, Any]) -> str:
    return _render_valid_receipt(result, "Proof Mode Verification")


def render_inspection(result: dict[str, Any]) -> str:
    if result.get("status") != "valid":
        diagnostic = result.get("diagnostic", {})
        return (
            "Proof Mode Inspection\n\n"
            "Receipt        INVALID\n"
            f"Diagnostic     {diagnostic.get('diagnostic_id', 'PROOF-VERIFY-000')}\n"
            f"Message        {diagnostic.get('message', 'Receipt could not be inspected.')}"
        )
    return _render_valid_receipt(result, "Proof Mode Inspection")


def _render_valid_receipt(result: dict[str, Any], title: str) -> str:
    engine = result["engine"]
    execution = result["execution"]
    program = result["program"]
    execution_label = "SUCCEEDED" if execution["status"] == "ok" else "FAILED"
    python_involved = engine["python_required"] or engine["python_embedded"]
    python_label = "involved" if python_involved else "not involved in recorded execution"
    program_label = "source" if program["kind"] == "source" else "source-backed bytecode"
    lines = [
        title,
        "",
        "Receipt        VALID",
        "Integrity      VALID",
        f"Execution      {execution_label} (exit {execution['exit_code']})",
        f"Program        {program_label}",
        f"Runtime        Sona {result['sona_version']}",
        f"Engine         {engine['label']}",
        f"Python         {python_label}",
        f"Fallback       {str(engine['fallback_used']).lower()}",
        f"Guardian       {'bound' if result.get('guardian_bound') else 'unbound'}",
        f"Schema         schema-{result['schema_version']}",
    ]
    runtime_identity = engine.get("runtime_identity")
    if isinstance(runtime_identity, dict):
        native_binary = runtime_identity["native_binary"]
        lines.extend(
            [
                "",
                "Runtime identity",
                f"- native binary {native_binary['bytes']} B",
                f"  {native_binary['sha256']}",
                f"- source revision {runtime_identity.get('source_revision', 'not recorded')}",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Runtime identity",
                "- native binary not recorded by this producer",
                "- source revision not recorded by this producer",
            ]
        )
    diagnostic = execution.get("diagnostic")
    if isinstance(diagnostic, dict):
        identifier = diagnostic.get("id") or diagnostic.get("diagnostic_id")
        if identifier:
            lines.append(f"Diagnostic     {identifier}")

    lines.extend(["", "Capabilities"])
    for label, value in _capability_display(result["capabilities"]):
        lines.append(f"- {label:<12} {'granted' if value else 'denied'}")

    lines.extend(["", "Observed effects"])
    effects = result.get("effects", [])
    if effects:
        lines.extend(_render_effect_line(effect) for effect in effects)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Program identity",
            f"- source       {program['source']['bytes']} B",
            f"  {program['source']['sha256']}",
        ]
    )
    if program["kind"] == "sbc":
        lines.extend(
            [
                f"- container    {program['container']['bytes']} B",
                f"  {program['container']['sha256']}",
            ]
        )

    lines.extend(
        [
            "",
            "Output identity",
            f"- stdout       {execution['stdout']['bytes']} B",
            f"  {execution['stdout']['sha256']}",
            f"- stderr       {execution['stderr']['bytes']} B",
            f"  {execution['stderr']['sha256']}",
            "",
            "Receipt identity",
            f"- generated    {result['generated_at_utc']}",
            f"- hash         {result['receipt_hash']}",
        ]
    )
    return "\n".join(lines)


def _render_effect_line(effect: dict[str, Any]) -> str:
    identifier = effect.get("effect")
    if not identifier:
        identifier = f"{effect['scope']}.{effect['operation']}".upper()
    support = effect.get("support")
    support_label = f" ({support})" if support else ""
    return f"- {identifier:<18} {effect['outcome']}{support_label}"


def _capability_display(capabilities: dict[str, bool]) -> list[tuple[str, bool]]:
    return [
        ("console", capabilities["console"]),
        ("fs.read", capabilities["filesystem_read"]),
        ("fs.write", capabilities["filesystem_write"]),
        ("network", capabilities["network"]),
        ("process", capabilities["process"]),
        ("environment", capabilities["environment"]),
    ]
