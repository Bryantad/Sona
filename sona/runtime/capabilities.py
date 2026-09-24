"""Policy-mediated scoped capabilities for trusted host/runtime code."""

from __future__ import annotations

import math
import re
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from .contracts import EffectClass, EffectDecision

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_-]{0,63}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN_SEAL = object()


class CapabilityPolicyError(RuntimeError):
    """A trusted capability policy could not return a valid decision."""


class CapabilityAuditFullError(OverflowError):
    """Raised fail-closed when authorization can no longer be audited."""


@dataclass(frozen=True, slots=True)
class CapabilityRequest:
    effect: EffectClass
    resource_ref: str
    requested_ttl_seconds: int = 300

    def __post_init__(self) -> None:
        if not isinstance(self.effect, EffectClass):
            raise TypeError("effect must be an EffectClass")
        _validate_resource_ref(self.resource_ref)
        if (
            isinstance(self.requested_ttl_seconds, bool)
            or not isinstance(self.requested_ttl_seconds, int)
            or not 1 <= self.requested_ttl_seconds <= 3600
        ):
            raise ValueError("requested_ttl_seconds must be between 1 and 3600")


@dataclass(frozen=True, slots=True)
class CapabilityPolicyDecision:
    decision: EffectDecision
    policy_id: str
    rule_id: str
    policy_sha256: str
    reason_code: str
    maximum_ttl_seconds: int

    def __post_init__(self) -> None:
        if not isinstance(self.decision, EffectDecision):
            raise TypeError("decision must be an EffectDecision")
        if self.decision not in {EffectDecision.ALLOWED, EffectDecision.DENIED}:
            raise ValueError("policy decision must be allowed or denied")
        for field_name, value in (("policy_id", self.policy_id), ("rule_id", self.rule_id)):
            if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
                raise ValueError(f"{field_name} must be a safe identifier")
        if not isinstance(self.policy_sha256, str) or not _SHA256.fullmatch(self.policy_sha256):
            raise ValueError("policy_sha256 must be a lowercase sha256 label")
        if not isinstance(self.reason_code, str) or not _SAFE_CODE.fullmatch(self.reason_code):
            raise ValueError("reason_code must be a safe uppercase code")
        if (
            isinstance(self.maximum_ttl_seconds, bool)
            or not isinstance(self.maximum_ttl_seconds, int)
            or not 0 <= self.maximum_ttl_seconds <= 3600
        ):
            raise ValueError("maximum_ttl_seconds must be between 0 and 3600")
        if self.decision is EffectDecision.ALLOWED and self.maximum_ttl_seconds < 1:
            raise ValueError("allowed decisions require a positive maximum_ttl_seconds")


class CapabilityPolicy(Protocol):
    """Trusted host policy port; untrusted proposals must never implement it."""

    def evaluate(self, request: CapabilityRequest) -> CapabilityPolicyDecision: ...


class CapabilityToken:
    """Opaque in-process grant; callers cannot construct one through the API."""

    __slots__ = ("_grant_id", "_effect", "_resource_ref", "_expires_at_monotonic", "_seal")

    def __init__(
        self,
        grant_id: str,
        effect: EffectClass,
        resource_ref: str,
        expires_at_monotonic: float,
        *,
        _seal: object,
    ) -> None:
        if _seal is not _TOKEN_SEAL:
            raise TypeError("CapabilityToken instances are issued only by CapabilityAuthority")
        object.__setattr__(self, "_grant_id", grant_id)
        object.__setattr__(self, "_effect", effect)
        object.__setattr__(self, "_resource_ref", resource_ref)
        object.__setattr__(self, "_expires_at_monotonic", expires_at_monotonic)
        object.__setattr__(self, "_seal", _seal)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("CapabilityToken is immutable")

    @property
    def capability_id(self) -> str:
        return self._grant_id

    @property
    def effect(self) -> EffectClass:
        return self._effect

    @property
    def resource_ref(self) -> str:
        return self._resource_ref


@dataclass(frozen=True, slots=True)
class CapabilityAuditRecord:
    sequence: int
    action: str
    capability_id: str | None
    effect: EffectClass
    resource_ref: str
    decision: EffectDecision
    policy_id: str | None
    rule_id: str | None
    reason_code: str
    occurred_at_utc: str


@dataclass(frozen=True, slots=True)
class CapabilityRequestResult:
    decision: EffectDecision
    reason_code: str
    capability: CapabilityToken | None
    audit_sequence: int


@dataclass(frozen=True, slots=True)
class CapabilityCheckResult:
    decision: EffectDecision
    reason_code: str
    audit_sequence: int


class CapabilityAuthority:
    """Issue exact-resource, expiring grants only after trusted policy allows.

    This is an API-level boundary within one process, not a Python sandbox.
    It never executes an effect; callers must still enforce grants at the
    trusted operation boundary and separately record the outcome.
    """

    def __init__(
        self,
        policy: CapabilityPolicy,
        *,
        maximum_active_grants: int = 4096,
        maximum_audit_records: int = 16_384,
        monotonic_clock: Callable[[], float] = time.monotonic,
        utc_clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not callable(getattr(policy, "evaluate", None)):
            raise TypeError("policy must implement evaluate(CapabilityRequest)")
        if (
            isinstance(maximum_active_grants, bool)
            or not isinstance(maximum_active_grants, int)
            or not 1 <= maximum_active_grants <= 65_536
        ):
            raise ValueError("maximum_active_grants must be between 1 and 65536")
        if (
            isinstance(maximum_audit_records, bool)
            or not isinstance(maximum_audit_records, int)
            or not 1 <= maximum_audit_records <= 65_536
        ):
            raise ValueError("maximum_audit_records must be between 1 and 65536")
        if not callable(monotonic_clock):
            raise TypeError("monotonic_clock must be callable")
        if utc_clock is not None and not callable(utc_clock):
            raise TypeError("utc_clock must be callable")
        self._policy = policy
        self._maximum_active_grants = maximum_active_grants
        self._maximum_audit_records = maximum_audit_records
        self._monotonic_clock = monotonic_clock
        self._utc_clock = utc_clock or (lambda: datetime.now(UTC))
        self._lock = threading.RLock()
        self._grants: dict[str, tuple[CapabilityToken, str]] = {}
        self._audit: list[CapabilityAuditRecord] = []

    def request(self, request: CapabilityRequest) -> CapabilityRequestResult:
        if not isinstance(request, CapabilityRequest):
            raise TypeError("request must be a CapabilityRequest")
        with self._lock:
            self._require_audit_capacity()
            try:
                decision = self._policy.evaluate(request)
                if not isinstance(decision, CapabilityPolicyDecision):
                    raise ValueError("policy returned an invalid decision")
            except Exception as exc:
                record = self._append_audit(
                    action="request_denied",
                    capability_id=None,
                    request=request,
                    decision=EffectDecision.DENIED,
                    policy_id=None,
                    rule_id=None,
                    reason_code="SONA-CAPABILITY-POLICY-ERROR",
                )
                raise CapabilityPolicyError(
                    f"trusted capability policy failed (audit sequence {record.sequence})"
                ) from None

            if decision.decision is EffectDecision.DENIED:
                record = self._append_audit(
                    "request_denied",
                    None,
                    request,
                    decision.decision,
                    decision.policy_id,
                    decision.rule_id,
                    decision.reason_code,
                )
                return CapabilityRequestResult(
                    decision.decision, decision.reason_code, None, record.sequence
                )
            if request.requested_ttl_seconds > decision.maximum_ttl_seconds:
                record = self._append_audit(
                    "request_denied",
                    None,
                    request,
                    EffectDecision.DENIED,
                    decision.policy_id,
                    decision.rule_id,
                    "SONA-CAPABILITY-TTL-EXCEEDED",
                )
                return CapabilityRequestResult(
                    EffectDecision.DENIED,
                    "SONA-CAPABILITY-TTL-EXCEEDED",
                    None,
                    record.sequence,
                )
            now = self._now_monotonic()
            active_count = sum(
                status == "active" and now < token._expires_at_monotonic
                for token, status in self._grants.values()
            )
            if active_count >= self._maximum_active_grants:
                raise CapabilityAuditFullError(
                    "active capability limit reached; no grant was issued"
                )
            grant_id = str(uuid.uuid4())
            token = CapabilityToken(
                grant_id,
                request.effect,
                request.resource_ref,
                now + request.requested_ttl_seconds,
                _seal=_TOKEN_SEAL,
            )
            record = self._append_audit(
                "grant_issued",
                grant_id,
                request,
                EffectDecision.ALLOWED,
                decision.policy_id,
                decision.rule_id,
                decision.reason_code,
            )
            self._grants[grant_id] = (token, "active")
            return CapabilityRequestResult(
                EffectDecision.ALLOWED, decision.reason_code, token, record.sequence
            )

    def check(
        self,
        token: CapabilityToken,
        effect: EffectClass,
        resource_ref: str,
    ) -> CapabilityCheckResult:
        if type(token) is not CapabilityToken:
            raise TypeError("token must be a CapabilityToken issued by this authority")
        if not isinstance(effect, EffectClass):
            raise TypeError("effect must be an EffectClass")
        _validate_resource_ref(resource_ref)
        request = CapabilityRequest(effect, resource_ref)
        with self._lock:
            self._require_audit_capacity()
            grant = self._grants.get(token.capability_id)
            reason_code = "SONA-CAPABILITY-UNKNOWN"
            decision = EffectDecision.DENIED
            action = "check_denied"
            if grant is not None and grant[0] is token:
                state = grant[1]
                if state == "active" and self._now_monotonic() >= token._expires_at_monotonic:
                    self._grants[token.capability_id] = (token, "expired")
                    state = "expired"
                    action = "grant_expired"
                    reason_code = "SONA-CAPABILITY-EXPIRED"
                if state == "active":
                    if token.effect is effect and token.resource_ref == resource_ref:
                        decision = EffectDecision.ALLOWED
                        action = "check_allowed"
                        reason_code = "SONA-CAPABILITY-ALLOWED"
                    else:
                        reason_code = "SONA-CAPABILITY-SCOPE-MISMATCH"
                elif state == "revoked":
                    reason_code = "SONA-CAPABILITY-REVOKED"
                elif state == "expired":
                    reason_code = "SONA-CAPABILITY-EXPIRED"
            record = self._append_audit(
                action,
                token.capability_id,
                request,
                decision,
                None,
                None,
                reason_code,
            )
            return CapabilityCheckResult(decision, reason_code, record.sequence)

    def revoke(self, token: CapabilityToken) -> bool:
        if type(token) is not CapabilityToken:
            raise TypeError("token must be a CapabilityToken issued by this authority")
        request = CapabilityRequest(token.effect, token.resource_ref)
        with self._lock:
            grant = self._grants.get(token.capability_id)
            if grant is None or grant[0] is not token or grant[1] != "active":
                return False
            self._require_audit_capacity()
            self._grants[token.capability_id] = (token, "revoked")
            self._append_audit(
                "grant_revoked",
                token.capability_id,
                request,
                EffectDecision.DENIED,
                None,
                None,
                "SONA-CAPABILITY-REVOKED",
            )
            return True

    def audit_snapshot(self) -> tuple[CapabilityAuditRecord, ...]:
        with self._lock:
            return tuple(self._audit)

    def _require_audit_capacity(self) -> None:
        if len(self._audit) >= self._maximum_audit_records:
            raise CapabilityAuditFullError("capability audit is full; authorization fails closed")

    def _append_audit(
        self,
        action: str,
        capability_id: str | None,
        request: CapabilityRequest,
        decision: EffectDecision,
        policy_id: str | None,
        rule_id: str | None,
        reason_code: str,
    ) -> CapabilityAuditRecord:
        self._require_audit_capacity()
        record = CapabilityAuditRecord(
            sequence=len(self._audit) + 1,
            action=action,
            capability_id=capability_id,
            effect=request.effect,
            resource_ref=request.resource_ref,
            decision=decision,
            policy_id=policy_id,
            rule_id=rule_id,
            reason_code=reason_code,
            occurred_at_utc=self._now_utc(),
        )
        self._audit.append(record)
        return record

    def _now_monotonic(self) -> float:
        value = self._monotonic_clock()
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("monotonic clock must return a finite number")
        try:
            value = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError("monotonic clock must return a finite number") from exc
        if not math.isfinite(value):
            raise ValueError("monotonic clock must return a finite number")
        return value

    def _now_utc(self) -> str:
        value = self._utc_clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError("UTC clock must return a timezone-aware datetime")
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _validate_resource_ref(value: str) -> None:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ValueError("resource_ref must be a safe opaque identifier, never a raw path")
