"""One-shot, exact-resource capabilities for Guide editor-buffer replacements."""

from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from sona.runtime import (
    CapabilityAuthority,
    CapabilityPolicyDecision,
    CapabilityRequest,
    EffectClass,
    EffectDecision,
)
from sona.runtime.capabilities import CapabilityAuditRecord

from .proposals import validate_source_proposal

_POLICY_HASH = "sha256:" + hashlib.sha256(b"sona-guide-buffer-policy-v1").hexdigest()
_EFFECT = EffectClass.EDITOR_BUFFER_REPLACE
_TTL_SECONDS = 5
_MAX_ROOTS = 64
_MAX_PENDING = 1024


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="strict")).hexdigest()


def _position(value: object) -> tuple[int, int]:
    if not isinstance(value, dict) or set(value) != {"line", "character"}:
        raise ValueError("selection position is invalid")
    line, character = value["line"], value["character"]
    if any(type(part) is not int or part < 0 or part > 2_147_483_647 for part in (line, character)):
        raise ValueError("selection position is invalid")
    return line, character


def _utf16_offset(source: str, line: int, character: int) -> int:
    lines = source.splitlines(keepends=True)
    if source.endswith(("\n", "\r")):
        lines.append("")
    if line >= max(1, len(lines)):
        raise ValueError("selection is outside the document")
    current = lines[line] if lines else ""
    content = current.rstrip("\r\n")
    units = 0
    for index, char in enumerate(content):
        if units == character:
            return sum(len(item) for item in lines[:line]) + index
        units += len(char.encode("utf-16-le")) // 2
        if units > character:
            raise ValueError("selection splits a UTF-16 character")
    if units == character:
        return sum(len(item) for item in lines[:line]) + len(content)
    raise ValueError("selection is outside the line")


def _binding(
    project_root: str | Path,
    document_uri: str,
    document_version: int,
    selection: object,
    source: str,
    proposed_source: str,
    replacement: str,
) -> tuple[str, str, str, str]:
    if not isinstance(document_uri, str) or not document_uri or len(document_uri) > 4096:
        raise ValueError("document identity is invalid")
    if type(document_version) is not int or not 0 <= document_version <= 2_147_483_647:
        raise ValueError("document version is invalid")
    if not isinstance(selection, dict) or set(selection) != {"start", "end"}:
        raise ValueError("selection is invalid")
    start, end = _position(selection["start"]), _position(selection["end"])
    if end < start:
        raise ValueError("selection is invalid")
    begin, finish = _utf16_offset(source, *start), _utf16_offset(source, *end)
    if finish < begin or source[:begin] + replacement + source[finish:] != proposed_source:
        raise ValueError("replacement does not match the exact selection")
    root = Path(project_root).expanduser().resolve()
    source_hash, proposed_hash, replacement_hash = (
        _hash_text(source),
        _hash_text(proposed_source),
        _hash_text(replacement),
    )
    # Only hashes of workspace and document identities enter the capability audit.
    material = "\0".join(
        (
            "sona-guide-editor-buffer-replace-v1",
            _hash_text(str(root)),
            _hash_text(document_uri),
            str(document_version),
            f"{start[0]}:{start[1]}",
            f"{end[0]}:{end[1]}",
            source_hash,
            proposed_hash,
            replacement_hash,
        )
    )
    return "guide-edit:" + _hash_text(material), source_hash, proposed_hash, replacement_hash


class GuideBufferPolicy:
    """Permit only the Guide effect; configured Guardian state becomes a fail-closed gate."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).expanduser().resolve()

    def _guardian_state(self) -> tuple[bool, bool, str]:
        state_dir = self.root / ".sona" / "guardian"
        state_files = (state_dir / "baseline.json", state_dir / "trusted_config.json")
        expected = any(path.exists() for path in state_files)
        if not expected:
            return False, True, _POLICY_HASH
        from sona.stdlib.native_guardian import guardian_check

        result = guardian_check(self.root)
        policy = result.get("policy") if isinstance(result, dict) else None
        valid = bool(
            isinstance(result, dict)
            and result.get("status") == "ok"
            and isinstance(policy, dict)
            and policy.get("status") == "valid"
            and policy.get("source") == "trusted-policy"
            and policy.get("legacy_baseline") is False
        )
        state_hashes = []
        for path in state_files:
            try:
                state_hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
            except FileNotFoundError:
                state_hashes.append("missing")
        state_hash = hashlib.sha256("\0".join(state_hashes).encode("ascii")).hexdigest()
        policy_hash = policy.get("policy_sha256") if isinstance(policy, dict) else "invalid"
        fingerprint = hashlib.sha256(f"{policy_hash}\0{state_hash}".encode()).hexdigest()
        return True, valid, "sha256:" + fingerprint

    def evaluate(self, request: CapabilityRequest) -> CapabilityPolicyDecision:
        try:
            guardian_expected, guardian_valid, policy_hash = self._guardian_state()
        except Exception:
            guardian_expected, guardian_valid, policy_hash = True, False, _POLICY_HASH
        allowed = request.effect is _EFFECT and guardian_valid
        return CapabilityPolicyDecision(
            decision=EffectDecision.ALLOWED if allowed else EffectDecision.DENIED,
            policy_id="guide-buffer",
            rule_id="exact-editor-buffer-replace",
            policy_sha256=policy_hash,
            reason_code=(
                "SONA-GUIDE-CAPABILITY-ALLOWED"
                if allowed and not guardian_expected
                else (
                    "SONA-GUIDE-GUARDIAN-TRUSTED"
                    if allowed
                    else (
                        "SONA-GUIDE-GUARDIAN-UNTRUSTED"
                        if guardian_expected
                        else "SONA-GUIDE-EFFECT-UNSUPPORTED"
                    )
                )
            ),
            maximum_ttl_seconds=_TTL_SECONDS if allowed else 0,
        )


@dataclass
class _Pending:
    authority: CapabilityAuthority
    token: object
    resource_ref: str
    project_root: Path
    expires_at: float
    policy_sha256: str


class EditorBufferCapabilityBroker:
    """Keep one-shot capabilities in process memory and expose only opaque handles."""

    def __init__(self, *, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._lock = RLock()
        self._authorities: dict[Path, CapabilityAuthority] = {}
        self._policies: dict[Path, GuideBufferPolicy] = {}
        self._pending: dict[str, _Pending] = {}

    def _authority(self, root: Path) -> CapabilityAuthority:
        authority = self._authorities.get(root)
        if authority is None:
            if len(self._authorities) >= _MAX_ROOTS:
                raise OverflowError("Guide workspace authorization limit reached")
            policy = GuideBufferPolicy(root)
            authority = CapabilityAuthority(
                policy,
                maximum_active_grants=_MAX_PENDING,
                maximum_audit_records=16_384,
                monotonic_clock=self._clock,
            )
            self._authorities[root] = authority
            self._policies[root] = policy
        return authority

    def prepare(
        self,
        project_root: str | Path,
        document_uri: str,
        document_version: int,
        selection: object,
        source: str,
        proposed_source: str,
        replacement: str,
    ) -> dict[str, object]:
        try:
            validation = validate_source_proposal(source, proposed_source, document="<editor>")
            if validation["status"] != "valid":
                return _denied(
                    "SONA-GUIDE-AUTH-INVALID-PROPOSAL",
                    "Sona rejected the proposed editor-buffer change.",
                )
            resource, source_hash, proposed_hash, replacement_hash = _binding(
                project_root,
                document_uri,
                document_version,
                selection,
                source,
                proposed_source,
                replacement,
            )
            if not hmac_compare(validation["proposed_sha256"], proposed_hash):
                return _denied(
                    "SONA-GUIDE-AUTH-PROPOSAL-MISMATCH",
                    "The proposal binding did not match validated source.",
                )
            root = Path(project_root).expanduser().resolve()
            with self._lock:
                now = self._clock()
                self._pending = {
                    key: value for key, value in self._pending.items() if now < value.expires_at
                }
                if len(self._pending) >= _MAX_PENDING:
                    return _denied(
                        "SONA-GUIDE-AUTH-BUSY",
                        "Too many pending editor approvals; retry with a fresh proposal.",
                    )
                authority = self._authority(root)
                policy = self._policies[root]
                before = policy.evaluate(CapabilityRequest(_EFFECT, resource, _TTL_SECONDS))
                if before.decision is not EffectDecision.ALLOWED:
                    return _denied(
                        "SONA-GUIDE-AUTH-DENIED",
                        "Trusted policy denied this editor-buffer change.",
                        before.reason_code,
                    )
                request = authority.request(CapabilityRequest(_EFFECT, resource, _TTL_SECONDS))
                if request.decision is not EffectDecision.ALLOWED or request.capability is None:
                    return _denied(
                        "SONA-GUIDE-AUTH-DENIED",
                        "Trusted policy denied this editor-buffer change.",
                        request.reason_code,
                    )
                after = policy.evaluate(CapabilityRequest(_EFFECT, resource, _TTL_SECONDS))
                if (
                    after.decision is not EffectDecision.ALLOWED
                    or after.policy_sha256 != before.policy_sha256
                ):
                    authority.revoke(request.capability)
                    return _denied(
                        "SONA-GUIDE-AUTH-TRUST-CHANGED",
                        "Project trust changed during authorization; request a fresh proposal.",
                    )
                handle = str(uuid.uuid4())
                self._pending[handle] = _Pending(
                    authority,
                    request.capability,
                    resource,
                    root,
                    now + _TTL_SECONDS,
                    before.policy_sha256,
                )
            return {
                "schema_version": 1,
                "status": "prepared",
                "handle": handle,
                "effect": _EFFECT.value,
                "source_sha256": "sha256:" + source_hash,
                "proposed_sha256": "sha256:" + proposed_hash,
                "replacement_sha256": "sha256:" + replacement_hash,
            }
        except Exception:
            return _denied(
                "SONA-GUIDE-AUTH-UNAVAILABLE",
                "Trusted editor authorization is unavailable; no edit was applied.",
            )

    def consume(
        self,
        handle: str,
        project_root: str | Path,
        document_uri: str,
        document_version: int,
        selection: object,
        source: str,
        proposed_source: str,
        replacement: str,
    ) -> dict[str, object]:
        with self._lock:
            pending = self._pending.pop(handle, None) if isinstance(handle, str) else None
        if pending is None:
            return _denied(
                "SONA-GUIDE-AUTH-CAPABILITY-MISSING",
                "The one-shot editor capability is missing, expired, or already consumed.",
            )
        try:
            try:
                resource, source_hash, proposed_hash, replacement_hash = _binding(
                    project_root,
                    document_uri,
                    document_version,
                    selection,
                    source,
                    proposed_source,
                    replacement,
                )
            except (ValueError, TypeError, UnicodeError):
                return _denied(
                    "SONA-GUIDE-AUTH-RESOURCE-CHANGED",
                    "The exact editor proposal changed; request a fresh proposal.",
                )
            if self._clock() >= pending.expires_at or resource != pending.resource_ref:
                return _denied(
                    "SONA-GUIDE-AUTH-RESOURCE-CHANGED",
                    "The exact editor proposal changed; request a fresh proposal.",
                )
            request = CapabilityRequest(_EFFECT, resource, _TTL_SECONDS)
            decision = GuideBufferPolicy(pending.project_root).evaluate(request)
            if decision.decision is not EffectDecision.ALLOWED:
                return _denied(
                    "SONA-GUIDE-AUTH-GUARDIAN-DENIED",
                    "Project trust state no longer permits this edit.",
                    decision.reason_code,
                )
            if decision.policy_sha256 != pending.policy_sha256:
                return _denied(
                    "SONA-GUIDE-AUTH-TRUST-CHANGED",
                    "Project trust state changed; request a fresh proposal.",
                )
            checked = pending.authority.check(pending.token, _EFFECT, resource)
            if checked.decision is not EffectDecision.ALLOWED:
                return _denied(
                    "SONA-GUIDE-AUTH-CAPABILITY-DENIED",
                    "The one-shot editor capability is no longer valid.",
                    checked.reason_code,
                )
            final_decision = GuideBufferPolicy(pending.project_root).evaluate(request)
            if final_decision.decision is not EffectDecision.ALLOWED:
                return _denied(
                    "SONA-GUIDE-AUTH-GUARDIAN-DENIED",
                    "Project trust state no longer permits this edit.",
                    final_decision.reason_code,
                )
            if final_decision.policy_sha256 != pending.policy_sha256:
                return _denied(
                    "SONA-GUIDE-AUTH-TRUST-CHANGED",
                    "Project trust state changed during authorization; request a fresh proposal.",
                )
            return {
                "schema_version": 1,
                "status": "authorized",
                "effect": _EFFECT.value,
                "source_sha256": "sha256:" + source_hash,
                "proposed_sha256": "sha256:" + proposed_hash,
                "replacement_sha256": "sha256:" + replacement_hash,
            }
        except Exception:
            return _denied(
                "SONA-GUIDE-AUTH-UNAVAILABLE",
                "Trusted editor authorization is unavailable; no edit was applied.",
            )
        finally:
            with suppress(Exception):
                pending.authority.revoke(pending.token)

    def discard(self, handle: str) -> None:
        """Burn a pending handle when the LSP live-document preflight fails."""
        with self._lock:
            pending = self._pending.pop(handle, None) if isinstance(handle, str) else None
        if pending is not None:
            with suppress(Exception):
                pending.authority.revoke(pending.token)

    def audit_snapshot(self, project_root: str | Path) -> tuple[CapabilityAuditRecord, ...]:
        root = Path(project_root).expanduser().resolve()
        authority = self._authorities.get(root)
        return authority.audit_snapshot() if authority is not None else ()


def hmac_compare(left: object, right: object) -> bool:
    import hmac

    return isinstance(left, str) and isinstance(right, str) and hmac.compare_digest(left, right)


def _denied(code: str, message: str, reason: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "denied",
        "diagnostic_id": code,
        "message": message,
    }
    if reason:
        result["reason_code"] = reason
    return result


_BROKER = EditorBufferCapabilityBroker()


def prepare_editor_buffer_edit(*args, **kwargs) -> dict[str, object]:
    return _BROKER.prepare(*args, **kwargs)


def consume_editor_buffer_edit(*args, **kwargs) -> dict[str, object]:
    return _BROKER.consume(*args, **kwargs)


def discard_editor_buffer_edit(handle: str) -> None:
    _BROKER.discard(handle)


def editor_buffer_authorization_audit(
    project_root: str | Path,
) -> tuple[CapabilityAuditRecord, ...]:
    return _BROKER.audit_snapshot(project_root)
