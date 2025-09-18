"""Policy loading and enforcement (feature foundation).

The policy file (JSON) is intentionally minimal for 0.9.3:
{
  "version": 1,
  "deny": ["regex", ...],
  "allow_providers": ["azure", "anthropic"],
  "max_output_chars": 20000
}

All fields optional. Unknown fields ignored (forward compatibility).
If file missing we treat as empty policy (no denies / no restrictions).

Enforcement helpers:
 - ``deny_text(text)`` returns first matching deny pattern or None
 - ``provider_allowed(name)``
 - ``enforce_output(text)`` raises if output too large per policy

Errors are non-fatal where possible—corrupt policy -> disabled with warning.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .flags import get_flags


@dataclass
class Policy:
    deny_patterns: list[re.Pattern]
    allow_providers: list[str]
    max_output_chars: int | None = None

    def to_dict(self) -> dict[str, object]:  # for diagnostics
        return {
            "deny": [p.pattern for p in self.deny_patterns],
            "allow_providers": self.allow_providers,
            "max_output_chars": self.max_output_chars,
        }


_policy: Policy | None = None


def _load_json(path: str) -> dict[str, object] | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        return None  # silent failure -> policy disabled


def _compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    compiled: list[re.Pattern] = []
    for pat in patterns:
        try:
            compiled.append(re.compile(pat, re.IGNORECASE))
        except re.error:
            # Skip bad pattern; continue
            continue
    return compiled


def load_policy(force: bool = False) -> Policy:
    global _policy
    if _policy is not None and not force:
        return _policy
    flags = get_flags()
    path = flags.policy_path
    data = _load_json(path) or {}
    deny = data.get("deny") if isinstance(data, dict) else None
    allow = data.get("allow_providers") if isinstance(data, dict) else None
    max_out = data.get("max_output_chars") if isinstance(data, dict) else None
    deny_list = [d for d in deny or [] if isinstance(d, str)]
    allow_list = [a for a in allow or [] if isinstance(a, str)]
    max_chars = max_out if isinstance(max_out, int) and max_out > 0 else None
    _policy = Policy(
        deny_patterns=_compile_patterns(deny_list),
        allow_providers=allow_list,
        max_output_chars=max_chars,
    )
    return _policy


def deny_text(text: str) -> str | None:
    pol = load_policy()
    for pat in pol.deny_patterns:
        if pat.search(text):
            return pat.pattern
    return None


def provider_allowed(name: str) -> bool:
    pol = load_policy()
    if not pol.allow_providers:  # empty -> allow all
        return True
    return name in pol.allow_providers


def enforce_output(text: str) -> None:
    pol = load_policy()
    if pol.max_output_chars is not None and len(text) > pol.max_output_chars:
        raise ValueError(
            f"Output exceeds policy limit {pol.max_output_chars} chars"
        )


def policy_snapshot() -> dict[str, object]:
    pol = load_policy()
    return pol.to_dict()
