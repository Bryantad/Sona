"""Bounded data-only AI proposals gated by trusted validation and approval."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Mapping

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_-]{0,63}$")
_MAX_PROPOSAL_BYTES = 65_536
_ACCEPTED_SEAL = object()


class ProposalStatus(StrEnum):
    REJECTED = "rejected"
    ACCEPTED = "accepted"


@dataclass(frozen=True, slots=True)
class UntrustedProposal:
    proposal_id: str
    source_id: str
    payload_json: str

    def __post_init__(self) -> None:
        _validate_id(self.proposal_id, "proposal_id")
        _validate_id(self.source_id, "source_id")
        if not isinstance(self.payload_json, str):
            raise TypeError("payload_json must be a string")
        if len(self.payload_json.encode("utf-8")) > _MAX_PROPOSAL_BYTES:
            raise ValueError("proposal payload exceeds 65536 UTF-8 bytes")
        try:
            data = json.loads(self.payload_json)
            canonical = json.dumps(
                data,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ValueError("payload_json must be canonical bounded JSON object data") from exc
        if not isinstance(data, dict) or canonical != self.payload_json:
            raise ValueError("payload_json must be canonical bounded JSON object data")

    @classmethod
    def from_data(
        cls, proposal_id: str, source_id: str, payload: Mapping[str, Any]
    ) -> UntrustedProposal:
        _validate_id(proposal_id, "proposal_id")
        _validate_id(source_id, "source_id")
        if not isinstance(payload, Mapping):
            raise TypeError("proposal payload must be a mapping")
        try:
            encoded = json.dumps(
                dict(payload),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("proposal payload must contain finite JSON data") from exc
        if len(encoded.encode("utf-8")) > _MAX_PROPOSAL_BYTES:
            raise ValueError("proposal payload exceeds 65536 UTF-8 bytes")
        return cls(proposal_id, source_id, encoded)

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)


@dataclass(frozen=True, slots=True)
class ProposalValidation:
    valid: bool
    diagnostic_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool):
            raise TypeError("valid must be a boolean")
        _validate_code(self.diagnostic_code)


@dataclass(frozen=True, slots=True)
class ProposalApproval:
    approved: bool
    approver_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.approved, bool):
            raise TypeError("approved must be a boolean")
        _validate_id(self.approver_id, "approver_id")


@dataclass(frozen=True, slots=True)
class AcceptedProposal:
    """Validated, explicitly approved data; never an execution grant."""

    proposal_id: str
    source_id: str
    payload_json: str
    validation_code: str
    approver_id: str
    _seal: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._seal is not _ACCEPTED_SEAL:
            raise TypeError("AcceptedProposal instances are issued only by ProposalGate")
        _validate_id(self.proposal_id, "proposal_id")
        _validate_id(self.source_id, "source_id")
        _validate_id(self.approver_id, "approver_id")
        _validate_code(self.validation_code)
        UntrustedProposal(self.proposal_id, self.source_id, self.payload_json)

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)


@dataclass(frozen=True, slots=True)
class ProposalGateResult:
    status: ProposalStatus
    reason_code: str
    accepted: AcceptedProposal | None = None


class ProposalGate:
    """Requires trusted validation and a distinct explicit approval decision.

    The gate returns data only. It does not execute operations, issue
    capabilities, or alter Guardian or Proof state.
    """

    def __init__(
        self,
        validator: Callable[[UntrustedProposal], ProposalValidation],
        approver: Callable[[UntrustedProposal], ProposalApproval],
    ) -> None:
        if not callable(validator) or not callable(approver):
            raise TypeError("trusted validator and explicit approver are required")
        if validator is approver:
            raise ValueError("validation and approval must be separate callbacks")
        self._validator = validator
        self._approver = approver

    def process(self, proposal: UntrustedProposal) -> ProposalGateResult:
        if not isinstance(proposal, UntrustedProposal):
            raise TypeError("proposal must be an UntrustedProposal")
        try:
            validation = self._validator(proposal)
            if not isinstance(validation, ProposalValidation):
                raise TypeError("validator returned an invalid result")
        except Exception:
            return ProposalGateResult(ProposalStatus.REJECTED, "SONA-PROPOSAL-VALIDATION-ERROR")
        if not validation.valid:
            return ProposalGateResult(ProposalStatus.REJECTED, validation.diagnostic_code)

        try:
            approval = self._approver(proposal)
            if not isinstance(approval, ProposalApproval):
                raise TypeError("approver returned an invalid result")
        except Exception:
            return ProposalGateResult(ProposalStatus.REJECTED, "SONA-PROPOSAL-APPROVAL-ERROR")
        if not approval.approved:
            return ProposalGateResult(ProposalStatus.REJECTED, "SONA-PROPOSAL-NOT-APPROVED")

        accepted = AcceptedProposal(
            proposal_id=proposal.proposal_id,
            source_id=proposal.source_id,
            payload_json=proposal.payload_json,
            validation_code=validation.diagnostic_code,
            approver_id=approval.approver_id,
            _seal=_ACCEPTED_SEAL,
        )
        return ProposalGateResult(ProposalStatus.ACCEPTED, "SONA-PROPOSAL-ACCEPTED", accepted)


def _validate_id(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{name} must be a safe identifier")


def _validate_code(value: str) -> None:
    if not isinstance(value, str) or not _SAFE_CODE.fullmatch(value):
        raise ValueError("diagnostic_code must be a safe uppercase code")
