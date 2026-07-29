"""Versioned governance policy parsing and deterministic decisions."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from .redaction import redact

SCHEMA_VERSION = 1
DEFAULT_POLICY: dict[str, Any] = {
    "schema_version": 1,
    "mode": "audit",
    "providers": {
        "deterministic": "allow", "local": "allow", "ollama": "allow",
        "huggingface": "ask", "azure": "ask", "openai_compatible": "ask",
        "claude": "deny", "codex": "deny",
    },
    "capabilities": {
        "read_workspace": "allow", "write_workspace": "ask", "apply_patch": "ask",
        "execute_code": "ask", "network_access": "ask", "read_secrets": "deny",
        "install_packages": "deny", "run_shell": "deny",
    },
    "limits": {
        "maximum_files_per_task": 10, "maximum_patch_bytes": 100000,
        "maximum_context_tokens": 32000, "maximum_estimated_cost_usd": 0.25,
        "require_known_cost": False,
    },
}


def canonical_json(value: Any) -> str:
    return json.dumps(redact(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def policy_hash(policy: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(policy).encode()).hexdigest()


def load_policy(workspace: str | Path) -> tuple[dict[str, Any], str]:
    root = Path(workspace).resolve()
    path = root / ".sona" / "governance.json"
    if not path.exists():
        legacy = root / ".sona-policy.json"
        source = "built-in"
        if legacy.exists():
            source += f"; legacy policy detected at {legacy} (migrate to .sona/governance.json)"
        return json.loads(json.dumps(DEFAULT_POLICY)), source
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_policy(data)
    return data, str(path)


def validate_policy(policy: dict[str, Any]) -> None:
    if not isinstance(policy, dict) or policy.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("governance policy requires schema_version 1")
    if policy.get("mode") not in {"off", "audit", "enforce"}:
        raise ValueError("governance mode must be off, audit, or enforce")
    for domain in ("providers", "capabilities"):
        if not isinstance(policy.get(domain, {}), dict):
            raise ValueError(f"governance {domain} must be an object")
        invalid = set(policy.get(domain, {}).values()) - {"allow", "ask", "deny"}
        if invalid:
            raise ValueError(f"invalid {domain} action: {sorted(invalid)}")
    limits = policy.get("limits", {})
    if not isinstance(limits, dict):
        raise ValueError("governance limits must be an object")
    for name in ("maximum_files_per_task", "maximum_patch_bytes", "maximum_context_tokens"):
        value = limits.get(name)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value <= 0):
            raise ValueError(f"governance limit {name} must be a positive integer")
    cost = limits.get("maximum_estimated_cost_usd")
    if cost is not None and (not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0):
        raise ValueError("maximum_estimated_cost_usd must be a non-negative number")
    if "require_known_cost" in limits and not isinstance(limits["require_known_cost"], bool):
        raise ValueError("require_known_cost must be a boolean")


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    decision: str
    source: str
    reason: str
    task_type: str
    provider: str | None
    model: str | None
    capability: str | None
    approval_required: bool
    blocked: bool
    policy_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def authorize_mutation(
    policy: dict[str, Any], *, source: str, task_type: str,
    capabilities: tuple[str, ...], approval_granted: bool,
    approval_scope: str,
) -> dict[str, Any]:
    """Resolve an enforcing, approval-scoped mutation authorization."""
    mode = policy.get("mode", "audit")
    decisions = [
        evaluate(policy, source=source, task_type=task_type, capability=capability).to_dict()
        for capability in capabilities
    ]
    denied = any(item["decision"] == "deny" for item in decisions)
    approval_needed = any(item["decision"] == "require_approval" for item in decisions)
    authorized = bool(
        mode == "enforce" and not denied and approval_granted
        and all(item["decision"] in {"allow", "require_approval"} for item in decisions)
    )
    reason = (
        "Mutation authorized by enforcing workspace policy and scoped approval."
        if authorized else
        "Mutation requires mode=enforce, non-denied capabilities, and scoped approval."
    )
    return {
        "schema_version": 1, "decision": "allow" if authorized else "deny",
        "authorized": authorized, "blocked": not authorized, "reason": reason,
        "task_type": task_type, "approval_required": approval_needed,
        "approval_granted": bool(approval_granted), "approval_scope": approval_scope,
        "capabilities": list(capabilities), "capability_decisions": decisions,
        "policy_hash": policy_hash(policy), "source": source,
    }


def evaluate(
    policy: dict[str, Any], *, source: str, task_type: str,
    provider: str | None = None, model: str | None = None,
    capability: str | None = None,
) -> GovernanceDecision:
    mode = policy.get("mode", "enforce")
    if capability in {"read_secrets", "run_shell", "install_packages"}:
        action, reason = "deny", f"{capability} is denied by the Sona 0.15.3 hard safety boundary."
    elif mode == "off":
        action, reason = "not_applicable", "Governance mode is off."
    else:
        rule = None
        if capability:
            rule = policy.get("capabilities", {}).get(capability)
        if rule is None and provider:
            rule = policy.get("providers", {}).get(provider)
        mapped = {"allow": "allow", "ask": "require_approval", "deny": "deny"}
        action = mapped.get(rule, "not_applicable")
        reason = f"Policy rule is {rule or 'not applicable'} for {capability or provider or task_type}."
    approval = action == "require_approval"
    hard_denial = capability in {"read_secrets", "run_shell", "install_packages"} and action == "deny"
    blocked = hard_denial or (mode == "enforce" and action in {"deny", "require_approval"})
    return GovernanceDecision(action, source, reason, task_type, provider, model, capability, approval, blocked, policy_hash(policy))


def append_audit(workspace: str | Path, decision: GovernanceDecision | dict[str, Any], *, timestamp: str | None = None) -> Path:
    path = Path(workspace).resolve() / ".sona" / "governance" / "audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": 1,
        "timestamp": timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        **(decision.to_dict() if isinstance(decision, GovernanceDecision) else dict(decision)),
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(record) + "\n")
    return path
