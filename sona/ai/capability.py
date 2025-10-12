"""Deterministic capability helpers (ai_plan / ai_review).

These are placeholder implementations for 0.9.3 focusing on
stable, testable JSON outputs rather than full model integration.
Real model calls can be wired later behind the same functions.
"""
from __future__ import annotations

import hashlib
from typing import Any

from ..flags import get_flags


def _stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def ai_plan(goal: str, context: str | None = None) -> dict[str, Any]:
    flags = get_flags()
    if not flags.enable_capabilities:
        raise RuntimeError("Capabilities feature disabled (enable flag)")
    ctx_hash = _stable_hash(context or "")
    goal_hash = _stable_hash(goal)
    steps = []
    # Simple heuristic splitting goal into pseudo steps
    tokens = [t for t in goal.replace("\n", " ").split(" ") if t]
    for i, tok in enumerate(tokens[:5], start=1):
        steps.append(
            {
                "id": i,
                "action": f"process:{tok.lower()}",
                "status": "pending",
            }
        )
    return {
        "type": "plan",
        "version": 1,
        "goal": goal,
        "goal_hash": goal_hash,
        "context_hash": ctx_hash,
        "steps": steps,
        "meta": {"token_count": len(tokens)},
    }


def ai_review(artifact: str, criteria: str | None = None) -> dict[str, Any]:
    flags = get_flags()
    if not flags.enable_capabilities:
        raise RuntimeError("Capabilities feature disabled (enable flag)")
    crit = criteria or "quality,clarity"
    crit_list = [c.strip().lower() for c in crit.split(",") if c.strip()]
    art_hash = _stable_hash(artifact)
    findings = []
    for c in crit_list:
        findings.append(
            {
                "criterion": c,
                "score": 0.75,  # placeholder deterministic score
                "issues": [],
                "hash": _stable_hash(c + artifact)[:8],
            }
        )
    return {
        "type": "review",
        "version": 1,
        "artifact_hash": art_hash,
        "criteria": crit_list,
        "findings": findings,
        "summary": {
            "overall": 0.75,
            "recommendation": "proceed",
            "hash": _stable_hash(artifact + crit_list[0])[:10],
        },
    }
