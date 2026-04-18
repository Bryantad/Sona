from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any


POLICY_VERSION = "0.1"
RULE_ORDERING = "priority_then_rule_id"


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    target: str
    action: str
    pattern: str
    priority: int = 100
    description: str = ""


_BASE_TEXT_RULES: tuple[PolicyRule, ...] = (
    PolicyRule(
        rule_id="deny.prompt.system_override_marker",
        target="prompt",
        action="deny",
        pattern=r"(?i)\bBEGIN_SYSTEM_OVERRIDE\b",
        priority=10,
        description="Block explicit system-override markers in prompts.",
    ),
    PolicyRule(
        rule_id="deny.prompt.policy_test_marker",
        target="prompt",
        action="deny",
        pattern=r"(?i)\bSONA_POLICY_DENY\b",
        priority=20,
        description="Deterministic policy deny marker used for smoke tests.",
    ),
    PolicyRule(
        rule_id="deny.output.policy_test_marker",
        target="output",
        action="deny",
        pattern=r"(?i)\bSONA_POLICY_DENY\b",
        priority=20,
        description="Prevent emitting explicitly denied marker strings.",
    ),
)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sorted_rules(rules: tuple[PolicyRule, ...]) -> list[PolicyRule]:
    return sorted(rules, key=lambda rule: (int(rule.priority), str(rule.rule_id)))


def _extra_deny_markers() -> tuple[str, ...]:
    raw = os.getenv("SONA_POLICY_EXTRA_DENY_MARKERS", "")
    values = [item.strip() for item in raw.split(",")]
    return tuple(item for item in values if item)


def _materialized_rules() -> tuple[PolicyRule, ...]:
    extras = []
    for idx, marker in enumerate(_extra_deny_markers()):
        escaped = re.escape(marker)
        extras.append(
            PolicyRule(
                rule_id=f"deny.prompt.extra_marker_{idx + 1}",
                target="prompt",
                action="deny",
                pattern=escaped,
                priority=50 + idx,
                description="Environment-configured deny marker.",
            )
        )
    merged = tuple(_BASE_TEXT_RULES) + tuple(extras)
    return tuple(_sorted_rules(merged))


def _compile_rule(rule: PolicyRule) -> re.Pattern[str]:
    return re.compile(rule.pattern)


def _evaluate_text(text: str, *, target: str) -> dict[str, Any]:
    value = str(text or "")
    for rule in _materialized_rules():
        if rule.target != target:
            continue
        if rule.action != "deny":
            continue
        if _compile_rule(rule).search(value):
            return {
                "matched": True,
                "decision": "deny",
                "rule_id": rule.rule_id,
                "pattern": rule.pattern,
                "priority": int(rule.priority),
            }
    return {"matched": False, "decision": "allow", "rule_id": None, "pattern": None, "priority": None}


def deny_text(text: str) -> str | None:
    result = _evaluate_text(text, target="prompt")
    if result["matched"]:
        return str(result["rule_id"])
    return None


def enforce_output(output: str) -> str:
    result = _evaluate_text(str(output), target="output")
    if result["matched"]:
        raise ValueError(f"Output denied by policy rule: {result['rule_id']}")
    return str(output)


def _env_provider_set(var_name: str) -> set[str]:
    raw = os.getenv(var_name, "")
    values = [item.strip().lower() for item in raw.split(",")]
    return {item for item in values if item}


def provider_allowed(provider_name: str) -> bool:
    name = str(provider_name or "").strip().lower()
    if not name:
        return False

    allowed = _env_provider_set("SONA_ALLOWED_PROVIDERS")
    denied = _env_provider_set("SONA_DENIED_PROVIDERS")

    if name in denied:
        return False
    if allowed and name not in allowed:
        return False
    return True


def policy_fingerprint() -> str:
    payload = {
        "version": POLICY_VERSION,
        "ordering": RULE_ORDERING,
        "rules": [
            {
                "id": rule.rule_id,
                "target": rule.target,
                "action": rule.action,
                "priority": int(rule.priority),
                "pattern": rule.pattern,
            }
            for rule in _materialized_rules()
        ],
    }
    return _hash_text(_canonical_json(payload))


def policy_snapshot() -> dict[str, Any]:
    rules = _materialized_rules()
    snapshot_rules = [
        {
            "id": rule.rule_id,
            "target": rule.target,
            "action": rule.action,
            "priority": int(rule.priority),
            "pattern": rule.pattern,
            "pattern_sha256": _hash_text(rule.pattern),
            "description": rule.description,
        }
        for rule in rules
    ]
    data = {
        "version": POLICY_VERSION,
        "deterministic_ordering": RULE_ORDERING,
        "rules": snapshot_rules,
        "provider_controls": {
            "allowed_providers_env": sorted(_env_provider_set("SONA_ALLOWED_PROVIDERS")),
            "denied_providers_env": sorted(_env_provider_set("SONA_DENIED_PROVIDERS")),
        },
    }
    data["policy_fingerprint"] = _hash_text(_canonical_json(data))
    return data
